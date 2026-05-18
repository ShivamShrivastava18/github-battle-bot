from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from ghbattle.db import get_link
from ghbattle.formatting import build_roast_embed
from ghbattle.github_client import GitHubNotFound
from ghbattle.personas import pick_persona


log = logging.getLogger(__name__)


class RoastCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="roast",
        description="LLM-generated one-liner roast based on real GitHub stats.",
    )
    @app_commands.describe(user="The Discord user to roast (defaults to you)")
    async def roast(
        self,
        interaction: discord.Interaction,
        user: discord.User | None = None,
    ) -> None:
        await interaction.response.defer()
        target = user or interaction.user
        login = await get_link(self.bot.db_path, target.id)  # type: ignore[attr-defined]
        if login is None:
            await interaction.followup.send(
                f"{target.mention} hasn't linked a GitHub account yet — "
                "they need to run `/link` first."
            )
            return

        try:
            stats = await self.bot.gh.get_stats(login)  # type: ignore[attr-defined]
        except GitHubNotFound:
            await interaction.followup.send(
                f"GitHub doesn't know `{login}` anymore."
            )
            return
        except Exception:
            log.exception("GitHub error during /roast for %s", login)
            await interaction.followup.send(
                "GitHub's having a moment, try again in a sec."
            )
            return

        persona_name, prompt = pick_persona()
        try:
            roast_text = await self.bot.groq.roast(stats, prompt)  # type: ignore[attr-defined]
        except Exception:
            log.warning("Groq failed for %s; degrading to stats only", login)
            roast_text = ""

        log.info("roast: %s -> %s (persona=%s)", interaction.user, login, persona_name)
        await interaction.followup.send(
            embed=build_roast_embed(stats, roast_text, persona_name)
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RoastCog(bot))
