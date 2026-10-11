"""Spaced repetition: kunlik takrorlash sessiyasi."""
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import repo
from src.db.models import User
from src.handlers.common import reviews_left
from src.keyboards.callbacks import ReviewCB
from src.keyboards.menus import review_kb
from src.services import learning, render
from src.services.clock import local_today

router = Router(name="review")


async def _next_card(msg: Message, session: AsyncSession, user: User, done_in_session: int = 0) -> None:
    today = local_today(user.timezone)
    left = await reviews_left(session, user, today)
    if left == 0:
        total, mastered = await repo.card_stats(session, user.id)
        text = "🎉 Bugungi takrorlash tugadi!" if done_in_session else "🔁 Bugun takrorlash uchun karta yo'q."
        await msg.answer(f"{text}\n📚 Kartalar: {total} · o'zlashtirilgan: {mastered}")
        return
    card = (await repo.due_cards(session, user.id, today, 1))[0]
    await msg.answer(render.review_text(card, done_in_session + 1, done_in_session + left),
                     reply_markup=review_kb(card.id, len(card.question.options)))


@router.message(Command("review"))
async def cmd_review(message: Message, session: AsyncSession):
    user = await repo.get_user(session, message.from_user.id)
    if not user:
        return await message.answer("Avval /start bosing 🙂")
    await _next_card(message, session, user)


@router.callback_query(ReviewCB.filter(F.card_id == 0))
async def start(cb: CallbackQuery, session: AsyncSession):
    user = await repo.get_user(session, cb.from_user.id)
    if not user:
        return await cb.answer("Avval /start bosing")
    await _next_card(cb.message, session, user)
    await cb.answer()


@router.callback_query(ReviewCB.filter(F.card_id > 0))
async def answer(cb: CallbackQuery, callback_data: ReviewCB, session: AsyncSession):
    user = await repo.get_user(session, cb.from_user.id)
    card = await repo.get_card(session, callback_data.card_id)
    if not user or not card or card.user_id != user.id:
        return await cb.answer()
    today = local_today(user.timezone)
    if card.last_reviewed == today:  # ikki marta bosilgan tugma
        return await cb.answer("Bu karta bugun javob berilgan")

    res = await learning.answer_card(session, user, card, callback_data.opt, today)
    await cb.message.edit_reply_markup(reply_markup=None)
    q = card.question
    if res.ok:
        verdict = "✅ To'g'ri! +1 XP" + (" · 🏅 O'zlashtirildi!" if res.mastered
                                         else f" · keyingisi: {res.next_due:%d.%m}")
    else:
        verdict = f"❌ To'g'ri javob: <b>{chr(65 + q.correct_index)}</b> · karta ertaga qaytadi"
    if q.explanation:
        verdict += f"\n💡 {render.fmt(q.explanation)}"
    await cb.message.answer(verdict)
    done = await repo.reviewed_today(session, user.id, today)
    await _next_card(cb.message, session, user, done_in_session=done)
    await cb.answer()
