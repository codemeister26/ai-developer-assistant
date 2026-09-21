from app.config.settings import HISTORY_MESSAGE_LIMIT
from app.db import chat_repository


def test_all_messages_returned_not_just_history_limit(db):
    """UI ko poori chat chahiye, sirf LLM wali last N nahi"""
    total = HISTORY_MESSAGE_LIMIT + 5
    chat_repository.create_conversation(db, "conv-1")
    for i in range(total):
        chat_repository.add_message(db, "conv-1", "user", f"message {i}")

    messages = chat_repository.get_messages(db, "conv-1", limit=None)

    assert len(messages) == total
    assert messages[0].content == "message 0"


def test_messages_stay_in_chronological_order(db):
    chat_repository.create_conversation(db, "conv-1")
    chat_repository.add_message(db, "conv-1", "user", "sawaal")
    chat_repository.add_message(db, "conv-1", "assistant", "jawaab")

    messages = chat_repository.get_messages(db, "conv-1", limit=None)

    assert [m.role for m in messages] == ["user", "assistant"]
