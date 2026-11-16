# -*- coding: utf-8 -*-
"""
app.py
──────
Disaster Response Intelligence — Main Streamlit Application.

Data flow:
  Real APIs (Open-Meteo, GDACS, OSRM)
        ↓
  services/ (weather.py, gdacs.py, social.py, routing.py)
        ↓
  Incident / Weather / Report State (state/app_state.py)
        ↓ 
  ML Models (ml/risk.py, ml/misinformation.py, ml/vision.py, ml/fusion.py)
        ↓
  Dashboard (Streamlit — this file)

Data integrity rules:
  - Source labels: LIVE | MODEL GENERATED | SIMULATION | DATA SOURCE UNAVAILABLE
  - Never present simulated data as live
  - Never claim hazard-aware routing if only standard OSRM is used
  - Never claim trained attention fusion if no fusion model exists
  - API failures show "NOT CONFIGURED" or "UNAVAILABLE" — never generate fake data
"""
import streamlit as st
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import pickle
import io
import shap
import folium
from streamlit_folium import st_folium
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# ── Service layer ─────────────────────────────────────────────────────────────
from services.config import (
    api_configured,
    WEATHER_REFRESH_INTERVAL,
    GDACS_REFRESH_INTERVAL,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
)
from services.weather import fetch_current_weather, weather_description
from services.gdacs import fetch_gdacs_alerts
from services.social import (
    fetch_x_reports,
    fetch_reddit_reports,
    fetch_gdelt_news,
    clean_text,
    determine_verification_status,
)
from services.routing import calculate_route, check_osrm_status

# ── ML layer ──────────────────────────────────────────────────────────────────
from ml.risk import run_risk_inference, classify_risk, build_feature_dataframe, load_risk_model
from ml.misinformation import load_misinfo_model, run_distilbert, batch_classify
from ml.vision import load_image_model, classify_single_image, classify_multiple_images
from ml.fusion import run_fusion

# ── State layer ───────────────────────────────────────────────────────────────
from state.app_state import (
    init_state,
    add_timeline_event,
    get_kpis,
    add_incident,
    get_next_incident_id,
    add_gdacs_incidents,
    add_report,
    dispatch_team,
)

from transformers import DistilBertTokenizer, DistilBertForSequenceClassification


# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Disaster Response Intelligence",
    layout="wide",
    page_icon="🚨",
    initial_sidebar_state="expanded",
)

