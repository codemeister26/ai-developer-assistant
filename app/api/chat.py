from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest
from app.services.chat_service import get_ai_response_stream
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