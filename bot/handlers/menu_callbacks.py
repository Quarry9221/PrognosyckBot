from aiogram.types import CallbackQuery
from bot.keyboards import WeatherKeyboards
from db.database import get_session
from db.crud import get_user_settings_summary


async def main_menu_callback(call: CallbackQuery):
    """Повернення до головного меню"""
    await call.answer()
    try:
        await call.message.edit_text(
            "🏠 **Головне меню**\n\nОбери дію з меню нижче:",
            reply_markup=WeatherKeyboards.main_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise


async def settings_menu_callback(call: CallbackQuery):
    """Відкриття меню налаштувань"""
    await call.answer()
    summary = ""
    async for session in get_session():
        summary = await get_user_settings_summary(session, call.from_user.id)
    
    try:
        await call.message.edit_text(
            summary,
            reply_markup=WeatherKeyboards.settings_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise
