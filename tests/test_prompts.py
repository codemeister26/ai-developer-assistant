import pytest

from app.config import prompts
from app.config.prompts import CODE_ACCURACY_RULES, PROMPTS, get_prompt
from app.schemas.chat import ChatMode


def test_every_mode_has_a_prompt():
    """Enum aur registry sync mein rahein — warna mode chupchap general pe gir jaata hai"""
    assert {mode.value for mode in ChatMode} == set(PROMPTS)


def test_no_prompt_is_left_unused():
    """5 prompts likhe pade the aur koi unhe use nahi karta tha — dobara na ho"""
    defined = {
        name
        for name in dir(prompts)
        if name.endswith("_PROMPT") and isinstance(getattr(prompts, name), str)
    }
    used = {
        name
        for name in defined
        if any(getattr(prompts, name) is value for value in PROMPTS.values())
    }

    assert defined == used, f"kisi registry mein nahi: {defined - used}"


@pytest.mark.parametrize("mode", [m.value for m in ChatMode])
def test_each_mode_returns_its_own_prompt(mode):
    assert get_prompt(mode).startswith(PROMPTS[mode].rstrip()[:40])


@pytest.mark.parametrize("mode", [m.value for m in ChatMode])
def test_accuracy_rules_attached_to_every_mode(mode):
    """Chhote models galat code likh dete hain — ye rules har mode ke saath jaane chahiye"""
    assert CODE_ACCURACY_RULES.strip() in get_prompt(mode)


def test_unknown_mode_falls_back_to_general():
    assert get_prompt("kuch-bhi") == get_prompt("general")


def test_modes_produce_different_prompts():
    assert get_prompt("debug") != get_prompt("architecture")
