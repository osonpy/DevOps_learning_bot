"""Streak mantiqi — sof funksiyalar (DB'siz), shuning uchun oson test qilinadi.

Qoidalar:
- Har bir "majburiy kun" (rest_weekday'dan boshqa kunlar) da 1 ta dars bajarilishi kerak.
- Dam olish kuni (default: Yakshanba) o'tkazilsa streak buzilmaydi, bajarilsa +1.
- Kuniga faqat 1 marta streak oshadi (bir kunda 3 dars qilsangiz ham +1).
"""
from dataclasses import dataclass
from datetime import date, timedelta


def missed_days_between(last_done: date, today: date, rest_weekday: int) -> int:
    """last_done va today ORASIDAGI (ikkalasi ham kirmaydi) majburiy kunlar soni.

    Ya'ni "kechagacha nechta majburiy kun o'tkazib yuborildi".
    """
    missed = 0
    d = last_done + timedelta(days=1)
    while d < today:
        if d.weekday() != rest_weekday:
            missed += 1
        d += timedelta(days=1)
    return missed


def reference_date(last_done: date | None, started_on: date) -> date:
    """Hisob boshlanadigan sana: oxirgi bajarilgan kun yoki boshlanishdan bir kun oldin."""
    return last_done or (started_on - timedelta(days=1))


@dataclass(frozen=True)
class StreakUpdate:
    streak: int
    best_streak: int
    counted: bool  # bugun streak oshdimi (False = bugun allaqachon hisoblangan)


def apply_completion(
    streak: int, best_streak: int, last_done: date | None, started_on: date,
    today: date, rest_weekday: int,
) -> StreakUpdate:
    if last_done == today:
        return StreakUpdate(streak, best_streak, counted=False)
    missed = missed_days_between(reference_date(last_done, started_on), today, rest_weekday)
    new_streak = streak + 1 if (missed == 0 and streak > 0) else 1
    return StreakUpdate(new_streak, max(best_streak, new_streak), counted=True)


def penalty_kind(missed: int, penalty_threshold: int, hardcore_threshold: int) -> str | None:
    if missed >= hardcore_threshold:
        return "hardcore"
    if missed >= penalty_threshold:
        return "quiz"
    return None


def streak_xp_bonus(streak: int) -> int:
    """Har 7 kunlik streak uchun bonus."""
    return 20 if streak > 0 and streak % 7 == 0 else 0
