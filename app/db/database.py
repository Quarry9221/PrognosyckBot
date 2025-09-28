# SQLAlchemy engine та session

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.config import DATABASE_URL
from typing import AsyncGenerator

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# Перевірка підключення до бази даних з логуванням
import logging

async def check_database_connection() -> bool:
    logger = logging.getLogger("db_check")
    try:
        logger.info("Початок перевірки підключення до бази даних...")
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Підключення до бази даних успішне.")
        return True
    except SQLAlchemyError as e:
        logger.error(f"❌ SQLAlchemyError при підключенні до бази даних: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Інша помилка при підключенні до бази даних: {e}")
        return False