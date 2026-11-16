"""
backend/state.py
────────────────
Backend thread-safe state store for Unified Multimodal Disaster Management System.
Decoupled from Streamlit session state, providing reliable state for FastAPI and WebSockets.
"""
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any

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
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "SIMULATION",
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
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "SIMULATION",
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


class AppStateManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AppStateManager, cls).__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        self._state_lock = threading.Lock()
        now_str = datetime.now().strftime("%H:%M:%S")
        self.incidents: List[Dict[str, Any]] = [dict(i) for i in _DEMO_INCIDENTS]
        self.rescue_teams: List[Dict[str, Any]] = [dict(t) for t in _DEMO_TEAMS]
        self.reports: List[Dict[str, Any]] = []
        self.timeline_events: List[Dict[str, Any]] = [
            {
                "time": now_str,
                "description": "FastAPI Disaster Operations Engine initialized.",
                "type": "system",
            }
        ]
        self.weather_cache: Optional[Dict[str, Any]] = None
        self.weather_last_fetched: Optional[datetime] = None
        self.gdacs_cache: Optional[Dict[str, Any]] = None
        self.gdacs_last_fetched: Optional[datetime] = None
        self.latest_risk_result: Optional[Dict[str, Any]] = None
        self.latest_multimodal_result: Optional[Dict[str, Any]] = None
        self.last_calculated_route: Optional[Dict[str, Any]] = None

    def get_incidents(self, status: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._state_lock:
            result = list(self.incidents)
            if status:
                result = [i for i in result if i.get("status") == status]
            if severity:
                result = [i for i in result if i.get("severity") == severity]
            return result

    def add_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        with self._state_lock:
            if "incident_id" not in incident or not incident["incident_id"]:
                incident["incident_id"] = self._generate_next_id()
            if "created_at" not in incident:
                incident["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            incident["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.incidents.append(incident)
            self._add_timeline_event_unlocked(
                f"New incident recorded: {incident.get('incident_id')} - {incident.get('disaster_type')} at {incident.get('location')}",
                "incident",
            )
            return incident

    def _generate_next_id(self) -> str:
        nums = []
        for inc in self.incidents:
            iid = inc.get("incident_id", "")
            if "-" in iid:
                parts = iid.split("-")
                try:
                    nums.append(int(parts[-1]))
                except ValueError:
                    pass
        max_num = max(nums, default=242)
        return f"INC-{max_num + 1:04d}"

    def merge_gdacs_incidents(self, gdacs_incidents: List[Dict[str, Any]]) -> int:
        added = 0
        with self._state_lock:
            existing_ids = {i["incident_id"] for i in self.incidents}
            for inc in gdacs_incidents:
                if inc.get("latitude") is None or inc.get("longitude") is None:
                    continue
                if inc["incident_id"] not in existing_ids:
                    self.incidents.append(inc)
                    existing_ids.add(inc["incident_id"])
                    added += 1
            if added > 0:
                self._add_timeline_event_unlocked(
                    f"Synchronized {added} live global alerts from GDACS RSS feed.",
                    "gdacs",
                )
        return added

    def get_teams(self) -> List[Dict[str, Any]]:
        with self._state_lock:
            return list(self.rescue_teams)

    def dispatch_team(self, team_id: str, incident_id: str) -> bool:
        with self._state_lock:
            now_str = datetime.now().strftime("%H:%M:%S")
            team_found = None
            for t in self.rescue_teams:
                if t["team_id"] == team_id:
                    t["status"] = "DISPATCHED"
                    t["current_assignment"] = incident_id
                    team_found = t
                    break

            if not team_found:
                return False

            inc_found = None
            for i in self.incidents:
                if i["incident_id"] == incident_id:
                    i["assigned_team"] = team_found["name"]
                    i["updated_at"] = now_str
                    inc_found = i
                    break

            self._add_timeline_event_unlocked(
                f"{team_found['name']} dispatched to Incident {incident_id}",
                "dispatch",
            )
            return True

    def add_report(self, report: Dict[str, Any]):
        with self._state_lock:
            if "ingested_at" not in report:
                report["ingested_at"] = datetime.now().strftime("%H:%M:%S")
            self.reports.insert(0, report)
            if len(self.reports) > 100:
                self.reports = self.reports[:100]

    def get_reports(self) -> List[Dict[str, Any]]:
        with self._state_lock:
            return list(self.reports)

    def add_timeline_event(self, description: str, event_type: str = "info"):
        with self._state_lock:
            self._add_timeline_event_unlocked(description, event_type)

    def _add_timeline_event_unlocked(self, description: str, event_type: str = "info"):
        self.timeline_events.insert(0, {
            "time": datetime.now().strftime("%H:%M:%S"),
            "description": description,
            "type": event_type,
        })
        if len(self.timeline_events) > 30:
            self.timeline_events = self.timeline_events[:30]

    def get_timeline(self) -> List[Dict[str, Any]]:
        with self._state_lock:
            return list(self.timeline_events)

    def get_kpis(self) -> Dict[str, Any]:
        with self._state_lock:
            active = [i for i in self.incidents if i.get("status") == "ACTIVE"]
            critical = [i for i in active if i.get("severity") == "CRITICAL"]
            verified_reports = [r for r in self.reports if r.get("is_genuine") is True]
            dispatched_teams = [t for t in self.rescue_teams if t.get("status") in ("DISPATCHED", "EN_ROUTE")]
            people_at_risk = sum(i.get("people_at_risk", 0) for i in active)
            gdacs_count = len([i for i in active if i.get("source") == "GDACS"])

            return {
                "active_incidents": len(active),
                "critical_alerts": len(critical),
                "verified_reports": len(verified_reports),
                "dispatched_teams": len(dispatched_teams),
                "people_at_risk": people_at_risk,
                "gdacs_incidents": gdacs_count,
            }


state_manager = AppStateManager()
