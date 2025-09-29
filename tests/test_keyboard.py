import pytest
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.keyboards import WeatherKeyboards, InlineKeyboards


class TestMainMenu:
    """Тести для головного меню"""
    
    def test_main_menu_structure(self):
        """Перевірка структури головного меню"""
        keyboard = WeatherKeyboards.main_menu()
        
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 4
        
        # Перевірка першого рядка
        assert len(keyboard.inline_keyboard[0]) == 1
        assert keyboard.inline_keyboard[0][0].text == "🌦️ Поточна погода"
        assert keyboard.inline_keyboard[0][0].callback_data == "weather:current"
    
    def test_main_menu_buttons_count(self):
        """Перевірка кількості кнопок"""
        keyboard = WeatherKeyboards.main_menu()
        
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 6
    
    def test_main_menu_callback_data(self):
        """Перевірка всіх callback_data"""
        keyboard = WeatherKeyboards.main_menu()
        all_callbacks = []
        
        for row in keyboard.inline_keyboard:
            for button in row:
                all_callbacks.append(button.callback_data)
        
        expected = [
            "weather:current",
            "weather:weekly",
            "weather:hourly",
            "menu:settings",
            "action:change_location",
            "action:help"
        ]
        assert all_callbacks == expected


class TestSettingsMenu:
    """Тести для меню налаштувань"""
    
    def test_settings_menu_structure(self):
        """Перевірка структури меню налаштувань"""
        keyboard = WeatherKeyboards.settings_menu()
        
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 7
    
    def test_settings_menu_has_back_button(self):
        """Перевірка наявності кнопки назад"""
        keyboard = WeatherKeyboards.settings_menu()
        
        last_button = keyboard.inline_keyboard[-1][0]
        assert last_button.text == "⬅️ Назад"
        assert last_button.callback_data == "menu:main"
    
    def test_settings_menu_all_options(self):
        """Перевірка всіх опцій налаштувань"""
        keyboard = WeatherKeyboards.settings_menu()
        
        expected_texts = [
            "📍 Локація та часовий пояс",
            "📏 Одиниці виміру",
            "📊 Що відображати",
            "📅 Налаштування прогнозу",
            "🔔 Сповіщення",
            "📋 Мої налаштування",
            "⬅️ Назад"
        ]
        
        actual_texts = [row[0].text for row in keyboard.inline_keyboard]
        assert actual_texts == expected_texts


class TestTemperatureUnitSelector:
    """Тести для вибору одиниць температури"""
    
    def test_celsius_selected(self):
        """Тест коли обрано Цельсій"""
        keyboard = WeatherKeyboards.temperature_unit_selector(current='celsius')
        
        celsius_button = keyboard.inline_keyboard[0][0]
        fahrenheit_button = keyboard.inline_keyboard[1][0]
        
        assert "✅" in celsius_button.text
        assert "⚪" in fahrenheit_button.text
        assert celsius_button.callback_data == "set_unit:temperature_unit:celsius"
    
    def test_fahrenheit_selected(self):
        """Тест коли обрано Фаренгейт"""
        keyboard = WeatherKeyboards.temperature_unit_selector(current='fahrenheit')
        
        celsius_button = keyboard.inline_keyboard[0][0]
        fahrenheit_button = keyboard.inline_keyboard[1][0]
        
        assert "⚪" in celsius_button.text
        assert "✅" in fahrenheit_button.text
        assert fahrenheit_button.callback_data == "set_unit:temperature_unit:fahrenheit"
    
    def test_has_back_button(self):
        """Перевірка кнопки назад"""
        keyboard = WeatherKeyboards.temperature_unit_selector()
        
        back_button = keyboard.inline_keyboard[-1][0]
        assert back_button.text == "⬅️ Назад"
        assert back_button.callback_data == "settings:units"


