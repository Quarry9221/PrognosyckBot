# Логіка для роботи з Geoapify
import httpx
import os
from datetime import datetime
from config import GEOAPIFY_KEY
from bot.logger_config import logger

# Логи налаштовуються через bot.logger_config


async def geocode_place(place: str) -> dict:
    """
    Геокодування місця через Geoapify з детальною валідацією та обробкою помилок
    Args:
        place: Назва місця
    Returns:
        dict з координатами та інформацією про місце
    Raises:
        ValueError: Якщо геокодування не вдалося
    """
    if not place or not isinstance(place, str) or len(place.strip()) < 2:
        logger.warning(f"Некоректний запит геокодування: '{place}'")
        raise ValueError("Введіть коректну назву місця")

    url = f"https://api.geoapify.com/v1/geocode/search?text={place}&limit=1&format=json&apiKey={GEOAPIFY_KEY}"
    logger.info(f"Geoapify запит: '{place}' -> {url}")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        logger.error("Geoapify: таймаут запиту")
        raise ValueError("Сервіс геокодування не відповідає. Спробуйте пізніше")
    except httpx.HTTPStatusError as e:
        logger.error(f"Geoapify HTTP помилка: {e.response.status_code}")
        raise ValueError("Помилка геокодування. Спробуйте іншу назву")
    except httpx.RequestError as e:
        logger.error(f"Geoapify мережевий збій: {str(e)}")
        raise ValueError("Проблема з мережею. Спробуйте ще раз")
    except Exception as e:
        logger.error(f"Geoapify несподівана помилка: {str(e)}", exc_info=True)
        raise ValueError("Технічна помилка геокодування")

    if not data.get("results"):
        logger.warning(f"Geoapify: не знайдено координат для '{place}'")
        raise ValueError("Я не знайшов таке місце. Спробуйте ще раз")

    result = data["results"][0]
    lat = result.get("lat")
    lon = result.get("lon")
    if lat is None or lon is None:
        logger.error(f"Geoapify: відсутні координати для '{place}'")
        raise ValueError("Не вдалося отримати координати місця")

    logger.info(f"Geoapify результат: '{place}' -> lat={lat}, lon={lon}")
    return {
        "lat": lat,
        "lon": lon,
        "city": result.get("city"),
        "state": result.get("state"),
        "country": result.get("country"),
        "formatted": result.get("formatted"),
    }
