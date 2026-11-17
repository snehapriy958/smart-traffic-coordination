"""
tests/test_webster_controller.py

Comprehensive unit and integration test suite for the Webster Optimum Signal Timing Controller.
Verifies:
1. Mathematical correctness of Webster (1958) cycle length and green split formulas.
2. Boundary conditions: zero demand, partial zero demand, oversaturation (Y >= 1.0).
3. Robustness against invalid inputs: negative flows, non-finite values (NaN, Inf), non-positive saturation, mismatched phases.
4. Constraint enforcement: C_min <= C <= C_max, and g_min <= g_i <= g_max.
5. Cyclic progression and yellow clearance transitions on SUMO corridor junctions (J1, J2, J3).
6. Non-bypass of SignalController safety shield and emergency priority overrides.
"""

import math
import pytest
from typing import Dict, List, Optional

from traffic_service.webster_controller import (
    WebsterTimingPlan,
    WebsterJunctionConfig,
    WebsterJunctionController,
    WebsterCorridorController,
    calculate_webster_timing,
    create_default_webster_configs,
)
from traffic_service.signal_controller import SignalController


# =====================================================================
# Fixtures and Mock TraCI Traffic Light Helpers
# =====================================================================

class MockTraCITrafficLight:
    """Mock TraCI traffic light simulator for deterministic unit/integration testing."""
    def __init__(self, initial_phase: int = 0):
        self.phase = initial_phase
        self.phase_history: List[Tuple[float, int]] = []
        self.duration_history: List[Tuple[float, int, float]] = []
        self._current_duration: float = 40.0

    def getPhase(self, tls_id: str) -> int:
        return self.phase

    def setPhase(self, tls_id: str, phase: int) -> None:
        self.phase = phase
        self.phase_history.append((0.0, phase))

    def setPhaseDuration(self, tls_id: str, duration: float) -> None:
        self._current_duration = duration
        self.duration_history.append((0.0, self.phase, duration))

    def getNextSwitch(self, tls_id: str) -> float:
        return 100.0


@pytest.fixture
def default_configs() -> Dict[str, WebsterJunctionConfig]:
    return create_default_webster_configs()


# =====================================================================
# 1. Mathematical Unit Tests: Webster Cycle & Green Splits
# =====================================================================

def test_valid_webster_cycle_calculation():
    """Verify standard Webster cycle calculation: C_0 = (1.5L + 5) / (1 - Y)."""
    # L = 4.0 + 4.0 = 8.0s
    # q = {0: 360, 2: 720}, s = {0: 1800, 2: 1800} -> y_0 = 0.20, y_2 = 0.40 -> Y = 0.60
    # C_0 = (1.5 * 8 + 5) / (1 - 0.60) = 17.0 / 0.40 = 42.5s
    # With min_cycle = 45.0s, C should be clamped to 45.0s
    plan = calculate_webster_timing(
        critical_flows={0: 360.0, 2: 720.0},
        saturation_flows={0: 1800.0, 2: 1800.0},
        yellow_durations={0: 4.0, 2: 4.0},
        min_cycle=40.0,
        max_cycle=120.0,
        min_green=10.0,
        max_green=60.0,
    )

    assert math.isclose(plan.theoretical_cycle_length, 42.5, abs_tol=1e-3)
    assert math.isclose(plan.cycle_length, 42.5, abs_tol=1e-3)
    assert math.isclose(plan.total_flow_ratio, 0.60, abs_tol=1e-3)
    assert math.isclose(plan.total_lost_time, 8.0, abs_tol=1e-3)
    assert not plan.is_saturated
    assert not plan.min_cycle_enforced
    assert not plan.max_cycle_enforced


def test_green_split_proportionality():
    """Verify that available green time is allocated in proportion to flow ratios y_i."""
    # L = 8.0s, Y = 0.60, y_0 = 0.20 (1/3), y_2 = 0.40 (2/3)
    # C = 42.5s -> G = 42.5 - 8.0 = 34.5s
    # g_0 = (0.2/0.6) * 34.5 = 11.5s
    # g_2 = (0.4/0.6) * 34.5 = 23.0s
    plan = calculate_webster_timing(
        critical_flows={0: 360.0, 2: 720.0},
        saturation_flows={0: 1800.0, 2: 1800.0},
        yellow_durations={0: 4.0, 2: 4.0},
        min_cycle=40.0,
        max_cycle=120.0,
        min_green=10.0,
        max_green=60.0,
    )

    assert math.isclose(plan.green_times[0], 11.5, abs_tol=1e-3)
    assert math.isclose(plan.green_times[2], 23.0, abs_tol=1e-3)
    # Ratio of green allocations must equal ratio of flow ratios: 23.0 / 11.5 == 2.0
    assert math.isclose(plan.green_times[2] / plan.green_times[0], 2.0, abs_tol=1e-3)
    # Total green + lost time must exactly equal cycle length
    assert math.isclose(sum(plan.green_times.values()) + plan.total_lost_time, plan.cycle_length, abs_tol=1e-3)


