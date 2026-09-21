from app.db.database import get_db
from app.db import chat_repository

def get_history(conversation_id : str) -> list:
    """Conversation ki history LLM ke format mein do"""
    with get_db() as db:
        messages = chat_repository.get_messages(db, conversation_id)

        return [
            { "role":msg.role, "content": msg.content }
            for msg in messages
        ]

def add_message(conversation_id:str, role:str, content:str):
    with get_db() as db:
        conversation = chat_repository.get_conversation(db, conversation_id)
        if not conversation:
            chat_repository.create_conversation(db, conversation_id)

        chat_repository.add_message(db, conversation_id, role, content)

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
            { "role": msg.role, "content": msg.content, "created_at": msg.created_at }
            for msg in messages
        ]

def list_conversations() -> list:
    """Saari conversations ki summary — newest pehle"""
    with get_db() as db:
        conversations = chat_repository.get_all_conversations(db)

        return [
            { "conversation_id": c.id, "created_at": c.created_at }
            for c in conversations
        ]

def clear_history(conversation_id: str) -> bool:
    """Conversation ki poori history permanently delete karo. Returns True agar conversation mili"""
    with get_db() as db:
        return chat_repository.delete_conversation(db, conversation_id)
