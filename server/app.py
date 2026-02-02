import os
import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
from datetime import datetime

from services.parse_holdings import parse_holdings
from services.chatbot_service import chatbot
from services.memory_manager import memory_manager

app = FastAPI(
    title="Portfolio Assistant API",
    description="Portfolio analysis and Q&A chatbot for Indian stock market",
    version="1.0.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    success: bool


class ResetRequest(BaseModel):
    session_id: str


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: Optional[str] = None
    message_count: int = 0

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Portfolio Assistant API is running", "version": "2.0.0"}

@app.post("/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    """
    Upload a portfolio PDF file and process it.
    Returns the parsed and enriched portfolio data.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file_path = UPLOAD_DIR / f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"📁 File uploaded: {file_path}")
        
        portfolio = parse_holdings(str(file_path))
        
        if portfolio is None:
            raise HTTPException(status_code=500, detail="Failed to parse portfolio PDF")
        
        if not portfolio.get("holdings"):
            raise HTTPException(status_code=400, detail="No holdings found in the PDF")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(__file__).parent / f"portfolio_analysis_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(portfolio, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "message": "Portfolio processed successfully",
            "portfolio": portfolio
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Clean up uploaded file after processing
        if file_path.exists():
            file_path.unlink()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    result = chatbot.chat(request.message, request.session_id)
    
    return ChatResponse(
        response=result["response"],
        session_id=result["session_id"],
        success=result["success"]
    )


@app.post("/chat/reset")
async def reset_chat(request: ResetRequest):
    """Reset a chat session to clear conversation history."""
    success = chatbot.reset_session(request.session_id)
    return {"success": success, "message": "Session reset" if success else "Session not found"}


@app.get("/chat/sessions", response_model=List[SessionResponse])
async def get_sessions():
    """Get all chat sessions."""
    sessions = memory_manager.get_all_sessions()
    return [
        SessionResponse(
            id=s.get("id", ""),
            title=s.get("title", "New Chat"),
            created_at=s.get("created_at"),
            message_count=s.get("message_count", 0)
        )
        for s in sessions
    ]


@app.post("/chat/sessions")
async def create_session():
    """Create a new chat session."""
    session_id = memory_manager.create_session()
    return {"success": True, "session_id": session_id}


@app.get("/chat/sessions/{session_id}")
async def get_session_messages(session_id: str):
    """Get messages for a specific session."""
    messages = memory_manager.get_history(session_id)
    return {"session_id": session_id, "messages": messages}


@app.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    success = memory_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "message": "Session deleted"}


@app.post("/portfolio/refresh")
async def refresh_portfolio():
    try:
        portfolio = parse_holdings()
        
        if portfolio is None:
            raise HTTPException(status_code=500, detail="Failed to parse portfolio")
        
        if not portfolio.get("holdings"):
            raise HTTPException(status_code=400, detail="No holdings found in portfolio")
        
        # Save to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"portfolio_analysis_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(portfolio, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "message": "Portfolio refreshed successfully",
            "file": output_file,
            "portfolio": portfolio
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio")
async def get_portfolio():
    """Get the latest portfolio data."""
    from Tools.portfolio_tools import _get_latest_portfolio
    
    portfolio = _get_latest_portfolio()
    if not portfolio:
        raise HTTPException(status_code=404, detail="No portfolio data found. Please upload a PDF first.")
    
    return portfolio


@app.get("/portfolio/summary")
async def get_portfolio_summary():
    """Get the latest portfolio summary."""
    from Tools.portfolio_tools import _get_latest_portfolio
    
    portfolio = _get_latest_portfolio()
    if not portfolio:
        raise HTTPException(status_code=404, detail="No portfolio data found. Please upload a PDF first.")
    
    return {
        "total_holdings": len(portfolio.get('holdings', [])),
        "total_investment": portfolio.get('total_investment', 0),
        "current_value": portfolio.get('total_current_value', 0),
        "total_pnl": portfolio.get('total_pnl', 0),
        "total_pnl_percentage": portfolio.get('total_pnl_percentage', 0)
    }

def main():
    print("🚀 Starting Portfolio Analysis...")
    
    portfolio = parse_holdings()
    
    if portfolio is None:
        print("❌ Failed to parse portfolio. Exiting...")
        return
    
    if not portfolio.get("holdings"):
        print("⚠️ No holdings found in portfolio")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"portfolio_analysis_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Success! Analysis saved to: {output_file}")
    print("\n" + "="*60)
    print("PORTFOLIO SUMMARY")
    print("="*60)
    print(f"Total Holdings: {len(portfolio['holdings'])}")
    print(f"Total Investment: ₹{portfolio['total_investment']:,.2f}")
    print(f"Current Value: ₹{portfolio['total_current_value']:,.2f}")
    print(f"Total P&L: ₹{portfolio['total_pnl']:+,.2f} ({portfolio.get('total_pnl_percentage', 0):+.2f}%)")
    print("="*60)


if __name__ == "__main__":
    main()