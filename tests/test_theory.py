"""'Batafsil nazariya': Markdown -> Telegram HTML, ## bo'yicha bo'laklash, seed, tugma va handler."""
import os
import re
import shutil
from datetime import date
from pathlib import Path

os.environ.setdefault("BOT_TOKEN", "1:test")

import pytest
from aiogram.types import CallbackQuery
from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db import repo
from src.db.base import Base
from src.db.models import Lesson, Module
from src.handlers import lesson as lesson_handlers
from src.keyboards.callbacks import LessonCB
from src.keyboards.menus import lesson_kb
from src.scripts.seed import load_content, seed, validate
from src.services import render
from src.services.theory import CHUNK_LIMIT, md_to_html, theory_messages

ROOT = Path(__file__).resolve().parents[1]
TELEGRAM_LIMIT = 4096


def visible_len(html: str) -> int:
    """Telegram limiti teglar olib tashlangan matnga qo'llanadi; biz HTML uzunligini ham tekshiramiz."""
    return len(re.sub(r"<[^>]+>", "", html))


# ───────── Markdown -> HTML ─────────
def test_md_to_html_formats_and_escapes():
    md = "## Sarlavha\nOddiy **qalin** va `ls -l <dir>` & <script>\n\n- birinchi\n* ikkinchi\n1. raqamli\n"
    html = md_to_html(md)
    assert "<b>Sarlavha</b>" in html
    assert "<b>qalin</b>" in html
    assert "<code>ls -l &lt;dir&gt;</code>" in html
    assert "&amp; &lt;script&gt;" in html and "<script>" not in html
    assert "• birinchi" in html and "• ikkinchi" in html and "1. raqamli" in html


def test_bold_may_contain_inline_code():
    html = md_to_html("- **`rm -rf` ni tekshirmaslik.** Belgi: `**` emas")
    assert html == "• <b><code>rm -rf</code> ni tekshirmaslik.</b> Belgi: <code>**</code> emas"


def test_code_block_is_preformatted_and_not_inline_formatted():
    md = "```bash\necho \"**not bold**\" `x` <tag>\n```\n"
    html = md_to_html(md)
    assert html.strip() == '<pre><code class="language-bash">echo "**not bold**" `x` &lt;tag&gt;</code></pre>'


# ───────── bo'laklash ─────────
def long_markdown() -> str:
    parts = []
    for i in range(8):
        parts.append(f"## Bo'lim {i}\n" + ("Matn **qalin** `kod` qatori. " * 40) + "\n")
        code = "\n".join(f"echo line-{i}-{n} && ls -la /var/log/{n}" for n in range(60))  # ~2500 belgi
        parts.append(f"```bash\n{code}\n```\n")
    return "\n".join(parts)


def test_chunks_respect_limits_and_never_split_code_blocks():
    md = long_markdown()
    messages = theory_messages(md, header="📖 <b>Batafsil nazariya — #1</b>")
    assert len(messages) > 1
    for msg in messages:
        assert len(msg) <= CHUNK_LIMIT < TELEGRAM_LIMIT
        assert visible_len(msg) <= TELEGRAM_LIMIT
        assert msg.count("<pre>") == msg.count("</pre>")  # kod bloki ichida uzilmagan
    joined = "\n".join(messages)
    for i in range(8):
        block_start = f"echo line-{i}-0 "
        block_end = f"echo line-{i}-59 "
        holder = [m for m in messages if block_start in m]
        assert len(holder) == 1 and block_end in holder[0]  # butun blok bitta xabarda
    assert joined.count("Bo'lim 7") == 1
    assert messages[0].startswith("📖 <b>Batafsil nazariya — #1</b>")


def test_sections_are_packed_together_when_small():
    md = "## A\nqisqa\n\n## B\nqisqa\n\n## C\nqisqa\n"
    assert len(theory_messages(md)) == 1


def test_oversized_code_block_is_rejected():
    huge = "```text\n" + "x" * (CHUNK_LIMIT + 10) + "\n```\n"
    with pytest.raises(ValueError):
        theory_messages(huge)


# ───────── seed ─────────
def content_copy(tmp_path: Path) -> Path:
    dst = tmp_path / "content"
    shutil.copytree(ROOT / "content", dst)
    shutil.rmtree(dst / "junior" / "theory", ignore_errors=True)
    (dst / "junior" / "theory").mkdir()
    return dst


def test_load_content_reads_theory_file(tmp_path):
    root = content_copy(tmp_path)
    (root / "junior" / "theory" / "linux-01-intro.md").write_text("## Tushuncha\nmatn\n", encoding="utf-8")
    _, lessons = load_content(root)
    by_key = {item["key"]: item for _, item in lessons}
    assert by_key["linux-01-intro"]["theory_full"] == "## Tushuncha\nmatn\n"
    assert "theory_full" not in by_key["linux-02-fhs"]


def test_validate_rejects_theory_file_for_unknown_lesson(tmp_path):
    root = content_copy(tmp_path)
    (root / "junior" / "theory" / "linux-99-typo.md").write_text("## X\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="linux-99-typo"):
        validate(*load_content(root))


@pytest.fixture
async def sf(tmp_path):
    root = content_copy(tmp_path)
    (root / "junior" / "theory" / "linux-01-intro.md").write_text(long_markdown(), encoding="utf-8")
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        await seed(s, *load_content(root))
    yield factory, root
    await engine.dispose()


async def test_seed_stores_and_clears_theory_full(sf):
    factory, root = sf
    async with factory() as s:
        first = await repo.get_lesson_by_day(s, 1)
        assert first.theory_full.startswith("## Bo'lim 0")
        assert (await repo.get_lesson_by_day(s, 2)).theory_full is None
        (root / "junior" / "theory" / "linux-01-intro.md").unlink()  # fayl o'chirildi -> tugma yo'qoladi
        await seed(s, *load_content(root))
        assert (await repo.get_lesson_by_day(s, 1)).theory_full is None


# ───────── tugma, karta, handler ─────────
def buttons(kb) -> list[str]:
    return [b.text for row in kb.inline_keyboard for b in row]


def test_theory_button_only_when_text_exists():
    module = Module(slug="m", title="M", emoji="🐧", level="junior", stage="J1", stage_title="")
    lesson = Lesson(id=1, day_number=1, week=1, kind="lesson", title="t", theory="qisqa", task="v",
                    done_criteria="", duration_min=60, xp=10, module=module, questions=[], resources=[])
    assert "📖 Batafsil nazariya" not in buttons(lesson_kb(lesson, None))
    card_before = render.lesson_card(lesson)
    lesson.theory_full = "## Tushuncha\nmatn"
    assert "📖 Batafsil nazariya" in buttons(lesson_kb(lesson, None))
    assert render.lesson_card(lesson) == card_before  # karta matni o'zgarmaydi


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, **kw):
        self.sent.append((chat_id, text))

    async def __call__(self, method, request_timeout=None):
        return True


async def test_theory_callback_sends_all_chunks(sf):
    factory, _ = sf
    bot = FakeBot()
    async with factory() as s:
        user, _ = await repo.get_or_create_user(s, 42, None, "Ali", date(2026, 10, 12))
        first = await repo.get_lesson_by_day(s, 1)
        expected = theory_messages(first.theory_full, header=render.theory_header(first))
        cb = CallbackQuery(id="1", from_user=TgUser(id=42, is_bot=False, first_name="Ali"),
                           chat_instance="ci", data="x", message=None).as_(bot)
        await lesson_handlers.theory(cb, LessonCB(action="theory", lesson_id=first.id), s, user)
    assert [text for _, text in bot.sent] == expected and len(expected) > 1
