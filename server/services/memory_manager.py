from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from services.database import init_db, SessionLocal, ChatRepository, ChatSession, ChatMessage


@dataclass
class InMemoryMessage:
    """A single chat message for in-memory storage."""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class InMemoryChatSession:
    """A chat session for in-memory storage."""
    session_id: str
    title: str = "New Chat"
    messages: List[InMemoryMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    max_messages: int = 50


class MemoryManager:
    """
    Manages chat sessions with PostgreSQL persistence.
    Falls back to in-memory storage if database unavailable.
    """
    
    def __init__(self, max_messages_per_session: int = 50):
        self._max_messages = max_messages_per_session
        self._use_db = init_db()
        self._in_memory_sessions: Dict[str, InMemoryChatSession] = {}
        
        if self._use_db:
            print("📦 Memory Manager: Using PostgreSQL storage")
        else:
            print("💾 Memory Manager: Using in-memory storage (no database)")
    
    def _get_db_session(self):
        """Get a database session."""
        if not self._use_db or SessionLocal is None:
            return None
        return SessionLocal()
    
    def create_session(self, title: str = "New Chat") -> str:
        """Create a new chat session and return session ID."""
        session_id = str(uuid.uuid4())
        
        if self._use_db:
            db = self._get_db_session()
            if db:
                try:
                    repo = ChatRepository(db)
                    session = repo.create_session(title)
                    return session.id
                finally:
                    db.close()
        self._in_memory_sessions[session_id] = InMemoryChatSession(
            session_id=session_id,
            title=title,
            max_messages=self._max_messages
        )
        return session_id
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Get existing session or create new one."""
        if session_id:
            if self._use_db:
                db = self._get_db_session()
                if db:
                    try:
                        repo = ChatRepository(db)
                        if repo.get_session(session_id):
                            return session_id
                    finally:
                        db.close()
            elif session_id in self._in_memory_sessions:
                return session_id
        
        return self.create_session()
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the session history."""
        if self._use_db:
            db = self._get_db_session()
            if db:
                try:
                    repo = ChatRepository(db)
                    repo.add_message(session_id, role, content)
                    return
                finally:
                    db.close()
        if session_id not in self._in_memory_sessions:
            self._in_memory_sessions[session_id] = InMemoryChatSession(
                session_id=session_id,
                max_messages=self._max_messages
            )
        
        session = self._in_memory_sessions[session_id]
        session.messages.append(InMemoryMessage(role=role, content=content))
        
        if len(session.messages) > session.max_messages:
            session.messages = session.messages[-session.max_messages:]
        
        if role == "user" and session.title == "New Chat":
            session.title = content[:50] + "..." if len(content) > 50 else content
    
    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get chat history as list of dicts."""
        if self._use_db:
            db = self._get_db_session()
            if db:
                try:
                    repo = ChatRepository(db)
                    messages = repo.get_messages(session_id, limit=self._max_messages)
                    return [{"role": m.role, "content": m.content} for m in messages]
                finally:
                    db.close()
        
        if session_id not in self._in_memory_sessions:
            return []
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self._in_memory_sessions[session_id].messages
        ]
    
    def get_history_for_context(self, session_id: str, last_n: int = 10) -> str:
        """Get formatted history string for context injection."""
        if self._use_db:
            db = self._get_db_session()
            if db:
                try:
                    repo = ChatRepository(db)
                    messages = repo.get_recent_messages(session_id, limit=last_n)
                    if not messages:
                        return ""
                    
                    formatted = []
                    for msg in messages:
                        role = "User" if msg.role == "user" else "Assistant"
                        formatted.append(f"{role}: {msg.content}")
                    return "\n".join(formatted)
                finally:
                    db.close()
        
        history = self.get_history(session_id)
        if not history:
            return ""
        
        recent = history[-last_n:]
        formatted = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)
    
    def get_all_sessions(self) -> List[Dict]:
        """Get all chat sessions."""
        if self._use_db:
            db = self._get_db_session()
            if db:
                try:
                    repo = ChatRepository(db)
                    sessions = repo.get_all_sessions()
                    return [s.to_dict() for s in sessions]
                finally:
                    db.close()
        
        return [
            {
                "id": s.session_id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "message_count": len(s.messages)
            }
            for s in self._in_memory_sessions.values()
        ]
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session's history but keep the session."""
        if self._use_db:
            db = self._get_db_session()
            if db:
                try:
                    from services.database import ChatMessage as CM
                    db.query(CM).filter(CM.session_id == session_id).delete()
                    db.commit()
                    return True
                except:
                    db.rollback()
                    return False
                finally:
                    db.close()
        
        if session_id in self._in_memory_sessions:
            self._in_memory_sessions[session_id].messages = []
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session entirely."""
        if self._use_db:
            db = self._get_db_session()
            if db:
                try:
                    repo = ChatRepository(db)
                    return repo.delete_session(session_id)
                finally:
                    db.close()
        
        if session_id in self._in_memory_sessions:
            del self._in_memory_sessions[session_id]
            return True
        return False


memory_manager = MemoryManager(max_messages_per_session=50)