class TestWindSpeedUnitSelector:
    """Тести для вибору одиниць швидкості вітру"""
    
    def test_all_options_present(self):
        """Перевірка наявності всіх опцій"""
        keyboard = WeatherKeyboards.wind_speed_unit_selector()
        
        # 4 опції + кнопка назад
        assert len(keyboard.inline_keyboard) == 5
    
    def test_kmh_selected(self):
        """Тест коли обрано км/год"""
        keyboard = WeatherKeyboards.wind_speed_unit_selector(current='kmh')
        
        kmh_button = keyboard.inline_keyboard[0][0]
        assert "✅" in kmh_button.text
        assert "км/год" in kmh_button.text
        assert kmh_button.callback_data == "set_unit:wind_speed_unit:kmh"
    
    def test_ms_selected(self):
        """Тест коли обрано м/с"""
        keyboard = WeatherKeyboards.wind_speed_unit_selector(current='ms')
        
        ms_button = keyboard.inline_keyboard[1][0]
        assert "✅" in ms_button.text
        assert "м/с" in ms_button.text
    
    def test_all_callback_data(self):
        """Перевірка всіх callback_data"""
        keyboard = WeatherKeyboards.wind_speed_unit_selector()
        
        expected_units = ['kmh', 'ms', 'mph', 'kn']
        for i, unit in enumerate(expected_units):
            button = keyboard.inline_keyboard[i][0]
            assert button.callback_data == f"set_unit:wind_speed_unit:{unit}"


class TestForecastDaysSelector:
    """Тести для вибору кількості днів прогнозу"""
    
    def test_all_options_present(self):
        """Перевірка наявності всіх опцій"""
        keyboard = WeatherKeyboards.forecast_days_selector()
        
        # 7 опцій + кнопка назад
        assert len(keyboard.inline_keyboard) == 8
    
    def test_current_day_selected(self):
        """Тест позначки поточного вибору"""
        keyboard = WeatherKeyboards.forecast_days_selector(current=7)
        
        # Знаходимо кнопку з 7 днями (індекс залежить від порядку)
        found_selected = False
        for row in keyboard.inline_keyboard[:-1]:  # Без кнопки назад
            button = row[0]
            if "7 днів" in button.text:
                assert "✅" in button.text
                found_selected = True
                break
        
        assert found_selected, "Не знайдено обраний варіант"
    
    def test_days_options(self):
        """Перевірка всіх варіантів днів"""
        keyboard = WeatherKeyboards.forecast_days_selector()
        
        expected_days = [1, 3, 5, 7, 10, 14, 16]
        for i, days in enumerate(expected_days):
            button = keyboard.inline_keyboard[i][0]
            assert button.callback_data == f"set_forecast:days:{days}"
    
    def test_correct_word_forms(self):
        """Перевірка правильних форм слова 'день'"""
        keyboard = WeatherKeyboards.forecast_days_selector()
        
        # 1 день, 3 дні, 7 днів
        buttons_text = [row[0].text for row in keyboard.inline_keyboard[:-1]]
        
        assert any("1 день" in text for text in buttons_text)
        assert any("3 дні" in text for text in buttons_text)
        assert any("7 днів" in text for text in buttons_text)


class TestPastDaysSelector:
    """Тести для вибору минулих днів"""
    
    def test_zero_days_option(self):
        """Тест опції 'немає' для 0 днів"""
        keyboard = WeatherKeyboards.forecast_past_days_selector(current=0)
        
        zero_button = keyboard.inline_keyboard[0][0]
        assert "✅" in zero_button.text
        assert "немає" in zero_button.text
        assert zero_button.callback_data == "set_forecast:past_days:0"
    
    def test_all_options(self):
        """Перевірка всіх опцій"""
        keyboard = WeatherKeyboards.forecast_past_days_selector()
        
        expected_days = [0, 1, 2, 3, 5, 7]
        assert len(keyboard.inline_keyboard) == len(expected_days) + 1  # +1 для кнопки назад
    
    def test_correct_pluralization(self):
        """Перевірка правильного відмінювання"""
        keyboard = WeatherKeyboards.forecast_past_days_selector()
        
        buttons_text = [row[0].text for row in keyboard.inline_keyboard[:-1]]
        
        assert any("1 день" in text for text in buttons_text)
        assert any("2 дні" in text for text in buttons_text)
        assert any("5 днів" in text for text in buttons_text)


