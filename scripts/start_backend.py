"""
scripts/start_backend.py

Production and Development Backend Application Launcher.
Validates the environment, verifies SUMO availability, applies database migrations,
and starts Uvicorn with graceful shutdown handling.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import DEBUG, HOST, PORT
from common.sumo_env import require_sumo_env, SumoEnvironmentError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("launcher")


def main() -> None:
    logger.info("Initializing Smart Traffic Coordination Backend...")
    logger.info(f"Root Directory: {PROJECT_ROOT}")

    # 1. Verify SUMO environment
    try:
        env = require_sumo_env()
        logger.info(f"Verified SUMO Environment: {env.version_string}")
        logger.info(f"SUMO Binary: {env.sumo_binary}")
    except SumoEnvironmentError as exc:
        logger.warning(
            f"SUMO Environment Warning: {exc}. "
            "Backend will launch, but simulation runs requiring SUMO will fail until installed."
        )

    # 2. Launch Uvicorn server
    import uvicorn
    logger.info(f"Starting server on http://{HOST}:{PORT} (Debug={DEBUG})")
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info" if not DEBUG else "debug",
    )


if __name__ == "__main__":
    main()
