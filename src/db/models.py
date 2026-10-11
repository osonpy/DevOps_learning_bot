"""Ma'lumotlar bazasi sxemasi.

modules (level, stage) ──< lessons ──< quiz_questions ──< review_cards >── users
                                  └──< hardcore_tasks
users ──< completions >── lessons
users ──< penalties   >── lessons
users ──< quiz_attempts
"""
from datetime import date, datetime, time

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, TimestampMixin


# ─────────────────────────── KONTENT ───────────────────────────
class Module(Base):
    """Modul: Linux asoslari, Bash, Tarmoq ... Har modul daraja (level) va bosqichga (stage) tegishli."""
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    title: Mapped[str] = mapped_column(String(120))
    emoji: Mapped[str] = mapped_column(String(8), default="📦")
    order: Mapped[int] = mapped_column(Integer)
    level: Mapped[str] = mapped_column(String(16), default="junior")  # junior | middle | senior
    stage: Mapped[str] = mapped_column(String(8), default="J1")       # J1..J4, M1.., S1..
    stage_title: Mapped[str] = mapped_column(String(120), default="")
    # "Manbalar" tugmasi: modulni to'liq o'rganish uchun asosiy manba va amaliyot platformalari
    main_resource: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))  # {"title":..,"url":..}; None -> SQL NULL
    practice: Mapped[list] = mapped_column(JSON, default=list, server_default=text("'[]'"))  # [{"title":..,"url":..}]

    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="module", order_by="Lesson.day_number"
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True)  # barqaror ID: "linux-01-fhs"
    day_number: Mapped[int] = mapped_column(Integer, unique=True, index=True)  # seed ketma-ket beradi
    week: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16), default="lesson")  # lesson | lab | project
    title: Mapped[str] = mapped_column(String(200))
    theory: Mapped[str] = mapped_column(Text)
    task: Mapped[str] = mapped_column(Text)
    done_criteria: Mapped[str] = mapped_column(Text, default="")
    resources: Mapped[list] = mapped_column(JSON, default=list)  # [{"title":..,"url":..}]
    duration_min: Mapped[int] = mapped_column(Integer, default=60)
    xp: Mapped[int] = mapped_column(Integer, default=10)

    module: Mapped[Module] = relationship(back_populates="lessons")
    questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", order_by="QuizQuestion.id"
    )
    hardcore: Mapped[list["HardcoreTask"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON)  # ["a", "b", "c", "d"]
    correct_index: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(Text, default="")

    lesson: Mapped[Lesson] = relationship(back_populates="questions")


class HardcoreTask(Base):
    __tablename__ = "hardcore_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)

    lesson: Mapped[Lesson] = relationship(back_populates="hardcore")


# ─────────────────────────── FOYDALANUVCHI ───────────────────────────
class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    full_name: Mapped[str] = mapped_column(String(200), default="")

    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tashkent")
    reminder_time: Mapped[time] = mapped_column(Time)
    nudge_time: Mapped[time] = mapped_column(Time)

    started_on: Mapped[date] = mapped_column(Date)
    # Joriy (navbatdagi) dars. Raqam emas, id: kontent tartibi o'zgarsa ham user o'sha darsda qoladi.
    # None — kurs tugagan; yangi dars qo'shilsa repo.current_lesson() uni topadi.
    current_lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"))

    streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    last_done_date: Mapped[date | None] = mapped_column(Date)

    # scheduler idempotentligi uchun ("bugun yuborildimi?")
    last_check_date: Mapped[date | None] = mapped_column(Date)
    last_nudge_date: Mapped[date | None] = mapped_column(Date)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    plan: Mapped[str] = mapped_column(String(16), default="free")  # kelajakda sotish uchun


class Completion(Base):
    """Bajarilgan dars (har bir dars bir marta)."""
    __tablename__ = "completions"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_completion_user_lesson"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    local_date: Mapped[date] = mapped_column(Date, index=True)  # foydalanuvchi vaqt zonasida
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    xp_earned: Mapped[int] = mapped_column(Integer, default=0)
    with_penalty: Mapped[bool] = mapped_column(Boolean, default=False)


class Penalty(TimestampMixin, Base):
    __tablename__ = "penalties"
    __table_args__ = (
        # Bir user'da bir vaqtda faqat bitta faol jarima (scheduler va user bir vaqtda bossa ham)
        Index("uq_penalties_user_active", "user_id", unique=True,
              postgresql_where=text("status = 'active'"), sqlite_where=text("status = 'active'")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))  # quiz | hardcore
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | resolved
    missed_days: Mapped[int] = mapped_column(Integer)
    hardcore_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("hardcore_tasks.id", ondelete="SET NULL"))
    quiz_progress: Mapped[int] = mapped_column(Integer, default=0)  # nechta savol to'g'ri
    proof: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class QuizAttempt(TimestampMixin, Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"))
    chosen_index: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    context: Mapped[str] = mapped_column(String(16), default="practice")  # practice | penalty | review


class ReviewCard(TimestampMixin, Base):
    """Spaced repetition (Leitner) kartasi: har bir savol × user.

    box 0..4 -> keyingi takrorlash 1, 3, 7, 21, 60 kundan keyin; box 5 = o'zlashtirilgan.
    """
    __tablename__ = "review_cards"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_review_user_question"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("quiz_questions.id", ondelete="CASCADE"))
    box: Mapped[int] = mapped_column(Integer, default=0)
    due_date: Mapped[date | None] = mapped_column(Date, index=True)  # None = o'zlashtirilgan
    reviews: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)  # necha marta xato qilingan
    last_reviewed: Mapped[date | None] = mapped_column(Date)

    question: Mapped[QuizQuestion] = relationship()
