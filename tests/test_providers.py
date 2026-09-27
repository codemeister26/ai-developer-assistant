import pytest

from app.llm.anthropic_provider import AnthropicProvider
from app.llm.base import LLMAuthError, LLMProvider, LLMUnavailableError
from app.llm.factory import get_provider
from app.llm.models import DEFAULT_MODEL, MODELS, MODELS_BY_ID, get_model
from app.llm.ollama_provider import OllamaProvider


# ─── Catalog ──────────────────────────────────────────────────────────────────

def test_default_model_exists_in_catalog():
    assert get_model(DEFAULT_MODEL) is not None


def test_default_model_needs_no_key():
    """Bina key ke app chalni chahiye — warna pehli hi baar mein user atak jayega"""
    assert get_model(DEFAULT_MODEL).needs_key is False


def test_model_ids_are_unique():
    assert len(MODELS) == len(MODELS_BY_ID)


@pytest.mark.parametrize("model", MODELS, ids=lambda m: m.id)
def test_every_model_has_a_working_provider(model):
    provider = get_provider(model.id, api_key="sk-test" if model.needs_key else None)
    assert isinstance(provider, LLMProvider)


def test_haiku_gets_no_effort_param():
    """Haiku 4.5 par effort bhejne se API error deta hai"""
    assert "output_config" not in get_model("claude-haiku-4-5").extra_params


# ─── Factory ──────────────────────────────────────────────────────────────────

def test_local_model_gives_ollama_provider():
    assert isinstance(get_provider("llama3.2:3b"), OllamaProvider)


def test_claude_model_gives_anthropic_provider():
    assert isinstance(get_provider("claude-opus-5", "sk-test"), AnthropicProvider)


def test_unknown_model_is_rejected():
    with pytest.raises(LLMUnavailableError, match="Unknown model"):
        get_provider("gpt-9-turbo-max")


def test_claude_without_key_raises_auth_error():
    """User ko "service down" nahi, "key daalo" dikhna chahiye"""
    with pytest.raises(LLMAuthError):
        get_provider("claude-opus-5")


def test_local_model_works_without_key():
    assert get_provider("llama3.2:3b", api_key=None) is not None


# ─── Key handling ─────────────────────────────────────────────────────────────

def test_key_is_not_logged_on_failure(caplog, monkeypatch):
    """Key kabhi logs mein nahi jaani chahiye"""
    import anthropic

    secret = "sk-ant-secret-value-12345"

    def explode(*args, **kwargs):
        raise anthropic.APIConnectionError(request=None)

    monkeypatch.setattr(anthropic.resources.messages.Messages, "stream", explode)

    with caplog.at_level("DEBUG"):
        with pytest.raises(LLMUnavailableError):
            list(AnthropicProvider(secret).stream("claude-opus-5", "sys", []))

    assert secret not in caplog.text


def test_provider_does_not_keep_key_on_the_class():
    """Key instance par hi rahe — class par chipak jaye toh next user ko mil sakti hai"""
    AnthropicProvider("sk-first")
    second = AnthropicProvider("sk-second")

    assert second.api_key == "sk-second"
    assert getattr(AnthropicProvider, "api_key", None) is None
