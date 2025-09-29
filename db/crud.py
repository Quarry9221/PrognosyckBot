from bot.logger_config import logger
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    User,
    UserWeatherSettings,
    UserMessage,
    BotChat,
    TEMPERATURE_UNITS,
    WIND_SPEED_UNITS,
    PRECIPITATION_UNITS,
)

# === КОРИСТУВАЧІ ===


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str = None,
    first_name: str = None,
    last_name: str = None,
    language_code: str = "uk",
) -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"Створено нового користувача: {telegram_id}")

        # Дефолтні налаштування погоди
        await create_default_weather_settings(session, telegram_id)
    else:
        updated = False
        for attr, value in [
            ("username", username),
            ("first_name", first_name),
            ("last_name", last_name),
            ("language_code", language_code),
        ]:
            if value and getattr(user, attr) != value:
                setattr(user, attr, value)
                updated = True
        if updated:
            user.updated_at = datetime.now()
            await session.commit()
            logger.info(f"Оновлено інформацію користувача: {telegram_id}")

    return user


async def create_default_weather_settings(
    session: AsyncSession, telegram_id: int
) -> UserWeatherSettings:
    settings = UserWeatherSettings(user_id=telegram_id)
    session.add(settings)
    await session.commit()
    await session.refresh(settings)
    logger.info(f"Створено дефолтні налаштування погоди для користувача {telegram_id}")
    return settings


# === НАЛАШТУВАННЯ ПОГОДИ ===


async def get_user_weather_settings(
    session: AsyncSession, telegram_id: int
) -> UserWeatherSettings:
    stmt = select(UserWeatherSettings).where(UserWeatherSettings.user_id == telegram_id)
    result = await session.execute(stmt)
    settings = result.scalar_one_or_none()

    if not settings:
        await get_or_create_user(session, telegram_id)
        settings = await create_default_weather_settings(session, telegram_id)

    return settings


async def update_user_location(
    session: AsyncSession,
    telegram_id: int,
    latitude: float,
    longitude: float,
    location_name: str = None,
    elevation: float = None,
    timezone: str = "auto",
) -> None:
    settings = await get_user_weather_settings(session, telegram_id)
    settings.latitude = latitude
    settings.longitude = longitude
    settings.location_name = location_name
    settings.elevation = elevation
    settings.timezone = timezone
    settings.updated_at = datetime.now()
    await session.commit()
    logger.info(
        f"Оновлено локацію для користувача {telegram_id}: {location_name} ({latitude}, {longitude})"
    )


async def update_user_units(
    session: AsyncSession,
    telegram_id: int,
    temperature_unit: str = None,
    wind_speed_unit: str = None,
    precipitation_unit: str = None,
    timeformat: str = None,
    past_days: int = None,
) -> None:
    settings = await get_user_weather_settings(session, telegram_id)
    if temperature_unit in TEMPERATURE_UNITS:
        settings.temperature_unit = temperature_unit
    if wind_speed_unit in WIND_SPEED_UNITS:
        settings.wind_speed_unit = wind_speed_unit
    if precipitation_unit in PRECIPITATION_UNITS:
        settings.precipitation_unit = precipitation_unit
    if timeformat in ["iso8601", "unixtime"]:
        settings.timeformat = timeformat
    if past_days is not None and 0 <= past_days <= 92:
        settings.past_days = past_days
    settings.updated_at = datetime.now()
    await session.commit()
    logger.info(f"Оновлено одиниці виміру та past_days для користувача {telegram_id}")


async def toggle_display_setting(
    session: AsyncSession, telegram_id: int, setting_name: str
) -> bool:
    settings = await get_user_weather_settings(session, telegram_id)
    if hasattr(settings, setting_name):
        current_value = getattr(settings, setting_name)
        new_value = not current_value
        setattr(settings, setting_name, new_value)
        settings.updated_at = datetime.now()
        await session.commit()
        logger.info(
            f"Перемкнуто {setting_name} для користувача {telegram_id}: {current_value} -> {new_value}"
        )
        return new_value
    else:
        raise ValueError(f"Невідомий параметр: {setting_name}")


async def update_forecast_settings(
    session: AsyncSession,
    telegram_id: int,
    forecast_days: int = None,
    past_days: int = None,
) -> None:
    settings = await get_user_weather_settings(session, telegram_id)
    if forecast_days is not None and 1 <= forecast_days <= 16:
        settings.forecast_days = forecast_days
    if past_days is not None and 0 <= past_days <= 92:
        settings.past_days = past_days
    settings.updated_at = datetime.now()
    await session.commit()
    logger.info(f"Оновлено налаштування прогнозу для користувача {telegram_id}")