class TestDisplaySettings:
    """Тести для налаштувань відображення"""
    
    def test_default_settings(self):
        """Тест з дефолтними налаштуваннями"""
        keyboard = WeatherKeyboards.display_settings()
        
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) > 0
    
    def test_enabled_setting(self):
        """Тест коли налаштування увімкнено"""
        settings = {'show_temperature': True}
        keyboard = WeatherKeyboards.display_settings(settings)
        
        # Шукаємо кнопку температури
        temp_button = None
        for row in keyboard.inline_keyboard:
            if row and "Температура" in row[0].text:
                temp_button = row[0]
                break
        
        assert temp_button is not None
        assert "✅" in temp_button.text
        assert temp_button.callback_data == "toggle:show_temperature"
    
    def test_disabled_setting(self):
        """Тест коли налаштування вимкнено"""
        settings = {'show_temperature': False}
        keyboard = WeatherKeyboards.display_settings(settings)
        
        temp_button = None
        for row in keyboard.inline_keyboard:
            if row and "Температура" in row[0].text:
                temp_button = row[0]
                break
        
        assert temp_button is not None
        assert "❌" in temp_button.text
    
    def test_section_headers(self):
        """Перевірка наявності заголовків секцій"""
        keyboard = WeatherKeyboards.display_settings()
        
        headers = [row[0].text for row in keyboard.inline_keyboard 
                  if row and row[0].callback_data == "noop"]
        
        assert "поточній погоді" in headers[0]
        assert "Денний прогноз" in headers[1]


class TestNotificationsSettings:
    """Тести для налаштувань сповіщень"""
    
    def test_notifications_disabled(self):
        """Тест коли сповіщення вимкнені"""
        settings = {'notification_enabled': False}
        keyboard = WeatherKeyboards.notifications_settings(settings)
        
        # Коли вимкнено, не повинно бути кнопки часу
        time_buttons = [row for row in keyboard.inline_keyboard 
                       if row and "Час сповіщень" in row[0].text]
        
        assert len(time_buttons) == 0
    
    def test_notifications_enabled(self):
        """Тест коли сповіщення увімкнені"""
        settings = {'notification_enabled': True, 'notification_time': '08:00'}
        keyboard = WeatherKeyboards.notifications_settings(settings)
        
        # Коли увімкнено, повинна бути кнопка часу
        time_buttons = [row for row in keyboard.inline_keyboard 
                       if row and "Час сповіщень" in row[0].text]
        
        assert len(time_buttons) == 1
        assert "08:00" in time_buttons[0][0].text
    
    def test_enabled_toggle_emoji(self):
        """Перевірка емодзі для увімкнених сповіщень"""
        settings = {'notification_enabled': True}
        keyboard = WeatherKeyboards.notifications_settings(settings)
        
        toggle_button = keyboard.inline_keyboard[0][0]
        assert "✅" in toggle_button.text
        assert toggle_button.callback_data == "toggle:notification_enabled"
    
    def test_disabled_toggle_emoji(self):
        """Перевірка емодзі для вимкнених сповіщень"""
        settings = {'notification_enabled': False}
        keyboard = WeatherKeyboards.notifications_settings(settings)
        
        toggle_button = keyboard.inline_keyboard[0][0]
        assert "❌" in toggle_button.text


class TestTimezoneSelector:
    """Тести для вибору часового поясу"""
    
    def test_auto_option_first(self):
        """Перевірка що автоматичний вибір йде першим"""
        keyboard = WeatherKeyboards.timezone_selector()
        
        first_button = keyboard.inline_keyboard[0][0]
        assert first_button.text == "🌐 Автоматично"
        assert first_button.callback_data == "set_timezone:auto"
    
    def test_all_timezones_present(self):
        """Перевірка наявності основних часових поясів"""
        keyboard = WeatherKeyboards.timezone_selector()
        
        expected_timezones = [
            "auto",
            "Europe/Kyiv",
            "GMT",
            "America/New_York",
            "Europe/London",
            "Europe/Berlin",
            "Asia/Tokyo"
        ]
        
        callbacks = [row[0].callback_data.replace("set_timezone:", "") 
                    for row in keyboard.inline_keyboard[:-1]]
        
        assert callbacks == expected_timezones
    
    def test_has_back_button(self):
        """Перевірка кнопки назад"""
        keyboard = WeatherKeyboards.timezone_selector()
        
        last_button = keyboard.inline_keyboard[-1][0]
        assert last_button.callback_data == "settings:location"


