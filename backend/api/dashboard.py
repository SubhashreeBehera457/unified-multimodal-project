"""
backend/api/dashboard.py
────────────────────────
Aggregated dashboard telemetry endpoint for the Command Center.
"""
from fastapi import APIRouter
from datetime import datetime

from backend.state import state_manager
from backend.schemas.dashboard import DashboardResponse
from services.weather import fetch_current_weather, weather_description
from services.gdacs import fetch_gdacs_alerts
from services.config import DEFAULT_LATITUDE, DEFAULT_LONGITUDE

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard_summary():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    kpis = state_manager.get_kpis()

    # Weather snapshot
    weather_data = state_manager.weather_cache
    if not weather_data:
        try:
            weather_data = fetch_current_weather(DEFAULT_LATITUDE, DEFAULT_LONGITUDE, timeout=4)
            state_manager.weather_cache = weather_data
            state_manager.weather_last_fetched = datetime.now()
        except Exception:
            weather_data = None

    if weather_data and "weather_description" not in weather_data:
        weather_data["weather_description"] = weather_description(weather_data.get("weathercode"))

    incidents = state_manager.get_incidents()
    if len(incidents) <= 2:
        try:
            gdacs_data = fetch_gdacs_alerts(max_events=250, timeout=6)
            if gdacs_data.get("source") == "LIVE" and gdacs_data.get("incidents"):
                state_manager.merge_gdacs_incidents(gdacs_data["incidents"])
                incidents = state_manager.get_incidents()
                kpis = state_manager.get_kpis()
        except Exception:
            pass

    timeline = state_manager.get_timeline()
    teams = state_manager.get_teams()

    return DashboardResponse(
        kpis=kpis,
        system_status="OPERATIONAL",
        last_synced=now_str,
        weather=weather_data,
        recent_incidents=incidents,
        timeline=timeline[:20],
        active_teams=teams,
    )
