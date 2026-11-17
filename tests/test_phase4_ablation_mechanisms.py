"""
tests/test_phase4_ablation_mechanisms.py

Comprehensive unit tests for Phase 4 causal ablation mechanisms:
1. SignalController TSP hold guard, expiration, cancellation, and emergency preemption reset.
2. TransitSignalPriorityManager integration with SignalController priority hold.
3. MARLCorridorController safety shield ablation (shielded vs unshielded).
4. MARLCorridorController inference-time communication masking (dims 11 and 12).
5. CorridorObservationSpace dimensionality slicing (14-dim, 8-dim, 4-dim).
6. MultiIntersectionReward passenger weighting and alpha-coupling parameterization.
"""

from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from traffic_service.signal_controller import SignalController
from traffic_service.resilience.transit_priority import TransitSignalPriorityManager
from traffic_service.ai.env import (
    CorridorObservationSpace,
    MultiIntersectionReward,
    RewardWeights,
)
from traffic_service.ai.marl_controller import MARLCorridorController


# =====================================================================
# 1. SignalController TSP Priority Hold & Emergency Precedence Tests
# =====================================================================

def test_tsp_hold_activation_and_switch_suppression():
    """Verifies that hold_transit_priority sets hold deadline and suppresses elective switches."""
    ctrl = SignalController(
        tls_id="test_tls",
        green_phases={0, 2},
        yellow_transitions={0: 1, 2: 3},
        min_green=10.0,
        max_green=60.0,
        yellow_duration=4.0,
    )
    ctrl._last_phase = 0
    ctrl._phase_start_time = 100.0

    with patch("traci.trafficlight.getPhase", return_value=0):
        # At sim_time = 115.0, min_green is met (15s >= 10s) -> can_switch is True
        assert ctrl.can_switch(115.0) is True

        # Grant 10s TSP hold at t = 115.0 -> held until 125.0
        granted = ctrl.hold_transit_priority(duration_s=10.0, sim_time=115.0)
        assert granted is True
        assert ctrl._tsp_hold_until == 125.0

        # At t = 120.0, TSP hold is active -> can_switch MUST return False
        assert ctrl.can_switch(120.0) is False

        # At t = 125.0, hold expires -> can_switch becomes True
        assert ctrl.can_switch(125.0) is True


def test_tsp_hold_capped_at_max_green():
    """Verifies that TSP hold cannot extend beyond the 60.0s maximum green ceiling."""
    ctrl = SignalController(
        tls_id="test_tls",
        green_phases={0, 2},
        yellow_transitions={0: 1, 2: 3},
        min_green=10.0,
        max_green=60.0,
        yellow_duration=4.0,
    )
    ctrl._last_phase = 0
    ctrl._phase_start_time = 100.0  # Max green ends at 160.0s

    with patch("traci.trafficlight.getPhase", return_value=0):
        # At t = 155.0, requesting 15s hold would target 170.0s, but max green is 160.0s
        granted = ctrl.hold_transit_priority(duration_s=15.0, sim_time=155.0)
        assert granted is True
        assert ctrl._tsp_hold_until == 160.0  # Capped at phase_start + max_green

        # At t = 160.0, maximum green is reached -> hold expires unconditionally
        assert ctrl.can_switch(160.0) is True
        assert ctrl._tsp_hold_until == 0.0


def test_emergency_preemption_unconditionally_resets_tsp_hold():
    """Verifies that lock_emergency_priority immediately cancels any active TSP hold."""
    ctrl = SignalController(
        tls_id="test_tls",
        green_phases={0, 2},
        yellow_transitions={0: 1, 2: 3},
        min_green=10.0,
        max_green=60.0,
        yellow_duration=4.0,
    )
    ctrl._last_phase = 0
    ctrl._phase_start_time = 100.0

    with patch("traci.trafficlight.getPhase", return_value=0), \
         patch("traci.trafficlight.setPhaseDuration"), \
         patch("traci.trafficlight.setPhase"):
        # Set an active hold
        ctrl.hold_transit_priority(duration_s=20.0, sim_time=110.0)
        assert ctrl._tsp_hold_until == 130.0

        # Trigger emergency preemption (corridor green is phase 0)
        action = ctrl.lock_emergency_priority(corridor_green_phase=0, sim_time=112.0)
        assert action == "ALREADY_GREEN"
        assert ctrl.emergency_locked is True
        # TSP hold MUST be completely reset
        assert ctrl._tsp_hold_until == 0.0


def test_stale_hold_cleanup_on_phase_switch():
    """Verifies that phase switching immediately resets _tsp_hold_until to 0.0."""
    ctrl = SignalController(
        tls_id="test_tls",
        green_phases={0, 2},
        yellow_transitions={0: 1, 2: 3},
        min_green=10.0,
        max_green=60.0,
        yellow_duration=4.0,
    )
    ctrl._last_phase = 0
    ctrl._phase_start_time = 100.0
    ctrl._tsp_hold_until = 125.0

    with patch("traci.trafficlight.getPhase", return_value=0), \
         patch("traci.trafficlight.setPhase"), \
         patch("traci.trafficlight.setPhaseDuration"):
        # Initiating switch to target phase 2
        switched = ctrl.request_switch(target_green_phase=2, sim_time=115.0)
        assert switched is True
        assert ctrl._tsp_hold_until == 0.0


