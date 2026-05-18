from __future__ import annotations

from groq import AsyncGroq

from ghbattle.types import Stats


_MODEL = "llama-3.3-70b-versatile"
_MAX_TOKENS = 80


def _stats_block(stats: Stats) -> str:
    return (
        f"login: {stats.login}\n"
        f"bio: {stats.bio or '(none)'}\n"
        f"public repos: {stats.public_repos}\n"
        f"total stars: {stats.total_stars}\n"
        f"followers: {stats.followers}\n"
        f"commits (last 30d): {stats.commits_30d}\n"
        f"top language: {stats.top_language or '(none)'}\n"
        f"account age (days): {stats.account_age_days}"
    )


class GroqClient:
    def __init__(self, api_key: str) -> None:
        self._client = AsyncGroq(api_key=api_key)

    async def roast(self, stats: Stats, prompt_template: str) -> str:
        prompt = prompt_template.format(stats_block=_stats_block(stats))
        resp = await self._client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=_MAX_TOKENS,
            temperature=0.9,
        )
        text = resp.choices[0].message.content or ""
        return text.strip().strip('"').strip("'")
