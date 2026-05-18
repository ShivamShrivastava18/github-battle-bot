from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from ghbattle.db import set_link


log = logging.getLogger(__name__)


class LinkCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="link",
        description="Link your Discord identity to a GitHub username.",
    )
    @app_commands.describe(github_username="Your GitHub username")
    async def link(
        self, interaction: discord.Interaction, github_username: str
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        login = github_username.strip().lstrip("@")

        try:
            exists = await self.bot.gh.user_exists(login)  # type: ignore[attr-defined]
        except Exception:
            log.exception("GitHub error during /link for %s", login)
            await interaction.followup.send(
                "GitHub's having a moment, try again in a sec."
            )
            return

        if not exists:
            await interaction.followup.send(
                f"No GitHub user found with username `{login}`. Typo?"
            )
            return

        await set_link(self.bot.db_path, interaction.user.id, login)  # type: ignore[attr-defined]
        log.info("link: %s -> %s", interaction.user, login)
        await interaction.followup.send(
            f"Linked {interaction.user.mention} → `{login}`"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LinkCog(bot))
