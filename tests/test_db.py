from __future__ import annotations

import pytest

from ghbattle.db import get_link, init_db, set_link


@pytest.fixture
async def db_path(tmp_path):
    p = str(tmp_path / "test.db")
    await init_db(p)
    return p


async def test_get_missing_returns_none(db_path) -> None:
    assert await get_link(db_path, 12345) is None


async def test_set_then_get_round_trips(db_path) -> None:
    await set_link(db_path, 12345, "octocat")
    assert await get_link(db_path, 12345) == "octocat"


async def test_set_overwrites_existing(db_path) -> None:
    await set_link(db_path, 12345, "octocat")
    await set_link(db_path, 12345, "torvalds")
    assert await get_link(db_path, 12345) == "torvalds"


async def test_separate_users_dont_collide(db_path) -> None:
    await set_link(db_path, 1, "alice")
    await set_link(db_path, 2, "bob")
    assert await get_link(db_path, 1) == "alice"
    assert await get_link(db_path, 2) == "bob"
