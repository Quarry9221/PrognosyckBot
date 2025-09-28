from datetime import datetime
from aiogram.types import CallbackQuery
from bot.handlers.settings_callbacks import location_settings_callback
from bot.keyboards import WeatherKeyboards
from db.database import get_session
from db.crud import get_user_weather_settings
from aiogram.fsm.context import FSMContext
from bot.states import SettingsStates
from bot.logger_config import logger



async def set_location_callback(call: CallbackQuery, state: FSMContext):
    """Початок процесу встановлення локації"""
    await call.answer()

    await call.message.edit_text(
        "📍 **Встановлення локації**\n\n"
        "Надішли назву міста або координати в форматі:\n"
        "• Київ\n"
        "• Mukachevo, Ukraine\n"
        "• 48.9166, 24.7111\n\n"
        "Або надішли геолокацію через вкладення.",
        reply_markup=WeatherKeyboards.location_input_help(),
        parse_mode="Markdown"
    )

    await state.set_state(SettingsStates.waiting_location)


async def timezone_callback(call: CallbackQuery):
    """Вибір часового поясу"""
    await call.answer()

    await call.message.edit_text(
        "🕐 **Оберіть часовий пояс:**\n\n"
        "Рекомендується використовувати автоматичний вибір.",
        reply_markup=WeatherKeyboards.timezone_selector(),
        parse_mode="Markdown"
    )


async def set_timezone_callback(call: CallbackQuery):
    """Встановлення часового поясу"""
    await call.answer()

    _, timezone = call.data.split(":", 1)

    try:
        async for session in get_session():
            settings = await get_user_weather_settings(session, call.from_user.id)
            settings.timezone = timezone
            settings.updated_at = datetime.now()
            await session.commit()

        await call.answer(f"Часовий пояс встановлено: {timezone}", show_alert=True)
        await location_settings_callback(call)

    except Exception as e:
        await call.answer(f"Помилка: {str(e)}", show_alert=True)
        logger.error(f"Помилка встановлення timezone для {call.from_user.id}: {str(e)}")