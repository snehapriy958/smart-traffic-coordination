"""
scripts/train_phase4_marl.py

Phase 4 Master MARL Training & Evaluation Pipeline:
- Series 4B: Observation Space Dimensionality Ablation (30 training runs, 300 evaluation runs)
- Series 4C: Cooperative Reward Coupling Ablation (25 training runs, 250 evaluation runs)
- Series 4E: Multi-Objective Passenger Reward Formulation (10 training runs, 100 evaluation runs)

Total workload = 65 training runs, 650 evaluation runs.
Checkpoints saved under `checkpoints/phase4/`.
Outputs saved under `outputs/experiments/phase4/`.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import logging
import os
from pathlib import Path
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import SUMO_CONFIG_PATH
from traffic_service.ai.env import (
    CorridorObservationSpace,
    MultiIntersectionReward,
    RewardWeights,
)
from traffic_service.ai.mappo_agent import MAPPOAgent, train_mappo_corridor
from traffic_service.ai.dqn_agent import DQNAgent
from traffic_service.ai.marl_controller import MARLCorridorController
from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation
from traffic_service.resilience.detailed_collector import DetailedCorridorMetricsCollector
from traffic_service.resilience.transit_priority import TransitSignalPriorityManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("phase4_marl_training")

BASE_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase4"
CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints" / "phase4"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================================
# TRAINING LOGIC
# =====================================================================

def train_marl_run(
    algorithm: str,
    train_seed: int,
    observation_dim: int = 14,
    reward_coupling_beta: float = 0.50,
    passenger_weighted: bool = False,
    num_episodes: int = 150,
    episode_duration_s: float = 1200.0,
    decision_interval_s: float = 5.0,
    checkpoint_out_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Executes a single clean MARL training run from scratch under the specified configuration.
    Strictly enforces 150 episodes for confirmatory Phase 4 execution.
    """
    if num_episodes < 150:
        raise ValueError(f"Unsafe episode count {num_episodes}. Confirmatory Phase 4 requires 150 episodes.")
    random.seed(train_seed)
    np.random.seed(train_seed)
    torch.manual_seed(train_seed)

    marl = MARLCorridorController(
        algorithm=algorithm,
        junctions=["J1", "J2", "J3"],
        seed=train_seed,
        observation_dim=observation_dim,
        enable_safety_shield=True,
        enable_communication=True,
    )

    reward_weights = RewardWeights(
        alpha=reward_coupling_beta,
        passenger_weighted=passenger_weighted,
    )
    reward_fn = MultiIntersectionReward(weights=reward_weights)
    obs_space = CorridorObservationSpace(dim=observation_dim)

    t0 = time.time()
    history = []

    for ep in range(1, num_episodes + 1):
        ep_seed = train_seed * 100 + ep * 13
        reward_fn.reset()
        ep_rewards = {j: 0.0 for j in ["J1", "J2", "J3"]}
        policy_losses = []
        critic_losses = []
        td_losses = []

        label = f"trn_{algorithm}_{observation_dim}d_{train_seed}_{ep}_{os.getpid()}"
        sim = MultiIntersectionSimulation(
            sumocfg_path=SUMO_CONFIG_PATH,
            mode="baseline",
            step_length=1.0,
            decision_interval=decision_interval_s,
            gui=False,
            label=label,
            enable_safety_shield=True,
            enable_communication=True,
            observation_dim=observation_dim,
        )
        marl.controllers = sim.controllers
        marl.hub = sim.hub
        marl.starvation_tracker.reset()

        sim.start(seed=ep_seed)
        try:
            sim_time = 0.0
            raw_states = sim.get_states(sim_time)
            raw_obs = sim.get_ai_observations(raw_states)
            prev_vecs = {j: obs_space.vectorize_junction(raw_states[j], j) for j in ["J1", "J2", "J3"]}
            prev_corridor_vec = np.concatenate([prev_vecs[j] for j in ["J1", "J2", "J3"]])

            while sim_time < episode_duration_s:
                # 1. Action selection
                decisions = marl.decide(raw_obs, sim_time=sim_time, eval_mode=False)
                marl.apply_decisions(decisions, sim_time)

                # 2. Advance simulation by decision interval
                for _ in range(int(decision_interval_s)):
                    states, _ = sim.step()

                sim_time = sim.sumo_manager.get_time()
                raw_obs_next = sim.get_ai_observations(states)
                next_vecs = {j: obs_space.vectorize_junction(states[j], j) for j in ["J1", "J2", "J3"]}
                next_corridor_vec = np.concatenate([next_vecs[j] for j in ["J1", "J2", "J3"]])
                is_done = (sim_time >= episode_duration_s)

                actions_dict = {j: decisions[j]["action"] for j in ["J1", "J2", "J3"]}
                completed_now = len(sim.metrics_collector._completed_travel_times)

                mixed_r, _ = reward_fn.compute_mixed_rewards(
                    states=raw_obs_next,
                    actions=actions_dict,
                    comm_hub=sim.hub,
                    starvation_tracker=marl.starvation_tracker,
                    completed_trips=completed_now,
                    current_time=sim_time,
                )

                for j in ["J1", "J2", "J3"]:
                    ep_rewards[j] += mixed_r[j]

                # Train step
                if algorithm == "mappo":
                    for j_id, agent in marl.agents.items():
                        assert isinstance(agent, MAPPOAgent)
                        dec = decisions[j_id]
                        agent.store_transition(
                            local_state=prev_vecs[j_id],
                            corridor_state=prev_corridor_vec,
                            action=dec["action"],
                            action_mask=np.array(dec.get("action_mask", [1.0, 1.0, 1.0]), dtype=np.float32),
                            reward=mixed_r[j_id],
                            log_prob=dec.get("log_prob", 0.0),
                            value=dec.get("value", 0.0),
                            done=is_done,
                        )

                    first_agent = marl.agents["J1"]
                    if len(first_agent.buffer) >= 16 or is_done:
                        last_c_val = first_agent.get_corridor_value(next_corridor_vec) if not is_done else 0.0
                        train_res = train_mappo_corridor(
                            agents=marl.agents,
                            shared_critic=marl.shared_critic,
                            shared_critic_optimizer=marl.shared_critic_optimizer,
                            last_corridor_value=last_c_val,
                            epochs=2,
                        )
                        policy_losses.append(train_res.get("mean_policy_loss", 0.0))
                        critic_losses.append(train_res.get("critic_loss", 0.0))

                elif algorithm == "dqn":
                    for j_id, agent in marl.agents.items():
                        assert isinstance(agent, DQNAgent)
                        act = decisions[j_id]["action"]
                        agent.replay_buffer.push(
                            prev_vecs[j_id], act, mixed_r[j_id], next_vecs[j_id], is_done
                        )
                        if len(agent.replay_buffer) >= 16:
                            td_l = agent.train_step(batch_size=16)
                            td_losses.append(td_l)

                prev_vecs = next_vecs
                prev_corridor_vec = next_corridor_vec
                raw_obs = raw_obs_next

            ep_summary = sim.metrics_collector.compute_summary()
            ep_rec = {
                "episode": ep,
                "mean_reward": float(np.mean(list(ep_rewards.values()))),
                "trips_completed": ep_summary.total_corridor_trips_completed,
                "travel_time_mean_s": ep_summary.mean_corridor_travel_time_s,
                "cumulative_delay_veh_s": ep_summary.cumulative_delay_veh_s,
                "policy_loss": float(np.mean(policy_losses)) if policy_losses else 0.0,
                "critic_loss": float(np.mean(critic_losses)) if critic_losses else 0.0,
                "td_loss": float(np.mean(td_losses)) if td_losses else 0.0,
            }
            history.append(ep_rec)

        finally:
            sim.close()

    wall_time = time.time() - t0

    # Save checkpoint
    if checkpoint_out_path is not None:
        checkpoint_out_path.parent.mkdir(parents=True, exist_ok=True)
        marl.save_checkpoint(checkpoint_out_path)
        logger.info(f"Saved checkpoint to {checkpoint_out_path.name}")

    return {
        "algorithm": algorithm,
        "train_seed": train_seed,
        "observation_dim": observation_dim,
        "reward_coupling_beta": reward_coupling_beta,
        "passenger_weighted": passenger_weighted,
        "num_episodes": num_episodes,
        "wall_time_s": round(wall_time, 2),
        "history": history,
        "checkpoint_path": str(checkpoint_out_path) if checkpoint_out_path else None,
    }


