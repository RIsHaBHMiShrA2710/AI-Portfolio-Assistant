from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid
import chromadb

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
    embeddings: List[Dict] = field(default_factory=list)
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
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(path="./chroma_store")
        self.collection = self.chroma_client.get_or_create_collection(
            name="chat_embeddings",
            metadata={"hnsw:space": "cosine"}
        )

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=350,  
            chunk_overlap=50 
        )
        if self._use_db:
            print("📦 Memory Manager: Using PostgreSQL storage")
        else:
            print("💾 Memory Manager: Using in-memory storage (no database)")
    
    def _get_db_session(self):
        """Get a database session."""
        # Lazy import forces Python to grab the live connection, not the initial 'None'
        from services.database import SessionLocal 
        
        if not self._use_db or SessionLocal is None:
            print("⚠️ Warning: DB is enabled but SessionLocal is still None!")
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
        """Get existing session or create new one with strict validation."""
        
        # 1. Sanitize common frontend bugs (JS sending "null" or "undefined" as strings)
        if isinstance(session_id, str):
            session_id = session_id.strip()
            if session_id.lower() in ["null", "none", "undefined", ""]:
                session_id = None

        if session_id:
            print(f"🕵️ Checking for existing session_id: '{session_id}'")
            
            if self._use_db:
                db = self._get_db_session()
                if db:
                    try:
                        repo = ChatRepository(db)
                        if repo.get_session(session_id):
                            print(f"✅ Found session in PostgreSQL DB: {session_id}")
                            return session_id
                        else:
                            print(f"❌ Session '{session_id}' NOT FOUND in PostgreSQL DB! Falling back to new session.")
                    finally:
                        db.close()
            elif session_id in self._in_memory_sessions:
                print(f"✅ Found session in In-Memory storage: {session_id}")
                return session_id
            else:
                print(f"❌ Session '{session_id}' NOT FOUND in Memory! Falling back to new session.")
        else:
            print("🆕 No session_id was provided to the backend. Creating a new one.")
        
        # 2. If it fell through to here, it means it must create a new session
        new_session = self.create_session()
        print(f"✨ Created NEW session: {new_session}")
        return new_session
    
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

    def store_embedding(self, session_id, text):
        # 1. Force string type and strip spaces to guarantee a perfect match later
        session_id = str(session_id).strip()
        
        chunks = self.splitter.split_text(text)
        
        # 2. Prevent silent failures if the text is empty
        if not chunks:
            print(f"⚠️ Warning: text split into 0 chunks for session={session_id}")
            return
            
        embeddings = self.embedding_model.encode(chunks).tolist()
        
        ids = [f"{session_id}_{uuid.uuid4()}" for _ in chunks]
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=[{"session_id": session_id} for _ in chunks]
        )
        print(f"📝 Stored {len(chunks)} chunks for session={session_id}. Total in DB={self.collection.count()}")
    def retrieve_similar(self, session_id, query, top_k=5) -> list[str]:
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Count how many chunks exist for this session
        session_chunks = self.collection.get(where={"session_id": session_id})
        available = len(session_chunks["ids"])
        print(f"🔍 retrieve_similar: session={session_id}, available_chunks={available}, total_in_collection={self.collection.count()}")
        
        if available == 0:
            return []
        
        actual_top_k = min(top_k, available)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_top_k,
            where={"session_id": session_id}
        )
        
        return results["documents"][0] if results["documents"] else []
memory_manager = MemoryManager(max_messages_per_session=50)
