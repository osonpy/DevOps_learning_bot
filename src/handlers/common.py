from datetime import date

from aiogram import Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db import repo
from src.db.models import User
from src.keyboards.menus import lesson_kb, review_start_kb
from src.services import learning, render, srs
from src.services.clock import local_today


class ChatReply:
    """cb.message o'rnini bosadi: xabar eskirgan (InaccessibleMessage) yoki inline (None) bo'lsa — user'ga yangi xabar."""

    def __init__(self, bot: Bot, chat_id: int):
        self.bot, self.chat_id = bot, chat_id

    async def answer(self, text: str, **kw):
        return await self.bot.send_message(self.chat_id, text, **kw)


def reply_target(cb: CallbackQuery) -> Message | ChatReply:
    return cb.message if isinstance(cb.message, Message) else ChatReply(cb.bot, cb.from_user.id)


async def drop_keyboard(cb: CallbackQuery) -> None:
    if isinstance(cb.message, Message):
        await cb.message.edit_reply_markup(reply_markup=None)


async def reviews_left(session: AsyncSession, user: User, today: date) -> int:
    """Bugun yana nechta karta so'rash mumkin (kunlik limit hisobga olinadi)."""
    limit = srs.daily_limit(today, settings.rest_weekday) - await repo.reviewed_today(session, user.id, today)
    if limit <= 0:
        return 0
    return min(limit, await repo.due_count(session, user.id, today))


async def build_today(session: AsyncSession, user: User, header: str | None = None,
                      today: date | None = None,
                      scheduled: bool = False) -> tuple[str, InlineKeyboardMarkup | None]:
    """Bugungi xabar: ish kuni — dars kartasi; Yakshanba ertalab — takrorlash kuni.

    scheduled=True — scheduler yuborayotgan ertalabki xabar. Foydalanuvchi o'zi
    "Bugungi dars"ni bossa, Yakshanba bo'lsa ham darsni oladi (xohlasa).
    """
    today = today or local_today(user.timezone)
    if user.last_check_date != today:
        check = await learning.run_daily_check(session, user, today)
        header = header or check.header

    due = await reviews_left(session, user, today)
    penalty = await repo.active_penalty(session, user.id)

    # Yakshanba: dars yo'q, faqat takrorlash (jarima bo'lsa — dars kartasi ko'rsatiladi)
    if scheduled and today.weekday() == settings.rest_weekday and penalty is None:
        if due:
            text = (f"🧘 <b>Yakshanba — takrorlash kuni</b>\n\nBugun yangi dars yo'q. "
                    f"{due} ta karta sizni kutyapti (~{max(1, due // 2)} daqiqa). Streak buzilmaydi.")
            return (f"{header}\n\n{text}" if header else text), review_start_kb(due)
        text = "🧘 <b>Yakshanba — dam olish kuni.</b> Takrorlash uchun karta yo'q. Ertaga yangi dars!"
        return (f"{header}\n\n{text}" if header else text), None

    lesson = await repo.get_lesson_by_day(session, user.current_day)
    if lesson is None:
        return ("🏆 Hozircha barcha darslarni tugatdingiz! Keyingi daraja kontenti qo'shilishini kuting.",
                review_start_kb(due) if due else None)

    hardcore = None
    if penalty and penalty.hardcore_task_id:
        hardcore = await repo.get_hardcore(session, penalty.hardcore_task_id)

    text = render.lesson_card(lesson, penalty, hardcore)
    if due:
        text += f"\n\n🔁 <b>Takrorlash:</b> bugun {due} ta karta (~{max(1, due // 2)} daq)."
    if user.last_done_date == today:
        text = "✅ <i>Bugungi streak allaqachon hisoblangan. Xohlasangiz keyingi darsni ham qiling!</i>\n\n" + text
    if header:
        text = f"{header}\n\n{text}"
    return text, lesson_kb(lesson, penalty, due)
