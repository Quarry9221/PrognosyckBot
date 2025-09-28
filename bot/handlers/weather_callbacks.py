from bot.logger_config import logger
from aiogram.types import CallbackQuery
from db.database import get_session
from db.crud import get_user_weather_settings, get_api_parameters
from services.weather import get_weather
from bot.keyboards import WeatherKeyboards
from bot.handlers.utils import format_weather_response
from aiogram.exceptions import TelegramBadRequest


async def current_weather_callback(call: CallbackQuery):
    """Показати поточну погоду"""
    await call.answer()
    try:
        async for session in get_session():
            api_params = await get_api_parameters(session, call.from_user.id)
            settings = await get_user_weather_settings(session, call.from_user.id)

        if not settings.latitude or not settings.longitude:
            await call.message.edit_text(
                "❌ **Локація не встановлена**\n\nСпочатку встанови свою локацію в налаштуваннях або надішли назву міста.",
                reply_markup=WeatherKeyboards.location_settings(),
                parse_mode="Markdown"
            )
            return

        api_params['current'] = 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m'

        weather_data = await get_weather(settings.latitude, settings.longitude, api_params)

        location_data = {
            "city": settings.location_name or "Невідома локація",
            "lat": settings.latitude,
            "lon": settings.longitude
        }

        response = await format_weather_response(weather_data, location_data, api_params)

        await call.message.edit_text(
            response,
            reply_markup=WeatherKeyboards.weather_type_menu(),
            parse_mode="Markdown"
        )

    except Exception as e:
        if isinstance(e, TelegramBadRequest) and "message is not modified" in str(e):
            pass
        else:
            await call.message.edit_text(
                f"❌ Помилка отримання погоди: {str(e)}",
                reply_markup=WeatherKeyboards.main_menu()
            )
            logger.error(f"Помилка отримання поточної погоди для {call.from_user.id}: {str(e)}")


async def weekly_weather_callback(call: CallbackQuery):
    """Показати тижневий прогноз"""
    await call.answer("Отримуємо тижневий прогноз...")
    await current_weather_callback(call)  # Використовуємо ту ж логіку


async def hourly_weather_callback(call: CallbackQuery):
    """Показати почасовий прогноз"""
    await call.answer("Почасовий прогноз поки в розробці", show_alert=True)


async def today_weather_callback(call: CallbackQuery):
    """Показати прогноз на сьогодні"""
    await call.answer("Отримуємо прогноз на сьогодні...")
    try:
        async for session in get_session():
            settings = await get_user_weather_settings(session, call.from_user.id)
            if not settings.latitude or not settings.longitude:
                await call.message.edit_text(
                    "❌ Локація не встановлена. Вкажіть місто або координати.",
                    reply_markup=WeatherKeyboards.main_menu()
                )
                return
            api_params = await get_api_parameters(session, call.from_user.id)
            api_params['forecast_days'] = 1
            api_params['daily'] = 'weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,precipitation_probability_max,wind_speed_10m_max'

            weather_data = await get_weather(settings.latitude, settings.longitude, api_params)

            location_data = {
                "city": settings.location_name or "Невідома локація",
                "lat": settings.latitude,
                "lon": settings.longitude
            }

            response = await format_weather_response(weather_data, location_data, api_params)

            await call.message.edit_text(
                response,
                reply_markup=WeatherKeyboards.weather_type_menu(),
                parse_mode="Markdown"
            )

    except Exception as e:
        if isinstance(e, TelegramBadRequest) and "message is not modified" in str(e):
            pass
        else:
            await call.message.edit_text(
                f"❌ Помилка отримання прогнозу: {str(e)}",
                reply_markup=WeatherKeyboards.main_menu()
            )
            logger.error(f"Помилка отримання прогнозу на сьогодні для {call.from_user.id}: {str(e)}")


async def three_days_weather_callback(call: CallbackQuery):
    """Показати прогноз на 3 дні"""
    await call.answer("Отримуємо прогноз на 3 дні...")
    try:
        async for session in get_session():
            api_params = await get_api_parameters(session, call.from_user.id)
            settings = await get_user_weather_settings(session, call.from_user.id)

        if not settings.latitude or not settings.longitude:
            await call.message.edit_text(
                "❌ **Локація не встановлена**\n\nСпочатку встанови свою локацію в налаштуваннях або надішли назву міста.",
                reply_markup=WeatherKeyboards.location_settings(),
                parse_mode="Markdown"
            )
            return

        api_params['current'] = 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m'
        api_params['forecast_days'] = 3

        weather_data = await get_weather(settings.latitude, settings.longitude, api_params)

        location_data = {
            "city": settings.location_name or "Невідома локація",
            "lat": settings.latitude,
            "lon": settings.longitude
        }

        response = await format_weather_response(weather_data, location_data, api_params)

        await call.message.edit_text(
            response,
            reply_markup=WeatherKeyboards.weather_type_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        if isinstance(e, TelegramBadRequest) and "message is not modified" in str(e):
            pass
        else:
            await call.message.edit_text(
                f"❌ Помилка отримання погоди: {str(e)}",
                reply_markup=WeatherKeyboards.main_menu()
            )
            logger.error(f"Помилка отримання погоди для {call.from_user.id}: {str(e)}")
