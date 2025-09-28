# PrognosyckBot

Персональний погодний Telegram-бот на Python з використанням Open-Meteo API, Geoapify та SQLAlchemy.

## Можливості
- Показ поточної погоди, денного та тижневого прогнозу
- Вибір міста та автоматичне геокодування
- Налаштування одиниць виміру, формату часу, відображення параметрів
- Щоденні сповіщення про погоду у вибраний час
- Збереження історії запитів
- Підтримка української мови

## Встановлення
1. Клонуйте репозиторій:
   ```bash
   git clone https://github.com/Quarry9221/PrognosyckBot.git
   cd PrognosyckBot
   ```
2. Створіть та активуйте віртуальне середовище:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```
3. Встановіть залежності:
   ```bash
   pip install -r requirements.txt
   ```
4. Створіть файл `.env` та заповніть змінні:
   ```env
   TELEGRAM_TOKEN=ваш_токен_бота
   GEOAPIFY_KEY=ваш_ключ_геокодування
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/weather_bot_db
   WEBHOOK_URL=https://your-domain.com/webhook
   ```
5. Ініціалізуйте базу даних (alembic):
   ```bash
   alembic upgrade head
   ```

## Запуск
```bash
python -m bot.bot
```

## Структура проекту
- `bot/` — логіка Telegram-бота, хендлери, клавіатури, логування
- `db/` — моделі, CRUD, робота з базою даних
- `services/` — інтеграція з Open-Meteo та Geoapify
- `alembic/` — міграції бази даних
- `logs/` — лог-файли

## Документація
- [Open-Meteo API](https://open-meteo.com/)
- [Geoapify Geocoding API](https://apidocs.geoapify.com/)
- [Aiogram](https://docs.aiogram.dev/en/latest/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)

## Ліцензія
MIT

---

З питаннями та пропозиціями звертайтесь до Quarry9221 на GitHub.