from app.llm.ollama_client import generate_response_stream, LLMUnavailableError
from app.memory.chat_memory import get_history, add_message
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# User ko dikhne wala fallback — ye kabhi history mein save nahi hota
AI_UNAVAILABLE_MESSAGE = "AI service is currently unavailable."

def get_ai_response_stream(message: str, conversation_id: str) -> Generator[str, None, None]:
    add_message(conversation_id=conversation_id, role="user", content=message)

    history = get_history(conversation_id)
    full_response = ""

    try:
        for chunk in generate_response_stream(history):   # normal for ✅
            full_response += chunk
            yield chunk

    except LLMUnavailableError:
        # Sirf user ko batao — save kuch nahi karte, warna agli baar ye error
        # LLM ko context ki tarah wapas chala jaayega
        yield AI_UNAVAILABLE_MESSAGE

    finally:
        # finally isliye — client beech mein disconnect ho jaaye tab bhi jitna
        # jawab bana tha wo history mein save ho jaata hai
        if full_response:
            add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response
            )
        else:
            logger.warning(
                "No assistant response saved for conversation %s", conversation_id
            )