class TestUnitsSettings:
    """Тести для налаштувань одиниць виміру"""
    
    def test_default_units(self):
        """Тест з дефолтними одиницями"""
        keyboard = WeatherKeyboards.units_settings()
        
        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 5
    
    def test_celsius_display(self):
        """Перевірка відображення Цельсія"""
        units = {
            'temperature_unit': 'celsius',
            'wind_speed_unit': 'kmh',
            'precipitation_unit': 'mm',
            'timeformat': 'iso8601'
        }
        keyboard = WeatherKeyboards.units_settings(units)
        
        temp_button = keyboard.inline_keyboard[0][0]
        assert "🌡️C" in temp_button.text
    
    def test_fahrenheit_display(self):
        """Перевірка відображення Фаренгейта"""
        units = {
            'temperature_unit': 'fahrenheit',
            'wind_speed_unit': 'kmh',
            'precipitation_unit': 'mm',
            'timeformat': 'iso8601'
        }
        keyboard = WeatherKeyboards.units_settings(units)
        
        temp_button = keyboard.inline_keyboard[0][0]
        assert "🌡️F" in temp_button.text
    
    def test_wind_speed_units_display(self):
        """Перевірка відображення одиниць швидкості вітру"""
        units = {
            'temperature_unit': 'celsius',
            'wind_speed_unit': 'ms',
            'precipitation_unit': 'mm',
            'timeformat': 'iso8601'
        }
        keyboard = WeatherKeyboards.units_settings(units)
        
        wind_button = keyboard.inline_keyboard[1][0]
        assert "м/с" in wind_button.text


class TestWeatherTypeMenu:
    """Тести для меню типів погоди"""
    
    def test_menu_structure(self):
        """Перевірка структури меню"""
        keyboard = WeatherKeyboards.weather_type_menu()
        
        assert len(keyboard.inline_keyboard) == 6
    
    def test_all_weather_types(self):
        """Перевірка всіх типів погоди"""
        keyboard = WeatherKeyboards.weather_type_menu()
        
        expected_callbacks = [
            "weather:current",
            "weather:today",
            "weather:3days",
            "weather:weekly",
            "weather:hourly",
            "menu:main"
        ]
        
        actual_callbacks = [row[0].callback_data for row in keyboard.inline_keyboard]
        assert actual_callbacks == expected_callbacks


class TestConfirmationDialog:
    """Тести для діалогу підтвердження"""
    
    def test_yes_no_buttons(self):
        """Перевірка кнопок Так/Ні"""
        keyboard = WeatherKeyboards.confirmation_dialog("delete", "location")
        
        assert len(keyboard.inline_keyboard) == 1
        assert len(keyboard.inline_keyboard[0]) == 2
        
        yes_button = keyboard.inline_keyboard[0][0]
        no_button = keyboard.inline_keyboard[0][1]
        
        assert yes_button.text == "✅ Так"
        assert no_button.text == "❌ Ні"
    
    def test_callback_data_format(self):
        """Перевірка формату callback_data"""
        keyboard = WeatherKeyboards.confirmation_dialog("reset", "settings")
        
        yes_button = keyboard.inline_keyboard[0][0]
        assert yes_button.callback_data == "confirm:reset:settings"


class TestBackButton:
    """Тести для кнопки назад"""
    
    def test_default_callback(self):
        """Тест дефолтного callback"""
        keyboard = WeatherKeyboards.back_button()
        
        button = keyboard.inline_keyboard[0][0]
        assert button.text == "⬅️ Назад"
        assert button.callback_data == "menu:main"
    
    def test_custom_callback(self):
        """Тест кастомного callback"""
        keyboard = WeatherKeyboards.back_button("settings:display")
        
        button = keyboard.inline_keyboard[0][0]
        assert button.callback_data == "settings:display"


