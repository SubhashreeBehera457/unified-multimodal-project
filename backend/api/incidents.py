"""
backend/api/incidents.py
────────────────────────
Live incidents management and team dispatch operations.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any

from backend.state import state_manager
from backend.schemas.incident import IncidentItem, IncidentCreateRequest, DispatchTeamRequest

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=List[IncidentItem])
def get_incidents(
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, RESOLVED"),
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
):
    return state_manager.get_incidents(status=status, severity=severity)


@router.get("/kpis")
def get_incident_kpis():
    return state_manager.get_kpis()


@router.get("/{incident_id}", response_model=IncidentItem)
def get_incident_by_id(incident_id: str):
    incidents = state_manager.get_incidents()
    for inc in incidents:
        if inc.get("incident_id") == incident_id:
            return inc
    raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")


@router.post("", response_model=IncidentItem)
def create_incident(req: IncidentCreateRequest):
    new_inc = {
        "disaster_type": req.disaster_type.upper(),
        "severity": req.severity.upper(),
        "status": "ACTIVE",
        "latitude": req.latitude,
        "longitude": req.longitude,
        "location": req.location,
        "people_at_risk": req.people_at_risk,
        "assigned_team": "Unassigned",
        "source": req.source,
        "verification_status": "VERIFIED" if req.source != "GDACS" else "GDACS_VERIFIED",
        "description": req.description,
        "alert_level": "Red" if req.severity == "CRITICAL" else ("Orange" if req.severity == "HIGH" else "Green"),
    }
    return state_manager.add_incident(new_inc)


@router.post("/dispatch")
def dispatch_team(req: DispatchTeamRequest):
    success = state_manager.dispatch_team(team_id=req.team_id, incident_id=req.incident_id)
    if not success:
        raise HTTPException(status_code=400, detail="Team dispatch failed. Verify team ID and incident ID.")
    return {"success": True, "message": f"Team {req.team_id} successfully dispatched to {req.incident_id}"}
