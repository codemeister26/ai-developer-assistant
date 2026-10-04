from sqlalchemy import Boolean, Column, Text, DateTime, String, Integer, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True)
    # index isliye — conversations list hamesha isi par ORDER BY karti hai
    created_at = Column(DateTime, default=func.now(), index=True)
    # User ne rename kiya toh ye bharti hai; khaali ho toh pehle message se
    # title banta hai
    title = Column(String, nullable=True)
    pinned = Column(Boolean, nullable=False, default=False, server_default="false")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # index isliye — har chat request history is column pe filter karti hai.
    # Postgres foreign key pe apne aap index nahi banata.
    conversation_id = Column(String, ForeignKey("conversations.id"), index=True)
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=func.now())
