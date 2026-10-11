"""Telegram HTML matnlarini yasash."""
import html
import re

from src.db.models import HardcoreTask, Lesson, Penalty, QuizQuestion, ReviewCard

_CODE = re.compile(r"`([^`]+)`")


def fmt(text: str) -> str:
    """HTML escape + `inline code` -> <code>."""
    return _CODE.sub(r"<code>\1</code>", html.escape(text.strip()))


KIND = {"lesson": "📘 DARS", "lab": "🔧 BREAK-FIX LAB", "project": "🏗 LOYIHA"}
LEVEL = {"junior": "🎓 Junior", "middle": "🛠 Middle", "senior": "🧙 Senior"}


def lesson_card(lesson: Lesson, penalty: Penalty | None = None,
                hardcore: HardcoreTask | None = None) -> str:
    kind = KIND.get(lesson.kind, "📘 DARS")
    m = lesson.module
    stage = f"{m.stage} {html.escape(m.stage_title)}".strip()
    parts = [
        f"<i>{LEVEL.get(m.level, m.level)} · {stage} · {lesson.week}-hafta</i>",
        f"{m.emoji} <b>{html.escape(m.title)}</b>",
        f"{kind} <b>#{lesson.day_number}: {html.escape(lesson.title)}</b>  ⏱ {lesson.duration_min} daq · +{lesson.xp} XP",
        "",
        "🧠 <b>Nazariya</b>",
        fmt(lesson.theory),
        "",
        "🛠 <b>Amaliy vazifa</b>",
        fmt(lesson.task),
    ]
    if lesson.done_criteria:
        parts += ["", "🎯 <b>Bajarildi deb hisoblanadi, agar:</b>", fmt(lesson.done_criteria)]
    if penalty and penalty.kind == "quiz":
        parts += ["", f"⛓ <b>Jarima:</b> darsni yopishdan oldin {len(lesson.questions)} ta savolga to'g'ri javob bering."]
    if penalty and penalty.kind == "hardcore" and hardcore:
        parts += ["", "☠️ <b>HARDCORE vazifa (jarima):</b>", fmt(hardcore.text),
                  "<i>Bajargach, isbot sifatida GitHub link yoki natijani yuborasiz.</i>"]
    return "\n".join(parts)


def resources_text(lesson: Lesson) -> str:
    if not lesson.resources:
        return "Bu dars uchun manba qo'shilmagan."
    lines = [f"📎 <b>Manbalar — #{lesson.day_number}</b>"]
    for r in lesson.resources:
        lines.append(f'• <a href="{html.escape(r["url"])}">{html.escape(r["title"])}</a>')
    return "\n".join(lines)


def review_text(card: ReviewCard, n: int, total: int) -> str:
    q = card.question
    opts = "\n".join(f"{chr(65 + i)}) {fmt(o)}" for i, o in enumerate(q.options))
    stars = "●" * card.box + "○" * (5 - card.box)
    return (f"🔁 <b>Takrorlash {n}/{total}</b>  <code>{stars}</code>\n"
            f"<i>#{q.lesson.day_number} {html.escape(q.lesson.title)}</i>\n\n{fmt(q.question)}\n\n{opts}")


def question_text(q: QuizQuestion, idx: int, total: int, title: str) -> str:
    opts = "\n".join(f"{chr(65 + i)}) {fmt(o)}" for i, o in enumerate(q.options))
    return f"🧩 <b>{html.escape(title)}</b> — savol {idx + 1}/{total}\n\n{fmt(q.question)}\n\n{opts}"
