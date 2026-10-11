import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from src.config import settings
from src.db.session import SessionFactory
from src.handlers import lesson, progress, review, start
from src.handlers import settings as settings_handlers
from src.middlewares.db import DbSessionMiddleware
from src.scheduler.jobs import setup_scheduler

COMMANDS = [
    BotCommand(command="today", description="📚 Bugungi dars"),
    BotCommand(command="review", description="🔁 Takrorlash"),
    BotCommand(command="progress", description="📊 Progress"),
    BotCommand(command="roadmap", description="🗺 Bosqichlar"),
    BotCommand(command="settings", description="⚙️ Sozlamalar"),
    BotCommand(command="help", description="Yordam"),
]


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True))
    dp = Dispatcher(storage=MemoryStorage())  # ko'p user bo'lganda: RedisStorage
    dp.update.middleware(DbSessionMiddleware(SessionFactory))
    dp.include_routers(start.router, settings_handlers.router, progress.router, review.router, lesson.router)

    scheduler = setup_scheduler(bot, SessionFactory)
    try:
        scheduler.start()
        await bot.set_my_commands(COMMANDS)
        await dp.start_polling(bot)
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
