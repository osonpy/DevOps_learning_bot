"""Repository: barcha SQL so'rovlar shu yerda — handler'lar toza qoladi."""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import settings
from src.db.models import (
    Completion,
    HardcoreTask,
    Lesson,
    Module,
    Penalty,
    QuizAttempt,
    QuizQuestion,
    ReviewCard,
    User,
)


# ───────── users ─────────
async def get_user(session: AsyncSession, tg_id: int) -> User | None:
    return await session.scalar(select(User).where(User.tg_id == tg_id))


async def get_or_create_user(
    session: AsyncSession, tg_id: int, username: str | None, full_name: str, today: date
) -> tuple[User, bool]:
    user = await get_user(session, tg_id)
    if user:
        user.username, user.full_name, user.is_active = username, full_name, True
        return user, False
    user = User(
        tg_id=tg_id,
        username=username,
        full_name=full_name,
        timezone=settings.default_timezone,
        reminder_time=settings.default_reminder_time,
        nudge_time=settings.default_nudge_time,
        started_on=today,
        last_check_date=today,  # ro'yxatdan o'tgan kuni "o'tkazib yubordi" deb hisoblamaymiz
        streak=0, best_streak=0, xp=0, current_day=1,
    )
    session.add(user)
    await session.flush()
    return user, True


async def active_user_ids(session: AsyncSession) -> list[int]:
    return list(await session.scalars(select(User.id).where(User.is_active.is_(True)).order_by(User.id)))


# ───────── lessons ─────────
async def get_lesson_by_day(session: AsyncSession, day: int) -> Lesson | None:
    return await session.scalar(
        select(Lesson)
        .where(Lesson.day_number == day, Lesson.is_active.is_(True))
        .options(selectinload(Lesson.module), selectinload(Lesson.questions),
                 selectinload(Lesson.hardcore))
    )


async def get_lesson(session: AsyncSession, lesson_id: int) -> Lesson | None:
    return await session.scalar(
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(selectinload(Lesson.module), selectinload(Lesson.questions),
                 selectinload(Lesson.hardcore))
    )


async def total_lessons(session: AsyncSession, level: str | None = None) -> int:
    q = select(func.count(Lesson.id)).where(Lesson.is_active.is_(True))
    if level:
        q = q.join(Module).where(Module.level == level)
    return await session.scalar(q) or 0


async def modules_with_lessons(session: AsyncSession) -> list[Module]:
    return list(await session.scalars(
        select(Module).order_by(Module.order).options(selectinload(Module.lessons))
    ))


async def get_question(session: AsyncSession, qid: int) -> QuizQuestion | None:
    return await session.get(QuizQuestion, qid)


async def get_hardcore(session: AsyncSession, hid: int) -> HardcoreTask | None:
    return await session.get(HardcoreTask, hid)


# ───────── completions ─────────
async def completed_lesson_ids(session: AsyncSession, user_id: int) -> set[int]:
    rows = await session.scalars(select(Completion.lesson_id).where(Completion.user_id == user_id))
    return set(rows)


async def done_dates_between(session: AsyncSession, user_id: int, start: date, end: date) -> set[date]:
    rows = await session.scalars(
        select(Completion.local_date).where(
            Completion.user_id == user_id,
            Completion.local_date >= start,
            Completion.local_date <= end,
        )
    )
    return set(rows)


async def is_completed(session: AsyncSession, user_id: int, lesson_id: int) -> bool:
    return bool(await session.scalar(
        select(Completion.id).where(Completion.user_id == user_id, Completion.lesson_id == lesson_id)
    ))


async def add_completion(
    session: AsyncSession, user: User, lesson: Lesson, local_date: date, xp: int, with_penalty: bool
) -> Completion:
    c = Completion(
        user_id=user.id, lesson_id=lesson.id, local_date=local_date,
        completed_at=datetime.now(timezone.utc), xp_earned=xp, with_penalty=with_penalty,
    )
    session.add(c)
    await session.flush()
    return c


