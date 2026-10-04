from app.llm.base import LLMError
from app.llm.factory import get_provider
from app.llm.models import DEFAULT_MODEL
from app.memory.chat_memory import get_conversation_messages, rename_conversation
import logging
import re

logger = logging.getLogger(__name__)

MAX_TITLE_LENGTH = 60

TITLE_PROMPT = """
You name chat conversations.

Reply with a title of 3 to 6 words describing what the conversation is about.
Reply with the title only — no quotes, no trailing punctuation, no preamble.
"""

# Title banane ke liye poori chat ki zarurat nahi — shuruat hi kaafi hai, aur
# isse paid models par tokens bhi bachte hain
CONTEXT_CHARS = 600


def clean_title(raw: str) -> str | None:
    """Model ke jawab ko title ke layak banao.

    Chhote models aksar quotes, "Title:" prefix ya poori line laga dete hain.
    """
    title = raw.strip().split("\n")[0].strip()
    title = re.sub(r'^(title|chat title)\s*[:\-]\s*', '', title, flags=re.I)
    title = title.strip(' "\'`*.')

    if not title:
        return None

    if len(title) > MAX_TITLE_LENGTH:
        title = title[:MAX_TITLE_LENGTH].rsplit(" ", 1)[0] + "…"

    return title


def generate_title(
    conversation_id: str,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> str | None:
    """Conversation ko chhota naam do aur save kar do. Fail ho toh None."""
    messages = get_conversation_messages(conversation_id)

    if not messages:
        return None

    excerpt = "\n".join(
        f"{m['role']}: {m['content'][:CONTEXT_CHARS]}" for m in messages[:2]
    )

    try:
        provider = get_provider(model, api_key)
        raw = "".join(
            provider.stream(
                model,
                TITLE_PROMPT,
                [{"role": "user", "content": excerpt}],
            )
        )
    except LLMError:
        # Title na bane toh koi baat nahi — pehla message title ki tarah
        # dikhta rahega
        logger.info("Title generation failed for %s", conversation_id)
        return None

    title = clean_title(raw)

    if title:
        rename_conversation(conversation_id, title)

    return title
