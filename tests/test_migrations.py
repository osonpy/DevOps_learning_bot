"""Alembic: initial migratsiya Postgres'ga qarshi generatsiya qilingan va modellar bilan mos."""
import asyncio
import os
from pathlib import Path

os.environ.setdefault("BOT_TOKEN", "1:test")

from datetime import date

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings
from src.db import (
    models,  # noqa: F401
    repo,
)
from src.db.base import Base
from src.scripts.seed import load_content, seed

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = sorted((ROOT / "migrations" / "versions").glob("*.py"))


def test_migrations_generated_against_postgres():
    assert VERSIONS[0].name.startswith("0001_")  # initial — Postgres'ga qarshi
    for path in VERSIONS:
        src = path.read_text(encoding="utf-8")
        assert "batch_alter_table" not in src, path.name
        assert "CURRENT_TIMESTAMP)" not in src, path.name  # SQLite'dan generatsiya izi
        assert "sa.text('now()')" not in src, path.name  # SQLite'da yo'q — sa.func.now() ishlatiladi


def test_migrations_upgrade_and_match_models_on_sqlite(tmp_path, monkeypatch):
    """Lokal (Docker'siz) ishlab chiqish: `alembic upgrade head` SQLite'da ham ishlaydi va drift yo'q."""
    url = f"sqlite+aiosqlite:///{tmp_path}/m.db"
    monkeypatch.setattr(settings, "database_url", url)
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(cfg, "head")

    async def diff_and_use():
        engine = create_async_engine(url)
        async with engine.connect() as conn:
            result = await conn.run_sync(lambda c: compare_metadata(MigrationContext.configure(c), Base.metadata))
        # server_default'lar (created_at) SQLite'da ham ishlashi kerak
        async with async_sessionmaker(engine)() as s:
            await seed(s, *load_content(ROOT / "content"))
            await repo.get_or_create_user(s, 1, None, "Ali", date(2026, 10, 12))
            await s.commit()
        await engine.dispose()
        return result

    assert asyncio.run(diff_and_use()) == []
    command.downgrade(cfg, "base")


def test_partial_unique_index_for_active_penalty():
    src = VERSIONS[0].read_text(encoding="utf-8")
    assert "uq_penalties_user_active" in src
    assert "postgresql_where=sa.text(\"status = 'active'\")" in src
