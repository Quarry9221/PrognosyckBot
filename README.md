
# PrognosyckBot (Telegram Weather Bot на aiogram)

Персональний погодний Telegram-бот на Python, написаний на фреймворку [aiogram](https://docs.aiogram.dev/en/latest/), з використанням Open-Meteo API, Geoapify та SQLAlchemy.

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

## Валідація та обробка помилок

У сервісах проєкту реалізована детальна валідація вхідних параметрів та обробка помилок:

- **services/weather.py**: Всі параметри запиту до Open-Meteo проходять перевірку типів, діапазонів, допустимих значень. Усі помилки HTTP, таймаути, мережеві та неочікувані винятки логуються та повертаються у вигляді зрозумілих повідомлень для користувача.
- **services/geocode.py**: Перевіряється статус відповіді Geoapify, наявність координат, обробляються всі можливі помилки та винятки, логуються причини невдачі.
- **db/crud.py**: Всі операції з базою даних мають обробку помилок, логування та повертають коректні винятки у разі проблем.

Завдяки цьому бот стабільно працює навіть при некоректних даних, проблемах з API чи базою даних, а користувач отримує зрозуміле повідомлення про причину помилки.

## Ліцензія
MIT

---

З питаннями та пропозиціями звертайтесь до Quarry9221 на GitHub.