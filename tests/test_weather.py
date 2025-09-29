import httpx
import pytest
from services.weather import WeatherService, WeatherFormatter, WeatherAPIError
import asyncio
from unittest.mock import patch, AsyncMock

# --- WeatherService.validate_parameters tests ---


def test_validate_parameters_valid_minimal():
    params = {"latitude": 50.45, "longitude": 30.52}
    result = WeatherService.validate_parameters(params)
    assert result["latitude"] == 50.45
    assert result["longitude"] == 30.52


def test_validate_parameters_invalid_latitude_type():
    params = {"latitude": "not_a_float", "longitude": 30.52}
    with pytest.raises(ValueError):
        WeatherService.validate_parameters(params)


def test_validate_parameters_missing_latitude():
    params = {"longitude": 30.52}
    with pytest.raises(ValueError):
        WeatherService.validate_parameters(params)


def test_validate_parameters_latitude_out_of_bounds():
    params = {"latitude": 100, "longitude": 30.52}
    with pytest.raises(ValueError):
        WeatherService.validate_parameters(params)


def test_validate_parameters_longitude_out_of_bounds():
    params = {"latitude": 50.45, "longitude": 200}
    with pytest.raises(ValueError):
        WeatherService.validate_parameters(params)


def test_validate_parameters_elevation_valid():
    params = {"latitude": 50.45, "longitude": 30.52, "elevation": 100}
    result = WeatherService.validate_parameters(params)
    assert result["elevation"] == 100


def test_validate_parameters_elevation_invalid():
    params = {"latitude": 50.45, "longitude": 30.52, "elevation": 10000}
    result = WeatherService.validate_parameters(params)
    assert "elevation" not in result


def test_validate_parameters_forecast_days_valid():
    params = {"latitude": 50.45, "longitude": 30.52, "forecast_days": 5}
    result = WeatherService.validate_parameters(params)
    assert result["forecast_days"] == 5


def test_validate_parameters_forecast_days_invalid():
    params = {"latitude": 50.45, "longitude": 30.52, "forecast_days": 20}
    result = WeatherService.validate_parameters(params)
    assert result["forecast_days"] == 7


def test_validate_parameters_units_valid():
    params = {
        "latitude": 50.45,
        "longitude": 30.52,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "timeformat": "iso8601",
    }
    result = WeatherService.validate_parameters(params)
    assert result["temperature_unit"] == "celsius"
    assert result["wind_speed_unit"] == "kmh"
    assert result["precipitation_unit"] == "mm"
    assert result["timeformat"] == "iso8601"


def test_validate_parameters_units_invalid():
    params = {
        "latitude": 50.45,
        "longitude": 30.52,
        "temperature_unit": "kelvin",
        "wind_speed_unit": "foo",
        "precipitation_unit": "bar",
        "timeformat": "baz",
    }
    result = WeatherService.validate_parameters(params)
    assert "temperature_unit" not in result
    assert "wind_speed_unit" not in result
    assert "precipitation_unit" not in result
    assert "timeformat" not in result


def test_validate_parameters_hourly_daily_current_as_list():
    params = {
        "latitude": 50.45,
        "longitude": 30.52,
        "hourly": ["temperature_2m", "humidity"],
        "daily": ["weathercode"],
        "current": ["temperature_2m"],
    }
    result = WeatherService.validate_parameters(params)
    assert result["hourly"] == "temperature_2m,humidity"
    assert result["daily"] == "weathercode"
    assert result["current"] == "temperature_2m"


def test_validate_parameters_hourly_daily_current_as_str():
    params = {
        "latitude": 50.45,
        "longitude": 30.52,
        "hourly": "temperature_2m",
        "daily": "weathercode",
        "current": "temperature_2m",
    }
    result = WeatherService.validate_parameters(params)
    assert result["hourly"] == "temperature_2m"
    assert result["daily"] == "weathercode"
    assert result["current"] == "temperature_2m"


# --- WeatherFormatter tests ---


def test_get_weather_description_known_code():
    desc = WeatherFormatter.get_weather_description(0)
    assert desc["description"] == "Ясно"
    assert desc["emoji"] == "☀️"


def test_get_weather_description_unknown_code():
    desc = WeatherFormatter.get_weather_description(123)
    assert desc["description"] == "Код 123"
    assert desc["emoji"] == "❓"


def test_format_temperature_celsius():
    assert WeatherFormatter.format_temperature(23.456, "celsius") == "23.5°C"


