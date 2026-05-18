from __future__ import annotations

from ghbattle.scoring import score_battle
from ghbattle.types import Stats


def _stats(
    login: str = "user",
    public_repos: int = 0,
    total_stars: int = 0,
    followers: int = 0,
    commits_30d: int = 0,
    top_language: str | None = None,
    account_age_days: int = 100,
) -> Stats:
    return Stats(
        login=login,
        avatar_url="",
        bio=None,
        public_repos=public_repos,
        total_stars=total_stars,
        followers=followers,
        commits_30d=commits_30d,
        top_language=top_language,
        account_age_days=account_age_days,
    )


def test_clear_a_wins() -> None:
    a = _stats(login="a", public_repos=10, total_stars=100, followers=50, commits_30d=20, account_age_days=200)
    b = _stats(login="b", public_repos=5, total_stars=20, followers=10, commits_30d=5, account_age_days=100)
    # higher wins for the first four; newer (smaller) wins for account_age_days,
    # so a wins all four "higher-wins" rows but loses on account age.
    result = score_battle(a, b)
    assert result.overall_winner == "a"
    assert result.score == "4-1"


def test_b_wins() -> None:
    a = _stats(login="a", public_repos=1, total_stars=2, followers=3, commits_30d=4, account_age_days=200)
    b = _stats(login="b", public_repos=10, total_stars=20, followers=30, commits_30d=40, account_age_days=100)
    # b wins all four higher-wins rows AND wins newer-account-age -> 5-0
    result = score_battle(a, b)
    assert result.overall_winner == "b"
    assert result.score == "0-5"


def test_all_tie() -> None:
    a = _stats(login="a", public_repos=5, total_stars=5, followers=5, commits_30d=5, account_age_days=100)
    b = _stats(login="b", public_repos=5, total_stars=5, followers=5, commits_30d=5, account_age_days=100)
    result = score_battle(a, b)
    assert result.overall_winner == "tie"
    assert result.score == "0-0"


def test_mixed_overall_tie() -> None:
    a = _stats(login="a", public_repos=10, total_stars=10, followers=1, commits_30d=1, account_age_days=200)
    b = _stats(login="b", public_repos=1, total_stars=1, followers=10, commits_30d=10, account_age_days=100)
    # a wins public_repos and total_stars (2); b wins followers, commits_30d, and account_age_days (3)
    result = score_battle(a, b)
    assert result.overall_winner == "b"
    assert result.score == "2-3"


def test_account_age_newer_wins() -> None:
    a = _stats(login="a", account_age_days=500)
    b = _stats(login="b", account_age_days=100)
    result = score_battle(a, b)
    # all other rows are 0-0 ties; account_age_days: b is newer, so b wins
    account_row = next(r for r in result.rows if r.label == "Account age (days)")
    assert account_row.winner == "b"
    assert result.overall_winner == "b"


def test_top_language_unscored() -> None:
    a = _stats(login="a", top_language="Python")
    b = _stats(login="b", top_language="Rust")
    result = score_battle(a, b)
    lang_row = next(r for r in result.rows if r.label == "Top language")
    assert lang_row.winner == "none"
    assert lang_row.value_a == "Python"
    assert lang_row.value_b == "Rust"


def test_top_language_none_renders_em_dash() -> None:
    a = _stats(login="a", top_language=None)
    b = _stats(login="b", top_language="Go")
    result = score_battle(a, b)
    lang_row = next(r for r in result.rows if r.label == "Top language")
    assert lang_row.value_a == "—"
    assert lang_row.value_b == "Go"


def test_large_numbers_are_formatted_with_thousands_separator() -> None:
    a = _stats(login="a", total_stars=12345)
    b = _stats(login="b", total_stars=1000)
    result = score_battle(a, b)
    stars_row = next(r for r in result.rows if r.label == "Total stars")
    assert stars_row.value_a == "12,345"
    assert stars_row.value_b == "1,000"


def test_row_order_is_stable() -> None:
    a = _stats(login="a")
    b = _stats(login="b")
    result = score_battle(a, b)
    labels = [r.label for r in result.rows]
    assert labels == [
        "Public repos",
        "Total stars",
        "Followers",
        "Commits (30d)",
        "Account age (days)",
        "Top language",
    ]
