"""
scripts/verify_environment.py

Comprehensive Environment & Dependency Verification Script for
the Smart Traffic Coordination System (Silk Board Corridor).

Checks:
1. Python runtime (>= 3.11)
2. Eclipse SUMO discovery, version, and tools (TraCI, sumolib)
3. PyTorch installation, version, and compute device
4. Core scientific and web libraries
5. SUMO network, demand, and configuration assets
6. Pre-trained MARL checkpoints integrity
7. SQLite database connection
8. Node.js & npm tooling for frontend
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def check_python() -> tuple[bool, str]:
    ver = sys.version_info
    ver_str = f"{ver.major}.{ver.minor}.{ver.micro}"
    ok = (ver.major == 3 and ver.minor >= 11)
    msg = f"Python {ver_str} ({'compatible' if ok else 'REQUIRES >= 3.11'})"
    return ok, msg


def check_sumo() -> tuple[bool, str]:
    try:
        from common.sumo_env import require_sumo_env
        env = require_sumo_env()
        # Verify tools import
        import traci
        import sumolib
        return True, f"{env.version_string} at {env.sumo_binary} (TraCI + sumolib OK)"
    except Exception as exc:
        return False, f"SUMO Error: {exc}"


def check_pytorch() -> tuple[bool, str]:
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return True, f"PyTorch {torch.__version__} (Device: {device})"
    except ImportError:
        return False, "PyTorch not installed"


def check_dependencies() -> tuple[bool, str]:
    required = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("sqlalchemy", "SQLAlchemy"),
        ("numpy", "NumPy"),
        ("scipy", "SciPy"),
        ("scikit-learn", "scikit-learn"),
        ("websockets", "WebSockets"),
    ]
    missing = []
    versions = []
    import importlib.metadata
    for pkg_name, disp in required:
        try:
            ver = importlib.metadata.version(pkg_name)
            versions.append(f"{disp} {ver}")
        except importlib.metadata.PackageNotFoundError:
            missing.append(disp)

    if missing:
        return False, f"Missing: {', '.join(missing)}"
    return True, f"All core packages present ({len(versions)} packages verified)"


def check_corridor_assets() -> tuple[bool, str]:
    cfg = PROJECT_ROOT / "sumo" / "silk_board" / "silk_board.sumocfg"
    net = PROJECT_ROOT / "sumo" / "silk_board" / "network" / "silk_board.net.xml"
    rou = PROJECT_ROOT / "sumo" / "silk_board" / "demand" / "silk_board.rou.xml"

    missing = [str(p.name) for p in [cfg, net, rou] if not p.is_file()]
    if missing:
        return False, f"Missing SUMO files: {', '.join(missing)}"
    return True, "Corridor configuration, network, and demand files verified"


def check_checkpoints() -> tuple[bool, str]:
    dqn = PROJECT_ROOT / "checkpoints" / "p6" / "dqn_stage_a_best.json"
    ppo = PROJECT_ROOT / "checkpoints" / "p6" / "ppo_stage_a_best.json"

    missing = [str(p.name) for p in [dqn, ppo] if not p.is_file()]
    if missing:
        return False, f"Missing checkpoints: {', '.join(missing)}"
    return True, "MARL Stage A best checkpoints verified (DQN & PPO)"


def check_database() -> tuple[bool, str]:
    try:
        from backend.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "SQLite database engine connected and responsive"
    except Exception as exc:
        return False, f"Database error: {exc}"


def check_node_npm() -> tuple[bool, str]:
    node = shutil.which("node")
    npm = shutil.which("npm")
    if not node or not npm:
        return False, "Node.js or npm not found in PATH"

    try:
        n_ver = subprocess.check_output([node, "--version"], text=True).strip()
        npm_ver = subprocess.check_output([npm, "--version"], text=True).strip()
        return True, f"Node {n_ver}, npm {npm_ver}"
    except Exception as exc:
        return False, f"Node check error: {exc}"


def main() -> int:
    checks = [
        ("Python Runtime", check_python),
        ("Eclipse SUMO & TraCI", check_sumo),
        ("PyTorch & Accelerators", check_pytorch),
        ("Python Dependencies", check_dependencies),
        ("Corridor Assets", check_corridor_assets),
        ("MARL Checkpoints", check_checkpoints),
        ("Database Engine", check_database),
        ("Node.js & npm (Frontend)", check_node_npm),
    ]

    print("=" * 80)
    print("SMART TRAFFIC COORDINATION SYSTEM — ENVIRONMENT VERIFICATION")
    print(f"Project Root: {PROJECT_ROOT}")
    print("=" * 80)

    all_passed = True
    for name, check_fn in checks:
        ok, msg = check_fn()
        status = "[  OK  ]" if ok else "[ FAIL ]"
        print(f"{status} {name:<26} : {msg}")
        if not ok:
            all_passed = False

    print("=" * 80)
    if all_passed:
        print("ENVIRONMENT STATUS: ALL VERIFICATION CHECKS PASSED (Ready for operation)")
        return 0
    else:
        print("ENVIRONMENT STATUS: ONE OR MORE CHECKS FAILED (Review above errors)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
