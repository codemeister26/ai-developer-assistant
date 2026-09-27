# ─── Provider Factory ─────────────────────────────────────────────────────────
# Model ka naam dekhkar sahi provider banata hai. Baaki app ko sirf ye pata hota
# hai ki "stream" milta hai — kaun sa provider chala, isse farak nahi padta.

from app.llm.anthropic_provider import AnthropicProvider
from app.llm.base import LLMProvider, LLMUnavailableError
from app.llm.models import get_model
from app.llm.ollama_provider import OllamaProvider


def get_provider(model_id: str, api_key: str | None = None) -> LLMProvider:
    """Model ke liye provider do. Unknown model par LLMUnavailableError."""
    info = get_model(model_id)

    if info is None:
        raise LLMUnavailableError(f"Unknown model: {model_id}")

    if info.provider == "ollama":
        return OllamaProvider()

    if info.provider == "anthropic":
        # Key na ho toh AnthropicProvider khud LLMAuthError uthata hai
        return AnthropicProvider(api_key or "")

    raise LLMUnavailableError(f"Unknown provider: {info.provider}")
