from __future__ import annotations

import discord

from ghbattle.formatting import build_battle_embed, build_roast_embed, build_stats_embed
from ghbattle.scoring import score_battle
from ghbattle.types import Stats


def _stats(login: str = "user", **kwargs: object) -> Stats:
    defaults = dict(
        avatar_url="https://example.com/a.png",
        bio="hello",
        public_repos=10,
        total_stars=100,
        followers=50,
        commits_30d=5,
        top_language="Python",
        account_age_days=365,
    )
    defaults.update(kwargs)
    return Stats(login=login, **defaults)  # type: ignore[arg-type]


def test_stats_embed_has_login_title_and_repo_link() -> None:
    embed = build_stats_embed(_stats(login="alice"))
    assert isinstance(embed, discord.Embed)
    assert embed.title == "alice"
    assert embed.url == "https://github.com/alice"


def test_stats_embed_handles_missing_bio() -> None:
    embed = build_stats_embed(_stats(bio=None))
    assert embed.description and "no bio" in embed.description.lower()


def test_battle_embed_title_when_a_wins() -> None:
    a = _stats(login="alice", public_repos=100, total_stars=1000, followers=500, commits_30d=50)
    b = _stats(login="bob",   public_repos=1,   total_stars=2,    followers=3,   commits_30d=4)
    embed = build_battle_embed(score_battle(a, b))
    assert embed.title is not None
    assert "alice" in embed.title and "bob" in embed.title


def test_battle_embed_title_when_b_wins_flips_score() -> None:
    a = _stats(login="alice", public_repos=1, total_stars=2, followers=3, commits_30d=4, account_age_days=500)
    b = _stats(login="bob", public_repos=10, total_stars=20, followers=30, commits_30d=40, account_age_days=100)
    result = score_battle(a, b)
    embed = build_battle_embed(result)
    # b wins all 5 scored rows: result.score is "0-5", embed should advertise the win as 5-0
    assert "5-0" in (embed.title or "")


def test_roast_embed_carries_persona_label() -> None:
    embed = build_roast_embed(_stats(login="alice"), roast="rough.", persona="savage")
    assert embed.title == "alice"
    # the persona name appears in one of the fields
    assert any("savage" in (f.name or "").lower() for f in embed.fields)


def test_roast_embed_falls_back_when_roast_empty() -> None:
    embed = build_roast_embed(_stats(login="alice"), roast="", persona="meme")
    assert any("unavailable" in (f.value or "").lower() for f in embed.fields)
