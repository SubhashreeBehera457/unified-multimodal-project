"""
services/weather.py
───────────────────
Open-Meteo weather ingestion.
Free public API — no credentials required.
Returns structured weather observations for Bhubaneswar (or any lat/lon).

Data labels:
  source = "LIVE"      → fresh API data
  source = "CACHED"    → data from a previous successful call still within TTL
  source = "UNAVAILABLE" → API call failed
"""
import requests
from datetime import datetime
from typing import Optional
from services.config import OPENMETEO_BASE_URL, DEFAULT_LATITUDE, DEFAULT_LONGITUDE


def fetch_current_weather(
    lat: float = DEFAULT_LATITUDE,
    lon: float = DEFAULT_LONGITUDE,
    timeout: int = 6,
) -> dict:
    """
    Fetch current weather and 1-day hourly precipitation from Open-Meteo.

    Returns a dict with keys:
        temperature         : float (°C) or None
        windspeed           : float (km/h) or None
        weathercode         : int (WMO code) or None
        precipitation_now   : float (mm, current hour) or None
        precipitation_24h   : float (mm, sum of last 24 hours) or None
        windspeed_max_24h   : float (km/h, max of last 24 hours) or None
        source              : "LIVE" | "UNAVAILABLE"
        fetched_at          : str (HH:MM:SS local time)
        lat, lon            : floats
    """
    url = (
        f"{OPENMETEO_BASE_URL}/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current_weather=true"
        f"&hourly=precipitation,windspeed_10m,temperature_2m"
        f"&forecast_days=1"
        f"&timezone=Asia%2FKolkata"
    )
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            return _unavailable(lat, lon)
        data = r.json()

        cw = data.get("current_weather", {})
        hourly = data.get("hourly", {})
        precip_series = hourly.get("precipitation", [])
        wind_series = hourly.get("windspeed_10m", [])

        # Sum precipitation over all available hours (= 24h window)
        precip_24h = round(sum(float(v) for v in precip_series if v is not None), 2)
        # Max wind over 24h
        windspeed_max_24h = round(max((float(v) for v in wind_series if v is not None), default=0.0), 1)
        # Current-hour precipitation (last value)
        precip_now = float(precip_series[-1]) if precip_series else None

        return {
            "temperature": cw.get("temperature"),
            "windspeed": cw.get("windspeed"),
            "weathercode": cw.get("weathercode"),
            "precipitation_now": precip_now,
            "precipitation_24h": precip_24h,
            "windspeed_max_24h": windspeed_max_24h,
            "source": "LIVE",
            "fetched_at": datetime.now().strftime("%H:%M:%S"),
            "lat": lat,
            "lon": lon,
        }
    except Exception:
        return _unavailable(lat, lon)


def _unavailable(lat: float, lon: float) -> dict:
    return {
        "temperature": None,
        "windspeed": None,
        "weathercode": None,
        "precipitation_now": None,
        "precipitation_24h": None,
        "windspeed_max_24h": None,
        "source": "UNAVAILABLE",
        "fetched_at": datetime.now().strftime("%H:%M:%S"),
        "lat": lat,
        "lon": lon,
    }


def weather_description(code: Optional[int]) -> str:
    """Map WMO weathercode to a human-readable string."""
    if code is None:
        return "Unknown"
    table = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall",
        80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm with heavy hail",
    }
    return table.get(code, f"WMO code {code}")
