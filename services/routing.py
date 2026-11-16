"""
services/routing.py
───────────────────
OSRM routing service wrapper.
Public API — no credentials required.

Provides:
  - calculate_route()     : primary and alternate routes via OSRM
  - check_osrm_status()   : connectivity check

Important:
  OSRM returns standard road routes (fastest driving path).
  It does NOT account for flood zones, road blockages, or hazards
  unless custom OSRM profiles are deployed with hazard data.
  All routes are labeled "STANDARD ROAD ROUTE" not "HAZARD-AWARE ROUTE".
"""
import requests
from datetime import datetime
from typing import Optional
from services.config import OSRM_BASE_URL


def calculate_route(
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    alternate: bool = False,
    timeout: int = 8,
) -> dict:
    """
    Calculate a driving route via OSRM.

    Args:
        start_lon, start_lat : Team/origin coordinates
        end_lon, end_lat     : Incident/destination coordinates
        alternate            : If True, add a small waypoint offset to explore alternate path
        timeout              : HTTP timeout in seconds

    Returns dict:
        success      : bool
        points       : list[[lat, lon]] (for Folium polyline) | None
        distance_km  : float | None
        duration_min : int | None
        route_type   : "STANDARD ROAD ROUTE" | "ALTERNATE STANDARD ROUTE"
        source       : "OSRM"
        error        : str | None   (when success=False)
        fetched_at   : str
    """
    route_type = "ALTERNATE STANDARD ROUTE" if alternate else "STANDARD ROAD ROUTE"
    try:
        if alternate:
            # Offset midpoint to force slightly different path
            mid_lon = (start_lon + end_lon) / 2 + 0.008
            mid_lat = (start_lat + end_lat) / 2 - 0.005
            coords = f"{start_lon},{start_lat};{mid_lon},{mid_lat};{end_lon},{end_lat}"
        else:
            coords = f"{start_lon},{start_lat};{end_lon},{end_lat}"

        url = f"{OSRM_BASE_URL}/route/v1/driving/{coords}?overview=full&geometries=geojson"
        r = requests.get(url, timeout=timeout)

        if r.status_code != 200:
            return _route_error(f"OSRM returned HTTP {r.status_code}", route_type)

        data = r.json()
        if not data.get("routes"):
            return _route_error("OSRM returned no routes", route_type)

        route = data["routes"][0]
        coords_list = route["geometry"]["coordinates"]
        # OSRM gives [lon, lat] — flip to [lat, lon] for Folium
        points = [[c[1], c[0]] for c in coords_list]
        distance_km = round(route["distance"] / 1000, 2)
        duration_min = round(route["duration"] / 60)

        return {
            "success": True,
            "points": points,
            "distance_km": distance_km,
            "duration_min": duration_min,
            "route_type": route_type,
            "source": "OSRM",
            "error": None,
            "fetched_at": datetime.now().strftime("%H:%M:%S"),
        }

    except requests.exceptions.ConnectionError:
        return _route_error("OSRM service unreachable — connection error", route_type)
    except Exception as e:
        return _route_error(str(e), route_type)


def check_osrm_status(timeout: int = 4) -> bool:
    """Return True if OSRM is reachable."""
    try:
        url = f"{OSRM_BASE_URL}/route/v1/driving/85.82,20.29;85.81,20.32?overview=false"
        r = requests.get(url, timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def _route_error(message: str, route_type: str) -> dict:
    return {
        "success": False,
        "points": None,
        "distance_km": None,
        "duration_min": None,
        "route_type": route_type,
        "source": "OSRM",
        "error": message,
        "fetched_at": datetime.now().strftime("%H:%M:%S"),
    }
