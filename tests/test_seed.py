"""Seed: parallel ishga tushganda Postgres advisory lock bilan himoyalangan."""
import os
from types import SimpleNamespace

os.environ.setdefault("BOT_TOKEN", "1:test")

from src.scripts import seed


class FakeSession:
    def __init__(self, dialect: str):
        self.bind = SimpleNamespace(dialect=SimpleNamespace(name=dialect))
        self.executed: list[tuple[str, dict]] = []

    async def execute(self, stmt, params=None):
        self.executed.append((str(stmt), params or {}))


async def test_seed_lock_on_postgres():
    s = FakeSession("postgresql")
    await seed.acquire_seed_lock(s)
    assert len(s.executed) == 1
    sql, params = s.executed[0]
    assert "pg_advisory_xact_lock" in sql and params == {"key": seed.SEED_LOCK_KEY}


async def test_seed_lock_skipped_on_sqlite():
    s = FakeSession("sqlite")
    await seed.acquire_seed_lock(s)
    assert s.executed == []
