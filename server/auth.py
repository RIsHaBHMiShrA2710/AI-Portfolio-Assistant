import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
import jwt
from dotenv import load_dotenv

from services.database import get_db, UserRepository

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key_change_in_production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

class GoogleAuthRequest(BaseModel):
    credential: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest, db=Depends(get_db)):
    try:
        # Verify the Google token
        id_info = id_token.verify_oauth2_token(
            request.credential, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )

        # Ensure the token was issued by Google
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # Extract user information
        email = id_info.get("email")
        name = id_info.get("name")
        picture = id_info.get("picture")
        google_id = id_info.get("sub")
        
        # Save or update user in database
        repo = UserRepository(db)
        db_user = repo.create_or_update_google_user(
            email=email,
            name=name,
            picture=picture,
            google_id=google_id
        )

        user_info = db_user.to_dict()

        # Create our own JWT access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_info["email"], "user": user_info}, 
            expires_delta=access_token_expires
        )

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_info
        )

    except ValueError as e:
        # Invalid token
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get the current user if logged in, otherwise returns None.
    Use this to identify users for free/paid tiers or session tracking.
    """
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("user")
    except jwt.PyJWTError:
        return None
