from sqlalchemy import Boolean, Column, Text, DateTime, String, Integer, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    # Kabhi plain password store nahi hota — ye pbkdf2 hash hai
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())

class Session(Base):
    """Opaque session tokens — JWT ke bajaye isliye ki inhe revoke kiya ja sake"""
    __tablename__ = "sessions"
    token = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True)
    # Nullable isliye — single-user mode (auth off) mein ye khaali rehta hai,
    # aur auth se pehle banayi gayi conversations bhi chalti rehti hain
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    # index isliye — conversations list hamesha isi par ORDER BY karti hai
    created_at = Column(DateTime, default=func.now(), index=True)
    # User ne rename kiya toh ye bharti hai; khaali ho toh pehle message se
    # title banta hai
    title = Column(String, nullable=True)
    pinned = Column(Boolean, nullable=False, default=False, server_default="false")

class Document(Base):
    """User ka upload kiya hua file — chat mein context ke liye"""
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    # Auth off ho toh None — conversations ki tarah hi
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    chunk_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), index=True)

class DocumentChunk(Base):
    """Document ka ek tukda aur uska embedding.

    Embedding JSON array ki tarah store hota hai. pgvector hota toh behtar
    hota, par wo extension har Postgres par maujood nahi — is scale par
    (hazaaron chunks) Python mein similarity theek chal jaati hai.
    """
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        Integer, ForeignKey("documents.id"), nullable=False, index=True
    )
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=False)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # index isliye — har chat request history is column pe filter karti hai.
    # Postgres foreign key pe apne aap index nahi banata.
    conversation_id = Column(String, ForeignKey("conversations.id"), index=True)
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=func.now())
