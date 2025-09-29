

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Dict, Any

class WeatherKeyboards:
    @staticmethod
    def forecast_past_days_selector(current: int = 0) -> InlineKeyboardMarkup:
        keyboard = []
        days_options = [0, 1, 2, 3, 5, 7]
        for days in days_options:
            emoji = "✅" if current == days else "⚪"
            text = f"{emoji} {days} {'день' if days == 1 else ('дні' if 1 < days < 5 else 'днів' if days > 0 else 'немає')}"
            keyboard.append([InlineKeyboardButton(
                text=text,
                callback_data=f"set_forecast:past_days:{days}"
            )])
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:forecast")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="🌦️ Поточна погода", callback_data="weather:current")],
            [
                InlineKeyboardButton(text="📅 Прогноз на тиждень", callback_data="weather:weekly"),
                InlineKeyboardButton(text="⏰ Почасовий прогноз", callback_data="weather:hourly")
            ],
            [
                InlineKeyboardButton(text="🔧 Налаштування", callback_data="menu:settings"),
                InlineKeyboardButton(text="🏙️ Змінити місто", callback_data="action:change_location")
            ],
            [InlineKeyboardButton(text="ℹ️ Допомога", callback_data="action:help")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="📍 Локація та часовий пояс", callback_data="settings:location")],
            [InlineKeyboardButton(text="📏 Одиниці виміру", callback_data="settings:units")],
            [InlineKeyboardButton(text="📊 Що відображати", callback_data="settings:display")],
            [InlineKeyboardButton(text="📅 Налаштування прогнозу", callback_data="settings:forecast")],
            [InlineKeyboardButton(text="🔔 Сповіщення", callback_data="settings:notifications")],
            [InlineKeyboardButton(text="📋 Мої налаштування", callback_data="settings:summary")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def location_settings() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="🌍 Встановити локацію", callback_data="location:set")],
            [InlineKeyboardButton(text="🕐 Часовий пояс", callback_data="location:timezone")],
            [InlineKeyboardButton(text="⛰️ Висота над рівнем моря", callback_data="location:elevation")],
            [InlineKeyboardButton(text="⬅️ Назад до налаштувань", callback_data="menu:settings")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def units_settings(current_units: Dict[str, str] = None) -> InlineKeyboardMarkup:
        if not current_units:
            current_units = {
                'temperature_unit': 'celsius',
                'wind_speed_unit': 'kmh',
                'precipitation_unit': 'mm',
                'timeformat': 'iso8601'
            }
        
        temp_emoji = "🌡️C" if current_units['temperature_unit'] == 'celsius' else "🌡️F"
        wind_units_map = {'kmh': 'км/год', 'ms': 'м/с', 'mph': 'миль/год', 'kn': 'вузли'}
        wind_emoji = f"💨 {wind_units_map.get(current_units['wind_speed_unit'], current_units['wind_speed_unit'])}"
        precip_emoji = "🌧️мм" if current_units['precipitation_unit'] == 'mm' else "🌧️дюйми"
        
        keyboard = [
            [InlineKeyboardButton(text=f"{temp_emoji} Температура", callback_data="units:temperature")],
            [InlineKeyboardButton(text=f"{wind_emoji} Швидкість вітру", callback_data="units:wind_speed")],
            [InlineKeyboardButton(text=f"{precip_emoji} Опади", callback_data="units:precipitation")],
            [InlineKeyboardButton(text="🕒 Формат часу", callback_data="units:timeformat")],
            [InlineKeyboardButton(text="⬅️ Назад до налаштувань", callback_data="menu:settings")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def temperature_unit_selector(current: str = 'celsius') -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(
                text=f"{'✅' if current == 'celsius' else '⚪'} Цельсій (°C)", 
                callback_data="set_unit:temperature_unit:celsius"
            )],
            [InlineKeyboardButton(
                text=f"{'✅' if current == 'fahrenheit' else '⚪'} Фаренгейт (°F)", 
                callback_data="set_unit:temperature_unit:fahrenheit"
            )],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:units")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def wind_speed_unit_selector(current: str = 'kmh') -> InlineKeyboardMarkup:
        options = {
            'kmh': 'Кілометри/година (км/год)',
            'ms': 'Метри/секунда (м/с)',
            'mph': 'Милі/година (mph)',
            'kn': 'Вузли (kn)'
        }
        
        keyboard = []
        for unit, label in options.items():
            emoji = "✅" if current == unit else "⚪"
            keyboard.append([InlineKeyboardButton(
                text=f"{emoji} {label}", 
                callback_data=f"set_unit:wind_speed_unit:{unit}"
            )])
        
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:units")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    

    @staticmethod
    def timeformat_unit_selector(current: str = 'iso8601') -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(
                text=f"{'✅' if current == 'iso8601' else '⚪'} ISO8601 (2025-09-28T16:55:01Z)", 
                callback_data="set_unit:timeformat:iso8601"
            )],
            [InlineKeyboardButton(
                text=f"{'✅' if current == 'unixtime' else '⚪'} Unix Timestamp (1625097600)", 
                callback_data="set_unit:timeformat:unixtime"
            )],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:units")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    @staticmethod
    def display_settings(settings: Dict[str, bool] = None) -> InlineKeyboardMarkup:
        if not settings:
            settings = {}
        
        def get_emoji(key: str, default: bool = True) -> str:
            return "✅" if settings.get(key, default) else "❌"
        
        keyboard = [
            [InlineKeyboardButton(text="📊 Що показувати в поточній погоді:", callback_data="noop")],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_temperature')} Температура", 
                callback_data="toggle:show_temperature"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_feels_like')} Відчувається як", 
                callback_data="toggle:show_feels_like"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_humidity')} Вологість", 
                callback_data="toggle:show_humidity"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_pressure', False)} Тиск", 
                callback_data="toggle:show_pressure"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_wind')} Вітер", 
                callback_data="toggle:show_wind"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_precipitation')} Опади", 
                callback_data="toggle:show_precipitation"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_precipitation_probability')} Ймовірність опадів", 
                callback_data="toggle:show_precipitation_probability"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_cloud_cover', False)} Хмарність", 
                callback_data="toggle:show_cloud_cover"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_uv_index')} УФ-індекс", 
                callback_data="toggle:show_uv_index"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_visibility', False)} Видимість", 
                callback_data="toggle:show_visibility"
            )],
            [InlineKeyboardButton(text="📅 Денний прогноз:", callback_data="noop")],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_daily_temperature')} Макс/мін температура", 
                callback_data="toggle:show_daily_temperature"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_sunrise_sunset')} Схід/захід сонця", 
                callback_data="toggle:show_sunrise_sunset"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_daylight_duration', False)} Тривалість дня", 
                callback_data="toggle:show_daylight_duration"
            )],
            [InlineKeyboardButton(text="⬅️ Назад до налаштувань", callback_data="menu:settings")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def forecast_settings(settings: Dict[str, Any] = None) -> InlineKeyboardMarkup:
        if not settings:
            settings = {'forecast_days': 7, 'past_days': 0}
        
        keyboard = [
            [InlineKeyboardButton(
                text=f"📅 Днів прогнозу: {settings.get('forecast_days', 7)}", 
                callback_data="forecast:days"
            )],
            [InlineKeyboardButton(
                text=f"🕰️ Минулих днів: {settings.get('past_days', 0)}", 
                callback_data="forecast:past_days"
            )],
            [InlineKeyboardButton(text="⬅️ Назад до налаштувань", callback_data="menu:settings")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def forecast_days_selector(current: int = 7) -> InlineKeyboardMarkup:
        keyboard = []
        days_options = [1, 3, 5, 7, 10, 14, 16]
        
        for days in days_options:
            emoji = "✅" if current == days else "⚪"
            text = f"{emoji} {days} {'день' if days == 1 else ('дні' if days < 5 else 'днів')}"
            keyboard.append([InlineKeyboardButton(
                text=text, 
                callback_data=f"set_forecast:days:{days}"
            )])
        
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:forecast")])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def notifications_settings(settings: Dict[str, Any] = None) -> InlineKeyboardMarkup:
        if not settings:
            settings = {'notification_enabled': False, 'notification_time': None}

        enabled = settings.get('notification_enabled', False)
        time_text = settings.get('notification_time', 'Не встановлено')

        keyboard = [
            [InlineKeyboardButton(
                text=f"{'✅' if enabled else '❌'} Щоденні сповіщення",
                callback_data="toggle:notification_enabled"
            )],
            [InlineKeyboardButton(
                text=f"⏰ Час сповіщень: {time_text}",
                callback_data="notifications:time"
            )] if enabled else [],
            [InlineKeyboardButton(
                text="✏️ Редагувати сповіщення",
                callback_data="notifications:edit_display"
            )],
            [InlineKeyboardButton(text="⬅️ Назад до налаштувань", callback_data="menu:settings")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=[row for row in keyboard if row])

    @staticmethod
    def timezone_selector() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="🌐 Автоматично", callback_data="set_timezone:auto")],
            [InlineKeyboardButton(text="🇺🇦 Київ (Europe/Kyiv)", callback_data="set_timezone:Europe/Kyiv")],
            [InlineKeyboardButton(text="🌍 GMT", callback_data="set_timezone:GMT")],
            [InlineKeyboardButton(text="🇺🇸 Нью-Йорк", callback_data="set_timezone:America/New_York")],
            [InlineKeyboardButton(text="🇬🇧 Лондон", callback_data="set_timezone:Europe/London")],
            [InlineKeyboardButton(text="🇩🇪 Берлін", callback_data="set_timezone:Europe/Berlin")],
            [InlineKeyboardButton(text="🇯🇵 Токіо", callback_data="set_timezone:Asia/Tokyo")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:location")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def weather_type_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="☀️ Поточна погода", callback_data="weather:current")],
            [InlineKeyboardButton(text="📅 На сьогодні", callback_data="weather:today")],
            [InlineKeyboardButton(text="🗓️ На 3 дні", callback_data="weather:3days")],
            [InlineKeyboardButton(text="📆 Тижневий прогноз", callback_data="weather:weekly")],
            [InlineKeyboardButton(text="⏰ Почасовий прогноз", callback_data="weather:hourly")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def confirmation_dialog(action: str, item: str) -> InlineKeyboardMarkup:
        keyboard = [
            [
                InlineKeyboardButton(text="✅ Так", callback_data=f"confirm:{action}:{item}"),
                InlineKeyboardButton(text="❌ Ні", callback_data="menu:settings")
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def back_button(callback_data: str = "menu:main") -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_data)
        ]])

    @staticmethod
    def location_input_help() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(text="📍 Надіслати геолокацію", callback_data="location:share")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:location")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def advanced_display_settings(settings: Dict[str, bool] = None) -> InlineKeyboardMarkup:
        if not settings:
            settings = {}
        
        def get_emoji(key: str, default: bool = False) -> str:
            return "✅" if settings.get(key, default) else "❌"
        
        keyboard = [
            [InlineKeyboardButton(text="🔬 Додаткові параметри:", callback_data="noop")],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_dew_point')} Точка роси", 
                callback_data="toggle:show_dew_point"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_solar_radiation')} Сонячна радіація", 
                callback_data="toggle:show_solar_radiation"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_sunshine_duration')} Тривалість сонячного світла", 
                callback_data="toggle:show_sunshine_duration"
            )],
            [InlineKeyboardButton(
                text=f"{get_emoji('show_current_weather')} Поточні умови", 
                callback_data="toggle:show_current_weather"
            )],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:display")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


class InlineKeyboards(WeatherKeyboards):
    pass
