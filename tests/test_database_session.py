import pytest

from app.db import database


class FakeSession:
    def __init__(self):
        self.rolled_back = False
        self.closed = False

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


@pytest.fixture
def fake_session(monkeypatch):
    session = FakeSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)
    return session


def test_session_closed_on_success(fake_session):
    with database.get_db() as db:
        assert db is fake_session

    assert fake_session.closed is True
    assert fake_session.rolled_back is False


def test_session_rolled_back_and_closed_on_error(fake_session):
    """Bina rollback ke fail hui transaction agli query ko bhi le dubti hai"""
    with pytest.raises(ValueError):
        with database.get_db() as db:
            raise ValueError("kuch toot gaya")

    assert fake_session.rolled_back is True
    assert fake_session.closed is True


def test_error_is_not_swallowed(fake_session):
    with pytest.raises(ValueError, match="kuch toot gaya"):
        with database.get_db():
            raise ValueError("kuch toot gaya")
