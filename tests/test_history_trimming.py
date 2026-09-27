from app.memory.chat_memory import trim_to_budget


def msg(role, size):
    return {"role": role, "content": "x" * size}


def test_everything_fits_within_budget():
    history = [msg("user", 10), msg("assistant", 10)]

    assert trim_to_budget(history, budget=100) == history


def test_oldest_messages_are_dropped_first():
    history = [
        {"role": "user", "content": "purana sawaal"},
        {"role": "assistant", "content": "purana jawab"},
        {"role": "user", "content": "naya sawaal"},
    ]

    kept = trim_to_budget(history, budget=len("naya sawaal") + 5)

    assert kept == [{"role": "user", "content": "naya sawaal"}]


def test_messages_are_never_cut_in_half():
    """Aadha message LLM ko confuse karta hai — poora rakho ya bilkul mat rakho"""
    history = [msg("user", 100), msg("assistant", 100), msg("user", 100)]

    for message in trim_to_budget(history, budget=250):
        assert len(message["content"]) == 100


def test_single_oversized_message_is_still_sent():
    """Warna user ka abhi bheja hua sawaal hi gayab ho jayega"""
    history = [msg("user", 5000)]

    assert len(trim_to_budget(history, budget=100)) == 1


def test_history_never_starts_with_assistant():
    """Anthropic pehla message user hi maangta hai — warna 400 aata hai"""
    history = [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a" * 100},
        {"role": "user", "content": "q2"},
    ]

    # Budget aisa ki trim ke baad assistant sabse aage aa jaye
    kept = trim_to_budget(history, budget=105)

    assert kept[0]["role"] == "user"


def test_empty_history_stays_empty():
    assert trim_to_budget([], budget=100) == []


def test_all_assistant_history_becomes_empty():
    """Aisa hona nahi chahiye, par hua toh API error se behtar khaali bhejna hai"""
    assert trim_to_budget([msg("assistant", 10)], budget=100) == []
