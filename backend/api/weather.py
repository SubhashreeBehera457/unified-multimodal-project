"""
backend/api/weather.py
──────────────────────
Open-Meteo weather endpoint with caching.
"""
from fastapi import APIRouter, Query
from datetime import datetime, timedelta

from services.config import DEFAULT_LATITUDE, DEFAULT_LONGITUDE, WEATHER_REFRESH_INTERVAL
from services.weather import fetch_current_weather, weather_description
from backend.state import state_manager
from backend.schemas.weather import WeatherResponse

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("", response_model=WeatherResponse)
def get_weather(
    lat: float = Query(DEFAULT_LATITUDE, ge=-90.0, le=90.0),
    lon: float = Query(DEFAULT_LONGITUDE, ge=-180.0, le=180.0),
    force_refresh: bool = Query(False),
):
    now = datetime.now()
    # Check cache
    cache = state_manager.weather_cache
    last_fetched = state_manager.weather_last_fetched

    if not force_refresh and cache and last_fetched:
        if (now - last_fetched).total_seconds() < WEATHER_REFRESH_INTERVAL:
            # Check coordinate match within tolerance
            if abs(cache.get("lat", 0) - lat) < 0.05 and abs(cache.get("lon", 0) - lon) < 0.05:
                return WeatherResponse(
                    temperature=cache.get("temperature"),
                    windspeed=cache.get("windspeed"),
                    weathercode=cache.get("weathercode"),
                    weather_description=weather_description(cache.get("weathercode")),
                    precipitation_now=cache.get("precipitation_now"),
                    precipitation_24h=cache.get("precipitation_24h"),
                    windspeed_max_24h=cache.get("windspeed_max_24h"),
                    source=cache.get("source", "LIVE"),
                    fetched_at=cache.get("fetched_at", now.strftime("%H:%M:%S")),
                    lat=lat,
                    lon=lon,
                )

    data = fetch_current_weather(lat=lat, lon=lon, timeout=6)
    state_manager.weather_cache = data
    state_manager.weather_last_fetched = now

    return WeatherResponse(
        temperature=data.get("temperature"),
        windspeed=data.get("windspeed"),
        weathercode=data.get("weathercode"),
        weather_description=weather_description(data.get("weathercode")),
        precipitation_now=data.get("precipitation_now"),
        precipitation_24h=data.get("precipitation_24h"),
        windspeed_max_24h=data.get("windspeed_max_24h"),
        source=data.get("source", "UNAVAILABLE"),
        fetched_at=data.get("fetched_at", now.strftime("%H:%M:%S")),
        lat=lat,
        lon=lon,
    )
