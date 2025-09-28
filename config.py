from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEOAPIFY_KEY = os.getenv("GEOAPIFY_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")  # e.g., postgresql+asyncpg://user:pass@localhost/db
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-domain.com/webhook