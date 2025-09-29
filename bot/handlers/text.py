import re
from bot.logger_config import logger
from aiogram.types import Message
from bot.keyboards import WeatherKeyboards
from db.crud import (
    get_user_state,
    set_user_state,
    update_user_location,
    save_notification_time,
    save_user_message,
    get_api_parameters,
)
from db.database import get_session
from services.weather import get_weather
from services.geocode import geocode_place
from bot.handlers.utils import format_weather_response


async def text_handler(message: Message):
    async for session in get_session():
        state = await get_user_state(session, message.from_user.id)

        if state == "AWAITING_NOTIFICATION_TIME":

            if re.match(r"^\d{2}:\d{2}$", message.text.strip()):
                await save_notification_time(
                    session, message.from_user.id, message.text.strip()
                )
                await set_user_state(session, message.from_user.id, None)
                await message.reply(
                    f"⏰ Час сповіщень встановлено: {message.text.strip()}",
                    reply_markup=WeatherKeyboards.main_menu(),
                )
            else:
                await message.reply(
                    "❌ Невірний формат часу. Вкажи у HH:MM (наприклад, 08:30)"
                )
            return

        place = message.text.strip()
        logger.info(f"Запит погоди від користувача {message.from_user.id}: '{place}'")

        await message.bot.send_chat_action(message.chat.id, "typing")

        try:
            location_data = await geocode_place(place)
            lat = location_data["lat"]
            lon = location_data["lon"]
            city = location_data.get("city", "")
            country = location_data.get("country", "")

            await update_user_location(
                session,
                message.from_user.id,
                lat,
                lon,
                location_name=f"{city}, {country}" if city and country else place,
            )

            api_params = await get_api_parameters(session, message.from_user.id)

            await save_user_message(
                session,
                message.from_user.id,
                message.chat.id,
                place,
                location_requested=place,
                latitude=lat,
                longitude=lon,
            )

            weather_data = await get_weather(lat, lon, api_params)
            response = await format_weather_response(
                weather_data, location_data, api_params
            )

            await message.reply(
                response,
                reply_markup=WeatherKeyboards.weather_type_menu(),
                parse_mode="Markdown",
            )

        except ValueError as e:
            await message.reply(
                f"❌ Помилка: {str(e)}\n💡 Спробуй вказати місто та країну",
                parse_mode="Markdown",
            )
            logger.warning(f"Помилка геокодування для {message.from_user.id}: {str(e)}")

        except Exception as e:
            await message.reply(
                "❌ Виникла технічна помилка. Спробуй пізніше або звернись до підтримки.",
                reply_markup=WeatherKeyboards.main_menu(),
            )
            logger.error(
                f"Несподівана помилка для {message.from_user.id}: {str(e)}",
                exc_info=True,
            )
