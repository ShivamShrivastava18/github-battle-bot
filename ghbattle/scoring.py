from __future__ import annotations

from typing import Literal

from ghbattle.types import BattleResult, BattleRow, Stats

WinnerLit = Literal["a", "b", "tie"]


def _wins(a_val: int, b_val: int, *, higher_wins: bool = True) -> WinnerLit:
    if a_val == b_val:
        return "tie"
    if higher_wins:
        return "a" if a_val > b_val else "b"
    return "a" if a_val < b_val else "b"


def _fmt_int(n: int) -> str:
    return f"{n:,}"


def _fmt_lang(lang: str | None) -> str:
    return lang or "—"


def score_battle(a: Stats, b: Stats) -> BattleResult:
    rows: list[BattleRow] = []

    for label, attr in (
        ("Public repos", "public_repos"),
        ("Total stars", "total_stars"),
        ("Followers", "followers"),
        ("Commits (30d)", "commits_30d"),
    ):
        va = getattr(a, attr)
        vb = getattr(b, attr)
        rows.append(
            BattleRow(
                label=label,
                value_a=_fmt_int(va),
                value_b=_fmt_int(vb),
                winner=_wins(va, vb, higher_wins=True),
            )
        )

    rows.append(
        BattleRow(
            label="Account age (days)",
            value_a=_fmt_int(a.account_age_days),
            value_b=_fmt_int(b.account_age_days),
            winner=_wins(a.account_age_days, b.account_age_days, higher_wins=False),
        )
    )

    rows.append(
        BattleRow(
            label="Top language",
            value_a=_fmt_lang(a.top_language),
            value_b=_fmt_lang(b.top_language),
            winner="none",
        )
    )

    a_wins = sum(1 for r in rows if r.winner == "a")
    b_wins = sum(1 for r in rows if r.winner == "b")

    if a_wins > b_wins:
        overall: WinnerLit = "a"
    elif b_wins > a_wins:
        overall = "b"
    else:
        overall = "tie"

    return BattleResult(
        rows=rows,
        a=a,
        b=b,
        overall_winner=overall,
        score=f"{a_wins}-{b_wins}",
    )
