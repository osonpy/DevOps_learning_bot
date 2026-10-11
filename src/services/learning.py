"""Asosiy biznes-logika (use-case'lar): kunlik tekshiruv, darsni yopish, jarima."""
import random
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db import repo
from src.db.models import Lesson, Penalty, User
from src.services import motivation, srs, streak


@dataclass
class DailyCheck:
    missed: int
    penalty: Penalty | None
    header: str


async def run_daily_check(session: AsyncSession, user: User, today: date) -> DailyCheck:
    """Har kuni ertalab (reminder vaqtida) 1 marta chaqiriladi."""
    ref = streak.reference_date(user.last_done_date, user.started_on)
    missed = streak.missed_days_between(ref, today, settings.rest_weekday)
    name = user.full_name.split(" ")[0] or "do'st"
    penalty = await repo.active_penalty(session, user.id)

    if missed >= 1:
        user.streak = 0

    kind = streak.penalty_kind(missed, settings.penalty_threshold, settings.hardcore_threshold)
    lesson = await repo.current_lesson(session, user)

    if kind and lesson:
        if penalty is None:
            penalty = await _create_penalty(session, user, lesson, kind, missed)
        elif penalty.kind == "quiz" and kind == "hardcore":
            # eskalatsiya: hali yopilmagan quiz jarimasi hardcore'ga ko'tariladi
            penalty.status = "resolved"
            penalty.resolved_at = datetime.now(timezone.utc)
            penalty = await _create_penalty(session, user, lesson, kind, missed)

    if penalty and penalty.kind == "hardcore":
        header = motivation.PENALTY_HARDCORE.format(missed=missed or penalty.missed_days)
    elif penalty:
        header = motivation.PENALTY_QUIZ.format(missed=missed or penalty.missed_days)
    elif missed >= 2:
        header = motivation.pick(motivation.MISSED_TWO, missed=missed)
    elif missed == 1:
        header = motivation.pick(motivation.MISSED_ONE, name=name)
    else:
        header = motivation.pick(motivation.MORNING, name=name, streak=user.streak)

    user.last_check_date = today
    return DailyCheck(missed=missed, penalty=penalty, header=header)


async def _create_penalty(session, user, lesson: Lesson, kind: str, missed: int) -> Penalty:
    hardcore_id = None
    if kind == "hardcore":
        if lesson.hardcore:
            hardcore_id = random.choice(lesson.hardcore).id
        else:
            kind = "quiz"  # hardcore vazifa yo'q bo'lsa quiz bilan cheklanamiz
    if kind == "quiz" and not lesson.questions:
        kind = "hardcore" if lesson.hardcore else "quiz"
    return await repo.create_penalty(session, user, lesson, kind, missed, hardcore_id)


@dataclass
class CompletionResult:
    ok: bool
    message: str
    xp: int = 0
    finished_course: bool = False


async def complete_lesson(session: AsyncSession, user: User, lesson: Lesson, today: date,
                          with_penalty: bool = False) -> CompletionResult:
    current = await repo.current_lesson(session, user)
    if current is None or lesson.id != current.id:
        return CompletionResult(False, "Bu dars hozirgi navbatdagi dars emas. 📚 Bugungi darsni oching.")
    if await repo.is_completed(session, user.id, lesson.id):
        return CompletionResult(False, "Bu dars allaqachon bajarilgan ✅")

    upd = streak.apply_completion(user.streak, user.best_streak, user.last_done_date,
                                  user.started_on, today, settings.rest_weekday)
    xp = lesson.xp + (5 if with_penalty else 0) + (streak.streak_xp_bonus(upd.streak) if upd.counted else 0)

    await repo.add_completion(session, user, lesson, today, xp, with_penalty)
    new_cards = await repo.schedule_cards(session, user.id, lesson, srs.first_due(today))
    user.streak, user.best_streak = upd.streak, upd.best_streak
    user.last_done_date = today
    user.xp += xp
    nxt = await repo.next_active_lesson(session, lesson.day_number)
    user.current_lesson_id = nxt.id if nxt else None

    finished = nxt is None
    msg = motivation.pick(motivation.DONE, xp=xp, streak=user.streak)
    if streak.streak_xp_bonus(upd.streak) and upd.counted:
        msg += f"\n🎁 {upd.streak} kunlik streak bonusi: +20 XP!"
    if not upd.counted:
        msg += "\n(Bugun streak allaqachon hisoblangan — lekin XP sizniki 😉)"
    if new_cards:
        msg += f"\n🔁 {new_cards} ta savol takrorlash kartasiga qo'shildi — ertadan qaytadi."
    if finished:
        msg += "\n\n🏆 <b>Barcha darslar tugadi!</b> Keyingi bosqich kontentini qo'shish vaqti."
    return CompletionResult(True, msg, xp, finished)


@dataclass
class ReviewResult:
    ok: bool
    mastered: bool
    next_due: date | None


async def answer_card(session: AsyncSession, user: User, card, chosen: int, today: date) -> ReviewResult:
    ok = chosen == card.question.correct_index
    st = srs.answer(card.box, card.lapses, ok, today)
    card.box, card.due_date, card.lapses = st.box, st.due_date, st.lapses
    card.reviews += 1
    card.last_reviewed = today
    await repo.log_attempt(session, user.id, card.question_id, chosen, ok, "review")
    if ok:
        user.xp += 1
    return ReviewResult(ok=ok, mastered=st.due_date is None, next_due=st.due_date)


async def resolve_penalty(penalty: Penalty, proof: str | None = None) -> None:
    penalty.status = "resolved"
    penalty.proof = proof
    penalty.resolved_at = datetime.now(timezone.utc)
