import asyncio
import logging

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, InlineQuery, Message
from aiogram.utils.i18n import gettext as _

from services import database

logger = logging.getLogger(__name__)


class UserBannedMiddleware(BaseMiddleware):
    async def _get_user_status(self, user_id: int | None) -> str:
        if user_id is None:
            return "active"

        try:
            return await database.status(user_id) or "active"
        except Exception:
            logger.warning("Failed to resolve user status for %s", user_id, exc_info=True)
            return "active"

    async def on_pre_process_message(self, message: Message, data: dict):
        user_status = await self._get_user_status(message.from_user.id if message.from_user else None)
        if user_status == "ban":
            if message.chat.type == "private":
                await message.answer(_("You are banned please contact @mak5er for more information!"))
            raise asyncio.CancelledError

    async def on_pre_process_callback_query(self, callback_query: CallbackQuery, data: dict):
        user_status = await self._get_user_status(callback_query.from_user.id if callback_query.from_user else None)
        if user_status == "ban":
            await callback_query.answer(
                _("You are banned please contact @mak5er for more information!"),
                show_alert=True,
            )
            raise asyncio.CancelledError

    async def on_pre_process_inline_query(self, inline_query: InlineQuery, data: dict):
        user_status = await self._get_user_status(inline_query.from_user.id if inline_query.from_user else None)
        if user_status == "ban":
            raise asyncio.CancelledError

    async def __call__(self, handler, event, data):
        if isinstance(event, Message):
            await self.on_pre_process_message(event, data)
        elif isinstance(event, CallbackQuery):
            await self.on_pre_process_callback_query(event, data)
        elif isinstance(event, InlineQuery):
            await self.on_pre_process_inline_query(event, data)
        return await handler(event, data)
