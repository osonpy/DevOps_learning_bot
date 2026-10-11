import html
from itertools import groupby

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db import repo
from src.keyboards.menus import BTN_PROGRESS, BTN_ROADMAP
from src.services import progress as pg
from src.services.clock import local_today
from src.services.render import LEVEL

router = Router(name="progress")


@router.message(Command("progress"))
@router.message(F.text == BTN_PROGRESS)
async def show_progress(message: Message, session: AsyncSession):
    user = await repo.get_user(session, message.from_user.id)
    if not user:
        return await message.answer("Avval /start bosing 🙂")
    today = local_today(user.timezone)
    done_ids = await repo.completed_lesson_ids(session, user.id)
    junior_total = await repo.total_lessons(session, "junior")
    mon, sun = repo.week_bounds(today)
    week_done = await repo.done_dates_between(session, user.id, mon, sun)
    level, to_next = pg.level_for(user.xp)
    penalties = await repo.penalties_count(session, user.id)
    cards, mastered = await repo.card_stats(session, user.id)
    lesson = await repo.get_lesson_by_day(session, user.current_day)
    where = (f"{LEVEL.get(lesson.module.level)} · {lesson.module.stage} · {html.escape(lesson.module.title)} · "
             f"{lesson.week}-hafta") if lesson else "Barcha darslar tugagan"

    text = (
        f"📊 <b>Progress — {html.escape(user.full_name)}</b>\n"
        f"📍 {where}\n\n"
        f"🏅 Unvon: <b>{level}</b>\n"
        f"✨ XP: <b>{user.xp}</b>" + (f" (keyingi unvongacha {to_next})" if to_next else "") + "\n"
        f"🔥 Streak: {pg.streak_flames(user.streak)}   🏆 Rekord: {user.best_streak}\n"
        f"🔁 Kartalar: {cards} · o'zlashtirilgan: {mastered}\n"
        f"⛓ Jarimalar: {penalties}\n\n"
        f"📅 <b>Bu hafta</b>\n{pg.week_strip(today, week_done, settings.rest_weekday, user.started_on)}\n\n"
        f"🎓 <b>Junior yo'li</b> ({len(done_ids)}/{junior_total} dars)\n{pg.bar(len(done_ids), junior_total, 12)}"
    )
    await message.answer(text)


@router.message(Command("roadmap"))
@router.message(F.text == BTN_ROADMAP)
async def show_roadmap(message: Message, session: AsyncSession):
    user = await repo.get_user(session, message.from_user.id)
    if not user:
        return await message.answer("Avval /start bosing 🙂")
    done_ids = await repo.completed_lesson_ids(session, user.id)
    modules = await repo.modules_with_lessons(session)
    lines = ["🗺 <b>DevOps yo'li: Junior → Middle → Senior</b>"]
    for (level, stage), group in groupby(modules, key=lambda m: (m.level, m.stage)):
        group = list(group)
        lessons = [ls for m in group for ls in m.lessons if ls.is_active]
        d = sum(1 for ls in lessons if ls.id in done_ids)
        title = html.escape(group[0].stage_title)
        if not lessons:
            lines.append(f"\n🔒 <b>{LEVEL.get(level, level)} · {stage} {title}</b> — kontent keyinroq qo'shiladi")
            continue
        lines.append(f"\n<b>{LEVEL.get(level, level)} · {stage} {title}</b>  {pg.bar(d, len(lessons), 8)}")
        for m in group:
            ml = [ls for ls in m.lessons if ls.is_active]
            md = sum(1 for ls in ml if ls.id in done_ids)
            status = "✅" if ml and md == len(ml) else ("▶️" if md else "▫️")
            lines.append(f"{status} {m.emoji} {html.escape(m.title)} ({md}/{len(ml)})")
    lines.append(f"\n▶️ Keyingi dars: <b>#{user.current_day}</b>")
    await message.answer("\n".join(lines))
