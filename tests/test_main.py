"""main(): ishga tushishda xato bo'lsa ham scheduler va HTTP session yopiladi."""
import os
from pathlib import Path

os.environ.setdefault("BOT_TOKEN", "1:test")

import pytest
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.methods import SetMyCommands

import src.main as app


class FakeSession:
    closed = False

    async def close(self):
        self.closed = True


class FakeBot:
    instances: list["FakeBot"] = []

    def __init__(self, token, default=None):
        self.default = default
        self.session = FakeSession()
        FakeBot.instances.append(self)

    async def set_my_commands(self, commands):
        raise TelegramUnauthorizedError(method=SetMyCommands(commands=commands), message="Unauthorized")


class FakeScheduler:
    def __init__(self):
        self.running = False
        self.shutdown_called = False

    def start(self):
        self.running = True

    def shutdown(self, wait=True):
        self.shutdown_called = True
        self.running = False


async def test_startup_failure_cleans_up(monkeypatch):
    scheduler = FakeScheduler()
    monkeypatch.setattr(app, "Bot", FakeBot)
    monkeypatch.setattr(app, "setup_scheduler", lambda bot, sf: scheduler)
    with pytest.raises(TelegramUnauthorizedError):
        await app.main()
    bot = FakeBot.instances[-1]
    assert scheduler.shutdown_called
    assert bot.session.closed
    # main() bir marta chaqiriladi (router'lar bitta Dispatcher'ga ulanadi) — default'ni shu yerda tekshiramiz
    assert bot.default.link_preview_is_disabled is True


def test_no_deprecated_disable_web_page_preview():
    """aiogram'da deprecated: DefaultBotProperties(link_preview_is_disabled=True) ishlatiladi."""
    root = Path(app.__file__).parent
    offenders = [str(p.relative_to(root)) for p in root.rglob("*.py") if "disable_web_page_preview" in p.read_text()]
    assert offenders == []
