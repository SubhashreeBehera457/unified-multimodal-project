"""
services/gdacs.py
─────────────────
GDACS (Global Disaster Alert and Coordination System) RSS ingestion.
Public API — no credentials required.
Attribution: European Union / GDACS (CC BY 4.0).

Parses the GDACS RSS feed and normalises events into the unified incident schema:
    incident_id      : str   (e.g. "GDACS-FL1104169")
    disaster_type    : str   (e.g. "FLOOD", "EARTHQUAKE", "CYCLONE")
    severity         : str   ("LOW" | "MEDIUM" | "HIGH" | "CRITICAL")
    status           : str   ("ACTIVE")
    latitude         : float
    longitude        : float
    location         : str
    people_at_risk   : int
    assigned_team    : str   ("Unassigned")
    created_at       : str   (ISO timestamp)
    updated_at       : str
    source           : str   ("GDACS")
    verification_status : str ("GDACS_VERIFIED")
    description      : str
    alert_level      : str   ("Green" | "Orange" | "Red")
    event_type_code  : str   ("FL" | "EQ" | "TC" | ...)
    gdacs_url        : str

Data integrity note:
    source = "GDACS" + verification_status = "GDACS_VERIFIED"
    This means the data comes directly from the GDACS system.
    It does NOT mean we have independently verified the event.
    GDACS data itself carries a confidence/alert level (Green/Orange/Red).
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from services.config import GDACS_RSS_URL


# XML namespace map used in GDACS RSS
_NS = {
    "gdacs": "http://www.gdacs.org",
    "geo":   "http://www.w3.org/2003/01/geo/wgs84_pos#",
    "dc":    "http://purl.org/dc/elements/1.1/",
    "georss":"http://www.georss.org/georss",
}

# Map GDACS alert level → our severity
_ALERT_TO_SEVERITY = {
    "Green":  "MEDIUM",
    "Orange": "HIGH",
    "Red":    "CRITICAL",
}

# Map GDACS event type code → human-readable disaster type
_EVENT_TYPE_MAP = {
    "FL": "FLOOD",
    "EQ": "EARTHQUAKE",
    "TC": "CYCLONE",
    "VO": "VOLCANIC ACTIVITY",
    "DR": "DROUGHT",
    "WF": "WILDFIRE",
    "TS": "TSUNAMI",
}


def fetch_gdacs_alerts(
    max_events: int = 300,
    timeout: int = 12,
    filter_event_types: Optional[list] = None,
) -> dict:
    """
    Fetch and parse the GDACS RSS feed.

    Args:
        max_events: Maximum number of events to return.
        timeout: HTTP request timeout in seconds.
        filter_event_types: List of GDACS event type codes to include,
                            e.g. ["FL", "TC", "EQ", "WF"]. None = all types.

    Returns a dict:
        {
            "source": "LIVE" | "UNAVAILABLE",
            "fetched_at": str,
            "total_events": int,
            "incidents": list[dict],
            "error": str | None,
        }
    """
    try:
        r = requests.get(GDACS_RSS_URL, timeout=timeout)
        if r.status_code != 200:
            return _error_response(f"GDACS returned HTTP {r.status_code}")

        root = ET.fromstring(r.content)
        channel = root.find("channel")
        if channel is None:
            return _error_response("GDACS RSS: no <channel> element found")

        incidents = []
        items = channel.findall("item")

        for item in items:
            if len(incidents) >= max_events:
                break

            # ── Event type ───────────────────────────────────────────────────
            event_code = _text(item, "gdacs:eventtype", _NS) or "UNKNOWN"
            if filter_event_types and event_code not in filter_event_types:
                continue

            disaster_type = _EVENT_TYPE_MAP.get(event_code, event_code)
            raw_title = _text(item, "title") or ""
            raw_desc = _text(item, "description") or ""
            if event_code == "WF" or "forest fire" in raw_title.lower() or "wildfire" in raw_title.lower():
                disaster_type = "WILDFIRE"

            # ── Alert level / severity ───────────────────────────────────────
            alert_level = _text(item, "gdacs:alertlevel", _NS) or "Green"
            severity = _ALERT_TO_SEVERITY.get(alert_level, "MEDIUM")

            # ── Coordinates ──────────────────────────────────────────────────
            lat_str = _text(item, "geo:lat", _NS)
            lon_str = _text(item, "geo:long", _NS)
            if lat_str is None or lon_str is None:
                georss = _text(item, "georss:point", _NS)
                if georss:
                    parts = georss.strip().split()
                    lat_str, lon_str = parts[0], parts[1]
            try:
                lat = float(lat_str) if lat_str else None
                lon = float(lon_str) if lon_str else None
            except ValueError:
                lat, lon = None, None

            if lat is None or lon is None:
                continue  # skip events without coordinates

            # ── Location ─────────────────────────────────────────────────────
            country = _text(item, "gdacs:country", _NS) or "Unknown"
            iso3 = _text(item, "gdacs:iso3", _NS) or ""
            event_name = _text(item, "gdacs:eventname", _NS) or ""
            location = f"{event_name}, {country}".strip(", ") if event_name else country

            # ── People at risk ───────────────────────────────────────────────
            pop_elem = item.find("gdacs:population", _NS)
            people_at_risk = 0
            if pop_elem is not None:
                try:
                    people_at_risk = int(float(pop_elem.get("value", "0")))
                except (ValueError, TypeError):
                    people_at_risk = 0

            # ── IDs and dates ─────────────────────────────────────────────────
            event_id = _text(item, "gdacs:eventid", _NS) or "UNKNOWN"
            incident_id = f"GDACS-{event_code}{event_id}"

            pub_date_str = _text(item, "pubDate") or ""
            created_at = _parse_rss_date(pub_date_str)

            # ── Description ──────────────────────────────────────────────────
            desc = _text(item, "description") or ""
            title = _text(item, "title") or desc[:80]
            gdacs_url = _text(item, "link") or GDACS_RSS_URL

            # ── Severity text ────────────────────────────────────────────────
            sev_elem = item.find("gdacs:severity", _NS)
            sev_text = sev_elem.text.strip() if (sev_elem is not None and sev_elem.text) else ""

            incidents.append({
                "incident_id": incident_id,
                "disaster_type": disaster_type,
                "severity": severity,
                "status": "ACTIVE",
                "latitude": lat,
                "longitude": lon,
                "location": location,
                "people_at_risk": people_at_risk,
                "assigned_team": "Unassigned",
                "created_at": created_at,
                "updated_at": created_at,
                "source": "GDACS",
                "verification_status": "GDACS_VERIFIED",
                "description": desc[:200],
                "title": title[:120],
                "alert_level": alert_level,
                "event_type_code": event_code,
                "severity_text": sev_text,
                "gdacs_url": gdacs_url,
            })

        return {
            "source": "LIVE",
            "fetched_at": datetime.now().strftime("%H:%M:%S"),
            "total_events": len(incidents),
            "incidents": incidents,
            "error": None,
        }

    except requests.exceptions.ConnectionError:
        return _error_response("GDACS connection error — check network")
    except ET.ParseError as e:
        return _error_response(f"GDACS XML parse error: {e}")
    except Exception as e:
        return _error_response(f"GDACS unexpected error: {e}")


def _text(element, tag: str, ns: dict = None) -> Optional[str]:
    """Safely get text from an XML element."""
    child = element.find(tag, ns) if ns else element.find(tag)
    if child is None:
        return None
    return (child.text or "").strip() or None


def _parse_rss_date(date_str: str) -> str:
    """Parse RSS pubDate to ISO-like string, fallback to now."""
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d %H:%M UTC")
        except ValueError:
            continue
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _error_response(error: str) -> dict:
    return {
        "source": "UNAVAILABLE",
        "fetched_at": datetime.now().strftime("%H:%M:%S"),
        "total_events": 0,
        "incidents": [],
        "error": error,
    }
