import pytest

from app.services.title_service import MAX_TITLE_LENGTH, clean_title


def test_plain_title_passes_through():
    assert clean_title("Python async basics") == "Python async basics"


@pytest.mark.parametrize(
    "raw",
    [
        '"Python async basics"',
        "'Python async basics'",
        "`Python async basics`",
        "**Python async basics**",
        "Python async basics.",
        "Title: Python async basics",
        "title: Python async basics",
        "Chat title - Python async basics",
    ],
)
def test_model_decorations_are_stripped(raw):
    """Chhote models quotes, "Title:" prefix aur punctuation laga dete hain"""
    assert clean_title(raw) == "Python async basics"


def test_only_the_first_line_is_used():
    """Model kabhi kabhi title ke baad explanation bhi likh deta hai"""
    assert clean_title("Python async basics\nThis covers coroutines") == (
        "Python async basics"
    )


def test_long_title_is_cut_at_a_word_boundary():
    raw = "A very long conversation about database indexes and query planning in postgres"

    title = clean_title(raw)

    assert len(title) <= MAX_TITLE_LENGTH + 1   # +1 ellipsis ke liye
    assert title.endswith("…")
    assert not title[:-1].endswith(" ")         # beech se shabd nahi kata


def test_empty_response_gives_no_title():
    assert clean_title("") is None


def test_response_with_only_decoration_gives_no_title():
    assert clean_title('  ""  ') is None
