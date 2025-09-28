from bot.handlers.utils import format_weather_response
from bot.logger_config import logger
from aiogram.types import Message
from bot.keyboards import WeatherKeyboards
from db.crud import update_user_location, save_user_message, get_api_parameters
from db.database import get_session
from services.weather import get_weather
from services.geocode import geocode_place


async def text_handler(message: Message):
    """Обробник текстових повідомлень (пошук погоди)"""
    place = message.text.strip()
    logger.info(f"Запит погоди від користувача {message.from_user.id}: '{place}'")
    
    # Показуємо індикатор набору
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Геокодування локації
        location_data = await geocode_place(place)
        lat = location_data["lat"]
        lon = location_data["lon"]
        city = location_data.get("city", "")
        country = location_data.get("country", "")
        
        logger.info(f"Геокодування пройшло успішно для {message.from_user.id}: {lat}, {lon} ({city}, {country})")
        
        # Оновлюємо локацію користувача
        async for session in get_session():
            await update_user_location(
                session, 
                message.from_user.id, 
                lat, lon, 
                location_name=f"{city}, {country}" if city and country else place
            )
            logger.info(f"Оновлено локацію користувача {message.from_user.id}")
            
            # Отримуємо параметри API
            api_params = await get_api_parameters(session, message.from_user.id)
            logger.info(f"Отримано API параметри для користувача {message.from_user.id}")
            
            # Зберігаємо повідомлення
            await save_user_message(
                session,
                message.from_user.id,
                message.chat.id,
                place,
                location_requested=place,
                latitude=lat,
                longitude=lon
            )
            logger.info(f"Збережено повідомлення користувача {message.from_user.id}: '{place}'")
        
        # Отримуємо дані про погоду
        weather_data = await get_weather(lat, lon, api_params)
        logger.info(f"Отримано дані про погоду для користувача {message.from_user.id}")
        
        # Форматуємо відповідь
        response = await format_weather_response(weather_data, location_data, api_params)
        
        await message.reply(
            response,
            reply_markup=WeatherKeyboards.weather_type_menu(),
            parse_mode="Markdown"
        )
        
        logger.info(f"Успішна відповідь користувачу {message.from_user.id} для '{place}'")
        
    except ValueError as e:
        error_msg = (
            f"❌ **Помилка:** {str(e)}\n\n"
            "💡 **Спробуй:**\n"
            "• Вказати місто та країну\n"
            "• Використати англійську назву\n"
            "• Перевірити правопис"
        )
        await message.reply(error_msg, parse_mode="Markdown")
        logger.warning(f"Помилка геокодування для {message.from_user.id}: {str(e)}")
        
    except Exception as e:
        await message.reply(
            "❌ Виникла технічна помилка. Спробуй пізніше або звернись до підтримки.",
            reply_markup=WeatherKeyboards.main_menu()
        )
        logger.error(f"Несподівана помилка для {message.from_user.id}: {str(e)}", exc_info=True)
