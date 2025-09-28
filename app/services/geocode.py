
# Логіка для роботи з Geoapify
import httpx
import logging
import os
from datetime import datetime
from app.config import GEOAPIFY_KEY

# Logging setup (щоденний лог-файл)
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"weather_bot_{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler(log_filename, encoding='utf-8'), logging.StreamHandler()]
)

async def geocode_place(place: str) -> tuple[float, float]:
    url = f"https://api.geoapify.com/v1/geocode/search?text={place}&limit=1&format=json&apiKey={GEOAPIFY_KEY}"
    logging.info(f"Geoapify запит: '{place}' -> {url}")
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            logging.error(f"Geoapify помилка: status={response.status_code}, text={response.text}")
            raise ValueError("Geocoding failed")
        data = response.json()
        if not data.get("results"):
            logging.warning(f"Geoapify: не знайдено координат для '{place}'")
            raise ValueError("Я не знайшов таке місце. Спробуйте ще раз")
        result = data["results"][0]
        lat = result["lat"]
        lon = result["lon"]
        logging.info(f"Geoapify результат: '{place}' -> lat={lat}, lon={lon}")
        return {
            "lat": lat,
            "lon": lon,
            "city": result.get("city"),
            "state": result.get("state"),
            "country": result.get("country"),
            "formatted": result.get("formatted")
        }