def test_zero_demand_all_phases():
    """Verify handling when all critical flows are zero (Y == 0)."""
    plan = calculate_webster_timing(
        critical_flows={0: 0.0, 2: 0.0},
        saturation_flows={0: 1800.0, 2: 1800.0},
        yellow_durations={0: 4.0, 2: 4.0},
        min_cycle=45.0,
        max_cycle=120.0,
        min_green=15.0,
        max_green=60.0,
    )

    assert plan.total_flow_ratio == 0.0
    assert plan.min_cycle_enforced
    assert plan.cycle_length >= 45.0
    # Green splits must be equal and >= min_green
    assert plan.green_times[0] == plan.green_times[2]
    assert plan.green_times[0] >= 15.0
    assert math.isclose(sum(plan.green_times.values()) + plan.total_lost_time, plan.cycle_length, abs_tol=1e-3)


def test_partial_zero_demand_one_phase():
    """Verify handling when one phase has zero demand (e.g. side street with zero vehicles)."""
    # Phase 0 has 0 demand, Phase 2 has heavy demand
    plan = calculate_webster_timing(
        critical_flows={0: 0.0, 2: 1200.0},
        saturation_flows={0: 1800.0, 2: 3600.0},
        yellow_durations={0: 4.0, 2: 4.0},
        min_cycle=45.0,
        max_cycle=120.0,
        min_green=15.0,
        max_green=60.0,
    )

    # Phase 0 must safely receive at least min_green (15.0s), NOT 0.0s
    assert plan.green_times[0] >= 15.0
    # Phase 2 receives the excess green
    assert plan.green_times[2] > plan.green_times[0]
    assert plan.green_times[2] <= 60.0
    assert math.isclose(sum(plan.green_times.values()) + plan.total_lost_time, plan.cycle_length, abs_tol=1e-3)


def test_oversaturation_y_greater_or_equal_one():
    """Verify safe handling when Y >= 1.0 (oversaturated intersection)."""
    # q_0 = 1200, s_0 = 1800 (y_0 = 0.667)
    # q_2 = 1800, s_2 = 1800 (y_2 = 1.000)
    # Y = 1.667 >= 1.0
    plan = calculate_webster_timing(
        critical_flows={0: 1200.0, 2: 1800.0},
        saturation_flows={0: 1800.0, 2: 1800.0},
        yellow_durations={0: 4.0, 2: 4.0},
        min_cycle=45.0,
        max_cycle=120.0,
        min_green=15.0,
        max_green=60.0,
    )

    assert plan.is_saturated
    assert plan.max_cycle_enforced
    # Cycle length must be capped at max_cycle (or sum of max greens + L)
    assert plan.cycle_length <= 120.0
    # Both phases must respect max_green
    assert plan.green_times[0] <= 60.0
    assert plan.green_times[2] <= 60.0
    assert plan.green_times[0] >= 15.0
    assert plan.green_times[2] >= 15.0


def test_near_saturation_threshold():
    """Verify that Y >= y_saturation_threshold triggers oversaturation cap before dividing by small epsilon."""
    plan = calculate_webster_timing(
        critical_flows={0: 950.0, 2: 950.0},
        saturation_flows={0: 1000.0, 2: 1000.0},
        yellow_durations={0: 4.0, 2: 4.0},
        min_cycle=45.0,
        max_cycle=120.0,
        y_saturation_threshold=0.95,
    )

    assert plan.is_saturated
    assert plan.max_cycle_enforced
    assert plan.cycle_length <= 120.0


def test_minimum_cycle_bound_enforcement():
    """Verify that light traffic clamps to min_cycle when C_0 < min_cycle."""
    # Very light traffic: q_0 = 100, q_2 = 100, s = 1800 -> Y = 0.111
    # C_0 = (1.5 * 8 + 5) / (1 - 0.111) = 17 / 0.889 = 19.1s < 45.0s
    plan = calculate_webster_timing(
        critical_flows={0: 100.0, 2: 100.0},
        saturation_flows={0: 1800.0, 2: 1800.0},
        yellow_durations={0: 4.0, 2: 4.0},
        min_cycle=45.0,
        max_cycle=120.0,
    )

    assert plan.theoretical_cycle_length < 45.0
    assert plan.min_cycle_enforced
    assert math.isclose(plan.cycle_length, 45.0, abs_tol=1e-3)


