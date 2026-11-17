"""
Tests for Series 4C: Cooperative Reward Coupling Mechanism Ablation.
Verifies mathematical invariants, extreme beta boundaries, weighting behavior,
and equity metric extraction before running confirmatory training.
"""

import pytest
import numpy as np
from traffic_service.ai.env import (
    RewardWeights,
    MultiIntersectionReward,
    RewardBreakdown,
    ACTION_KEEP,
    ACTION_SWITCH,
)
from traffic_service.resilience.detailed_collector import (
    DetailedCorridorMetricsCollector,
    calculate_gini_coefficient,
)


# =====================================================================
# 1. Beta Boundary Invariant Tests (beta = 0.0, 0.50, 1.0)
# =====================================================================

def test_reward_coupling_beta_zero_pure_local():
    """Verifies that beta = 0.0 produces strictly pure local rewards for all junctions."""
    weights = RewardWeights(alpha=0.0)
    reward_fn = MultiIntersectionReward(weights=weights)

    mock_states = {
        "J1": {"total_queue": 15, "total_waiting_time": 100.0, "average_speed_kmh": 20.0, "co2_mg_s": 2000.0, "phase": 2},
        "J2": {"total_queue": 25, "total_waiting_time": 250.0, "average_speed_kmh": 10.0, "co2_mg_s": 4000.0, "phase": 0},
        "J3": {"total_queue": 5, "total_waiting_time": 30.0, "average_speed_kmh": 35.0, "co2_mg_s": 800.0, "phase": 2},
    }
    actions = {"J1": ACTION_KEEP, "J2": ACTION_KEEP, "J3": ACTION_KEEP}

    mixed_r, breakdowns = reward_fn.compute_mixed_rewards(
        states=mock_states,
        actions=actions,
        completed_trips=10,
    )

    for j_id in ["J1", "J2", "J3"]:
        bd = breakdowns[j_id]
        # At alpha=0.0, mixed reward must strictly equal local reward
        assert np.isclose(mixed_r[j_id], bd.local_reward, atol=1e-5), (
            f"Junction {j_id} mixed reward {mixed_r[j_id]} != local reward {bd.local_reward} at beta=0.0"
        )
        assert np.isclose(bd.mixed_reward, bd.local_reward, atol=1e-5)


def test_reward_coupling_beta_one_pure_global():
    """Verifies that beta = 1.0 produces identical global corridor reward for all junctions."""
    weights = RewardWeights(alpha=1.0)
    reward_fn = MultiIntersectionReward(weights=weights)

    mock_states = {
        "J1": {"total_queue": 10, "total_waiting_time": 50.0, "average_speed_kmh": 25.0, "co2_mg_s": 1500.0, "phase": 2},
        "J2": {"total_queue": 30, "total_waiting_time": 300.0, "average_speed_kmh": 8.0, "co2_mg_s": 5000.0, "phase": 0},
        "J3": {"total_queue": 8, "total_waiting_time": 40.0, "average_speed_kmh": 30.0, "co2_mg_s": 1000.0, "phase": 2},
    }
    actions = {"J1": ACTION_KEEP, "J2": ACTION_KEEP, "J3": ACTION_KEEP}

    mixed_r, breakdowns = reward_fn.compute_mixed_rewards(
        states=mock_states,
        actions=actions,
        completed_trips=5,
    )

    global_ref = breakdowns["J1"].corridor_reward
    for j_id in ["J1", "J2", "J3"]:
        bd = breakdowns[j_id]
        # At alpha=1.0, mixed reward must strictly equal corridor reward
        assert np.isclose(mixed_r[j_id], global_ref, atol=1e-5), (
            f"Junction {j_id} mixed reward {mixed_r[j_id]} != global {global_ref} at beta=1.0"
        )
        assert np.isclose(bd.mixed_reward, bd.corridor_reward, atol=1e-5)


