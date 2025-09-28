import logging
from logging.handlers import TimedRotatingFileHandler
import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from datetime import datetime, timedelta
import pytz

# ------- Налаштування (вставте свої ключі) -------
TELEGRAM_TOKEN = "8018140800:AAHkQdORjvTZIvmKKtDUVpwiSsgKUd6ymw0"
GEOAPIFY_API_KEY = "8e7e4ce8457f417ba01a94598743a7bf"
# --------------------------------------------------


# Логування у файл з ротацією по днях
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"weather_bot_{datetime.now().strftime('%Y-%m-%d')}.log")

file_handler = TimedRotatingFileHandler(
    filename=log_filename,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)
file_handler.suffix = "%Y-%m-%d"
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger("weather_bot")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Конфіг для Open-Meteo
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


# --- Інтеграція з FastAPI бекендом ---
BACKEND_URL = "http://localhost:8000"

def backend_register_user(user_id: int, username: str = None, language: str = "uk"):
    url = f"{BACKEND_URL}/user/register"
    payload = {
        "id": user_id,
        "username": username,
        "language": language,
        "settings": None
    }
    try:
        resp = requests.post(url, json=payload, timeout=5)
        logger.info(f"Backend register user {user_id}: {resp.status_code}")
    except Exception as e:
        logger.error(f"Backend register user error: {e}")

def backend_log_query(user_id: int, place: str, lat: float, lon: float, weather_response: dict):
    url = f"{BACKEND_URL}/query/log"
    payload = {
        "id": int(datetime.utcnow().timestamp()),
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "place": place,
        "lat": lat,
        "lon": lon,
        "weather_response": weather_response
    }
    try:
        resp = requests.post(url, json=payload, timeout=5)
        logger.info(f"Backend log query for user {user_id}: {resp.status_code}")
    except Exception as e:
        logger.error(f"Backend log query error: {e}")

def geocode_place(place_name: str, lang: str = "uk") -> dict:
    """
    Використовує Geoapify Geocoding API для отримання координат та імені місця.
    Повертає словник з keys: lat, lon, name, country, city (за можливості).
    Якщо не знайдено — повертає None.
    """
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "apiKey": GEOAPIFY_API_KEY,
        "text": place_name,
        "lang": lang,
        "limit": 5,          # беремо кілька результатів, можна покращити вибір
        "format": "json"
    }
    logger.info(f"Geoapify geocode request: {url} params={params}")
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        logger.info(f"Geoapify response: {resp.status_code} {resp.url}")
    except requests.RequestException as e:
        logger.error(f"Geoapify request failed: {e}")
        return None

    data = resp.json()
    logger.info(f"Geoapify raw response: {data}")
    features = data.get("features") or []
    # Якщо features порожній, спробувати results (як у C#)
    if not features and "results" in data:
        logger.info(f"Geoapify 'results' found: {len(data['results'])}")
        if data["results"]:
            # Спробувати взяти перший результат
            r = data["results"][0]
            lat = r.get("lat")
            lon = r.get("lon")
            name = r.get("name") or place_name
            country = r.get("country")
            city = r.get("city") or r.get("state") or None
            country_code = r.get("country_code")
            logger.info(f"Geocoded (results): name={name}, lat={lat}, lon={lon}, country={country}, city={city}, country_code={country_code}")
            # Перевірка на RU
            if country_code and country_code.lower() == "ru":
                logger.warning(f"Запит погоди для забороненої країни: {country_code}")
                return None
            return {
                "lat": lat,
                "lon": lon,
                "name": name,
                "country": country,
                "city": city
            }
        else:
            return None

    logger.info(f"Geoapify found {len(features)} features for '{place_name}'")
    if not features:
        return None

    # Простий вибір: перший результат, або можна фільтрувати за типом place
    f = features[0]
    props = f.get("properties", {})
    lat = props.get("lat") or f.get("geometry", {}).get("coordinates", [None, None])[1]
    lon = props.get("lon") or f.get("geometry", {}).get("coordinates", [None, None])[0]
    name = props.get("formatted") or props.get("name") or place_name
    country = props.get("country")
    city = props.get("city") or props.get("state") or None
    country_code = props.get("country_code")

    logger.info(f"Geocoded: name={name}, lat={lat}, lon={lon}, country={country}, city={city}, country_code={country_code}")
    # Перевірка на RU
    if country_code and country_code.lower() == "ru":
        logger.warning(f"Запит погоди для забороненої країни: {country_code}")
        return None
    return {
        "lat": lat,
        "lon": lon,
        "name": name,
        "country": country,
        "city": city
    }

def fetch_weather_open_meteo(lat: float, lon: float, days: int = 3, timezone: str = "auto") -> dict:
    """
    Запит до Open-Meteo:
    Повертає прогноз daily та hourly за необхідності.
    days: кількість днів вперед (включно з сьогодні). Максимум Open-Meteo зазвичай 16 днів.
    timezone: може бути "auto" або конкретна назва часової зони.
    """
    if days < 1:
        days = 1
    if days > 16:
        days = 16

    today = datetime.utcnow().date()
    end_date = today + timedelta(days=days-1)

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "weathercode",
            "sunrise",
            "sunset",
        ]),
        "timezone": timezone,
        "start_date": today.isoformat(),
        "end_date": end_date.isoformat(),
    }

    logger.info(f"Open-Meteo request: {OPEN_METEO_BASE} params={params}")
    try:
        resp = requests.get(OPEN_METEO_BASE, params=params, timeout=10)
        resp.raise_for_status()
        logger.info(f"Open-Meteo response: {resp.status_code} {resp.url}")
    except requests.RequestException as e:
        logger.error(f"Open-Meteo request failed: {e}")
        return None

    return resp.json()