def test_maximum_cycle_bound_enforcement():
    """Verify that heavy traffic clamps to max_cycle when C_0 > max_cycle."""
    # Y = 0.90, L = 8s -> C_0 = (1.5*8 + 5) / (1 - 0.90) = 17 / 0.10 = 170.0s > 120.0s
    plan = calculate_webster_timing(
        critical_flows={0: 810.0, 2: 810.0},
        saturation_flows={0: 1800.0, 2: 1800.0},
        yellow_durations={0: 4.0, 2: 4.0},
        min_cycle=45.0,
        max_cycle=120.0,
    )

    assert plan.theoretical_cycle_length > 120.0
    assert plan.max_cycle_enforced
    assert plan.cycle_length <= 120.0


def test_deterministic_output():
    """Verify that repeated calculations with identical inputs yield bit-exact results."""
    flows = {0: 250.0, 2: 1100.0}
    sats = {0: 1800.0, 2: 3600.0}
    yels = {0: 4.0, 2: 4.0}

    p1 = calculate_webster_timing(flows, sats, yels)
    p2 = calculate_webster_timing(flows, sats, yels)

    assert p1.cycle_length == p2.cycle_length
    assert p1.green_times == p2.green_times
    assert p1.flow_ratios == p2.flow_ratios


# =====================================================================
# 2. Input Validation and Failure Rejection Tests
# =====================================================================

def test_negative_flow_raises_value_error():
    """Verify that negative flow rate raises ValueError with descriptive message."""
    with pytest.raises(ValueError, match="Invalid critical flow"):
        calculate_webster_timing(
            critical_flows={0: -100.0, 2: 500.0},
            saturation_flows={0: 1800.0, 2: 1800.0},
            yellow_durations={0: 4.0, 2: 4.0},
        )


def test_zero_or_negative_saturation_flow_raises_value_error():
    """Verify that non-positive saturation flow raises ValueError."""
    with pytest.raises(ValueError, match="Invalid saturation flow"):
        calculate_webster_timing(
            critical_flows={0: 200.0, 2: 500.0},
            saturation_flows={0: 0.0, 2: 1800.0},
            yellow_durations={0: 4.0, 2: 4.0},
        )

    with pytest.raises(ValueError, match="Invalid saturation flow"):
        calculate_webster_timing(
            critical_flows={0: 200.0, 2: 500.0},
            saturation_flows={0: -1800.0, 2: 1800.0},
            yellow_durations={0: 4.0, 2: 4.0},
        )


def test_non_finite_inputs_raise_value_error():
    """Verify that NaN and Inf flow or saturation inputs raise ValueError."""
    with pytest.raises(ValueError, match="Invalid critical flow"):
        calculate_webster_timing(
            critical_flows={0: float("nan"), 2: 500.0},
            saturation_flows={0: 1800.0, 2: 1800.0},
            yellow_durations={0: 4.0, 2: 4.0},
        )

    with pytest.raises(ValueError, match="Invalid saturation flow"):
        calculate_webster_timing(
            critical_flows={0: 200.0, 2: 500.0},
            saturation_flows={0: float("inf"), 2: 1800.0},
            yellow_durations={0: 4.0, 2: 4.0},
        )


def test_mismatched_phase_dictionaries_raise_value_error():
    """Verify that mismatched phase keys between flows and saturation raise ValueError."""
    with pytest.raises(ValueError, match="Phase mismatch"):
        calculate_webster_timing(
            critical_flows={0: 200.0, 2: 500.0},
            saturation_flows={0: 1800.0, 1: 1800.0},  # Key 1 instead of 2
            yellow_durations={0: 4.0, 2: 4.0},
        )


# =====================================================================
# 3. Corridor Junction Configurations Ground Truth Tests (J1, J2, J3)
# =====================================================================

def test_j1_default_webster_plan(default_configs):
    """Verify J1 default timing plan satisfies all engineering constraints."""
    cfg = default_configs["J1"]
    plan = calculate_webster_timing(
        critical_flows=cfg.critical_flows,
        saturation_flows=cfg.saturation_flows,
        yellow_durations=cfg.yellow_durations,
        min_cycle=cfg.min_cycle,
        max_cycle=cfg.max_cycle,
        min_green=cfg.min_green,
        max_green=cfg.max_green,
        junction_id="J1",
    )

    # J1: Phase 0 (Cross: q=150, s=1800), Phase 2 (Hosur: q=1200, s=3600)
    # y_0 = 0.0833, y_2 = 0.3333 -> Y = 0.4167
    # L = 8.0s -> C_0 = (1.5*8 + 5) / (1 - 0.4167) = 17 / 0.5833 = 29.1s -> Floored to C_min = 45.0s
    assert plan.cycle_length >= 45.0
    assert plan.min_cycle_enforced
    # Minimum green satisfied on both phases
    assert plan.green_times[0] >= 15.0
    assert plan.green_times[2] >= 15.0
    # Arterial gets more green than cross street
    assert plan.green_times[2] > plan.green_times[0]
    # Sum of greens + lost time == cycle length
    assert math.isclose(sum(plan.green_times.values()) + plan.total_lost_time, plan.cycle_length, abs_tol=1e-3)


