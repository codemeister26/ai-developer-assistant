from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from app.llm.models import MODELS
from app.schemas.chat import (
    ChatRequest,
    ConversationSummary,
    MessageOut,
    ModelOut,
    RegenerateRequest,
)
from app.services.chat_service import get_ai_response_stream, regenerate_response_stream
from app.memory.chat_memory import (
    clear_history,
    get_conversation_messages,
    list_conversations,
    truncate_from,
)
from typing import List
import uuid

router = APIRouter(prefix="/api/v1", tags=["Chat"])

@router.post("/chat")
def chat(
    request: ChatRequest,
    # Key header mein aati hai, body mein nahi — body log ya save ho sakti hai.
    # Server ise kabhi store nahi karta, sirf is request ke liye use karta hai.
    x_llm_api_key: str | None = Header(default=None),
):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    return StreamingResponse(
        get_ai_response_stream(
           message=request.message,
           conversation_id=conversation_id,
           mode=request.mode.value,
           model=request.model,
           api_key=x_llm_api_key),
        media_type="text/plain",
        headers={"X-Conversation-Id": conversation_id}
    )

@router.post("/chat/{conversation_id}/regenerate")
def regenerate(
    conversation_id: str,
    request: RegenerateRequest,
    x_llm_api_key: str | None = Header(default=None),
):
    """Aakhri jawab hatao aur naya banao — wahi sawaal, dobara"""
    if get_conversation_messages(conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return StreamingResponse(
        regenerate_response_stream(
            conversation_id=conversation_id,
            mode=request.mode.value,
            model=request.model,
            api_key=x_llm_api_key),
        media_type="text/plain",
        headers={"X-Conversation-Id": conversation_id}
    )

@router.delete("/chat/{conversation_id}/messages/{message_id}")
def truncate_conversation(conversation_id: str, message_id: int):
    """Is message ko aur uske baad ke sabko hatao — edit-and-resend ke liye"""
    if get_conversation_messages(conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    deleted = truncate_from(conversation_id, message_id)
    return {"deleted": deleted}

@router.get("/models", response_model=List[ModelOut])
def get_models():
    """Kaun se models available hain — dropdown yahi list use karta hai"""
    return MODELS

@router.get("/conversations", response_model=List[ConversationSummary])
def get_conversations():
    """Saari conversations list karo — newest pehle"""
    return list_conversations()

@router.get("/chat/{conversation_id}", response_model=List[MessageOut])
def get_chat(conversation_id: str):
    """Ek conversation ke saare messages — purani chat dobara kholne ke liye"""
    messages = get_conversation_messages(conversation_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return messages

@router.delete("/chat/{conversation_id}")
def delete_chat(conversation_id: str):
    deleted = clear_history(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted", "conversation_id": conversation_id}