# Невелика мапа weathercode -> опис (англ/укр). Можна розширити.
WEATHERCODE_UA = {
    0: "ясно",
    1: "мало хмар",
    2: "перемінна хмарність",
    3: "похмуро",
    45: "туман",
    48: "морозний туман (димка)",
    51: "легкий моросящий дощ",
    53: "помірний моросящий дощ",
    55: "щільний моросящий дощ",
    56: "легкий моросящий дощ (з льодяними кристалами)",
    57: "щільний моросящий дощ (з льодяними кристалами)",
    61: "невеликий дощ",
    63: "помірний дощ",
    65: "сильний дощ",
    66: "сніг з дощем (ледяний дощ)",
    67: "інтенсивний дощ/сніг з дощем",
    71: "невеликий сніг",
    73: "помірний сніг",
    75: "сильний сніг",
    77: "снігові зерна",
    80: "короткочасні зливи",
    81: "тривалі зливи",
    82: "інтенсивні зливи",
    85: "короткочасні снігопади",
    86: "тривалі снігопади",
    95: "гроза",
    96: "гроза з невеликим градом",
    99: "гроза з сильним градом",
}

def format_daily_forecast(location_name: str, weather_json: dict) -> str:
    """
    Форматує відповідь для користувача: кілька днів (з daily).
    """
    if not weather_json:
        logger.warning("No weather data to format for location: %s", location_name)
        return "Не вдалося отримати дані погоди."

    daily = weather_json.get("daily", {})
    dates = daily.get("time", [])
    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    precipitation = daily.get("precipitation_sum", [])
    weathercodes = daily.get("weathercode", [])
    sunrises = daily.get("sunrise", [])
    sunsets = daily.get("sunset", [])

    lines = [f"Погода для {location_name}:\n"]
    for i, d in enumerate(dates):
        # Формат дати: YYYY-MM-DD -> локальний формат
        try:
            date_obj = datetime.fromisoformat(d)
            date_str = date_obj.strftime("%a, %d.%m.%Y")
        except Exception:
            date_str = d

        max_t = temps_max[i] if i < len(temps_max) else "—"
        min_t = temps_min[i] if i < len(temps_min) else "—"
        prec = precipitation[i] if i < len(precipitation) else 0
        code = weathercodes[i] if i < len(weathercodes) else None
        desc = WEATHERCODE_UA.get(code, f"код {code}") if code is not None else "—"
        sunrise = sunrises[i].split("T")[1] if i < len(sunrises) and sunrises[i] else "—"
        sunset = sunsets[i].split("T")[1] if i < len(sunsets) and sunsets[i] else "—"

        lines.append(
            f"{date_str}: {desc}. T: {min_t}°C — {max_t}°C. Опади: {prec} мм. Схід: {sunrise}, Захід: {sunset}"
        )

    return "\n".join(lines)

# Обробники Telegram

async def start(update: Update, context: CallbackContext) -> None:
    logger.info(f"/start command from user_id={update.effective_user.id}")
    await update.message.reply_text("Привіт! Напишіть назву місця українською, і я пришлю погоду на кілька днів. Наприклад: Львів або Київ, вулиця або село.")

async def help_command(update: Update, context: CallbackContext) -> None:
    logger.info(f"/help command from user_id={update.effective_user.id}")
    await update.message.reply_text("Надішліть назву місця українською — отримаєте прогноз. /start для початку.")

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_text = update.message.text.strip()
    user_id = update.effective_user.id if update.effective_user else None
    username = update.effective_user.username if update.effective_user else None
    logger.info(f"Message from user_id={user_id}: '{user_text}'")
    if not user_text:
        logger.warning(f"Empty message from user_id={user_id}")
        await update.message.reply_text("Будь ласка, введіть назву місця.")
        return

    # Реєстрація користувача у бекенді (якщо ще не існує)
    backend_register_user(user_id, username)

    msg = await update.message.reply_text("Шукаю місце…")
    geocoded = geocode_place(user_text, lang="uk")
    if not geocoded:
        logger.warning(f"Geocode failed for '{user_text}' from user_id={user_id}")
        await msg.edit_text("❌ Не вдалося знайти місце або країна заборонена. Спробуйте іншу назву, перевірте написання або виберіть інше місце.")
        return

    lat = geocoded.get("lat")
    lon = geocoded.get("lon")
    place_name = geocoded.get("name") or user_text
    logger.info(f"User {user_id} requested weather for: {place_name} (lat={lat}, lon={lon})")

    await msg.edit_text(f"Знайдено: {place_name} (lat={lat}, lon={lon}). Отримую прогноз…")

    # Отримати прогноз на 4 дні (можна змінити або додати команду для вибору)
    days = 4
    # Визначимо timezone = auto (Open-Meteo підтримає рядок "auto")
    weather = fetch_weather_open_meteo(lat, lon, days=days, timezone="auto")
    if not weather:
        logger.error(f"Weather fetch failed for {place_name} (lat={lat}, lon={lon}) user_id={user_id}")
        await msg.edit_text("Не вдалося отримати дані погоди з Open-Meteo.")
        return

    # Логування запиту у бекенд
    backend_log_query(user_id, place_name, lat, lon, weather)

    reply = format_daily_forecast(place_name, weather)
    logger.info(f"Sending weather reply to user_id={user_id} for {place_name}")
    await msg.edit_text(reply)

async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    user_id = update.effective_user.id if update and update.effective_user else None
    logger.error(f"Error handler triggered for user_id={user_id}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("Сталася помилка при обробці запиту.")
    except Exception as e:
        logger.error(f"Failed to send error message to user_id={user_id}: {e}")

from telegram.ext import ApplicationBuilder

def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add handlers as before
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    logger.info("Starting bot...")
    application.run_polling()

if __name__ == "__main__":
    main()