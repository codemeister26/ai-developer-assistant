import uuid

import pytest

from app.llm.base import LLMAuthError, LLMUnavailableError
from app.services import chat_service
from app.services.chat_service import (
    AI_AUTH_MESSAGE,
    AI_UNAVAILABLE_MESSAGE,
    get_ai_response_stream,
)


class FakeProvider:
    """Provider ki jagah — kya bheja gaya wo record karta hai"""

    def __init__(self, chunks=(), error=None):
        self.chunks = chunks
        self.error = error
        self.calls = []

    def stream(self, model, system, messages):
        self.calls.append({"model": model, "system": system, "messages": messages})

        for chunk in self.chunks:
            yield chunk

        if self.error:
            raise self.error


@pytest.fixture
def saved(monkeypatch):
    """add_message ko intercept karke dekho ki history mein actually kya save hua"""
    recorded = []

    def fake_add_message(conversation_id, role, content):
        recorded.append((role, content))

    monkeypatch.setattr(chat_service, "add_message", fake_add_message)
    monkeypatch.setattr(chat_service, "get_history", lambda conversation_id: [])
    return recorded


def use_provider(monkeypatch, provider):
    monkeypatch.setattr(chat_service, "get_provider", lambda model, api_key: provider)
    return provider


def run_stream(monkeypatch, provider, stop_after=None, **kwargs):
    """Stream consume karo; stop_after do toh client disconnect simulate hota hai"""
    use_provider(monkeypatch, provider)

    output = ""
    generator = get_ai_response_stream("hello", str(uuid.uuid4()), **kwargs)

    for index, chunk in enumerate(generator):
        output += chunk
        if stop_after is not None and index + 1 == stop_after:
            generator.close()
            break

    return output


def test_successful_response_is_saved(monkeypatch, saved):
    provider = FakeProvider(chunks=["Hello", " world"])

    assert run_stream(monkeypatch, provider) == "Hello world"
    assert saved == [("user", "hello"), ("assistant", "Hello world")]


def test_llm_failure_is_not_saved_to_history(monkeypatch, saved):
    """Error text history mein chala jaata tha aur agli baar LLM ko wapas milta tha"""
    provider = FakeProvider(error=LLMUnavailableError("service down"))

    assert run_stream(monkeypatch, provider) == AI_UNAVAILABLE_MESSAGE
    assert saved == [("user", "hello")]


def test_auth_error_shows_its_own_message(monkeypatch, saved):
    """Galat API key user khud theek kar sakta hai — generic error se alag dikhe"""
    provider = FakeProvider(error=LLMAuthError("bad key"))

    assert run_stream(monkeypatch, provider) == AI_AUTH_MESSAGE
    assert saved == [("user", "hello")]


def test_partial_response_saved_without_error_text(monkeypatch, saved):
    provider = FakeProvider(
        chunks=["partial answer"], error=LLMUnavailableError("died mid-stream")
    )

    output = run_stream(monkeypatch, provider)

    assert output == "partial answer" + AI_UNAVAILABLE_MESSAGE
    assert saved == [("user", "hello"), ("assistant", "partial answer")]


def test_client_disconnect_keeps_partial_response(monkeypatch, saved):
    """Pehle disconnect pe poora jawab gum ho jaata tha"""
    provider = FakeProvider(chunks=["chunk1", "chunk2", "chunk3"])

    assert run_stream(monkeypatch, provider, stop_after=2) == "chunk1chunk2"
    assert saved == [("user", "hello"), ("assistant", "chunk1chunk2")]


@pytest.mark.parametrize("error", [LLMUnavailableError("x"), LLMAuthError("x")])
def test_error_text_never_reaches_history(monkeypatch, saved, error):
    run_stream(monkeypatch, FakeProvider(error=error))

    fallbacks = (AI_UNAVAILABLE_MESSAGE, AI_AUTH_MESSAGE)
    assert all(text not in content for _, content in saved for text in fallbacks)


def test_mode_selects_the_system_prompt(monkeypatch, saved):
    """Mode system prompt tak na pahunche toh dropdown dikhega par kuch karega nahi"""
    provider = FakeProvider(chunks=["ok"])

    run_stream(monkeypatch, provider, mode="debug")

    assert "expert debugger" in provider.calls[0]["system"]


def test_mode_defaults_to_general(monkeypatch, saved):
    provider = FakeProvider(chunks=["ok"])

    run_stream(monkeypatch, provider)

    assert "AI Developer Assistant" in provider.calls[0]["system"]


def test_model_reaches_the_provider(monkeypatch, saved):
    provider = FakeProvider(chunks=["ok"])

    run_stream(monkeypatch, provider, model="claude-haiku-4-5")

    assert provider.calls[0]["model"] == "claude-haiku-4-5"


def test_api_key_is_passed_to_the_factory_not_the_stream(monkeypatch, saved):
    """Key provider banane ke liye hai — messages ke saath nahi jaani chahiye"""
    seen = {}

    def fake_factory(model, api_key):
        seen["model"] = model
        seen["api_key"] = api_key
        return FakeProvider(chunks=["ok"])

    monkeypatch.setattr(chat_service, "get_provider", fake_factory)
    list(get_ai_response_stream("hello", str(uuid.uuid4()), model="claude-opus-5", api_key="sk-test"))

    assert seen == {"model": "claude-opus-5", "api_key": "sk-test"}
