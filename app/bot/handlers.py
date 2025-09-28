# handlers.py - Покращені обробники команд для погодного бота

import logging
import os
from datetime import datetime
from typing import Optional

from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.db.database import get_session
from app.db.crud import (
    get_or_create_user, get_user_weather_settings, update_user_location,
    update_user_units, toggle_display_setting, get_api_parameters,
    save_user_message, get_user_settings_summary
)
from app.services.geocode import geocode_place
from app.services.weather import get_weather
from app.bot.keyboards import WeatherKeyboards

# Налаштування логування
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"weather_bot_{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# FSM стани для роботи з налаштуваннями
class SettingsStates(StatesGroup):
    waiting_location = State()
    waiting_elevation = State()
    waiting_notification_time = State()

# ===== БАЗОВІ ОБРОБНИКИ =====

async def start_handler(message: Message):
    """Обробник команди /start"""
    logging.info(f"/start від користувача {message.from_user.id}")
    
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

🔹 Надішли назву міста, щоб отримати прогноз погоди
🔹 Використовуй кнопки меню для швидкого доступу
🔹 Налаштуй бота під себе в розділі налаштувань

Для початку встанови свою локацію або просто надішли назву міста!
    """
    
    await message.reply(
        welcome_text,
        reply_markup=WeatherKeyboards.main_menu(),
        parse_mode="Markdown"
    )

async def help_handler(message: Message):
    """Обробник команди /help"""
    help_text = """
🆘 **Допомога по боту:**

**Основні команди:**
• `/start` - Почати роботу з ботом
• `/settings` - Переглянути налаштування
• `/help` - Ця довідка

**Як користуватися:**
1️⃣ Надішли назву міста для отримання погоди
2️⃣ Використовуй кнопки меню для швидкого доступу
3️⃣ Налаштуй параметри в розділі "Налаштування"

**Підтримувані формати міст:**
• "Київ"
• "Mukachevo, Ukraine" 
• "New York, USA"
• "48.9166, 24.7111" (координати)

**Налаштування:**
• Одиниці виміру (°C/°F, км/год/м/с тощо)
• Що показувати в прогнозі
• Кількість днів прогнозу (1-16)
• Щоденні сповіщення

