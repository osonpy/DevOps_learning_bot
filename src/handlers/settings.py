import re
from datetime import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import repo
from src.keyboards.menus import BTN_SETTINGS

router = Router(name="settings")
HM = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def _parse(arg: str | None) -> time | None:
    m = HM.match((arg or "").strip())
    return time(int(m[1]), int(m[2])) if m else None


@router.message(F.text == BTN_SETTINGS)
@router.message(Command("settings"))
async def show(message: Message, session: AsyncSession):
    user = await repo.get_user(session, message.from_user.id)
    if not user:
        return await message.answer("Avval /start bosing 🙂")
    await message.answer(
        "⚙️ <b>Sozlamalar</b>\n"
        f"⏰ Ertalabki eslatma: <b>{user.reminder_time:%H:%M}</b> — /time 07:30\n"
        f"🌙 Kechki eslatma: <b>{user.nudge_time:%H:%M}</b> — /nudge 21:30\n"
        f"🌍 Vaqt zonasi: <b>{user.timezone}</b> — /tz Asia/Riyadh"
    )


@router.message(Command("time"))
async def set_time(message: Message, command: CommandObject, session: AsyncSession):
    t = _parse(command.args)
    if not t:
        return await message.answer("Format: /time 07:30")
    user = await repo.get_user(session, message.from_user.id)
    user.reminder_time = t
    await message.answer(f"✅ Ertalabki eslatma: {t:%H:%M}")


@router.message(Command("nudge"))
async def set_nudge(message: Message, command: CommandObject, session: AsyncSession):
    t = _parse(command.args)
    if not t:
        return await message.answer("Format: /nudge 21:30")
    user = await repo.get_user(session, message.from_user.id)
    user.nudge_time = t
    await message.answer(f"✅ Kechki eslatma: {t:%H:%M}")


@router.message(Command("tz"))
async def set_tz(message: Message, command: CommandObject, session: AsyncSession):
    name = (command.args or "").strip()
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        return await message.answer("Noto'g'ri zona. Misol: /tz Asia/Tashkent yoki /tz Asia/Riyadh")
    user = await repo.get_user(session, message.from_user.id)
    user.timezone = name
    await message.answer(f"✅ Vaqt zonasi: {name}")
