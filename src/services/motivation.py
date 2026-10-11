import random

MORNING = [
    "☀️ Xayrli tong, {name}! Bugungi missiya tayyor. 60 daqiqa — va siz kechagidan kuchliroqsiz.",
    "🚀 {name}, server uyg'ondi — siz ham! Bugungi dars kutyapti.",
    "⚡️ Streak: {streak}. Uni uzmaslik — eng oson g'alaba. Boshladik!",
]

MISSED_ONE = [
    "😶 Kecha dars bo'lmadi, {name}. Hech gap yo'q — production ham ba'zan yiqiladi. Muhimi — tez recovery! 💪",
    "🔁 1 kun o'tkazildi. Senior'lar ham xato qiladi, lekin postmortem yozib, davom etadi. Bugun qaytamiz!",
    "🧯 Streak 0 ga tushdi, lekin bilim saqlanib qoldi. Bugungi 60 daqiqa — yangi streak'ning 1-kuni.",
]

MISSED_TWO = [
    "⚠️ {missed} kun ketma-ket o'tkazildi. Yana 1 kun — va jarima tizimi ishga tushadi. Bugun albatta!",
    "🚨 Alert: learning_uptime < 70%. {missed} kun downtime. Bugun incident'ni yopamiz!",
]

PENALTY_QUIZ = (
    "⛓ <b>Jarima rejimi yoqildi</b> ({missed} kun o'tkazildi)\n"
    "Bugungi darsni yopish uchun avval shu mavzu bo'yicha mini-testdan to'liq o'tasiz."
)

PENALTY_HARDCORE = (
    "☠️ <b>HARDCORE jarima</b> ({missed} kun o'tkazildi)\n"
    "Dars + qo'shimcha hardcore vazifa. Isbot (GitHub link / natija) yubormaguningizcha dars yopilmaydi."
)

NUDGE = [
    "🌙 {name}, bugungi dars hali ochiq. Uxlashdan oldin 60 daqiqa topiladimi? Streak: {streak} 🔥",
    "⏰ Kun tugashiga oz qoldi. Hatto 30 daqiqa ham — 0 daqiqadan yaxshi.",
]

DONE = [
    "✅ Zo'r! +{xp} XP. Streak: {streak} 🔥",
    "🎯 Mission complete! +{xp} XP. Ertaga yangi level kutadi.",
    "🏁 Bajarildi! +{xp} XP. Siz to'xtamayapsiz — bu eng muhim skill.",
]


def pick(pool: list[str], **kw) -> str:
    return random.choice(pool).format(**kw)
