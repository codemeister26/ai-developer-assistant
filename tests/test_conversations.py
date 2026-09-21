from app.config.settings import HISTORY_MESSAGE_LIMIT
from app.db import chat_repository


def test_history_limit_comes_from_settings(db):
    """Limit hardcoded 10 thi — ab settings se aati hai"""
    chat_repository.create_conversation(db, "conv-1")
    for i in range(HISTORY_MESSAGE_LIMIT + 5):
        chat_repository.add_message(db, "conv-1", "user", f"message {i}")

    messages = chat_repository.get_messages(db, "conv-1")

    assert len(messages) == HISTORY_MESSAGE_LIMIT


def test_get_all_conversations_returns_newest_first(db):
    from datetime import datetime

    older = chat_repository.create_conversation(db, "older")
    newer = chat_repository.create_conversation(db, "newer")
    older.created_at = datetime(2025, 1, 1)
    newer.created_at = datetime(2026, 1, 1)
    db.commit()

    conversations = chat_repository.get_all_conversations(db)

    assert [c.id for c in conversations] == ["newer", "older"]


def test_get_all_conversations_empty_by_default(db):
    assert chat_repository.get_all_conversations(db) == []
