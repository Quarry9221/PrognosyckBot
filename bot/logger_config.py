# bot/logger_config.py
import logging
from logging.handlers import TimedRotatingFileHandler
import os

# --- Папка для логів ---
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# --- Формат логів ---
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# --- Головний логер ---
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # рівень для бота

# --- Handler для файлу з ротацією щодня ---
file_handler = TimedRotatingFileHandler(
    filename=os.path.join(LOG_DIR, "bot.log"),
    when="midnight",      # ротація щодня
    interval=1,
    backupCount=7,         # зберігати логи за останні 7 днів
    encoding="utf-8",
    delay=True             # важливо для Windows: відкриває файл при першому записі
)
file_handler.suffix = "%Y-%m-%d"  # додає дату до імені файлу
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
logger.addHandler(file_handler)

# --- Handler для консолі ---
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
logger.addHandler(console_handler)

# --- Зменшуємо лог SQLAlchemy до WARNING (щоб не спамив SELECT/ROLLBACK/COMMIT) ---
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)

# --- Логи aiogram залишаємо на INFO ---
logging.getLogger('aiogram').setLevel(logging.INFO)
