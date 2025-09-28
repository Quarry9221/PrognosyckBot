from aiogram import types
from aiogram.types import CallbackQuery
from bot.keyboards import WeatherKeyboards
from db.crud import get_user_weather_settings, set_user_state
from db.database import get_session

async def notifications_settings_callback(call: CallbackQuery):
    """Налаштування сповіщень"""
    await call.answer()
    
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    
    notification_settings = {
        'notification_enabled': settings.notification_enabled,
        'notification_time': settings.notification_time
    }
    
    await call.message.edit_text(
        "🔔 **Налаштування сповіщень**\n\n"
        f"Стан: {'✅ Увімкнені' if settings.notification_enabled else '❌ Вимкнені'}\n"
        f"Час: {settings.notification_time or 'Не встановлено'}",
        reply_markup=WeatherKeyboards.notifications_settings(notification_settings),
        parse_mode="Markdown"
    )

async def notifications_time_callback(call: CallbackQuery):
    """Обробник вибору часу сповіщень"""
    await call.answer()
    
    # Встановлюємо стан користувача на очікування часу
    async for session in get_session():
        await set_user_state(session, call.from_user.id, "AWAITING_NOTIFICATION_TIME")
    
    await call.message.edit_text(
        "⏰ **Оберіть час для щоденних сповіщень:**\n\nНапишіть час у форматі HH:MM (наприклад, 08:30)",
        reply_markup=WeatherKeyboards.back_button("settings:notifications"),
        parse_mode="Markdown"
    )

