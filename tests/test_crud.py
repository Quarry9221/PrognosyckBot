import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, UserWeatherSettings, UserMessage, BotChat
from db.crud import (
    get_or_create_user,
    create_default_weather_settings,
    get_user_weather_settings,
    update_user_location,
    update_user_units,
    toggle_display_setting,
    update_forecast_settings,
    update_notification_settings,
    get_api_parameters,
    save_user_message,
    normalize_chat_id,
    save_chat_to_db,
    track_chat_member_update,
    get_user_settings_summary,
    get_settings,
    update_setting,
    get_user_state,
    set_user_state,
    save_notification_time
)


@pytest.fixture
def mock_session():
    """Мок AsyncSession для тестування"""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def sample_user():
    """Зразок користувача"""
    return User(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        language_code="uk",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_settings():
    """Зразок налаштувань погоди"""
    return UserWeatherSettings(
        user_id=123456789,
        latitude=50.4501,
        longitude=30.5234,
        location_name="Kyiv",
        temperature_unit="celsius",
        wind_speed_unit="kmh",
        precipitation_unit="mm",
        timezone="auto",
        forecast_days=7,
        past_days=0,
        show_temperature=True,
        show_humidity=True,
        show_wind=True,
        notification_enabled=False
    )


# === ТЕСТИ ДЛЯ КОРИСТУВАЧІВ ===

@pytest.mark.asyncio
async def test_get_or_create_user_new_user(mock_session, sample_user):
    """Тест створення нового користувача"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    with patch('db.crud.create_default_weather_settings', new_callable=AsyncMock):
        user = await get_or_create_user(
            mock_session,
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User",
            language_code="uk"
        )
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called()
    assert mock_session.refresh.called


@pytest.mark.asyncio
async def test_get_or_create_user_existing_user(mock_session, sample_user):
    """Тест отримання існуючого користувача"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_user
    mock_session.execute.return_value = mock_result
    
    user = await get_or_create_user(
        mock_session,
        telegram_id=123456789,
        username="newusername"
    )
    
    assert user.username == "newusername"
    mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_create_default_weather_settings(mock_session):
    """Тест створення дефолтних налаштувань"""
    settings = await create_default_weather_settings(mock_session, 123456789)
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()


# === ТЕСТИ ДЛЯ НАЛАШТУВАНЬ ПОГОДИ ===

@pytest.mark.asyncio
async def test_get_user_weather_settings_existing(mock_session, sample_settings):
    """Тест отримання існуючих налаштувань"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_settings
    mock_session.execute.return_value = mock_result
    
    settings = await get_user_weather_settings(mock_session, 123456789)
    
    assert settings.user_id == 123456789
    assert settings.location_name == "Kyiv"


@pytest.mark.asyncio
async def test_get_user_weather_settings_create_if_not_exists(mock_session):
    """Тест створення налаштувань, якщо їх немає"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    with patch('db.crud.get_or_create_user', new_callable=AsyncMock):
        with patch('db.crud.create_default_weather_settings', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = UserWeatherSettings(user_id=123456789)
            settings = await get_user_weather_settings(mock_session, 123456789)
            
            mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_location(mock_session, sample_settings):
    """Тест оновлення локації користувача"""
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        await update_user_location(
            mock_session,
            telegram_id=123456789,
            latitude=49.8397,
            longitude=24.0297,
            location_name="Lviv",
            elevation=296.0,
            timezone="Europe/Kiev"
        )
        
        assert sample_settings.latitude == 49.8397
        assert sample_settings.longitude == 24.0297
        assert sample_settings.location_name == "Lviv"
        assert sample_settings.elevation == 296.0
        mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_user_units(mock_session, sample_settings):
    """Тест оновлення одиниць виміру"""
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        await update_user_units(
            mock_session,
            telegram_id=123456789,
            temperature_unit="fahrenheit",
            wind_speed_unit="mph",
            precipitation_unit="inch",
            past_days=5
        )
        
        assert sample_settings.temperature_unit == "fahrenheit"
        assert sample_settings.wind_speed_unit == "mph"
        assert sample_settings.precipitation_unit == "inch"
        assert sample_settings.past_days == 5
        mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_toggle_display_setting(mock_session, sample_settings):
    """Тест перемикання налаштувань відображення"""
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        initial_value = sample_settings.show_temperature
        new_value = await toggle_display_setting(mock_session, 123456789, 'show_temperature')
        
        assert new_value != initial_value
        assert sample_settings.show_temperature == new_value
        mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_toggle_display_setting_invalid(mock_session, sample_settings):
    """Тест перемикання неіснуючого параметра"""
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        with pytest.raises(ValueError, match="Невідомий параметр"):
            await toggle_display_setting(mock_session, 123456789, 'invalid_setting')


@pytest.mark.asyncio
async def test_update_forecast_settings(mock_session, sample_settings):
    """Тест оновлення налаштувань прогнозу"""
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        await update_forecast_settings(
            mock_session,
            telegram_id=123456789,
            forecast_days=10,
            past_days=7
        )
        
        assert sample_settings.forecast_days == 10
        assert sample_settings.past_days == 7
        mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_notification_settings(mock_session, sample_settings):
    """Тест оновлення налаштувань сповіщень"""
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        await update_notification_settings(
            mock_session,
            telegram_id=123456789,
            notification_enabled=True,
            notification_time="08:30"
        )
        
        assert sample_settings.notification_enabled is True
        assert sample_settings.notification_time == "08:30"
        mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_notification_settings_invalid_time(mock_session, sample_settings):
    """Тест оновлення з некоректним часом"""
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        with pytest.raises(ValueError, match="Час повинен бути у форматі HH:MM"):
            await update_notification_settings(
                mock_session,
                telegram_id=123456789,
                notification_time="25:99"
            )


# === ТЕСТИ ДЛЯ API ПАРАМЕТРІВ ===

@pytest.mark.asyncio
async def test_get_api_parameters(mock_session, sample_settings):
    """Тест отримання параметрів API"""
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        params = await get_api_parameters(mock_session, 123456789)
        
        assert params['latitude'] == 50.4501
        assert params['longitude'] == 30.5234
        assert params['temperature_unit'] == 'celsius'
        assert 'hourly' in params
        assert 'temperature_2m' in params['hourly']


@pytest.mark.asyncio
async def test_get_api_parameters_no_location(mock_session, sample_settings):
    """Тест отримання параметрів без локації"""
    sample_settings.latitude = None
    sample_settings.longitude = None
    
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        with pytest.raises(ValueError, match="Локація не встановлена"):
            await get_api_parameters(mock_session, 123456789)


# === ТЕСТИ ДЛЯ ПОВІДОМЛЕНЬ ===

@pytest.mark.asyncio
async def test_save_user_message(mock_session):
    """Тест збереження повідомлення користувача"""
    await save_user_message(
        mock_session,
        telegram_id=123456789,
        chat_id=987654321,
        message_text="Яка погода?",
        location_requested="Kyiv",
        weather_response="Сонячно, +20°C"
    )
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called()


# === ТЕСТИ ДЛЯ ЧАТІВ ===

@pytest.mark.asyncio
async def test_normalize_chat_id_negative():
    """Тест нормалізації від'ємного ID чату"""
    result = await normalize_chat_id(-1001234567890)
    assert result == -1001234567890 + 10**12


@pytest.mark.asyncio
async def test_normalize_chat_id_positive():
    """Тест нормалізації позитивного ID чату"""
    result = await normalize_chat_id(123456789)
    assert result == 123456789


@pytest.mark.asyncio
async def test_save_chat_to_db_new_chat(mock_session):
    """Тест збереження нового чату"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    await save_chat_to_db(
        mock_session,
        chat_id=123456789,
        chat_type="group",
        title="Test Group"
    )
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_save_chat_to_db_existing_chat(mock_session):
    """Тест оновлення існуючого чату"""
    existing_chat = BotChat(
        chat_id=123456789,
        chat_type="group",
        title="Old Title",
        is_active=False
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_chat
    mock_session.execute.return_value = mock_result
    
    await save_chat_to_db(
        mock_session,
        chat_id=123456789,
        chat_type="group",
        title="New Title"
    )
    
    assert existing_chat.title == "New Title"
    assert existing_chat.is_active is True
    mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_track_chat_member_update_added(mock_session):
    """Тест додавання бота до чату"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    await track_chat_member_update(
        mock_session,
        chat_id=123456789,
        chat_type="group",
        new_status="member",
        old_status="left"
    )
    
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_track_chat_member_update_removed(mock_session):
    """Тест видалення бота з чату"""
    existing_chat = BotChat(
        chat_id=123456789,
        chat_type="group",
        is_active=True
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_chat
    mock_session.execute.return_value = mock_result
    
    await track_chat_member_update(
        mock_session,
        chat_id=123456789,
        chat_type="group",
        new_status="kicked"
    )
    
    assert existing_chat.is_active is False
    mock_session.commit.assert_called()


# === ТЕСТИ ДЛЯ ЗВІТНОСТІ ===

@pytest.mark.asyncio
async def test_get_user_settings_summary(mock_session, sample_settings):
    """Тест отримання сумарної інформації про налаштування"""
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        summary = await get_user_settings_summary(mock_session, 123456789)
        
        assert "Kyiv" in summary
        assert "celsius" in summary
        assert "7 днів" in summary


# === ТЕСТИ ДЛЯ LEGACY ФУНКЦІЙ ===

@pytest.mark.asyncio
async def test_get_settings(mock_session, sample_settings):
    """Тест отримання налаштувань (legacy)"""
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        settings = await get_settings(mock_session, 123456789)
        
        assert settings['temperature_unit'] == 'celsius'
        assert settings['location_name'] == 'Kyiv'


@pytest.mark.asyncio
async def test_update_setting(mock_session, sample_settings):
    """Тест оновлення налаштування (legacy)"""
    with patch('db.crud.get_user_weather_settings', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_settings
        
        await update_setting(mock_session, 123456789, 'temperature_unit', 'fahrenheit')
        
        assert sample_settings.temperature_unit == 'fahrenheit'
        mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_get_user_state(mock_session):
    """Тест отримання стану користувача"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = "waiting_for_location"
    mock_session.execute.return_value = mock_result
    
    state = await get_user_state(mock_session, 123456789)
    
    assert state == "waiting_for_location"


@pytest.mark.asyncio
async def test_set_user_state(mock_session):
    """Тест встановлення стану користувача"""
    await set_user_state(mock_session, 123456789, "waiting_for_time")
    
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_save_notification_time(mock_session, sample_settings):
    """Тест збереження часу сповіщень"""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = sample_settings
    mock_session.execute.return_value = mock_result
    
    await save_notification_time(mock_session, 123456789, "09:00")
    
    assert sample_settings.notification_time == "09:00"
    assert sample_settings.notification_enabled is True
    mock_session.commit.assert_called()