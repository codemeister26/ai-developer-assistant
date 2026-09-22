import uuid

import pytest

from app.llm.ollama_client import LLMUnavailableError
from app.services import chat_service
from app.services.chat_service import AI_UNAVAILABLE_MESSAGE, get_ai_response_stream


@pytest.fixture
def saved(monkeypatch):
    """add_message ko intercept karke dekho ki history mein actually kya save hua"""
    recorded = []

    def fake_add_message(conversation_id, role, content):
        recorded.append((role, content))

    monkeypatch.setattr(chat_service, "add_message", fake_add_message)
    monkeypatch.setattr(chat_service, "get_history", lambda conversation_id: [])
    return recorded


def run_stream(monkeypatch, stream_fn, stop_after=None):
    """Stream consume karo; stop_after do toh client disconnect simulate hota hai"""
    monkeypatch.setattr(chat_service, "generate_response_stream", stream_fn)

    output = ""
    generator = get_ai_response_stream("hello", str(uuid.uuid4()))

    for index, chunk in enumerate(generator):
        output += chunk
        if stop_after is not None and index + 1 == stop_after:
            generator.close()
            break

    return output


def test_successful_response_is_saved(monkeypatch, saved):
    def stream(history, mode):
        yield "Hello"
        yield " world"

    assert run_stream(monkeypatch, stream) == "Hello world"
    assert saved == [("user", "hello"), ("assistant", "Hello world")]


def test_llm_failure_is_not_saved_to_history(monkeypatch, saved):
    """Error text history mein chala jaata tha aur agli baar LLM ko wapas milta tha"""
    def stream(history, mode):
        raise LLMUnavailableError("ollama down")
        yield   # pragma: no cover — isse function generator banta hai

    assert run_stream(monkeypatch, stream) == AI_UNAVAILABLE_MESSAGE
    assert saved == [("user", "hello")]


def test_partial_response_saved_without_error_text(monkeypatch, saved):
    def stream(history, mode):
        yield "partial answer"
        raise LLMUnavailableError("ollama died mid-stream")

    output = run_stream(monkeypatch, stream)

    assert output == "partial answer" + AI_UNAVAILABLE_MESSAGE
    assert saved == [("user", "hello"), ("assistant", "partial answer")]


def test_client_disconnect_keeps_partial_response(monkeypatch, saved):
    """Pehle disconnect pe poora jawab gum ho jaata tha"""
    def stream(history, mode):
        yield "chunk1"
        yield "chunk2"
        yield "chunk3"

    assert run_stream(monkeypatch, stream, stop_after=2) == "chunk1chunk2"
    assert saved == [("user", "hello"), ("assistant", "chunk1chunk2")]


def test_error_text_never_reaches_history(monkeypatch, saved):
    def stream(history, mode):
        raise LLMUnavailableError("ollama down")
        yield   # pragma: no cover

    run_stream(monkeypatch, stream)

    assert all(AI_UNAVAILABLE_MESSAGE not in content for _, content in saved)


def test_mode_reaches_the_llm_layer(monkeypatch, saved):
    """Mode LLM tak na pahunche toh dropdown dikhega par kuch karega nahi"""
    received = []

    def stream(history, mode):
        received.append(mode)
        yield "ok"

    monkeypatch.setattr(chat_service, "generate_response_stream", stream)
    list(get_ai_response_stream("hello", str(uuid.uuid4()), mode="debug"))

    assert received == ["debug"]


def test_mode_defaults_to_general(monkeypatch, saved):
    received = []

    def stream(history, mode):
        received.append(mode)
        yield "ok"

    monkeypatch.setattr(chat_service, "generate_response_stream", stream)
    list(get_ai_response_stream("hello", str(uuid.uuid4())))

    assert received == ["general"]
