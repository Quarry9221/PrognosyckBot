from aiogram import Router, types
from aiogram.filters import Command
from bot.keyboards import WeatherKeyboards

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привіт 👋 Я бот для прогнозу погоди!\n\nВведи назву міста або скористайся меню:",
        reply_markup=WeatherKeyboards.main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Я можу показати прогноз погоди по місту.\n"
        "Введи назву міста або скористайся меню кнопок нижче.",
        reply_markup=WeatherKeyboards.main_menu(),
    )
