"""
scripts/train_marl.py

Reproducible Multi-Agent Reinforcement Learning (MARL) Training Script:
- Trains Double-DQN and Actor-Critic PPO agents on the Silk Board corridor simulation.
- Learns inter-intersection signal coordination (J1 -> J2 -> J3) across randomized traffic demand.
- Enforces strict safety action masking and min/max green constraints during training.
- Saves checkpoints to checkpoints/marl_{algorithm}_corridor.json and training curves.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation
from traffic_service.ai.marl_controller import MARLCorridorController
from traffic_service.ai.env import CorridorObservationSpace, MultiIntersectionReward, ACTION_NAMES
from traffic_service.ai.dqn_agent import DQNAgent
from traffic_service.ai.ppo_agent import PPOAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_marl")

SUMO_CONFIG = PROJECT_ROOT / "sumo" / "silk_board" / "silk_board.sumocfg"
CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "corridor" / "training_logs"


def train_agent(
    algorithm: str = "dqn",
    num_episodes: int = 8,
    episode_duration: int = 300,
    decision_interval: float = 5.0,
    base_seed: int = 42,
) -> Dict[str, Any]:
    """
    Executes reproducible MARL training on the Silk Board corridor.
    """
    algorithm = algorithm.lower()
    logger.info("=" * 80)
    logger.info(f"STARTING MARL TRAINING: Algorithm={algorithm.upper()}")
    logger.info(f"Episodes={num_episodes} | Duration={episode_duration}s | Decision Interval={decision_interval}s | Seed={base_seed}")
    logger.info("=" * 80)

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    reward_fn = MultiIntersectionReward()
    obs_space = CorridorObservationSpace(junctions=["J1", "J2", "J3"])

    # Instantiate MARL controller
    marl = MARLCorridorController(
        algorithm=algorithm,
        junctions=["J1", "J2", "J3"],
        seed=base_seed,
    )

    training_history: List[Dict[str, Any]] = []
    start_time = time.time()

    for episode in range(1, num_episodes + 1):
        ep_seed = base_seed + (episode * 19)
        reward_fn.reset()

        # Initialize simulation in baseline mode (so SUMO runs, but MARL takes control)
        sim = MultiIntersectionSimulation(
            sumocfg_path=SUMO_CONFIG,
            mode="baseline",
            step_length=1.0,
            decision_interval=decision_interval,
            enable_emergency=False,  # Train on standard traffic progression
        )

        # Wire controllers and communication hub to MARL
        marl.set_controllers(sim.controllers)
        marl.set_communication_hub(sim.hub)

        sim.start(seed=ep_seed)

        ep_rewards: Dict[str, float] = {j: 0.0 for j in marl.junctions}
        ep_losses: Dict[str, List[float]] = {j: [] for j in marl.junctions}
        decisions_count = 0

        prev_observations: Dict[str, np.ndarray] = {}
        prev_actions: Dict[str, int] = {}
        prev_log_probs: Dict[str, float] = {}
        prev_values: Dict[str, float] = {}

        try:
            while sim.sumo_manager.get_time() < episode_duration:
                sim_time = sim.sumo_manager.step()
                states = sim.get_states(sim_time)

                # Update communication hub
                j1_corridor_q = states["J1"].approach_queues.get("corridor_hosur", 0)
                sim.hub.publish_upstream_inflow("J1", outflow_rate_veh_s=j1_corridor_q * 0.1, timestamp=sim_time)
                j2_corridor_q = states["J2"].approach_queues.get("corridor_hosur", 0)
                sim.hub.publish_upstream_inflow("J2", outflow_rate_veh_s=j2_corridor_q * 0.1, timestamp=sim_time)

                # Record step metrics
                sim.metrics_collector.record_step(sim_time, states)

                # Check if decision interval reached
                if sim_time >= sim._next_decision_time:
                    sim._next_decision_time += decision_interval
                    decisions_count += 1
                    raw_obs = sim.get_ai_observations(states)

                    # Compute current vector observations
                    curr_vecs = {
                        j_id: obs_space.vectorize_junction(j_id, raw_obs.get(j_id, {}))
                        for j_id in marl.junctions
                    }

                    # If not first step, store transitions and train on previous step
                    if prev_observations:
                        for j_id in marl.junctions:
                            st_dict = states[j_id].approach_queues
                            r = reward_fn.compute_junction_reward(
                                j_id=j_id,
                                state={
                                    "total_queue": states[j_id].total_queue,
                                    "total_waiting_time": states[j_id].total_waiting_time,
                                    "average_speed_kmh": states[j_id].average_speed_kmh,
                                    "co2_mg_s": states[j_id].emissions.co2_mg_s,
                                    "phase": states[j_id].current_phase,
                                },
                                action=prev_actions[j_id],
                            )
                            ep_rewards[j_id] += r

                            agent = marl.agents[j_id]
                            if algorithm == "dqn" and isinstance(agent, DQNAgent):
                                agent.store_transition(
                                    state=prev_observations[j_id],
                                    action=prev_actions[j_id],
                                    reward=r,
                                    next_state=curr_vecs[j_id],
                                    done=False,
                                )
                                loss = agent.train_step(batch_size=16)
                                if loss is not None:
                                    ep_losses[j_id].append(loss)
                            elif algorithm == "ppo" and isinstance(agent, PPOAgent):
                                agent.store_transition(
                                    state=prev_observations[j_id],
                                    action=prev_actions[j_id],
                                    reward=r,
                                    log_prob=prev_log_probs[j_id],
                                    value=prev_values[j_id],
                                    done=False,
                                )

                    # Select new exploratory actions
                    decisions = marl.decide(raw_obs, sim_time, eval_mode=False)
                    marl.apply_decisions(decisions, sim_time)

                    # Save current state for next transition
                    prev_observations = curr_vecs
                    for j_id in marl.junctions:
                        prev_actions[j_id] = decisions[j_id]["action"]
                        agent = marl.agents[j_id]
                        if algorithm == "ppo" and isinstance(agent, PPOAgent):
                            info = agent.select_action(curr_vecs[j_id], eval_mode=False, can_switch=True)[1]
                            prev_log_probs[j_id] = info.get("log_prob", 0.0)
                            prev_values[j_id] = info.get("value", 0.0)

            # End of episode for PPO: execute batch policy & value update
            if algorithm == "ppo":
                for j_id in marl.junctions:
                    agent = marl.agents[j_id]
                    if isinstance(agent, PPOAgent):
                        p_info = agent.train_step(last_value=0.0, epochs=4)
                        ep_losses[j_id].append(p_info.get("loss", 0.0))

            summary = sim.metrics_collector.compute_summary()
            ep_time = sim.sumo_manager.get_time()

        finally:
            sim.close()

        # Log episode metrics
        total_ep_reward = sum(ep_rewards.values())
        avg_loss = np.mean([np.mean(losses) if losses else 0.0 for losses in ep_losses.values()])

        ep_record = {
            "episode": episode,
            "seed": ep_seed,
            "total_reward": round(float(total_ep_reward), 2),
            "rewards_per_junction": {j: round(r, 2) for j, r in ep_rewards.items()},
            "mean_loss": round(float(avg_loss), 4),
            "mean_travel_time_s": round(summary.mean_corridor_travel_time_s, 2),
            "mean_speed_kmh": round(summary.mean_corridor_speed_kmh, 2),
            "total_waiting_time_s": round(summary.total_corridor_waiting_time_s, 2),
            "mean_queue": round(summary.mean_corridor_queue, 2),
            "completed_trips": summary.total_corridor_trips_completed,
            "decisions_count": decisions_count,
        }
        training_history.append(ep_record)

        logger.info(
            f"Ep {episode:02d}/{num_episodes:02d} [Seed {ep_seed}]: "
            f"Reward={total_ep_reward:7.1f} | "
            f"Wait={summary.total_corridor_waiting_time_s:6.1f}s | "
            f"Speed={summary.mean_corridor_speed_kmh:4.1f} km/h | "
            f"Loss={avg_loss:.4f}"
        )

    # Save Checkpoint
    checkpoint_file = CHECKPOINT_DIR / f"marl_{algorithm}_corridor.json"
    marl.save_checkpoint(checkpoint_file)

    total_training_duration = time.time() - start_time

    # Save Training History Log
    training_summary = {
        "algorithm": algorithm,
        "base_seed": base_seed,
        "num_episodes": num_episodes,
        "episode_duration_s": episode_duration,
        "total_training_wall_clock_s": round(total_training_duration, 2),
        "checkpoint_file": str(checkpoint_file),
        "episodes": training_history,
    }

    summary_file = OUTPUT_DIR / f"training_summary_{algorithm}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(training_summary, f, indent=2)

    logger.info("=" * 80)
    logger.info(f"TRAINING COMPLETED in {total_training_duration:.1f}s")
    logger.info(f"Checkpoint saved to: {checkpoint_file}")
    logger.info(f"Training summary saved to: {summary_file}")
    logger.info("=" * 80)

    return training_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Train MARL Corridor Controllers (DQN and PPO)")
    parser.add_argument("--algorithm", choices=["dqn", "ppo", "both"], default="both", help="Algorithm to train")
    parser.add_argument("--episodes", type=int, default=8, help="Number of training episodes per algorithm")
    parser.add_argument("--duration", type=int, default=300, help="Simulation duration (s) per episode")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    args = parser.parse_args()

    if args.algorithm in ("dqn", "both"):
        train_agent(algorithm="dqn", num_episodes=args.episodes, episode_duration=args.duration, base_seed=args.seed)

    if args.algorithm in ("ppo", "both"):
        train_agent(algorithm="ppo", num_episodes=args.episodes, episode_duration=args.duration, base_seed=args.seed)


if __name__ == "__main__":
    main()
