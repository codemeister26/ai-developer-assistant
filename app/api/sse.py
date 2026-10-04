# ─── Server-Sent Events ───────────────────────────────────────────────────────
# Pehle stream plain text thi, isliye usme text ke alawa kuch bhej hi nahi
# sakte the — na error, na metadata. Ab har cheez ek typed event hai.

from typing import Generator, Iterable
import json


def format_event(event: dict) -> str:
    """Ek event ko SSE frame mein badlo.

    JSON isliye — newline wale jawab plain text SSE ko tod dete hain, JSON
    unhe escape kar deta hai.
    """
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def to_sse(events: Iterable[dict]) -> Generator[str, None, None]:
    for event in events:
        yield format_event(event)


# StreamingResponse ke saath ye headers zaruri hain, warna proxy stream ko
# buffer kar leta hai aur user ko sab ek saath milta hai
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}
