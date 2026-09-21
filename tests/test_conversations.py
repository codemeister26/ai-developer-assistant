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


def test_title_is_the_first_user_message(db):
    """Sidebar mein id ke bajaye pehla sawaal dikhna chahiye"""
    chat_repository.create_conversation(db, "conv-1")
    chat_repository.add_message(db, "conv-1", "user", "how do I index a column?")
    chat_repository.add_message(db, "conv-1", "assistant", "use index=True")
    chat_repository.add_message(db, "conv-1", "user", "baad wala sawaal")

    conversation = chat_repository.get_all_conversations(db)[0]

    assert conversation.title == "how do I index a column?"


def test_title_ignores_assistant_messages(db):
    chat_repository.create_conversation(db, "conv-1")
    chat_repository.add_message(db, "conv-1", "assistant", "assistant pehle bola")
    chat_repository.add_message(db, "conv-1", "user", "user ka sawaal")

    assert chat_repository.get_all_conversations(db)[0].title == "user ka sawaal"


def test_title_is_none_for_empty_conversation(db):
    chat_repository.create_conversation(db, "conv-1")

    assert chat_repository.get_all_conversations(db)[0].title is None


def test_each_conversation_gets_its_own_title(db):
    chat_repository.create_conversation(db, "conv-1")
    chat_repository.create_conversation(db, "conv-2")
    chat_repository.add_message(db, "conv-1", "user", "pehli chat")
    chat_repository.add_message(db, "conv-2", "user", "doosri chat")

    titles = {c.id: c.title for c in chat_repository.get_all_conversations(db)}

    assert titles == {"conv-1": "pehli chat", "conv-2": "doosri chat"}
