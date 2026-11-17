import pytest
import numpy as np
import torch
from traffic_service.ai.env import CorridorObservationSpace
from traffic_service.ai.marl_controller import MARLCorridorController
from traffic_service.ai.dqn_agent import DQNAgent
from traffic_service.ai.ppo_agent import PPOAgent
from traffic_service.ai.mappo_agent import MAPPOAgent

def test_empty_observations_dimensions():
    """Verify empty observations return correct shapes for 14D, 8D, and 4D."""
    obs14 = CorridorObservationSpace(dim=14)
    obs8 = CorridorObservationSpace(dim=8)
    obs4 = CorridorObservationSpace(dim=4)

    v14 = obs14.vectorize_junction("J1", {})
    v8 = obs8.vectorize_junction("J1", {})
    v4 = obs4.vectorize_junction("J1", {})

    assert v14.shape == (14,), f"Expected shape (14,), got {v14.shape}"
    assert v8.shape == (8,), f"Expected shape (8,), got {v8.shape}"
    assert v4.shape == (4,), f"Expected shape (4,), got {v4.shape}"
    assert np.all(v14 == 0.0)
    assert np.all(v8 == 0.0)
    assert np.all(v4 == 0.0)

def test_non_empty_observations_dimensions():
    """Verify non-empty observations return correct shapes and features for 14D, 8D, and 4D."""
    raw = {
        "phase": 2,
        "phase_elapsed": 20.0,
        "time_to_switch": 10.0,
        "total_queue": 15,
        "average_speed_kmh": 25.0,
        "total_waiting_time": 40.0,
        "vehicle_count": 18,
        "upstream_expected_inflow": 4.0,
        "approaching_platoons_count": 2,
        "co2_mg_s": 500.0,
        "emergency_approaching": False,
        "approach_queues": {"corridor_hosur": 10, "side_cross": 5},
    }

    obs14 = CorridorObservationSpace(dim=14)
    obs8 = CorridorObservationSpace(dim=8)
    obs4 = CorridorObservationSpace(dim=4)

    v14 = obs14.vectorize_junction("J1", raw)
    v8 = obs8.vectorize_junction("J1", raw)
    v4 = obs4.vectorize_junction("J1", raw)

    assert v14.shape == (14,)
    assert v8.shape == (8,)
    assert v4.shape == (4,)

    # Check 8D feature subset [0, 1, 2, 3, 4, 5, 6, 13]
    expected_8d = v14[[0, 1, 2, 3, 4, 5, 6, 13]]
    np.testing.assert_allclose(v8, expected_8d)

    # Check 4D feature subset [0, 1, 4, 5]
    expected_4d = v14[[0, 1, 4, 5]]
    np.testing.assert_allclose(v4, expected_4d)

def test_dqn_marl_controller_initialization_all_dims():
    """Verify DQN agents in MARLCorridorController are created with correct input dimensions."""
    for dim in [14, 8, 4]:
        ctrl = MARLCorridorController(algorithm="dqn", observation_dim=dim, seed=42)
        for j_id in ["J1", "J2", "J3"]:
            agent = ctrl.agents[j_id]
            assert isinstance(agent, DQNAgent)
            assert agent.in_features == dim, f"Expected {dim}, got {agent.in_features}"
            assert agent.q_network.in_features == dim
            assert agent.target_network.in_features == dim
            # Check weight matrices shape of fc1
            w = agent.q_network.get_weights()
            assert w["fc1_w"].shape == (dim, 64), f"Expected ({dim}, 64), got {w['fc1_w'].shape}"

def test_dqn_forward_and_train_step_8d_and_4d():
    """Verify forward pass and train_step for DQN with 8D and 4D observations."""
    for dim in [8, 4]:
        agent = DQNAgent(agent_id="J1", in_features=dim, seed=101)
        obs = np.ones(dim, dtype=np.float32)

        # Action selection / forward pass
        action, info = agent.select_action(obs, eval_mode=False)
        assert action in [0, 1, 2]
        assert "q_values" in info
        assert len(info["q_values"]) == 3

        # Populate replay buffer with transitions
        for step in range(20):
            s_t = np.random.randn(dim).astype(np.float32)
            s_tp1 = np.random.randn(dim).astype(np.float32)
            agent.replay_buffer.push(s_t, step % 3, 1.0, s_tp1, False)

        assert len(agent.replay_buffer) == 20
        # Train step should succeed without RuntimeError
        loss = agent.train_step(batch_size=16)
        assert isinstance(loss, float)
        assert not np.isnan(loss) and not np.isinf(loss)

def test_dqn_14d_behavior_preserved():
    """Verify DQN 14D remains functional and deterministic with existing behavior."""
    agent = DQNAgent(agent_id="J1", in_features=14, seed=42)
    obs = np.zeros(14, dtype=np.float32)
    action, info = agent.select_action(obs, eval_mode=True)
    assert action in [0, 1, 2]

    # Buffer & train step
    for step in range(16):
        agent.replay_buffer.push(np.zeros(14), 0, 0.5, np.zeros(14), False)
    loss = agent.train_step(batch_size=16)
    assert isinstance(loss, float)
    assert not np.isnan(loss)

def test_mappo_regression_all_dims():
    """Verify MAPPO controller and agents initialize and step across 14D, 8D, and 4D."""
    for dim in [14, 8, 4]:
        ctrl = MARLCorridorController(algorithm="mappo", observation_dim=dim, seed=101)
        for j_id in ["J1", "J2", "J3"]:
            agent = ctrl.agents[j_id]
            assert isinstance(agent, MAPPOAgent)
            assert agent.in_features == dim
            assert agent.corridor_features == dim * 3

        # Test coordination with empty observations
        raw_obs = {j: {} for j in ["J1", "J2", "J3"]}
        decisions = ctrl.decide(raw_obs, sim_time=10.0)
        assert set(decisions.keys()) == {"J1", "J2", "J3"}
        for j in ["J1", "J2", "J3"]:
            assert decisions[j]["action"] in [0, 1, 2]

def test_ppo_initialization_all_dims():
    """Verify PPO controller and agents initialize across 14D, 8D, and 4D."""
    for dim in [14, 8, 4]:
        ctrl = MARLCorridorController(algorithm="ppo", observation_dim=dim, seed=101)
        for j_id in ["J1", "J2", "J3"]:
            agent = ctrl.agents[j_id]
            assert isinstance(agent, PPOAgent)
            assert agent.in_features == dim
            w = agent.ac_network.get_weights()
            assert w["fc1_w"].shape == (dim, 64)
