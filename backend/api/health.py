"""
backend/api/health.py
─────────────────────
System health check endpoint verifying actual configuration and reachability.
Uses concurrent checks and caching to ensure rapid response times.
"""
from fastapi import APIRouter
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor

from services.config import api_configured, OSRM_BASE_URL, OPENMETEO_BASE_URL, GDACS_RSS_URL
from services.routing import check_osrm_status
from backend.model_loader import model_manager
from backend.schemas.health import HealthResponse, ServiceHealth

router = APIRouter(prefix="/health", tags=["Health"])

_last_health_cache = None
_last_health_time = None


def _check_url(url: str, timeout: float = 2.5) -> bool:
    try:
        r = requests.head(url, timeout=timeout)
        return r.status_code in (200, 301, 302, 403, 405)
    except Exception:
        try:
            r = requests.get(url, timeout=timeout)
            return r.status_code == 200
        except Exception:
            return False


@router.get("", response_model=HealthResponse)
def get_system_health():
    global _last_health_cache, _last_health_time
    now = datetime.now()

    # Cache for 20 seconds
    if _last_health_cache and _last_health_time:
        if (now - _last_health_time).total_seconds() < 20:
            return _last_health_cache

    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # 1. AI Engine check
    models_status = model_manager.get_status()
    all_models_online = all(
        s.startswith("ONLINE") for s in [
            models_status["xgboost_risk"],
            models_status["shap_explainer"],
            models_status["distilbert_misinfo"],
            models_status["resnet_vision"],
        ]
    )
    ai_status = "ONLINE" if all_models_online else "DEGRADED"

    # 2. Concurrently check external services
    with ThreadPoolExecutor(max_workers=4) as executor:
        f_gdacs = executor.submit(_check_url, GDACS_RSS_URL, 2.5)
        f_weather = executor.submit(
            _check_url,
            f"{OPENMETEO_BASE_URL}/v1/forecast?latitude=20.29&longitude=85.82&current_weather=true",
            2.5,
        )
        f_gdelt = executor.submit(
            _check_url,
            "https://api.gdeltproject.org/api/v2/doc/doc?query=flood&mode=ArtList&maxrecords=1&format=json",
            2.5,
        )
        f_osrm = executor.submit(check_osrm_status, 2.5)

        gdacs_online = f_gdacs.result()
        weather_online = f_weather.result()
        gdelt_online = f_gdelt.result()
        osrm_online = f_osrm.result()

    gdacs_status = "ONLINE" if gdacs_online else "UNAVAILABLE"
    weather_status = "ONLINE" if weather_online else "UNAVAILABLE"
    gdelt_status = "ONLINE" if gdelt_online else "UNAVAILABLE"
    osrm_status = "ONLINE" if osrm_online else "UNAVAILABLE"
    pipeline_status = "ONLINE"

    # X / Twitter
    if api_configured("x"):
        x_status = "ONLINE"
        x_msg = "X API Bearer token configured."
    else:
        x_status = "NOT CONFIGURED"
        x_msg = "X_BEARER_TOKEN environment variable not set."

    # Reddit
    if api_configured("reddit"):
        reddit_status = "ONLINE"
        reddit_msg = "Reddit client credentials configured."
    else:
        reddit_status = "NOT CONFIGURED"
        reddit_msg = "REDDIT_CLIENT_ID / SECRET not configured."

    services = {
        "ai_engine": ServiceHealth(status=ai_status, message="XGBoost, SHAP, DistilBERT, ResNet-50", last_checked=now_str),
        "data_pipeline": ServiceHealth(status=pipeline_status, message="In-memory operations state manager active", last_checked=now_str),
        "gdacs": ServiceHealth(status=gdacs_status, message="European Union GDACS Public RSS Feed", last_checked=now_str),
        "weather": ServiceHealth(status=weather_status, message="Open-Meteo High-Resolution Weather API", last_checked=now_str),
        "gdelt": ServiceHealth(status=gdelt_status, message="GDELT Global Disaster News Feed", last_checked=now_str),
        "osrm": ServiceHealth(status=osrm_status, message="Open Source Routing Machine (OSRM)", last_checked=now_str),
        "x_twitter": ServiceHealth(status=x_status, message=x_msg, last_checked=now_str),
        "reddit": ServiceHealth(status=reddit_status, message=reddit_msg, last_checked=now_str),
    }

    critical_services = [ai_status, pipeline_status, gdacs_status, weather_status]
    if all(s == "ONLINE" for s in critical_services):
        overall = "OPERATIONAL"
    elif any(s == "ONLINE" for s in critical_services):
        overall = "DEGRADED"
    else:
        overall = "OFFLINE"

    result = HealthResponse(
        overall_status=overall,
        timestamp=now_str,
        services=services,
        models=models_status,
    )
    _last_health_cache = result
    _last_health_time = now
    return result
