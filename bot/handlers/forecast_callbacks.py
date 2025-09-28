import logging
from datetime import datetime
from aiogram.types import CallbackQuery
from bot.keyboards import WeatherKeyboards
from db.database import get_session
from db.crud import get_user_weather_settings, update_user_units


async def forecast_settings_callback(call: CallbackQuery):
    """Налаштування прогнозу"""
    await call.answer()
    
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    
    forecast_settings = {
        'forecast_days': settings.forecast_days,
        'past_days': settings.past_days
    }
    
    await call.message.edit_text(
        "📅 **Налаштування прогнозу**\n\n"
        f"Поточні налаштування:\n"
        f"• Днів прогнозу: {settings.forecast_days}\n"
        f"• Минулих днів: {settings.past_days}",
        reply_markup=WeatherKeyboards.forecast_settings(forecast_settings),
        parse_mode="Markdown"
    )


async def forecast_days_callback(call: CallbackQuery):
    """Вибір кількості днів прогнозу"""
    await call.answer()
    
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    
    await call.message.edit_text(
        "📅 **Оберіть кількість днів прогнозу:**\n\n"
        "Максимум 16 днів згідно з обмеженнями Open-Meteo API.",
        reply_markup=WeatherKeyboards.forecast_days_selector(settings.forecast_days),
        parse_mode="Markdown"
    )


async def set_forecast_days_callback(call: CallbackQuery):
    """Встановлення кількості днів прогнозу"""
    await call.answer()
    
    _, _, days_str = call.data.split(":", 2)
    days = int(days_str)
    
    try:
        async for session in get_session():
            settings = await get_user_weather_settings(session, call.from_user.id)
            settings.forecast_days = days
            settings.updated_at = datetime.now()
            await session.commit()
        
        await call.answer(f"Встановлено {days} днів прогнозу", show_alert=True)
        await forecast_settings_callback(call)
        
    except Exception as e:
        await call.answer(f"Помилка: {str(e)}", show_alert=True)
        logging.error(f"Помилка встановлення forecast_days для {call.from_user.id}: {str(e)}")


async def forecast_past_days_callback(call: CallbackQuery):
    """Вибір кількості минулих днів"""
    await call.answer()
    
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    
    await call.message.edit_text(
        "🕰️ **Оберіть кількість минулих днів:**\n\n"
        "Максимум 7 днів згідно з обмеженнями Open-Meteo API.",
        reply_markup=WeatherKeyboards.forecast_past_days_selector(settings.past_days),
        parse_mode="Markdown"
    )


async def set_forecast_past_days_callback(call: CallbackQuery):
    """Встановлення кількості минулих днів"""
    await call.answer()
    
    _, _, days_str = call.data.split(":", 2)
    days = int(days_str)
    
    try:
        async for session in get_session():
            await update_user_units(session, call.from_user.id, past_days=days)
        
        await call.answer(f"Минулих днів встановлено: {days}", show_alert=True)
        await forecast_settings_callback(call)
        
    except Exception as e:
        await call.answer(f"Помилка: {str(e)}", show_alert=True)
        logging.error(f"Помилка встановлення past_days для {call.from_user.id}: {str(e)}")
