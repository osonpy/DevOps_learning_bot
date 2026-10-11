"""Handler'lar: ro'yxatdan o'tmagan user guard'i va cb.message mavjud bo'lmagan callback'lar."""
import os
from datetime import date
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("BOT_TOKEN", "1:test")

import pytest
from aiogram.types import CallbackQuery, Chat, InaccessibleMessage
from aiogram.types import User as TgUser
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db import repo
from src.db.base import Base
from src.db.models import QuizAttempt
from src.handlers import lesson as lesson_handlers
from src.handlers.common import drop_keyboard, reply_target
from src.keyboards.callbacks import LessonCB, QuizCB
from src.middlewares.user import UserMiddleware
from src.scripts.seed import load_content, seed

ROOT = Path(__file__).resolve().parents[1]
TG_ID = 42


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []
        self.calls: list = []

    async def send_message(self, chat_id, text, **kw):
        self.sent.append((chat_id, text))

    async def __call__(self, method, request_timeout=None):  # cb.answer() va boshqa API chaqiruvlari
        self.calls.append(method)
        return True


class FakeEvent:
    def __init__(self):
        self.answers: list[str] = []

    async def answer(self, text=None, **kw):
        self.answers.append(text)


def callback(bot: FakeBot, message=None) -> CallbackQuery:
    cb = CallbackQuery(id="1", from_user=TgUser(id=TG_ID, is_bot=False, first_name="Ali"),
                       chat_instance="ci", data="x", message=message)
    return cb.as_(bot)


def inaccessible() -> InaccessibleMessage:
    return InaccessibleMessage(chat=Chat(id=TG_ID, type="private"), message_id=1, date=0)


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


# ───────── guard ─────────
async def test_guard_blocks_unknown_user(sf):
    called = False

    async def handler(event, data):
        nonlocal called
        called = True

    event = FakeEvent()
    async with sf() as s:
        await UserMiddleware()(handler, event, {"session": s, "event_from_user": SimpleNamespace(id=999)})
    assert not called
    assert event.answers and "/start" in event.answers[0]


async def test_guard_passes_user_to_handler(sf):
    got = {}

    async def handler(event, data):
        got.update(data)

    async with sf() as s:
        await repo.get_or_create_user(s, TG_ID, None, "Ali", date(2026, 10, 12))
        await UserMiddleware()(handler, FakeEvent(), {"session": s, "event_from_user": SimpleNamespace(id=TG_ID)})
    assert got["user"].tg_id == TG_ID


def test_guard_registered_on_all_user_routers():
    from src.handlers import lesson, progress, review, settings, start

    for router in (lesson.router, progress.router, review.router, settings.router):
        for observer in (router.message, router.callback_query):
            assert any(isinstance(m, UserMiddleware) for m in observer.middleware), (router.name, observer.event_name)
    assert not start.router.message.middleware  # /start user'ni o'zi yaratadi


# ───────── cb.message yo'q ─────────
@pytest.mark.parametrize("message", [None, inaccessible()])
async def test_reply_target_falls_back_to_private_chat(message):
    bot = FakeBot()
    cb = callback(bot, message)
    await reply_target(cb).answer("salom")
    await drop_keyboard(cb)  # xato bermasligi kerak
    assert bot.sent == [(TG_ID, "salom")]


@pytest.mark.parametrize("message", [None, inaccessible()])
async def test_done_with_inaccessible_message(sf, message):
    bot = FakeBot()
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, TG_ID, None, "Ali", date(2026, 10, 12))
        first = await repo.get_lesson_by_day(s, 1)
        await lesson_handlers.done(callback(bot, message), LessonCB(action="done", lesson_id=first.id), s, user)
        assert await repo.is_completed(s, user.id, first.id)
    assert bot.sent and bot.sent[0][0] == TG_ID


async def test_quiz_answer_with_inaccessible_message(sf):
    bot = FakeBot()
    async with sf() as s:
        user, _ = await repo.get_or_create_user(s, TG_ID, None, "Ali", date(2026, 10, 12))
        first = await repo.get_lesson_by_day(s, 1)
        q = first.questions[0]
        data = QuizCB(mode="practice", lesson_id=first.id, q_idx=0, opt=q.correct_index)
        await lesson_handlers.answer(callback(bot, inaccessible()), data, s, user)
        assert await s.scalar(select(func.count(QuizAttempt.id))) == 1
    assert any("To'g'ri" in text for _, text in bot.sent)

