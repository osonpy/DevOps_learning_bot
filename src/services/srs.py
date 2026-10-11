"""Spaced repetition (Leitner tizimi) — sof funksiyalar.

To'g'ri javob -> karta keyingi qutiga o'tadi va keyinroq qaytadi.
Xato javob -> karta 0-qutiga qaytadi va ertaga yana so'raladi.
5 marta ketma-ket to'g'ri (1+3+7+21+60 kun) -> o'zlashtirilgan, boshqa so'ralmaydi.
"""
from dataclasses import dataclass
from datetime import date, timedelta

INTERVALS = [1, 3, 7, 21, 60]  # kun
MASTERED = len(INTERVALS)

# Barqaror holatda: haftasiga ~12 yangi karta x 5 takrorlash ~= kuniga 8-9 karta.
# Limit undan kichik bo'lsa navbat to'planib qoladi.
WEEKDAY_LIMIT = 8    # ish kunlari: ~4-5 daqiqa
REST_DAY_LIMIT = 25  # Yakshanba — takrorlash kuni (~12-15 daqiqa)


@dataclass(frozen=True)
class CardState:
    box: int
    due_date: date | None
    lapses: int


def first_due(today: date) -> date:
    """Yangi o'tilgan dars savollari ertaga birinchi marta qaytadi."""
    return today + timedelta(days=INTERVALS[0])


def answer(box: int, lapses: int, ok: bool, today: date) -> CardState:
    if not ok:
        return CardState(box=0, due_date=today + timedelta(days=INTERVALS[0]), lapses=lapses + 1)
    nxt = box + 1
    if nxt >= MASTERED:
        return CardState(box=MASTERED, due_date=None, lapses=lapses)
    return CardState(box=nxt, due_date=today + timedelta(days=INTERVALS[nxt]), lapses=lapses)


def daily_limit(today: date, rest_weekday: int) -> int:
    return REST_DAY_LIMIT if today.weekday() == rest_weekday else WEEKDAY_LIMIT
