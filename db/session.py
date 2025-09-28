# db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # наприклад: postgresql+asyncpg://user:pass@localhost/weather_db

# Створюємо асинхронний engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # щоб бачити SQL-запити в консолі
)

# Створюємо асинхронний sessionmaker
async_session = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)
