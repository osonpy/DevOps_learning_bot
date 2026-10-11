"""Bir user'da bir vaqtda faqat bitta faol jarima (DB darajasida)."""
import os
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("BOT_TOKEN", "1:test")

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db import repo
from src.db.base import Base
from src.db.models import Penalty
from src.scripts.seed import load_content, seed
from src.services import learning

ROOT = Path(__file__).resolve().parents[1]
MON = date(2026, 10, 12)


@pytest.fixture
async def sf(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        await seed(s, *load_content(ROOT / "content"))
    yield factory
    await engine.dispose()


async def active_count(s, user_id):
    return await s.scalar(select(func.count(Penalty.id)).where(Penalty.user_id == user_id, Penalty.status == "active"))


async def test_db_rejects_second_active_penalty(sf):
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, 1, None, "Ali", MON)
        lesson = await repo.current_lesson(s, user)
        s.add_all([Penalty(user_id=user.id, lesson_id=lesson.id, kind="quiz", missed_days=3),
                   Penalty(user_id=user.id, lesson_id=lesson.id, kind="quiz", missed_days=3)])
        with pytest.raises(IntegrityError):
            await s.flush()


async def test_create_penalty_returns_existing_active(sf):
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, 1, None, "Ali", MON)
        lesson = await repo.current_lesson(s, user)
        p1 = await repo.create_penalty(s, user, lesson, "quiz", 3, None)
        p2 = await repo.create_penalty(s, user, lesson, "quiz", 3, None)
        assert p2.id == p1.id
        assert await active_count(s, user.id) == 1
        await s.commit()  # sessiya ishlashda davom etadi


async def test_resolved_penalties_do_not_block_new_one(sf):
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, 1, None, "Ali", MON)
        lesson = await repo.current_lesson(s, user)
        p1 = await repo.create_penalty(s, user, lesson, "quiz", 3, None)
        await learning.resolve_penalty(p1)
        p2 = await repo.create_penalty(s, user, lesson, "quiz", 4, None)
        assert p2.id != p1.id and await active_count(s, user.id) == 1


async def test_quiz_escalates_to_hardcore(sf):
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, 1, None, "Ali", MON)
        quiz = (await learning.run_daily_check(s, user, MON + timedelta(days=3))).penalty
        assert quiz.kind == "quiz"
        hard = (await learning.run_daily_check(s, user, MON + timedelta(days=6))).penalty
        assert hard.kind == "hardcore" and quiz.status == "resolved"
        assert await active_count(s, user.id) == 1
