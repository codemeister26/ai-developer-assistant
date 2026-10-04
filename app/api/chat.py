from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.api.auth import current_user
from app.api.rate_limit import rate_limit
from app.api.sse import SSE_HEADERS, to_sse
from app.config.settings import CONVERSATION_PAGE_SIZE
from app.llm.models import MODELS
from app.schemas.chat import (
    ChatRequest,
    ConversationSummary,
    MessageOut,
    ModelOut,
    PinRequest,
    RegenerateRequest,
    RenameRequest,
)
from app.services.chat_service import get_ai_response_stream, regenerate_response_stream
from app.services.title_service import generate_title
from app.memory.chat_memory import (
    clear_history,
    get_conversation_messages,
    list_conversations,
    rename_conversation,
    set_pinned,
    truncate_from,
)
from typing import List
import uuid

router = APIRouter(prefix="/api/v1", tags=["Chat"])

@router.post("/chat", dependencies=[Depends(rate_limit)])
def chat(
    request: ChatRequest,
    # Key header mein aati hai, body mein nahi — body log ya save ho sakti hai.
    # Server ise kabhi store nahi karta, sirf is request ke liye use karta hai.
    x_llm_api_key: str | None = Header(default=None),
    user: dict | None = Depends(current_user),
):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    return StreamingResponse(
        to_sse(get_ai_response_stream(
           message=request.message,
           conversation_id=conversation_id,
           mode=request.mode.value,
           model=request.model,
           api_key=x_llm_api_key,
           user_id=_uid(user))),
        media_type="text/event-stream",
        headers={**SSE_HEADERS, "X-Conversation-Id": conversation_id}
    )

@router.post("/chat/{conversation_id}/regenerate", dependencies=[Depends(rate_limit)])
def regenerate(
    conversation_id: str,
    request: RegenerateRequest,
    x_llm_api_key: str | None = Header(default=None),
    user: dict | None = Depends(current_user),
):
    """Aakhri jawab hatao aur naya banao — wahi sawaal, dobara"""
    if get_conversation_messages(conversation_id, _uid(user)) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return StreamingResponse(
        to_sse(regenerate_response_stream(
            conversation_id=conversation_id,
            mode=request.mode.value,
            model=request.model,
            api_key=x_llm_api_key)),
        media_type="text/event-stream",
        headers={**SSE_HEADERS, "X-Conversation-Id": conversation_id}
    )

@router.delete("/chat/{conversation_id}/messages/{message_id}")
def truncate_conversation(
    conversation_id: str,
    message_id: int,
    user: dict | None = Depends(current_user),
):
    """Is message ko aur uske baad ke sabko hatao — edit-and-resend ke liye"""
    if get_conversation_messages(conversation_id, _uid(user)) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    deleted = truncate_from(conversation_id, message_id)
    return {"deleted": deleted}

@router.get("/models", response_model=List[ModelOut])
def get_models():
    """Kaun se models available hain — dropdown yahi list use karta hai"""
    return MODELS

@router.get("/conversations", response_model=List[ConversationSummary])
def get_conversations(
    search: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=CONVERSATION_PAGE_SIZE, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: dict | None = Depends(current_user),
):
    """Conversations list karo — pinned pehle, phir newest.

    search title aur message content dono mein dhoondhta hai.
    """
    return list_conversations(search=search, limit=limit, offset=offset, user_id=_uid(user))

@router.patch("/conversations/{conversation_id}", response_model=ConversationSummary)
def rename(
    conversation_id: str,
    request: RenameRequest,
    user: dict | None = Depends(current_user),
):
    """Conversation ka naam badlo. title null bhejo toh auto-title wapas aa jaata hai."""
    title = request.title.strip() if request.title else None

    if not rename_conversation(conversation_id, title or None, _uid(user)):
        raise HTTPException(status_code=404, detail="Conversation not found")

    return _summary_for(conversation_id, _uid(user))

@router.post(
    "/conversations/{conversation_id}/title",
    response_model=ConversationSummary,
    dependencies=[Depends(rate_limit)],
)
def auto_title(
    conversation_id: str,
    request: RegenerateRequest,
    x_llm_api_key: str | None = Header(default=None),
    user: dict | None = Depends(current_user),
):
    """Chat ko chhota naam do (LLM se).

    Alag endpoint isliye hai taaki ye extra call streaming ko dheema na kare.
    Fail ho jaye toh bhi 200 — title na banna koi error nahi, pehla message
    title ki tarah dikhta rehta hai.
    """
    if get_conversation_messages(conversation_id, _uid(user)) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    generate_title(conversation_id, request.model, x_llm_api_key)
    return _summary_for(conversation_id, _uid(user))

@router.patch("/conversations/{conversation_id}/pin", response_model=ConversationSummary)
def pin(
    conversation_id: str,
    request: PinRequest,
    user: dict | None = Depends(current_user),
):
    if not set_pinned(conversation_id, request.pinned, _uid(user)):
        raise HTTPException(status_code=404, detail="Conversation not found")

    return _summary_for(conversation_id, _uid(user))

def _uid(user: dict | None) -> int | None:
    return user["id"] if user else None

def _summary_for(conversation_id: str, user_id: int | None = None):
    """Update ke baad wapas bheji jaane wali summary"""
    for summary in list_conversations(user_id=user_id):
        if summary["conversation_id"] == conversation_id:
            return summary

    raise HTTPException(status_code=404, detail="Conversation not found")

@router.get("/chat/{conversation_id}", response_model=List[MessageOut])
def get_chat(conversation_id: str, user: dict | None = Depends(current_user)):
    """Ek conversation ke saare messages — purani chat dobara kholne ke liye"""
    messages = get_conversation_messages(conversation_id, _uid(user))
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return messages

@router.delete("/chat/{conversation_id}")
def delete_chat(conversation_id: str, user: dict | None = Depends(current_user)):
    deleted = clear_history(conversation_id, _uid(user))
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted", "conversation_id": conversation_id}