from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db import repo
from src.keyboards.menus import main_menu
from src.services.clock import local_today

router = Router(name="start")

WELCOME = (
    "👋 Salom, <b>{name}</b>! Men — <b>DevOps Quest</b> boti.\n\n"
    "🎯 Maqsad: 0 → Senior DevOps. Har kuni 1 soat: nazariya + amaliyot.\n"
    "🗓 Hafta: 6 kun dars + Yakshanba review (streak buzilmaydi).\n"
    "🔥 Har kuni ✅ bosing — streak o'sadi, XP to'planadi, level oshadi.\n"
    "⛓ {pen}+ kun ketma-ket o'tkazsangiz — jarima: mini-test yoki hardcore vazifa.\n\n"
    "⏰ Eslatma: har kuni <b>{rem}</b> ({tz}). O'zgartirish: /time 07:30\n\n"
    "Boshladik? 👇 <b>📚 Bugungi dars</b>"
)

HELP = (
    "<b>Buyruqlar</b>\n"
    "/today — bugungi dars\n/progress — statistika\n/roadmap — bosqichlar\n"
    "/time HH:MM — ertalabki eslatma vaqti\n/nudge HH:MM — kechki eslatma vaqti\n"
    "/tz Region/City — vaqt zonasi (masalan <code>Asia/Riyadh</code>)\n/help — yordam"
)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    u = message.from_user
    tz = settings.default_timezone
    user, _ = await repo.get_or_create_user(session, u.id, u.username, u.full_name, local_today(tz))
    await message.answer(
        WELCOME.format(name=u.first_name, pen=settings.penalty_threshold,
                       rem=user.reminder_time.strftime("%H:%M"), tz=user.timezone),
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP)
