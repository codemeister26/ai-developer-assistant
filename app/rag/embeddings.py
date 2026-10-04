# ─── Embeddings ───────────────────────────────────────────────────────────────
# Text ko numbers mein badalte hain taaki "matlab" se dhoondha ja sake. Keyword
# search mein "login" likho toh "authentication" wala hissa nahi milta;
# embeddings mein mil jaata hai.

from app.config.settings import EMBEDDING_MODEL, OLLAMA_HOST, OLLAMA_READ_TIMEOUT
import httpx
import logging
import math

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Embedding model se jawab nahi mila"""


def embed(texts: list[str]) -> list[list[float]]:
    """Har text ka embedding do. Ek bhi fail ho toh poora batch fail."""
    if not texts:
        return []

    try:
        with httpx.Client(timeout=OLLAMA_READ_TIMEOUT) as client:
            response = client.post(
                f"{OLLAMA_HOST}/api/embed",
                json={"model": EMBEDDING_MODEL, "input": texts},
            )
            response.raise_for_status()
            vectors = response.json().get("embeddings")

    except Exception as e:
        logger.warning("Embedding failed: %s", type(e).__name__)
        raise EmbeddingError(
            f"Embedding model '{EMBEDDING_MODEL}' se jawab nahi mila. "
            f"Chala hua hai? `ollama pull {EMBEDDING_MODEL}`"
        ) from e

    if not vectors or len(vectors) != len(texts):
        raise EmbeddingError("Embedding model ne adhura jawab diya")

    return vectors


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Do embeddings kitne milte-julte hain: 1 = same, 0 = bilkul alag"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)
