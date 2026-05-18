from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from ghbattle.types import Stats


class GitHubError(Exception):
    pass


class GitHubNotFound(GitHubError):
    pass


class GitHubRateLimited(GitHubError):
    def __init__(self, reset_at: datetime):
        self.reset_at = reset_at
        super().__init__(f"Rate limited until {reset_at.isoformat()}")


class GitHubClient:
    def __init__(self, token: str, *, base_url: str = "https://api.github.com") -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            transport=httpx.AsyncHTTPTransport(retries=2),
            timeout=httpx.Timeout(10.0),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def user_exists(self, login: str) -> bool:
        try:
            await self._get(f"/users/{login}")
            return True
        except GitHubNotFound:
            return False

    async def get_stats(self, login: str) -> Stats:
        user = await self._get(f"/users/{login}")
        repos = await self._get(f"/users/{login}/repos?per_page=100&type=owner")

        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        public_repos = user.get("public_repos", 0)
        followers = user.get("followers", 0)
        created_at = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
        account_age_days = (datetime.now(UTC) - created_at).days
        top_language = self._top_language(repos)
        commits_30d = await self._count_commits_30d(login)

        return Stats(
            login=user["login"],
            avatar_url=user.get("avatar_url", ""),
            bio=user.get("bio"),
            public_repos=public_repos,
            total_stars=total_stars,
            followers=followers,
            commits_30d=commits_30d,
            top_language=top_language,
            account_age_days=account_age_days,
        )

    def _top_language(self, repos: list[dict[str, Any]]) -> str | None:
        lang_stars: Counter[str] = Counter()
        lang_latest: dict[str, str] = {}
        for r in repos:
            lang = r.get("language")
            if not lang:
                continue
            lang_stars[lang] += r.get("stargazers_count", 0)
            pushed = r.get("pushed_at") or ""
            if pushed > lang_latest.get(lang, ""):
                lang_latest[lang] = pushed
        if not lang_stars:
            return None
        return sorted(
            lang_stars,
            key=lambda l: (lang_stars[l], lang_latest.get(l, "")),
            reverse=True,
        )[0]

    async def _count_commits_30d(self, login: str) -> int:
        since = (datetime.now(UTC) - timedelta(days=30)).date().isoformat()
        try:
            data = await self._get(
                f"/search/commits?q=author:{login}+committer-date:>{since}&per_page=1",
                accept="application/vnd.github.cloak-preview+json",
            )
            return data.get("total_count", 0)
        except GitHubError:
            return 0

    async def _get(self, path: str, *, accept: str | None = None) -> Any:
        headers: dict[str, str] = {}
        if accept:
            headers["Accept"] = accept
        resp = await self._client.get(path, headers=headers)
        if resp.status_code == 404:
            raise GitHubNotFound(f"GitHub 404: {path}")
        if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
            reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
            raise GitHubRateLimited(datetime.fromtimestamp(reset_ts, tz=UTC))
        resp.raise_for_status()
        return resp.json()
