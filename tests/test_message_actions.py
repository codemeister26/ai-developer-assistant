from app.db import chat_repository


def build_chat(db, conversation_id="conv-1"):
    chat_repository.create_conversation(db, conversation_id)
    chat_repository.add_message(db, conversation_id, "user", "q1")
    chat_repository.add_message(db, conversation_id, "assistant", "a1")
    chat_repository.add_message(db, conversation_id, "user", "q2")
    chat_repository.add_message(db, conversation_id, "assistant", "a2")
    return chat_repository.get_messages(db, conversation_id, limit=None)


# ─── Regenerate ───────────────────────────────────────────────────────────────

def test_regenerate_drops_only_the_last_assistant_message(db):
    build_chat(db)

    assert chat_repository.delete_trailing_assistant_message(db, "conv-1") is True

    remaining = chat_repository.get_messages(db, "conv-1", limit=None)
    assert [(m.role, m.content) for m in remaining] == [
        ("user", "q1"),
        ("assistant", "a1"),
        ("user", "q2"),
    ]


def test_regenerate_does_nothing_when_last_message_is_from_user(db):
    """User ka sawaal kabhi delete nahi hona chahiye"""
    chat_repository.create_conversation(db, "conv-1")
    chat_repository.add_message(db, "conv-1", "user", "q1")

    assert chat_repository.delete_trailing_assistant_message(db, "conv-1") is False
    assert len(chat_repository.get_messages(db, "conv-1", limit=None)) == 1


def test_regenerate_on_empty_conversation_is_safe(db):
    chat_repository.create_conversation(db, "conv-1")

    assert chat_repository.delete_trailing_assistant_message(db, "conv-1") is False


# ─── Edit and resend (truncate) ───────────────────────────────────────────────

def test_truncate_removes_the_message_and_everything_after(db):
    messages = build_chat(db)
    second_question = messages[2]

    deleted = chat_repository.delete_messages_from(db, "conv-1", second_question.id)

    assert deleted == 2
    remaining = chat_repository.get_messages(db, "conv-1", limit=None)
    assert [(m.role, m.content) for m in remaining] == [
        ("user", "q1"),
        ("assistant", "a1"),
    ]


def test_truncate_from_first_message_clears_the_chat(db):
    messages = build_chat(db)

    chat_repository.delete_messages_from(db, "conv-1", messages[0].id)

    assert chat_repository.get_messages(db, "conv-1", limit=None) == []


def test_truncate_does_not_touch_other_conversations(db):
    messages = build_chat(db, "conv-1")
    build_chat(db, "conv-2")

    chat_repository.delete_messages_from(db, "conv-1", messages[0].id)

    assert len(chat_repository.get_messages(db, "conv-2", limit=None)) == 4
