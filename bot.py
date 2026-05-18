from __future__ import annotations

import asyncio
import logging
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

from ghbattle.db import init_db
from ghbattle.github_client import GitHubClient
from ghbattle.groq_client import GroqClient


DB_PATH = "ghbattle.db"

_COGS = (
    "ghbattle.cogs.link_cog",
    "ghbattle.cogs.stats_cog",
    "ghbattle.cogs.battle_cog",
    "ghbattle.cogs.roast_cog",
)


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        print(f"Missing required env var: {name}", file=sys.stderr)
        sys.exit(1)
    return val


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    load_dotenv()
    discord_token = _require("DISCORD_TOKEN")
    github_token = _require("GITHUB_TOKEN")
    groq_api_key = _require("GROQ_API_KEY")

    await init_db(DB_PATH)

    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)

    bot.gh = GitHubClient(github_token)         # type: ignore[attr-defined]
    bot.groq = GroqClient(groq_api_key)         # type: ignore[attr-defined]
    bot.db_path = DB_PATH                       # type: ignore[attr-defined]

    for cog in _COGS:
        await bot.load_extension(cog)

    @bot.event
    async def on_ready() -> None:
        synced = await bot.tree.sync()
        logging.info(f"Logged in as {bot.user}; synced {len(synced)} commands")

    try:
        await bot.start(discord_token)
    finally:
        await bot.gh.close()                    # type: ignore[attr-defined]


if __name__ == "__main__":
    asyncio.run(main())
