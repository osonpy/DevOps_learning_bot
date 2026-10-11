"""Integration: SQLite'da seed -> user -> dars -> takrorlash -> o'tkazish -> jarima -> scheduler tick."""
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("BOT_TOKEN", "1:test")

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db import repo
from src.db.base import Base
from src.db.models import Lesson, QuizQuestion, ReviewCard
from src.handlers.common import build_today
from src.scheduler import jobs
from src.scripts.seed import load_content, seed
from src.services import learning, render

ROOT = Path(__file__).resolve().parents[1]
MON = date(2026, 10, 12)  # Dushanba


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, **kw):
        self.sent.append((chat_id, text))


@pytest.fixture
async def sf(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    modules, lessons = load_content(ROOT / "content")
    async with factory() as s:
        await seed(s, modules, lessons)
    yield factory
    await engine.dispose()


async def test_curriculum_shape(sf):
    async with sf() as s:
        assert await repo.total_lessons(s, "junior") == 264
        first = await repo.get_lesson_by_day(s, 1)
        last = await repo.get_lesson_by_day(s, 264)
        assert first.key == "linux-01-intro" and first.week == 1
        assert last.key == "jf-06-gate" and last.week == 44
        # har dars Telegram limitiga (4096) sig'ishi kerak, jarima bloki bilan ham
        for day in range(1, 265):
            lesson = await repo.get_lesson_by_day(s, day)
            text = render.lesson_card(lesson)
            assert len(text) < 3600, (lesson.key, len(text))
            assert lesson.questions, lesson.key


async def test_reseed_keeps_ids(sf):
    """Qayta seed savol id'larini saqlaydi -> takrorlash kartalari yo'qolmaydi."""
    async with sf() as s:
        ids_before = set(await s.scalars(select(QuizQuestion.id)))
        modules, lessons = load_content(ROOT / "content")
        await seed(s, modules, lessons)
        ids_after = set(await s.scalars(select(QuizQuestion.id)))
        assert ids_before == ids_after
        assert await s.scalar(select(func.count(Lesson.id))) == 264


async def test_full_flow_with_penalty_and_review(sf):
    async with sf() as s:
        user, created = await repo.get_or_create_user(s, 42, "osonpy", "Osonbek Test", MON)
        assert created and user.current_day == 1

        lesson = await repo.get_lesson_by_day(s, 1)
        res = await learning.complete_lesson(s, user, lesson, MON)
        assert res.ok and user.streak == 1 and user.current_day == 2
        # dars savollari takrorlash kartasiga aylandi, ertaga due
        assert await repo.due_count(s, user.id, MON) == 0
        assert await repo.due_count(s, user.id, MON + timedelta(days=1)) == len(lesson.questions)

        # takrorlash: to'g'ri javob -> box 1, 3 kundan keyin
        tue = MON + timedelta(days=1)
        card = (await repo.due_cards(s, user.id, tue, 1))[0]
        r = await learning.answer_card(s, user, card, card.question.correct_index, tue)
        assert r.ok and card.box == 1 and card.due_date == tue + timedelta(days=3)
        # xato javob -> box 0, ertaga
        card2 = (await repo.due_cards(s, user.id, tue, 1))[0]
        wrong = (card2.question.correct_index + 1) % len(card2.question.options)
        r = await learning.answer_card(s, user, card2, wrong, tue)
        assert not r.ok and card2.box == 0 and card2.lapses == 1

        # Se..Pa o'tkazildi (3 kun) -> Juma: quiz jarima
        fri = MON + timedelta(days=4)
        check = await learning.run_daily_check(s, user, fri)
        assert check.missed == 3 and user.streak == 0
        assert check.penalty is not None and check.penalty.kind == "quiz"
        await learning.resolve_penalty(check.penalty)
        lesson2 = await repo.get_lesson_by_day(s, 2)
        res = await learning.complete_lesson(s, user, lesson2, fri, with_penalty=True)
        assert res.ok and user.streak == 1
        await s.commit()

    async with sf() as s:
        user = await repo.get_user(s, 42)
        nxt = fri + timedelta(days=8)  # 6 majburiy kun o'tkazildi -> hardcore
        check = await learning.run_daily_check(s, user, nxt)
        assert check.missed == 6 and check.penalty.kind == "hardcore"
        assert check.penalty.hardcore_task_id is not None


async def test_scheduler_weekday_and_sunday(sf):
    bot = FakeBot()
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, 7, None, "Ali", MON - timedelta(days=1))
        await s.commit()
    # Dushanba 09:00 Toshkent = 04:00 UTC -> dars kartasi, bir marta
    t = datetime(2026, 10, 12, 4, 0, tzinfo=timezone.utc)
    await jobs.tick(bot, sf, now_utc=t)
    await jobs.tick(bot, sf, now_utc=t + timedelta(minutes=1))
    assert len(bot.sent) == 1 and "#1" in bot.sent[0][1]

    # 21:00 — bajarilmagan -> nudge (bir marta)
    t2 = datetime(2026, 10, 12, 16, 0, tzinfo=timezone.utc)
    await jobs.tick(bot, sf, now_utc=t2)
    await jobs.tick(bot, sf, now_utc=t2 + timedelta(minutes=1))
    assert len(bot.sent) == 2

    # Du-Sh har kuni bitta dars, so'ng Yakshanba: takrorlash kuni xabari (jarima yo'q)
    async with sf() as s:
        user = await repo.get_user(s, 7)
        for i in range(6):
            lesson = await repo.get_lesson_by_day(s, i + 1)
            res = await learning.complete_lesson(s, user, lesson, MON + timedelta(days=i))
            assert res.ok
        assert user.streak == 6
        await s.commit()
    sun = datetime(2026, 10, 18, 4, 0, tzinfo=timezone.utc)
    await jobs.tick(bot, sf, now_utc=sun)
    assert "takrorlash kuni" in bot.sent[-1][1].lower()


async def test_sunday_user_can_still_open_lesson(sf):
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, 9, None, "Vali", MON)
        sunday = MON + timedelta(days=6)
        text, _ = await build_today(s, user, today=sunday)  # foydalanuvchi o'zi bosdi
        assert "#1" in text


async def test_review_card_limit(sf):
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, 11, None, "Test", MON)
        for day in range(1, 7):
            lesson = await repo.get_lesson_by_day(s, day)
            await repo.schedule_cards(s, user.id, lesson, MON)
        total_due = await repo.due_count(s, user.id, MON)
        assert total_due >= 12
        from src.handlers.common import reviews_left
        assert await reviews_left(s, user, MON) == 8  # ish kuni limiti
        assert await s.scalar(select(func.count(ReviewCard.id))) == total_due
