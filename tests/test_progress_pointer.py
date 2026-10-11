"""Progress dars id'siga bog'langan: kontent tartibi o'zgarsa yoki dars o'chirilsa user adashmaydi."""
import os
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("BOT_TOKEN", "1:test")

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db import repo
from src.db.base import Base
from src.scripts.seed import load_content, seed
from src.services import learning

ROOT = Path(__file__).resolve().parents[1]
MON = date(2026, 10, 12)


def content():
    return load_content(ROOT / "content")


def swap_first_modules(modules, lessons):
    """1- va 2-modul o'rnini almashtiradi (darslar ham shu tartibda)."""
    modules = [modules[1], modules[0], *modules[2:]]
    order = {m["slug"]: i for i, m in enumerate(modules)}
    return modules, sorted(lessons, key=lambda pair: order[pair[0]])


@pytest.fixture
async def sf(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        await seed(s, *content())
    yield factory
    await engine.dispose()


async def complete_n(s, user, n):
    for i in range(n):
        lesson = await repo.current_lesson(s, user)
        res = await learning.complete_lesson(s, user, lesson, MON + timedelta(days=i))
        assert res.ok, res.message


async def test_new_user_starts_at_first_lesson(sf):
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, 1, None, "Ali", MON)
        first = await repo.get_lesson_by_day(s, 1)
        assert user.current_lesson_id == first.id
        assert (await repo.current_lesson(s, user)).id == first.id


async def test_next_lesson_is_smallest_active_day_after_current(sf):
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, 1, None, "Ali", MON)
        await complete_n(s, user, 2)
        assert (await repo.current_lesson(s, user)).day_number == 3


async def test_reorder_modules_keeps_user_on_same_lesson(sf):
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, 1, None, "Ali", MON)
        await complete_n(s, user, 2)
        before = await repo.current_lesson(s, user)
        before_key, before_day = before.key, before.day_number  # obyekt identity map'da — seed uni yangilaydi
        await s.commit()

        await seed(s, *swap_first_modules(*content()))
        await s.refresh(user)
        after = await repo.current_lesson(s, user)
        assert after.key == before_key
        assert after.day_number != before_day  # raqam o'zgardi, dars — yo'q

        # keyingi dars yangi tartib bo'yicha: joriy darsdan keyingi eng kichik day_number
        res = await learning.complete_lesson(s, user, after, MON + timedelta(days=3))
        assert res.ok
        assert (await repo.current_lesson(s, user)).day_number == after.day_number + 1


async def test_deleted_current_lesson_moves_user_to_next_active(sf):
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, 1, None, "Ali", MON)
        await complete_n(s, user, 2)
        current = await repo.current_lesson(s, user)
        following = await repo.get_lesson_by_day(s, current.day_number + 1)
        await s.commit()

        modules, lessons = content()
        await seed(s, modules, [pair for pair in lessons if pair[1]["key"] != current.key])
        await s.refresh(user)
        assert (await repo.current_lesson(s, user)).key == following.key


async def test_finished_user_gets_newly_added_lesson(sf):
    modules, lessons = content()
    async with sf() as s:
        await seed(s, modules, lessons[:3])  # kurs 3 ta darsdan iborat
        user, _ = await repo.get_or_create_user(s, 1, None, "Ali", MON)
        await complete_n(s, user, 3)
        assert await repo.current_lesson(s, user) is None
        await s.commit()

        await seed(s, modules, lessons[:4])  # yangi dars qo'shildi
        await s.refresh(user)
        assert (await repo.current_lesson(s, user)).key == lessons[3][1]["key"]