async def update_notification_settings(
    session: AsyncSession,
    telegram_id: int,
    notification_enabled: bool = None,
    notification_time: str = None,
) -> None:
    settings = await get_user_weather_settings(session, telegram_id)
    if notification_enabled is not None:
        settings.notification_enabled = notification_enabled
    if notification_time is not None:
        try:
            datetime.strptime(notification_time, "%H:%M")
            settings.notification_time = notification_time
        except ValueError:
            raise ValueError("Час повинен бути у форматі HH:MM")
    settings.updated_at = datetime.now()
    await session.commit()
    logger.info(f"Оновлено налаштування сповіщень для користувача {telegram_id}")


# === API ПАРАМЕТРИ ===


async def get_api_parameters(session: AsyncSession, telegram_id: int) -> Dict[str, Any]:
    settings = await get_user_weather_settings(session, telegram_id)
    if not settings.latitude or not settings.longitude:
        raise ValueError(
            "Локація не встановлена. Спочатку вкажіть своє місцезнаходження."
        )

    params = {
        "latitude": settings.latitude,
        "longitude": settings.longitude,
        "timezone": settings.timezone,
        "temperature_unit": settings.temperature_unit,
        "wind_speed_unit": settings.wind_speed_unit,
        "precipitation_unit": settings.precipitation_unit,
        "timeformat": settings.timeformat,
        "forecast_days": settings.forecast_days,
        "past_days": settings.past_days,
    }
    if settings.elevation is not None:
        params["elevation"] = settings.elevation

    # Hourly
    hourly_params = []
    if settings.show_temperature:
        hourly_params.append("temperature_2m")
    if settings.show_feels_like:
        hourly_params.append("apparent_temperature")
    if settings.show_humidity:
        hourly_params.append("relative_humidity_2m")
    if settings.show_pressure:
        hourly_params.append("pressure_msl")
    if settings.show_wind:
        hourly_params.extend(["wind_speed_10m", "wind_direction_10m", "wind_gusts_10m"])
    if settings.show_precipitation:
        hourly_params.extend(["precipitation", "rain", "showers"])
    if settings.show_precipitation_probability:
        hourly_params.append("precipitation_probability")
    if settings.show_cloud_cover:
        hourly_params.append("cloud_cover")
    if settings.show_uv_index:
        hourly_params.append("uv_index")
    if settings.show_visibility:
        hourly_params.append("visibility")
    if settings.show_dew_point:
        hourly_params.append("dew_point_2m")
    if settings.show_solar_radiation:
        hourly_params.extend(
            ["shortwave_radiation", "direct_radiation", "diffuse_radiation"]
        )
    hourly_params.extend(["weather_code", "is_day"])
    if hourly_params:
        params["hourly"] = ",".join(list(set(hourly_params)))

    # Daily
    daily_params = ["weather_code"]
    if settings.show_daily_temperature:
        daily_params.extend(
            [
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
            ]
        )
    if settings.show_daily_precipitation:
        daily_params.extend(
            [
                "precipitation_sum",
                "precipitation_probability_max",
                "precipitation_hours",
            ]
        )
    if settings.show_daily_wind:
        daily_params.extend(
            ["wind_speed_10m_max", "wind_gusts_10m_max", "wind_direction_10m_dominant"]
        )
    if settings.show_sunrise_sunset:
        daily_params.extend(["sunrise", "sunset"])
    if settings.show_daylight_duration:
        daily_params.append("daylight_duration")
    if settings.show_sunshine_duration:
        daily_params.append("sunshine_duration")
    if settings.show_daily_uv:
        daily_params.extend(["uv_index_max", "uv_index_clear_sky_max"])
    if daily_params:
        params["daily"] = ",".join(list(set(daily_params)))

    # Current
    if settings.show_current_weather:
        current_params = [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "is_day",
            "precipitation",
            "weather_code",
            "cloud_cover",
            "pressure_msl",
            "wind_speed_10m",
            "wind_direction_10m",
        ]
        params["current"] = ",".join(current_params)

    return params


# === ПОВІДОМЛЕННЯ ===


async def save_user_message(
    session: AsyncSession,
    telegram_id: int,
    chat_id: int,
    message_text: str,
    location_requested: str = None,
    latitude: float = None,
    longitude: float = None,
    weather_response: str = None,
) -> None:
    message = UserMessage(
        user_id=telegram_id,
        chat_id=chat_id,
        message_text=message_text,
        location_requested=location_requested,
        latitude=latitude,
        longitude=longitude,
        weather_response=weather_response,
    )
    session.add(message)
    await session.commit()


# === ЧАТИ ===


async def normalize_chat_id(chat_id: int) -> int:
    return chat_id + 10**12 if chat_id < 0 else chat_id


