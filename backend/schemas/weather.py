from pydantic import BaseModel
from typing import Optional

class WeatherResponse(BaseModel):
    temperature: Optional[float] = None
    windspeed: Optional[float] = None
    weathercode: Optional[int] = None
    weather_description: str = "Unknown"
    precipitation_now: Optional[float] = None
    precipitation_24h: Optional[float] = None
    windspeed_max_24h: Optional[float] = None
    source: str  # "LIVE" | "UNAVAILABLE"
    fetched_at: str
    lat: float
    lon: float
