# bot/handlers/settings_callbacks.py
from aiogram import types
from bot.keyboards import WeatherKeyboards
from db.crud import get_user_settings_summary, get_user_weather_settings
from db.database import get_session
from aiogram.types import CallbackQuery
from bot.logger_config import logger


async def units_settings_callback(call: CallbackQuery):
    """Налаштування одиниць виміру"""
    await call.answer()
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)

    current_units = {
        "temperature_unit": settings.temperature_unit,
        "wind_speed_unit": settings.wind_speed_unit,
        "precipitation_unit": settings.precipitation_unit,
        "timeformat": settings.timeformat,
    }

    try:
        await call.message.edit_text(
            "📏 **Налаштування одиниць виміру**\n\nОбери параметр для зміни:",
            reply_markup=WeatherKeyboards.units_settings(current_units),
            parse_mode="Markdown",
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise


async def location_settings_callback(call: CallbackQuery):
    """Налаштування локації"""
    await call.answer()
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)

    location_info = "❌ Локація не встановлена"
    if settings.latitude and settings.longitude:
        location_info = (
            f"📍 **Поточна локація:**\n"
            f"{settings.location_name or 'Невідома назва'}\n"
            f"🌐 {settings.latitude:.4f}, {settings.longitude:.4f}\n"
            f"🕐 Часовий пояс: {settings.timezone}"
        )

    text = f"🌍 **Налаштування локації**\n\n{location_info}"
    try:
        await call.message.edit_text(
            text,
            reply_markup=WeatherKeyboards.location_settings(),
            parse_mode="Markdown",
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise


async def display_settings_callback(call: CallbackQuery):
    """Налаштування відображення"""
    await call.answer()
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)

    display_settings = {
        "show_temperature": settings.show_temperature,
        "show_feels_like": settings.show_feels_like,
        "show_humidity": settings.show_humidity,
        "show_pressure": settings.show_pressure,
        "show_wind": settings.show_wind,
        "show_precipitation": settings.show_precipitation,
        "show_precipitation_probability": settings.show_precipitation_probability,
        "show_cloud_cover": settings.show_cloud_cover,
        "show_uv_index": settings.show_uv_index,
        "show_visibility": settings.show_visibility,
        "show_daily_temperature": settings.show_daily_temperature,
        "show_sunrise_sunset": settings.show_sunrise_sunset,
        "show_daylight_duration": settings.show_daylight_duration,
    }

    try:
        await call.message.edit_text(
            "📊 **Налаштування відображення**\n\nВибери, що показувати в прогнозі погоди:",
            reply_markup=WeatherKeyboards.display_settings(display_settings),
            parse_mode="Markdown",
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise


async def settings_summary_callback(call: CallbackQuery):
    """Показати детальний опис налаштувань"""
    await call.answer()

    async for session in get_session():
        summary = await get_user_settings_summary(session, call.from_user.id)

    await call.message.edit_text(
        summary,
        reply_markup=WeatherKeyboards.back_button("menu:settings"),
        parse_mode="Markdown",
    )


async def edit_notifications_display_callback(call: CallbackQuery):
    """Відкрити меню налаштування відображення для сповіщень"""
    await call.answer()
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    display_settings = {
        "show_temperature": settings.show_temperature,
        "show_feels_like": settings.show_feels_like,
        "show_humidity": settings.show_humidity,
        "show_pressure": settings.show_pressure,
        "show_wind": settings.show_wind,
        "show_precipitation": settings.show_precipitation,
        "show_precipitation_probability": settings.show_precipitation_probability,
        "show_cloud_cover": settings.show_cloud_cover,
        "show_uv_index": settings.show_uv_index,
        "show_visibility": settings.show_visibility,
        "show_daily_temperature": settings.show_daily_temperature,
        "show_sunrise_sunset": settings.show_sunrise_sunset,
        "show_daylight_duration": settings.show_daylight_duration,
    }
    await call.message.edit_text(
        "📊 **Налаштування відображення для сповіщень**\n\nВибери, що показувати в повідомленнях:",
        reply_markup=WeatherKeyboards.display_settings(display_settings),
        parse_mode="Markdown",
    )