# ───────── penalties ─────────
async def active_penalty(session: AsyncSession, user_id: int) -> Penalty | None:
    return await session.scalar(
        select(Penalty).where(Penalty.user_id == user_id, Penalty.status == "active")
        .order_by(Penalty.id.desc())
    )


async def get_penalty(session: AsyncSession, pid: int) -> Penalty | None:
    return await session.get(Penalty, pid)


async def create_penalty(
    session: AsyncSession, user: User, lesson: Lesson, kind: str, missed: int,
    hardcore_task_id: int | None,
) -> Penalty:
    p = Penalty(user_id=user.id, lesson_id=lesson.id, kind=kind, missed_days=missed,
                hardcore_task_id=hardcore_task_id)
    session.add(p)
    await session.flush()
    return p


async def penalties_count(session: AsyncSession, user_id: int) -> int:
    return await session.scalar(select(func.count(Penalty.id)).where(Penalty.user_id == user_id)) or 0


# ───────── quiz ─────────
async def log_attempt(session: AsyncSession, user_id: int, qid: int, chosen: int, ok: bool, ctx: str):
    session.add(QuizAttempt(user_id=user_id, question_id=qid, chosen_index=chosen,
                            is_correct=ok, context=ctx))


async def practice_already_rewarded(session: AsyncSession, user_id: int, qid: int) -> bool:
    return bool(await session.scalar(
        select(QuizAttempt.id).where(
            QuizAttempt.user_id == user_id, QuizAttempt.question_id == qid,
            QuizAttempt.is_correct.is_(True),
        )
    ))


# ───────── spaced repetition ─────────
async def schedule_cards(session: AsyncSession, user_id: int, lesson: Lesson, due: date) -> int:
    existing = set(await session.scalars(
        select(ReviewCard.question_id).where(
            ReviewCard.user_id == user_id,
            ReviewCard.question_id.in_([q.id for q in lesson.questions] or [-1]),
        )
    ))
    added = 0
    for q in lesson.questions:
        if q.id not in existing:
            session.add(ReviewCard(user_id=user_id, question_id=q.id, box=0, due_date=due))
            added += 1
    await session.flush()
    return added


async def due_cards(session: AsyncSession, user_id: int, today: date, limit: int) -> list[ReviewCard]:
    return list(await session.scalars(
        select(ReviewCard)
        .where(ReviewCard.user_id == user_id, ReviewCard.due_date.is_not(None),
               ReviewCard.due_date <= today)
        .order_by(ReviewCard.due_date, ReviewCard.box, ReviewCard.id)
        .limit(limit)
        .options(selectinload(ReviewCard.question).selectinload(QuizQuestion.lesson))
    ))


async def due_count(session: AsyncSession, user_id: int, today: date) -> int:
    return await session.scalar(
        select(func.count(ReviewCard.id)).where(
            ReviewCard.user_id == user_id, ReviewCard.due_date.is_not(None),
            ReviewCard.due_date <= today)
    ) or 0


async def reviewed_today(session: AsyncSession, user_id: int, today: date) -> int:
    return await session.scalar(
        select(func.count(ReviewCard.id)).where(
            ReviewCard.user_id == user_id, ReviewCard.last_reviewed == today)
    ) or 0


async def get_card(session: AsyncSession, card_id: int) -> ReviewCard | None:
    return await session.scalar(
        select(ReviewCard).where(ReviewCard.id == card_id)
        .options(selectinload(ReviewCard.question).selectinload(QuizQuestion.lesson))
    )


async def card_stats(session: AsyncSession, user_id: int) -> tuple[int, int]:
    """(jami kartalar, o'zlashtirilganlar)."""
    total = await session.scalar(
        select(func.count(ReviewCard.id)).where(ReviewCard.user_id == user_id)) or 0
    mastered = await session.scalar(
        select(func.count(ReviewCard.id)).where(
            ReviewCard.user_id == user_id, ReviewCard.due_date.is_(None))) or 0
    return total, mastered


def week_bounds(d: date) -> tuple[date, date]:
    start = d - timedelta(days=d.weekday())
    return start, start + timedelta(days=6)
