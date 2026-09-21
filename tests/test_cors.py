from fastapi.testclient import TestClient

from app.config.settings import CORS_ORIGINS
from app.main import app

client = TestClient(app)
ALLOWED_ORIGIN = CORS_ORIGINS[0]


def test_allowed_origin_gets_cors_header():
    response = client.get("/health", headers={"Origin": ALLOWED_ORIGIN})

    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_unknown_origin_is_not_allowed():
    response = client.get("/health", headers={"Origin": "http://evil.example.com"})

    assert "access-control-allow-origin" not in response.headers


def test_preflight_request_is_accepted():
    response = client.options(
        "/api/v1/chat",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_conversation_id_header_is_readable_by_browser():
    """Frontend ko ye header padhna hota hai — expose kiye bina wo dikhta hi nahi"""
    response = client.get("/health", headers={"Origin": ALLOWED_ORIGIN})

    assert "X-Conversation-Id" in response.headers["access-control-expose-headers"]
