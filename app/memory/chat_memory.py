from app.config.settings import HISTORY_CHAR_BUDGET
from app.db.database import get_db
from app.db import chat_repository
import logging

logger = logging.getLogger(__name__)

def trim_to_budget(messages: list, budget: int = HISTORY_CHAR_BUDGET) -> list:
    """Newest se peeche chalte hue jitne messages budget mein aate hain utne rakho.

    Message beech se nahi kaatte — aadha message LLM ko confuse karta hai.
    Ek hi message budget se bada ho toh use rakhte hain, warna user ka abhi
    bheja hua sawaal hi gayab ho jayega.
    """
    kept = []
    used = 0

    for message in reversed(messages):
        size = len(message["content"])

        if kept and used + size > budget:
            break

        kept.append(message)
        used += size

    kept.reverse()

    # Anthropic pehla message "user" hi maangta hai — trim ke baad agar assistant
    # aage aa gaya toh use hata do, warna API request reject kar degi
    while kept and kept[0]["role"] != "user":
        kept.pop(0)

    if len(kept) < len(messages):
        logger.info(
            "History trimmed: %d of %d messages sent (%d chars)",
            len(kept), len(messages), used,
        )

    return kept

def get_history(conversation_id : str) -> list:
    """Conversation ki history LLM ke format mein do (context budget ke andar)"""
    with get_db() as db:
        messages = chat_repository.get_messages(db, conversation_id)

        return trim_to_budget([
            { "role":msg.role, "content": msg.content }
            for msg in messages
        ])

def add_message(conversation_id:str, role:str, content:str):
    with get_db() as db:
        conversation = chat_repository.get_conversation(db, conversation_id)
        if not conversation:
            chat_repository.create_conversation(db, conversation_id)

        chat_repository.add_message(db, conversation_id, role, content)

def truncate_from(conversation_id: str, message_id: int) -> int:
    """Is message se aage ka sab hatao. Returns kitne delete hue."""
    with get_db() as db:
        return chat_repository.delete_messages_from(db, conversation_id, message_id)

def drop_last_assistant_message(conversation_id: str) -> bool:
    """Regenerate se pehle purana jawab hatao"""
    with get_db() as db:
        return chat_repository.delete_trailing_assistant_message(db, conversation_id)

def get_conversation_messages(conversation_id: str):
    """Conversation ke saare messages (UI ke liye, sirf last N nahi).

    None return karta hai agar conversation hi exist nahi karti — taaki caller
    khaali conversation aur missing conversation mein farak kar sake.
    """
    with get_db() as db:
        if chat_repository.get_conversation(db, conversation_id) is None:
            return None

        messages = chat_repository.get_messages(db, conversation_id, limit=None)

        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at,
            }
            for msg in messages
        ]

def list_conversations() -> list:
    """Saari conversations ki summary — newest pehle"""
    with get_db() as db:
        conversations = chat_repository.get_all_conversations(db)

        return [
            {
                "conversation_id": c.id,
                "created_at": c.created_at,
                "title": c.title,
            }
            for c in conversations
        ]

def clear_history(conversation_id: str) -> bool:
    """Conversation ki poori history permanently delete karo. Returns True agar conversation mili"""
    with get_db() as db:
        return chat_repository.delete_conversation(db, conversation_id)
