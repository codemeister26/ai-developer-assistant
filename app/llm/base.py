# ─── LLM Provider Interface ───────────────────────────────────────────────────
# Har provider (Ollama, Anthropic, ...) isi shape ko follow karta hai, taaki
# baaki app ko pata hi na chale ki jawab kahan se aa raha hai.

from abc import ABC, abstractmethod
from typing import Generator


class LLMError(Exception):
    """Sabhi LLM errors ka base"""


class LLMUnavailableError(LLMError):
    """Service se baat nahi ho payi — user ki galti nahi hai"""


class LLMAuthError(LLMError):
    """API key galat ya missing — ye user khud theek kar sakta hai"""


class LLMProvider(ABC):
    def __init__(self):
        # Stream khatam hone par bharta hai: {"input_tokens": n, "output_tokens": n}
        # Har request ke liye naya provider banta hai, isliye instance par
        # rakhna safe hai — ek user ka usage doosre ko nahi dikhega.
        self.usage: dict | None = None

    @abstractmethod
    def stream(self, model: str, system: str, messages: list) -> Generator[str, None, None]:
        """Jawab token-by-token do.

        Error par LLMUnavailableError ya LLMAuthError raise karo — error text
        yield mat karo, warna wo assistant ke jawab ki tarah save ho jaata hai.
        """
