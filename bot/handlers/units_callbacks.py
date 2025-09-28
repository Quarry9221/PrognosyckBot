from bot.logger_config import logger
from datetime import datetime
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from bot.handlers.notifications_callbacks import notifications_settings_callback
from bot.handlers.settings_callbacks import display_settings_callback, units_settings_callback
from bot.keyboards import WeatherKeyboards
from db.database import get_session
from db.crud import (
    get_user_weather_settings,
    toggle_display_setting,
    update_user_units
)

async def toggle_setting_callback(call: CallbackQuery):
    logger.info(f"Toggle callback: {call.data} from user {call.from_user.id}")
    """Перемикання булевих налаштувань"""
    await call.answer()
    
    _, setting_name = call.data.split(":", 1)
    
    try:
        async for session in get_session():
            new_value = await toggle_display_setting(session, call.from_user.id, setting_name)
        
        status = "✅ Увімкнено" if new_value else "❌ Вимкнено"
        await call.answer(f"{setting_name.replace('show_', '').replace('_', ' ').title()}: {status}", show_alert=True)
        
        # Оновлюємо відповідну клавіатуру
        if setting_name == "notification_enabled":
            await notifications_settings_callback(call)
        else:
            await display_settings_callback(call)
        logger.info(f"Toggled {setting_name} for user {call.from_user.id}: new value {new_value}")
        
    except ValueError as e:
        await call.answer(f"Помилка: {str(e)}", show_alert=True)
        logger.error(f"Error toggling {setting_name} for user {call.from_user.id}: {str(e)}")


async def set_unit_callback(call: CallbackQuery):
    """Встановлення одиниць виміру"""
    await call.answer()
    
    _, unit_type, unit_value = call.data.split(":", 2)
    
    try:
        async for session in get_session():
            kwargs = {unit_type: unit_value}
            await update_user_units(session, call.from_user.id, **kwargs)
        
        unit_labels = {
            'temperature_unit': 'Температура',
            'wind_speed_unit': 'Швидкість вітру',
            'precipitation_unit': 'Опади',
            'timeformat': 'Формат часу'
        }
        
        await call.answer(f"{unit_labels.get(unit_type, unit_type)}: {unit_value}", show_alert=True)
        
        # Повертаємося до меню одиниць
        await units_settings_callback(call)
        
    except Exception as e:
        await call.answer(f"Помилка: {str(e)}", show_alert=True)
        logger.error(f"Помилка встановлення {unit_type}={unit_value} для {call.from_user.id}: {str(e)}")


async def temperature_unit_callback(call: CallbackQuery):
    """Вибір одиниць температури"""
    await call.answer()
    
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    
    await call.message.edit_text(
        "🌡️ **Оберіть одиниці температури:**",
        reply_markup=WeatherKeyboards.temperature_unit_selector(settings.temperature_unit),
        parse_mode="Markdown"
    )


async def wind_speed_unit_callback(call: CallbackQuery):
    """Вибір одиниць швидкості вітру"""
    await call.answer()
    
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    
    await call.message.edit_text(
        "💨 **Оберіть одиниці швидкості вітру:**",
        reply_markup=WeatherKeyboards.wind_speed_unit_selector(settings.wind_speed_unit),
        parse_mode="Markdown"
    )


async def precipitation_unit_callback(call: CallbackQuery):
    """Вибір одиниць опадів"""
    await call.answer()
    
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    
    precipitation_keyboard = [
        [InlineKeyboardButton(
            text=f"{'✅' if settings.precipitation_unit == 'mm' else '⚪'} Міліметри (мм)", 
            callback_data="set_unit:precipitation_unit:mm"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if settings.precipitation_unit == 'inch' else '⚪'} Дюйми (inch)", 
            callback_data="set_unit:precipitation_unit:inch"
        )],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:units")]
    ]
    
    await call.message.edit_text(
        "🌧️ **Оберіть одиниці опадів:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=precipitation_keyboard),
        parse_mode="Markdown"
    )


async def timeformat_unit_callback(call: CallbackQuery):
    """Вибір формату часу"""
    await call.answer()
    
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    
    await call.message.edit_text(
        "🕒 **Оберіть формат часу:**",
        reply_markup=WeatherKeyboards.timeformat_unit_selector(settings.timeformat),
        parse_mode="Markdown"
    )


async def set_timeformat_callback(call: CallbackQuery):
    """Встановлення формату часу"""
    await call.answer()
    
    _, _, timeformat = call.data.split(":", 2)
    
    try:
        async for session in get_session():
            settings = await get_user_weather_settings(session, call.from_user.id)
            settings.timeformat = timeformat
            settings.updated_at = datetime.now()
            await session.commit()
        
        await call.answer(f"Формат часу встановлено: {timeformat}", show_alert=True)
        await units_settings_callback(call)
        
    except Exception as e:
        await call.answer(f"Помилка: {str(e)}", show_alert=True)
        logger.error(f"Помилка встановлення timeformat для {call.from_user.id}: {str(e)}")
