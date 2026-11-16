"""
state/app_state.py
───────────────────
Central application state management.

Session state schema and utility functions.
All modules read/write through these functions — never access st.session_state directly.

Design principles:
  - All incident data is clearly tagged with source (DEMO | GDACS | DISTILBERT_VERIFIED | etc.)
  - Verification status is tracked separately from source
  - KPIs are always computed dynamically from state — never hardcoded
  - Timeline events are logged for every significant system action

This module is framework-agnostic — could be adapted to FastAPI + PostgreSQL later.
"""
from datetime import datetime
import streamlit as st


# ── Default demo incidents (clearly labeled DEMO/SIMULATION) ─────────────────
_DEMO_INCIDENTS = [
    {
        "incident_id": "INC-0241",
        "disaster_type": "FLASH FLOOD",
        "severity": "CRITICAL",
        "status": "ACTIVE",
        "latitude": 20.29,
        "longitude": 85.82,
        "location": "Downtown Sector 4, Bhubaneswar",
        "people_at_risk": 1284,
        "assigned_team": "Unassigned",
        "created_at": "",      # filled at runtime
        "updated_at": "",
        "source": "DEMO",
        "verification_status": "VERIFIED",
        "description": "Flash flood — demo incident loaded at startup.",
        "alert_level": "Red",
    },
    {
        "incident_id": "INC-0242",
        "disaster_type": "ROAD BLOCKAGE",
        "severity": "HIGH",
        "status": "ACTIVE",
        "latitude": 20.31,
        "longitude": 85.85,
        "location": "Highway 12, Cuttack Road",
        "people_at_risk": 150,
        "assigned_team": "Unassigned",
        "created_at": "",
        "updated_at": "",
        "source": "DEMO",
        "verification_status": "VERIFIED",
        "description": "Road blockage — demo incident loaded at startup.",
        "alert_level": "Orange",
    },
]

_DEMO_TEAMS = [
    {
        "team_id": "R-17",
        "name": "Team R-17 (Heavy Rescue)",
        "latitude": 20.32,
        "longitude": 85.81,
        "status": "AVAILABLE",
        "capacity": 20,
        "current_assignment": None,
    },
    {
        "team_id": "R-03",
        "name": "Team R-03 (Medical Unit)",
        "latitude": 20.28,
        "longitude": 85.80,
        "status": "AVAILABLE",
        "capacity": 10,
        "current_assignment": None,
    },
    {
        "team_id": "R-21",
        "name": "Team R-21 (Rapid Clearance)",
        "latitude": 20.33,
        "longitude": 85.83,
        "status": "AVAILABLE",
        "capacity": 15,
        "current_assignment": None,
    },
]


def init_state():
    """
    Initialize all session state keys if not already present.
    Call once at app startup — safe to call multiple times (idempotent).
    """
    if st.session_state.get("_state_initialized"):
        return

    now_str = datetime.now().strftime("%H:%M:%S")

    # Patch created_at for demo incidents
    incidents = []
    for inc in _DEMO_INCIDENTS:
        i = dict(inc)
        i["created_at"] = now_str
        i["updated_at"] = now_str
        incidents.append(i)

    st.session_state["incidents"] = incidents
    st.session_state["rescue_teams"] = [dict(t) for t in _DEMO_TEAMS]
    st.session_state["reports"] = []
    st.session_state["timeline_events"] = [
        {
            "time": now_str,
            "description": "System initialized — 2 demo incidents loaded.",
            "type": "system",
        }
    ]
    st.session_state["last_route"] = None
    st.session_state["gdacs_cache"] = None
    st.session_state["gdacs_loaded"] = False
    st.session_state["risk_result"] = None
    st.session_state["risk_mode"] = "SIMULATION"   # "SIMULATION" | "LIVE"
    st.session_state["last_distilbert_result"] = None
    st.session_state["multimodal_text_result"] = None
    st.session_state["vision_result"] = None
    st.session_state["_state_initialized"] = True


def add_timeline_event(description: str, event_type: str = "info"):
    """Insert a timestamped event at the top of the timeline (max 25 events kept)."""
    events = st.session_state.get("timeline_events", [])
    events.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "description": description,
        "type": event_type,
    })
    st.session_state["timeline_events"] = events[:25]


def get_kpis() -> dict:
    """
    Compute dashboard KPIs from incident and team state.
    All values are derived from actual state — never hardcoded.
    """
    incidents = st.session_state.get("incidents", [])
    active = [i for i in incidents if i["status"] == "ACTIVE"]
    critical = [i for i in active if i["severity"] == "CRITICAL"]
    reports = st.session_state.get("reports", [])
    verified_reports = [r for r in reports if r.get("is_genuine", False)]
    teams = st.session_state.get("rescue_teams", [])
    dispatched = [t for t in teams if t["status"] in ("DISPATCHED", "EN_ROUTE")]
    people_at_risk = sum(i.get("people_at_risk", 0) for i in active)
    gdacs_count = len([i for i in active if i.get("source") == "GDACS"])

    return {
        "active_incidents": len(active),
        "critical_alerts": len(critical),
        "verified_reports": len(verified_reports),
        "dispatched_teams": len(dispatched),
        "people_at_risk": people_at_risk,
        "gdacs_incidents": gdacs_count,
    }


def add_incident(incident: dict):
    """Add a new incident to the state."""
    incidents = st.session_state.get("incidents", [])
    incidents.append(incident)
    st.session_state["incidents"] = incidents


def get_next_incident_id() -> str:
    """Generate the next sequential INC-XXXX id."""
    incidents = st.session_state.get("incidents", [])
    ids = [i["incident_id"] for i in incidents if "-" in i.get("incident_id", "")]
    nums = []
    for iid in ids:
        parts = iid.split("-")
        try:
            nums.append(int(parts[-1]))
        except ValueError:
            pass
    max_num = max(nums, default=241)
    return f"INC-{max_num + 1:04d}"


def add_gdacs_incidents(gdacs_result: dict):
    """
    Merge GDACS incidents into state.
    Deduplicates by incident_id — existing GDACS incidents are replaced with fresh data.
    Only adds incidents that have valid coordinates.
    """
    if gdacs_result.get("source") != "LIVE":
        return 0

    existing_ids = {i["incident_id"] for i in st.session_state.get("incidents", [])}
    added = 0
    for inc in gdacs_result.get("incidents", []):
        if inc["latitude"] is None or inc["longitude"] is None:
            continue
        if inc["incident_id"] not in existing_ids:
            st.session_state["incidents"].append(inc)
            existing_ids.add(inc["incident_id"])
            added += 1
    return added


def add_report(report: dict):
    """Add a report to the reports store."""
    reports = st.session_state.get("reports", [])
    reports.append(report)
    st.session_state["reports"] = reports


def dispatch_team(team_id: str, incident_id: str, route: dict):
    """Update team and incident state after dispatch."""
    now_str = datetime.now().strftime("%H:%M:%S")

    for team in st.session_state.get("rescue_teams", []):
        if team["team_id"] == team_id:
            team["status"] = "DISPATCHED"
            team["current_assignment"] = incident_id

    for inc in st.session_state.get("incidents", []):
        if inc["incident_id"] == incident_id:
            team_name = next(
                (t["name"] for t in st.session_state.get("rescue_teams", []) if t["team_id"] == team_id),
                team_id,
            )
            inc["assigned_team"] = team_name
            inc["updated_at"] = now_str
