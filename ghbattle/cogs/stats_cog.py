from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from ghbattle.db import get_link
from ghbattle.formatting import build_stats_embed
from ghbattle.github_client import GitHubNotFound, GitHubRateLimited


log = logging.getLogger(__name__)


class StatsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="stats",
        description="Show a user's GitHub stats card.",
    )
    @app_commands.describe(user="The Discord user to look up (defaults to you)")
    async def stats(
        self,
        interaction: discord.Interaction,
        user: discord.User | None = None,
    ) -> None:
        await interaction.response.defer()
        target = user or interaction.user
        login = await get_link(self.bot.db_path, target.id)  # type: ignore[attr-defined]
        if login is None:
            if target.id == interaction.user.id:
                msg = "You haven't linked a GitHub account yet — run `/link <github_username>` first."
            else:
                msg = (
                    f"{target.mention} hasn't linked a GitHub account yet — "
                    "they need to run `/link` first."
                )
            await interaction.followup.send(msg)
            return

        try:
            stats = await self.bot.gh.get_stats(login)  # type: ignore[attr-defined]
        except GitHubNotFound:
            await interaction.followup.send(
                f"GitHub doesn't know `{login}` anymore. Try `/link` again."
            )
            return
        except GitHubRateLimited as e:
            await interaction.followup.send(
                f"Rate-limited until {e.reset_at.strftime('%H:%M:%S UTC')}. Try again then."
            )
            return
        except Exception:
            log.exception("GitHub error during /stats for %s", login)
            await interaction.followup.send(
                "GitHub's having a moment, try again in a sec."
            )
            return

        log.info("stats: %s -> %s", interaction.user, login)
        await interaction.followup.send(embed=build_stats_embed(stats))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StatsCog(bot))