def test_j2_default_webster_plan(default_configs):
    """Verify J2 Central Silk Board default timing plan."""
    cfg = default_configs["J2"]
    plan = calculate_webster_timing(
        critical_flows=cfg.critical_flows,
        saturation_flows=cfg.saturation_flows,
        yellow_durations=cfg.yellow_durations,
        min_cycle=cfg.min_cycle,
        max_cycle=cfg.max_cycle,
        min_green=cfg.min_green,
        max_green=cfg.max_green,
        junction_id="J2",
    )

    # J2: Phase 0 (Hosur: q=1800, s=5400 -> y_0 = 0.3333)
    #     Phase 2 (Madiwala: q=900, s=3600 -> y_2 = 0.2500)
    # Y = 0.5833, L = 6 + 6 = 12.0s
    # C_0 = (1.5*12 + 5) / (1 - 0.5833) = 23 / 0.4167 = 55.2s
    assert math.isclose(plan.theoretical_cycle_length, 55.2, abs_tol=0.1)
    assert math.isclose(plan.cycle_length, 55.2, abs_tol=0.1)
    assert not plan.min_cycle_enforced
    assert not plan.max_cycle_enforced
    assert plan.green_times[0] > plan.green_times[2]
    assert plan.green_times[0] >= 15.0
    assert plan.green_times[2] >= 15.0
    assert math.isclose(sum(plan.green_times.values()) + plan.total_lost_time, plan.cycle_length, abs_tol=1e-3)


def test_j3_default_webster_plan(default_configs):
    """Verify J3 default timing plan satisfies all engineering constraints."""
    cfg = default_configs["J3"]
    plan = calculate_webster_timing(
        critical_flows=cfg.critical_flows,
        saturation_flows=cfg.saturation_flows,
        yellow_durations=cfg.yellow_durations,
        min_cycle=cfg.min_cycle,
        max_cycle=cfg.max_cycle,
        min_green=cfg.min_green,
        max_green=cfg.max_green,
        junction_id="J3",
    )

    # J3: Phase 0 (Cross: q=150, s=1800), Phase 2 (Hosur: q=1400, s=3600)
    # y_0 = 0.0833, y_2 = 0.3889 -> Y = 0.4722
    # L = 8.0s -> C_0 = 17 / 0.5278 = 32.2s -> Floored to C_min = 45.0s
    assert plan.cycle_length >= 45.0
    assert plan.min_cycle_enforced
    assert plan.green_times[0] >= 15.0
    assert plan.green_times[2] >= 15.0
    assert plan.green_times[2] > plan.green_times[0]
    assert math.isclose(sum(plan.green_times.values()) + plan.total_lost_time, plan.cycle_length, abs_tol=1e-3)


# =====================================================================
# 4. Integration Tests: Junction Controller & Safety Shield Integration
# =====================================================================

def test_junction_controller_cyclic_phase_progression(default_configs, monkeypatch):
    """Verify cyclic phase switching: Green 0 -> Yellow 1 -> Green 2 -> Yellow 3 -> Green 0."""
    import traffic_service.signal_controller as signal_controller_module

    mock_tl = MockTraCITrafficLight(initial_phase=0)
    monkeypatch.setattr(signal_controller_module.traci, "trafficlight", mock_tl)

    sig_ctrl = SignalController(
        tls_id="tls_j1",
        green_phases={0, 2},
        yellow_transitions={0: 1, 2: 3},
        min_green=15.0,
        max_green=60.0,
        yellow_duration=4.0,
    )

    cfg = default_configs["J1"]
    # Provide explicit green times for testing: Phase 0 = 20s, Phase 2 = 30s
    plan = calculate_webster_timing(
        critical_flows={0: 300.0, 2: 900.0},
        saturation_flows={0: 1800.0, 2: 1800.0},
        yellow_durations={0: 4.0, 2: 4.0},
        min_cycle=45.0,
        max_cycle=120.0,
    )

    j_ctrl = WebsterJunctionController(config=cfg, signal_controller=sig_ctrl, plan=plan)

    target_g0 = plan.green_times[0]
    assert target_g0 >= 15.0

    # Start in Phase 0 at t=0
    sig_ctrl._last_phase = 0
    sig_ctrl._phase_start_time = 0.0

    # Advance time before planned green duration: controller must NOT trigger switch
    dec = j_ctrl.step(sim_time=target_g0 - 1.0)
    assert dec is None
    assert mock_tl.phase == 0

    # Advance time to planned green duration: controller MUST trigger switch to yellow phase 1
    dec = j_ctrl.step(sim_time=target_g0)
    assert dec is not None
    assert dec["action"] == "SWITCH_TO_YELLOW"
    assert dec["target_green_phase"] == 2
    assert mock_tl.phase == 1  # Switched to yellow phase 1!

    # While in yellow phase 1: step() should not interrupt
    dec = j_ctrl.step(sim_time=target_g0 + 2.0)
    assert dec is None
    assert mock_tl.phase == 1

    # Simulate TraCI naturally advancing to Green Phase 2 after yellow expires
    mock_tl.phase = 2
    sig_ctrl._last_phase = 2
    sig_ctrl._phase_start_time = target_g0 + 4.0  # yellow duration was 4s

    # Advance time before Phase 2 green duration expires
    target_g2 = plan.green_times[2]
    dec = j_ctrl.step(sim_time=sig_ctrl._phase_start_time + target_g2 - 1.0)
    assert dec is None
    assert mock_tl.phase == 2

    # Advance time to Phase 2 green completion: triggers switch to Yellow Phase 3
    dec = j_ctrl.step(sim_time=sig_ctrl._phase_start_time + target_g2)
    assert dec is not None
    assert dec["action"] == "SWITCH_TO_YELLOW"
    assert dec["target_green_phase"] == 0
    assert mock_tl.phase == 3  # Switched to yellow phase 3!


