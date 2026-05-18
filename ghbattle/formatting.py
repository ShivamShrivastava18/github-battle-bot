from __future__ import annotations

import discord

from ghbattle.types import BattleResult, Stats


_WIN_EMOJI = "👑"
_TIE_EMOJI = "🤝"


def _fmt_int(n: int) -> str:
    return f"{n:,}"


def build_stats_embed(stats: Stats) -> discord.Embed:
    embed = discord.Embed(
        title=stats.login,
        url=f"https://github.com/{stats.login}",
        description=stats.bio or "*(no bio)*",
        color=0x6E5494,
    )
    if stats.avatar_url:
        embed.set_thumbnail(url=stats.avatar_url)
    embed.add_field(name="Public repos", value=_fmt_int(stats.public_repos))
    embed.add_field(name="Total stars", value=_fmt_int(stats.total_stars))
    embed.add_field(name="Followers", value=_fmt_int(stats.followers))
    embed.add_field(name="Commits (30d)", value=_fmt_int(stats.commits_30d))
    embed.add_field(name="Top language", value=stats.top_language or "—")
    embed.add_field(name="Account age (days)", value=_fmt_int(stats.account_age_days))
    return embed


def build_battle_embed(result: BattleResult) -> discord.Embed:
    a, b = result.a, result.b
    a_wins, b_wins = result.score.split("-")

    if result.overall_winner == "a":
        title = f"{_WIN_EMOJI} {a.login} beats {b.login} ({a_wins}-{b_wins})"
        color = 0x2EA043
    elif result.overall_winner == "b":
        title = f"{_WIN_EMOJI} {b.login} beats {a.login} ({b_wins}-{a_wins})"
        color = 0x2EA043
    else:
        title = f"{_TIE_EMOJI} {a.login} vs {b.login} — TIE ({a_wins}-{b_wins})"
        color = 0xBF8700

    embed = discord.Embed(title=title, color=color)
    embed.set_author(name=f"{a.login} vs {b.login}")

    lines: list[str] = []
    for row in result.rows:
        mark_a = f" {_WIN_EMOJI}" if row.winner == "a" else ""
        mark_b = f" {_WIN_EMOJI}" if row.winner == "b" else ""
        lines.append(f"**{row.label}** — {row.value_a}{mark_a}  vs  {row.value_b}{mark_b}")
    embed.description = "\n".join(lines)
    return embed


def build_roast_embed(stats: Stats, roast: str, persona: str) -> discord.Embed:
    embed = build_stats_embed(stats)
    embed.add_field(
        name=f"🔥 Roast ({persona})",
        value=roast or "*(roast unavailable, try `/roast` again)*",
        inline=False,
    )
    return embed
