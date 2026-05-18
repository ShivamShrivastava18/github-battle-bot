from __future__ import annotations

import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from ghbattle.db import get_link
from ghbattle.formatting import build_battle_embed
from ghbattle.github_client import GitHubNotFound, GitHubRateLimited
from ghbattle.scoring import score_battle


log = logging.getLogger(__name__)


class BattleCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="battle",
        description="Head-to-head GitHub stats battle.",
    )
    @app_commands.describe(user_a="First contestant", user_b="Second contestant")
    async def battle(
        self,
        interaction: discord.Interaction,
        user_a: discord.User,
        user_b: discord.User,
    ) -> None:
        await interaction.response.defer()

        login_a = await get_link(self.bot.db_path, user_a.id)  # type: ignore[attr-defined]
        login_b = await get_link(self.bot.db_path, user_b.id)  # type: ignore[attr-defined]

        missing: list[str] = []
        if login_a is None:
            missing.append(user_a.mention)
        if login_b is None:
            missing.append(user_b.mention)
        if missing:
            who = " and ".join(missing)
            await interaction.followup.send(
                f"{who} need to `/link` a GitHub account first."
            )
            return

        try:
            stats_a, stats_b = await asyncio.gather(
                self.bot.gh.get_stats(login_a),  # type: ignore[attr-defined]
                self.bot.gh.get_stats(login_b),  # type: ignore[attr-defined]
            )
        except GitHubNotFound:
            await interaction.followup.send(
                "One of those GitHub accounts doesn't exist anymore."
            )
            return
        except GitHubRateLimited as e:
            await interaction.followup.send(
                f"Rate-limited until {e.reset_at.strftime('%H:%M:%S UTC')}. Try again then."
            )
            return
        except Exception:
            log.exception("GitHub error during /battle")
            await interaction.followup.send(
                "GitHub's having a moment, try again in a sec."
            )
            return

        result = score_battle(stats_a, stats_b)
        log.info(
            "battle: %s vs %s -> winner=%s score=%s",
            login_a, login_b, result.overall_winner, result.score,
        )
        await interaction.followup.send(embed=build_battle_embed(result))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BattleCog(bot))
