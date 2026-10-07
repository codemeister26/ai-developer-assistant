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

    def __init__(self, chunks=(), error=None, usage=None):
        self.chunks = chunks
        self.error = error
        self.calls = []
        # Asli providers stream khatam hone par ye bharte hain
        self.usage = usage

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

    def fake_add_message(conversation_id, role, content, user_id=None):
        recorded.append((role, content))

    monkeypatch.setattr(chat_service, "add_message", fake_add_message)
    monkeypatch.setattr(chat_service, "get_history", lambda conversation_id: [])
    # RAG document lookup alag feature hai — yahan wo DB tak na jaye
    monkeypatch.setattr(
        chat_service, "build_context", lambda question, user_id: ("", [])
    )
    return recorded


def use_provider(monkeypatch, provider):
    monkeypatch.setattr(chat_service, "get_provider", lambda model, api_key: provider)
    return provider


def collect(monkeypatch, provider, stop_after=None, **kwargs):
    """Saare events uthao; stop_after do toh client disconnect simulate hota hai"""
    use_provider(monkeypatch, provider)

    events = []
    generator = get_ai_response_stream("hello", str(uuid.uuid4()), **kwargs)

    for index, event in enumerate(generator):
        events.append(event)
        if stop_after is not None and index + 1 == stop_after:
            generator.close()
            break

    return events


def text_of(events):
    """Sirf token events ka text jod do"""
    return "".join(e["text"] for e in events if e["type"] == "token")


def run_stream(monkeypatch, provider, stop_after=None, **kwargs):
    return text_of(collect(monkeypatch, provider, stop_after, **kwargs))


def test_successful_response_is_saved(monkeypatch, saved):
    provider = FakeProvider(chunks=["Hello", " world"])

    assert run_stream(monkeypatch, provider) == "Hello world"
    assert saved == [("user", "hello"), ("assistant", "Hello world")]


def test_llm_failure_sends_an_error_event_and_saves_nothing(monkeypatch, saved):
    """Error text history mein chala jaata tha aur agli baar LLM ko wapas milta tha"""
    events = collect(monkeypatch, FakeProvider(error=LLMUnavailableError("down")))

    assert events[-1] == {
        "type": "error",
        "kind": "unavailable",
        "message": AI_UNAVAILABLE_MESSAGE,
    }
    assert saved == [("user", "hello")]


def test_auth_error_has_its_own_kind(monkeypatch, saved):
    """Galat API key user khud theek kar sakta hai — generic error se alag dikhe"""
    events = collect(monkeypatch, FakeProvider(error=LLMAuthError("bad key")))

    assert events[-1]["kind"] == "auth"
    assert events[-1]["message"] == AI_AUTH_MESSAGE
    assert saved == [("user", "hello")]


def test_partial_response_is_saved_and_error_stays_out_of_it(monkeypatch, saved):
    provider = FakeProvider(
        chunks=["partial answer"], error=LLMUnavailableError("died mid-stream")
    )

    events = collect(monkeypatch, provider)

    # Error ab apne event mein hai, jawab ke text mein nahi
    assert text_of(events) == "partial answer"
    assert events[-1]["type"] == "error"
    assert saved == [("user", "hello"), ("assistant", "partial answer")]


def test_successful_stream_ends_with_a_done_event(monkeypatch, saved):
    events = collect(monkeypatch, FakeProvider(chunks=["Hello", " world"]))

    assert events[-1]["type"] == "done"
    assert events[-1]["chars"] == len("Hello world")


def test_done_event_carries_the_conversation_id(monkeypatch, saved):
    """Frontend ise header ke bajaye yahan se bhi le sakta hai"""
    conversation_id = str(uuid.uuid4())
    use_provider(monkeypatch, FakeProvider(chunks=["ok"]))

    events = list(get_ai_response_stream("hello", conversation_id))

    assert events[-1]["conversation_id"] == conversation_id


def test_no_done_event_when_the_stream_fails(monkeypatch, saved):
    events = collect(monkeypatch, FakeProvider(error=LLMUnavailableError("down")))

    assert not any(e["type"] == "done" for e in events)


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


# ─── Token usage aur cost ─────────────────────────────────────────────────────

def test_done_event_carries_token_usage(monkeypatch, saved):
    provider = FakeProvider(
        chunks=["hi"], usage={"input_tokens": 100, "output_tokens": 50}
    )

    events = collect(monkeypatch, provider)

    assert events[-1]["usage"]["input_tokens"] == 100
    assert events[-1]["usage"]["output_tokens"] == 50


def test_local_model_costs_nothing(monkeypatch, saved):
    provider = FakeProvider(
        chunks=["hi"], usage={"input_tokens": 1000, "output_tokens": 1000}
    )

    events = collect(monkeypatch, provider, model="llama3.2:3b")

    assert events[-1]["usage"]["cost_usd"] == 0


def test_paid_model_reports_cost(monkeypatch, saved):
    """Haiku: $1 input / $5 output per million"""
    provider = FakeProvider(
        chunks=["hi"], usage={"input_tokens": 1_000_000, "output_tokens": 1_000_000}
    )

    events = collect(monkeypatch, provider, model="claude-haiku-4-5")

    assert events[-1]["usage"]["cost_usd"] == pytest.approx(6.0)


def test_done_event_works_without_usage(monkeypatch, saved):
    """Provider usage na de toh event phir bhi jaana chahiye"""
    events = collect(monkeypatch, FakeProvider(chunks=["hi"], usage=None))

    assert events[-1]["type"] == "done"
    assert "usage" not in events[-1]


def test_done_event_names_the_documents_used(monkeypatch, saved):
    """User ko dikhna chahiye ki jawab kahan se aaya"""
    monkeypatch.setattr(
        chat_service,
        "build_context",
        lambda question, user_id: ("excerpt", ["manual.pdf", "notes.md"]),
    )

    events = collect(monkeypatch, FakeProvider(chunks=["hi"]))

    assert events[-1]["sources"] == ["manual.pdf", "notes.md"]


def test_no_sources_key_when_no_documents_matched(monkeypatch, saved):
    events = collect(monkeypatch, FakeProvider(chunks=["hi"]))

    assert "sources" not in events[-1]
