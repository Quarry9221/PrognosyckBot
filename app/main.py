# main.py - Головний файл запуску погодного бота

import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from aiogram.fsm.storage.memory import MemoryStorage
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import TELEGRAM_TOKEN, WEBHOOK_PATH, DATABASE_URL
from app.bot.handlers import register_handlers
from app.db.models import Base
from app.db.database import engine, check_database_connection

# Налаштування логування
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(LOG_DIR, f"weather_bot.log"), 
            encoding='utf-8'
        )
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управління життєвим циклом додатку (polling only)"""
    logger.info("🚀 Запуск Weather Telegram Bot...")
    try:
        # Перевірка підключення до БД
        if not await check_database_connection():
            raise Exception("Неможливо підключитися до бази даних")
        # Створення таблиць
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Таблиці бази даних створені/оновлені")
        # Polling режим
        logger.info("🔄 Запуск у режимі polling...")
        await bot.delete_webhook(drop_pending_updates=True)
        asyncio.create_task(start_polling())
    except Exception as e:
        logger.error(f"❌ Помилка ініціалізації: {e}")
        raise
    yield
    # Очищення при завершенні
    logger.info("🛑 Зупинка бота...")
    try:
        await bot.session.close()
        await engine.dispose()
        logger.info("✅ Ресурси звільнені")
    except Exception as e:
        logger.error(f"❌ Помилка при завершенні: {e}")

# Ініціалізація бота та диспетчера
bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Реєстрація обробників
register_handlers(dp)

# FastAPI додаток
app = FastAPI(
    title="Weather Telegram Bot",
    description="Telegram бот для прогнозу погоди з використанням Open-Meteo API",
    version="2.0.0",
    lifespan=lifespan
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

async def start_polling():
    """Запуск бота в режимі polling"""
    try:
        logger.info("📡 Початок polling...")
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "chat_member"],
            skip_updates=True
        )
    except Exception as e:
        logger.error(f"❌ Помилка polling: {e}")



@app.get("/")
async def root():
    """Головна сторінка API"""
    bot_info = await bot.get_me()
    return {
        "message": "Weather Telegram Bot API",
        "version": "2.0.0",
        "bot": {
            "username": bot_info.username,
            "first_name": bot_info.first_name
        },
        "mode": "polling",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Перевірка здоров'я сервісу"""
    try:
        # Перевіряємо БД
        db_healthy = await check_database_connection()
        # Перевіряємо бота
        try:
            bot_info = await bot.get_me()
            bot_healthy = True
        except Exception:
            bot_healthy = False
        if db_healthy and bot_healthy:
            return {
                "status": "healthy",
                "database": "connected",
                "bot": "active",
                "mode": "polling"
            }
        else:
            raise HTTPException(status_code=503, detail="Service unhealthy")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")



@app.get("/stats")
@limiter.limit("10/minute")
async def get_stats(request: Request):
    """Базова статистика бота"""
    try:
        from app.db.database import get_session
        from app.db.models import User, UserMessage, BotChat
        from sqlalchemy import func, select
        
        async for session in get_session():
            # Кількість користувачів
            users_result = await session.execute(
                select(func.count(User.telegram_id))
            )
            total_users = users_result.scalar() or 0
            
            # Кількість повідомлень
            messages_result = await session.execute(
                select(func.count(UserMessage.id))
            )
            total_messages = messages_result.scalar() or 0
            
            # Кількість активних чатів
            active_chats_result = await session.execute(
                select(func.count(BotChat.id)).where(BotChat.is_active == True)
            )
            active_chats = active_chats_result.scalar() or 0
        
        return {
            "users": {
                "total": total_users
            },
            "messages": {
                "total": total_messages
            },
            "chats": {
                "active": active_chats
            },
            "database": DATABASE_URL.split("://")[0] if DATABASE_URL else "unknown"
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Cannot fetch stats")

# Middleware для логування запитів
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = asyncio.get_event_loop().time()
    response = await call_next(request)
    process_time = asyncio.get_event_loop().time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {process_time:.3f}s"
    )
    return response

if __name__ == "__main__":
    import uvicorn
    
    # Конфігурація сервера
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🌐 Запуск сервера на {host}:{port}")
    
    logger.info("🔄 Режим: Polling")
    
    # Запуск сервера
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )