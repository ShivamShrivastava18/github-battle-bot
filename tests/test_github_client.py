from __future__ import annotations

import os

import pytest

from ghbattle.github_client import GitHubClient


_HAS_TOKEN = bool(os.environ.get("GITHUB_TOKEN"))


@pytest.mark.skipif(not _HAS_TOKEN, reason="needs GITHUB_TOKEN env var")
async def test_get_stats_octocat() -> None:
    async with GitHubClient(os.environ["GITHUB_TOKEN"]) as gh:
        stats = await gh.get_stats("octocat")

    assert stats.login == "octocat"
    assert isinstance(stats.public_repos, int)
    assert isinstance(stats.total_stars, int)
    assert isinstance(stats.followers, int)
    assert isinstance(stats.commits_30d, int)
    assert isinstance(stats.account_age_days, int)
    assert stats.account_age_days > 365 * 10  # octocat is ancient
    assert stats.avatar_url.startswith("https://")


@pytest.mark.skipif(not _HAS_TOKEN, reason="needs GITHUB_TOKEN env var")
async def test_user_exists_true() -> None:
    async with GitHubClient(os.environ["GITHUB_TOKEN"]) as gh:
        assert await gh.user_exists("octocat") is True


@pytest.mark.skipif(not _HAS_TOKEN, reason="needs GITHUB_TOKEN env var")
async def test_user_exists_false() -> None:
    async with GitHubClient(os.environ["GITHUB_TOKEN"]) as gh:
        assert await gh.user_exists("this-user-does-not-exist-xyz-12345") is False
