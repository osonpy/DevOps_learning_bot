from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import repo
from src.db.models import Lesson, User
from src.handlers.common import ChatReply, build_today, drop_keyboard, reply_target
from src.keyboards.callbacks import LessonCB, QuizCB
from src.keyboards.menus import BTN_TODAY, quiz_kb
from src.middlewares.user import require_user
from src.services import learning, render
from src.services.clock import local_today

router = require_user(Router(name="lesson"))


class ProofState(StatesGroup):
    waiting = State()


# ───────── bugungi dars ─────────
@router.message(Command("today"))
@router.message(F.text == BTN_TODAY)
async def today(message: Message, session: AsyncSession, user: User):
    text, kb = await build_today(session, user)
    await message.answer(text, reply_markup=kb)


@router.callback_query(LessonCB.filter(F.action == "res"))
async def resources(cb: CallbackQuery, callback_data: LessonCB, session: AsyncSession):
    lesson = await repo.get_lesson(session, callback_data.lesson_id)
    await reply_target(cb).answer(render.resources_text(lesson))
    await cb.answer()


# ───────── "Bajardim" ─────────
@router.callback_query(LessonCB.filter(F.action == "done"))
async def done(cb: CallbackQuery, callback_data: LessonCB, session: AsyncSession, user: User):
    lesson = await repo.get_lesson(session, callback_data.lesson_id)
    penalty = await repo.active_penalty(session, user.id)

    if penalty and penalty.kind == "quiz":
        await cb.answer("Avval jarima testi ⛓")
        return await _send_question(reply_target(cb), lesson, "penalty", penalty.quiz_progress)
    if penalty and penalty.kind == "hardcore":
        return await cb.answer("Avval hardcore isbotini yuboring ☠️", show_alert=True)

    await _finish(reply_target(cb), session, user, lesson, with_penalty=False)
    await cb.answer()


async def _finish(msg: Message | ChatReply, session: AsyncSession, user: User, lesson: Lesson, with_penalty: bool):
    res = await learning.complete_lesson(session, user, lesson, local_today(user.timezone), with_penalty)
    await msg.answer(res.message)


# ───────── quiz (practice + penalty) ─────────
async def _send_question(msg: Message | ChatReply, lesson: Lesson, mode: str, idx: int):
    q = lesson.questions[idx]
    title = "Jarima testi" if mode == "penalty" else f"Mini-test #{lesson.day_number}"
    await msg.answer(render.question_text(q, idx, len(lesson.questions), title),
                     reply_markup=quiz_kb(mode, lesson.id, idx, len(q.options)))


@router.callback_query(LessonCB.filter(F.action == "quiz"))
async def start_practice(cb: CallbackQuery, callback_data: LessonCB, session: AsyncSession):
    lesson = await repo.get_lesson(session, callback_data.lesson_id)
    if not lesson.questions:
        return await cb.answer("Bu darsda test yo'q")
    await _send_question(reply_target(cb), lesson, "practice", 0)
    await cb.answer()


@router.callback_query(QuizCB.filter())
async def answer(cb: CallbackQuery, callback_data: QuizCB, session: AsyncSession, user: User):
    msg = reply_target(cb)
    lesson = await repo.get_lesson(session, callback_data.lesson_id)
    idx = callback_data.q_idx
    if idx >= len(lesson.questions):
        return await cb.answer()
    q = lesson.questions[idx]
    ok = callback_data.opt == q.correct_index
    mode = callback_data.mode

    rewarded_before = await repo.practice_already_rewarded(session, user.id, q.id)
    await repo.log_attempt(session, user.id, q.id, callback_data.opt, ok, mode)
    await drop_keyboard(cb)

    verdict = "✅ To'g'ri!" if ok else f"❌ Noto'g'ri. To'g'ri javob: <b>{chr(65 + q.correct_index)}</b>"
    if q.explanation:
        verdict += f"\n💡 {render.fmt(q.explanation)}"

    if mode == "practice":
        if ok and not rewarded_before:
            user.xp += 2
            verdict += "\n+2 XP"
        await msg.answer(verdict)
        if idx + 1 < len(lesson.questions):
            await _send_question(msg, lesson, mode, idx + 1)
        return await cb.answer()

    # ── penalty rejimi: hamma savolga to'g'ri javob berilmaguncha dars yopilmaydi
    penalty = await repo.active_penalty(session, user.id)
    if penalty is None or penalty.kind != "quiz":
        return await cb.answer("Faol jarima yo'q")
    if not ok:
        await msg.answer(verdict + "\n🔁 Qaytadan urinib ko'ring:")
        await _send_question(msg, lesson, mode, idx)
        return await cb.answer()

    penalty.quiz_progress = idx + 1
    await msg.answer(verdict)
    if penalty.quiz_progress < len(lesson.questions):
        await _send_question(msg, lesson, mode, penalty.quiz_progress)
    else:
        await learning.resolve_penalty(penalty)
        await msg.answer("🔓 Jarima yopildi! Endi dars hisoblanadi (+5 XP bonus).")
        await _finish(msg, session, user, lesson, with_penalty=True)
    await cb.answer()


# ───────── hardcore isbot ─────────
@router.callback_query(LessonCB.filter(F.action == "proof"))
async def ask_proof(cb: CallbackQuery, callback_data: LessonCB, state: FSMContext):
    await state.set_state(ProofState.waiting)
    await state.update_data(lesson_id=callback_data.lesson_id)
    await reply_target(cb).answer(
        "☠️ Isbotni yuboring: GitHub commit/PR link, yoki buyruq natijasi (kamida 20 belgi).\n"
        "Bekor qilish: /cancel"
    )
    await cb.answer()


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.")


@router.message(ProofState.waiting, F.text)
async def receive_proof(message: Message, state: FSMContext, session: AsyncSession, user: User):
    if len(message.text.strip()) < 20:
        return await message.answer("Juda qisqa 🙂 Batafsilroq isbot yuboring (link yoki natija).")
    data = await state.get_data()
    lesson = await repo.get_lesson(session, data["lesson_id"])
    penalty = await repo.active_penalty(session, user.id)
    if penalty:
        await learning.resolve_penalty(penalty, proof=message.text.strip())
    await state.clear()
    await message.answer("💀→😎 Hardcore yopildi! Hurmat.")
    await _finish(message, session, user, lesson, with_penalty=True)
