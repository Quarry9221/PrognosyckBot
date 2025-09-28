# bot/handlers/commands.py
import logging
from bot.logger_config import logger  # імпортуємо налаштований logger
from aiogram import types
from aiogram.types import Message
from bot.keyboards import WeatherKeyboards
from db.crud import get_user_settings_summary
from db.database import get_session
from db.utils import get_or_create_user

async def start_handler(message: Message):
    logger.info(f"/start від користувача {message.from_user.id}")
    async for session in get_session():
        user = await get_or_create_user(
            session,
            message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code
        )
    
    welcome_text = """
🌤️ **Привіт! Я твій персональний погодний асистент!**
...
    """
    await message.reply(
        welcome_text,
        reply_markup=WeatherKeyboards.main_menu(),
        parse_mode="Markdown"
    )

async def help_handler(message: Message):
    logger.info(f"/help від користувача {message.from_user.id}")
    help_text = """
🆘 **Допомога по боту:**...
    """
    await message.reply(help_text, reply_markup=WeatherKeyboards.main_menu(), parse_mode="Markdown")

async def settings_handler(message: Message):
    logger.info(f"/settings від користувача {message.from_user.id}")
    async for session in get_session():
        summary = await get_user_settings_summary(session, message.from_user.id)
    
    await message.reply(summary, reply_markup=WeatherKeyboards.settings_menu(), parse_mode="Markdown")
