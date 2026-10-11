"""Scheduler tick izolyatsiyasi: bitta user'dagi xato qolganlarga ta'sir qilmasin."""
import os
from datetime import date, datetime, timezone
from pathlib import Path

os.environ.setdefault("BOT_TOKEN", "1:test")

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.methods import SendMessage
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db import repo
from src.db.base import Base
from src.scheduler import jobs
from src.scripts.seed import load_content, seed

ROOT = Path(__file__).resolve().parents[1]
SUN = date(2026, 10, 11)
MON_0900_TASHKENT = datetime(2026, 10, 12, 4, 0, tzinfo=timezone.utc)


class FakeBot:
    """`fail` — chat_id -> tashlanadigan exception (har chaqiruvda)."""

    def __init__(self, fail: dict[int, Exception] | None = None):
        self.fail = fail or {}
        self.sent: list[int] = []
        self.kwargs: list[dict] = []

    async def send_message(self, chat_id, text, **kw):
        if chat_id in self.fail:
            raise self.fail[chat_id]
        self.sent.append(chat_id)
        self.kwargs.append(kw)


def bad_request(msg: str) -> TelegramBadRequest:
    return TelegramBadRequest(method=SendMessage(chat_id=0, text="x"), message=msg)


@pytest.fixture
async def sf(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        await seed(s, *load_content(ROOT / "content"))
        for tg_id in (1, 2, 3):
            await repo.get_or_create_user(s, tg_id, None, f"User{tg_id}", SUN)
        await s.commit()
    yield factory
    await engine.dispose()


@pytest.mark.parametrize("error", [
    bad_request("Bad Request: chat not found"),
    bad_request("Bad Request: message is too long"),
    RuntimeError("kutilmagan xato"),
])
async def test_middle_user_failure_does_not_block_others(sf, error):
    bot = FakeBot(fail={2: error})
    await jobs.tick(bot, sf, now_utc=MON_0900_TASHKENT)
    assert bot.sent == [1, 3]


async def test_chat_not_found_deactivates_user(sf):
    await jobs.tick(FakeBot(fail={2: bad_request("Bad Request: chat not found")}), sf, now_utc=MON_0900_TASHKENT)
    async with sf() as s:
        assert (await repo.get_user(s, 2)).is_active is False
        assert (await repo.get_user(s, 1)).is_active is True


async def test_blocked_bad_request_deactivates_user(sf):
    err = bad_request("Bad Request: bot was blocked by the user")
    await jobs.tick(FakeBot(fail={2: err}), sf, now_utc=MON_0900_TASHKENT)
    async with sf() as s:
        assert (await repo.get_user(s, 2)).is_active is False


async def test_network_error_retries_on_next_tick(sf):
    net = TelegramNetworkError(method=SendMessage(chat_id=0, text="x"), message="timeout")
    bot = FakeBot(fail={2: net})
    await jobs.tick(bot, sf, now_utc=MON_0900_TASHKENT)
    async with sf() as s:
        u2 = await repo.get_user(s, 2)
        assert u2.is_active is True
        assert u2.last_check_date == SUN  # yangilanmadi -> keyingi tick qayta urinadi
    bot.fail.clear()
    await jobs.tick(bot, sf, now_utc=MON_0900_TASHKENT.replace(minute=1))
    assert bot.sent == [1, 3, 2]
