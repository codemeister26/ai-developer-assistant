from app.config.prompts import get_prompt
from app.llm.base import LLMAuthError, LLMUnavailableError
from app.llm.factory import get_provider
from app.llm.models import DEFAULT_MODEL, cost_of
from app.memory.chat_memory import add_message, drop_last_assistant_message, get_history
from app.rag.documents import build_context
from app.rag.embeddings import EmbeddingError
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
    user_id: int | None = None,
) -> Generator[dict, None, None]:
    # user_id sirf yahan chahiye — nayi conversation isi ke naam par banti hai
    add_message(
        conversation_id=conversation_id,
        role="user",
        content=message,
        user_id=user_id,
    )
    yield from _stream_reply(conversation_id, mode, model, api_key, question=message, user_id=user_id)


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
    question: str | None = None,
    user_id: int | None = None,
) -> Generator[dict, None, None]:
    """Typed events yield karta hai, raw text nahi.

    Isse error ab jawab ke beech mein text ki tarah nahi jaata — frontend use
    alag se dikha sakta hai, aur baad mein token count jaisi cheezein bhejna
    bhi aasaan rahega.
    """
    history = get_history(conversation_id)
    full_response = ""

    try:
        provider = get_provider(model, api_key)

        for chunk in provider.stream(model, _system_prompt(mode, question, user_id), history):
            full_response += chunk
            yield {"type": "token", "text": chunk}

    except LLMAuthError:
        # Ye user khud theek kar sakta hai — isliye alag kind
        yield {"type": "error", "kind": "auth", "message": AI_AUTH_MESSAGE}

    except LLMUnavailableError:
        yield {"type": "error", "kind": "unavailable", "message": AI_UNAVAILABLE_MESSAGE}

    else:
        done = {
            "type": "done",
            "conversation_id": conversation_id,
            "chars": len(full_response),
        }

        # Provider stream khatam hone par usage bharta hai. Na mile toh event
        # usage ke bina jaata hai — UI bas kuch nahi dikhayega.
        if provider.usage:
            done["usage"] = {
                **provider.usage,
                "cost_usd": cost_of(
                    model,
                    provider.usage["input_tokens"],
                    provider.usage["output_tokens"],
                ),
            }

        yield done

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


def _system_prompt(mode: str, question: str | None, user_id: int | None) -> str:
    """Mode ka prompt, aur agar upload kiye documents mein jawab ho toh wo bhi.

    Documents na hon ya embedding model band ho toh chat normal chalti rehti
    hai — RAG ek bonus hai, zaroorat nahi.
    """
    prompt = get_prompt(mode)

    if not question:
        return prompt

    try:
        return prompt + build_context(question, user_id)
    except EmbeddingError:
        logger.info("Skipping document context — embedding model unavailable")
        return prompt
