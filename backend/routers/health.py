"""
backend/routers/health.py

Health check, environment status, and Kubernetes/container readiness endpoints.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Response, status
from sqlalchemy import text

from backend.config import BASE_DIR, SUMO_CONFIG_PATH
from backend.database import engine
from backend.schemas import HealthResponse, ReadinessResponse
from backend.simulation_service import sim_service
from common.sumo_env import require_sumo_env, SumoEnvironmentError

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Returns backend system status, SUMO binary availability, and simulation state."""
    sumo_ok = False
    version_str = "Unavailable"
    try:
        env = require_sumo_env()
        sumo_ok = True
        version_str = env.version_string
    except SumoEnvironmentError as e:
        version_str = str(e)

    status_obj = sim_service.get_status()

    return HealthResponse(
        status="ok",
        sumo_available=sumo_ok,
        sumo_version=version_str,
        active_simulation=status_obj.running,
        message="Backend and coordination service active.",
    )


@router.get("/readiness", response_model=ReadinessResponse)
@router.get("/ready", response_model=ReadinessResponse)
def get_readiness(response: Response) -> ReadinessResponse:
    """
    Evaluates whether the service is ready to accept simulation workloads.
    Verifies SUMO binary, corridor configuration XML, SQLite database, and ML checkpoints.
    Returns 200 OK when ready, 503 SERVICE UNAVAILABLE when dependencies are missing.
    """
    details: Dict[str, Any] = {}

    # 1. SUMO binary verification
    sumo_ready = False
    try:
        env = require_sumo_env()
        sumo_ready = True
        details["sumo"] = {
            "version": env.version_string,
            "binary": str(env.sumo_binary),
            "home": str(env.sumo_home),
        }
    except Exception as exc:
        details["sumo"] = {"error": str(exc)}

    # 2. Corridor configuration & network file check
    config_ready = SUMO_CONFIG_PATH.is_file()
    details["config"] = {
        "path": str(SUMO_CONFIG_PATH),
        "exists": config_ready,
    }

    # 3. Database connection check
    database_ready = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        database_ready = True
        details["database"] = {"status": "connected"}
    except Exception as exc:
        details["database"] = {"error": str(exc)}

    # 4. Checkpoints check
    dqn_chk = BASE_DIR / "checkpoints" / "p6" / "dqn_stage_a_best.json"
    ppo_chk = BASE_DIR / "checkpoints" / "p6" / "ppo_stage_a_best.json"
    checkpoints_ready = dqn_chk.is_file() and ppo_chk.is_file()
    details["checkpoints"] = {
        "dqn_stage_a": dqn_chk.is_file(),
        "ppo_stage_a": ppo_chk.is_file(),
    }

    is_all_ready = sumo_ready and config_ready and database_ready and checkpoints_ready
    if not is_all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_all_ready else "not_ready",
        sumo_ready=sumo_ready,
        config_ready=config_ready,
        database_ready=database_ready,
        checkpoints_ready=checkpoints_ready,
        details=details,
    )
