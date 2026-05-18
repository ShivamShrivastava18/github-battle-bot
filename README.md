# github-battle-bot

A Discord bot for friend groups to compare and roast each other's GitHub stats.

## Commands

- `/link <github_username>` — link your Discord identity to a GitHub login (run once per person)
- `/stats [@user]` — solo profile card (defaults to caller)
- `/battle @userA @userB` — head-to-head scorecard across five scored fields, plus top language
- `/roast [@user]` — LLM-generated one-line roast based on real stats (random persona: savage / gentle / meme)

## Setup

### 1. Tokens

You need three secrets:

- **Discord bot token** — Discord Developer Portal → New Application → Bot → Reset Token. Add the bot to your server with the `applications.commands` scope.
- **GitHub PAT** — github.com → Settings → Developer settings → Fine-grained PAT, read-only public scope, no specific repo access needed.
- **Groq API key** — groq.com → Console → API Keys.

Copy `.env.example` to `.env` and fill them in:

```
DISCORD_TOKEN=...
GITHUB_TOKEN=ghp_...
GROQ_API_KEY=gsk_...
```

### 2. Install and run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python bot.py
```

The bot syncs its slash commands on startup; you'll see them in the server within a few seconds.

### 3. Tests

```bash
pytest -q
```

The GitHub-API integration tests are skipped unless `GITHUB_TOKEN` is set in the environment.

## Stack

Python 3.11+ · `discord.py` · `httpx` · `aiosqlite` · `groq` SDK