class TestLocationInputHelp:
    """Тести для допомоги з введенням локації"""
    
    def test_has_share_button(self):
        """Перевірка кнопки поділитися локацією"""
        keyboard = WeatherKeyboards.location_input_help()
        
        share_button = keyboard.inline_keyboard[0][0]
        assert "геолокацію" in share_button.text
        assert share_button.callback_data == "location:share"
    
    def test_has_back_button(self):
        """Перевірка кнопки назад"""
        keyboard = WeatherKeyboards.location_input_help()
        
        back_button = keyboard.inline_keyboard[1][0]
        assert back_button.callback_data == "settings:location"


class TestAdvancedDisplaySettings:
    """Тести для розширених налаштувань відображення"""
    
    def test_default_all_disabled(self):
        """Тест що всі розширені опції за замовчуванням вимкнені"""
        keyboard = WeatherKeyboards.advanced_display_settings()
        
        # Перший рядок - заголовок
        for row in keyboard.inline_keyboard[1:-1]:  # Без заголовка та кнопки назад
            button = row[0]
            if button.callback_data != "noop":
                assert "❌" in button.text
    
    def test_enabled_options(self):
        """Тест увімкнених опцій"""
        settings = {
            'show_dew_point': True,
            'show_solar_radiation': True
        }
        keyboard = WeatherKeyboards.advanced_display_settings(settings)
        
        enabled_count = sum(1 for row in keyboard.inline_keyboard 
                          if row and "✅" in row[0].text)
        
        assert enabled_count == 2


class TestBackwardCompatibility:
    """Тести сумісності зі старим кодом"""
    
    def test_inline_keyboards_alias(self):
        """Перевірка що InlineKeyboards працює як alias"""
        keyboard1 = WeatherKeyboards.main_menu()
        keyboard2 = InlineKeyboards.main_menu()
        
        assert keyboard1.inline_keyboard == keyboard2.inline_keyboard
    
    def test_all_methods_available(self):
        """Перевірка доступності всіх методів через alias"""
        methods = [
            'main_menu',
            'settings_menu',
            'temperature_unit_selector',
            'back_button'
        ]
        
        for method in methods:
            assert hasattr(InlineKeyboards, method)


class TestForecastSettings:
    """Тести для налаштувань прогнозу"""
    
    def test_default_values(self):
        """Перевірка дефолтних значень"""
        keyboard = WeatherKeyboards.forecast_settings()
        
        # Шукаємо кнопку з днями прогнозу
        days_button = keyboard.inline_keyboard[0][0]
        assert "7" in days_button.text
        
        # Шукаємо кнопку з минулими днями
        past_button = keyboard.inline_keyboard[1][0]
        assert "0" in past_button.text
    
    def test_custom_values(self):
        """Тест з кастомними значеннями"""
        settings = {'forecast_days': 14, 'past_days': 5}
        keyboard = WeatherKeyboards.forecast_settings(settings)
        
        days_button = keyboard.inline_keyboard[0][0]
        past_button = keyboard.inline_keyboard[1][0]
        
        assert "14" in days_button.text
        assert "5" in past_button.text


class TestTimeformatSelector:
    """Тести для вибору формату часу"""
    
    def test_iso8601_selected(self):
        """Тест коли обрано ISO8601"""
        keyboard = WeatherKeyboards.timeformat_unit_selector(current='iso8601')
        
        iso_button = keyboard.inline_keyboard[0][0]
        assert "✅" in iso_button.text
        assert "ISO8601" in iso_button.text
    
    def test_unixtime_selected(self):
        """Тест коли обрано Unix Timestamp"""
        keyboard = WeatherKeyboards.timeformat_unit_selector(current='unixtime')
        
        unix_button = keyboard.inline_keyboard[1][0]
        assert "✅" in unix_button.text
        assert "Unix Timestamp" in unix_button.text
    
    def test_callback_data(self):
        """Перевірка callback_data"""
        keyboard = WeatherKeyboards.timeformat_unit_selector()
        
        iso_button = keyboard.inline_keyboard[0][0]
        unix_button = keyboard.inline_keyboard[1][0]
        
        assert iso_button.callback_data == "set_unit:timeformat:iso8601"
        assert unix_button.callback_data == "set_unit:timeformat:unixtime"