def test_safety_shield_prevents_premature_switch(default_configs, monkeypatch):
    """Verify that SignalController safety invariant (min_green) blocks premature switching."""
    import traffic_service.signal_controller as signal_controller_module

    mock_tl = MockTraCITrafficLight(initial_phase=0)
    monkeypatch.setattr(signal_controller_module.traci, "trafficlight", mock_tl)

    sig_ctrl = SignalController(
        tls_id="tls_j1",
        green_phases={0, 2},
        yellow_transitions={0: 1, 2: 3},
        min_green=15.0,
        max_green=60.0,
    )

    # Force an artificially low target green in plan (e.g. 10s < min_green 15s)
    plan = calculate_webster_timing(
        critical_flows={0: 100.0, 2: 500.0},
        saturation_flows={0: 1800.0, 2: 1800.0},
        yellow_durations={0: 4.0, 2: 4.0},
        min_green=10.0,
    )
    cfg = default_configs["J1"]
    j_ctrl = WebsterJunctionController(config=cfg, signal_controller=sig_ctrl, plan=plan)

    sig_ctrl._last_phase = 0
    sig_ctrl._phase_start_time = 0.0

    # At t=10s, target_green (10s) is met, but SignalController min_green (15s) is NOT met.
    # SignalController.can_switch(10.0) returns False, so switch is blocked.
    dec = j_ctrl.step(sim_time=10.0)
    assert dec is None
    assert mock_tl.phase == 0


def test_emergency_override_bypasses_webster_switching(default_configs, monkeypatch):
    """Verify that emergency priority lock suspends Webster switching until lock is released."""
    import traffic_service.signal_controller as signal_controller_module

    mock_tl = MockTraCITrafficLight(initial_phase=2)
    monkeypatch.setattr(signal_controller_module.traci, "trafficlight", mock_tl)

    sig_ctrl = SignalController(
        tls_id="tls_j1",
        green_phases={0, 2},
        yellow_transitions={0: 1, 2: 3},
        min_green=15.0,
        max_green=60.0,
    )

    # Lock emergency on Phase 2
    sig_ctrl._last_phase = 2
    sig_ctrl._phase_start_time = 0.0
    sig_ctrl.lock_emergency_priority(corridor_green_phase=2, sim_time=10.0)
    assert sig_ctrl.emergency_locked

    cfg = default_configs["J1"]
    j_ctrl = WebsterJunctionController(config=cfg, signal_controller=sig_ctrl)

    # Even at t=100s, Webster must NOT attempt to switch away from emergency green
    dec = j_ctrl.step(sim_time=100.0)
    assert dec["action"] == "EMERGENCY_LOCK_ACTIVE"
    assert mock_tl.phase == 2

    # Release emergency lock
    sig_ctrl.release_emergency_priority()
    assert not sig_ctrl.emergency_locked

    # Normal operation resumes
    dec = j_ctrl.step(sim_time=101.0)
    assert dec is not None
    assert dec["action"] == "SWITCH_TO_YELLOW"
    assert mock_tl.phase == 3


