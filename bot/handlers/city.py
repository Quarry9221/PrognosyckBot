from aiogram import Router, types
from services.geocode import geocode_place
from services.weather import get_weather
from bot.keyboards import WeatherKeyboards

router = Router()


@router.message()
async def handle_city(message: types.Message):
    place = message.text.strip()
    try:
        location = await geocode_place(place)
        weather = await get_weather(location["lat"], location["lon"])
        response = f"📍 {location['formatted']}\n🌡️ {weather['temperature']}°C\n💨 {weather['windspeed']} км/год"
        await message.answer(
            response, reply_markup=WeatherKeyboards.weather_type_menu()
        )
    except Exception as e:
        await message.answer(f"Помилка: {e}")
