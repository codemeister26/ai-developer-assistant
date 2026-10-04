from datetime import datetime

from app.db import chat_repository


def make_chat(db, conversation_id, first_question, created_at=None):
    conversation = chat_repository.create_conversation(db, conversation_id)
    chat_repository.add_message(db, conversation_id, "user", first_question)

    if created_at:
        conversation.created_at = created_at
        db.commit()

    return conversation


# ─── Rename ───────────────────────────────────────────────────────────────────

def test_rename_overrides_the_auto_title(db):
    make_chat(db, "conv-1", "how do I index a column?")

    assert chat_repository.rename_conversation(db, "conv-1", "DB notes") is True
    assert chat_repository.get_all_conversations(db)[0].title == "DB notes"


def test_clearing_the_name_brings_back_the_auto_title(db):
    make_chat(db, "conv-1", "how do I index a column?")
    chat_repository.rename_conversation(db, "conv-1", "DB notes")

    chat_repository.rename_conversation(db, "conv-1", None)

    assert chat_repository.get_all_conversations(db)[0].title == "how do I index a column?"


def test_rename_unknown_conversation_returns_false(db):
    assert chat_repository.rename_conversation(db, "missing", "x") is False


# ─── Pin ──────────────────────────────────────────────────────────────────────

def test_pinned_conversations_come_first(db):
    make_chat(db, "old-pinned", "purana", created_at=datetime(2025, 1, 1))
    make_chat(db, "new-normal", "naya", created_at=datetime(2026, 1, 1))

    chat_repository.set_pinned(db, "old-pinned", True)

    assert [c.id for c in chat_repository.get_all_conversations(db)] == [
        "old-pinned",
        "new-normal",
    ]


def test_unpinning_restores_date_order(db):
    make_chat(db, "old-pinned", "purana", created_at=datetime(2025, 1, 1))
    make_chat(db, "new-normal", "naya", created_at=datetime(2026, 1, 1))
    chat_repository.set_pinned(db, "old-pinned", True)

    chat_repository.set_pinned(db, "old-pinned", False)

    assert [c.id for c in chat_repository.get_all_conversations(db)] == [
        "new-normal",
        "old-pinned",
    ]


def test_new_conversations_are_not_pinned(db):
    make_chat(db, "conv-1", "hello")

    assert chat_repository.get_all_conversations(db)[0].pinned is False


# ─── Search ───────────────────────────────────────────────────────────────────

def test_search_finds_text_inside_messages(db):
    make_chat(db, "conv-1", "tell me about postgres indexes")
    make_chat(db, "conv-2", "how does react state work")

    found = chat_repository.get_all_conversations(db, search="postgres")

    assert [c.id for c in found] == ["conv-1"]


def test_search_finds_a_renamed_conversation_by_its_new_name(db):
    make_chat(db, "conv-1", "kuch bhi")
    chat_repository.rename_conversation(db, "conv-1", "Deployment notes")

    assert [c.id for c in chat_repository.get_all_conversations(db, search="deploy")] == [
        "conv-1"
    ]


def test_search_ignores_case(db):
    make_chat(db, "conv-1", "Tell me about POSTGRES")

    assert len(chat_repository.get_all_conversations(db, search="postgres")) == 1


def test_search_matches_any_message_not_just_the_first(db):
    """Baad wale message mein mila toh bhi conversation milni chahiye"""
    make_chat(db, "conv-1", "pehla sawaal")
    chat_repository.add_message(db, "conv-1", "user", "alembic migration kaise likhun")

    assert len(chat_repository.get_all_conversations(db, search="alembic")) == 1


def test_search_with_no_match_returns_nothing(db):
    make_chat(db, "conv-1", "hello")

    assert chat_repository.get_all_conversations(db, search="zzzz") == []


# ─── Pagination ───────────────────────────────────────────────────────────────

def test_limit_caps_the_number_returned(db):
    for i in range(5):
        make_chat(db, f"conv-{i}", f"q{i}", created_at=datetime(2026, 1, i + 1))

    assert len(chat_repository.get_all_conversations(db, limit=2)) == 2


def test_offset_moves_to_the_next_page(db):
    for i in range(5):
        make_chat(db, f"conv-{i}", f"q{i}", created_at=datetime(2026, 1, i + 1))

    page1 = chat_repository.get_all_conversations(db, limit=2, offset=0)
    page2 = chat_repository.get_all_conversations(db, limit=2, offset=2)

    assert {c.id for c in page1}.isdisjoint({c.id for c in page2})