Потрібна допомога? Напиши @your_support_username
    """
    
    await message.reply(
        help_text,
        reply_markup=WeatherKeyboards.main_menu(),
        parse_mode="Markdown"
    )

async def settings_handler(message: Message):
    """Обробник команди /settings"""
    logging.info(f"/settings від користувача {message.from_user.id}")
    
    async for session in get_session():
        summary = await get_user_settings_summary(session, message.from_user.id)
    
    await message.reply(
        summary,
        reply_markup=WeatherKeyboards.settings_menu(),
        parse_mode="Markdown"
    )

# ===== ОБРОБНИКИ ТЕКСТУ =====

async def text_handler(message: Message):
    """Обробник текстових повідомлень (пошук погоди)"""
    place = message.text.strip()
    logging.info(f"Запит погоди від {message.from_user.id}: '{place}'")
    
    # Показуємо індикатор набору
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Геокодування локації
        location_data = await geocode_place(place)
        lat = location_data["lat"]
        lon = location_data["lon"]
        city = location_data.get("city", "")
        state = location_data.get("state", "")
        country = location_data.get("country", "")
        
        # Оновлюємо локацію користувача
        async for session in get_session():
            await update_user_location(
                session, 
                message.from_user.id, 
                lat, lon, 
                location_name=f"{city}, {country}" if city and country else place
            )
            
            # Отримуємо параметри API
            api_params = await get_api_parameters(session, message.from_user.id)
            
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
        
        # Отримуємо дані про погоду
        weather_data = await get_weather(lat, lon, api_params)
        
        # Форматуємо відповідь
        response = await format_weather_response(weather_data, location_data, api_params)
        
        await message.reply(
            response,
            reply_markup=WeatherKeyboards.weather_type_menu(),
            parse_mode="Markdown"
        )
        
        logging.info(f"Успішна відповідь користувачу {message.from_user.id} для '{place}'")
        
    except ValueError as e:
        error_msg = f"❌ **Помилка:** {str(e)}\n\n💡 **Спробуй:**\n• Вказати місто та країну\n• Використати англійську назву\n• Перевірити правопис"
        await message.reply(error_msg, parse_mode="Markdown")
        logging.error(f"Помилка геокодування для {message.from_user.id}: {str(e)}")
        
    except Exception as e:
        await message.reply(
            "❌ Виникла технічна помилка. Спробуй пізніше або звернись до підтримки.",
            reply_markup=WeatherKeyboards.main_menu()
        )
        logging.error(f"Несподівана помилка для {message.from_user.id}: {str(e)}", exc_info=True)

# ===== CALLBACK ОБРОБНИКИ МЕНЮ =====

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

# ===== CALLBACK ОБРОБНИКИ НАЛАШТУВАНЬ =====

async def location_settings_callback(call: CallbackQuery):
    """Налаштування локації"""
    await call.answer()
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    location_info = "❌ Локація не встановлена"
    if settings.latitude and settings.longitude:
        location_info = f"📍 **Поточна локація:**\n{settings.location_name or 'Невідома назва'}\n🌐 {settings.latitude:.4f}, {settings.longitude:.4f}\n🕐 Часовий пояс: {settings.timezone}"
    text = f"🌍 **Налаштування локації**\n\n{location_info}"
    try:
        await call.message.edit_text(
            text,
            reply_markup=WeatherKeyboards.location_settings(),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise

async def units_settings_callback(call: CallbackQuery):
    """Налаштування одиниць виміру"""
    await call.answer()
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    current_units = {
        'temperature_unit': settings.temperature_unit,
        'wind_speed_unit': settings.wind_speed_unit,
        'precipitation_unit': settings.precipitation_unit,
        'timeformat': settings.timeformat
    }
    try:
        await call.message.edit_text(
            "📏 **Налаштування одиниць виміру**\n\nОбери параметр для зміни:",
            reply_markup=WeatherKeyboards.units_settings(current_units),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise

async def display_settings_callback(call: CallbackQuery):
    """Налаштування відображення"""
    await call.answer()
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    display_settings = {
        'show_temperature': settings.show_temperature,
        'show_feels_like': settings.show_feels_like,
        'show_humidity': settings.show_humidity,
        'show_pressure': settings.show_pressure,
        'show_wind': settings.show_wind,
        'show_precipitation': settings.show_precipitation,
        'show_precipitation_probability': settings.show_precipitation_probability,
        'show_cloud_cover': settings.show_cloud_cover,
        'show_uv_index': settings.show_uv_index,
        'show_visibility': settings.show_visibility,
        'show_daily_temperature': settings.show_daily_temperature,
        'show_sunrise_sunset': settings.show_sunrise_sunset,
        'show_daylight_duration': settings.show_daylight_duration,
    }
    try:
        await call.message.edit_text(
            "📊 **Налаштування відображення**\n\nВибери, що показувати в прогнозі погоди:",
            reply_markup=WeatherKeyboards.display_settings(display_settings),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "message is not modified" in str(e):
            pass
        else:
            raise

# ===== ОБРОБНИКИ ПЕРЕМИКАННЯ НАЛАШТУВАНЬ =====

async def toggle_setting_callback(call: CallbackQuery):
    logging.info(f"Toggle callback: {call.data} from user {call.from_user.id}")
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
        logging.info(f"Toggled {setting_name} for user {call.from_user.id}: new value {new_value}")
        
    except ValueError as e:
        await call.answer(f"Помилка: {str(e)}", show_alert=True)
        logging.error(f"Error toggling {setting_name} for user {call.from_user.id}: {str(e)}")

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
        logging.error(f"Помилка встановлення {unit_type}={unit_value} для {call.from_user.id}: {str(e)}")

# ===== ДОПОМІЖНІ ФУНКЦІЇ =====

async def format_weather_response(weather_data: dict, location_data: dict, api_params: dict) -> str:
    """Форматування відповіді з погодою"""
    city = location_data.get("city", "")
    state = location_data.get("state", "")
    country = location_data.get("country", "")
    
    # Заголовок з локацією
    location_str = f"🌍 **{city}"
    if state:
        location_str += f", {state}"
    if country:
        location_str += f", {country}"
    location_str += "**\n\n"
    
    response = location_str
    
    # Поточна погода
    current = weather_data.get("current", {})
    if current:
        temp_unit = "°C" if api_params.get('temperature_unit') == 'celsius' else "°F"
        wind_unit = api_params.get('wind_speed_unit', 'kmh')
        
        response += "☀️ **Поточна погода:**\n"
        response += f"🌡️ Температура: {current.get('temperature_2m', 'N/A')}{temp_unit}\n"
        
        if 'apparent_temperature' in current:
            response += f"🌡️ Відчувається: {current['apparent_temperature']}{temp_unit}\n"
        
        if 'relative_humidity_2m' in current:
            response += f"💧 Вологість: {current['relative_humidity_2m']}%\n"
        
        if 'wind_speed_10m' in current:
            response += f"💨 Вітер: {current['wind_speed_10m']} {wind_unit}\n"
        
        if 'weather_code' in current:
            weather_desc = get_weather_description(current['weather_code'])
            response += f"☁️ Опис: {weather_desc}\n"
        
        response += "\n"
    
    # Денний прогноз
    daily = weather_data.get("daily", {})
    if daily and 'time' in daily:
        response += "📅 **Прогноз на найближчі дні:**\n"
        
        # Визначаємо кількість днів для прогнозу
        forecast_days = api_params.get('forecast_days')
        try:
            forecast_days = int(forecast_days)
        except (TypeError, ValueError):
            forecast_days = len(daily['time'])
        times = daily['time'][:forecast_days]
        temp_max = daily.get('temperature_2m_max', [])
        temp_min = daily.get('temperature_2m_min', [])
        weather_codes = daily.get('weather_code', [])

        temp_unit = "°C" if api_params.get('temperature_unit') == 'celsius' else "°F"

        for i in range(len(times)):
            date_str = times[i]
            max_temp = temp_max[i] if i < len(temp_max) else "N/A"
            min_temp = temp_min[i] if i < len(temp_min) else "N/A"
            weather_code = weather_codes[i] if i < len(weather_codes) else 0

            # Форматуємо дату
            try:
                from datetime import datetime
                date_obj = datetime.fromisoformat(date_str)
                day_name = date_obj.strftime("%A")
                day_names = {
                    'Monday': 'Понеділок', 'Tuesday': 'Вівторок', 'Wednesday': 'Середа',
                    'Thursday': 'Четвер', 'Friday': 'П\'ятниця', 'Saturday': 'Субота', 'Sunday': 'Неділя'
                }
                day_name = day_names.get(day_name, day_name)
                date_formatted = f"{day_name}, {date_obj.strftime('%d.%m')}"
            except:
                date_formatted = date_str

            weather_desc = get_weather_description(weather_code)
            response += f"• {date_formatted}: {max_temp}°/{min_temp}° {weather_desc}\n"
    
    return response

# In handlers.py, add after precipitation_unit_callback

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
        logging.error(f"Помилка встановлення timeformat для {call.from_user.id}: {str(e)}")

def get_weather_description(weather_code: int) -> str:
    """Отримати опис погоди за WMO кодом"""
    descriptions = {
        0: "☀️ Ясно",
        1: "🌤️ Переважно ясно", 2: "⛅ Частково хмарно", 3: "☁️ Хмарно",
        45: "🌫️ Туман", 48: "🌫️ Іней",
        51: "🌦️ Легкий дощ", 53: "🌦️ Помірний дощ", 55: "🌧️ Сильний дощ",
        56: "🌨️ Легкий сніг з дощем", 57: "🌨️ Сніг з дощем",
        61: "🌦️ Легкий дощ", 63: "🌦️ Дощ", 65: "🌧️ Сильний дощ",
        66: "🌨️ Дощ зі снігом", 67: "🌨️ Сильний дощ зі снігом",
        71: "❄️ Легкий сніг", 73: "❄️ Сніг", 75: "❄️ Сильний сніг",
        77: "❄️ Снігопад",
        80: "🌦️ Зливи", 81: "⛈️ Грози", 82: "⛈️ Сильні грози",
        85: "❄️ Снігопад", 86: "❄️ Сильний снігопад",
        95: "⛈️ Гроза", 96: "⛈️ Гроза з градом", 99: "⛈️ Сильна гроза"
    }
    return descriptions.get(weather_code, f"Код {weather_code}")

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
            # Тимчасово перезаписуємо кількість днів для прогнозу на сьогодні
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
        from aiogram.exceptions import TelegramBadRequest
        if isinstance(e, TelegramBadRequest) and "message is not modified" in str(e):
            pass
        else:
            await call.message.edit_text(
                f"❌ Помилка отримання прогнозу: {str(e)}",
                reply_markup=WeatherKeyboards.main_menu()
            )
            logging.error(f"Помилка отримання прогнозу на сьогодні для {call.from_user.id}: {str(e)}")

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

        # Додаємо current і daily параметри, обмежуємо daily до 3 днів
        api_params['current'] = 'temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m'
        api_params['forecast_days'] = 3

        weather_data = await get_weather(settings.latitude, settings.longitude, api_params)

        location_data = {
            "city": settings.location_name or "Невідома локація",
            "lat": settings.latitude,
            "lon": settings.longitude
        }

        # Форматуємо відповідь, але daily буде тільки 3 дні
        response = await format_weather_response(weather_data, location_data, api_params)

        await call.message.edit_text(
            response,
            reply_markup=WeatherKeyboards.weather_type_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        from aiogram.exceptions import TelegramBadRequest
        if isinstance(e, TelegramBadRequest) and "message is not modified" in str(e):
            pass
        else:
            await call.message.edit_text(
                f"❌ Помилка отримання погоди: {str(e)}",
                reply_markup=WeatherKeyboards.main_menu()
            )

# ===== РЕЄСТРАЦІЯ ОБРОБНИКІВ =====

def register_handlers(dp: Dispatcher):
    # === CALLBACK ОБРОБНИКИ РЕДАГУВАННЯ СПОВІЩЕНЬ ===
    dp.callback_query.register(edit_notifications_display_callback, lambda c: c.data == "notifications:edit_display")
    """Реєстрація всіх обробників"""
    
    # Команди
    dp.message.register(start_handler, Command("start"))
    dp.message.register(help_handler, Command("help"))
    dp.message.register(settings_handler, Command("settings"))
    
    # Текстові повідомлення (пошук погоди)
    dp.message.register(text_handler)
    
    # === CALLBACK ОБРОБНИКИ МЕНЮ ===
    dp.callback_query.register(main_menu_callback, lambda c: c.data == "menu:main")
    dp.callback_query.register(settings_menu_callback, lambda c: c.data == "menu:settings")
    
    # === CALLBACK ОБРОБНИКИ НАЛАШТУВАНЬ ===
    dp.callback_query.register(location_settings_callback, lambda c: c.data == "settings:location")
    dp.callback_query.register(units_settings_callback, lambda c: c.data == "settings:units")
    dp.callback_query.register(display_settings_callback, lambda c: c.data == "settings:display")
    
    # === CALLBACK ОБРОБНИКИ ПЕРЕМИКАННЯ ===
    dp.callback_query.register(toggle_setting_callback, lambda c: c.data.startswith("toggle:"))
    dp.callback_query.register(set_unit_callback, lambda c: c.data.startswith("set_unit:"))
    
    # === CALLBACK ОБРОБНИКИ ПОГОДИ ===
    dp.callback_query.register(current_weather_callback, lambda c: c.data == "weather:current")
    dp.callback_query.register(weekly_weather_callback, lambda c: c.data == "weather:weekly")
    dp.callback_query.register(hourly_weather_callback, lambda c: c.data == "weather:hourly")
    dp.callback_query.register(today_weather_callback, lambda c: c.data == "weather:today")
    # ===== ДОДАТКОВИЙ CALLBACK: ПРОГНОЗ НА СЬОГОДНІ =====
    dp.callback_query.register(three_days_weather_callback, lambda c: c.data == "weather:3days")
    # ===== ДОДАТКОВИЙ CALLBACK: ПРОГНОЗ НА 3 ДНІ =====

    # === CALLBACK ОБРОБНИКИ ФОРМАТУ ЧАСУ ===
    dp.callback_query.register(timeformat_unit_callback, lambda call: call.data == "units:timeformat")
    dp.callback_query.register(set_timeformat_callback, lambda call: call.data.startswith("set_unit:timeformat:"))

    
    # === CALLBACK ОБРОБНИКИ ОДИНИЦЬ ===
    dp.callback_query.register(temperature_unit_callback, lambda c: c.data == "units:temperature")
    dp.callback_query.register(wind_speed_unit_callback, lambda c: c.data == "units:wind_speed")
    dp.callback_query.register(precipitation_unit_callback, lambda c: c.data == "units:precipitation")
    
    # === CALLBACK ОБРОБНИКИ ЛОКАЦІЇ ===
    dp.callback_query.register(set_location_callback, lambda c: c.data == "location:set")
    dp.callback_query.register(timezone_callback, lambda c: c.data == "location:timezone")
    dp.callback_query.register(set_timezone_callback, lambda c: c.data.startswith("set_timezone:"))
    
    # === CALLBACK ОБРОБНИКИ ПРОГНОЗУ ===
    dp.callback_query.register(forecast_settings_callback, lambda c: c.data == "settings:forecast")
    dp.callback_query.register(forecast_days_callback, lambda c: c.data == "forecast:days")
    dp.callback_query.register(set_forecast_days_callback, lambda c: c.data.startswith("set_forecast:days:"))
        # === CALLBACK ОБРОБНИКИ МИНУЛИХ ДНІВ ===
    dp.callback_query.register(forecast_past_days_callback, lambda c: c.data == "forecast:past_days")
    dp.callback_query.register(set_forecast_past_days_callback, lambda c: c.data.startswith("set_forecast:past_days:"))
    
    # === CALLBACK ОБРОБНИКИ СПОВІЩЕНЬ ===
    dp.callback_query.register(notifications_settings_callback, lambda c: c.data == "settings:notifications")
    dp.callback_query.register(notifications_time_callback, lambda c: c.data == "notifications:time")
    
    # === CALLBACK ОБРОБНИК SUMMARY ===
    dp.callback_query.register(settings_summary_callback, lambda c: c.data == "settings:summary")
    
    # === FALLBACK для невідомих callback ===
    dp.callback_query.register(unknown_callback)

# ===== ДОДАТКОВІ CALLBACK ОБРОБНИКИ =====

async def edit_notifications_display_callback(call: CallbackQuery):
    """Відкрити меню налаштування відображення для сповіщень"""
    await call.answer()
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    display_settings = {
        'show_temperature': settings.show_temperature,
        'show_feels_like': settings.show_feels_like,
        'show_humidity': settings.show_humidity,
        'show_pressure': settings.show_pressure,
        'show_wind': settings.show_wind,
        'show_precipitation': settings.show_precipitation,
        'show_precipitation_probability': settings.show_precipitation_probability,
        'show_cloud_cover': settings.show_cloud_cover,
        'show_uv_index': settings.show_uv_index,
        'show_visibility': settings.show_visibility,
        'show_daily_temperature': settings.show_daily_temperature,
        'show_sunrise_sunset': settings.show_sunrise_sunset,
        'show_daylight_duration': settings.show_daylight_duration,
    }
    await call.message.edit_text(
        "📊 **Налаштування відображення для сповіщень**\n\nВибери, що показувати в повідомленнях:",
        reply_markup=WeatherKeyboards.display_settings(display_settings),
        parse_mode="Markdown"
    )

async def forecast_past_days_callback(call: CallbackQuery):
    """Вибір кількості минулих днів"""
    await call.answer()
    async for session in get_session():
        settings = await get_user_weather_settings(session, call.from_user.id)
    await call.message.edit_text(
        "🕰️ **Оберіть кількість минулих днів:**\n\nМаксимум 7 днів згідно з обмеженнями Open-Meteo API.",
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

        # Додаємо current параметри для поточної погоди
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
        from aiogram.exceptions import TelegramBadRequest
        if isinstance(e, TelegramBadRequest) and "message is not modified" in str(e):
            # Тихо ігноруємо, не показуємо користувачу і не логуємо
            pass
        else:
            await call.message.edit_text(
                f"❌ Помилка отримання погоди: {str(e)}",
                reply_markup=WeatherKeyboards.main_menu()
            )
            logging.error(f"Помилка отримання поточної погоди для {call.from_user.id}: {str(e)}")

async def weekly_weather_callback(call: CallbackQuery):
    """Показати тижневий прогноз"""
    await call.answer("Отримуємо тижневий прогноз...")
    await current_weather_callback(call)  # Використовуємо ту ж логіку

async def hourly_weather_callback(call: CallbackQuery):
    """Показати почасовий прогноз"""
    await call.answer("Почасовий прогноз поки в розробці", show_alert=True)

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

async def set_location_callback(call: CallbackQuery, state: FSMContext):
    """Початок процесу встановлення локації"""
    await call.answer()
    
    await call.message.edit_text(
        "📍 **Встановлення локації**\n\n"
        "Надішли назву міста або координати в форматі:\n"
        "• Київ\n"
        "• Mukachevo, Ukraine\n"
        "• 48.9166, 24.7111\n\n"
        "Або надішли геолокацію через вкладення.",
        reply_markup=WeatherKeyboards.location_input_help(),
        parse_mode="Markdown"
    )
    
    await state.set_state(SettingsStates.waiting_location)

async def timezone_callback(call: CallbackQuery):
    """Вибір часового поясу"""
    await call.answer()
    
    await call.message.edit_text(
        "🕐 **Оберіть часовий пояс:**\n\n"
        "Рекомендується використовувати автоматичний вибір.",
        reply_markup=WeatherKeyboards.timezone_selector(),
        parse_mode="Markdown"
    )

async def set_timezone_callback(call: CallbackQuery):
    """Встановлення часового поясу"""
    await call.answer()
    
    _, timezone = call.data.split(":", 1)
    
    try:
        async for session in get_session():
            settings = await get_user_weather_settings(session, call.from_user.id)
            settings.timezone = timezone
            settings.updated_at = datetime.now()
            await session.commit()
        
        await call.answer(f"Часовий пояс встановлено: {timezone}", show_alert=True)
        await location_settings_callback(call)
        
    except Exception as e:
        await call.answer(f"Помилка: {str(e)}", show_alert=True)
        logging.error(f"Помилка встановлення timezone для {call.from_user.id}: {str(e)}")

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
    await call.message.edit_text(
        "⏰ **Оберіть час для щоденних сповіщень:**\n\nНапишіть час у форматі HH:MM (наприклад, 08:30)",
        reply_markup=WeatherKeyboards.back_button("settings:notifications"),
        parse_mode="Markdown"
    )

async def settings_summary_callback(call: CallbackQuery):
    """Показати детальний опис налаштувань"""
    await call.answer()
    
    async for session in get_session():
        summary = await get_user_settings_summary(session, call.from_user.id)
    
    await call.message.edit_text(
        summary,
        reply_markup=WeatherKeyboards.back_button("menu:settings"),
        parse_mode="Markdown"
    )

async def unknown_callback(call: CallbackQuery):
    """Обробка невідомих callback"""
    await call.answer("Невідома команда", show_alert=True)
    logging.warning(f"Невідомий callback від {call.from_user.id}: {call.data}")

# ===== ОБРОБНИКИ FSM СТАНІВ =====

async def location_input_handler(message: Message, state: FSMContext):
    """Обробка введення локації"""
    place = message.text.strip()
    
    try:
        # Геокодування
        location_data = await geocode_place(place)
        
        # Збереження в БД
        async for session in get_session():
            await update_user_location(
                session,
                message.from_user.id,
                location_data["lat"],
                location_data["lon"],
                location_name=f"{location_data.get('city', '')}, {location_data.get('country', '')}".strip(", "),
                timezone='auto'
            )
        
        await message.reply(
            f"✅ **Локація встановлена!**\n\n"
            f"📍 {location_data.get('city', 'Невідоме місто')}, {location_data.get('country', '')}\n"
            f"🌐 {location_data['lat']:.4f}, {location_data['lon']:.4f}",
            reply_markup=WeatherKeyboards.main_menu(),
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except ValueError as e:
        await message.reply(f"❌ {str(e)}\n\nСпробуй ще раз:")
        # Не очищаємо стан, щоб користувач міг спробувати знову

# Реєстрація FSM обробників
def register_fsm_handlers(dp: Dispatcher):
    """Реєстрація FSM обробників"""
    dp.message.register(location_input_handler, SettingsStates.waiting_location)