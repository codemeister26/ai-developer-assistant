from app.db import chat_repository


def test_create_and_get_conversation(db):
    chat_repository.create_conversation(db, "conv-1")

    assert chat_repository.get_conversation(db, "conv-1") is not None
    assert chat_repository.get_conversation(db, "missing") is None


def test_add_and_get_messages_in_order(db):
    chat_repository.create_conversation(db, "conv-1")
    chat_repository.add_message(db, "conv-1", "user", "first")
    chat_repository.add_message(db, "conv-1", "assistant", "second")

    messages = chat_repository.get_messages(db, "conv-1")

    assert [(m.role, m.content) for m in messages] == [
        ("user", "first"),
        ("assistant", "second"),
    ]


def test_get_messages_returns_newest_within_limit_oldest_first(db):
    """Limit newest messages leta hai, par LLM ko chronological order chahiye"""
    chat_repository.create_conversation(db, "conv-1")
    for i in range(5):
        chat_repository.add_message(db, "conv-1", "user", f"message {i}")

    messages = chat_repository.get_messages(db, "conv-1", limit=3)

    assert [m.content for m in messages] == ["message 2", "message 3", "message 4"]


def test_messages_are_scoped_to_their_conversation(db):
    chat_repository.create_conversation(db, "conv-1")
    chat_repository.create_conversation(db, "conv-2")
    chat_repository.add_message(db, "conv-1", "user", "belongs to one")
    chat_repository.add_message(db, "conv-2", "user", "belongs to two")

    messages = chat_repository.get_messages(db, "conv-1")

    assert [m.content for m in messages] == ["belongs to one"]


def test_delete_conversation_removes_its_messages(db):
    chat_repository.create_conversation(db, "conv-1")
    chat_repository.add_message(db, "conv-1", "user", "hello")

    assert chat_repository.delete_conversation(db, "conv-1") is True
    assert chat_repository.get_conversation(db, "conv-1") is None
    assert chat_repository.get_messages(db, "conv-1") == []


def test_delete_unknown_conversation_returns_false(db):
    assert chat_repository.delete_conversation(db, "missing") is False
