# services/weather.py - Покращений сервіс для роботи з Open-Meteo API

import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from bot.logger_config import logger


class WeatherAPIError(Exception):
    """Помилка API погоди"""

    pass


class WeatherService:
    """Сервіс для роботи з Open-Meteo API"""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    @staticmethod
    async def get_weather(
        latitude: float, longitude: float, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Отримати дані про погоду з Open-Meteo API

        Args:
            latitude: Широта
            longitude: Довгота
            params: Параметри API запиту

        Returns:
            Dict з даними про погоду

        Raises:
            WeatherAPIError: При помилці отримання даних
        """
        # Додаткова валідація типів
        if not isinstance(latitude, (float, int)) or not isinstance(
            longitude, (float, int)
        ):
            logger.warning(
                f"Некоректний тип координат: latitude={latitude}, longitude={longitude}"
            )
            raise WeatherAPIError("Координати мають бути числами")
        if not isinstance(params, dict):
            logger.warning(f"Некоректний тип параметрів: {params}")
            raise WeatherAPIError("Параметри мають бути словником")

        try:
            # Підготовка параметрів запиту
            api_params = {"latitude": latitude, "longitude": longitude, **params}

            # Перевірка наявності обов'язкових параметрів
            if not (-90 <= float(latitude) <= 90) or not (
                -180 <= float(longitude) <= 180
            ):
                logger.warning(
                    f"Координати поза межами: latitude={latitude}, longitude={longitude}"
                )
                raise WeatherAPIError("Координати поза допустимими межами")

            logger.info(
                f"Запит погоди для {latitude}, {longitude} з параметрами: {api_params}"
            )

            # Виконання HTTP запиту
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(WeatherService.BASE_URL, params=api_params)
                response.raise_for_status()

                data = response.json()

                # Перевіряємо наявність помилки в відповіді
                if "error" in data:
                    logger.error(f"Open-Meteo API повернув помилку: {data['error']}")
                    raise WeatherAPIError(f"API помилка: {data['error']}")

                # Логування успішної відповіді
                logger.info(f"Успішно отримано дані погоди для {latitude}, {longitude}")

                return data

        except httpx.TimeoutException:
            error_msg = "Перевищено час очікування відповіді від сервера погоди"
            logger.error(error_msg)
            raise WeatherAPIError(error_msg)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                error_msg = "Некоректні параметри запиту до API погоди"
            elif e.response.status_code == 429:
                error_msg = "Перевищено ліміт запитів до API погоди. Спробуйте пізніше"
            elif e.response.status_code >= 500:
                error_msg = "Проблема з сервером погоди. Спробуйте пізніше"
            else:
                error_msg = f"Помилка HTTP {e.response.status_code}"

            logger.error(
                f"HTTP помилка при запиті погоди: {e.response.status_code}, details: {e.response.text}"
            )
            raise WeatherAPIError(error_msg)

        except httpx.RequestError as e:
            error_msg = "Помилка мережі при отриманні даних про погоду"
            logger.error(f"Мережева помилка: {str(e)}")
            raise WeatherAPIError(error_msg)

        except ValueError as ve:
            logger.error(f"Валідаційна помилка: {str(ve)}")
            raise WeatherAPIError(str(ve))

        except Exception as e:
            error_msg = f"Несподівана помилка при отриманні погоди: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise WeatherAPIError("Технічна помилка. Спробуйте пізніше")

    @staticmethod
    def validate_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валідація та очищення параметрів API

        Args:
            params: Вхідні параметри

        Returns:
            Очищені параметри
        """
        clean_params = {}

        # Обов'язкові параметри
        if "latitude" not in params or "longitude" not in params:
            logger.warning(f"Відсутні координати у параметрах: {params}")
            raise ValueError("Широта та довгота обов'язкові")

        try:
            clean_params["latitude"] = float(params["latitude"])
            clean_params["longitude"] = float(params["longitude"])
        except Exception:
            logger.warning(f"Некоректний тип координат: {params}")
            raise ValueError("Координати мають бути числами")

        # Валідація координат
        if not (-90 <= clean_params["latitude"] <= 90):
            logger.warning(f"Широта поза межами: {clean_params['latitude']}")
            raise ValueError("Широта повинна бути між -90 та 90")
        if not (-180 <= clean_params["longitude"] <= 180):
            logger.warning(f"Довгота поза межами: {clean_params['longitude']}")
            raise ValueError("Довгота повинна бути між -180 та 180")

        # Опціональні параметри з валідацією
        if "elevation" in params and params["elevation"] is not None:
            try:
                elevation = float(params["elevation"])
                if -1000 <= elevation <= 9000:
                    clean_params["elevation"] = elevation
                else:
                    logger.warning(f"Висота поза межами: {elevation}")
            except Exception:
                logger.warning(f"Некоректна висота: {params['elevation']}")

        if "forecast_days" in params:
            try:
                days = int(params["forecast_days"])
                if 1 <= days <= 16:
                    clean_params["forecast_days"] = days
                else:
                    clean_params["forecast_days"] = 7
            except Exception:
                logger.warning(f"Некоректний forecast_days: {params['forecast_days']}")
                clean_params["forecast_days"] = 7

        if "past_days" in params:
            try:
                days = int(params["past_days"])
                if 0 <= days <= 92:
                    clean_params["past_days"] = days
            except Exception:
                logger.warning(f"Некоректний past_days: {params['past_days']}")

        # Одиниці виміру
        valid_temp_units = ["celsius", "fahrenheit"]
        if params.get("temperature_unit") in valid_temp_units:
            clean_params["temperature_unit"] = params["temperature_unit"]
        elif "temperature_unit" in params:
            logger.warning(
                f"Некоректна одиниця температури: {params.get('temperature_unit')}"
            )

        valid_wind_units = ["kmh", "ms", "mph", "kn"]
        if params.get("wind_speed_unit") in valid_wind_units:
            clean_params["wind_speed_unit"] = params["wind_speed_unit"]
        elif "wind_speed_unit" in params:
            logger.warning(
                f"Некоректна одиниця швидкості вітру: {params.get('wind_speed_unit')}"
            )

        valid_precip_units = ["mm", "inch"]
        if params.get("precipitation_unit") in valid_precip_units:
            clean_params["precipitation_unit"] = params["precipitation_unit"]
        elif "precipitation_unit" in params:
            logger.warning(
                f"Некоректна одиниця опадів: {params.get('precipitation_unit')}"
            )

        valid_timeformats = ["iso8601", "unixtime"]
        if params.get("timeformat") in valid_timeformats:
            clean_params["timeformat"] = params["timeformat"]
        elif "timeformat" in params:
            logger.warning(f"Некоректний формат часу: {params.get('timeformat')}")

        # Часовий пояс
        if "timezone" in params and params["timezone"]:
            clean_params["timezone"] = str(params["timezone"])

        # Параметри погодних змінних
        for param_type in ["hourly", "daily", "current"]:
            if param_type in params and params[param_type]:
                if isinstance(params[param_type], str):
                    clean_params[param_type] = params[param_type]
                elif isinstance(params[param_type], list):
                    clean_params[param_type] = ",".join(params[param_type])
                else:
                    logger.warning(
                        f"Некоректний тип параметра {param_type}: {params[param_type]}"
                    )

        return clean_params


class WeatherFormatter:
    """Клас для форматування даних про погоду"""

    # Словник для перекладу кодів погоди
    WEATHER_CODES = {
        0: {"description": "Ясно", "emoji": "☀️"},
        1: {"description": "Переважно ясно", "emoji": "🌤️"},
        2: {"description": "Частково хмарно", "emoji": "⛅"},
        3: {"description": "Хмарно", "emoji": "☁️"},
        45: {"description": "Туман", "emoji": "🌫️"},
        48: {"description": "Іней", "emoji": "🌫️"},
        51: {"description": "Легка мряка", "emoji": "🌦️"},
        53: {"description": "Помірна мряка", "emoji": "🌦️"},
        55: {"description": "Густа мряка", "emoji": "🌦️"},
        56: {"description": "Легкий крижаний дощ", "emoji": "🌨️"},
        57: {"description": "Крижаний дощ", "emoji": "🌨️"},
        61: {"description": "Легкий дощ", "emoji": "🌦️"},
        63: {"description": "Помірний дощ", "emoji": "🌧️"},
        65: {"description": "Сильний дощ", "emoji": "🌧️"},
        66: {"description": "Легкий дощ зі снігом", "emoji": "🌨️"},
        67: {"description": "Дощ зі снігом", "emoji": "🌨️"},
        71: {"description": "Легкий сніг", "emoji": "❄️"},
        73: {"description": "Помірний сніг", "emoji": "❄️"},
        75: {"description": "Сильний сніг", "emoji": "❄️"},
        77: {"description": "Снігові зерна", "emoji": "❄️"},
        80: {"description": "Легкі зливи", "emoji": "🌦️"},
        81: {"description": "Помірні зливи", "emoji": "⛈️"},
        82: {"description": "Сильні зливи", "emoji": "⛈️"},
        85: {"description": "Легкий снігопад", "emoji": "❄️"},
        86: {"description": "Сильний снігопад", "emoji": "❄️"},
        95: {"description": "Гроза", "emoji": "⛈️"},
        96: {"description": "Гроза з легким градом", "emoji": "⛈️"},
        99: {"description": "Гроза з сильним градом", "emoji": "⛈️"},
    }

    @staticmethod
    def get_weather_description(weather_code: int) -> Dict[str, str]:
        """Отримати опис погоди за кодом"""
        return WeatherFormatter.WEATHER_CODES.get(
            weather_code, {"description": f"Код {weather_code}", "emoji": "❓"}
        )

    @staticmethod
    def format_temperature(temp: float, unit: str = "celsius") -> str:
        """Форматування температури"""
        if temp is None:
            return "N/A"

        symbol = "°C" if unit == "celsius" else "°F"
        return f"{temp:.1f}{symbol}"

    @staticmethod
    def format_wind(speed: float, direction: int, unit: str = "kmh") -> str:
        """Форматування вітру"""
        if speed is None:
            return "N/A"

        # Одиниці виміру
        unit_symbols = {"kmh": "км/год", "ms": "м/с", "mph": "миль/год", "kn": "вузли"}
        unit_symbol = unit_symbols.get(unit, unit)

        # Напрямок вітру
        directions = [
            "Пн",
            "ПнПнСх",
            "ПнСх",
            "СхПнСх",
            "Сх",
            "СхПдСх",
            "ПдСх",
            "ПдПдСх",
            "Пд",
            "ПдПдЗх",
            "ПдЗх",
            "ЗхПдЗх",
            "Зх",
            "ЗхПнЗх",
            "ПнЗх",
            "ПнПнЗх",
        ]

        direction_text = ""
        if direction is not None:
            index = int((direction + 11.25) / 22.5) % 16
            direction_text = f" {directions[index]}"

        return f"{speed:.1f} {unit_symbol}{direction_text}"

    @staticmethod
    def format_humidity(humidity: float) -> str:
        """Форматування вологості"""
        if humidity is None:
            return "N/A"
        return f"{humidity:.0f}%"

    @staticmethod
    def format_pressure(pressure: float) -> str:
        """Форматування тиску"""
        if pressure is None:
            return "N/A"
        return f"{pressure:.0f} hPa"

    @staticmethod
    def format_precipitation(precip: float, unit: str = "mm") -> str:
        """Форматування опадів"""
        if precip is None or precip == 0:
            return "0 мм"

        unit_symbol = "мм" if unit == "mm" else "дюйм"
        return f"{precip:.1f} {unit_symbol}"

    @staticmethod
    def format_datetime(dt_str: str, format_type: str = "date") -> str:
        """Форматування дати та часу"""
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

            if format_type == "date":
                return dt.strftime("%d.%m.%Y")
            elif format_type == "time":
                return dt.strftime("%H:%M")
            elif format_type == "datetime":
                return dt.strftime("%d.%m.%Y %H:%M")
            elif format_type == "weekday":
                weekdays = {
                    0: "Понеділок",
                    1: "Вівторок",
                    2: "Середа",
                    3: "Четвер",
                    4: "П'ятниця",
                    5: "Субота",
                    6: "Неділя",
                }
                return weekdays.get(dt.weekday(), "Невідомо")

        except Exception:
            return dt_str


# Функція для зворотної сумісності
async def get_weather(
    latitude: float, longitude: float, params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Функція для зворотної сумісності з існуючим кодом

    Args:
        latitude: Широта
        longitude: Довгота
        params: Параметри запиту

    Returns:
        Dict з даними про погоду
    """
    validated_params = WeatherService.validate_parameters(
        {"latitude": latitude, "longitude": longitude, **params}
    )

    return await WeatherService.get_weather(latitude, longitude, validated_params)
