"""APScheduler: har daqiqada 1 ta `tick`.

Nega har bir user uchun alohida cron emas?
- user vaqtini o'zgartirsa job'ni qayta yaratish shart emas;
- bot o'chib-yonsa ham `last_check_date` tufayli o'tkazilgan eslatma "catch-up" bo'ladi;
- 10 000 tagacha user uchun bitta SELECT/daqiqa — bemalol.
"""
import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.config import settings
from src.db import repo
from src.db.models import User
from src.handlers.common import build_today
from src.services import motivation
from src.services.clock import local_now

log = logging.getLogger(__name__)


async def _send(bot: Bot, user: User, text: str, kb=None) -> None:
    try:
        await bot.send_message(user.tg_id, text, reply_markup=kb, disable_web_page_preview=True)
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        await bot.send_message(user.tg_id, text, reply_markup=kb, disable_web_page_preview=True)
    except TelegramForbiddenError:
        log.info("user %s botni bloklagan — o'chiramiz", user.tg_id)
        user.is_active = False


async def tick(bot: Bot, session_factory: async_sessionmaker, now_utc: datetime | None = None) -> None:
    now_utc = now_utc or datetime.now(timezone.utc)
    async with session_factory() as session:
        for user in await repo.active_users(session):
            try:
                local = local_now(user.timezone, now_utc)
                today, hm = local.date(), local.time().replace(second=0, microsecond=0)

                # 1) Ertalabki eslatma + kunlik tekshiruv (streak/motivatsiya/jarima)
                if user.last_check_date != today and hm >= user.reminder_time:
                    text, kb = await build_today(session, user, today=today, scheduled=True)
                    await _send(bot, user, text, kb)

                # 2) Kechki "nudge" — bugun hali bajarilmagan bo'lsa (dam olish kuni emas)
                elif (hm >= user.nudge_time and user.last_nudge_date != today
                      and user.last_done_date != today and today.weekday() != settings.rest_weekday):
                    user.last_nudge_date = today
                    await _send(bot, user, motivation.pick(
                        motivation.NUDGE, name=user.full_name.split(" ")[0], streak=user.streak))
                await session.commit()
            except Exception:
                log.exception("tick xatosi user=%s", user.tg_id)
                await session.rollback()


def setup_scheduler(bot: Bot, session_factory: async_sessionmaker) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        tick, CronTrigger(second=0), args=[bot, session_factory],
        id="tick", max_instances=1, coalesce=True, misfire_grace_time=30,
    )
    return scheduler
