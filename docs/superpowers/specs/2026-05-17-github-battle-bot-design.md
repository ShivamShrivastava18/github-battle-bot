# github-battle-bot — Design Spec

**Date:** 2026-05-17
**Status:** Approved (design phase complete, ready for implementation plan)

A private Discord bot that lets a small group of friends compare and roast each other's GitHub stats. Four slash commands: `/link`, `/stats`, `/battle`, `/roast`.

## Goals & non-goals

**Goals**
- Make it fun to share dev stats in a friend group's Discord server.
- Ship a complete v1 in a single working session (~600 LOC, ~20 tests).
- Self-hosted on a laptop during dev; trivially movable to a free tier (Railway/Fly) later.
- Cogs + helpers structure so adding commands later is one new file.

**Non-goals (v1)**
- Public bot listing, OAuth-based GitHub auth, GitHub App install flow.
- Persistent failure queues, Sentry-style error reporting, dashboards.
- Per-user cooldowns or per-server rate limiting.
- Cross-platform stats (GitLab, Bitbucket).
- A web UI, leaderboards, or history beyond what GitHub already exposes.

## Stack

- **Python 3.11+** (matches user's existing toolchain)
- **discord.py** — Discord client + slash commands
- **httpx** (async) — GitHub REST API
- **groq** SDK — `/roast` LLM call (free tier)
- **aiosqlite** — single `links` table for `discord_id ↔ github_login`
- **python-dotenv** — `.env` loader for tokens
- **pytest** + **pytest-asyncio** — tests

## Architecture

```
github-battle-bot/
├── .env                 # DISCORD_TOKEN, GITHUB_TOKEN, GROQ_API_KEY
├── .env.example         # same keys, no values, checked in
├── pyproject.toml
├── README.md
├── bot.py               # entry point: load env, build Bot, load cogs, run
└── ghbattle/
    ├── __init__.py
    ├── cogs/
    │   ├── __init__.py
    │   ├── link_cog.py      # /link
    │   ├── stats_cog.py     # /stats
    │   ├── battle_cog.py    # /battle
    │   └── roast_cog.py     # /roast
    ├── github_client.py     # PAT-authed, fetches the 8-field bundle
    ├── groq_client.py       # Groq chat call
    ├── db.py                # aiosqlite, links table
    ├── formatting.py        # discord.Embed builders
    ├── scoring.py           # pure: score_battle(a, b) -> BattleResult
    ├── personas.py          # 3 roast prompts + random.choice
    └── types.py             # Stats, BattleRow, BattleResult dataclasses
```

Each cog file stays under ~100 LOC. Helpers are pure functions or thin async clients — fully unit-testable without Discord running.

## Data flow

A `/battle @alice @bob` traverses the system like this:

```
discord gateway → battle_cog.battle()
                  ├── db.get_link(alice.id) → "alice_gh"
                  ├── db.get_link(bob.id)   → "bob_gh"
                  │   (if either is None → reply "@x hasn't /link'd yet")
                  ├── asyncio.gather(
                  │       github_client.get_stats("alice_gh"),
                  │       github_client.get_stats("bob_gh"),
                  │   )
                  ├── scoring.score_battle(stats_a, stats_b)
                  └── formatting.build_battle_embed(result)
                  → interaction.followup.send(embed=...)
```

`/stats` is the single-user version of the same flow. `/roast` is `/stats` + an appended Groq call with a randomly-picked persona.

## Stats bundle (8 fields)

Fetched per GitHub user. Cost: 3 API calls per user.

| Field | Source | Notes |
|---|---|---|
| `login`, `avatar_url`, `bio` | `GET /users/{login}` | One call |
| `public_repos`, `followers`, `account_age_days` | same call | (derive `account_age_days` from `created_at`) |
| `total_stars` | `GET /users/{login}/repos?per_page=100` | Sum `stargazers_count` across owned repos |
| `top_language` | same call | Group repos by `language`, pick the language with the highest summed stars |
| `commits_30d` | `GET /search/commits?q=author:{login}+committer-date:>{30d_ago}` | Public-repo commits authored by the user in the last 30 days; uses the `cloak-preview` accept header |

`top_language` ties broken by most-recently-pushed repo. Users with no public repos get `top_language = None` and `total_stars = 0` — formatted as "—" in the embed.

## Battle scoring

`scoring.score_battle(a: Stats, b: Stats) -> BattleResult` returns one row per compared field, marks a per-row winner, and computes the overall winner by majority of rows.

Comparison rules:

| Field | Winner rule |
|---|---|
| `public_repos`, `total_stars`, `followers`, `commits_30d` | higher wins |
| `top_language` | no comparison — shown in both columns, not scored |
| `account_age_days` | **newer** account wins (the underdog framing; configurable later) |
| any tie | counted as "tie" — does not give either side a point |

Five rows are scored (`public_repos`, `total_stars`, `followers`, `commits_30d`, `account_age_days`); `top_language` is shown but not scored. Overall winner: whichever side wins more scored rows. If equal, "tie". The `score` string shows win counts only (e.g. `3-2`); tied rows are absorbed and not displayed in the headline (e.g. 2 wins, 1 tie, 2 wins → `2-2` overall tie).

## Roast persona

`personas.pick_persona()` uniformly picks one of three prompts each call:

- **savage** — punches at the stats, dry tone
- **gentle** — affectionate dad-joke energy
- **meme** — dev-twitter cliché voice

Each prompt accepts the `Stats` dataclass and instructs Groq to return a single sentence, no preamble, no quotes. If Groq fails or times out, `/roast` degrades to a stats embed with a footer "(roast unavailable, try again)" — the command never blocks the user.

## Persistence

One SQLite file `ghbattle.db` in the repo root (gitignored). Single table:

```sql
CREATE TABLE IF NOT EXISTS links (
    discord_id   INTEGER PRIMARY KEY,
    github_login TEXT    NOT NULL
);
```

`db.get_link(discord_id) -> str | None` and `db.set_link(discord_id, github_login) -> None`. That's it.

No caching of `Stats` in v1 — friends won't query the same user often enough to matter. Adding a TTL cache later is a non-breaking change.

## Configuration

Single `.env` file, three required variables:

```
DISCORD_TOKEN=...           # Bot token from Discord Developer Portal
GITHUB_TOKEN=ghp_...        # Fine-grained PAT, public-data read scope only
GROQ_API_KEY=gsk_...        # Free tier from groq.com
```

`bot.py` fails at startup if any are missing — no fallbacks, no silent defaults. `.env.example` is checked in to make setup obvious.

## Error handling

**User-facing** (always reply, never raise into Discord):
- Caller hasn't `/link`'d → "Run `/link <your_github_username>` first."
- Battle opponent hasn't `/link`'d → "@target hasn't linked a GitHub account yet."
- `/link <name>` for a non-existent GitHub user → validated before insert → "No GitHub user found with that username. Typo?"
- Linked login now 404s → "GitHub doesn't know that username anymore. Try `/link` again?"

**Transient** (retry then degrade):
- GitHub 5xx / network timeout → httpx auto-retry x2 → if still failing, "GitHub's having a moment, try again in a sec."
- GitHub 403 rate-limited → parse `X-RateLimit-Reset` → reply with the reset time.
- Groq failure → catch in `roast_cog`, fall back to stats embed with footer note. `/roast` never fails entirely.

**Programmer errors** (let them crash, log them):
- Missing env var → fail at startup before connecting to Discord.
- Unhandled cog exception → stderr log, Discord interaction times out.

All cogs call `interaction.response.defer()` immediately to dodge Discord's 3-second response window, then `followup.send()` with the result.

Logging: `logging` stdlib, INFO level. One line per command: `INFO ghbattle.battle: alice vs bob -> alice 5-3`.

## Testing

Unit tests (`pytest` + `pytest-asyncio`), no Discord, no network:

| Test file | Coverage | ~tests |
|---|---|---|
| `tests/test_scoring.py` | Per-field winners, ties on each axis, all-tie outcome, overall tally math | 8 |
| `tests/test_formatting.py` | Embed builders produce expected fields/values; long-content truncation | 5 |
| `tests/test_personas.py` | `pick_persona()` returns one of three; each prompt has expected anchors | 3 |
| `tests/test_db.py` | `aiosqlite` against `:memory:`: set/get round-trip, missing returns None, upsert overwrites | 4 |

One integration test:

| `tests/test_github_client.py` | Fetch `octocat` (stable test account), assert `Stats` shape + types. Skipped via `pytest.mark.skipif(not os.environ.get("GITHUB_TOKEN"))`. |

No mock-Discord harness, no end-to-end tests, no coverage percentage target. Cogs are thin glue and exercised by manual smoke-test against the real Discord server.

`.github/workflows/test.yml` runs unit tests on push (skips the integration test unless `GITHUB_TOKEN` is configured as a secret).

## Out of scope for v1

- Caching of GitHub `Stats`
- `/duel` (random-axis battle), `/achievement` (rank titles) — slot in cleanly later
- Pretty avatar-based card images (vs Discord embeds)
- Cross-server data sharing or any public/community features
- Charts / graphs / activity timelines
- Authentication beyond a single shared PAT
