import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from db.models import (
    Base, User, UserWeatherSettings, UserMessage, BotChat,
    HOURLY_PARAMETERS, DAILY_PARAMETERS, CURRENT_PARAMETERS,
    TEMPERATURE_UNITS, WIND_SPEED_UNITS, PRECIPITATION_UNITS, TIMEFORMAT_OPTIONS
)


@pytest.fixture(scope='function')
def db_session():
    """Створює тестову базу даних в пам'яті"""
    engine = create_engine('sqlite:///:memory:')
    
    # Увімкнути Foreign Key constraints для SQLite
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


class TestUserModel:
    """Тести для моделі User"""
    
    def test_create_user(self, db_session):
        """Тест створення користувача"""
        user = User(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            language_code="uk"
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.created_at is not None
    
    def test_user_default_values(self, db_session):
        """Тест дефолтних значень"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        assert user.language_code == 'uk'
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_user_unique_telegram_id(self, db_session):
        """Тест унікальності telegram_id"""
        user1 = User(telegram_id=123456789, username="user1")
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(telegram_id=123456789, username="user2")
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_nullable_fields(self, db_session):
        """Тест що необов'язкові поля можуть бути None"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        assert user.username is None
        assert user.first_name is None
        assert user.last_name is None


class TestUserWeatherSettingsModel:
    """Тести для моделі UserWeatherSettings"""
    
    def test_create_settings(self, db_session):
        """Тест створення налаштувань"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        settings = UserWeatherSettings(
            user_id=123456789,
            latitude=50.4501,
            longitude=30.5234,
            location_name="Kyiv"
        )
        db_session.add(settings)
        db_session.commit()
        
        assert settings.user_id == 123456789
        assert settings.latitude == 50.4501
        assert settings.longitude == 30.5234
    
    def test_settings_default_values(self, db_session):
        """Тест дефолтних значень налаштувань"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        settings = UserWeatherSettings(user_id=123456789)
        db_session.add(settings)
        db_session.commit()
        
        # Одиниці виміру
        assert settings.temperature_unit == 'celsius'
        assert settings.wind_speed_unit == 'kmh'
        assert settings.precipitation_unit == 'mm'
        assert settings.timeformat == 'iso8601'
        
        # Налаштування прогнозу
        assert settings.forecast_days == 7
        assert settings.past_days == 0
        
        # Показувати hourly
        assert settings.show_temperature is True
        assert settings.show_feels_like is True
        assert settings.show_humidity is True
        assert settings.show_pressure is False
        assert settings.show_wind is True
        
        # Показувати daily
        assert settings.show_daily_temperature is True
        assert settings.show_sunrise_sunset is True
        
        # Сповіщення
        assert settings.notification_enabled is False
    
    def test_settings_unique_user_id(self, db_session):
        """Тест що один користувач може мати тільки одні налаштування"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        settings1 = UserWeatherSettings(user_id=123456789)
        db_session.add(settings1)
        db_session.commit()
        
        settings2 = UserWeatherSettings(user_id=123456789)
        db_session.add(settings2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_settings_foreign_key_cascade(self, db_session):
        """Тест каскадного видалення при видаленні користувача"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        settings = UserWeatherSettings(user_id=123456789)
        db_session.add(settings)
        db_session.commit()
        
        db_session.delete(user)
        db_session.commit()
        
        # Налаштування повинні бути видалені автоматично
        result = db_session.query(UserWeatherSettings).filter_by(user_id=123456789).first()
        assert result is None
    
    def test_settings_all_boolean_flags(self, db_session):
        """Тест що всі boolean прапорці мають правильні типи"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        settings = UserWeatherSettings(user_id=123456789)
        db_session.add(settings)
        db_session.commit()
        
        boolean_fields = [
            'show_temperature', 'show_feels_like', 'show_humidity', 'show_pressure',
            'show_wind', 'show_precipitation', 'show_precipitation_probability',
            'show_cloud_cover', 'show_uv_index', 'show_visibility', 'show_dew_point',
            'show_solar_radiation', 'show_daily_temperature', 'show_daily_precipitation',
            'show_daily_wind', 'show_sunrise_sunset', 'show_daylight_duration',
            'show_sunshine_duration', 'show_daily_uv', 'show_current_weather',
            'notification_enabled'
        ]
        
        for field in boolean_fields:
            value = getattr(settings, field)
            assert isinstance(value, bool), f"{field} має бути boolean"
    
    def test_settings_notification_time_format(self, db_session):
        """Тест формату часу сповіщень"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        settings = UserWeatherSettings(
            user_id=123456789,
            notification_time="08:30"
        )
        db_session.add(settings)
        db_session.commit()
        
        assert settings.notification_time == "08:30"
        assert len(settings.notification_time) == 5


