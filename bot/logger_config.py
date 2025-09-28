# bot/logger_config.py
import logging
from logging.handlers import TimedRotatingFileHandler
import os

# Створюємо папку logs, якщо її немає
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Формат логів
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Ініціалізація логера
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Handler для файлу з ротацією щодня
file_handler = TimedRotatingFileHandler(
    filename=f"{LOG_DIR}/bot.log",
    when="midnight",  # ротація щодня
    interval=1,
    backupCount=7,    # зберігати логи за останні 7 днів
    encoding="utf-8"
)
file_handler.suffix = "%Y-%m-%d"  # додає дату до імені файлу
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
logger.addHandler(file_handler)

# Також вивід у консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
logger.addHandler(console_handler)
