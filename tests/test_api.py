"""
tests/test_api.py

Unit and integration tests for FastAPI REST API endpoints.
Tests health, simulation controls, input validation, signals, traffic metrics,
emergencies, risk zones, decisions, and comparisons.
"""

import pytest
from fastapi.testclient import TestClient

from backend.database import init_db
from backend.main import app
from backend.simulation_service import sim_service

client = TestClient(app)


def setup_module():
    """Initialize DB tables."""
    init_db()


def setup_function():
    """Ensure clean simulation state before each test."""
    sim_service.reset_simulation()


def teardown_function():
    """Clean up after test."""
    sim_service.stop_simulation()


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "sumo_available" in data
    assert "sumo_version" in data
    assert "active_simulation" in data


def test_simulation_status():
    response = client.get("/api/simulation/status")
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False
    assert data["paused"] is False
    assert data["simulation_time"] == 0.0
    assert "junctions" in data
    assert set(data["junctions"]) == {"J1", "J2", "J3"}


def test_simulation_start_validation():
    # Test invalid mode
    res_bad = client.post("/api/simulation/start", json={"mode": "invalid_mode"})
    assert res_bad.status_code == 400

    # Test invalid duration (< 10)
    res_short = client.post("/api/simulation/start", json={"duration": 5})
    assert res_short.status_code == 422  # Pydantic validation error


def test_traffic_live():
    response = client.get("/api/traffic/live")
    assert response.status_code == 200
    data = response.json()
    assert "simulation_time" in data
    assert "status" in data
    assert "junctions" in data
    assert "J1" in data["junctions"]
    assert "J2" in data["junctions"]
    assert "J3" in data["junctions"]


