import json

from app.api.sse import SSE_HEADERS, format_event, to_sse


def parse(frame):
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    return json.loads(frame[len("data: "):-2])


def test_event_round_trips():
    assert parse(format_event({"type": "token", "text": "hi"})) == {
        "type": "token",
        "text": "hi",
    }


def test_newlines_do_not_break_the_frame():
    """Code blocks mein newlines hoti hain — plain text SSE unse toot jaata hai"""
    frame = format_event({"type": "token", "text": "line1\nline2\n\nline3"})

    assert frame.count("\n\n") == 1          # sirf frame ka terminator
    assert parse(frame)["text"] == "line1\nline2\n\nline3"


def test_text_containing_data_prefix_stays_one_frame():
    """Jawab mein "data: " likha ho toh wo nayi frame nahi banna chahiye"""
    frame = format_event({"type": "token", "text": "data: not an event"})

    lines = [line for line in frame.split("\n") if line]
    assert len(lines) == 1
    assert parse(frame)["text"] == "data: not an event"


def test_unicode_is_kept_readable():
    assert "नमस्ते" in format_event({"type": "token", "text": "नमस्ते"})


def test_to_sse_formats_every_event():
    frames = list(to_sse([{"type": "token", "text": "a"}, {"type": "done"}]))

    assert [parse(f)["type"] for f in frames] == ["token", "done"]


def test_headers_stop_proxies_from_buffering():
    """Buffering ho gayi toh user ko poora jawab ek saath milega, stream ka matlab hi khatam"""
    assert SSE_HEADERS["X-Accel-Buffering"] == "no"
    assert SSE_HEADERS["Cache-Control"] == "no-cache"