def test_format_temperature_fahrenheit():
    assert WeatherFormatter.format_temperature(75.2, "fahrenheit") == "75.2°F"


def test_format_temperature_none():
    assert WeatherFormatter.format_temperature(None) == "N/A"


def test_format_wind_kmh():
    result = WeatherFormatter.format_wind(12.345, 90, "kmh")
    assert "12.3 км/год" in result
    assert "Сх" in result


def test_format_wind_none_speed():
    assert WeatherFormatter.format_wind(None, 90, "kmh") == "N/A"


def test_format_humidity():
    assert WeatherFormatter.format_humidity(55.7) == "56%"


def test_format_humidity_none():
    assert WeatherFormatter.format_humidity(None) == "N/A"


def test_format_pressure():
    assert WeatherFormatter.format_pressure(1013.25) == "1013 hPa"


def test_format_pressure_none():
    assert WeatherFormatter.format_pressure(None) == "N/A"


def test_format_precipitation_mm():
    assert WeatherFormatter.format_precipitation(5.678, "mm") == "5.7 мм"


def test_format_precipitation_inch():
    assert WeatherFormatter.format_precipitation(2.5, "inch") == "2.5 дюйм"


def test_format_precipitation_zero():
    assert WeatherFormatter.format_precipitation(0, "mm") == "0 мм"


def test_format_precipitation_none():
    assert WeatherFormatter.format_precipitation(None, "mm") == "0 мм"


def test_format_datetime_date():
    assert (
        WeatherFormatter.format_datetime("2024-06-01T12:34:56Z", "date") == "01.06.2024"
    )


def test_format_datetime_time():
    assert WeatherFormatter.format_datetime("2024-06-01T12:34:56Z", "time") == "12:34"


def test_format_datetime_datetime():
    assert (
        WeatherFormatter.format_datetime("2024-06-01T12:34:56Z", "datetime")
        == "01.06.2024 12:34"
    )


def test_format_datetime_weekday():
    # 2024-06-03 is Monday
    assert (
        WeatherFormatter.format_datetime("2024-06-03T00:00:00Z", "weekday")
        == "Понеділок"
    )


def test_format_datetime_invalid():
    assert WeatherFormatter.format_datetime("not_a_date", "date") == "not_a_date"


# --- WeatherService.get_weather tests ---


@pytest.mark.asyncio
async def test_get_weather_success():
    params = {"hourly": "temperature_2m"}
    mock_response = AsyncMock()
    mock_response.json = lambda: {"temperature_2m": [20, 21]}
    mock_response.raise_for_status.return_value = None

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        result = await WeatherService.get_weather(50.45, 30.52, params)
        assert "temperature_2m" in result


@pytest.mark.asyncio
async def test_get_weather_api_error_in_response():
    params = {"hourly": "temperature_2m"}
    mock_response = AsyncMock()
    mock_response.json = lambda: {"error": "Invalid request"}
    mock_response.raise_for_status.return_value = None

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        with pytest.raises(WeatherAPIError):
            await WeatherService.get_weather(50.45, 30.52, params)


@pytest.mark.asyncio
async def test_get_weather_timeout():
    params = {"hourly": "temperature_2m"}
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(WeatherAPIError):
            await WeatherService.get_weather(50.45, 30.52, params)


@pytest.mark.asyncio
async def test_get_weather_http_status_error_400():
    params = {"hourly": "temperature_2m"}
    mock_response = AsyncMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    error = httpx.HTTPStatusError("Bad Request", request=None, response=mock_response)
    with patch("httpx.AsyncClient.get", side_effect=error):
        with pytest.raises(WeatherAPIError) as exc:
            await WeatherService.get_weather(50.45, 30.52, params)
        assert "Некоректні параметри" in str(exc.value)


@pytest.mark.asyncio
async def test_get_weather_request_error():
    params = {"hourly": "temperature_2m"}
    with patch(
        "httpx.AsyncClient.get",
        side_effect=httpx.RequestError("Network error", request=None),
    ):
        with pytest.raises(WeatherAPIError):
            await WeatherService.get_weather(50.45, 30.52, params)


@pytest.mark.asyncio
async def test_get_weather_invalid_latitude_type():
    params = {"hourly": "temperature_2m"}
    with pytest.raises(WeatherAPIError):
        await WeatherService.get_weather("not_a_float", 30.52, params)


@pytest.mark.asyncio
async def test_get_weather_invalid_params_type():
    with pytest.raises(WeatherAPIError):
        await WeatherService.get_weather(50.45, 30.52, "not_a_dict")
