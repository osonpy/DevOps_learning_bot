"""content/ -> DB (idempotent upsert).

Struktura:
  content/modules.yaml          — barcha modullar tartib bilan (level, stage, file)
  content/junior/NN-<slug>.yaml — modul darslari ro'yxati

Darslar `key` bo'yicha upsert qilinadi; `day_number` va `week` tartibdan avtomatik.
Savollar va hardcore vazifalar joyida yangilanadi (id saqlanadi) — shuning uchun
takrorlash kartalari va faol jarimalar qayta seed'da yo'qolmaydi.

Ishga tushirish:  python -m src.scripts.seed [content_dir]
"""
import asyncio
import sys
from pathlib import Path

import yaml
from sqlalchemy import select, update
from sqlalchemy import text as sql
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models import HardcoreTask, Lesson, Module, QuizQuestion

CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"
LESSONS_PER_WEEK = 6
DEFAULT_XP = {"lesson": 10, "lab": 12, "project": 20}
SEED_LOCK_KEY = 0x5EED_D0C5  # pg_advisory_xact_lock kaliti (bir vaqtda faqat bitta seed)


def load_content(root: Path) -> tuple[list[dict], list[tuple[str, dict]]]:
    modules = yaml.safe_load((root / "modules.yaml").read_text(encoding="utf-8"))["modules"]
    lessons: list[tuple[str, dict]] = []
    for m in modules:
        if m.get("file"):
            items = yaml.safe_load((root / m["file"]).read_text(encoding="utf-8"))["lessons"]
            lessons += [(m["slug"], item) for item in items]
    return modules, lessons


def validate(modules: list[dict], lessons: list[tuple[str, dict]]) -> None:
    slugs = [m["slug"] for m in modules]
    assert len(slugs) == len(set(slugs)), "modul slug'lari takrorlanmasin"
    for m in modules:
        links = ([m["main_resource"]] if m.get("main_resource") else []) + m.get("practice", [])
        for r in links:
            assert r.get("title") and str(r.get("url", "")).startswith("https://"), f"{m['slug']}: manba {r}"
    keys = [item["key"] for _, item in lessons]
    dup = {k for k in keys if keys.count(k) > 1}
    assert not dup, f"takrorlangan key: {dup}"
    for _, item in lessons:
        for field in ("key", "title", "theory", "task"):
            assert item.get(field), f"{item.get('key')}: '{field}' bo'sh"
        assert item.get("kind", "lesson") in DEFAULT_XP, f"{item['key']}: noto'g'ri kind"
        for q in item.get("quiz", []):
            assert 2 <= len(q["options"]) <= 4, f"{item['key']}: 2-4 variant bo'lsin"
            assert 0 <= q["answer"] < len(q["options"]), f"{item['key']}: answer indeksi xato"


async def acquire_seed_lock(session: AsyncSession) -> None:
    """Parallel seed'lar day_number almashtirishda to'qnashmasin. Lock tranzaksiya oxirida o'zi bo'shaydi."""
    if session.bind.dialect.name == "postgresql":
        await session.execute(sql("SELECT pg_advisory_xact_lock(:key)"), {"key": SEED_LOCK_KEY})


async def seed(session: AsyncSession, modules: list[dict], lessons: list[tuple[str, dict]]) -> tuple[int, int]:
    validate(modules, lessons)
    await acquire_seed_lock(session)

    by_slug: dict[str, Module] = {}
    for order, m in enumerate(modules, start=1):
        obj = await session.scalar(select(Module).where(Module.slug == m["slug"]))
        if obj is None:
            obj = Module(slug=m["slug"])
            session.add(obj)
        obj.title, obj.emoji, obj.order = m["title"], m.get("emoji", "📦"), order
        obj.level, obj.stage, obj.stage_title = m["level"], m["stage"], m.get("stage_title", "")
        obj.main_resource, obj.practice = m.get("main_resource"), m.get("practice", [])
        by_slug[m["slug"]] = obj
    await session.flush()

    # 1-faza: day_number'larni vaqtincha manfiyga o'tkazamiz (unique to'qnashuv bo'lmasin)
    await session.execute(update(Lesson).values(day_number=-Lesson.id, is_active=False))

    for i, (slug, item) in enumerate(lessons):
        lesson = await session.scalar(
            select(Lesson).where(Lesson.key == item["key"])
            .options(selectinload(Lesson.questions), selectinload(Lesson.hardcore))
        )
        if lesson is None:
            lesson = Lesson(key=item["key"], questions=[], hardcore=[])
            session.add(lesson)
        kind = item.get("kind", "lesson")
        lesson.day_number, lesson.week, lesson.is_active = i + 1, i // LESSONS_PER_WEEK + 1, True
        lesson.module_id = by_slug[slug].id
        lesson.kind, lesson.title = kind, item["title"]
        lesson.theory, lesson.task = item["theory"], item["task"]
        lesson.done_criteria = item.get("done", "")
        lesson.resources = item.get("resources", [])
        lesson.duration_min = item.get("duration", 60)
        lesson.xp = item.get("xp", DEFAULT_XP[kind])

        quiz = item.get("quiz", [])
        qs = sorted(lesson.questions, key=lambda q: q.id or 0)
        for q, data in zip(qs, quiz, strict=False):
            q.question, q.options = data["q"], data["options"]
            q.correct_index, q.explanation = data["answer"], data.get("why", "")
        for data in quiz[len(qs):]:
            lesson.questions.append(QuizQuestion(question=data["q"], options=data["options"],
                                                 correct_index=data["answer"], explanation=data.get("why", "")))
        for q in qs[len(quiz):]:
            lesson.questions.remove(q)

        hard = item.get("hardcore", [])
        hs = sorted(lesson.hardcore, key=lambda h: h.id or 0)
        for h, text in zip(hs, hard, strict=False):
            h.text = text
        for text in hard[len(hs):]:
            lesson.hardcore.append(HardcoreTask(text=text))
        for h in hs[len(hard):]:
            lesson.hardcore.remove(h)
        await session.flush()

    await session.commit()
    return len(modules), len(lessons)


async def main(root: Path) -> None:
    from src.db.session import SessionFactory

    modules, lessons = load_content(root)
    async with SessionFactory() as session:
        m, n = await seed(session, modules, lessons)
    print(f"✅ seed: {m} modul, {n} dars")


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]) if len(sys.argv) > 1 else CONTENT_DIR))
