"""
tests/test_ai_controller.py

Comprehensive unit tests for the AI / MARL Decision Layer:
- Observation vectorization and normalization
- Multi-objective reward function
- Double-DQN Agent (action masking, replay buffer, training step)
- PPO Agent (policy distribution, GAE, clipped objective)
- MARL Corridor Controller (communication propagation, fallback safety, emergency lock)
"""

import numpy as np
import pytest

from traffic_service.ai.env import (
    ACTION_EXTEND,
    ACTION_KEEP,
    ACTION_SWITCH,
    CorridorObservationSpace,
    MultiIntersectionReward,
    RewardWeights,
)
from traffic_service.ai.models import ActorCriticNetwork, DuelingDQNNetwork
from traffic_service.ai.dqn_agent import DQNAgent, ReplayBuffer
from traffic_service.ai.ppo_agent import PPOAgent
from traffic_service.ai.marl_controller import MARLCorridorController
from traffic_service.communication import CorridorCommunicationHub
from traffic_service.signal_controller import SignalController


@pytest.fixture
def sample_raw_observation():
    return {
        "phase": 0,
        "phase_elapsed": 20.0,
        "time_to_switch": 15.0,
        "approach_queues": {"corridor_hosur": 12, "madiwala": 4},
        "total_queue": 16,
        "average_speed_kmh": 28.5,
        "total_waiting_time": 64.0,
        "vehicle_count": 18,
        "upstream_expected_inflow": 2.2,
        "approaching_platoons_count": 1,
        "co2_mg_s": 2400.0,
        "emergency_approaching": False,
    }


# =====================================================================
# 1. Observation Space & Vectorization Tests
# =====================================================================

def test_observation_space_vectorization(sample_raw_observation):
    obs_space = CorridorObservationSpace()
    vec = obs_space.vectorize_junction("J2", sample_raw_observation)

    assert isinstance(vec, np.ndarray)
    assert vec.shape == (14,)
    assert vec.dtype == np.float32

    # Check bounds [0.0, 1.0]
    assert np.all(vec >= 0.0)
    assert np.all(vec <= 1.0)

    # Check specific mapped features
    assert vec[0] == 0.0 / 3.0  # Phase 0
    assert pytest.approx(vec[1], 0.01) == 20.0 / 60.0  # Elapsed
    assert vec[3] == 1.0  # can_switch flag (elapsed 20 >= min_green 15)
    assert pytest.approx(vec[4], 0.01) == 12.0 / 50.0  # Hosur queue


def test_observation_space_corrupted_data_safety():
    obs_space = CorridorObservationSpace()

    # Empty dict
    empty_vec = obs_space.vectorize_junction("J1", {})
    assert empty_vec.shape == (14,)
    assert np.all(empty_vec == 0.0)

    # Corrupted / NaN entries
    corrupted = {"phase": np.nan, "total_queue": "invalid", "co2_mg_s": np.inf}
    safe_vec = obs_space.vectorize_junction("J1", corrupted)
    assert not np.isnan(safe_vec).any()
    assert not np.isinf(safe_vec).any()


def test_corridor_observation_concatenation(sample_raw_observation):
    obs_space = CorridorObservationSpace(junctions=["J1", "J2", "J3"])
    corridor_dict = {
        "J1": sample_raw_observation,
        "J2": sample_raw_observation,
        "J3": sample_raw_observation,
    }
    concat_vec = obs_space.vectorize_corridor(corridor_dict)
    assert concat_vec.shape == (42,)
    assert concat_vec.dtype == np.float32


# =====================================================================
# 2. Reward Function Tests
# =====================================================================

def test_multi_objective_reward_computation(sample_raw_observation):
    reward_fn = MultiIntersectionReward()
    r = reward_fn.compute_junction_reward(
        j_id="J2",
        state=sample_raw_observation,
        action=ACTION_KEEP,
        emergency_stopped=False,
    )
    assert isinstance(r, float)
    assert -10.0 <= r <= 10.0

    # Test emergency penalty
    r_emergency = reward_fn.compute_junction_reward(
        j_id="J2",
        state=sample_raw_observation,
        action=ACTION_KEEP,
        emergency_stopped=True,
    )
    assert r_emergency < r


def test_corridor_reward_throughput_bonus(sample_raw_observation):
    reward_fn = MultiIntersectionReward()
    states = {"J1": sample_raw_observation, "J2": sample_raw_observation, "J3": sample_raw_observation}
    actions = {"J1": ACTION_KEEP, "J2": ACTION_EXTEND, "J3": ACTION_KEEP}

    r1 = reward_fn.compute_corridor_reward(states, actions, completed_trips=0)
    # Trip completion bonus
    r2 = reward_fn.compute_corridor_reward(states, actions, completed_trips=5)
    assert r2 > r1


# =====================================================================
# 3. Double-DQN Agent Tests
# =====================================================================

