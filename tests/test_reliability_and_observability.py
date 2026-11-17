"""
tests/test_reliability_and_observability.py

Tests for Phase 1 Engineering Foundation enhancements:
- Container readiness probe (/api/readiness, /api/ready)
- Security hardening headers (X-Content-Type-Options, X-Frame-Options, etc.)
- Request latency timing headers (X-Process-Time)
- Environment verification programmatic integrity
"""

import re
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from scripts.verify_environment import (
    check_corridor_assets,
    check_checkpoints,
    check_database,
    check_dependencies,
    check_python,
    check_pytorch,
    check_sumo,
)

client = TestClient(app)


def test_readiness_endpoint():
    """Verifies that /api/readiness evaluates dependencies and returns ready state."""
    response = client.get("/api/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["sumo_ready"] is True
    assert data["config_ready"] is True
    assert data["database_ready"] is True
    assert data["checkpoints_ready"] is True
    assert "details" in data
    assert "sumo" in data["details"]
    assert "config" in data["details"]


def test_ready_alias_endpoint():
    """Verifies that the /api/ready alias functions identically to /api/readiness."""
    response = client.get("/api/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_security_headers_present():
    """Verifies that standard HTTP security headers are injected into responses."""
    response = client.get("/api/health")
    assert response.status_code == 200
    headers = response.headers

    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_process_time_header():
    """Verifies that X-Process-Time header is injected with valid numeric format."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "x-process-time" in response.headers
    val = response.headers["x-process-time"]
    assert re.match(r"^\d+\.\d+ms$", val) is not None


def test_environment_verification_checks():
    """Verifies that the environment verification modules all pass on the current machine."""
    py_ok, _ = check_python()
    assert py_ok is True

    sumo_ok, _ = check_sumo()
    assert sumo_ok is True

    torch_ok, _ = check_pytorch()
    assert torch_ok is True

    dep_ok, _ = check_dependencies()
    assert dep_ok is True

    assets_ok, _ = check_corridor_assets()
    assert assets_ok is True

    chk_ok, _ = check_checkpoints()
    assert chk_ok is True

    db_ok, _ = check_database()
    assert db_ok is True
