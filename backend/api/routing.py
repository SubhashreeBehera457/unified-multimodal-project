"""
backend/api/routing.py
──────────────────────
Rescue routing endpoint using OSRM.
Returns standard road route polylines and distances.
Does NOT claim hazard-aware avoidance.
"""
from fastapi import APIRouter
from backend.schemas.routing import RouteCalculateRequest, RouteCalculateResponse
from backend.state import state_manager
from services.routing import calculate_route

router = APIRouter(prefix="/routing", tags=["Rescue Routing"])


@router.post("/calculate", response_model=RouteCalculateResponse)
def compute_route(req: RouteCalculateRequest):
    res = calculate_route(
        start_lon=req.start_lon,
        start_lat=req.start_lat,
        end_lon=req.end_lon,
        end_lat=req.end_lat,
        alternate=req.alternate,
    )

    if res.get("success"):
        state_manager.last_calculated_route = res

    return RouteCalculateResponse(
        success=res.get("success", False),
        points=res.get("points"),
        distance_km=res.get("distance_km"),
        duration_min=res.get("duration_min"),
        route_type=res.get("route_type", "STANDARD ROAD ROUTE"),
        routing_engine="OSRM (Open Source Routing Machine)",
        hazard_aware=False,
        disclaimer="Standard road routing path. Does not account for flooded or debris-blocked roads in real time.",
        source="OSRM",
        error=res.get("error"),
        fetched_at=res.get("fetched_at", ""),
    )
