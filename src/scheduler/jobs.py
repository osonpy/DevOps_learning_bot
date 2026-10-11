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
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config import settings
from src.db import repo
from src.db.models import User
from src.handlers.common import build_today
from src.services import motivation
from src.services.clock import local_now

log = logging.getLogger(__name__)


# Bu xatolar "chat endi yo'q" degani — user'ni o'chiramiz
_GONE = ("chat not found", "bot was blocked", "user is deactivated")


async def _send(bot: Bot, user: User, text: str, kb=None) -> bool:
    """Yuboradi. False — tarmoq xatosi: chaqiruvchi o'zgarishlarni rollback qilsin (keyingi tick qayta urinadi)."""
    try:
        try:
            await bot.send_message(user.tg_id, text, reply_markup=kb)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            await bot.send_message(user.tg_id, text, reply_markup=kb)
    except TelegramForbiddenError:
        log.info("user %s botni bloklagan — o'chiramiz", user.tg_id)
        user.is_active = False
    except TelegramBadRequest as e:
        if any(s in e.message.lower() for s in _GONE):
            log.info("user %s: %s — o'chiramiz", user.tg_id, e.message)
            user.is_active = False
        else:  # qayta yuborish yordam bermaydi (masalan, matn juda uzun) — har daqiqa spam qilmaymiz
            log.error("user %s: xabar yuborilmadi: %s", user.tg_id, e.message)
    except TelegramNetworkError as e:
        log.warning("user %s: tarmoq xatosi, keyingi tick'da qayta: %s", user.tg_id, e.message)
        return False
    return True


async def _process_user(bot: Bot, session: AsyncSession, user: User, now_utc: datetime) -> None:
    local = local_now(user.timezone, now_utc)
    today, hm = local.date(), local.time().replace(second=0, microsecond=0)
    delivered = True

    # 1) Ertalabki eslatma + kunlik tekshiruv (streak/motivatsiya/jarima)
    if user.last_check_date != today and hm >= user.reminder_time:
        text, kb = await build_today(session, user, today=today, scheduled=True)
        delivered = await _send(bot, user, text, kb)

    # 2) Kechki "nudge" — bugun hali bajarilmagan bo'lsa (dam olish kuni emas)
    elif (hm >= user.nudge_time and user.last_nudge_date != today
          and user.last_done_date != today and today.weekday() != settings.rest_weekday):
        user.last_nudge_date = today
        delivered = await _send(bot, user, motivation.pick(
            motivation.NUDGE, name=user.full_name.split(" ")[0], streak=user.streak))

    if delivered:
        await session.commit()
    else:
        await session.rollback()


async def tick(bot: Bot, session_factory: async_sessionmaker, now_utc: datetime | None = None) -> None:
    """Har user o'z session'ida: bittasidagi xato faqat o'shani rollback qiladi."""
    now_utc = now_utc or datetime.now(timezone.utc)
    async with session_factory() as session:
        user_ids = await repo.active_user_ids(session)
    for user_id in user_ids:
        async with session_factory() as session:
            try:
                user = await session.get(User, user_id)
                if user is not None and user.is_active:
                    await _process_user(bot, session, user, now_utc)
            except Exception:
                log.exception("tick xatosi user_id=%s", user_id)
                await session.rollback()


def setup_scheduler(bot: Bot, session_factory: async_sessionmaker) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        tick, CronTrigger(second=0), args=[bot, session_factory],
        id="tick", max_instances=1, coalesce=True, misfire_grace_time=30,
    )
    return scheduler
