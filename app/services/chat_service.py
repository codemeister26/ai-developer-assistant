from app.config.prompts import get_prompt
from app.llm.base import LLMAuthError, LLMUnavailableError
from app.llm.factory import get_provider
from app.llm.models import DEFAULT_MODEL
from app.memory.chat_memory import add_message, drop_last_assistant_message, get_history
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# User ko dikhne wale fallbacks — ye kabhi history mein save nahi hote
AI_UNAVAILABLE_MESSAGE = "AI service is currently unavailable."
AI_AUTH_MESSAGE = "Check your API key in Settings — the provider rejected it."

def get_ai_response_stream(
    message: str,
    conversation_id: str,
    mode: str = "general",
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> Generator[str, None, None]:
    add_message(conversation_id=conversation_id, role="user", content=message)
    yield from _stream_reply(conversation_id, mode, model, api_key)


def regenerate_response_stream(
    conversation_id: str,
    mode: str = "general",
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> Generator[str, None, None]:
    """Purana jawab hatao aur wahi sawaal dobara bhejo.

    User ka message dobara add nahi hota — wo pehle se history mein hai.
    """
    drop_last_assistant_message(conversation_id)
    yield from _stream_reply(conversation_id, mode, model, api_key)


def _stream_reply(
    conversation_id: str,
    mode: str,
    model: str,
    api_key: str | None,
) -> Generator[str, None, None]:
    history = get_history(conversation_id)
    full_response = ""

    # Kuch stream hua ya nahi — error hone par isse pata chalta hai ki backend ne
    # kuch save kiya ya request pehle hi reject ho gayi
    received_anything = False

    try:
        provider = get_provider(model, api_key)

        for chunk in provider.stream(model, get_prompt(mode), history):
            received_anything = True
            full_response += chunk
            yield chunk

    except LLMAuthError:
        # Ye user khud theek kar sakta hai — isliye alag message
        yield AI_AUTH_MESSAGE

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
        elif not received_anything:
            logger.warning(
                "No assistant response saved for conversation %s", conversation_id
            )
