from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties
import asyncio
import os

from dotenv import load_dotenv

from bot.notifications import daily_notifications_scheduler
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

async def main():
    bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()
    
    # Реєстрація хендлерів
    from bot.handlers import register_handlers
    register_handlers(dp)
    
    # Запуск фонового шедулера
    asyncio.create_task(daily_notifications_scheduler(bot))
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