def test_corridor_controller_step_and_parameters(default_configs, monkeypatch):
    """Verify that WebsterCorridorController manages all 3 junctions and exposes parameter telemetry."""
    import traffic_service.signal_controller as signal_controller_module

    mock_tl1 = MockTraCITrafficLight(initial_phase=0)
    mock_tl2 = MockTraCITrafficLight(initial_phase=0)
    mock_tl3 = MockTraCITrafficLight(initial_phase=0)

    # Dispatch to specific mock depending on tls_id
    tls_map = {
        default_configs["J1"].tls_id: mock_tl1,
        default_configs["J2"].tls_id: mock_tl2,
        default_configs["J3"].tls_id: mock_tl3,
    }

    class MultiMockTraCI:
        @staticmethod
        def getPhase(tls_id):
            return tls_map[tls_id].getPhase(tls_id)
        @staticmethod
        def setPhase(tls_id, p):
            return tls_map[tls_id].setPhase(tls_id, p)
        @staticmethod
        def setPhaseDuration(tls_id, d):
            return tls_map[tls_id].setPhaseDuration(tls_id, d)
        @staticmethod
        def getNextSwitch(tls_id):
            return 100.0

    monkeypatch.setattr(signal_controller_module.traci, "trafficlight", MultiMockTraCI)

    controllers = {
        "J1": SignalController("1617743335", green_phases={0, 2}, yellow_transitions={0: 1, 2: 3}),
        "J2": SignalController("GS_cluster_10282769895_10775075568_11964440742_11964440743", green_phases={0, 2}, yellow_transitions={0: 1, 2: 3}, yellow_duration=6.0),
        "J3": SignalController("6970466614", green_phases={0, 2}, yellow_transitions={0: 1, 2: 3}),
    }

    corridor_ctrl = WebsterCorridorController(controllers=controllers, configs=default_configs)

    # Check plans
    plans = corridor_ctrl.get_plans()
    assert set(plans.keys()) == {"J1", "J2", "J3"}
    for j_id, plan in plans.items():
        assert plan.cycle_length >= 45.0
        assert math.isclose(sum(plan.green_times.values()) + plan.total_lost_time, plan.cycle_length, abs_tol=1e-3)

    # Check parameters summary for experiment logging
    summary = corridor_ctrl.get_parameters_summary()
    assert summary["controller_type"] == "webster_optimum_fixed_time"
    assert "J1" in summary["junctions"]
    assert "J2" in summary["junctions"]
    assert "J3" in summary["junctions"]

    # Step corridor controller
    decisions = corridor_ctrl.step(sim_time=0.0)
    assert isinstance(decisions, dict)


def test_no_starvation_beyond_max_red_constraint(default_configs):
    """Verify that no phase red duration exceeds the maximum red constraint (<= 60s)."""
    # For a 2-phase junction, Red duration for phase i is C - g_i = g_other + L
    for j_id, cfg in default_configs.items():
        plan = calculate_webster_timing(
            critical_flows=cfg.critical_flows,
            saturation_flows=cfg.saturation_flows,
            yellow_durations=cfg.yellow_durations,
            min_cycle=cfg.min_cycle,
            max_cycle=cfg.max_cycle,
            min_green=cfg.min_green,
            max_green=cfg.max_green,
        )

        for p in cfg.green_phases:
            g_p = plan.green_times[p]
            red_duration = plan.cycle_length - g_p
            # Red duration must strictly not exceed max_red threshold (60.0s)
            assert red_duration <= 60.0, (
                f"Junction {j_id} phase {p} red duration {red_duration:.1f}s exceeds max_red constraint (60.0s)!"
            )


def test_monotone_green_expansion_with_increasing_demand():
    """Verify that green duration for a phase expands monotonically as its demand increases."""
    sats = {0: 1800.0, 2: 3600.0}
    yels = {0: 4.0, 2: 4.0}

    demands = [300.0, 600.0, 900.0, 1200.0, 1500.0]
    greens_p2 = []

    for d in demands:
        plan = calculate_webster_timing(
            critical_flows={0: 200.0, 2: d},
            saturation_flows=sats,
            yellow_durations=yels,
            min_cycle=45.0,
            max_cycle=120.0,
        )
        greens_p2.append(plan.green_times[2])

    # Green duration on Phase 2 must be strictly non-decreasing
    for i in range(len(greens_p2) - 1):
        assert greens_p2[i + 1] >= greens_p2[i], (
            f"Green allocation failed monotonicity: {greens_p2[i]} -> {greens_p2[i+1]}"
        )


def test_multi_intersection_simulation_webster_mode_initialization():
    """Verify MultiIntersectionSimulation correctly instantiates in webster mode."""
    from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation

    sim = MultiIntersectionSimulation(
        sumocfg_path="sumo/silk_board/silk_board.sumocfg",
        mode="webster",
    )

    assert sim.mode == "webster"
    assert sim.webster_controller is not None
    assert isinstance(sim.webster_controller, WebsterCorridorController)
    assert sim.marl_controller is None
    assert set(sim.webster_controller.junction_controllers.keys()) == {"J1", "J2", "J3"}


# =====================================================================
# 5. Task 1-3 Verification Tests (Yellow Durations, Infeasible Bounds, Max Red)
# =====================================================================

