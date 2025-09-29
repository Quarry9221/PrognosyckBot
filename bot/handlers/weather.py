from aiogram import Router, types
from aiogram.types import CallbackQuery
from bot.keyboards import WeatherKeyboards
from services.weather import get_weather

router = Router()


@router.callback_query(lambda c: c.data.startswith("weather:"))
async def weather_menu_handler(callback: CallbackQuery):
    data = callback.data.split(":")[1]
    if data == "current":
        # приклад, можна доопрацювати
        await callback.message.answer("Поточна погода буде тут...")
    elif data == "weekly":
        await callback.message.answer("Тижневий прогноз буде тут...")
    await callback.answer()  # щоб кнопка "клікалась"
