from fastapi import FastAPI, Query
from services.geocode import geocode_place
from services.weather import get_weather

app = FastAPI(title="Weather API")


@app.get("/weather")
async def get_weather_api(city: str = Query(..., description="Назва міста")):
    location = await geocode_place(city)
    weather = await get_weather(location["lat"], location["lon"])
    return {"city": location["formatted"], "weather": weather}