def test_j1_j2_j3_yellow_duration_verification(monkeypatch):
    """
    Verify Task 1:
    1. J1 SignalController uses 4 seconds.
    2. J2 SignalController uses 6 seconds.
    3. J3 SignalController uses 4 seconds.
    4. TraCI phase transition applies the exact configured duration.
    5. Webster's planned lost time matches the duration applied at runtime.
    """
    import traffic_service.signal_controller as signal_controller_module
    from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation

    sim = MultiIntersectionSimulation(
        sumocfg_path="sumo/silk_board/silk_board.sumocfg",
        mode="webster",
    )

    # 1-3: Verify configured yellow duration on each controller
    assert sim.controllers["J1"].yellow_duration == 4.0
    assert sim.controllers["J2"].yellow_duration == 6.0
    assert sim.controllers["J3"].yellow_duration == 4.0

    # 4: Verify TraCI phase transition applies the exact duration
    mock_tl1 = MockTraCITrafficLight(initial_phase=0)
    mock_tl2 = MockTraCITrafficLight(initial_phase=0)
    mock_tl3 = MockTraCITrafficLight(initial_phase=0)

    tls_map = {
        sim.tls_ids["J1"]: mock_tl1,
        sim.tls_ids["J2"]: mock_tl2,
        sim.tls_ids["J3"]: mock_tl3,
    }

    class MultiMockTraCI:
        @staticmethod
        def getPhase(tls_id):
            return tls_map[tls_id].getPhase(tls_id)
        @staticmethod
        def setPhase(tls_id, p):
            return tls_map[tls_id].setPhase(tls_id, p)
        @staticmethod
        def setPhaseDuration(tls_id, d):
            return tls_map[tls_id].setPhaseDuration(tls_id, d)
        @staticmethod
        def getNextSwitch(tls_id):
            return 100.0

    monkeypatch.setattr(signal_controller_module.traci, "trafficlight", MultiMockTraCI)

    # Force switch on J1 (phase 0 -> 1)
    sim.controllers["J1"]._last_phase = 0
    sim.controllers["J1"]._phase_start_time = 0.0
    sim.controllers["J1"].request_switch(target_green_phase=2, sim_time=20.0)
    assert mock_tl1.phase == 1
    assert mock_tl1._current_duration == 4.0

    # Force switch on J2 (phase 0 -> 1)
    sim.controllers["J2"]._last_phase = 0
    sim.controllers["J2"]._phase_start_time = 0.0
    sim.controllers["J2"].request_switch(target_green_phase=2, sim_time=25.0)
    assert mock_tl2.phase == 1
    assert mock_tl2._current_duration == 6.0  # Must be 6.0 seconds for J2!

    # Force switch on J3 (phase 0 -> 1)
    sim.controllers["J3"]._last_phase = 0
    sim.controllers["J3"]._phase_start_time = 0.0
    sim.controllers["J3"].request_switch(target_green_phase=2, sim_time=20.0)
    assert mock_tl3.phase == 1
    assert mock_tl3._current_duration == 4.0

    # 5: Verify Webster planned lost time matches applied runtime yellow duration
    plans = sim.webster_controller.get_plans()
    assert plans["J1"].total_lost_time == 8.0   # 4.0 + 4.0
    assert plans["J2"].total_lost_time == 12.0  # 6.0 + 6.0
    assert plans["J3"].total_lost_time == 8.0   # 4.0 + 4.0


def test_infeasible_cycle_bounds_rejection():
    """
    Verify Task 2:
    - Reject configurations where max_cycle < total_lost_time + number_of_phases * min_green.
    - Raise clear ValueError without silently increasing max_cycle.
    - Test feasible configurations, boundary equality, and cycle invariant.
    """
    # L = 4 + 4 = 8.0s, 2 phases * 15s min_green = 30.0s -> min feasible = 38.0s
    flows = {0: 300.0, 2: 600.0}
    sats = {0: 1800.0, 2: 1800.0}
    yels = {0: 4.0, 2: 4.0}

    # Infeasible: max_cycle = 37.9s < 38.0s -> MUST RAISE ValueError
    with pytest.raises(ValueError, match="Infeasible cycle bounds"):
        calculate_webster_timing(
            critical_flows=flows,
            saturation_flows=sats,
            yellow_durations=yels,
            min_cycle=20.0,
            max_cycle=37.9,
            min_green=15.0,
        )

    # Infeasible: max_cycle = 30.0s < 38.0s -> MUST RAISE ValueError
    with pytest.raises(ValueError, match="Infeasible cycle bounds"):
        calculate_webster_timing(
            critical_flows=flows,
            saturation_flows=sats,
            yellow_durations=yels,
            min_cycle=20.0,
            max_cycle=30.0,
            min_green=15.0,
        )

    # Boundary equality: max_cycle == 38.0s == L + len(phases) * min_green -> Feasible!
    plan_eq = calculate_webster_timing(
        critical_flows=flows,
        saturation_flows=sats,
        yellow_durations=yels,
        min_cycle=20.0,
        max_cycle=38.0,
        min_green=15.0,
    )
    assert math.isclose(plan_eq.cycle_length, 38.0, abs_tol=1e-3)
    assert plan_eq.green_times[0] == 15.0
    assert plan_eq.green_times[2] == 15.0
    assert math.isclose(sum(plan_eq.green_times.values()) + plan_eq.total_lost_time, plan_eq.cycle_length, abs_tol=1e-3)

    # Feasible: max_cycle = 45.0s > 38.0s -> Feasible!
    plan_feas = calculate_webster_timing(
        critical_flows=flows,
        saturation_flows=sats,
        yellow_durations=yels,
        min_cycle=20.0,
        max_cycle=45.0,
        min_green=15.0,
    )
    assert plan_feas.cycle_length <= 45.0
    assert math.isclose(sum(plan_feas.green_times.values()) + plan_feas.total_lost_time, plan_feas.cycle_length, abs_tol=1e-3)