# =============================================================================
# GLOBAL CSS
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E0E6ED; }
    .stApp { background-color: #0B0E14; }
    [data-testid="stSidebar"] { background-color: #121721; border-right: 1px solid #1F2937; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}

    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 10px !important; }
    iframe { width: 100% !important; max-width: 100% !important; border-radius: 8px; }
    .block-container { padding: 1rem 1.5rem !important; max-width: 100% !important; }

    .stButton > button {
        background: linear-gradient(135deg, #1A73E8, #58A6FF) !important;
        color: #FFFFFF !important; border: none !important; border-radius: 8px !important;
        padding: 10px 18px !important; font-weight: 600 !important; font-size: 0.88rem !important;
        transition: all 0.25s ease !important; box-shadow: 0 2px 8px rgba(88,166,255,0.2) !important;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 16px rgba(88,166,255,0.4) !important; transform: translateY(-1px) !important;
    }
    .stSlider > div > div > div > div { background-color: #58A6FF !important; }
    .stTextArea textarea {
        background-color: #161B22 !important; color: #E0E6ED !important;
        border: 1px solid #30363D !important; border-radius: 8px !important;
    }
    [data-testid="stFileUploader"] { background-color: #161B22 !important; border-radius: 8px !important; }

    .metric-card {
        background-color: #161B22; border: 1px solid #30363D; border-radius: 12px;
        padding: clamp(10px, 2vw, 18px); box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s, box-shadow 0.2s; margin-bottom: 10px;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.5); border-color: #58A6FF; }
    .metric-value { font-size: clamp(1.4rem, 3vw, 2.2rem); font-weight: 700; color: #FFFFFF; font-family: 'IBM Plex Sans', sans-serif; margin: 5px 0; }
    .metric-label { font-size: clamp(0.62rem, 1.1vw, 0.82rem); font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #8B949E; }
    .metric-trend.positive { color: #2EA043; } .metric-trend.negative { color: #F85149; } .metric-trend.warning { color: #D29922; }

    .incident-card {
        background: linear-gradient(145deg, #1A1F2B, #121721);
        border-left: 4px solid #F85149; border-radius: 10px;
        padding: clamp(10px, 2vw, 14px); margin-bottom: 10px;
        border-top: 1px solid #30363D; border-right: 1px solid #30363D; border-bottom: 1px solid #30363D;
        transition: transform 0.2s;
    }
    .incident-card:hover { transform: translateX(3px); }
    .incident-title { font-size: clamp(0.88rem, 1.4vw, 1.05rem); font-weight: 600; color: #FFF; margin-bottom: 6px; }
    .incident-meta { font-size: clamp(0.68rem, 1.1vw, 0.82rem); color: #8B949E; display: flex; justify-content: space-between; margin-bottom: 3px; flex-wrap: wrap; gap: 3px; }

    .badge-critical { background-color: rgba(248,81,73,0.15); color: #F85149; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; border: 1px solid rgba(248,81,73,0.4); }
    .badge-high { background-color: rgba(210,153,34,0.18); color: #E3B341; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; border: 1px solid rgba(210,153,34,0.45); }
    .badge-medium { background-color: rgba(88,166,255,0.15); color: #58A6FF; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; border: 1px solid rgba(88,166,255,0.4); }
    .badge-low { background-color: rgba(46,160,67,0.15); color: #3FB950; padding: 2px 8px; border-radius: 12px; font-size: 0.72rem; font-weight: 700; border: 1px solid rgba(46,160,67,0.4); }

    .incident-card.border-critical { border-left: 4px solid #F85149; }
    .incident-card.border-high { border-left: 4px solid #D29922; }
    .incident-card.border-medium { border-left: 4px solid #58A6FF; }
    .incident-card.border-low { border-left: 4px solid #2EA043; }

    .ai-card { background-color: #0D1117; border: 1px solid #30363D; border-radius: 12px; padding: clamp(12px, 2vw, 20px); }
    .ai-score { font-size: clamp(1.8rem, 4vw, 2.8rem); font-weight: 700; color: #58A6FF; }

    .status-dot { height: 9px; width: 9px; border-radius: 50%; display: inline-block; margin-right: 7px; animation: pulse-dot 2s infinite; }
    .status-online { background-color: #2EA043; box-shadow: 0 0 6px #2EA043; }
    .status-offline { background-color: #F85149; box-shadow: 0 0 6px #F85149; }
    .status-warning { background-color: #D29922; box-shadow: 0 0 6px #D29922; }
    @keyframes pulse-dot { 0%,100% { opacity:1; } 50% { opacity:0.45; } }

    .timeline-item { border-left: 2px solid #30363D; padding-left: 13px; padding-bottom: 13px; position: relative; }
    .timeline-item::before { content:''; position:absolute; width:9px; height:9px; background:#58A6FF; border-radius:50%; left:-5px; top:3px; }
    .timeline-time { font-size: 0.78rem; color: #8B949E; font-family: monospace; }
    .timeline-desc { font-size: clamp(0.78rem, 1.2vw, 0.92rem); color: #C9D1D9; margin-top: 3px; }

    h1, h2, h3 { font-family: 'IBM Plex Sans', sans-serif; color: #F0F6FC; }
    hr { border-color: #30363D; }

    .app-header {
        display: flex; justify-content: space-between; align-items: center;
        padding: 14px 0; border-bottom: 1px solid #30363D; margin-bottom: 22px;
        flex-wrap: wrap; gap: 8px;
    }
    .app-header h2 { margin: 0; font-size: clamp(1.1rem, 2.8vw, 1.7rem); letter-spacing: -0.5px; }
    .map-legend { display:flex; gap:14px; margin-top:8px; font-size:0.83rem; color:#8B949E; flex-wrap:wrap; }

    .data-label-live { display:inline-flex; align-items:center; gap:4px; font-size:0.73rem; font-weight:700; letter-spacing:0.7px; color:#2EA043; padding:2px 7px; border-radius:10px; background:rgba(46,160,67,0.15); border:1px solid rgba(46,160,67,0.4); }
    .data-label-model { display:inline-flex; align-items:center; gap:4px; font-size:0.73rem; font-weight:700; letter-spacing:0.7px; color:#58A6FF; padding:2px 7px; border-radius:10px; background:rgba(88,166,255,0.15); border:1px solid rgba(88,166,255,0.4); }
    .data-label-simulation { display:inline-flex; align-items:center; gap:4px; font-size:0.73rem; font-weight:700; letter-spacing:0.7px; color:#D29922; padding:2px 7px; border-radius:10px; background:rgba(210,153,34,0.15); border:1px solid rgba(210,153,34,0.4); }
    .data-label-unavailable { display:inline-flex; align-items:center; gap:4px; font-size:0.73rem; font-weight:700; letter-spacing:0.7px; color:#8B949E; padding:2px 7px; border-radius:10px; background:rgba(139,148,158,0.15); border:1px solid rgba(139,148,158,0.4); }
    .data-label-gdacs { display:inline-flex; align-items:center; gap:4px; font-size:0.73rem; font-weight:700; letter-spacing:0.7px; color:#D29922; padding:2px 7px; border-radius:10px; background:rgba(210,153,34,0.1); border:1px solid rgba(210,153,34,0.35); }

    @media (max-width:768px) {
        [data-testid="stHorizontalBlock"] { flex-direction:column !important; }
        [data-testid="stHorizontalBlock"]>div,[data-testid="column"] { width:100% !important; flex:1 1 100% !important; min-width:100% !important; }
        .block-container { padding:0.5rem 0.8rem !important; }
        .app-header { flex-direction:column; text-align:center; }
    }
    @media (min-width:769px) and (max-width:1024px) {
        [data-testid="stHorizontalBlock"]>div,[data-testid="column"] { min-width:44% !important; }
        .block-container { padding:0.8rem 1rem !important; }
    }
    ::-webkit-scrollbar { width:5px; height:5px; }
    ::-webkit-scrollbar-track { background:#0B0E14; }
    ::-webkit-scrollbar-thumb { background:#30363D; border-radius:3px; }
    ::-webkit-scrollbar-thumb:hover { background:#58A6FF; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# STATE INITIALIZATION
# =============================================================================
init_state()


# =============================================================================
# CACHED MODEL LOADERS
# (cached per session — models load once)
# =============================================================================
@st.cache_resource
def _load_risk_model():
    return load_risk_model()

@st.cache_resource
def _load_misinfo_model():
    return load_misinfo_model()

@st.cache_resource
def _load_image_model():
    return load_image_model()


# =============================================================================
# CACHED API FETCHERS
# (cached with TTL matching each source's refresh rate)
# =============================================================================
@st.cache_data(ttl=WEATHER_REFRESH_INTERVAL)
def _fetch_weather(lat=DEFAULT_LATITUDE, lon=DEFAULT_LONGITUDE):
    return fetch_current_weather(lat, lon)

@st.cache_data(ttl=GDACS_REFRESH_INTERVAL)
def _fetch_gdacs(max_events=30, filter_types=None):
    return fetch_gdacs_alerts(max_events=max_events, filter_event_types=filter_types)

@st.cache_data(ttl=60)
def _check_services():
    osrm = check_osrm_status()
    weather = _fetch_weather()
    return {
        "osrm": osrm,
        "openmeteo": weather["source"] == "LIVE",
        "gdacs": True,      # GDACS checked separately via _fetch_gdacs
        "x_twitter": api_configured("x"),
        "reddit": api_configured("reddit"),
    }


# =============================================================================
# COMPONENT HELPERS — All HTML is intentionally generated and passed to
# st.markdown(unsafe_allow_html=True). No raw HTML leaks to output.
# =============================================================================
def label_live(last_ts=None):
    ts_str = f"&nbsp;{last_ts}" if last_ts else ""
    return f'<span class="data-label-live">● LIVE{ts_str}</span>'

def label_model():
    return '<span class="data-label-model">⬡ MODEL OUTPUT</span>'

def label_simulation():
    return '<span class="data-label-simulation">◈ SIMULATION</span>'

def label_unavailable():
    return '<span class="data-label-unavailable">○ UNAVAILABLE</span>'

def label_gdacs():
    return '<span class="data-label-gdacs">◉ GDACS VERIFIED</span>'


def render_kpi(label, value, trend, trend_type="positive", context=""):
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div style="display:flex;justify-content:space-between;font-size:0.78rem;">
            <span class="metric-trend {trend_type}"><b>{trend}</b></span>
            <span style="color:#8B949E;">{context}</span>
        </div>
    </div>"""


def render_incident_card(incident):
    id_ = incident["incident_id"]
    title = incident["disaster_type"]
    loc = incident["location"]
    sev = incident["severity"]
    people = f"{incident.get('people_at_risk', 0):,}"
    team = incident.get("assigned_team", "Unassigned")
    updated = incident.get("updated_at", "--:--")
    source = incident.get("source", "")

    sev_up = sev.upper()
    if "CRITICAL" in sev_up: bc, brd = "badge-critical", "border-critical"
    elif "HIGH" in sev_up: bc, brd = "badge-high", "border-high"
    elif "MEDIUM" in sev_up: bc, brd = "badge-medium", "border-medium"
    else: bc, brd = "badge-low", "border-low"

    src_html = ""
    if source == "DEMO":
        src_html = ' <span style="font-size:0.68rem;color:#8B949E;font-style:italic;">[DEMO]</span>'
    elif source == "GDACS":
        src_html = ' <span style="font-size:0.68rem;color:#D29922;font-weight:600;">[GDACS]</span>'
    elif source == "DISTILBERT_VERIFIED":
        src_html = ' <span style="font-size:0.68rem;color:#2EA043;font-weight:600;">[NLP]</span>'
    elif source == "MULTIMODAL_FUSION":
        src_html = ' <span style="font-size:0.68rem;color:#58A6FF;font-weight:600;">[FUSION]</span>'

    return f"""
    <div class="incident-card {brd}">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;">
            <span style="color:#8B949E;font-family:monospace;font-size:0.78rem;font-weight:600;">{id_}{src_html}</span>
            <span class="{bc}">{sev}</span>
        </div>
        <div class="incident-title">{title}</div>
        <div class="incident-meta"><span>📍 {loc}</span><span>👥 {people} at risk</span></div>
        <div class="incident-meta"><span>🚑 {team}</span><span>🕒 {updated}</span></div>
    </div>"""


# =============================================================================
# SERVICES CHECK & HEADER
# =============================================================================
services = _check_services()

st.markdown(f"""
<div class="app-header">
    <div>
        <h2>DISASTER RESPONSE INTELLIGENCE</h2>
        <div style="font-size:0.88rem;color:#8B949E;margin-top:3px;">Real-Time Emergency Operations Platform</div>
    </div>
    <div style="text-align:right;">
        <div style="display:flex;align-items:center;justify-content:flex-end;margin-bottom:3px;gap:5px;">
            <span class="status-dot status-online"></span>
            <span style="font-weight:600;color:#2EA043;font-size:0.88rem;letter-spacing:1px;">SYSTEM OPERATIONAL</span>
        </div>
        <div style="font-size:0.78rem;color:#8B949E;font-family:monospace;">Session: {datetime.now().strftime('%H:%M:%S IST')}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# SIDEBAR — Navigation + Service Status
# =============================================================================
st.sidebar.markdown("""
<div style="margin-bottom:25px;text-align:center;">
    <h1 style="font-size:1.9rem;margin:0;">🛡️</h1>
    <h3 style="margin:4px 0 0 0;font-size:1.05rem;color:#58A6FF;">COMMAND CENTER</h3>
</div>
""", unsafe_allow_html=True)

nav_options = [
    "Command Center Home",
    "Pre-Disaster Risk",
    "Misinformation Intelligence",
    "Multimodal Analysis",
    "Rescue Routing",
]
selected_page = st.sidebar.radio("OPERATIONAL MODULES", nav_options)

st.sidebar.markdown("<hr style='margin:25px 0 18px 0;'>", unsafe_allow_html=True)

# Dynamic service status dots (real connectivity)
def _dot(ok): return "status-online" if ok else "status-offline"
def _lbl(ok, name, note=""):
    note_html = f' <span style="font-size:0.75rem;color:#8B949E;">{note}</span>' if note else ""
    return f"<b>{name}</b>{note_html}"

svc_html = '<div style="font-size:0.78rem;color:#8B949E;letter-spacing:1px;margin-bottom:12px;">DATA SOURCES</div>'
svc_html += f'<div style="margin-bottom:8px;font-size:0.87rem;"><span class="status-dot {_dot(services["osrm"])}"></span>OSRM Routing</div>'
svc_html += f'<div style="margin-bottom:8px;font-size:0.87rem;"><span class="status-dot {_dot(services["openmeteo"])}"></span>Open-Meteo Weather</div>'
svc_html += f'<div style="margin-bottom:8px;font-size:0.87rem;"><span class="status-dot status-online"></span>GDACS Disaster Alerts</div>'
x_dot = "status-online" if services["x_twitter"] else "status-warning"
x_note = "" if services["x_twitter"] else " [NOT CONFIGURED]"
svc_html += f'<div style="margin-bottom:8px;font-size:0.87rem;"><span class="status-dot {x_dot}"></span>X/Twitter API{x_note}</div>'
rd_dot = "status-online" if services["reddit"] else "status-warning"
rd_note = "" if services["reddit"] else " [NOT CONFIGURED]"
svc_html += f'<div style="margin-bottom:8px;font-size:0.87rem;"><span class="status-dot {rd_dot}"></span>Reddit API{rd_note}</div>'
svc_html += f'<div style="margin-bottom:8px;font-size:0.87rem;"><span class="status-dot status-online"></span>GDELT News Feed</div>'
st.sidebar.markdown(svc_html, unsafe_allow_html=True)

# Load model status
_risk_model, _explainer = _load_risk_model()
_tok, _nlp = _load_misinfo_model()
_img_model = _load_image_model()

ai_dot = "status-online" if (_risk_model and _tok and _img_model) else "status-warning"
ai_label = "AI ENGINE READY" if (_risk_model and _tok and _img_model) else "AI ENGINE PARTIAL"
st.sidebar.markdown(f"""
<hr style='margin:12px 0;'>
<div style="margin-bottom:8px;font-size:0.87rem;"><span class="status-dot {ai_dot}"></span>{ai_label}</div>
""", unsafe_allow_html=True)

# Quick stats
st.sidebar.markdown("<hr style='margin:12px 0 10px 0;'>", unsafe_allow_html=True)
kpis_sb = get_kpis()
st.sidebar.markdown(f"""
<div style="font-size:0.78rem;color:#8B949E;letter-spacing:1px;margin-bottom:8px;">QUICK STATS</div>
<div style="font-size:0.84rem;margin-bottom:5px;">Active Incidents: <b style="color:#F85149;">{kpis_sb['active_incidents']}</b></div>
<div style="font-size:0.84rem;margin-bottom:5px;">Critical Alerts: <b style="color:#F85149;">{kpis_sb['critical_alerts']}</b></div>
<div style="font-size:0.84rem;margin-bottom:5px;">GDACS Events: <b style="color:#D29922;">{kpis_sb['gdacs_incidents']}</b></div>
<div style="font-size:0.84rem;margin-bottom:5px;">People at Risk: <b style="color:#D29922;">{kpis_sb['people_at_risk']:,}</b></div>
""", unsafe_allow_html=True)


# =============================================================================
# PAGE: COMMAND CENTER HOME
# =============================================================================
if selected_page == "Command Center Home":
    kpis = get_kpis()

    # ── KPI Cards (dynamic from state) ───────────────────────────────────────
    kpi_html = f"""
    <div class="kpi-grid">
        {render_kpi("Active Incidents", f"{kpis['active_incidents']:02d}", "from incident state", "negative", "live count")}
        {render_kpi("Critical Alerts", f"{kpis['critical_alerts']:02d}", "severity=CRITICAL", "negative", "active")}
        {render_kpi("Verified Reports", str(kpis['verified_reports']), "DistilBERT verified", "positive", "this session")}
        {render_kpi("Dispatched Teams", str(kpis['dispatched_teams']), "rescue team state", "positive", "deployed")}
        {render_kpi("People at Risk", f"{kpis['people_at_risk']:,}", "sum of active incidents", "negative", "est. impact")}
        {render_kpi("GDACS Alerts", str(kpis['gdacs_incidents']), "live disaster feed", "warning", "active")}
    </div>"""
    st.markdown(kpi_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_map, col_panel = st.columns([7, 3])

    with col_map:
        st.markdown("### 🗺️ TACTICAL INCIDENT MAP")
        map_mode_col, refresh_col = st.columns([3, 1])
        with map_mode_col:
            st.markdown(
                label_live() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>Incidents from state + GDACS feed. "
                "No live satellite imagery connected.</span>",
                unsafe_allow_html=True,
            )
        with refresh_col:
            if st.button("🔄 Load GDACS Alerts", use_container_width=True):
                with st.spinner("Fetching GDACS disaster alerts..."):
                    gdacs_result = _fetch_gdacs()
                    if gdacs_result["source"] == "LIVE":
                        added = add_gdacs_incidents(gdacs_result)
                        add_timeline_event(
                            f"GDACS feed loaded: {gdacs_result['total_events']} events, "
                            f"{added} new added to state.",
                            "gdacs",
                        )
                        st.success(f"✅ GDACS: {gdacs_result['total_events']} events found, {added} new incidents added.")
                    else:
                        err = gdacs_result.get("error", "Unknown error")
                        st.warning(f"⚠️ GDACS unavailable: {err}")

        # Build folium map
        m = folium.Map(location=[20.305, 85.835], zoom_start=5, tiles="OpenStreetMap")
        severity_colors = {"CRITICAL": "red", "HIGH": "orange", "MEDIUM": "blue", "LOW": "green"}

        for inc in st.session_state["incidents"]:
            if inc["status"] != "ACTIVE" or inc.get("latitude") is None:
                continue
            color = severity_colors.get(inc["severity"], "gray")
            source_tag = f" [{inc.get('source', '')}]" if inc.get("source") != "DEMO" else ""
            popup_html = (
                f"<b>{inc['incident_id']}</b>{source_tag}<br>"
                f"{inc['disaster_type']}<br>"
                f"📍 {inc['location']}<br>"
                f"👥 {inc.get('people_at_risk', 0):,} at risk<br>"
                f"Severity: {inc['severity']}"
            )
            radius = 14 if inc["severity"] == "CRITICAL" else (11 if inc["severity"] == "HIGH" else 8)
            hex_color = {"red": "#F85149", "orange": "#D29922", "blue": "#58A6FF", "green": "#2EA043"}.get(color, "#8B949E")
            folium.CircleMarker(
                [inc["latitude"], inc["longitude"]],
                radius=radius, color=hex_color, fill=True, fill_opacity=0.4,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(m)
            folium.Marker(
                [inc["latitude"], inc["longitude"]],
                icon=folium.Icon(color=color, icon="info-sign"),
                popup=popup_html,
            ).add_to(m)

        for team in st.session_state["rescue_teams"]:
            t_color = "blue" if team["status"] == "AVAILABLE" else "orange"
            folium.Marker(
                [team["latitude"], team["longitude"]],
                icon=folium.Icon(color=t_color, icon="truck", prefix="fa"),
                popup=f"{team['name']}<br>Status: {team['status']}",
            ).add_to(m)

        st_folium(m, height=480, returned_objects=[])
        st.markdown("""
        <div class="map-legend">
            <div><span style="color:#F85149;">●</span> Critical Incident</div>
            <div><span style="color:#D29922;">●</span> High Incident / GDACS Alert</div>
            <div><span style="color:#58A6FF;">●</span> Rescue Team</div>
            <div><span style="color:#2EA043;">●</span> Low Severity</div>
        </div>""", unsafe_allow_html=True)

    with col_panel:
        st.markdown("### 📋 ACTIVE INCIDENTS")
        active_incidents = [i for i in st.session_state["incidents"] if i["status"] == "ACTIVE"]
        if active_incidents:
            # Show critical first, then by creation time
            sorted_incidents = sorted(
                active_incidents,
                key=lambda x: (0 if x["severity"] == "CRITICAL" else 1 if x["severity"] == "HIGH" else 2),
            )
            for inc in sorted_incidents[:8]:
                st.markdown(render_incident_card(inc), unsafe_allow_html=True)
            if len(active_incidents) > 8:
                st.caption(f"+ {len(active_incidents) - 8} more incidents")
        else:
            st.info("No active incidents.")

        st.markdown("### ⏱️ LIVE TIMELINE")
        st.markdown(
            label_model() + "&nbsp;<span style='font-size:0.78rem;color:#8B949E;'>Generated from system actions</span>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        timeline_html = ""
        for event in st.session_state.get("timeline_events", [])[:12]:
            timeline_html += f"""
            <div class="timeline-item">
                <div class="timeline-time">{event['time']}</div>
                <div class="timeline-desc">{event['description']}</div>
            </div>"""
        if timeline_html:
            st.markdown(timeline_html, unsafe_allow_html=True)
        else:
            st.info("No timeline events yet.")

    # ── GDACS Alert Explorer ──────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("🌍 GDACS LIVE DISASTER ALERTS — Browse Recent Events", expanded=False):
        st.markdown(
            label_live() + "&nbsp;<span style='font-size:0.82rem;color:#8B949E;'>GDACS public RSS — "
            "European Commission / JRC (CC BY 4.0). Attribution: gdacs.org</span>",
            unsafe_allow_html=True,
        )
        filter_col, load_col = st.columns([3, 1])
        with filter_col:
            event_types = st.multiselect(
                "Filter by event type",
                ["FL", "EQ", "TC", "VO", "DR", "WF", "TS"],
                default=["FL", "TC", "EQ"],
                help="FL=Flood, EQ=Earthquake, TC=Tropical Cyclone, VO=Volcano, DR=Drought, WF=Wildfire, TS=Tsunami",
                key="gdacs_filter",
            )
        with load_col:
            load_gdacs_btn = st.button("🌐 FETCH GDACS FEED", use_container_width=True, key="gdacs_browse_btn")

        if load_gdacs_btn or st.session_state.get("gdacs_cache"):
            if load_gdacs_btn:
                with st.spinner("Fetching GDACS RSS feed..."):
                    gdacs_data = _fetch_gdacs(max_events=50, filter_types=event_types if event_types else None)
                    st.session_state["gdacs_cache"] = gdacs_data
            else:
                gdacs_data = st.session_state.get("gdacs_cache")

            if gdacs_data and gdacs_data["source"] == "LIVE":
                incidents_gdacs = gdacs_data["incidents"]
                st.success(
                    f"✅ GDACS: {gdacs_data['total_events']} events | "
                    f"Fetched at {gdacs_data['fetched_at']} | "
                    f"Source: gdacs.org (CC BY 4.0)"
                )

                if incidents_gdacs:
                    df_gdacs = pd.DataFrame([
                        {
                            "ID": i["incident_id"],
                            "Type": i["disaster_type"],
                            "Alert": i["alert_level"],
                            "Severity": i["severity"],
                            "Country/Location": i["location"][:40],
                            "People": i["people_at_risk"],
                            "Date": i["created_at"],
                        }
                        for i in incidents_gdacs
                    ])
                    st.dataframe(df_gdacs, use_container_width=True, hide_index=True)

                    # Add selected GDACS events to incident state
                    if st.button("📌 ADD ALL TO INCIDENT STATE", use_container_width=True):
                        added = add_gdacs_incidents(gdacs_data)
                        add_timeline_event(
                            f"GDACS bulk add: {added} new incidents merged into state.", "gdacs"
                        )
                        st.success(f"✅ {added} new GDACS incidents added to state.")
                        st.rerun()
                else:
                    st.info("No GDACS events matched the current filter.")
            elif gdacs_data:
                err = gdacs_data.get("error", "Unknown error")
                st.error(f"❌ GDACS feed unavailable: {err}")

    # ── Add Demo Incident ─────────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("➕ Add Demo Incident (for demonstration)", expanded=False):
        st.caption("Use this to demonstrate cross-module state propagation.")
        dc1, dc2, dc3, dc4 = st.columns(4)
        with dc1:
            new_type = st.selectbox("Disaster Type", ["CYCLONE", "EARTHQUAKE", "LANDSLIDE", "BRIDGE COLLAPSE", "TSUNAMI", "WILDFIRE"])
        with dc2:
            new_sev = st.selectbox("Severity", ["LOW", "MEDIUM", "HIGH", "CRITICAL"], index=2)
        with dc3:
            new_people = st.number_input("People at Risk", 0, 100000, 200, step=50)
        with dc4:
            new_loc = st.text_input("Location Name", "Sector 7, Bhubaneswar")

        if st.button("➕ ADD DEMO INCIDENT", use_container_width=True):
            now = datetime.now()
            new_inc = {
                "incident_id": get_next_incident_id(),
                "disaster_type": new_type,
                "severity": new_sev,
                "status": "ACTIVE",
                "latitude": DEFAULT_LATITUDE + np.random.uniform(-0.04, 0.06),
                "longitude": DEFAULT_LONGITUDE + np.random.uniform(-0.04, 0.06),
                "location": new_loc,
                "people_at_risk": int(new_people),
                "assigned_team": "Unassigned",
                "created_at": now.strftime("%H:%M:%S"),
                "updated_at": now.strftime("%H:%M:%S"),
                "source": "DEMO",
                "verification_status": "UNVERIFIED",
                "description": f"Demo incident: {new_type} at {new_loc}",
                "alert_level": "Orange" if new_sev in ("HIGH", "CRITICAL") else "Green",
            }
            add_incident(new_inc)
            add_timeline_event(f"Demo incident {new_inc['incident_id']} ({new_type}) added — {new_loc}.", "incident")
            st.success(f"✅ Incident {new_inc['incident_id']} added.")
            st.rerun()


# =============================================================================
# PAGE: PRE-DISASTER RISK
# =============================================================================
elif selected_page == "Pre-Disaster Risk":
    st.markdown("### 📈 PRE-DISASTER RISK & METEOROLOGICAL INTELLIGENCE")

    # ── Mode selector ─────────────────────────────────────────────────────────
    mode_col, _ = st.columns([2, 3])
    with mode_col:
        risk_mode = st.radio(
            "INPUT MODE",
            ["SIMULATION", "LIVE"],
            horizontal=True,
            help=(
                "SIMULATION: Manual sliders for demonstration. "
                "LIVE: Pre-fill inputs from Open-Meteo live weather data."
            ),
            key="risk_mode_selector",
        )

    # Fetch live weather regardless of mode (for display)
    weather = _fetch_weather()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        <div class="metric-card" style="margin-bottom:18px;">
            <h4 style="margin-top:0;">SENSOR TELEMETRY INPUT</h4>
            <p style="color:#8B949E;font-size:0.88rem;margin:0;">
            Adjust telemetry or use Live mode to pre-fill from Open-Meteo weather data.
            </p>
        </div>""", unsafe_allow_html=True)

        # ── Live weather display ───────────────────────────────────────────────
        if weather["source"] == "LIVE":
            st.markdown(
                label_live(weather["fetched_at"]) +
                f"&nbsp;<b>Open-Meteo</b>: {weather['windspeed']} km/h wind · "
                f"{weather_description(weather['weathercode'])} · "
                f"24h precip: {weather['precipitation_24h']} mm",
                unsafe_allow_html=True,
            )
            live_rainfall = weather.get("precipitation_24h") or 0.0
            live_wind = weather.get("windspeed") or 0.0
        else:
            st.markdown(
                label_unavailable() + "&nbsp;<span style='color:#8B949E;font-size:0.85rem;'>Open-Meteo weather unavailable</span>",
                unsafe_allow_html=True,
            )
            live_rainfall = 0.0
            live_wind = 0.0

        # ── Simulation / Live mode sliders ────────────────────────────────────
        if risk_mode == "SIMULATION":
            st.markdown(label_simulation() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>Manual telemetry — for model demonstration</span>", unsafe_allow_html=True)
            rainfall = st.slider("Past 24h Cumulative Rainfall (mm)", 0, 500, 150,
                                 help="XGBoost input: Manual Daily Rainfall (mm)")
            wind_speed = st.slider("Cyclone Sustained Wind (km/h)", 0, 250, 80,
                                   help="XGBoost input: WMO_WIND")
        else:  # LIVE
            st.markdown(
                label_live(weather["fetched_at"]) +
                "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>Pre-filled from Open-Meteo. You can adjust below.</span>",
                unsafe_allow_html=True,
            )
            if weather["source"] != "LIVE":
                st.warning("⚠️ LIVE MODE: Open-Meteo unavailable. Using default values (0). Switch to SIMULATION for manual input.")
            rainfall = st.slider("Past 24h Cumulative Rainfall (mm)", 0, 500,
                                 min(500, max(0, int(live_rainfall))),
                                 help="Pre-filled from Open-Meteo precipitation_24h")
            wind_speed = st.slider("Cyclone Sustained Wind (km/h)", 0, 250,
                                   min(250, max(0, int(live_wind))),
                                   help="Pre-filled from Open-Meteo windspeed")

        st.markdown("---")
        st.markdown("**🌊 AUXILIARY TELEMETRY — not XGBoost model input**")
        river_level = st.slider(
            "River Level Trend (m above danger level)", 0.0, 10.0, 5.5,
            help="Displayed for situational awareness only. NOT a feature in the trained XGBoost model.",
        )
        st.info(
            "ℹ️ River Level is **auxiliary telemetry** — displayed for situational awareness only. "
            "It is **not** a feature in the trained XGBoost model and does **not** affect the prediction.",
            icon="ℹ️",
        )

        st.markdown("---")

        if st.button("⚡ EXECUTE PREDICTIVE AI MODEL", use_container_width=True):
            risk_model, explainer = _load_risk_model()
            if risk_model is None:
                st.error("❌ XGBoost model files not found. Check models/risk_model/")
            else:
                with st.spinner("Running XGBoost inference + SHAP..."):
                    result = run_risk_inference(rainfall, wind_speed, risk_model, explainer)
                    result["data_label"] = risk_mode
                    st.session_state["risk_result"] = result
                    add_timeline_event(
                        f"Risk model [{risk_mode}]: rainfall={rainfall}mm, wind={wind_speed}km/h "
                        f"→ score={result['risk_score']:.1f} ({result['risk_level']})",
                        "model",
                    )

        # ── Risk output display ───────────────────────────────────────────────
        if st.session_state.get("risk_result"):
            result = st.session_state["risk_result"]
            risk_score = result["risk_score"]
            risk_level = result["risk_level"]
            color = result["risk_color"]
            mode_label = result.get("data_label", "SIMULATION")

            # Data source label
            if mode_label == "LIVE":
                st.markdown(label_live() + "&nbsp;LIVE MODE — inputs from Open-Meteo", unsafe_allow_html=True)
            else:
                st.markdown(label_simulation() + "&nbsp;SIMULATION MODE — manual inputs", unsafe_allow_html=True)
            st.markdown(label_model() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>XGBoost inference output</span>", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="ai-card" style="text-align:center;border-top:4px solid {color};margin-top:12px;">
                <div class="metric-label">PREDICTED RISK SCORE</div>
                <div class="ai-score" style="color:{color};">{risk_score:.1f}</div>
                <div style="font-size:0.73rem;color:#8B949E;margin-top:2px;">risk-score units (model output, 0–100 scale)</div>
                <div style="font-size:0.95rem;font-weight:700;color:{color};letter-spacing:0.5px;margin-top:8px;">{risk_level}</div>
                <div style="color:#8B949E;margin-top:8px;font-size:0.82rem;">
                    Thresholds: LOW &lt;10 · MODERATE 10–20 · HIGH 20–30 · CRITICAL ≥30
                </div>
            </div>""", unsafe_allow_html=True)

            if risk_level == "CRITICAL":
                st.error("⚠️ CRITICAL RISK — Recommend advancing to Phase 2 (Active Monitoring & Pre-deployment).")
            elif risk_level == "HIGH":
                st.warning("⚠️ HIGH RISK — Enhanced monitoring recommended.")

            with st.expander("🔧 Model Diagnostics", expanded=False):
                st.markdown("""
                **Model Output Range Explanation:**
                XGBoost was trained on Odisha rainfall + IBTrACS cyclone data.
                Target `Risk_Score` was normalized by the dataset maximum (extreme historical cyclone winds).
                Typical slider-range inputs produce predictions in the **0–39 range**, not 0–100.
                Risk thresholds are calibrated to this real output range.
                """)
                st.markdown("**Lag Features — Synthetic Approximations:**")
                st.info(
                    "Rain_Lag1 = rainfall × 0.8, Rain_Lag3 = rainfall × 0.7, Wind_Lag1 = wind × 0.9. "
                    "These are synthetic proxies. Real lag features require time-series data from past days.",
                    icon="ℹ️",
                )
                st.markdown("**Model Feature DataFrame (exact input sent to XGBoost)**")
                st.dataframe(result["input_data"], use_container_width=True)
                c1, c2 = st.columns(2)
                c1.code(f"raw_score      = {result['raw_score']:.6f}")
                c2.code(f"risk_score     = {result['risk_score']:.4f}")
                if result.get("base_value") is not None:
                    st.code(f"SHAP base_value = {result['base_value']:.4f} (expected model output)")
        else:
            st.markdown("""
            <div class="ai-card" style="text-align:center;color:#8B949E;margin-top:20px;">
                <div class="metric-label">PREDICTIVE INFERENCE ENGINE</div>
                <div style="margin:14px 0;font-size:1.4rem;">📊</div>
                <div style="font-size:0.88rem;">Adjust telemetry and click EXECUTE PREDICTIVE AI MODEL.</div>
            </div>""", unsafe_allow_html=True)

    with col2:
        # ── Model comparison ──────────────────────────────────────────────────
        st.markdown("#### MODEL PERFORMANCE COMPARISON")
        try:
            comp_df = pd.read_csv("models/risk_model_comparison.csv")
            fig = px.bar(
                comp_df, x="R2_Score", y="Model", orientation="h",
                color="R2_Score", color_continuous_scale="Blues", template="plotly_dark",
            )
            fig.update_layout(margin=dict(l=0,r=0,t=30,b=0), height=220,
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.info("Model comparison CSV not found.")

        # ── SHAP display ──────────────────────────────────────────────────────
        st.markdown("#### 🧠 XAI — SHAP FEATURE CONTRIBUTIONS")
        st.markdown(
            label_model() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>TreeExplainer — identical input as XGBoost</span>",
            unsafe_allow_html=True,
        )

        if st.session_state.get("risk_result"):
            result = st.session_state["risk_result"]
            shap_vals = result.get("shap_vals")
            base_value = result.get("base_value")
            feature_names = result.get("shap_feature_names", [
                "Daily Rainfall (mm)", "Cyclone Wind (km/h)",
                "Rainfall Lag 1-Day", "Rainfall Lag 3-Day", "Wind Lag 1-Day",
            ])

            if shap_vals is not None:
                shap_array = np.array([float(v) for v in shap_vals])
                max_abs = max(float(np.max(np.abs(shap_array))), 1e-6)
                sorted_idx = np.argsort(-np.abs(shap_array))

                bars_html = ""
                for i in sorted_idx:
                    label_name = feature_names[i] if i < len(feature_names) else f"Feature {i}"
                    f_val = float(shap_array[i])
                    pct_width = min(100, max(2, int((abs(f_val) / max_abs) * 100)))
                    sign = "+" if f_val >= 0 else ""
                    val_str = f"{sign}{f_val:.4f} pts"
                    bar_color = "#F85149" if f_val > 0.5 else ("#D29922" if f_val > 0 else "#2EA043")
                    bars_html += f"""
                    <div style="display:flex;align-items:center;margin-bottom:9px;">
                        <div style="width:170px;font-size:0.8rem;color:#E0E6ED;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{label_name}</div>
                        <div style="flex-grow:1;background:#30363D;height:7px;border-radius:4px;margin:0 8px;">
                            <div style="background:{bar_color};height:100%;border-radius:4px;width:{pct_width}%;"></div>
                        </div>
                        <div style="width:90px;text-align:right;font-size:0.8rem;font-family:monospace;color:{bar_color};">{val_str}</div>
                    </div>"""

                top_idx = int(np.argmax(np.abs(shap_array)))
                top_label = feature_names[top_idx] if top_idx < len(feature_names) else f"Feature {top_idx}"
                top_val = float(shap_array[top_idx])
                sign = "+" if top_val >= 0 else ""
                base_str = f"{base_value:.4f} pts" if base_value is not None else "N/A"

                st.markdown(f"""
                <div class="metric-card">
                    <div style="margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;">
                        <span style="color:#8B949E;font-size:0.82rem;letter-spacing:0.5px;">TREEEXPLAINER — FEATURE CONTRIBUTIONS</span>
                        <span style="color:#58A6FF;font-size:0.73rem;font-family:monospace;">BASE VALUE: {base_str}</span>
                    </div>
                    {bars_html}
                    <p style="margin-top:10px;font-size:0.8rem;color:#C9D1D9;border-top:1px solid #30363D;padding-top:8px;margin-bottom:0;">
                    <b>Primary driver:</b> <b>{top_label}</b>
                    ({sign}{top_val:.4f} risk-score points).
                    SHAP values are in <i>risk-score-point units</i>, not percentages.
                    </p>
                    <p style="margin-top:6px;font-size:0.75rem;color:#8B949E;margin-bottom:0;">
                    ⚠️ Lag features (Rain_Lag1, Rain_Lag3, Wind_Lag1) are synthetic linear proxies —
                    XGBoost assigns near-zero marginal SHAP to them due to collinearity with today's values.
                    This is expected behavior, not a code error.
                    </p>
                </div>""", unsafe_allow_html=True)
            else:
                st.warning("SHAP values unavailable for this run.")
        else:
            st.markdown(
                "<div class='metric-card' style='text-align:center;color:#8B949E;padding:20px;'>"
                "Execute prediction to generate SHAP analysis."
                "</div>",
                unsafe_allow_html=True,
            )

        # ── Live weather panel ────────────────────────────────────────────────
        st.markdown("#### 🌤️ LIVE WEATHER — Bhubaneswar")
        if weather["source"] == "LIVE":
            wc1, wc2, wc3 = st.columns(3)
            wc1.metric("Temperature", f"{weather['temperature']} °C" if weather['temperature'] is not None else "N/A")
            wc2.metric("Wind Speed", f"{weather['windspeed']} km/h" if weather['windspeed'] is not None else "N/A")
            wc3.metric("24h Precip.", f"{weather['precipitation_24h']} mm" if weather['precipitation_24h'] is not None else "N/A")
            st.caption(f"● LIVE — Open-Meteo | {weather_description(weather['weathercode'])} | Updated {weather['fetched_at']}")
        else:
            st.markdown(label_unavailable() + "&nbsp;Open-Meteo weather data unavailable", unsafe_allow_html=True)


# =============================================================================
# PAGE: MISINFORMATION INTELLIGENCE
# =============================================================================
elif selected_page == "Misinformation Intelligence":
    st.markdown("### 📱 SOCIAL INTELLIGENCE & MISINFORMATION ANALYSIS")

    # ── KPI cards ─────────────────────────────────────────────────────────────
    reports = st.session_state.get("reports", [])
    total_rpts = len(reports)
    genuine_rpts = sum(1 for r in reports if r.get("is_genuine", False))
    misleading_rpts = sum(1 for r in reports if not r.get("is_genuine", True))
    uncertain_rpts = total_rpts - genuine_rpts - misleading_rpts

    kpi_html2 = f"""
    <div class="kpi-grid">
        {render_kpi("Reports Analyzed", str(total_rpts), "this session", "positive", "DistilBERT")}
        {render_kpi("Likely Genuine", str(genuine_rpts), f"{(genuine_rpts/total_rpts*100):.0f}%" if total_rpts else "—", "positive", "P(genuine)≥0.5")}
        {render_kpi("Likely Misleading", str(misleading_rpts), f"{(misleading_rpts/total_rpts*100):.0f}%" if total_rpts else "—", "negative", "P(genuine)<0.5")}
        {render_kpi("Uncertain", str(uncertain_rpts), "0.35–0.65 range", "warning", "borderline")}
    </div>"""
    st.markdown(kpi_html2, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_input, col_ai = st.columns([1, 1])

    with col_input:
        # ── Social feed ingestion ──────────────────────────────────────────────
        st.markdown("#### 📥 SOCIAL REPORT INGESTION")

        # Source status
        x_status = label_live() if api_configured("x") else label_unavailable()
        reddit_status = label_live() if api_configured("reddit") else label_unavailable()

        st.markdown(
            f"{x_status}&nbsp;X/Twitter&nbsp;&nbsp;"
            f"{reddit_status}&nbsp;Reddit&nbsp;&nbsp;"
            f"{label_live()}&nbsp;GDELT News&nbsp;&nbsp;"
            f'{label_simulation()}&nbsp;Manual Input',
            unsafe_allow_html=True,
        )

        with st.expander("🌐 LIVE SOCIAL FEEDS (GDELT / X / Reddit)", expanded=False):
            feed_col1, feed_col2 = st.columns(2)
            with feed_col1:
                if st.button("📰 FETCH GDELT NEWS", use_container_width=True):
                    with st.spinner("Fetching GDELT disaster news..."):
                        gdelt_result = fetch_gdelt_news(max_results=8)
                        if gdelt_result["source"] == "GDELT_LIVE" and gdelt_result["reports"]:
                            for r in gdelt_result["reports"]:
                                add_report(r)
                            st.success(f"✅ {len(gdelt_result['reports'])} GDELT articles ingested. Run DistilBERT to classify.")
                            add_timeline_event(f"GDELT: {len(gdelt_result['reports'])} disaster news articles ingested.", "social")
                        elif gdelt_result["source"] == "GDELT_LIVE":
                            st.info("GDELT returned no matching articles.")
                        else:
                            st.error(f"GDELT unavailable: {gdelt_result.get('error', 'Unknown')}")

            with feed_col2:
                if not api_configured("x"):
                    st.markdown(
                        label_unavailable() + "&nbsp;X/Twitter: Set X_BEARER_TOKEN in .env",
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button("🐦 FETCH X REPORTS", use_container_width=True):
                        with st.spinner("Fetching X disaster reports..."):
                            x_result = fetch_x_reports()
                            if x_result["source"] == "X_LIVE":
                                for r in x_result["reports"]:
                                    add_report(r)
                                st.success(f"✅ {len(x_result['reports'])} X reports ingested.")
                            else:
                                st.error(f"X API error: {x_result.get('error', 'Unknown')}")

        # ── Manual report input ────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("**✏️ MANUAL REPORT INPUT**")
        st.markdown(
            label_simulation() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>Enter any disaster report text for DistilBERT classification</span>",
            unsafe_allow_html=True,
        )

        report_text = st.text_area(
            "Enter Report Text:",
            placeholder=(
                "Paste or type a disaster report here…\n"
                "Example: 'Huge flood in downtown. Cars are floating. Send help immediately!'"
            ),
            height=120,
            key="report_input",
        )

        tokenizer, nlp_model = _load_misinfo_model()
        model_ready = tokenizer is not None and nlp_model is not None
        if not model_ready:
            st.error("❌ DistilBERT model not loaded. Check models/misinformation_filter/")

        if st.button("🤖 RUN DISTILBERT VERIFICATION", use_container_width=True, disabled=not model_ready):
            if not report_text.strip():
                st.warning("⚠️ Please enter a report text before running verification.")
            else:
                with st.spinner("Running DistilBERT NLP embeddings..."):
                    cleaned = clean_text(report_text.strip())
                    result = run_distilbert(cleaned, tokenizer, nlp_model)
                    result["text"] = cleaned
                    result["timestamp"] = datetime.now().strftime("%H:%M:%S")
                    result["source_platform"] = "Manual Input"
                    add_report(result)
                    st.session_state["last_distilbert_result"] = result
                    add_timeline_event(
                        f"DistilBERT: '{cleaned[:55]}...' → "
                        f"{result['verification_status']} ({result['credibility_score']}%)",
                        "nlp",
                    )

        # ── Batch classify all pending reports ────────────────────────────────
        pending = [r for r in st.session_state.get("reports", []) if r.get("verification_status") == "UNVERIFIED"]
        if pending and model_ready:
            if st.button(f"🔄 CLASSIFY {len(pending)} PENDING REPORTS", use_container_width=True):
                with st.spinner(f"Classifying {len(pending)} reports with DistilBERT..."):
                    texts = [r.get("text", r.get("raw_text", "")) for r in pending]
                    results = batch_classify(texts, tokenizer, nlp_model)
                    # Update reports in state
                    for r, classified in zip(pending, results):
                        r.update(classified)
                    add_timeline_event(f"Batch DistilBERT: {len(pending)} reports classified.", "nlp")
                    st.success(f"✅ {len(pending)} reports classified.")
                    st.rerun()

        # ── Create incident from verified report ───────────────────────────────
        if st.session_state.get("last_distilbert_result"):
            res = st.session_state["last_distilbert_result"]
            if res.get("is_genuine"):
                st.markdown("---")
                st.markdown("**📍 Create Incident from This Report**")
                inc_loc = st.text_input("Location (required for incident)", "Location Unknown", key="rpt_loc")
                inc_type = st.selectbox(
                    "Disaster Type",
                    ["FLASH FLOOD", "CYCLONE", "EARTHQUAKE", "FIRE", "LANDSLIDE", "OTHER"],
                    key="rpt_type",
                )
                inc_people = st.number_input("Estimated People at Risk", 0, 100000, 0, key="rpt_people")
                if st.button("📌 CREATE INCIDENT FROM REPORT", use_container_width=True):
                    now = datetime.now()
                    sev = "HIGH" if res["credibility_score"] > 70 else "MEDIUM"
                    new_inc = {
                        "incident_id": get_next_incident_id(),
                        "disaster_type": inc_type,
                        "severity": sev,
                        "status": "ACTIVE",
                        "latitude": None,
                        "longitude": None,
                        "location": inc_loc,
                        "people_at_risk": int(inc_people),
                        "assigned_team": "Unassigned",
                        "created_at": now.strftime("%H:%M:%S"),
                        "updated_at": now.strftime("%H:%M:%S"),
                        "source": "DISTILBERT_VERIFIED",
                        "verification_status": "VERIFIED",
                        "description": res["text"][:200],
                        "alert_level": "Orange",
                    }
                    add_incident(new_inc)
                    add_timeline_event(
                        f"Incident {new_inc['incident_id']} created from DistilBERT-verified report — {inc_loc}.",
                        "incident",
                    )
                    st.success(
                        f"✅ Incident {new_inc['incident_id']} created. "
                        f"Note: No coordinates (text-only report). Incident in state but not mappable."
                    )

    with col_ai:
        if st.session_state.get("last_distilbert_result"):
            res = st.session_state["last_distilbert_result"]
            color = "#2EA043" if res["is_genuine"] else "#F85149"

            st.markdown(f'<div class="ai-card" style="border-top:4px solid {color};">', unsafe_allow_html=True)
            st.markdown(
                label_model() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>DistilBERT fine-tuned on Kaggle Disaster Tweets</span>",
                unsafe_allow_html=True,
            )
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:14px;">
                <div>
                    <div style="font-size:0.88rem;color:#8B949E;">CREDIBILITY SCORE</div>
                    <div class="ai-score" style="color:{color};">{res['credibility_score']}%</div>
                    <div style="font-size:0.73rem;color:#8B949E;">P(genuine disaster report)</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.88rem;color:#8B949E;">VERIFICATION STATUS</div>
                    <div style="font-size:1.15rem;font-weight:700;color:{color};">{res['verification_status']}</div>
                </div>
            </div>""", unsafe_allow_html=True)

            # Probability bars
            st.markdown(f"""
            <div style="margin-top:18px;">
                <div style="display:flex;justify-content:space-between;font-size:0.83rem;margin-bottom:3px;">
                    <span style="color:#2EA043;">P(genuine)</span>
                    <span style="font-family:monospace;">{res['prob_genuine']:.3f}</span>
                </div>
                <div style="background:#30363D;height:6px;border-radius:3px;margin-bottom:9px;">
                    <div style="background:#2EA043;height:100%;border-radius:3px;width:{int(res['prob_genuine']*100)}%;"></div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:0.83rem;margin-bottom:3px;">
                    <span style="color:#F85149;">P(misleading)</span>
                    <span style="font-family:monospace;">{res['prob_misleading']:.3f}</span>
                </div>
                <div style="background:#30363D;height:6px;border-radius:3px;margin-bottom:9px;">
                    <div style="background:#F85149;height:100%;border-radius:3px;width:{int(res['prob_misleading']*100)}%;"></div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:0.83rem;margin-bottom:3px;">
                    <span>Confidence (max prob)</span>
                    <span style="font-family:monospace;">{res['confidence']:.3f}</span>
                </div>
                <div style="background:#30363D;height:6px;border-radius:3px;">
                    <div style="background:#58A6FF;height:100%;border-radius:3px;width:{int(res['confidence']*100)}%;"></div>
                </div>
            </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div style="margin-top:18px;padding:10px;background:rgba(255,255,255,0.05);border-radius:6px;">
                <div style="font-size:0.83rem;color:#8B949E;margin-bottom:4px;">RECOMMENDED ACTION</div>
                <div style="font-weight:600;color:{color};">{res['recommended_action']}</div>
            </div>
            <div style="margin-top:8px;font-size:0.73rem;color:#8B949E;">
                ⚠️ MODEL CONFIDENCE ≠ FACTUAL TRUTH. DistilBERT detects whether text <i>resembles</i>
                a real disaster tweet (Kaggle training schema: label=1 → real disaster tweet, label=0 → not real).
                It does NOT independently verify the event. | Analyzed: {res.get('timestamp', '—')}
            </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="ai-card" style="text-align:center;color:#8B949E;padding:40px;">
                <h1 style="font-size:2.5rem;margin:0;">🤖</h1>
                <p style="margin-top:12px;">Enter a report and click RUN DISTILBERT VERIFICATION.</p>
            </div>""", unsafe_allow_html=True)

        # ── Report history ─────────────────────────────────────────────────────
        if reports:
            st.markdown("---")
            st.markdown("#### REPORT LOG")
            rpts_df_data = []
            for r in reversed(reports[-10:]):
                rpts_df_data.append({
                    "Time": r.get("timestamp", r.get("ingested_at", "—")),
                    "Source": r.get("source_platform", "Manual"),
                    "Status": r.get("verification_status", "UNVERIFIED"),
                    "Score": f"{r.get('credibility_score', '—')}%",
                    "Text": (r.get("text", r.get("raw_text", ""))[:60] + "..."),
                })
            st.dataframe(pd.DataFrame(rpts_df_data), use_container_width=True, hide_index=True)

    # ── NLP benchmark comparison ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### NLP MODEL BENCHMARKS (Kaggle Disaster Tweets Dataset)")
    st.caption("Metrics from evaluation on held-out validation split.")
    bc1, bc2, bc3 = st.columns(3)
    try:
        nlp_df = pd.read_csv("models/nlp_model_comparison.csv")
        with bc1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">TF-IDF + NAIVE BAYES</div>
                <div style="margin-top:12px;">
                    <div style="display:flex;justify-content:space-between;font-size:0.88rem;margin-bottom:4px;"><span>Accuracy</span><span>88.43%</span></div>
                    <div style="background:#30363D;height:4px;border-radius:2px;margin-bottom:12px;"><div style="background:#8B949E;height:100%;width:88.43%;"></div></div>
                    <div style="display:flex;justify-content:space-between;font-size:0.88rem;margin-bottom:4px;"><span>F1 Score</span><span>54.26%</span></div>
                    <div style="background:#30363D;height:4px;border-radius:2px;"><div style="background:#8B949E;height:100%;width:54.26%;"></div></div>
                </div>
            </div>""", unsafe_allow_html=True)
        with bc2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">TF-IDF + LOGISTIC REG.</div>
                <div style="margin-top:12px;">
                    <div style="display:flex;justify-content:space-between;font-size:0.88rem;margin-bottom:4px;"><span>Accuracy</span><span>88.39%</span></div>
                    <div style="background:#30363D;height:4px;border-radius:2px;margin-bottom:12px;"><div style="background:#8B949E;height:100%;width:88.39%;"></div></div>
                    <div style="display:flex;justify-content:space-between;font-size:0.88rem;margin-bottom:4px;"><span>F1 Score</span><span>54.17%</span></div>
                    <div style="background:#30363D;height:4px;border-radius:2px;"><div style="background:#8B949E;height:100%;width:54.17%;"></div></div>
                </div>
            </div>""", unsafe_allow_html=True)
        with bc3:
            st.markdown("""
            <div class="metric-card" style="border-color:#58A6FF;">
                <div class="metric-label" style="color:#58A6FF;">DISTILBERT (DEPLOYED)</div>
                <div style="margin-top:12px;">
                    <div style="display:flex;justify-content:space-between;font-size:0.88rem;margin-bottom:4px;"><span>Accuracy</span><span>84.12%</span></div>
                    <div style="background:#30363D;height:4px;border-radius:2px;margin-bottom:12px;"><div style="background:#58A6FF;height:100%;width:84.12%;"></div></div>
                    <div style="display:flex;justify-content:space-between;font-size:0.88rem;margin-bottom:4px;font-weight:600;color:#58A6FF;"><span>F1 Score (Critical)</span><span>83.50%</span></div>
                    <div style="background:#30363D;height:4px;border-radius:2px;"><div style="background:#58A6FF;height:100%;width:83.50%;"></div></div>
                </div>
            </div>""", unsafe_allow_html=True)
    except Exception:
        bc1.metric("TF-IDF + NB Accuracy", "88.43%")
        bc2.metric("TF-IDF + LR Accuracy", "88.39%")
        bc3.metric("DistilBERT F1 (Critical)", "83.50%")


# =============================================================================
# PAGE: MULTIMODAL ANALYSIS
# =============================================================================
elif selected_page == "Multimodal Analysis":
    st.markdown("### 👁️ DECISION-LEVEL MULTIMODAL FUSION")
    st.markdown(
        "<p style='color:#8B949E;'>Combining Computer Vision (ResNet-50) and NLP (DistilBERT) "
        "for multimodal damage assessment.</p>",
        unsafe_allow_html=True,
    )

    st.warning(
        "⚠️ **ResNet-50 Model Limitation:** Trained on **synthetic random-noise images** (500 samples). "
        "Predictions are **not reliable** for real-world damage assessment. "
        "Included as an architectural demonstration only.",
        icon="⚠️",
    )
    st.info(
        "ℹ️ **No Trained Fusion Model Exists.** `models/fusion_model/` is empty. "
        "Fusion is **transparent decision-level combination** (Vision × 0.6 + Text × 0.4) "
        "— not a neural attention model.",
        icon="ℹ️",
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    # ── Vision Module ─────────────────────────────────────────────────────────
    with col1:
        st.markdown("#### 📷 VISION INPUT (ResNet-50)")
        st.markdown(
            label_simulation() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>Trained on synthetic noise — indicative only</span>",
            unsafe_allow_html=True,
        )

        # Multi-image uploader (accept_multiple_files=True)
        uploaded_files = st.file_uploader(
            "Upload Crisis Scene Images (multiple allowed)",
            type=["jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif"],
            accept_multiple_files=True,
            help="Upload one or more images. Each is processed independently. Results are aggregated.",
        )

        img_model = _load_image_model()
        vision_result = None
        pil_images = []

        if uploaded_files:
            for uf in uploaded_files:
                try:
                    pil_images.append(Image.open(uf).convert("RGB"))
                except Exception as e:
                    st.warning(f"⚠️ Could not open {uf.name}: {e}")

        if pil_images:
            if img_model is None:
                st.error("❌ ResNet-50 model not loaded. Check models/image_model/resnet_damage.pth")
            else:
                # Show thumbnails
                thumb_cols = st.columns(min(len(pil_images), 3))
                for i, (uf, pil) in enumerate(zip(uploaded_files, pil_images)):
                    with thumb_cols[i % 3]:
                        st.image(pil, caption=f"#{i+1}: {uf.name}", use_container_width=True)

                # Classify all images
                with st.spinner(f"Running ResNet-50 on {len(pil_images)} image(s)..."):
                    if len(pil_images) == 1:
                        single = classify_single_image(pil_images[0], img_model)
                        # Adapt to multi-image schema for fusion
                        vision_result = {
                            **single,
                            "individual_results": [single],
                            "aggregate_score": single["damage_score"],
                            "aggregate_class": single["damage_class"],
                            "aggregate_class_idx": single["class_idx"],
                            "image_count": 1,
                            "severity_summary": {
                                "NO DAMAGE": 1 if single["class_idx"] == 0 else 0,
                                "MILD DAMAGE": 1 if single["class_idx"] == 1 else 0,
                                "SEVERE DAMAGE": 1 if single["class_idx"] == 2 else 0,
                            },
                        }
                    else:
                        vision_result = classify_multiple_images(pil_images, img_model)
                    st.session_state["vision_result"] = vision_result

            if vision_result:
                agg_class = vision_result["aggregate_class"]
                agg_score = vision_result["aggregate_score"]
                vis_color = "#F85149" if "SEVERE" in agg_class else ("#D29922" if "MILD" in agg_class else "#2EA043")
                n = vision_result["image_count"]
                summary = vision_result["severity_summary"]

                st.markdown(f"""
                <div class="metric-card" style="margin-top:10px;">
                    <div class="metric-label">VISUAL ASSESSMENT ({n} IMAGE{"S" if n>1 else ""})</div>
                    <div style="font-size:1.2rem;font-weight:700;color:{vis_color};margin:6px 0;">{agg_class}</div>
                    <div style="font-size:0.78rem;color:#8B949E;margin-bottom:8px;">
                        Confidence-weighted aggregate | Aggregation score: {agg_score:.3f}
                    </div>""", unsafe_allow_html=True)

                if n > 1:
                    st.markdown(f"""
                    <div style="font-size:0.8rem;color:#8B949E;margin-bottom:5px;">Per-image breakdown:</div>""",
                    unsafe_allow_html=True)
                    for j, ir in enumerate(vision_result["individual_results"]):
                        ic = "#F85149" if "SEVERE" in ir["damage_class"] else ("#D29922" if "MILD" in ir["damage_class"] else "#2EA043")
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:3px;">
                            <span>Image #{j+1}</span>
                            <span style="color:{ic};">{ir['damage_class']} ({ir['confidence']:.0%})</span>
                        </div>""", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="font-size:0.78rem;color:#8B949E;margin-top:6px;">
                        Summary: NO_DMG={summary['NO DAMAGE']} · MILD={summary['MILD DAMAGE']} · SEVERE={summary['SEVERE DAMAGE']}
                    </div>""", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

        elif not uploaded_files:
            st.session_state.pop("vision_result", None)
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">IMAGE INPUT (ResNet-50)</div>
                <div style="height:100px;background:#21262D;border:1px dashed #30363D;border-radius:6px;margin:12px 0;display:flex;align-items:center;justify-content:center;">
                    <div style="color:#8B949E;font-size:0.88rem;">[Awaiting Image Upload]</div>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Text Module ────────────────────────────────────────────────────────────
    with col2:
        st.markdown("#### 📝 TEXT INTELLIGENCE (DistilBERT)")
        st.markdown(
            label_model() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>Fine-tuned on Kaggle Disaster Tweets</span>",
            unsafe_allow_html=True,
        )

        text_report = st.text_area(
            "Enter Disaster Report Text:",
            placeholder="Enter the field report or witness statement here…\nExample: 'Severe bridge damage confirmed at Sector 4.'",
            height=110,
            key="multimodal_text",
        )

        tokenizer, nlp_model = _load_misinfo_model()
        text_result = None

        if st.button("🔍 RUN TEXT ANALYSIS", use_container_width=True):
            if not text_report.strip():
                st.warning("⚠️ Enter report text before running analysis.")
            elif tokenizer is None or nlp_model is None:
                st.error("❌ DistilBERT model not loaded.")
            else:
                with st.spinner("Running DistilBERT text analysis..."):
                    cleaned = clean_text(text_report.strip())
                    text_result = run_distilbert(cleaned, tokenizer, nlp_model)
                    st.session_state["multimodal_text_result"] = text_result
                    add_timeline_event(
                        f"Multimodal text: '{cleaned[:50]}...' → {text_result['verification_status']}",
                        "nlp",
                    )

        if st.session_state.get("multimodal_text_result"):
            tr = st.session_state["multimodal_text_result"]
            tc = "#2EA043" if tr["is_genuine"] else "#F85149"
            st.markdown(f"""
            <div class="metric-card" style="margin-top:10px;border-top:3px solid {tc};">
                <div class="metric-label">TEXT CLASSIFICATION</div>
                <div style="font-size:1.05rem;font-weight:700;color:{tc};margin:5px 0;">{tr['verification_status']}</div>
                <div style="display:flex;justify-content:space-between;font-size:0.82rem;margin-bottom:3px;"><span>P(genuine)</span><span style="font-family:monospace;color:#2EA043;">{tr['prob_genuine']:.3f}</span></div>
                <div style="background:#30363D;height:5px;border-radius:3px;margin-bottom:7px;"><div style="background:#2EA043;height:100%;border-radius:3px;width:{int(tr['prob_genuine']*100)}%;"></div></div>
                <div style="display:flex;justify-content:space-between;font-size:0.82rem;margin-bottom:3px;"><span>P(misleading)</span><span style="font-family:monospace;color:#F85149;">{tr['prob_misleading']:.3f}</span></div>
                <div style="background:#30363D;height:5px;border-radius:3px;"><div style="background:#F85149;height:100%;border-radius:3px;width:{int(tr['prob_misleading']*100)}%;"></div></div>
            </div>""", unsafe_allow_html=True)

        if st.button("🔄 Clear Text Result", use_container_width=True):
            st.session_state.pop("multimodal_text_result", None)
            st.rerun()

    # ── Fusion Engine ──────────────────────────────────────────────────────────
    with col3:
        st.markdown("#### 🔗 DECISION-LEVEL FUSION")
        st.markdown(
            label_model() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>Transparent rule-based fusion (no trained fusion model)</span>",
            unsafe_allow_html=True,
        )

        vr = st.session_state.get("vision_result") if uploaded_files else None
        tr = st.session_state.get("multimodal_text_result")

        fusion = run_fusion(vision_result=vr, text_result=tr)
        fusion_score = fusion["fusion_score"]
        fusion_color = fusion["fusion_color"]

        if vr is None and tr is None:
            st.markdown("""
            <div class="ai-card" style="text-align:center;color:#8B949E;padding:30px;">
                <div style="font-size:2rem;margin-bottom:10px;">🔗</div>
                <div>Upload image(s) and/or enter text + run analysis to activate fusion engine.</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="ai-card" style="border-left:4px solid {fusion_color};">
                <div class="metric-label">FUSION ENGINE OUTPUT</div>
                <div style="font-size:1.2rem;font-weight:700;color:{fusion_color};margin:10px 0;">{fusion['fusion_title']}</div>

                <div style="font-size:0.82rem;color:#8B949E;margin-bottom:3px;">Fusion Score</div>
                <div style="font-size:1.5rem;font-weight:700;color:{fusion_color};font-family:monospace;margin-bottom:7px;">{fusion_score:.3f}</div>
                <div style="background:#30363D;height:6px;border-radius:3px;margin-bottom:14px;">
                    <div style="background:{fusion_color};height:100%;border-radius:3px;width:{int(fusion_score*100)}%;"></div>
                </div>

                <div style="font-size:0.8rem;color:#8B949E;margin-bottom:2px;">Vision Input:</div>
                <div style="font-size:0.88rem;margin-bottom:8px;">{fusion['vision_label']}</div>
                <div style="font-size:0.78rem;color:#8B949E;margin-bottom:2px;">Vision contribution (×{0.6}):</div>
                <div style="font-size:0.82rem;font-family:monospace;color:{fusion_color};margin-bottom:10px;">{fusion['vision_contribution']:.4f}</div>

                <div style="font-size:0.8rem;color:#8B949E;margin-bottom:2px;">Text Input:</div>
                <div style="font-size:0.88rem;margin-bottom:8px;">{fusion['text_label']}</div>
                <div style="font-size:0.78rem;color:#8B949E;margin-bottom:2px;">Text contribution (×{0.4}):</div>
                <div style="font-size:0.82rem;font-family:monospace;color:{fusion_color};margin-bottom:10px;">{fusion['text_contribution']:.4f}</div>

                <div style="font-size:0.78rem;color:#8B949E;margin-bottom:3px;">Fusion Method:</div>
                <div style="font-size:0.8rem;margin-bottom:12px;">{fusion['fusion_method']}</div>

                <hr style="border-color:#30363D;margin:10px 0;">
                <div style="font-size:0.83rem;color:#8B949E;margin-bottom:4px;">RECOMMENDED ACTION</div>
                <div style="font-weight:600;color:{fusion_color};">{fusion['recommended_action']}</div>

                <div style="margin-top:10px;font-size:0.72rem;color:#8B949E;">
                    ⚠️ {fusion['limitation_notice']}
                </div>
            </div>""", unsafe_allow_html=True)

            if fusion_score >= 0.4:
                st.markdown("---")
                if st.button("📌 CREATE INCIDENT FROM FUSION", use_container_width=True):
                    now = datetime.now()
                    sev = "CRITICAL" if fusion_score >= 0.7 else "HIGH"
                    new_inc = {
                        "incident_id": get_next_incident_id(),
                        "disaster_type": "MULTIMODAL DETECTED",
                        "severity": sev,
                        "status": "ACTIVE",
                        "latitude": None,
                        "longitude": None,
                        "location": "LOCATION UNKNOWN — Multimodal Analysis",
                        "people_at_risk": 0,
                        "assigned_team": "Unassigned",
                        "created_at": now.strftime("%H:%M:%S"),
                        "updated_at": now.strftime("%H:%M:%S"),
                        "source": "MULTIMODAL_FUSION",
                        "verification_status": "VERIFIED",
                        "description": f"Fusion score: {fusion_score:.3f}. {fusion['fusion_method']}",
                        "alert_level": "Red" if sev == "CRITICAL" else "Orange",
                    }
                    add_incident(new_inc)
                    add_timeline_event(
                        f"Incident {new_inc['incident_id']} from multimodal fusion (score={fusion_score:.3f}). No coordinates.",
                        "incident",
                    )
                    st.success(f"✅ Incident {new_inc['incident_id']} added (no map coordinates — location unknown).")


# =============================================================================
# PAGE: RESCUE ROUTING
# =============================================================================
elif selected_page == "Rescue Routing":
    st.markdown("### 🚑 DYNAMIC RESCUE ROUTING & OPTIMIZATION")

    col_inc, col_map, col_route = st.columns([2, 5, 3])

    with col_inc:
        st.markdown("#### TARGET INCIDENT")

        active_incidents = [i for i in st.session_state["incidents"] if i["status"] == "ACTIVE"]
        mappable = [i for i in active_incidents if i.get("latitude") is not None and i.get("longitude") is not None]

        if not mappable:
            st.warning("No mappable active incidents. Add incidents with coordinates on the Command Center page.")
        else:
            inc_labels = {
                f"{i['incident_id']} — {i['disaster_type']} @ {i['location'][:22]}": i
                for i in mappable
            }
            sel_inc_label = st.selectbox("Select Incident", list(inc_labels.keys()), key="routing_incident")
            sel_inc = inc_labels[sel_inc_label]
            st.markdown(render_incident_card(sel_inc), unsafe_allow_html=True)

            st.markdown("#### RESCUE TEAM")
            avail_teams = [t for t in st.session_state["rescue_teams"] if t["status"] == "AVAILABLE"]
            if not avail_teams:
                st.warning("All rescue teams are dispatched.")
            else:
                team_labels = {t["name"]: t for t in avail_teams}
                sel_team_label = st.selectbox("Select Team", list(team_labels.keys()), key="routing_team")
                sel_team = team_labels[sel_team_label]
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">TEAM</div>
                    <div style="font-weight:600;margin:3px 0;">{sel_team['name']}</div>
                    <div style="font-size:0.83rem;color:#8B949E;">Status: {sel_team['status']}</div>
                    <div style="font-size:0.83rem;color:#8B949E;">Capacity: {sel_team['capacity']}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            btn1, btn2 = st.columns(2)
            with btn1:
                dispatch_clicked = st.button("🚨 DISPATCH TEAM", type="primary", use_container_width=True)
            with btn2:
                alt_clicked = st.button("🔄 ALTERNATE ROUTE", use_container_width=True)

            if dispatch_clicked and mappable and avail_teams:
                dispatch_team(sel_team["team_id"], sel_inc["incident_id"], route=None)
                route = calculate_route(
                    sel_team["longitude"], sel_team["latitude"],
                    sel_inc["longitude"], sel_inc["latitude"],
                    alternate=False,
                )
                st.session_state["last_route"] = {
                    "route": route,
                    "team": sel_team,
                    "incident": sel_inc,
                    "alternate": False,
                }
                eta_str = f"{route['duration_min']} min" if route["success"] else "Unknown"
                add_timeline_event(
                    f"Team {sel_team['team_id']} dispatched → {sel_inc['incident_id']} "
                    f"({sel_inc['disaster_type']}). Route: {route['route_type']}. ETA: {eta_str}.",
                    "dispatch",
                )
                if route["success"]:
                    st.success(f"✅ {sel_team['name']} dispatched. ETA: {eta_str} | {route['distance_km']} km")
                else:
                    st.warning(f"⚠️ Dispatched, but route failed: {route.get('error', 'Unknown')}")
                st.rerun()

            if alt_clicked:
                if st.session_state.get("last_route"):
                    prev = st.session_state["last_route"]
                    route = calculate_route(
                        prev["team"]["longitude"], prev["team"]["latitude"],
                        prev["incident"]["longitude"], prev["incident"]["latitude"],
                        alternate=True,
                    )
                    st.session_state["last_route"]["route"] = route
                    st.session_state["last_route"]["alternate"] = True
                    add_timeline_event(
                        f"Alternate route calculated: {prev['team']['team_id']} → {prev['incident']['incident_id']}.",
                        "routing",
                    )
                    if route["success"]:
                        st.info(f"🔄 Alternate: {route['distance_km']} km, {route['duration_min']} min.")
                    else:
                        st.warning(f"⚠️ Alternate route failed: {route.get('error', 'Unknown')}")
                else:
                    st.warning("⚠️ Dispatch a team first before requesting an alternate route.")

    with col_map:
        st.markdown("#### LIVE ROUTE MAP")
        if services["osrm"]:
            st.markdown(
                label_live() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>OSRM Open Routing — STANDARD ROAD ROUTES (not hazard-aware)</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                label_unavailable() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>OSRM offline — fallback straight-line shown</span>",
                unsafe_allow_html=True,
            )

        route_data = st.session_state.get("last_route")
        center = [20.305, 85.830]
        if route_data and route_data["route"]["success"]:
            pts = route_data["route"]["points"]
            if pts:
                center = [pts[len(pts)//2][0], pts[len(pts)//2][1]]

        m_route = folium.Map(location=center, zoom_start=13, tiles="OpenStreetMap")

        for inc in st.session_state["incidents"]:
            if inc["status"] == "ACTIVE" and inc.get("latitude") is not None:
                folium.CircleMarker(
                    [inc["latitude"], inc["longitude"]],
                    radius=8, color="#F85149", fill=True, fill_opacity=0.35,
                    popup=f"{inc['incident_id']}: {inc['disaster_type']}",
                ).add_to(m_route)
                folium.Marker(
                    [inc["latitude"], inc["longitude"]],
                    icon=folium.Icon(color="red", icon="info-sign"),
                    popup=inc["incident_id"],
                ).add_to(m_route)

        for team in st.session_state["rescue_teams"]:
            t_color = "blue" if team["status"] == "AVAILABLE" else "orange"
            folium.Marker(
                [team["latitude"], team["longitude"]],
                icon=folium.Icon(color=t_color, icon="truck", prefix="fa"),
                popup=f"{team['name']}: {team['status']}",
            ).add_to(m_route)

        if route_data:
            route = route_data["route"]
            if route["success"]:
                line_color = "#D29922" if route_data.get("alternate") else "#58A6FF"
                route_label = route.get("route_type", "STANDARD ROAD ROUTE")
                folium.PolyLine(
                    route["points"],
                    color=line_color, weight=5, opacity=0.85,
                    tooltip=f"{route_label} — {route['distance_km']} km / {route['duration_min']} min",
                ).add_to(m_route)
            else:
                # Straight-line fallback
                t = route_data["team"]
                i = route_data["incident"]
                folium.PolyLine(
                    [[t["latitude"], t["longitude"]], [i["latitude"], i["longitude"]]],
                    color="#8B949E", weight=3, dash_array="6,6", opacity=0.6,
                    tooltip="Direct line (OSRM unavailable)",
                ).add_to(m_route)

        st_folium(m_route, height=430, returned_objects=[])

    with col_route:
        st.markdown("#### ROUTE INTELLIGENCE")
        st.markdown(
            label_model() + "&nbsp;<span style='font-size:0.8rem;color:#8B949E;'>Computed from OSRM + incident state</span>",
            unsafe_allow_html=True,
        )

        route_data = st.session_state.get("last_route")

        if route_data:
            route = route_data["route"]
            team = route_data["team"]
            incident = route_data["incident"]
            route_type = route.get("route_type", "STANDARD ROAD ROUTE")

            if route["success"]:
                distance_km = route["distance_km"]
                duration_min = route["duration_min"]
                routing_source = "● OSRM API"
                routing_color = "#2EA043"
                eta_display = f"{duration_min} min"
                dist_display = f"{distance_km} km"
            else:
                routing_source = "○ OSRM UNAVAILABLE"
                routing_color = "#F85149"
                eta_display = "—"
                dist_display = "—"
                route_type = f"ERROR: {route.get('error', 'Unknown')[:40]}"

            st.markdown(f"""
            <div class="metric-card">
                <div style="display:flex;justify-content:space-between;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #30363D;">
                    <span style="color:#8B949E;font-size:0.83rem;">Routing Source</span>
                    <span style="font-weight:600;color:{routing_color};font-size:0.83rem;">{routing_source}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                    <span style="color:#8B949E;">Route Type</span>
                    <span style="font-weight:600;font-size:0.82rem;">{route_type}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                    <span style="color:#8B949E;">Dispatched Team</span>
                    <span style="font-weight:600;color:#58A6FF;font-size:0.85rem;">{team['name']}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                    <span style="color:#8B949E;">Target Incident</span>
                    <span style="font-weight:600;">{incident['incident_id']}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                    <span style="color:#8B949E;">ETA</span>
                    <span style="font-weight:700;font-size:1.15rem;color:#2EA043;">{eta_display}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                    <span style="color:#8B949E;">Distance</span>
                    <span style="font-weight:600;">{dist_display}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                    <span style="color:#8B949E;">En-route Hazards</span>
                    <span class="data-label-unavailable" style="font-size:0.7rem;">HAZARD DATA N/A</span>
                </div>
                <div style="margin-top:12px;padding:8px;background:rgba(139,148,158,0.1);border-radius:4px;border:1px solid rgba(139,148,158,0.3);color:#8B949E;font-size:0.8rem;text-align:center;">
                    ⚠️ OSRM provides standard road routes only.<br>
                    Hazard avoidance requires custom routing profiles with flood/blockage data.
                </div>
            </div>""", unsafe_allow_html=True)

            if route["success"]:
                st.markdown(f"""
                <div style="padding:8px;background:rgba(46,160,67,0.1);border-radius:6px;border:1px solid rgba(46,160,67,0.3);text-align:center;font-size:0.8rem;color:#2EA043;margin-top:8px;">
                    Fetched at: {route.get('fetched_at', '—')} | Source: OSRM (router.project-osrm.org)
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card" style="text-align:center;color:#8B949E;padding:25px;">
                <div style="font-size:1.8rem;margin-bottom:8px;">🚑</div>
                <div>Select an incident and dispatch a team to see route intelligence.</div>
            </div>""", unsafe_allow_html=True)

        # Team roster
        st.markdown("#### RESCUE TEAM ROSTER")
        for team in st.session_state["rescue_teams"]:
            s = team["status"]
            dot = "status-online" if s == "AVAILABLE" else ("status-offline" if s == "BUSY" else "status-warning")
            asgn = team.get("current_assignment") or "—"
            st.markdown(f"""
            <div style="padding:7px 0;border-bottom:1px solid #21262D;font-size:0.83rem;">
                <span class="status-dot {dot}"></span>
                <b>{team['team_id']}</b> — {s}
                <div style="color:#8B949E;font-size:0.75rem;margin-left:16px;">Assignment: {asgn}</div>
            </div>""", unsafe_allow_html=True)
