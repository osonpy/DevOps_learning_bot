# 🚀 DevOps Quest Bot

0 → Junior → Middle → Senior DevOps yo'lini o'yinga aylantiruvchi Telegram bot: kunlik 1 soatlik dars (15 daq nazariya + 45 daq amaliyot), spaced repetition takrorlash, streak, XP, eslatmalar va jarima tizimi.

**Stack:** Python 3.12 · uv · Aiogram 3 · SQLAlchemy 2 (async) · PostgreSQL 16 · Alembic · APScheduler · Docker Compose

**Kontent:** Junior darajasi to'liq — 44 hafta, 264 dars, 21 modul, 4 bosqich (J1 Poydevor → J2 Konteyner va CI/CD → J3 IaC va Cloud → J4 Kubernetes va Monitoring). Middle va Senior modullari roadmap'da ko'rinadi, darslari keyinroq qo'shiladi.

## Tez start

```bash
cp .env.example .env          # BOT_TOKEN ni BotFather'dan qo'ying
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -base64 32)|" .env
docker compose up -d --build  # migratsiya + seed avtomatik
docker compose logs -f bot
```

Telegram'da botga `/start` yozing. Birinchi darsni Dushanba boshlang — Yakshanba takrorlash kuniga to'g'ri keladi.

## Lokal ishlab chiqish (Docker'siz)

Paketlar [uv](https://docs.astral.sh/uv/) bilan boshqariladi (`pyproject.toml` + `uv.lock`).

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # uv o'rnatilmagan bo'lsa
uv sync                                           # .venv + dev vositalar (Python 3.12 avtomatik)
export BOT_TOKEN=... DATABASE_URL=sqlite+aiosqlite:///dev.db
uv run alembic upgrade head
uv run python -m src.scripts.seed
uv run python -m src.main
uv run pytest -q && uv run ruff check .
```

Paket qo'shish: `uv add <paket>` (dev uchun `uv add --dev <paket>`), yangilash: `uv lock --upgrade`. `uv.lock` Git'ga commit qilinadi.

## Struktura

```
src/
├── main.py              # entrypoint: Bot, Dispatcher, routers, scheduler
├── config.py            # pydantic-settings (.env)
├── db/                  # base, models, session, repo (barcha SQL shu yerda)
├── services/
│   ├── streak.py        # streak va jarima qoidalari (sof funksiyalar)
│   ├── srs.py           # spaced repetition: 1, 3, 7, 21, 60 kun
│   ├── learning.py      # kunlik tekshiruv, darsni yopish, karta javobi
│   ├── progress.py      # progress bar, haftalik shkala, unvonlar
│   ├── render.py        # Telegram HTML kartalar
│   └── motivation.py    # xabar shablonlari
├── handlers/            # start, lesson, review (takrorlash), progress, settings
├── keyboards/           # callback factory'lar va menyular
├── middlewares/db.py    # update boshiga AsyncSession
├── scheduler/jobs.py    # APScheduler tick: ertalab dars / Yakshanba takrorlash, kechki nudge
└── scripts/seed.py      # content/ -> DB (key bo'yicha upsert)
content/
├── modules.yaml         # barcha modullar: level, stage, fayl
└── junior/NN-*.yaml     # har modul darslari
migrations/              # Alembic
tests/                   # streak/SRS unit + to'liq oqim integration testlari
```

## Kun qanday o'tadi

| Kun | Bot nima yuboradi |
|---|---|
| Du–Sh, ertalab | Bugungi dars kartasi + o'sha kunga to'plangan takrorlash kartalari (kuniga 8 tagacha, ~5 daq) |
| Du–Sh, kechqurun | Dars bajarilmagan bo'lsa — eslatma |
| Yakshanba | Yangi dars yo'q: takrorlash kuni (25 tagacha karta). Streak buzilmaydi |

## O'yin qoidalari

| Hodisa | Natija |
|---|---|
| Dars / lab / loyiha bajarildi | +10 / +12 / +20 XP, streak +1 (kuniga 1 marta) |
| Dars savollari | Takrorlash kartasiga aylanadi: 1, 3, 7, 21, 60 kundan keyin qaytadi; xato javob — kartani boshiga |
| Takrorlashda to'g'ri javob | +1 XP |
| Har 7 kunlik streak | +20 XP bonus |
| 1–2 kun o'tkazildi | Streak 0, motivatsion xabar |
| 3+ kun (`PENALTY_THRESHOLD`) | ⛓ Quiz jarima: dars testiga to'liq to'g'ri javob bermaguncha dars yopilmaydi |
| 5+ kun (`HARDCORE_THRESHOLD`) | ☠️ Hardcore vazifa: isbot (link/natija) yuborish shart |
| Jarima yopildi | +5 XP |

## Yangi kontent qo'shish

1. `content/<level>/NN-<modul>.yaml` yarating (`lessons:` ro'yxati; har darsda barqaror `key`).
2. `content/modules.yaml` da modulga `file:` qo'shing.
3. `uv run python -m src.scripts.seed` (yoki konteynerni qayta ishga tushiring).

Seed `key` bo'yicha upsert qiladi: savollar va hardcore vazifalar joyida yangilanadi, shuning uchun takrorlash kartalari va faol jarimalar saqlanadi. Dars raqamlari va haftalar tartibdan avtomatik hisoblanadi (har 6 dars = 1 hafta).

## Kelajakda sotish uchun tayyorlangan joylar

- `users.plan` maydoni (free/pro), `ADMIN_IDS`
- Har userning o'z vaqt zonasi va eslatma vaqtlari
- FSM storage → `RedisStorage` (ko'p instance uchun)
