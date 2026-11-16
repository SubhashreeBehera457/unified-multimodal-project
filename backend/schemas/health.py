from pydantic import BaseModel
from typing import Dict, Any, Optional

class ServiceHealth(BaseModel):
    status: str  # "ONLINE" | "DEGRADED" | "NOT CONFIGURED" | "UNAVAILABLE"
    message: Optional[str] = None
    last_checked: Optional[str] = None

class HealthResponse(BaseModel):
    overall_status: str  # "OPERATIONAL" | "DEGRADED" | "OFFLINE"
    timestamp: str
    services: Dict[str, ServiceHealth]
    models: Dict[str, str]
