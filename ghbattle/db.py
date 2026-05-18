from __future__ import annotations

import aiosqlite


SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    discord_id   INTEGER PRIMARY KEY,
    github_login TEXT    NOT NULL
)
"""


async def init_db(path: str) -> None:
    async with aiosqlite.connect(path) as db:
        await db.execute(SCHEMA)
        await db.commit()


async def get_link(path: str, discord_id: int) -> str | None:
    async with aiosqlite.connect(path) as db:
        cursor = await db.execute(
            "SELECT github_login FROM links WHERE discord_id = ?",
            (discord_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def set_link(path: str, discord_id: int, github_login: str) -> None:
    async with aiosqlite.connect(path) as db:
        await db.execute(
            "INSERT INTO links (discord_id, github_login) VALUES (?, ?) "
            "ON CONFLICT(discord_id) DO UPDATE SET github_login = excluded.github_login",
            (discord_id, github_login),
        )
        await db.commit()
