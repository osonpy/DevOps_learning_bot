"""'Manbalar' tugmasi: dars manbalari + modulning asosiy manbasi + amaliyot platformalari."""
import os
from pathlib import Path

os.environ.setdefault("BOT_TOKEN", "1:test")

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.db import repo
from src.db.base import Base
from src.db.models import Lesson, Module
from src.scripts.seed import load_content, seed
from src.services import render

ROOT = Path(__file__).resolve().parents[1]
LESSON_H, MAIN_H, PRACTICE_H = "Bu dars uchun", "📘 Modulning asosiy manbasi", "🧪 Amaliyot"


@pytest.fixture
async def sf(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/t.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        await seed(s, *load_content(ROOT / "content"))
    yield factory
    await engine.dispose()


async def test_seed_loads_module_resources(sf):
    async with sf() as s:
        linux = await s.scalar(select(Module).where(Module.slug == "linux-basics"))
        assert linux.main_resource == {"title": "The Linux Command Line", "url": "https://linuxcommand.org/tlcl.php"}
        assert [p["title"] for p in linux.practice] == ["OverTheWire Bandit", "SadServers"]
        middle = await s.scalar(select(Module).where(Module.level == "middle"))
        assert middle.main_resource is None and middle.practice == []


async def test_first_lesson_shows_all_three_sections(sf):
    async with sf() as s:
        text = render.resources_text(await repo.get_lesson_by_day(s, 1))
    assert text.index(LESSON_H) < text.index(MAIN_H) < text.index(PRACTICE_H)
    assert "https://linuxupskillchallenge.org/" in text and "Linux Upskill Challenge" in text
    assert "Operating System bo'limi" not in text
    assert 'href="https://linuxcommand.org/tlcl.php"' in text
    assert 'href="https://overthewire.org/wargames/bandit/"' in text


async def test_module_without_main_resource_hides_sections(sf):
    async with sf() as s:
        lesson = await s.scalar(select(Lesson).join(Module).where(Module.slug == "python-ops").limit(1))
        lesson = await repo.get_lesson(s, lesson.id)
        text = render.resources_text(lesson)
    assert LESSON_H in text
    assert MAIN_H not in text and PRACTICE_H not in text


def test_empty_sections_are_hidden():
    module = Module(slug="m", title="M", main_resource=None, practice=[{"title": "Lab", "url": "https://lab.example"}])
    only_practice = Lesson(day_number=7, title="t", resources=[], module=module)
    text = render.resources_text(only_practice)
    assert PRACTICE_H in text and LESSON_H not in text and MAIN_H not in text

    module.practice = []
    assert render.resources_text(only_practice) == "Bu dars uchun manba qo'shilmagan."


async def test_missing_main_resource_is_sql_null(sf):
    """JSON 'null' emas, haqiqiy SQL NULL — `WHERE main_resource IS NULL` ishlashi uchun."""
    async with sf() as s:
        slugs = set(await s.scalars(select(Module.slug).where(Module.main_resource.is_(None))))
    assert "python-ops" in slugs and "linux-basics" not in slugs
