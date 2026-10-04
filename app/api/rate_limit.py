# ─── Rate limiting ────────────────────────────────────────────────────────────
# Chat endpoint har request par LLM chalata hai — wo mehnga aur dheema hai.
# Bina limit ke ek script poore backend ko jam kar sakti hai (aur BYOK ke case
# mein kisi ke paise bhi uda sakti hai).
#
# Ye in-memory hai, yaani ek hi process ke liye. Kai instances chalane hon toh
# Redis chahiye hoga — par abhi app ek hi process mein chalti hai.

from collections import defaultdict, deque
from fastapi import HTTPException, Request
import time

from app.config.settings import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

_hits: dict[str, deque] = defaultdict(deque)


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def rate_limit(request: Request) -> None:
    """Sliding window — window ke andar RATE_LIMIT_REQUESTS se zyada nahi"""
    if RATE_LIMIT_REQUESTS <= 0:          # 0 ya kam = limit band
        return

    key = _client_key(request)
    now = time.monotonic()
    hits = _hits[key]

    # Window se bahar nikal chuke hits hata do
    while hits and now - hits[0] > RATE_LIMIT_WINDOW:
        hits.popleft()

    if len(hits) >= RATE_LIMIT_REQUESTS:
        retry_after = int(RATE_LIMIT_WINDOW - (now - hits[0])) + 1
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment.",
            headers={"Retry-After": str(retry_after)},
        )

    hits.append(now)


def reset() -> None:
    """Tests ke liye — state process bhar rehti hai"""
    _hits.clear()
