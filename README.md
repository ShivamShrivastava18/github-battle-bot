# github-battle-bot

A private Discord bot for friend groups to compare and roast each other's GitHub stats. Four slash commands:

- `/link <github_username>` — map your Discord identity to a GitHub login
- `/stats [@user]` — solo profile card (defaults to caller)
- `/battle @userA @userB` — head-to-head 8-field scorecard with overall winner
- `/roast [@user]` — LLM-generated one-liner roast based on real stats

## Status

In design. See [`docs/superpowers/specs/2026-05-17-github-battle-bot-design.md`](docs/superpowers/specs/2026-05-17-github-battle-bot-design.md) for the full design spec.

## Stack

Python 3.11+ · discord.py · httpx · aiosqlite · groq SDK
