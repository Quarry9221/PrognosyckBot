# bot/notifications.py
import asyncio
import datetime
from bot.logger_config import logger

from aiogram.enums import ParseMode
from bot.keyboards import WeatherKeyboards
from bot.handlers.utils import format_weather_response
from db.crud import get_api_parameters
from services.weather import get_weather
from db.models import UserWeatherSettings
from db.session import async_session  # твій async_sessionmaker
from sqlalchemy import select


async def daily_notifications_scheduler(bot):
    """
    Фонова задача для щоденних сповіщень про погоду.
    Бере користувачів, у яких увімкнені сповіщення та час співпадає з поточним.
    """
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        try:
            async with async_session() as session:
                # отримуємо об’єкти UserWeatherSettings
                stmt = select(UserWeatherSettings).where(
                    UserWeatherSettings.notification_enabled.is_(True),
                    UserWeatherSettings.notification_time == now
                )
                result = await session.execute(stmt)
                users_settings = result.scalars().all()  # список ORM об’єктів

                for settings in users_settings:
                    try:
                        api_params = await get_api_parameters(session, settings.user_id)
                        weather_data = await get_weather(
                            settings.latitude,
                            settings.longitude,
                            api_params
                        )

                        location_data = {
                            "city": settings.location_name or "Ваша локація",
                            "lat": settings.latitude,
                            "lon": settings.longitude
                        }

                        response = await format_weather_response(weather_data, location_data, api_params)

                        await bot.send_message(
                            settings.user_id,
                            f"🔔 Щоденна погода:\n\n{response}",
                            reply_markup=WeatherKeyboards.weather_type_menu(),
                            parse_mode=ParseMode.MARKDOWN
                        )
                        logger.info(f"Відправлено щоденне повідомлення користувачу {settings.user_id}")

                    except Exception as e:
                        logger.error(f"Помилка надсилання щоденного повідомлення {settings.user_id}: {e}")

        except Exception as e:
            logger.error(f"Помилка при отриманні користувачів для щоденних сповіщень: {e}")

        await asyncio.sleep(60)  # перевірка щохвилини
