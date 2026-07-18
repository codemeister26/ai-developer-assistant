from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest
from app.services.chat_service import get_ai_response_stream

router = APIRouter(prefix="/api/v1", tags=["Chat"])

@router.post("/chat")
def chat(request: ChatRequest):              # async nahi, sync def ✅
    return StreamingResponse(
        get_ai_response_stream(request.message),
        media_type="text/plain"
    )