def test_traffic_metrics():
    response = client.get("/api/traffic/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_vehicles" in data
    assert "throughput_vehicles" in data
    assert "mean_speed_kmh" in data
    assert "total_co2_kg" in data
    assert "total_fuel_liters" in data


def test_signals_endpoint():
    response = client.get("/api/signals")
    assert response.status_code == 200
    data = response.json()
    assert "signals" in data
    assert "J1" in data["signals"]
    assert "J2" in data["signals"]
    assert "J3" in data["signals"]


def test_signal_override_validation():
    # Unconfirmed override should fail
    res_unconf = client.post(
        "/api/signals/override",
        json={"junction_id": "J2", "target_phase": 0, "confirmed": False},
    )
    assert res_unconf.status_code == 400
    assert "confirmation" in res_unconf.json()["detail"].lower()

    # Confirmed override when simulation is not running
    res_not_run = client.post(
        "/api/signals/override",
        json={"junction_id": "J2", "target_phase": 0, "confirmed": True},
    )
    assert res_not_run.status_code == 400
    assert "not currently running" in res_not_run.json()["detail"].lower()


def test_emergencies_endpoint():
    response = client.get("/api/emergencies")
    assert response.status_code == 200
    data = response.json()
    assert "active_emergency" in data
    assert "emergency_locked_junctions" in data
    assert "events" in data


def test_risks_endpoint():
    response = client.get("/api/risks")
    assert response.status_code == 200
    data = response.json()
    assert "total_zones" in data
    assert "risk_zones" in data
    assert "hotspots" in data
    assert len(data["risk_zones"]) >= 1


def test_decisions_endpoint():
    response = client.get("/api/decisions")
    assert response.status_code == 200
    data = response.json()
    assert "total_decisions" in data
    assert "decisions" in data
    assert len(data["decisions"]) >= 1


def test_experiments_compare():
    response = client.get("/api/experiments/compare")
    assert response.status_code == 200
    data = response.json()
    assert "controllers" in data
    names = [c["controller_name"] for c in data["controllers"]]
    assert "Fixed-Time Baseline" in names
    assert "Coordinated Adaptive Controller" in names

    ctrl_map = {c["controller_name"]: c for c in data["controllers"]}

    # If authoritative 10-seed benchmark is active
    if "Double-DQN (Stage A)" in ctrl_map:
        base = ctrl_map["Fixed-Time Baseline"]
        coord = ctrl_map["Coordinated Adaptive Controller"]
        dqn = ctrl_map["Double-DQN (Stage A)"]
        ppo = ctrl_map["PPO (Stage A)"]

        # In 10-seed benchmark:
        # Baseline ~ 90.02s, Coordinated ~ 49.87s, DQN ~ 56.64s, PPO ~ 85.50s
        assert pytest.approx(base["mean_travel_time_s"], 0.5) == 90.02
        assert pytest.approx(coord["mean_travel_time_s"], 0.5) == 49.87
        assert pytest.approx(dqn["mean_travel_time_s"], 0.5) == 56.64
        assert pytest.approx(ppo["mean_travel_time_s"], 0.5) == 85.50
        assert coord["mean_travel_time_s"] < base["mean_travel_time_s"]
        assert dqn["mean_travel_time_s"] < base["mean_travel_time_s"]
        assert coord["mean_travel_time_s"] < dqn["mean_travel_time_s"]

        # Authoritative fuel and delay assertions
        assert "Implemented" in base["status"] or "Reproduced" in base["status"]
        assert pytest.approx(base["total_fuel_liters"], 0.5) == 23.99
        assert base["total_fuel_liters"] < 50.0
        assert pytest.approx(coord["total_fuel_liters"], 0.5) == 18.44
        assert coord["total_fuel_liters"] < base["total_fuel_liters"]
        assert pytest.approx(dqn["total_fuel_liters"], 0.5) == 20.35
        assert dqn["total_fuel_liters"] < base["total_fuel_liters"]

        assert pytest.approx(base["cumulative_delay_veh_s"], 5.0) == 12373.2
        assert pytest.approx(coord["cumulative_delay_veh_s"], 5.0) == 5836.8
        assert coord["cumulative_delay_veh_s"] < base["cumulative_delay_veh_s"]
        assert pytest.approx(dqn["cumulative_delay_veh_s"], 5.0) == 8024.4
        assert dqn["cumulative_delay_veh_s"] < base["cumulative_delay_veh_s"]

        assert base["mean_instantaneous_waiting_time_s"] is not None
        assert base["cumulative_waiting_time_s"] is not None
        assert base["cumulative_delay_veh_s"] is not None
    else:
        # Legacy / fallback 5-seed benchmark
        assert "DQN (Deep Q-Network)" in names
        assert "PPO (Proximal Policy Optimization)" in names
        base = ctrl_map["Fixed-Time Baseline"]
        coord = ctrl_map["Coordinated Adaptive Controller"]
        dqn = ctrl_map["DQN (Deep Q-Network)"]
        ppo = ctrl_map["PPO (Proximal Policy Optimization)"]

        assert pytest.approx(base["total_fuel_liters"], 0.1) == 23.18
        assert base["total_fuel_liters"] < 50.0
        assert coord["mean_travel_time_s"] < base["mean_travel_time_s"]
        assert dqn["completed_trips"] == 0.0
        assert pytest.approx(ppo["mean_travel_time_s"], 0.1) == 65.15


def test_experiments_marl_summary():
    response = client.get("/api/experiments/marl-summary")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "fuel_density_model" in data
    assert "0.750 kg/L" in data["fuel_density_model"]

    metrics = {r["metric"]: r for r in data["summary"]}
    assert "total_fuel_liters" in metrics
    fuel_row = metrics["total_fuel_liters"]
    assert pytest.approx(fuel_row["baseline"], 0.1) == 23.18
    assert pytest.approx(fuel_row["coordinated"], 0.1) == 18.39
    assert pytest.approx(fuel_row["marl_ppo"], 0.1) == 26.55
    assert pytest.approx(fuel_row["marl_dqn"], 0.1) == 34.15

    assert "total_corridor_waiting_time_s" in metrics
    assert "cumulative_waiting_time_s" in metrics


def test_experiments_marl_detailed():
    response = client.get("/api/experiments/marl-detailed")
    assert response.status_code == 200
    data = response.json()
    assert "seeds" in data
    assert data["seeds"] == [1, 2, 3, 4, 5]
    assert "provenance_metadata" in data
    assert "fuel_density_model" in data
    assert "runs" in data
    assert "baseline" in data["runs"]
    assert "coordinated" in data["runs"]
    assert "marl_dqn" in data["runs"]
    assert "marl_ppo" in data["runs"]
    assert len(data["runs"]["baseline"]) == 5
    assert len(data["runs"]["coordinated"]) == 5
    assert len(data["runs"]["marl_dqn"]) == 5
    assert len(data["runs"]["marl_ppo"]) == 5


def test_experiments_history():
    response = client.get("/api/experiments/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
