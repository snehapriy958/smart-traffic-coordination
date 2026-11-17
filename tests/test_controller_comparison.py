"""
tests/test_controller_comparison.py

Regression test suite for the Controller Comparison endpoint (GET /api/experiments/compare).
Verifies:
1. Status is "Implemented" for all operational controllers (not "Not implemented").
2. Capability fields: is_implemented, available_for_inference, has_trained_checkpoint.
3. Authoritative 10-seed master benchmark (N=10 seeds, 900s window, 109 completed trips).
4. Double-DQN uses valid Stage A master benchmark metrics (56.64s TT, 109 trips), not 0 trips.
5. Preserved historical 5-seed benchmark available in historical_5seed_controllers.
6. MAPPO is NOT in the 4-controller master benchmark.
"""

from __future__ import annotations

from backend.routers.experiments import get_controller_comparison
from backend.schemas import ExperimentCompareResponse


def test_controller_comparison_schema_and_metadata():
    """Verifies that get_controller_comparison returns Authoritative 10-seed metadata and 4 canonical controllers."""
    resp = get_controller_comparison()
    assert isinstance(resp, ExperimentCompareResponse)

    # Benchmark metadata
    assert resp.benchmark_name == "Authoritative 10-Seed Master Benchmark"
    assert resp.benchmark_duration_s == 900
    assert resp.seeds_count == 10

    controllers = resp.controllers
    assert len(controllers) == 4, f"Expected 4 controllers, got {len(controllers)}"

    ctrl_names = [c.controller_name for c in controllers]
    assert "Fixed-Time Baseline" in ctrl_names
    assert "Coordinated Adaptive Controller" in ctrl_names
    assert "Double-DQN (Stage A)" in ctrl_names
    assert "PPO (Stage A)" in ctrl_names

    # MAPPO must NOT be in the 4-controller master benchmark
    assert not any("MAPPO" in name for name in ctrl_names), "MAPPO must not be in the 4-controller master benchmark"


def test_all_controllers_implemented_and_capable():
    """Verifies that all 4 controllers have is_implemented=True and available_for_inference=True."""
    resp = get_controller_comparison()
    assert isinstance(resp, ExperimentCompareResponse)

    for c in resp.controllers:
        # None should be "Not implemented"
        assert c.status == "Implemented", f"Expected Implemented for {c.controller_name}, got {c.status}"
        assert c.is_implemented is True, f"Expected is_implemented=True for {c.controller_name}"
        assert c.available_for_inference is True, f"Expected available_for_inference=True for {c.controller_name}"

    # Verify checkpoint flags
    by_name = {c.controller_name: c for c in resp.controllers}
    assert by_name["Fixed-Time Baseline"].has_trained_checkpoint is False
    assert by_name["Coordinated Adaptive Controller"].has_trained_checkpoint is False
    assert by_name["Double-DQN (Stage A)"].has_trained_checkpoint is True
    assert by_name["PPO (Stage A)"].has_trained_checkpoint is True


def test_dqn_stage_a_master_benchmark_metrics():
    """Verifies that Double-DQN reflects valid Stage A metrics, not the old zero-trip prototype."""
    resp = get_controller_comparison()
    by_name = {c.controller_name: c for c in resp.controllers}

    dqn = by_name["Double-DQN (Stage A)"]
    assert dqn.mean_travel_time_s == 56.64, f"Expected 56.64s travel time, got {dqn.mean_travel_time_s}"
    assert dqn.mean_speed_kmh == 31.46, f"Expected 31.46 km/h, got {dqn.mean_speed_kmh}"
    assert dqn.completed_trips == 109.0, f"Expected 109 completed trips, got {dqn.completed_trips}"
    assert dqn.mean_queue == 8.92


def test_historical_5seed_benchmark_preserved():
    """Verifies that the historical 5-seed benchmark is preserved under historical_5seed_controllers."""
    resp = get_controller_comparison()
    hist = resp.historical_5seed_controllers
    assert hist is not None
    assert len(hist) == 4

    hist_by_name = {c.controller_name: c for c in hist}
    # Double-DQN in historical list is marked as Historical Artifact with 0 completed trips
    dqn_hist = hist_by_name["Double-DQN (Historical 8-Ep Prototype)"]
    assert dqn_hist.status == "Historical Artifact"
    assert dqn_hist.completed_trips == 0.0
    assert dqn_hist.mean_travel_time_s is None
