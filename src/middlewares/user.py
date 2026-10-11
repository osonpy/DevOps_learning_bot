from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Router
from aiogram.types import TelegramObject

from src.db import repo


class UserMiddleware(BaseMiddleware):
    """Handler'ga `user` beradi; /start qilmagan bo'lsa — bir xil javob va handler chaqirilmaydi.

    DbSessionMiddleware'dan keyin ishlaydi (data["session"] kerak).
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        user = await repo.get_user(data["session"], tg_user.id) if tg_user else None
        if user is None:
            await event.answer("Avval /start bosing 🙂")  # Message: xabar, CallbackQuery: toast
            return None
        data["user"] = user
        return await handler(event, data)


def require_user(router: Router) -> Router:
    """Router'dagi barcha message/callback handler'lari uchun guard."""
    router.message.middleware(UserMiddleware())
    router.callback_query.middleware(UserMiddleware())
    return router
