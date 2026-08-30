from app.db.database import SessionLocal
from app.db import chat_repository

def get_history(conversation_id : str) -> list:
    """Conversation ki history LLM ke format mein do"""
    db = SessionLocal()

    try:
        messages = chat_repository.get_messages(db, conversation_id)

        return [
            { "role":msg.role, "content": msg.content }
            for msg in messages
        ]
    finally:
        db.close()

def add_message(conversation_id:str, role:str, content:str):
    db=SessionLocal()

    try:
        conversation = chat_repository.get_conversation(db, conversation_id)
        if not conversation:
            chat_repository.create_conversation(db, conversation_id)

        chat_repository.add_message(db, conversation_id, role, content)

    finally:
        db.close()

def clear_history(conversation_id: str) -> bool:
    """Conversation ki poori history permanently delete karo. Returns True agar conversation mili"""
    db = SessionLocal()

    try:
        return chat_repository.delete_conversation(db, conversation_id)
    finally:
        db.close()
