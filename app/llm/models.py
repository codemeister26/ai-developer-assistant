# ─── Model Catalog ────────────────────────────────────────────────────────────
# Kaun se models chun sakte ho, kaun sa provider chalayega, aur kiske liye API
# key chahiye. Frontend ka dropdown /api/v1/models se yahi list uthata hai.

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelInfo:
    id: str
    label: str
    provider: str
    needs_key: bool
    note: str = ""
    # Price per million tokens (USD). Local models free hain, isliye 0.
    input_price: float = 0.0
    output_price: float = 0.0
    # Anthropic ke alag-alag models alag params lete hain — Haiku 4.5 effort par
    # error deta hai, jabki Sonnet/Opus use karte hain. Isliye per-model rakha hai.
    extra_params: dict = field(default_factory=dict)


MODELS = [
    ModelInfo(
        id="llama3.2:3b",
        label="Llama 3.2 3B (local)",
        provider="ollama",
        needs_key=False,
        note="Free, tumhare laptop par chalta hai",
    ),
    ModelInfo(
        id="claude-haiku-4-5",
        label="Claude Haiku 4.5",
        provider="anthropic",
        needs_key=True,
        note="Sabse sasta Claude — $1/$5 per million tokens",
        input_price=1.0,
        output_price=5.0,
        # Haiku 4.5 par "effort" bhejne se error aata hai, isliye kuch nahi bhejte
        extra_params={},
    ),
    ModelInfo(
        id="claude-sonnet-5",
        label="Claude Sonnet 5",
        provider="anthropic",
        needs_key=True,
        note="Balanced — $2/$10 per million tokens",
        input_price=2.0,
        output_price=10.0,
        extra_params={
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": "medium"},
        },
    ),
    ModelInfo(
        id="claude-opus-5",
        label="Claude Opus 5",
        provider="anthropic",
        needs_key=True,
        note="Sabse capable — $5/$25 per million tokens",
        input_price=5.0,
        output_price=25.0,
        extra_params={
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": "medium"},
        },
    ),
]

MODELS_BY_ID = {model.id: model for model in MODELS}

DEFAULT_MODEL = "llama3.2:3b"


def get_model(model_id: str) -> ModelInfo | None:
    return MODELS_BY_ID.get(model_id)


def cost_of(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Is request ka kharcha (USD). Local models par hamesha 0."""
    info = get_model(model_id)

    if info is None:
        return 0.0

    return (
        input_tokens * info.input_price + output_tokens * info.output_price
    ) / 1_000_000
