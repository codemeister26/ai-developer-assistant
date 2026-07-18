from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest
from app.services.chat_service import get_ai_response_stream

router = APIRouter(prefix="/api/v1", tags=["Chat"])

@router.post("/chat")
def chat(request: ChatRequest):            
    return StreamingResponse(
        get_ai_response_stream(
           message= request.message,
           conversation_id=request.conversation_id),
        media_type="text/plain"
    )