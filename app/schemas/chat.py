from pydantic import BaseModel
from typing import Optional
import uuid

class ChatRequest(BaseModel):
    message:str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer:str
    conversation_id:str

