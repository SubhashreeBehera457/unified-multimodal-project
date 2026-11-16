from pydantic import BaseModel, Field
from typing import Optional, List

class IncidentItem(BaseModel):
    incident_id: str
    disaster_type: str
    severity: str  # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    status: str    # "ACTIVE" | "RESOLVED"
    latitude: float
    longitude: float
    location: str
    people_at_risk: int = 0
    assigned_team: Optional[str] = "Unassigned"
    created_at: str
    updated_at: str
    source: str    # "LIVE" | "SIMULATION" | "GDACS" | "MODEL" | "USER"
    verification_status: str  # "VERIFIED" | "GDACS_VERIFIED" | "UNVERIFIED"
    description: Optional[str] = ""
    alert_level: Optional[str] = "Green"
    title: Optional[str] = None
    event_type_code: Optional[str] = None
    gdacs_url: Optional[str] = None

class IncidentCreateRequest(BaseModel):
    disaster_type: str
    severity: str = "HIGH"
    latitude: float
    longitude: float
    location: str
    people_at_risk: int = 0
    description: Optional[str] = ""
    source: str = "SIMULATION"

class DispatchTeamRequest(BaseModel):
    team_id: str
    incident_id: str
