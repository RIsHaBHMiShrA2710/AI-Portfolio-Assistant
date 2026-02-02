import os
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
SessionLocal = None
Base = declarative_base()


def init_db():
    global engine, SessionLocal
    
    if not DATABASE_URL:
        print("⚠️ DATABASE_URL not set. Running in memory-only mode.")
        return False
    
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        Base.metadata.create_all(bind=engine)
        print("✅ Database connected and tables created")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def get_db():
    """Get database session."""
    if SessionLocal is None:
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatSession(Base):
    """Chat session model."""
    __tablename__ = "chat_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages) if self.messages else 0
        }


class ChatMessage(Base):
    """Chat message model."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ChatRepository:
    """Repository for chat operations."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def create_session(self, title: str = "New Chat") -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(title=title)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID."""
        return self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
    
    def get_all_sessions(self):
        """Get all sessions ordered by updated_at."""
        return self.db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    
    def update_session_title(self, session_id: str, title: str) -> Optional[ChatSession]:
        """Update session title."""
        session = self.get_session(session_id)
        if session:
            session.title = title
            session.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(session)
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        session = self.get_session(session_id)
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False
    
    def add_message(self, session_id: str, role: str, content: str) -> Optional[ChatMessage]:
        """Add a message to a session."""
        session = self.get_session(session_id)
        if not session:
            session = ChatSession(id=session_id)
            self.db.add(session)
            self.db.commit()
        
        message = ChatMessage(session_id=session_id, role=role, content=content)
        self.db.add(message)
        
        session.updated_at = datetime.utcnow()
        
        if role == "user" and session.title == "New Chat":
            session.title = content[:50] + "..." if len(content) > 50 else content
        
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_messages(self, session_id: str, limit: int = 50):
        """Get messages for a session."""
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .all()
        )
    
    def get_recent_messages(self, session_id: str, limit: int = 10):
        """Get recent messages for context."""
        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(messages))  
