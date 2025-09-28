from aiogram import types
from aiogram.types import CallbackQuery
from bot.logger_config import logger
async def unknown_callback(call: CallbackQuery):
    """Обробка невідомих callback"""
    await call.answer("Невідома команда", show_alert=True)
    logger.warning(f"Невідомий callback від {call.from_user.id}: {call.data}")