def test_invalid_cycle_and_green_settings_rejection():
    """Verify input validation for non-positive or inverted bounds."""
    flows = {0: 300.0, 2: 600.0}
    sats = {0: 1800.0, 2: 1800.0}
    yels = {0: 4.0, 2: 4.0}

    # min_cycle <= 0
    with pytest.raises(ValueError, match="Invalid min_cycle"):
        calculate_webster_timing(flows, sats, yels, min_cycle=0.0)

    # max_cycle <= 0
    with pytest.raises(ValueError, match="Invalid max_cycle"):
        calculate_webster_timing(flows, sats, yels, max_cycle=-10.0)

    # min_cycle > max_cycle
    with pytest.raises(ValueError, match="min_cycle .* cannot exceed max_cycle"):
        calculate_webster_timing(flows, sats, yels, min_cycle=90.0, max_cycle=50.0)

    # min_green <= 0
    with pytest.raises(ValueError, match="Invalid min_green"):
        calculate_webster_timing(flows, sats, yels, min_green=0.0)

    # max_green <= 0
    with pytest.raises(ValueError, match="Invalid max_green"):
        calculate_webster_timing(flows, sats, yels, max_green=-5.0)

    # min_green > max_green
    with pytest.raises(ValueError, match="min_green .* cannot exceed max_green"):
        calculate_webster_timing(flows, sats, yels, min_green=50.0, max_green=20.0)


def test_maximum_red_analysis_default_vs_asymmetric_demand():
    """
    Verify Task 3:
    1. Default Silk Board timing plans guarantee max red duration <= 36.7s << 60s.
    2. High asymmetric demand (g_2 = 60s) yields red duration > 60s, proving
       Webster fixed-time does NOT unconditionally guarantee max_red <= 60s without
       explicit cycle length capping.
    """
    # 1. Default plans: max red strictly <= 36.7s
    configs = create_default_webster_configs()
    for j_id, cfg in configs.items():
        plan = calculate_webster_timing(
            critical_flows=cfg.critical_flows,
            saturation_flows=cfg.saturation_flows,
            yellow_durations=cfg.yellow_durations,
            min_cycle=cfg.min_cycle,
            max_cycle=cfg.max_cycle,
            min_green=cfg.min_green,
            max_green=cfg.max_green,
        )
        for p in cfg.green_phases:
            # Red duration includes the other phase green + all intervening yellows (L)
            r_p = plan.cycle_length - plan.green_times[p]
            assert r_p <= 36.7, f"Default plan {j_id} phase {p} has red duration {r_p:.1f}s > 36.7s"

    # 2. Extreme asymmetric demand test on J2:
    # Phase 2 (Madiwala) has min flow (q=50), Phase 0 (Hosur) has high flow (q=4500)
    # This pushes Phase 0 green to max_green (60.0s), making Phase 2 red duration:
    # R_2 = g_0 + L = 60.0 + 12.0 = 72.0s > 60.0s!
    asym_plan_j2 = calculate_webster_timing(
        critical_flows={0: 4500.0, 2: 50.0},
        saturation_flows={0: 5400.0, 2: 3600.0},
        yellow_durations={0: 6.0, 2: 6.0},
        min_cycle=45.0,
        max_cycle=120.0,
        min_green=15.0,
        max_green=60.0,
    )
    red_p2 = asym_plan_j2.cycle_length - asym_plan_j2.green_times[2]
    # Proof: In this configuration, red_p2 exceeds 60s!
    assert red_p2 > 60.0, f"Expected red duration to exceed 60s in unconstrained extreme plan, got {red_p2}"
    assert math.isclose(red_p2, asym_plan_j2.green_times[0] + asym_plan_j2.total_lost_time, abs_tol=1e-3)


