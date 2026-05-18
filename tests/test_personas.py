from __future__ import annotations

from ghbattle.personas import PERSONAS, pick_persona


def test_pick_persona_returns_known_name() -> None:
    name, prompt = pick_persona()
    assert name in {"savage", "gentle", "meme"}
    assert "{stats_block}" in prompt


def test_three_personas_defined() -> None:
    names = {name for name, _ in PERSONAS}
    assert names == {"savage", "gentle", "meme"}


def test_every_prompt_has_anchors() -> None:
    for _, prompt in PERSONAS:
        assert "{stats_block}" in prompt
        assert "ONE sentence" in prompt
        assert "no preamble" in prompt
