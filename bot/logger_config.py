import logging
from logging.handlers import TimedRotatingFileHandler
import os


LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


logger = logging.getLogger()
logger.setLevel(logging.INFO)


file_handler = TimedRotatingFileHandler(
    filename=os.path.join(LOG_DIR, "bot.log"),
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
    delay=True,
)
file_handler.suffix = "%Y-%m-%d"
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
logger.addHandler(file_handler)


console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
logger.addHandler(console_handler)


logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)


logging.getLogger("aiogram").setLevel(logging.INFO)
