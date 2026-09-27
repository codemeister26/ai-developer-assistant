from pydantic import BaseModel, Field, field_validator
from app.config.settings import MAX_MESSAGE_LENGTH
from app.llm.models import DEFAULT_MODEL
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid

class ChatMode(str, Enum):
    """Kis tarah ka jawab chahiye — har mode ka apna system prompt hai"""
    GENERAL = "general"
    CODE_REVIEW = "code_review"
    DEBUG = "debug"
    EXPLAIN = "explain"
    ARCHITECTURE = "architecture"
    CODE_WRITING = "code_writing"

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=MAX_MESSAGE_LENGTH)
    conversation_id: Optional[str] = None
    mode: ChatMode = ChatMode.GENERAL
    # API key request body mein nahi aati — wo X-LLM-Api-Key header se aati hai,
    # taaki galti se kisi log ya saved payload mein na chali jaye
    model: str = DEFAULT_MODEL

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        """Khaali ya sirf spaces wala message reject karo — LLM call waste na ho"""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message cannot be empty")
        return cleaned

    @field_validator("conversation_id")
    @classmethod
    def conversation_id_must_be_uuid(cls, value: Optional[str]) -> Optional[str]:
        """Server hamesha UUID hi deta hai — junk IDs se fake conversations na banein"""
        if value is None:
            return value
        try:
            uuid.UUID(value)
        except ValueError:
            raise ValueError("conversation_id must be a valid UUID")
        return value

class ChatResponse(BaseModel):
    answer:str
    conversation_id:str

class ConversationSummary(BaseModel):
    conversation_id: str
    created_at: datetime
    title: Optional[str] = None   # pehla user message; khaali conversation mein None

class MessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

class ModelOut(BaseModel):
    id: str
    label: str
    provider: str
    needs_key: bool
    note: str
