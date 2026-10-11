from aiogram.filters.callback_data import CallbackData


class LessonCB(CallbackData, prefix="ls"):
    action: str  # done | quiz | res | proof
    lesson_id: int


class QuizCB(CallbackData, prefix="qz"):
    mode: str     # practice | penalty
    lesson_id: int
    q_idx: int
    opt: int


class ReviewCB(CallbackData, prefix="rv"):
    card_id: int  # 0 = sessiyani boshlash
    opt: int      # -1 = boshlash
