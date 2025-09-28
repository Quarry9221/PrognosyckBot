# models.py - Покращена структура БД для погодного бота

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from datetime import datetime
import json

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    telegram_id = Column(BigInteger, primary_key=True, unique=True, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), default='uk')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class UserWeatherSettings(Base):
    __tablename__ = "user_weather_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Локація
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(255), nullable=True)
    elevation = Column(Float, nullable=True)
    timezone = Column(String(100), default='auto')
    
    # Одиниці виміру
    temperature_unit = Column(String(20), default='celsius')  # celsius, fahrenheit
    wind_speed_unit = Column(String(10), default='kmh')      # kmh, ms, mph, kn
    precipitation_unit = Column(String(10), default='mm')     # mm, inch
    timeformat = Column(String(20), default='iso8601')       # iso8601, unixtime
    
    # Налаштування прогнозу
    forecast_days = Column(Integer, default=7)  # 1-16
    past_days = Column(Integer, default=0)      # 0-92
    
    # Що показувати в hourly
    show_temperature = Column(Boolean, default=True)
    show_feels_like = Column(Boolean, default=True)
    show_humidity = Column(Boolean, default=True)
    show_pressure = Column(Boolean, default=False)
    show_wind = Column(Boolean, default=True)
    show_precipitation = Column(Boolean, default=True)
    show_precipitation_probability = Column(Boolean, default=True)
    show_cloud_cover = Column(Boolean, default=False)
    show_uv_index = Column(Boolean, default=True)
    show_visibility = Column(Boolean, default=False)
    show_dew_point = Column(Boolean, default=False)
    show_solar_radiation = Column(Boolean, default=False)
    
    # Що показувати в daily
    show_daily_temperature = Column(Boolean, default=True)
    show_daily_precipitation = Column(Boolean, default=True)
    show_daily_wind = Column(Boolean, default=True)
    show_sunrise_sunset = Column(Boolean, default=True)
    show_daylight_duration = Column(Boolean, default=False)
    show_sunshine_duration = Column(Boolean, default=False)
    show_daily_uv = Column(Boolean, default=True)
    
    # Що показувати в current
    show_current_weather = Column(Boolean, default=True)
    
    # Налаштування повідомлень
    notification_enabled = Column(Boolean, default=False)
    notification_time = Column(String(5), nullable=True)  # HH:MM format
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class UserMessage(Base):
    __tablename__ = "user_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=True)
    chat_id = Column(BigInteger, nullable=False)
    message_text = Column(Text, nullable=False)
    location_requested = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    weather_response = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)

class BotChat(Base):
    __tablename__ = "bot_chats"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, unique=True, index=True)
    chat_type = Column(String(50), nullable=False)  # private, group, supergroup, channel
    title = Column(String(255), nullable=True)
    added_at = Column(DateTime, default=datetime.now)
    last_activity = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

# Константи для валідації параметрів
HOURLY_PARAMETERS = [
    'temperature_2m', 'relative_humidity_2m', 'dew_point_2m', 'apparent_temperature',
    'pressure_msl', 'surface_pressure', 'cloud_cover', 'cloud_cover_low', 
    'cloud_cover_mid', 'cloud_cover_high', 'wind_speed_10m', 'wind_direction_10m',
    'wind_gusts_10m', 'shortwave_radiation', 'direct_radiation', 'diffuse_radiation',
    'vapour_pressure_deficit', 'precipitation', 'precipitation_probability',
    'rain', 'showers', 'snowfall', 'weather_code', 'snow_depth', 'visibility',
    'uv_index', 'is_day'
]

DAILY_PARAMETERS = [
    'weather_code', 'temperature_2m_max', 'temperature_2m_min', 'temperature_2m_mean',
    'apparent_temperature_max', 'apparent_temperature_min', 'apparent_temperature_mean',
    'sunrise', 'sunset', 'daylight_duration', 'sunshine_duration',
    'uv_index_max', 'uv_index_clear_sky_max', 'precipitation_sum', 'rain_sum',
    'showers_sum', 'snowfall_sum', 'precipitation_hours', 'precipitation_probability_max',
    'precipitation_probability_min', 'precipitation_probability_mean',
    'wind_speed_10m_max', 'wind_gusts_10m_max', 'wind_direction_10m_dominant',
    'shortwave_radiation_sum', 'et0_fao_evapotranspiration'
]

CURRENT_PARAMETERS = [
    'temperature_2m', 'relative_humidity_2m', 'apparent_temperature', 'is_day',
    'precipitation', 'rain', 'showers', 'snowfall', 'weather_code',
    'cloud_cover', 'pressure_msl', 'surface_pressure', 'wind_speed_10m',
    'wind_direction_10m', 'wind_gusts_10m'
]

TEMPERATURE_UNITS = ['celsius', 'fahrenheit']
WIND_SPEED_UNITS = ['kmh', 'ms', 'mph', 'kn']
PRECIPITATION_UNITS = ['mm', 'inch']
TIMEFORMAT_OPTIONS = ['iso8601', 'unixtime']