async def save_chat_to_db(
    session: AsyncSession, chat_id: int, chat_type: str, title: str = None
) -> None:
    norm_id = await normalize_chat_id(chat_id)
    stmt = select(BotChat).where(BotChat.chat_id == norm_id)
    chat = (await session.execute(stmt)).scalar_one_or_none()
    if not chat:
        chat = BotChat(
            chat_id=norm_id, chat_type=chat_type, title=title, is_active=True
        )
        session.add(chat)
        logger.info(f"Збережено новий чат {norm_id} ({chat_type})")
    else:
        chat.last_activity = datetime.now()
        chat.is_active = True
        if title and chat.title != title:
            chat.title = title
        logger.debug(f"Оновлено активність чату {norm_id}")
    await session.commit()


async def track_chat_member_update(
    session: AsyncSession,
    chat_id: int,
    chat_type: str,
    new_status: str,
    old_status: str = None,
) -> None:
    norm_id = await normalize_chat_id(chat_id)
    chat = (
        await session.execute(select(BotChat).where(BotChat.chat_id == norm_id))
    ).scalar_one_or_none()

    if new_status == "member" and old_status != "member":
        if not chat:
            chat = BotChat(
                chat_id=norm_id,
                chat_type=chat_type,
                added_at=datetime.now(),
                last_activity=datetime.now(),
                is_active=True,
            )
            session.add(chat)
        else:
            chat.is_active = True
            chat.last_activity = datetime.now()
        await session.commit()
        logger.info(f"Бот додано або оновлено чат {norm_id} ({chat_type})")
    elif new_status in ["kicked", "left"] and chat:
        chat.is_active = False
        chat.last_activity = datetime.now()
        await session.commit()
        logger.warning(f"Бот видалено з чату {norm_id} ({chat_type})")


# === ЗВІТНІСТЬ ===


async def get_user_settings_summary(session: AsyncSession, telegram_id: int) -> str:
    settings = await get_user_weather_settings(session, telegram_id)
    location_info = "Не встановлена"
    if settings.latitude and settings.longitude:
        location_info = f"{settings.location_name or 'Невідома назва'} ({settings.latitude:.4f}, {settings.longitude:.4f})"

    summary = f"""Ваші налаштування:

Локація: {location_info}

Одиниці виміру:
• Температура: {settings.temperature_unit}
• Швидкість вітру: {settings.wind_speed_unit}
• Опади: {settings.precipitation_unit}

Прогноз: {settings.forecast_days} днів
Часовий пояс: {settings.timezone}

Сповіщення: {'Увімкнені' if settings.notification_enabled else 'Вимкнені'}
"""
    if settings.notification_enabled and settings.notification_time:
        summary += f"Час сповіщень: {settings.notification_time}\n"

    return summary


# === LEGACY ===


async def get_settings(session: AsyncSession, telegram_id: int) -> dict:
    settings = await get_user_weather_settings(session, telegram_id)
    return {
        "temperature_unit": settings.temperature_unit,
        "wind_speed_unit": settings.wind_speed_unit,
        "precipitation_unit": settings.precipitation_unit,
        "timezone": settings.timezone,
        "forecast_days": str(settings.forecast_days),
        "latitude": str(settings.latitude) if settings.latitude else None,
        "longitude": str(settings.longitude) if settings.longitude else None,
        "location_name": settings.location_name,
    }


async def update_setting(
    session: AsyncSession, telegram_id: int, key: str, value: str
) -> None:
    settings = await get_user_weather_settings(session, telegram_id)
    if key == "temperature_unit" and value in TEMPERATURE_UNITS:
        settings.temperature_unit = value
    elif key == "wind_speed_unit" and value in WIND_SPEED_UNITS:
        settings.wind_speed_unit = value
    elif key == "precipitation_unit" and value in PRECIPITATION_UNITS:
        settings.precipitation_unit = value
    elif key == "timezone":
        settings.timezone = value
    elif key == "forecast_days":
        days = int(value)
        if 1 <= days <= 16:
            settings.forecast_days = days
    else:
        raise ValueError(f"Невідомий або некоректний параметр: {key}={value}")
    settings.updated_at = datetime.now()
    await session.commit()


async def get_user_state(session, telegram_id: int) -> str | None:
    result = await session.execute(
        text("SELECT state FROM users WHERE telegram_id = :telegram_id"),
        {"telegram_id": telegram_id},
    )
    state = result.scalar_one_or_none()
    return state


async def set_user_state(session, telegram_id: int, state: str):
    query = text("UPDATE users SET state = :state WHERE telegram_id = :telegram_id")
    await session.execute(query, {"state": state, "telegram_id": telegram_id})
    await session.commit()


async def save_notification_time(session, user_id: int, time_str: str):
    """
    Зберігає час щоденних сповіщень для користувача у таблиці user_weather_settings.
    """
    query = await session.execute(
        select(UserWeatherSettings).where(UserWeatherSettings.user_id == user_id)
    )
    settings = query.scalar_one_or_none()
    if settings:
        settings.notification_time = time_str
        settings.notification_enabled = True  # якщо хочеш включити сповіщення
        session.add(settings)
        await session.commit()
