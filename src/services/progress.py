"""Vizual progress: progress bar, haftalik emoji shkala, darajalar."""
from datetime import date, timedelta

WEEKDAYS = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]

LEVELS = [  # (min_xp, nom)
    (0, "🐣 Intern"),
    (100, "🐧 Linux Padawan"),
    (250, "🐚 Shell Ninja"),
    (450, "🐳 Container Captain"),
    (700, "⚙️ Pipeline Engineer"),
    (1000, "☸️ Kube Navigator"),
    (1400, "🏗 IaC Architect"),
    (1900, "☁️ Cloud Commander"),
    (2500, "📈 SRE Guardian"),
    (3200, "🧙 Senior DevOps"),
]


def bar(done: int, total: int, width: int = 10) -> str:
    if total <= 0:
        return "▱" * width + " 0%"
    ratio = min(done / total, 1)
    filled = round(width * ratio)
    return f"{'▰' * filled}{'▱' * (width - filled)} {round(ratio * 100)}%"


def level_for(xp: int) -> tuple[str, int | None]:
    """(joriy daraja, keyingi darajagacha qolgan XP | None)."""
    current, nxt = LEVELS[0][1], None
    for i, (min_xp, name) in enumerate(LEVELS):
        if xp >= min_xp:
            current = name
            nxt = LEVELS[i + 1][0] - xp if i + 1 < len(LEVELS) else None
    return current, nxt


def week_strip(today: date, done_dates: set[date], rest_weekday: int, started_on: date) -> str:
    """Joriy hafta: ✅ bajarilgan, ❌ o'tkazilgan, 😴 dam olish, 🔵 bugun, ⬜ kelajak."""
    monday = today - timedelta(days=today.weekday())
    cells, labels = [], []
    for i in range(7):
        d = monday + timedelta(days=i)
        if d in done_dates:
            c = "✅"
        elif d < started_on:
            c = "▫️"
        elif d == today:
            c = "🔵"
        elif d > today:
            c = "⬜"
        elif d.weekday() == rest_weekday:
            c = "😴"
        else:
            c = "❌"
        cells.append(c)
        labels.append(WEEKDAYS[i])
    return " ".join(cells) + "\n<code>" + "  ".join(labels) + "</code>"


def streak_flames(streak: int) -> str:
    if streak == 0:
        return "🧊 0"
    if streak < 7:
        return "🔥" * streak + f" {streak}"
    return f"🔥x{streak}" + (" 🏆" if streak >= 30 else "")
