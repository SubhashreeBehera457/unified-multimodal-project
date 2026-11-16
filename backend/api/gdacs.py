"""
backend/api/gdacs.py
────────────────────
GDACS RSS alerts endpoint with caching and incident synchronization.
"""
from fastapi import APIRouter, Query
from datetime import datetime
from typing import List, Dict, Any

from services.config import GDACS_REFRESH_INTERVAL
from services.gdacs import fetch_gdacs_alerts
from backend.state import state_manager

router = APIRouter(prefix="/gdacs", tags=["GDACS"])


@router.get("")
def get_gdacs_alerts(
    max_events: int = Query(250, ge=1, le=500),
    sync_to_incidents: bool = Query(True),
    force_refresh: bool = Query(False),
):
    now = datetime.now()
    cache = state_manager.gdacs_cache
    last_fetched = state_manager.gdacs_last_fetched

    if not force_refresh and cache and last_fetched:
        if (now - last_fetched).total_seconds() < GDACS_REFRESH_INTERVAL:
            return cache

    data = fetch_gdacs_alerts(max_events=max_events, timeout=12)
    if data.get("source") == "LIVE":
        state_manager.gdacs_cache = data
        state_manager.gdacs_last_fetched = now
        if sync_to_incidents and data.get("incidents"):
            state_manager.merge_gdacs_incidents(data["incidents"])

    return data