def test_reward_coupling_convex_combination_linearity():
    """Verifies that mixed reward is an exact linear convex combination across all beta levels."""
    betas = [0.0, 0.25, 0.50, 0.75, 1.0]
    mock_states = {
        "J1": {"total_queue": 12, "total_waiting_time": 80.0, "average_speed_kmh": 22.0, "co2_mg_s": 1800.0, "phase": 2},
        "J2": {"total_queue": 20, "total_waiting_time": 180.0, "average_speed_kmh": 14.0, "co2_mg_s": 3200.0, "phase": 0},
        "J3": {"total_queue": 6, "total_waiting_time": 45.0, "average_speed_kmh": 28.0, "co2_mg_s": 1100.0, "phase": 2},
    }
    actions = {"J1": ACTION_KEEP, "J2": ACTION_KEEP, "J3": ACTION_KEEP}

    for b in betas:
        weights = RewardWeights(alpha=b)
        reward_fn = MultiIntersectionReward(weights=weights)
        mixed_r, breakdowns = reward_fn.compute_mixed_rewards(
            states=mock_states,
            actions=actions,
            completed_trips=3,
        )
        for j_id in ["J1", "J2", "J3"]:
            bd = breakdowns[j_id]
            expected = float(np.clip((1.0 - b) * bd.local_reward + b * bd.corridor_reward, -15.0, 15.0))
            assert np.isclose(mixed_r[j_id], expected, atol=1e-5), (
                f"Beta {b} for {j_id}: got {mixed_r[j_id]}, expected {expected}"
            )


# =====================================================================
# 2. Numerical Stability and Bounds
# =====================================================================

def test_reward_numerical_bounds_under_extreme_traffic():
    """Verifies that rewards remain bounded in [-15.0, 15.0] under extreme congestion."""
    weights = RewardWeights(alpha=0.50)
    reward_fn = MultiIntersectionReward(weights=weights)

    # Massive congestion
    extreme_states = {
        "J1": {"total_queue": 500, "total_waiting_time": 50000.0, "average_speed_kmh": 0.0, "co2_mg_s": 100000.0, "phase": 1},
        "J2": {"total_queue": 600, "total_waiting_time": 60000.0, "average_speed_kmh": 0.0, "co2_mg_s": 120000.0, "phase": 1},
        "J3": {"total_queue": 400, "total_waiting_time": 40000.0, "average_speed_kmh": 0.0, "co2_mg_s": 80000.0, "phase": 1},
    }
    actions = {"J1": ACTION_SWITCH, "J2": ACTION_SWITCH, "J3": ACTION_SWITCH}

    mixed_r, breakdowns = reward_fn.compute_mixed_rewards(
        states=extreme_states,
        actions=actions,
        completed_trips=0,
    )

    for j_id, r in mixed_r.items():
        assert not np.isnan(r)
        assert not np.isinf(r)
        assert -15.0 <= r <= 15.0
        assert -10.0 <= breakdowns[j_id].local_reward <= 10.0
        assert -10.0 <= breakdowns[j_id].corridor_reward <= 10.0


# =====================================================================
# 3. Equity Metric and Gini Coefficient Calculation Tests
# =====================================================================

def test_gini_coefficient_exact_properties():
    """Verifies mathematical properties of Gini coefficient calculation."""
    # Completely equal delays -> Gini = 0.0
    equal_delays = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
    assert np.isclose(calculate_gini_coefficient(equal_delays), 0.0, atol=1e-4)

    # Extreme inequality -> Gini close to (N-1)/N = 5/6 = 0.8333
    extreme_delays = [0.0, 0.0, 0.0, 0.0, 0.0, 600.0]
    gini_extreme = calculate_gini_coefficient(extreme_delays)
    assert 0.80 <= gini_extreme <= 0.85

    # All zeros edge case
    zero_delays = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    assert calculate_gini_coefficient(zero_delays) == 0.0
