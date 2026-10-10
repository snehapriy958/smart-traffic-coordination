"""
backend/main.py

FastAPI Application Entry Point.
Configures CORS, lifespan initialization, REST routers, and WebSocket telemetry stream.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import CORS_ORIGINS, DEBUG
from backend.database import init_db
from backend.routers import (
    decisions,
    emergencies,
    experiments,
    health,
    risks,
    signals,
    simulation,
    traffic,
)
from backend.simulation_service import sim_service
from backend.websocket_manager import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup initialization and graceful shutdown."""
    # 1. Initialize Database schema and pre-seed risk zones
    init_db()

    # 2. Provide running event loop to simulation service for WebSocket broadcasts
    loop = asyncio.get_running_loop()
    sim_service.set_event_loop(loop)

    yield

    # 3. Shutdown: ensure TraCI and background simulation thread are terminated
    sim_service.stop_simulation()


app = FastAPI(
    title="Smart Traffic Coordination API",
    description="Intelligent Traffic Management and Multi-Intersection Coordination Platform for Bengaluru's Silk Board Corridor.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST Routers
app.include_router(health.router)
app.include_router(simulation.router)
app.include_router(traffic.router)
app.include_router(signals.router)
app.include_router(emergencies.router)
app.include_router(risks.router)
app.include_router(decisions.router)
app.include_router(experiments.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "Smart Traffic Coordination System",
        "corridor": "Bengaluru Silk Board (J1 -> J2 -> J3)",
        "docs": "/docs",
        "health": "/api/health",
        "websocket": "/ws/traffic",
    }


# ----------------------------------------------------
# WebSocket Endpoint: WS /ws/traffic
# ----------------------------------------------------

@app.websocket("/ws/traffic")
async def websocket_traffic_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket telemetry stream.
    Broadcasts simulation time, queues, vehicle counts, signal states, emissions,
    emergency preemption status, and controller decisions while running.
    """
    await ws_manager.connect(websocket)
    try:
        # Send immediate initial state upon connection
        st = sim_service.get_status()
        initial_payload = {
            "type": "INITIAL_STATE",
            "simulation_time": st.simulation_time,
            "status": "RUNNING" if st.running and not st.paused else ("PAUSED" if st.paused else "STOPPED"),
            "mode": st.mode,
            "metrics": sim_service.get_metrics(),
            "junctions": sim_service.get_live_junctions(),
            "signals": sim_service.get_signals(),
            "emergencies": sim_service.get_emergencies(),
            "decisions": [d.model_dump() for d in sim_service.get_decisions()[-5:]],
        }
        await websocket.send_json(initial_payload)

        # Keep connection open and listen for optional client pings/messages
        while True:
            client_msg = await websocket.receive_text()
            if client_msg.strip().lower() == "ping":
                await websocket.send_json({"type": "PONG"})
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
