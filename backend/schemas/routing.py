from pydantic import BaseModel, Field
from typing import List, Optional

class RouteCalculateRequest(BaseModel):
    start_lat: float = Field(..., description="Origin latitude")
    start_lon: float = Field(..., description="Origin longitude")
    end_lat: float = Field(..., description="Destination latitude")
    end_lon: float = Field(..., description="Destination longitude")
    alternate: bool = False

class RouteCalculateResponse(BaseModel):
    success: bool
    points: Optional[List[List[float]]] = None  # [[lat, lon], ...]
    distance_km: Optional[float] = None
    duration_min: Optional[int] = None
    route_type: str = "STANDARD ROAD ROUTE"
    routing_engine: str = "OSRM (Open Source Routing Machine)"
    hazard_aware: bool = False
    disclaimer: str = "OSRM calculates standard road navigation. It does NOT automatically avoid flooded or blocked sectors unless custom road closures are fed."
    source: str = "OSRM"
    error: Optional[str] = None
    fetched_at: str
