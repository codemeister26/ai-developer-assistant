import pytest

from app.auth.passwords import hash_password, verify_password
from app.db import chat_repository


# ─── Password hashing ─────────────────────────────────────────────────────────

def test_hash_is_not_the_password():
    """Plain password kabhi store nahi hona chahiye"""
    stored = hash_password("correct horse battery")

    assert "correct horse battery" not in stored


def test_correct_password_verifies():
    assert verify_password("hunter2hunter2", hash_password("hunter2hunter2"))


def test_wrong_password_fails():
    assert not verify_password("wrong-password", hash_password("hunter2hunter2"))


def test_same_password_hashes_differently_each_time():
    """Salt ke bina do same passwords ek jaise dikhte, aur ek crack hone par
    dono chale jaate"""
    assert hash_password("same-password") != hash_password("same-password")


def test_garbage_stored_value_does_not_crash():
    assert verify_password("anything", "not-a-real-hash") is False
    assert verify_password("anything", "") is False


def test_unknown_algorithm_is_rejected():
    assert verify_password("x", "md5$1$aa$bb") is False


# ─── Conversation ownership ───────────────────────────────────────────────────

def test_user_cannot_see_another_users_conversation(db):
    chat_repository.create_conversation(db, "alice-chat", user_id=1)
    chat_repository.create_conversation(db, "bob-chat", user_id=2)

    assert chat_repository.get_conversation(db, "bob-chat", user_id=1) is None
    assert chat_repository.get_conversation(db, "alice-chat", user_id=1) is not None


def test_list_only_returns_your_own_conversations(db):
    chat_repository.create_conversation(db, "alice-chat", user_id=1)
    chat_repository.add_message(db, "alice-chat", "user", "alice ka sawaal")
    chat_repository.create_conversation(db, "bob-chat", user_id=2)
    chat_repository.add_message(db, "bob-chat", "user", "bob ka sawaal")

    found = chat_repository.get_all_conversations(db, user_id=1)

    assert [c.id for c in found] == ["alice-chat"]


def test_search_does_not_leak_other_users_messages(db):
    """Search content mein dhoondhti hai — yahan leak hona sabse aasaan hai"""
    chat_repository.create_conversation(db, "bob-chat", user_id=2)
    chat_repository.add_message(db, "bob-chat", "user", "bob ka secret project")

    found = chat_repository.get_all_conversations(db, search="secret", user_id=1)

    assert found == []


def test_single_user_mode_sees_everything(db):
    """Auth off (user_id None) par app pehle jaisi chalti hai"""
    chat_repository.create_conversation(db, "legacy-chat")       # user_id None
    chat_repository.create_conversation(db, "alice-chat", user_id=1)

    found = chat_repository.get_all_conversations(db)

    assert {c.id for c in found} == {"legacy-chat", "alice-chat"}


def test_conversations_made_before_auth_keep_working(db):
    """Purani conversations ka user_id None hai — wo gayab nahi honi chahiye"""
    chat_repository.create_conversation(db, "legacy-chat")

    assert chat_repository.get_conversation(db, "legacy-chat") is not None