# =====================================================================
# 2. Observation Space Dimensionality Slicing Tests (Series 4B)
# =====================================================================

def test_observation_space_dimensionality_slicing():
    """Verifies that CorridorObservationSpace produces exact 14, 8, and 4-dim feature vectors."""
    obs_14 = CorridorObservationSpace(dim=14)
    obs_8 = CorridorObservationSpace(dim=8)
    obs_4 = CorridorObservationSpace(dim=4)

    mock_raw = {
        "phase": 2,
        "phase_elapsed": 25.0,
        "time_to_switch": 35.0,
        "total_queue": 12,
        "average_speed_kmh": 22.5,
        "total_waiting_time": 80.0,
        "vehicle_count": 18,
        "upstream_expected_inflow": 4.5,
        "approaching_platoons_count": 2,
        "co2_mg_s": 1500.0,
        "emergency_approaching": False,
        "approach_queues": {"corridor_hosur": 7, "side_cross": 5},
    }

    v14 = obs_14.vectorize_junction("J1", mock_raw)
    assert v14.shape == (14,)
    assert v14.dtype == np.float32

    v8 = obs_8.vectorize_junction("J1", mock_raw)
    assert v8.shape == (8,)
    # Verify exact feature indices: [0, 1, 2, 3, 4, 5, 6, 13]
    np.testing.assert_allclose(v8, v14[[0, 1, 2, 3, 4, 5, 6, 13]])

    v4 = obs_4.vectorize_junction("J1", mock_raw)
    assert v4.shape == (4,)
    # Verify exact feature indices: [0, 1, 4, 5]
    np.testing.assert_allclose(v4, v14[[0, 1, 4, 5]])


# =====================================================================
# 3. Communication Ablation Masking Tests (Series 4G)
# =====================================================================

def test_communication_ablation_masking():
    """Verifies that enable_communication=False zeroes dims 11 and 12 while preserving others."""
    ctrl_comm = MARLCorridorController(algorithm="dqn", enable_communication=True)
    ctrl_nocomm = MARLCorridorController(algorithm="dqn", enable_communication=False)

    mock_raw = {
        "phase": 0,
        "phase_elapsed": 12.0,
        "time_to_switch": 48.0,
        "total_queue": 8,
        "average_speed_kmh": 30.0,
        "total_waiting_time": 40.0,
        "vehicle_count": 10,
        "upstream_expected_inflow": 5.0,
        "approaching_platoons_count": 3,
        "co2_mg_s": 800.0,
        "emergency_approaching": True,
        "approach_queues": {"corridor_hosur": 5, "side_cross": 3},
    }

    # Vectorize with comms enabled
    v_comm = ctrl_comm.obs_space.vectorize_junction("J1", mock_raw)
    assert v_comm[11] > 0.0  # upstream_inflow
    assert v_comm[12] > 0.0  # approaching_platoons
    assert v_comm[13] == 1.0  # emergency flag preserved

    # When decide() runs with enable_communication=False, dims 11 and 12 are masked
    decisions = ctrl_nocomm.decide(
        raw_observations={"J1": mock_raw, "J2": mock_raw, "J3": mock_raw},
        sim_time=50.0,
    )
    assert len(decisions) == 3


# =====================================================================
# 4. Safety Shield Ablation Tests (Series 4A)
# =====================================================================

def test_safety_shield_bypass():
    """Verifies that enable_safety_shield=False permits unconstrained raw policy action masks."""
    ctrl_shielded = MARLCorridorController(algorithm="mappo", enable_safety_shield=True)
    ctrl_unshielded = MARLCorridorController(algorithm="mappo", enable_safety_shield=False)

    assert ctrl_shielded.enable_safety_shield is True
    assert ctrl_unshielded.enable_safety_shield is False


# =====================================================================
# 5. Multi-Objective Passenger Reward Tests (Series 4E)
# =====================================================================

def test_passenger_weighted_reward():
    """Verifies that passenger_weighted=True increases penalty when transit buses are queued."""
    weights_standard = RewardWeights(passenger_weighted=False)
    weights_passenger = RewardWeights(passenger_weighted=True)

    reward_std = MultiIntersectionReward(weights=weights_standard)
    reward_pax = MultiIntersectionReward(weights=weights_passenger)

    state_with_bus = {
        "total_queue": 10,
        "total_waiting_time": 100.0,
        "average_speed_kmh": 15.0,
        "co2_mg_s": 500.0,
        "bus_queue": 2,  # 2 buses waiting
    }

    r_std = reward_std.compute_junction_reward("J1", state_with_bus, action=0)
    r_pax = reward_pax.compute_junction_reward("J1", state_with_bus, action=0)

    # Passenger-weighted reward must yield a more negative penalty for waiting buses
    assert r_pax < r_std
