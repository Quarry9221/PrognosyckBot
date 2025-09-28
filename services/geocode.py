
# Логіка для роботи з Geoapify
import httpx
import os
from datetime import datetime
from config import GEOAPIFY_KEY
from bot.logger_config import logger

# Логи налаштовуються через bot.logger_config

async def geocode_place(place: str) -> tuple[float, float]:
    url = f"https://api.geoapify.com/v1/geocode/search?text={place}&limit=1&format=json&apiKey={GEOAPIFY_KEY}"
    logger.info(f"Geoapify запит: '{place}' -> {url}")
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            logger.error(f"Geoapify помилка: status={response.status_code}, text={response.text}")
            raise ValueError("Geocoding failed")
        data = response.json()
        if not data.get("results"):
            logger.warning(f"Geoapify: не знайдено координат для '{place}'")
            raise ValueError("Я не знайшов таке місце. Спробуйте ще раз")
        result = data["results"][0]
        lat = result["lat"]
        lon = result["lon"]
        logger.info(f"Geoapify результат: '{place}' -> lat={lat}, lon={lon}")
        return {
            "lat": lat,
            "lon": lon,
            "city": result.get("city"),
            "state": result.get("state"),
            "country": result.get("country"),
            "formatted": result.get("formatted")
        }