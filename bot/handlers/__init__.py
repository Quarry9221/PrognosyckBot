from bot.handlers.commands import start_handler, help_handler, settings_handler
from bot.handlers.text import text_handler
from bot.handlers.menu_callbacks import help_callback_handler, main_menu_callback, settings_menu_callback
from bot.handlers.settings_callbacks import edit_notifications_display_callback, location_settings_callback, units_settings_callback, display_settings_callback
from bot.handlers.weather_callbacks import current_weather_callback, weekly_weather_callback, hourly_weather_callback, today_weather_callback, three_days_weather_callback
from bot.handlers.units_callbacks import toggle_setting_callback, set_unit_callback, temperature_unit_callback, wind_speed_unit_callback, precipitation_unit_callback, timeformat_unit_callback, set_timeformat_callback
from bot.handlers.location_callbacks import set_location_callback, timezone_callback, set_timezone_callback
from bot.handlers.forecast_callbacks import forecast_settings_callback, forecast_days_callback, set_forecast_days_callback, forecast_past_days_callback, set_forecast_past_days_callback
from bot.handlers.notifications_callbacks import notifications_settings_callback, notifications_time_callback
from bot.handlers.fallback import unknown_callback
from aiogram import Dispatcher
from aiogram.filters import Command

def register_handlers(dp: Dispatcher):
    # Команди

    dp.callback_query.register(edit_notifications_display_callback, lambda c: c.data == "notifications:edit_display")
    dp.message.register(start_handler, Command("start"))
    dp.message.register(help_handler, Command("help"))
    dp.message.register(settings_handler, Command("settings"))
    
    # Текстові повідомлення
    dp.message.register(text_handler)
    
    # Callback
    dp.callback_query.register(main_menu_callback, lambda c: c.data == "menu:main")
    dp.callback_query.register(settings_menu_callback, lambda c: c.data == "menu:settings")
    dp.callback_query.register(help_callback_handler, lambda c: c.data == "action:help")

    # Settings
    dp.callback_query.register(location_settings_callback, lambda c: c.data == "settings:location")
    dp.callback_query.register(units_settings_callback, lambda c: c.data == "settings:units")
    dp.callback_query.register(display_settings_callback, lambda c: c.data == "settings:display")

    # Weather
    dp.callback_query.register(current_weather_callback, lambda c: c.data == "weather:current")
    dp.callback_query.register(weekly_weather_callback, lambda c: c.data == "weather:weekly")
    dp.callback_query.register(hourly_weather_callback, lambda c: c.data == "weather:hourly")
    dp.callback_query.register(today_weather_callback, lambda c: c.data == "weather:today")
    dp.callback_query.register(three_days_weather_callback, lambda c: c.data == "weather:3days")
    
    # Units callbacks
    dp.callback_query.register(toggle_setting_callback, lambda c: c.data.startswith("toggle:"))
    dp.callback_query.register(set_unit_callback, lambda c: c.data.startswith("set_unit:"))
    
    # Specific unit callbacks
    dp.callback_query.register(temperature_unit_callback, lambda c: c.data == "units:temperature")
    dp.callback_query.register(wind_speed_unit_callback, lambda c: c.data == "units:wind_speed")
    dp.callback_query.register(precipitation_unit_callback, lambda c: c.data == "units:precipitation")

    # Timeformat callbacks
    dp.callback_query.register(timeformat_unit_callback, lambda call: call.data == "units:timeformat")
    dp.callback_query.register(set_timeformat_callback, lambda call: call.data.startswith("set_unit:timeformat:"))
    
    # Location callbacks
    dp.callback_query.register(set_location_callback, lambda c: c.data == "location:set")
    dp.callback_query.register(timezone_callback, lambda c: c.data == "location:timezone")
    dp.callback_query.register(set_timezone_callback, lambda c: c.data.startswith("set_timezone:"))
    
    # Forecast callbacks
    dp.callback_query.register(forecast_settings_callback, lambda c: c.data == "settings:forecast")
    dp.callback_query.register(forecast_days_callback, lambda c: c.data == "forecast:days")
    dp.callback_query.register(set_forecast_days_callback, lambda c: c.data.startswith("set_forecast:days:"))
    dp.callback_query.register(forecast_past_days_callback, lambda c: c.data == "forecast:past_days")
    dp.callback_query.register(set_forecast_past_days_callback, lambda c: c.data.startswith("set_forecast:past_days:"))
    
    # Notifications callbacks
    dp.callback_query.register(notifications_settings_callback, lambda c: c.data == "settings:notifications")
    dp.callback_query.register(notifications_time_callback, lambda c: c.data == "notifications:time")
    
    dp.callback_query.register(unknown_callback)
