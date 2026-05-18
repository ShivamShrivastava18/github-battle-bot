from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Stats:
    login: str
    avatar_url: str
    bio: str | None
    public_repos: int
    total_stars: int
    followers: int
    commits_30d: int
    top_language: str | None
    account_age_days: int


@dataclass(frozen=True)
class BattleRow:
    label: str
    value_a: str
    value_b: str
    winner: Literal["a", "b", "tie", "none"]


@dataclass(frozen=True)
class BattleResult:
    rows: list[BattleRow]
    a: Stats
    b: Stats
    overall_winner: Literal["a", "b", "tie"]
    score: str  # rendered as "{a_wins}-{b_wins}"
