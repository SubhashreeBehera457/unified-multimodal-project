from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class DashboardResponse(BaseModel):
    kpis: Dict[str, Any]
    system_status: str
    last_synced: str
    weather: Optional[Dict[str, Any]] = None
    recent_incidents: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    active_teams: List[Dict[str, Any]]