class TestUserMessageModel:
    """Тести для моделі UserMessage"""
    
    def test_create_message(self, db_session):
        """Тест створення повідомлення"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        message = UserMessage(
            user_id=123456789,
            chat_id=987654321,
            message_text="Яка погода?",
            location_requested="Kyiv"
        )
        db_session.add(message)
        db_session.commit()
        
        assert message.user_id == 123456789
        assert message.chat_id == 987654321
        assert message.message_text == "Яка погода?"
        assert message.timestamp is not None
    
    def test_message_with_coordinates(self, db_session):
        """Тест повідомлення з координатами"""
        message = UserMessage(
            chat_id=123456789,
            message_text="location",
            latitude=50.4501,
            longitude=30.5234
        )
        db_session.add(message)
        db_session.commit()
        
        assert message.latitude == 50.4501
        assert message.longitude == 30.5234
    
    def test_message_nullable_user_id(self, db_session):
        """Тест що user_id може бути None (для груп)"""
        message = UserMessage(
            chat_id=123456789,
            message_text="test"
        )
        db_session.add(message)
        db_session.commit()
        
        assert message.user_id is None


class TestBotChatModel:
    """Тести для моделі BotChat"""
    
    def test_create_chat(self, db_session):
        """Тест створення чату"""
        chat = BotChat(
            chat_id=123456789,
            chat_type="group",
            title="Test Group"
        )
        db_session.add(chat)
        db_session.commit()
        
        assert chat.chat_id == 123456789
        assert chat.chat_type == "group"
        assert chat.title == "Test Group"
    
    def test_chat_default_values(self, db_session):
        """Тест дефолтних значень чату"""
        chat = BotChat(
            chat_id=123456789,
            chat_type="private"
        )
        db_session.add(chat)
        db_session.commit()
        
        assert chat.is_active is True
        assert isinstance(chat.added_at, datetime)
        assert isinstance(chat.last_activity, datetime)
    
    def test_chat_unique_chat_id(self, db_session):
        """Тест унікальності chat_id"""
        chat1 = BotChat(chat_id=123456789, chat_type="group")
        db_session.add(chat1)
        db_session.commit()
        
        chat2 = BotChat(chat_id=123456789, chat_type="supergroup")
        db_session.add(chat2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_chat_types(self, db_session):
        """Тест різних типів чатів"""
        chat_types = ["private", "group", "supergroup", "channel"]
        
        for i, chat_type in enumerate(chat_types):
            chat = BotChat(chat_id=123456789 + i, chat_type=chat_type)
            db_session.add(chat)
        
        db_session.commit()
        
        for i, chat_type in enumerate(chat_types):
            chat = db_session.query(BotChat).filter_by(chat_id=123456789 + i).first()
            assert chat.chat_type == chat_type


class TestConstants:
    """Тести для констант"""
    
    def test_hourly_parameters_not_empty(self):
        """Тест що hourly параметри не порожні"""
        assert len(HOURLY_PARAMETERS) > 0
        assert isinstance(HOURLY_PARAMETERS, list)
    
    def test_hourly_parameters_contain_basic_fields(self):
        """Тест що hourly містить базові поля"""
        required_fields = [
            'temperature_2m',
            'weather_code',
            'precipitation',
            'wind_speed_10m'
        ]
        
        for field in required_fields:
            assert field in HOURLY_PARAMETERS, f"{field} має бути в HOURLY_PARAMETERS"
    
    def test_daily_parameters_not_empty(self):
        """Тест що daily параметри не порожні"""
        assert len(DAILY_PARAMETERS) > 0
        assert isinstance(DAILY_PARAMETERS, list)
    
    def test_daily_parameters_contain_basic_fields(self):
        """Тест що daily містить базові поля"""
        required_fields = [
            'weather_code',
            'temperature_2m_max',
            'temperature_2m_min',
            'sunrise',
            'sunset'
        ]
        
        for field in required_fields:
            assert field in DAILY_PARAMETERS, f"{field} має бути в DAILY_PARAMETERS"
    
    def test_current_parameters_not_empty(self):
        """Тест що current параметри не порожні"""
        assert len(CURRENT_PARAMETERS) > 0
        assert isinstance(CURRENT_PARAMETERS, list)
    
    def test_current_parameters_contain_basic_fields(self):
        """Тест що current містить базові поля"""
        required_fields = [
            'temperature_2m',
            'weather_code',
            'precipitation',
            'wind_speed_10m'
        ]
        
        for field in required_fields:
            assert field in CURRENT_PARAMETERS, f"{field} має бути в CURRENT_PARAMETERS"
    
    def test_temperature_units(self):
        """Тест одиниць температури"""
        assert TEMPERATURE_UNITS == ['celsius', 'fahrenheit']
        assert len(TEMPERATURE_UNITS) == 2
    
    def test_wind_speed_units(self):
        """Тест одиниць швидкості вітру"""
        expected = ['kmh', 'ms', 'mph', 'kn']
        assert WIND_SPEED_UNITS == expected
        assert len(WIND_SPEED_UNITS) == 4
    
    def test_precipitation_units(self):
        """Тест одиниць опадів"""
        assert PRECIPITATION_UNITS == ['mm', 'inch']
        assert len(PRECIPITATION_UNITS) == 2
    
    def test_timeformat_options(self):
        """Тест варіантів формату часу"""
        assert TIMEFORMAT_OPTIONS == ['iso8601', 'unixtime']
        assert len(TIMEFORMAT_OPTIONS) == 2
    
    def test_no_duplicate_parameters(self):
        """Тест що немає дублікатів у параметрах"""
        assert len(HOURLY_PARAMETERS) == len(set(HOURLY_PARAMETERS))
        assert len(DAILY_PARAMETERS) == len(set(DAILY_PARAMETERS))
        assert len(CURRENT_PARAMETERS) == len(set(CURRENT_PARAMETERS))
    
    def test_parameters_are_strings(self):
        """Тест що всі параметри є рядками"""
        for param in HOURLY_PARAMETERS:
            assert isinstance(param, str)
        
        for param in DAILY_PARAMETERS:
            assert isinstance(param, str)
        
        for param in CURRENT_PARAMETERS:
            assert isinstance(param, str)


class TestDataIntegrity:
    """Тести цілісності даних"""
    
    def test_user_with_settings_relationship(self, db_session):
        """Тест зв'язку між користувачем і налаштуваннями"""
        user = User(telegram_id=123456789, username="test")
        db_session.add(user)
        db_session.commit()
        
        settings = UserWeatherSettings(
            user_id=123456789,
            latitude=50.45,
            longitude=30.52
        )
        db_session.add(settings)
        db_session.commit()
        
        # Перевіряємо що можемо знайти налаштування за user_id
        found_settings = db_session.query(UserWeatherSettings).filter_by(
            user_id=user.telegram_id
        ).first()
        
        assert found_settings is not None
        assert found_settings.user_id == user.telegram_id
    
    def test_multiple_messages_per_user(self, db_session):
        """Тест що користувач може мати багато повідомлень"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        for i in range(5):
            message = UserMessage(
                user_id=123456789,
                chat_id=987654321,
                message_text=f"Message {i}"
            )
            db_session.add(message)
        
        db_session.commit()
        
        messages = db_session.query(UserMessage).filter_by(user_id=123456789).all()
        assert len(messages) == 5
    
    def test_chat_activity_tracking(self, db_session):
        """Тест відстеження активності чату"""
        chat = BotChat(
            chat_id=123456789,
            chat_type="group",
            is_active=True
        )
        db_session.add(chat)
        db_session.commit()
        
        # Симулюємо оновлення активності
        chat.is_active = False
        chat.last_activity = datetime.now()
        db_session.commit()
        
        updated_chat = db_session.query(BotChat).filter_by(chat_id=123456789).first()
        assert updated_chat.is_active is False


class TestEdgeCases:
    """Тести граничних випадків"""
    
    def test_forecast_days_limits(self, db_session):
        """Тест меж кількості днів прогнозу"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        settings = UserWeatherSettings(
            user_id=123456789,
            forecast_days=16,  # максимум
            past_days=92  # максимум
        )
        db_session.add(settings)
        db_session.commit()
        
        assert settings.forecast_days == 16
        assert settings.past_days == 92
    
    def test_long_location_name(self, db_session):
        """Тест довгої назви локації"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        long_name = "A" * 255  # Максимальна довжина
        settings = UserWeatherSettings(
            user_id=123456789,
            location_name=long_name
        )
        db_session.add(settings)
        db_session.commit()
        
        assert len(settings.location_name) == 255
    
    def test_negative_coordinates(self, db_session):
        """Тест від'ємних координат"""
        user = User(telegram_id=123456789)
        db_session.add(user)
        db_session.commit()
        
        settings = UserWeatherSettings(
            user_id=123456789,
            latitude=-33.8688,  # Сідней
            longitude=151.2093
        )
        db_session.add(settings)
        db_session.commit()
        
        assert settings.latitude < 0
        assert settings.longitude > 0
    
    def test_very_large_telegram_id(self, db_session):
        """Тест дуже великого telegram_id"""
        large_id = 9999999999999  # Максимально можливий
        user = User(telegram_id=large_id)
        db_session.add(user)
        db_session.commit()
        
        assert user.telegram_id == large_id