# =====================================================================
# EVALUATION WORKER TASK
# =====================================================================

def evaluate_marl_checkpoint_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates a specific trained MARL checkpoint on an evaluation seed.
    """
    series = task["series"]
    checkpoint_path = task["checkpoint_path"]
    eval_seed = task["eval_seed"]
    train_seed = task.get("train_seed")
    observation_dim = int(task.get("observation_dim", 14))
    enable_tsp = bool(task.get("enable_tsp", False))
    duration = float(task.get("duration", 900.0))
    out_file = Path(task["out_file"])
    algo = task.get("algorithm", "mappo")

    if out_file.is_file():
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                if d.get("completed", False):
                    return d
        except Exception:
            pass

    out_file.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    mode = f"marl_{algo}"
    label = f"ev_{series}_{train_seed}_{eval_seed}_{os.getpid()}_{int(time.time()*1000)%10000}"

    try:
        sim = MultiIntersectionSimulation(
            sumocfg_path=SUMO_CONFIG_PATH,
            mode=mode,
            step_length=1.0,
            decision_interval=5.0,
            gui=False,
            label=label,
            observation_dim=observation_dim,
            checkpoint_path=checkpoint_path,
        )

        detailed_collector = DetailedCorridorMetricsCollector(
            entry_edge="172853382#2",
            exit_edge="40696223#1",
            step_length=1.0,
        )
        sim.metrics_collector = detailed_collector

        tsp_mgr: Optional[TransitSignalPriorityManager] = None
        if enable_tsp:
            tsp_mgr = TransitSignalPriorityManager(
                controllers=sim.controllers,
                detection_distance_m=150.0,
                max_bus_eta_s=5.0,
                extension_seconds=5.0,
                max_green=60.0,
                enabled=True,
            )

        sim.start(seed=eval_seed)
        try:
            while sim.sumo_manager.get_time() < duration:
                states, _ = sim.step()
                sim_time = sim.sumo_manager.get_time()
                if tsp_mgr is not None:
                    tsp_mgr.update(sim_time)

            metrics_summary = detailed_collector.compute_detailed_summary(
                emergency_duration=None,
                emergency_cleared=True,
            )

            record: Dict[str, Any] = {
                "series": series,
                "algorithm": algo,
                "formulation": task.get("formulation"),
                "beta": task.get("beta"),
                "train_seed": train_seed,
                "eval_seed": eval_seed,
                "observation_dim": observation_dim,
                "checkpoint_path": checkpoint_path,
                "completed": True,
                "execution_wall_time_s": round(time.time() - t0, 2),
                "total_corridor_trips_completed": metrics_summary["total_corridor_trips_completed"],
                "mean_corridor_travel_time_s": metrics_summary["mean_corridor_travel_time_s"],
                "mean_corridor_speed_kmh": metrics_summary["mean_corridor_speed_kmh"],
                "cumulative_delay_veh_s": metrics_summary["cumulative_delay_veh_s"],
                "mean_corridor_queue": metrics_summary["mean_corridor_queue"],
                "max_corridor_queue": metrics_summary["max_corridor_queue"],
                "total_co2_kg": metrics_summary["total_co2_kg"],
                "total_fuel_liters": metrics_summary["total_fuel_liters"],
                "reliability": metrics_summary["reliability"],
                "multi_modal": metrics_summary["multi_modal"],
                "equity": metrics_summary["equity"],
            }

            if tsp_mgr is not None:
                record["transit_priority"] = asdict(tsp_mgr.compute_summary())

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)

            return record

        finally:
            sim.close()

    except Exception as exc:
        logger.error(f"Eval failure ({series}, seed={eval_seed}): {exc!r}", exc_info=True)
        err_rec = {
            "series": series,
            "train_seed": train_seed,
            "eval_seed": eval_seed,
            "completed": False,
            "error": str(exc),
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(err_rec, f, indent=2)
        return err_rec


# =====================================================================
# SERIES RUNNERS
# =====================================================================

def train_task_wrapper(task: Dict[str, Any]) -> Dict[str, Any]:
    """Helper wrapper for parallel training dispatch."""
    ckpt_path = Path(task["checkpoint_out_path"])
    if ckpt_path.is_file():
        logger.info(f"Using cached checkpoint: {ckpt_path.name}")
        return {"status": "CACHED", "checkpoint_path": str(ckpt_path)}
    logger.info(f"Training: {ckpt_path.name}...")
    return train_marl_run(
        algorithm=task["algorithm"],
        train_seed=task["train_seed"],
        observation_dim=task.get("observation_dim", 14),
        reward_coupling_beta=task.get("reward_coupling_beta", 0.50),
        passenger_weighted=task.get("passenger_weighted", False),
        num_episodes=task.get("num_episodes", 5),
        episode_duration_s=task.get("episode_duration_s", 1200.0),
        decision_interval_s=task.get("decision_interval_s", 5.0),
        checkpoint_out_path=ckpt_path,
    )


def run_series_4b(workers: int = 4, episodes: int = 150, duration: float = 900.0) -> Dict[str, Any]:
    """
    Series 4B: Observation Space Dimensionality Ablation
    3 dims (14, 8, 4) x 2 algos (MAPPO, DQN) x 5 train seeds = 30 training runs.
    Evaluated on seeds 1..10 = 300 evaluation runs.
    """
    series_dir = BASE_OUTPUT_DIR / "series_4b_observation_space"
    series_dir.mkdir(parents=True, exist_ok=True)
    dims = [14, 8, 4]
    algos = ["mappo", "dqn"]
    train_seeds = [101, 102, 103, 104, 105]
    eval_seeds = list(range(1, 11))

    logger.info(">>> STEP 1: PARALLEL TRAINING 30 MODELS FOR SERIES 4B <<<")
    train_tasks = []
    checkpoints = {}
    for algo in algos:
        for dim in dims:
            for ts in train_seeds:
                ckpt_name = f"series_4b_{algo}_{dim}dim_seed{ts}.json"
                ckpt_file = CHECKPOINT_DIR / ckpt_name
                checkpoints[(algo, dim, ts)] = str(ckpt_file)
                train_tasks.append({
                    "algorithm": algo,
                    "train_seed": ts,
                    "observation_dim": dim,
                    "num_episodes": episodes,
                    "checkpoint_out_path": str(ckpt_file),
                })

    with ProcessPoolExecutor(max_workers=workers) as pool:
        list(pool.map(train_task_wrapper, train_tasks))

    logger.info(">>> STEP 2: EVALUATING 300 RUNS FOR SERIES 4B <<<")
    eval_tasks = []
    for (algo, dim, ts), ckpt_path in checkpoints.items():
        for es in eval_seeds:
            out_f = series_dir / f"eval_{algo}_{dim}dim_train{ts}_eval{es}.json"
            eval_tasks.append({
                "series": "4b_observation_space",
                "algorithm": algo,
                "observation_dim": dim,
                "train_seed": ts,
                "eval_seed": es,
                "checkpoint_path": ckpt_path,
                "duration": duration,
                "out_file": str(out_f),
            })

    results = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(evaluate_marl_checkpoint_task, t): t for t in eval_tasks}
        for future in as_completed(future_map):
            res = future.result()
            results.append(res)

    summary: Dict[str, Any] = {
        "metadata": {
            "experiment": "Series 4B: Observation Space Dimensionality Ablation",
            "dims": dims,
            "algorithms": algos,
            "train_seeds": train_seeds,
            "eval_seeds": eval_seeds,
            "total_eval_runs": len(eval_tasks),
            "completed_runs": sum(1 for r in results if r.get("completed")),
        },
        "per_dimension": {},
    }

    for algo in algos:
        summary["per_dimension"][algo] = {}
        for dim in dims:
            runs = [
                r for r in results
                if r.get("algorithm") == algo
                and r.get("observation_dim") == dim
                and r.get("completed")
            ]
            runs.sort(key=lambda x: (x.get("train_seed", 0), x.get("eval_seed", 0)))
            tts = [r["mean_corridor_travel_time_s"] for r in runs if r["mean_corridor_travel_time_s"] is not None]
            delays = [r["cumulative_delay_veh_s"] for r in runs]
            trips = [r["total_corridor_trips_completed"] for r in runs]

            summary["per_dimension"][algo][f"{dim}dim"] = {
                "runs_completed": len(runs),
                "travel_time_mean_s": round(float(np.mean(tts)), 2) if tts else None,
                "travel_time_std_s": round(float(np.std(tts, ddof=1)), 2) if len(tts) > 1 else 0.0,
                "cumulative_delay_veh_s": round(float(np.mean(delays)), 2),
                "total_corridor_trips_completed": round(float(np.mean(trips)), 1),
                "raw_travel_times": tts,
                "raw_delays": delays,
            }

    with open(series_dir / "series_4b_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def run_series_4c(workers: int = 4, episodes: int = 150, duration: float = 900.0) -> Dict[str, Any]:
    """
    Series 4C: Cooperative Reward Coupling Ablation
    5 betas ({0.0, 0.25, 0.50, 0.75, 1.0}) x 5 train seeds = 25 training runs.
    Evaluated on seeds 1..10 = 250 evaluation runs.
    """
    series_dir = BASE_OUTPUT_DIR / "series_4c_reward_coupling"
    series_dir.mkdir(parents=True, exist_ok=True)
    betas = [0.0, 0.25, 0.50, 0.75, 1.0]
    train_seeds = [101, 102, 103, 104, 105]
    eval_seeds = list(range(1, 11))

    logger.info(">>> STEP 1: PARALLEL TRAINING 25 MODELS FOR SERIES 4C <<<")
    train_tasks = []
    checkpoints = {}
    for beta in betas:
        for ts in train_seeds:
            b_tag = f"beta_{int(beta*100):03d}"
            ckpt_name = f"series_4c_mappo_{b_tag}_seed{ts}.json"
            ckpt_file = CHECKPOINT_DIR / ckpt_name
            checkpoints[(beta, ts)] = str(ckpt_file)
            train_tasks.append({
                "algorithm": "mappo",
                "train_seed": ts,
                "observation_dim": 14,
                "reward_coupling_beta": beta,
                "num_episodes": episodes,
                "checkpoint_out_path": str(ckpt_file),
            })

    with ProcessPoolExecutor(max_workers=workers) as pool:
        list(pool.map(train_task_wrapper, train_tasks))

    logger.info(">>> STEP 2: EVALUATING 250 RUNS FOR SERIES 4C <<<")
    eval_tasks = []
    for (beta, ts), ckpt_path in checkpoints.items():
        b_tag = f"beta_{int(beta*100):03d}"
        for es in eval_seeds:
            out_f = series_dir / f"eval_mappo_{b_tag}_train{ts}_eval{es}.json"
            eval_tasks.append({
                "series": "4c_reward_coupling",
                "algorithm": "mappo",
                "beta": beta,
                "train_seed": ts,
                "eval_seed": es,
                "checkpoint_path": ckpt_path,
                "duration": duration,
                "out_file": str(out_f),
            })

    results = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(evaluate_marl_checkpoint_task, t): t for t in eval_tasks}
        for future in as_completed(future_map):
            res = future.result()
            results.append(res)

    summary: Dict[str, Any] = {
        "metadata": {
            "experiment": "Series 4C: Cooperative Reward Coupling Ablation",
            "betas": betas,
            "train_seeds": train_seeds,
            "eval_seeds": eval_seeds,
            "total_eval_runs": len(eval_tasks),
            "completed_runs": sum(1 for r in results if r.get("completed")),
        },
        "per_beta": {},
    }

    for beta in betas:
        b_tag = f"beta_{int(beta*100):03d}"
        runs = [
            r for r in results
            if r.get("beta") == beta
            and r.get("completed")
        ]
        runs.sort(key=lambda x: (x.get("train_seed", 0), x.get("eval_seed", 0)))
        tts = [r["mean_corridor_travel_time_s"] for r in runs if r["mean_corridor_travel_time_s"] is not None]
        delays = [r["cumulative_delay_veh_s"] for r in runs]
        trips = [r["total_corridor_trips_completed"] for r in runs]

        summary["per_beta"][b_tag] = {
            "beta": beta,
            "runs_completed": len(runs),
            "travel_time_mean_s": round(float(np.mean(tts)), 2) if tts else None,
            "travel_time_std_s": round(float(np.std(tts, ddof=1)), 2) if len(tts) > 1 else 0.0,
            "cumulative_delay_veh_s": round(float(np.mean(delays)), 2),
            "total_corridor_trips_completed": round(float(np.mean(trips)), 1),
            "total_corridor_trips_std": round(float(np.std(trips, ddof=1)), 2) if len(trips) > 1 else 0.0,
            "raw_travel_times": tts,
            "raw_trips": trips,
        }

    with open(series_dir / "series_4c_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def run_series_4e(workers: int = 4, episodes: int = 150, duration: float = 900.0) -> Dict[str, Any]:
    """
    Series 4E: Multi-Objective Passenger Reward Formulation
    2 formulations x 5 train seeds = 10 training runs.
    Evaluated on seeds 1..10 with TSP enabled = 100 evaluation runs (50 matched pairs).
    """
    series_dir = BASE_OUTPUT_DIR / "series_4e_passenger_reward"
    series_dir.mkdir(parents=True, exist_ok=True)
    formulations = [
        {"name": "delay_centric", "passenger_weighted": False},
        {"name": "passenger_weighted", "passenger_weighted": True},
    ]
    train_seeds = [101, 102, 103, 104, 105]
    eval_seeds = list(range(1, 11))

    logger.info(">>> STEP 1: PARALLEL TRAINING 10 MODELS FOR SERIES 4E <<<")
    train_tasks = []
    checkpoints = {}
    for form in formulations:
        for ts in train_seeds:
            ckpt_name = f"series_4e_mappo_{form['name']}_seed{ts}.json"
            ckpt_file = CHECKPOINT_DIR / ckpt_name
            checkpoints[(form["name"], ts)] = str(ckpt_file)
            train_tasks.append({
                "algorithm": "mappo",
                "train_seed": ts,
                "observation_dim": 14,
                "passenger_weighted": form["passenger_weighted"],
                "num_episodes": episodes,
                "checkpoint_out_path": str(ckpt_file),
            })

    with ProcessPoolExecutor(max_workers=workers) as pool:
        list(pool.map(train_task_wrapper, train_tasks))

    logger.info(">>> STEP 2: EVALUATING 100 RUNS (50 MATCHED PAIRS) FOR SERIES 4E <<<")
    eval_tasks = []
    for form in formulations:
        for ts in train_seeds:
            ckpt_path = checkpoints[(form["name"], ts)]
            for es in eval_seeds:
                out_f = series_dir / f"eval_mappo_{form['name']}_train{ts}_eval{es}.json"
                eval_tasks.append({
                    "series": "4e_passenger_reward",
                    "algorithm": "mappo",
                    "formulation": form["name"],
                    "train_seed": ts,
                    "eval_seed": es,
                    "checkpoint_path": ckpt_path,
                    "enable_tsp": True,
                    "duration": duration,
                    "out_file": str(out_f),
                })

    results = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(evaluate_marl_checkpoint_task, t): t for t in eval_tasks}
        for future in as_completed(future_map):
            res = future.result()
            results.append(res)

    summary: Dict[str, Any] = {
        "metadata": {
            "experiment": "Series 4E: Multi-Objective Passenger Reward Formulation",
            "formulations": ["delay_centric", "passenger_weighted"],
            "train_seeds": train_seeds,
            "eval_seeds": eval_seeds,
            "total_eval_runs": len(eval_tasks),
            "completed_runs": sum(1 for r in results if r.get("completed")),
        },
        "per_formulation": {},
        "matched_pairs": [],
    }

    for form in formulations:
        fname = form["name"]
        runs = [
            r for r in results
            if (r.get("formulation") == fname or fname in r.get("checkpoint_path", ""))
            and r.get("completed")
        ]
        tts = [r["mean_corridor_travel_time_s"] for r in runs if r["mean_corridor_travel_time_s"] is not None]
        delays = [r["cumulative_delay_veh_s"] for r in runs]
        phds = [r["multi_modal"]["passenger_hours_of_delay_phd"] for r in runs]
        tsp_reqs = [r.get("transit_priority", {}).get("total_requests", 0) for r in runs]
        tsp_grants = [r.get("transit_priority", {}).get("granted_requests", 0) for r in runs]
        tsp_rates = [g / max(1, req) for g, req in zip(tsp_grants, tsp_reqs)]

        summary["per_formulation"][fname] = {
            "runs_completed": len(runs),
            "travel_time_mean_s": round(float(np.mean(tts)), 2) if tts else None,
            "passenger_hours_of_delay_phd": round(float(np.mean(phds)), 3),
            "tsp_requests_mean": round(float(np.mean(tsp_reqs)), 1),
            "tsp_grants_mean": round(float(np.mean(tsp_grants)), 1),
            "tsp_grant_rate_mean": round(float(np.mean(tsp_rates)), 4),
            "raw_grant_rates": tsp_rates,
            "raw_phds": phds,
        }

    # Construct 50 matched pairs differences
    for ts in train_seeds:
        for es in eval_seeds:
            run_delay = next(
                (r for r in results if (r.get("formulation") == "delay_centric" or "delay_centric" in r.get("checkpoint_path", "")) and r.get("train_seed") == ts and r.get("eval_seed") == es),
                None
            )
            run_pass = next(
                (r for r in results if (r.get("formulation") == "passenger_weighted" or "passenger_weighted" in r.get("checkpoint_path", "")) and r.get("train_seed") == ts and r.get("eval_seed") == es),
                None
            )
            if run_delay and run_pass and run_delay.get("completed") and run_pass.get("completed"):
                req_d = run_delay.get("transit_priority", {}).get("total_requests", 0)
                req_p = run_pass.get("transit_priority", {}).get("total_requests", 0)
                g_d = run_delay.get("transit_priority", {}).get("granted_requests", 0)
                g_p = run_pass.get("transit_priority", {}).get("granted_requests", 0)

                rate_d = g_d / req_d if req_d > 0 else None
                rate_p = g_p / req_p if req_p > 0 else None
                diff = (rate_p - rate_d) if (rate_d is not None and rate_p is not None) else None

                summary["matched_pairs"].append({
                    "train_seed": ts,
                    "eval_seed": es,
                    "req_delay": req_d,
                    "req_passenger": req_p,
                    "grants_delay": g_d,
                    "grants_passenger": g_p,
                    "grant_rate_delay": round(rate_d, 4) if rate_d is not None else None,
                    "grant_rate_passenger": round(rate_p, 4) if rate_p is not None else None,
                    "delta_grant_rate": round(diff, 4) if diff is not None else None,
                    "phd_delay": run_delay["multi_modal"]["passenger_hours_of_delay_phd"],
                    "phd_passenger": run_pass["multi_modal"]["passenger_hours_of_delay_phd"],
                    "delta_phd": round(
                        run_pass["multi_modal"]["passenger_hours_of_delay_phd"]
                        - run_delay["multi_modal"]["passenger_hours_of_delay_phd"],
                        3
                    ),
                })

    with open(series_dir / "series_4e_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


# =====================================================================
# MAIN
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description="Phase 4 MARL Training & Evaluation Suite")
    parser.add_argument("--workers", type=int, default=4, help="Workers (default: 4 for safe memory footprint)")
    parser.add_argument("--episodes", type=int, default=150, help="Training episodes per run (strictly 150)")
    parser.add_argument("--duration", type=float, default=900.0, help="Eval simulation duration (default: 900.0s)")
    parser.add_argument(
        "--series",
        nargs="+",
        default=["4b", "4c", "4e"],
        help="Which series to execute (4b, 4c, 4e)",
    )
    args = parser.parse_args()

    if args.episodes < 150:
        raise ValueError(f"Unsafe episode count {args.episodes}. Confirmatory Phase 4 requires strictly 150 episodes.")

    t_start = time.time()
    logger.info("======================================================================")
    logger.info("PHASE 4 MARL TRAINING & EVALUATION PIPELINE")
    logger.info(f"Workers: {args.workers} | Episodes: {args.episodes} | Series: {args.series}")
    logger.info("======================================================================")

    if "4b" in args.series:
        run_series_4b(workers=args.workers, episodes=args.episodes, duration=args.duration)

    if "4c" in args.series:
        run_series_4c(workers=args.workers, episodes=args.episodes, duration=args.duration)

    if "4e" in args.series:
        run_series_4e(workers=args.workers, episodes=args.episodes, duration=args.duration)

    total_time = time.time() - t_start
    logger.info("======================================================================")
    logger.info(f"MARL TRAINING & EVALUATION COMPLETE IN {total_time:.1f}s ({total_time/60:.2f} min)")
    logger.info("======================================================================")


if __name__ == "__main__":
    main()
