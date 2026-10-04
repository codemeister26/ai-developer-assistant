import pytest
from fastapi import HTTPException

from app.api import rate_limit as limiter


class FakeRequest:
    def __init__(self, host="1.2.3.4"):
        self.client = type("Client", (), {"host": host})()


@pytest.fixture(autouse=True)
def clean_state():
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def small_limit(monkeypatch):
    monkeypatch.setattr(limiter, "RATE_LIMIT_REQUESTS", 3)
    monkeypatch.setattr(limiter, "RATE_LIMIT_WINDOW", 60)


def test_requests_under_the_limit_pass(small_limit):
    request = FakeRequest()

    for _ in range(3):
        limiter.rate_limit(request)


def test_request_over_the_limit_is_rejected(small_limit):
    request = FakeRequest()
    for _ in range(3):
        limiter.rate_limit(request)

    with pytest.raises(HTTPException) as caught:
        limiter.rate_limit(request)

    assert caught.value.status_code == 429


def test_rejection_tells_the_client_when_to_retry(small_limit):
    request = FakeRequest()
    for _ in range(3):
        limiter.rate_limit(request)

    with pytest.raises(HTTPException) as caught:
        limiter.rate_limit(request)

    assert int(caught.value.headers["Retry-After"]) > 0


def test_clients_are_counted_separately(small_limit):
    """Ek banda limit cross kare toh baaki sab block nahi hone chahiye"""
    for _ in range(3):
        limiter.rate_limit(FakeRequest("1.1.1.1"))

    limiter.rate_limit(FakeRequest("2.2.2.2"))


def test_old_hits_fall_out_of_the_window(monkeypatch):
    monkeypatch.setattr(limiter, "RATE_LIMIT_REQUESTS", 2)
    monkeypatch.setattr(limiter, "RATE_LIMIT_WINDOW", 60)

    clock = [1000.0]
    monkeypatch.setattr(limiter.time, "monotonic", lambda: clock[0])

    request = FakeRequest()
    limiter.rate_limit(request)
    limiter.rate_limit(request)

    clock[0] += 61          # window nikal gayi
    limiter.rate_limit(request)


def test_limit_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(limiter, "RATE_LIMIT_REQUESTS", 0)
    request = FakeRequest()

    for _ in range(50):
        limiter.rate_limit(request)
