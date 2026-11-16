"""
services/config.py
──────────────────
Central configuration loader.
Reads from environment variables (or a .env file if python-dotenv is available).
All API credentials MUST come from here — never hardcode them in app.py.
"""
import os

# Try to load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)  # don't override already-set env vars
except ImportError:
    pass  # python-dotenv not installed — read from actual env only


# ── External APIs ────────────────────────────────────────────────────────────
X_BEARER_TOKEN: str | None = os.environ.get("X_BEARER_TOKEN") or None
REDDIT_CLIENT_ID: str | None = os.environ.get("REDDIT_CLIENT_ID") or None
REDDIT_CLIENT_SECRET: str | None = os.environ.get("REDDIT_CLIENT_SECRET") or None
REDDIT_USER_AGENT: str = os.environ.get("REDDIT_USER_AGENT", "DisasterIntelligence/1.0")
HF_TOKEN: str | None = os.environ.get("HF_TOKEN") or None

# ── Service base URLs ────────────────────────────────────────────────────────
OSRM_BASE_URL: str = os.environ.get("OSRM_BASE_URL", "http://router.project-osrm.org")
OPENMETEO_BASE_URL: str = os.environ.get("OPENMETEO_BASE_URL", "https://api.open-meteo.com")

# GDACS public RSS — no credentials needed
GDACS_RSS_URL: str = "https://www.gdacs.org/xml/rss.xml"

# ── Location defaults ────────────────────────────────────────────────────────
DEFAULT_LATITUDE: float = float(os.environ.get("DEFAULT_LATITUDE", "20.2961"))
DEFAULT_LONGITUDE: float = float(os.environ.get("DEFAULT_LONGITUDE", "85.8245"))

# ── Storage ──────────────────────────────────────────────────────────────────
DB_PATH: str = os.environ.get("DB_PATH", "data/incidents.db")

# ── Refresh intervals (seconds) ──────────────────────────────────────────────
WEATHER_REFRESH_INTERVAL: int = int(os.environ.get("WEATHER_REFRESH_INTERVAL", "900"))
GDACS_REFRESH_INTERVAL: int = int(os.environ.get("GDACS_REFRESH_INTERVAL", "300"))
SOCIAL_REFRESH_INTERVAL: int = int(os.environ.get("SOCIAL_REFRESH_INTERVAL", "60"))


def api_configured(name: str) -> bool:
    """Return True if the given API credentials are present."""
    mapping = {
        "x": X_BEARER_TOKEN is not None,
        "twitter": X_BEARER_TOKEN is not None,
        "reddit": REDDIT_CLIENT_ID is not None and REDDIT_CLIENT_SECRET is not None,
        "hf": HF_TOKEN is not None,
    }
    return mapping.get(name.lower(), False)