def test_dqn_agent_action_selection_and_masking(sample_raw_observation):
    obs_space = CorridorObservationSpace()
    vec = obs_space.vectorize_junction("J2", sample_raw_observation)

    agent = DQNAgent(agent_id="J2", in_features=14, num_actions=3, seed=42)

    # When can_switch is False, ACTION_SWITCH must NEVER be chosen
    for _ in range(20):
        action, info = agent.select_action(vec, eval_mode=True, can_switch=False)
        assert action in {ACTION_KEEP, ACTION_EXTEND}
        assert action != ACTION_SWITCH

    # When can_switch is True, any valid action may be chosen
    action, info = agent.select_action(vec, eval_mode=True, can_switch=True)
    assert action in {ACTION_KEEP, ACTION_SWITCH, ACTION_EXTEND}
    assert "q_values" in info


def test_dqn_replay_buffer_and_training(sample_raw_observation):
    obs_space = CorridorObservationSpace()
    vec = obs_space.vectorize_junction("J2", sample_raw_observation)
    next_vec = vec * 0.9

    agent = DQNAgent(agent_id="J2", in_features=14, num_actions=3, seed=42)

    # Populate replay buffer
    for i in range(40):
        agent.store_transition(vec, ACTION_EXTEND, 1.5, next_vec, False)

    assert len(agent.replay_buffer) == 40

    loss = agent.train_step(batch_size=16)
    assert loss is not None
    assert loss >= 0.0


# =====================================================================
# 4. PPO Agent Tests
# =====================================================================

def test_ppo_agent_action_selection_and_masking(sample_raw_observation):
    obs_space = CorridorObservationSpace()
    vec = obs_space.vectorize_junction("J2", sample_raw_observation)

    agent = PPOAgent(agent_id="J2", in_features=14, num_actions=3, seed=42)

    # Action masking: ACTION_SWITCH probability must be zero
    action, info = agent.select_action(vec, eval_mode=False, can_switch=False)
    assert action in {ACTION_KEEP, ACTION_EXTEND}
    assert info["masked_probs"][ACTION_SWITCH] == 0.0
    assert pytest.approx(sum(info["masked_probs"]), 0.001) == 1.0


def test_ppo_trajectory_rollout_and_training(sample_raw_observation):
    obs_space = CorridorObservationSpace()
    vec = obs_space.vectorize_junction("J2", sample_raw_observation)

    agent = PPOAgent(agent_id="J2", in_features=14, num_actions=3, seed=42)

    for i in range(10):
        act, info = agent.select_action(vec, eval_mode=False)
        agent.store_transition(vec, act, reward=1.0, log_prob=info["log_prob"], value=info["value"], done=False)

    assert len(agent.buffer) == 10
    metrics = agent.train_step(last_value=0.5, epochs=2)
    assert "loss" in metrics
    assert "policy_loss" in metrics
    assert "value_loss" in metrics
    assert len(agent.buffer) == 0  # Buffer cleared after update


# =====================================================================
# 5. MARL Corridor Controller Tests
# =====================================================================

def test_marl_corridor_controller_decisions(sample_raw_observation):
    hub = CorridorCommunicationHub(corridor_sequence=["J1", "J2", "J3"])
    controller = MARLCorridorController(
        algorithm="dqn",
        junctions=["J1", "J2", "J3"],
        communication_hub=hub,
        seed=42,
    )

    observations = {
        "J1": sample_raw_observation,
        "J2": sample_raw_observation,
        "J3": sample_raw_observation,
    }

    decisions = controller.decide(observations, sim_time=30.0, eval_mode=True)

    assert set(decisions.keys()) == {"J1", "J2", "J3"}
    for j_id, dec in decisions.items():
        assert dec["action"] in {ACTION_KEEP, ACTION_SWITCH, ACTION_EXTEND}
        assert dec["is_fallback"] is False
        assert "reason" in dec


def test_marl_communication_propagation(sample_raw_observation):
    hub = CorridorCommunicationHub(corridor_sequence=["J1", "J2", "J3"])
    controller = MARLCorridorController(
        algorithm="ppo",
        junctions=["J1", "J2", "J3"],
        communication_hub=hub,
        seed=42,
    )

    # J1 is green on Hosur Road corridor (phase 2)
    j1_obs = dict(sample_raw_observation)
    j1_obs["phase"] = 2
    j1_obs["approach_queues"] = {"corridor_hosur": 10}

    controller.decide({"J1": j1_obs, "J2": sample_raw_observation, "J3": sample_raw_observation}, sim_time=40.0)

    # J2 should now receive expected inflow propagated from J1
    assert hub.get_expected_inflow("J2") > 0.0


def test_marl_fallback_on_corrupted_observation():
    controller = MARLCorridorController(algorithm="dqn", junctions=["J1", "J2", "J3"])

    # Provide corrupted input for J2
    bad_obs = {"J1": {}, "J2": {"corrupted": True}, "J3": {}}
    decisions = controller.decide(bad_obs, sim_time=10.0)

    assert decisions["J2"]["is_fallback"] is True
    assert "Fallback" in decisions["J2"]["reason"]
