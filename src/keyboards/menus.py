from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.db.models import Lesson, Penalty
from src.keyboards.callbacks import LessonCB, QuizCB, ReviewCB

BTN_TODAY = "📚 Bugungi dars"
BTN_PROGRESS = "📊 Progress"
BTN_ROADMAP = "🗺 Roadmap"
BTN_SETTINGS = "⚙️ Sozlamalar"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_TODAY), KeyboardButton(text=BTN_PROGRESS)],
            [KeyboardButton(text=BTN_ROADMAP), KeyboardButton(text=BTN_SETTINGS)],
        ],
        resize_keyboard=True,
    )


def review_start_kb(due: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=f"🔁 Takrorlashni boshlash ({due})", callback_data=ReviewCB(card_id=0, opt=-1))
    return kb.as_markup()


def lesson_kb(lesson: Lesson, penalty: Penalty | None, due: int = 0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if due:
        kb.button(text=f"🔁 Takrorlash ({due})", callback_data=ReviewCB(card_id=0, opt=-1))
    if penalty and penalty.kind == "hardcore":
        kb.button(text="☠️ Hardcore isbotini yuborish", callback_data=LessonCB(action="proof", lesson_id=lesson.id))
    elif penalty and penalty.kind == "quiz":
        kb.button(text="⛓ Jarima testini boshlash", callback_data=LessonCB(action="done", lesson_id=lesson.id))
    else:
        kb.button(text="✅ Bajardim", callback_data=LessonCB(action="done", lesson_id=lesson.id))
    if lesson.questions and not penalty:
        kb.button(text="🧠 Mini-test (+XP)", callback_data=LessonCB(action="quiz", lesson_id=lesson.id))
    if lesson.theory_full:
        kb.button(text="📖 Batafsil nazariya", callback_data=LessonCB(action="theory", lesson_id=lesson.id))
    kb.button(text="📎 Manbalar", callback_data=LessonCB(action="res", lesson_id=lesson.id))
    kb.adjust(1)
    return kb.as_markup()


def quiz_kb(mode: str, lesson_id: int, q_idx: int, n_options: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for i in range(n_options):
        kb.button(text=chr(65 + i), callback_data=QuizCB(mode=mode, lesson_id=lesson_id, q_idx=q_idx, opt=i))
    kb.adjust(n_options)
    return kb.as_markup()


def review_kb(card_id: int, n_options: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for i in range(n_options):
        kb.button(text=chr(65 + i), callback_data=ReviewCB(card_id=card_id, opt=i))
    kb.adjust(n_options)
    return kb.as_markup()
