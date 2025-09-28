from aiogram import types
from aiogram.types import CallbackQuery
import logging
async def unknown_callback(call: CallbackQuery):
    """Обробка невідомих callback"""
    await call.answer("Невідома команда", show_alert=True)
    logging.warning(f"Невідомий callback від {call.from_user.id}: {call.data}")
