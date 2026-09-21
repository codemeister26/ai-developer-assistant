from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, ConversationSummary
from app.services.chat_service import get_ai_response_stream
from app.memory.chat_memory import clear_history, list_conversations
from typing import List
import uuid

router = APIRouter(prefix="/api/v1", tags=["Chat"])

@router.post("/chat")
def chat(request: ChatRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    return StreamingResponse(
        get_ai_response_stream(
           message=request.message,
           conversation_id=conversation_id),
        media_type="text/plain",
        headers={"X-Conversation-Id": conversation_id}
    )

@router.get("/conversations", response_model=List[ConversationSummary])
def get_conversations():
    """Saari conversations list karo — newest pehle"""
    return list_conversations()

@router.delete("/chat/{conversation_id}")
def delete_chat(conversation_id: str):
    deleted = clear_history(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted", "conversation_id": conversation_id}