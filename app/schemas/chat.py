from pydantic import BaseModel, Field, field_validator
from app.config.settings import MAX_MESSAGE_LENGTH
from typing import Optional
import uuid

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=MAX_MESSAGE_LENGTH)
    conversation_id: Optional[str] = None

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
