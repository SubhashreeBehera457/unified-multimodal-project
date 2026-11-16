"""
backend/main.py
───────────────
FastAPI Entry Point for Unified Multimodal Disaster Management System.
Bridges existing ML models, real external APIs (GDACS, Open-Meteo, GDELT, OSRM),
and the modern React Command Center frontend.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.model_loader import model_manager
from backend.state import state_manager
from backend.api import (
    health,
    dashboard,
    incidents,
    weather,
    gdacs,
    risk,
    misinformation,
    vision,
    fusion,
    routing,
    social,
    teams,
)

from services.gdacs import fetch_gdacs_alerts

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load ML models in background thread or asynchronously
    logger.info("Initializing Disaster Operations Engine & Loading Machine Learning Models...")
    try:
        model_manager.load_all()
        logger.info("ML Models initialized successfully.")
    except Exception as e:
        logger.warning(f"Non-blocking model initialization notice: {e}")

    # Synchronize GDACS live global alerts asynchronously in background so server starts instantly
    async def _bg_gdacs_sync():
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: fetch_gdacs_alerts(max_events=250, timeout=12))
            if data.get("source") == "LIVE" and data.get("incidents"):
                added = state_manager.merge_gdacs_incidents(data["incidents"])
                logger.info(f"Startup: Synchronized {added} live global disaster alerts from GDACS RSS feed.")
        except Exception as e:
            logger.warning(f"Startup GDACS background sync notice: {e}")

    asyncio.create_task(_bg_gdacs_sync())

    yield

    logger.info("Disaster Operations Engine shutting down.")


app = FastAPI(
    title="Unified Multimodal Disaster Management System API",
    description="Real-time disaster response intelligence operations API bridging ML models and emergency services.",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS Configuration ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include API Routers under /api ─────────────────────────────────────────────
api_prefix = "/api"
app.include_router(health.router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)
app.include_router(incidents.router, prefix=api_prefix)
app.include_router(weather.router, prefix=api_prefix)
app.include_router(gdacs.router, prefix=api_prefix)
app.include_router(risk.router, prefix=api_prefix)
app.include_router(misinformation.router, prefix=api_prefix)
app.include_router(vision.router, prefix=api_prefix)
app.include_router(fusion.router, prefix=api_prefix)
app.include_router(routing.router, prefix=api_prefix)
app.include_router(social.router, prefix=api_prefix)
app.include_router(teams.router, prefix=api_prefix)


# ── Active WebSocket Connection Manager ──────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()


@app.websocket("/ws/live")
async def websocket_live_feed(websocket: WebSocket):
    """
    WebSocket endpoint for real-time telemetry updates.
    Sends live telemetry heartbeat every 3 seconds and responds to client pings.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Send live telemetry snapshot
            kpis = state_manager.get_kpis()
            recent_timeline = state_manager.get_timeline()[:3]
            payload = {
                "type": "TELEMETRY_PULSE",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "kpis": kpis,
                "latest_events": recent_timeline,
            }
            await websocket.send_json(payload)
            # Sleep 4 seconds between pulses
            await asyncio.sleep(4)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket client disconnected: {e}")
        ws_manager.disconnect(websocket)


@app.get("/")
def root():
    return {
        "system": "UNIFIED MULTIMODAL DISASTER MANAGEMENT SYSTEM",
        "tier": "FASTAPI INTELLIGENCE ENGINE",
        "version": "2.0.0",
        "documentation": "/docs",
        "health": "/api/health",
        "status": "OPERATIONAL",
    }
