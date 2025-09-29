async def format_weather_response(
    weather_data: dict, location_data: dict, api_params: dict
) -> str:
    city = location_data.get("city", "")
    state = location_data.get("state", "")
    country = location_data.get("country", "")

    location_str = f"🌍 **{city}"
    if state:
        location_str += f", {state}"
    if country:
        location_str += f", {country}"
    location_str += "**\n\n"

    response = location_str

    current = weather_data.get("current", {})
    if current:
        temp_unit = "°C" if api_params.get("temperature_unit") == "celsius" else "°F"
        wind_unit = api_params.get("wind_speed_unit", "kmh")

        response += "☀️ **Поточна погода:**\n"
        response += (
            f"🌡️ Температура: {current.get('temperature_2m', 'N/A')}{temp_unit}\n"
        )

        if "apparent_temperature" in current:
            response += (
                f"🌡️ Відчувається: {current['apparent_temperature']}{temp_unit}\n"
            )

        if "relative_humidity_2m" in current:
            response += f"💧 Вологість: {current['relative_humidity_2m']}%\n"

        if "wind_speed_10m" in current:
            response += f"💨 Вітер: {current['wind_speed_10m']} {wind_unit}\n"

        if "weather_code" in current:
            weather_desc = get_weather_description(current["weather_code"])
            response += f"☁️ Опис: {weather_desc}\n"

        response += "\n"

    daily = weather_data.get("daily", {})
    if daily and "time" in daily:
        response += "📅 **Прогноз на найближчі дні:**\n"

        forecast_days = api_params.get("forecast_days")
        try:
            forecast_days = int(forecast_days)
        except (TypeError, ValueError):
            forecast_days = len(daily["time"])
        times = daily["time"][:forecast_days]
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        weather_codes = daily.get("weather_code", [])

        temp_unit = "°C" if api_params.get("temperature_unit") == "celsius" else "°F"

        for i in range(len(times)):
            date_str = times[i]
            max_temp = temp_max[i] if i < len(temp_max) else "N/A"
            min_temp = temp_min[i] if i < len(temp_min) else "N/A"
            weather_code = weather_codes[i] if i < len(weather_codes) else 0

            try:
                from datetime import datetime

                date_obj = datetime.fromisoformat(date_str)
                day_name = date_obj.strftime("%A")
                day_names = {
                    "Monday": "Понеділок",
                    "Tuesday": "Вівторок",
                    "Wednesday": "Середа",
                    "Thursday": "Четвер",
                    "Friday": "П'ятниця",
                    "Saturday": "Субота",
                    "Sunday": "Неділя",
                }
                day_name = day_names.get(day_name, day_name)
                date_formatted = f"{day_name}, {date_obj.strftime('%d.%m')}"
            except:
                date_formatted = date_str

            weather_desc = get_weather_description(weather_code)
            response += f"• {date_formatted}: {max_temp}°/{min_temp}° {weather_desc}\n"

    return response


def get_weather_description(weather_code: int) -> str:
    descriptions = {
        0: "☀️ Ясно",
        1: "🌤️ Переважно ясно",
        2: "⛅ Частково хмарно",
        3: "☁️ Хмарно",
        45: "🌫️ Туман",
        48: "🌫️ Іней",
        51: "🌦️ Легкий дощ",
        53: "🌦️ Помірний дощ",
        55: "🌧️ Сильний дощ",
        56: "🌨️ Легкий сніг з дощем",
        57: "🌨️ Сніг з дощем",
        61: "🌦️ Легкий дощ",
        63: "🌦️ Дощ",
        65: "🌧️ Сильний дощ",
        66: "🌨️ Дощ зі снігом",
        67: "🌨️ Сильний дощ зі снігом",
        71: "❄️ Легкий сніг",
        73: "❄️ Сніг",
        75: "❄️ Сильний сніг",
        77: "❄️ Снігопад",
        80: "🌦️ Зливи",
        81: "⛈️ Грози",
        82: "⛈️ Сильні грози",
        85: "❄️ Снігопад",
        86: "❄️ Сильний снігопад",
        95: "⛈️ Гроза",
        96: "⛈️ Гроза з градом",
        99: "⛈️ Сильна гроза",
    }
    return descriptions.get(weather_code, f"Код {weather_code}")
