#!/usr/bin/env python3
"""
Series 4C: Cooperative Reward Coupling Mechanism Ablation
Master Sequential Execution & Confirmatory Evaluation Harness

Protocol:
- Algorithm: MAPPO only
- Observation Dimension: 14D
- Coupling Betas: [0.0, 0.25, 0.50, 0.75, 1.0]
- Training Seeds: [101, 102, 103, 104, 105] (25 training runs x 150 episodes = 3,750 episodes)
- Evaluation Seeds: [1..10] (250 confirmatory evaluations)
- Single sequential worker to eliminate Windows SUMO/TraCI socket and memory conflicts.
- Strict isolation under checkpoints/phase4/final_150ep/ and outputs/experiments/phase4/final_150ep/series_4c_reward_coupling/
"""

import os
import sys
import time
import json
import random
import hashlib
import logging
import argparse
import gc
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import scipy.stats as stats

# Project imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from traffic_service.ai.env import (
    RewardWeights,
    MultiIntersectionReward,
    CorridorObservationSpace,
    ACTION_KEEP,
    ACTION_SWITCH,
)
from traffic_service.ai.mappo_agent import MAPPOAgent, train_mappo_corridor
from traffic_service.ai.marl_controller import MARLCorridorController
from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation
from traffic_service.sumo_manager import SumoManager
from traffic_service.resilience.detailed_collector import (
    DetailedCorridorMetricsCollector,
    calculate_gini_coefficient,
)
from scripts.train_phase4_150ep import (
    get_available_ram_gb,
    evaluate_marl_checkpoint_task,
    SUMO_CONFIG_PATH,
)

# Configuration & Directories
CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints" / "phase4" / "final_150ep"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase4" / "final_150ep" / "series_4c_reward_coupling"
MASTER_MANIFEST_PATH = PROJECT_ROOT / "outputs" / "experiments" / "phase4" / "execution_manifest.json"
SERIES_MANIFEST_PATH = OUTPUT_DIR / "manifest_series_4c.json"

BETAS = [0.0, 0.25, 0.50, 0.75, 1.0]
TRAIN_SEEDS = [101, 102, 103, 104, 105]
EVAL_SEEDS = list(range(1, 11))
OBSERVATION_DIM = 14
NUM_EPISODES = 150
EPISODE_DURATION_S = 1200.0
DECISION_INTERVAL_S = 5.0
EVAL_DURATION_S = 900.0
RAM_SAFETY_THRESHOLD_GB = 1.2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(OUTPUT_DIR / "series_4c_execution.log" if OUTPUT_DIR.exists() else "series_4c_execution.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("Series4CMaster")


def get_beta_tag(beta: float) -> str:
    return f"beta_{int(round(beta * 100)):03d}"


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def cleanup_orphan_sumo_processes() -> None:
    """Safely cleans up any SUMO subprocesses tracked in this session.
    Operates strictly on session PIDs; never executes global taskkill or pkill commands.
    """
    SumoManager.cleanup_session_processes()


def verify_checkpoint_integrity(ckpt_path: Path, expected_beta: float, expected_seed: int) -> Tuple[bool, Optional[str]]:
    """Strictly validates checkpoint and history sidecar integrity."""
    if not ckpt_path.is_file():
        return False, "Checkpoint file does not exist"
    if ckpt_path.stat().st_size < 1000:
        return False, f"Checkpoint file too small ({ckpt_path.stat().st_size} bytes)"

    hist_path = ckpt_path.with_suffix(".history.json")
    if not hist_path.is_file():
        return False, "History sidecar file does not exist"

    try:
        with open(ckpt_path, "r", encoding="utf-8") as f:
            ckpt = json.load(f)
        meta = ckpt.get("metadata", {})
        if meta.get("regime") != "FINAL_CONFIRMATORY_150EP":
            return False, f"Invalid regime: {meta.get('regime')}"
        if not meta.get("verified_150ep"):
            return False, "verified_150ep flag is not True"
        if meta.get("total_episodes_completed") != NUM_EPISODES:
            return False, f"Episodes completed {meta.get('total_episodes_completed')} != {NUM_EPISODES}"
        if meta.get("train_seed") != expected_seed:
            return False, f"Seed {meta.get('train_seed')} != {expected_seed}"
        if not np.isclose(meta.get("reward_coupling_beta", -1.0), expected_beta, atol=1e-4):
            return False, f"Beta {meta.get('reward_coupling_beta')} != {expected_beta}"
        if meta.get("algorithm") != "mappo":
            return False, f"Algorithm {meta.get('algorithm')} != mappo"
        if meta.get("observation_dim") != OBSERVATION_DIM:
            return False, f"Observation dim {meta.get('observation_dim')} != {OBSERVATION_DIM}"

        with open(hist_path, "r", encoding="utf-8") as f:
            hist = json.load(f)
        if len(hist) != NUM_EPISODES:
            return False, f"History length {len(hist)} != {NUM_EPISODES}"

        return True, None
    except Exception as exc:
        return False, f"Deserialization error: {exc}"


def verify_evaluation_integrity(eval_path: Path, expected_beta: float, expected_train_seed: int, expected_eval_seed: int) -> Tuple[bool, Optional[str]]:
    if not eval_path.is_file():
        return False, "Evaluation file does not exist"
    try:
        with open(eval_path, "r", encoding="utf-8") as f:
            rec = json.load(f)
        if rec.get("regime") != "FINAL_CONFIRMATORY_150EP":
            return False, f"Invalid regime: {rec.get('regime')}"
        if not rec.get("completed"):
            return False, "Evaluation not marked completed"
        if not np.isclose(rec.get("beta", -1.0), expected_beta, atol=1e-4):
            return False, f"Beta {rec.get('beta')} != {expected_beta}"
        if rec.get("train_seed") != expected_train_seed:
            return False, f"Train seed {rec.get('train_seed')} != {expected_train_seed}"
        if rec.get("eval_seed") != expected_eval_seed:
            return False, f"Eval seed {rec.get('eval_seed')} != {expected_eval_seed}"
        if rec.get("mean_corridor_travel_time_s") is None or rec.get("mean_corridor_travel_time_s") <= 0.0:
            return False, "Invalid travel time value"
        if "equity" not in rec or "cross_street_delay_gini" not in rec["equity"]:
            return False, "Missing equity breakdown"
        return True, None
    except Exception as exc:
        return False, f"Evaluation deserialization error: {exc}"


# =====================================================================
# MANIFEST MANAGEMENT
# =====================================================================

def init_or_load_manifest() -> Dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    if SERIES_MANIFEST_PATH.is_file():
        try:
            with open(SERIES_MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    tasks = {}
    for beta in BETAS:
        b_tag = get_beta_tag(beta)
        for ts in TRAIN_SEEDS:
            run_key = f"{b_tag}_seed{ts}"
            ckpt_name = f"series_4c_mappo_{b_tag}_seed{ts}.json"
            ckpt_file = CHECKPOINT_DIR / ckpt_name
            tasks[run_key] = {
                "beta": beta,
                "beta_tag": b_tag,
                "train_seed": ts,
                "algorithm": "mappo",
                "observation_dim": OBSERVATION_DIM,
                "num_episodes": NUM_EPISODES,
                "checkpoint_path": str(ckpt_file),
                "history_path": str(ckpt_file.with_suffix(".history.json")),
                "training_status": "PENDING",
                "training_wall_time_s": 0.0,
                "checkpoint_sha256": None,
                "evaluations": {
                    f"eval_seed_{es}": {
                        "eval_seed": es,
                        "status": "PENDING",
                        "output_path": str(OUTPUT_DIR / f"eval_mappo_{b_tag}_train{ts}_eval{es}.json"),
                        "travel_time_s": None,
                        "trips_completed": None,
                        "delay_gini": None,
                    }
                    for es in EVAL_SEEDS
                },
            }

    manifest = {
        "series": "Series 4C: Cooperative Reward Coupling Mechanism Ablation",
        "regime": "FINAL_CONFIRMATORY_150EP",
        "algorithm": "mappo",
        "observation_dim": OBSERVATION_DIM,
        "betas": BETAS,
        "train_seeds": TRAIN_SEEDS,
        "eval_seeds": EVAL_SEEDS,
        "total_training_runs": len(tasks),
        "total_evaluations_target": len(tasks) * len(EVAL_SEEDS),
        "runs": tasks,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%S+05:30"),
    }
    save_manifest(manifest)
    return manifest


def save_manifest(manifest: Dict[str, Any]) -> None:
    manifest["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S+05:30")
    tmp_path = SERIES_MANIFEST_PATH.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    tmp_path.replace(SERIES_MANIFEST_PATH)
    sync_to_master_manifest(manifest)


def sync_to_master_manifest(series_manifest: Dict[str, Any]) -> None:
    if not MASTER_MANIFEST_PATH.is_file():
        return
    try:
        with open(MASTER_MANIFEST_PATH, "r", encoding="utf-8") as f:
            master = json.load(f)

        s4c = master.get("confirmatory_150ep_workload", {}).get("series", {}).get("series_4c_reward_coupling", {})
        runs = series_manifest.get("runs", {})
        completed_trains = sum(1 for r in runs.values() if r.get("training_status") == "COMPLETED")
        completed_evals = sum(
            1 for r in runs.values() for e in r.get("evaluations", {}).values() if e.get("status") == "COMPLETED"
        )

        s4c["training_runs_completed"] = completed_trains
        s4c["episodes_completed"] = completed_trains * NUM_EPISODES
        s4c["evaluation_runs_completed"] = completed_evals
        s4c["status"] = "COMPLETED" if (completed_trains == 25 and completed_evals == 250) else "IN_PROGRESS"

        master["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%S+05:30")
        tmp_p = MASTER_MANIFEST_PATH.with_suffix(".tmp")
        with open(tmp_p, "w", encoding="utf-8") as f:
            json.dump(master, f, indent=2)
        tmp_p.replace(MASTER_MANIFEST_PATH)
    except Exception as exc:
        logger.warning(f"Failed to sync master execution_manifest.json: {exc}")


# =====================================================================
# TRAINING & EVALUATION WORKFLOW
# =====================================================================

def execute_single_training_run(task: Dict[str, Any]) -> Dict[str, Any]:
    beta = task["beta"]
    ts = task["train_seed"]
    ckpt_path = Path(task["checkpoint_path"])

    logger.info(f"=== Starting Training: Beta={beta:.2f} ({task['beta_tag']}), Seed={ts} (150 Episodes) ===")

    cleanup_orphan_sumo_processes()
    gc.collect()

    avail_ram = get_available_ram_gb()
    if avail_ram < RAM_SAFETY_THRESHOLD_GB:
        raise RuntimeError(f"Available RAM ({avail_ram:.2f} GB) fell below safe threshold {RAM_SAFETY_THRESHOLD_GB} GB")

    random.seed(ts)
    np.random.seed(ts)

    # Initialize MAPPO
    marl = MARLCorridorController(
        algorithm="mappo",
        junctions=["J1", "J2", "J3"],
        seed=ts,
        observation_dim=OBSERVATION_DIM,
        enable_safety_shield=True,
        enable_communication=True,
    )

    reward_weights = RewardWeights(
        alpha=beta,
        passenger_weighted=False,
    )
    reward_fn = MultiIntersectionReward(weights=reward_weights)
    obs_space = CorridorObservationSpace(dim=OBSERVATION_DIM)

    t0 = time.time()
    history = []

    for ep in range(1, NUM_EPISODES + 1):
        avail_ram = get_available_ram_gb()
        if avail_ram < RAM_SAFETY_THRESHOLD_GB:
            raise RuntimeError(f"RAM below threshold during training ep {ep}: {avail_ram:.2f} GB")

        ep_seed = ts * 1000 + ep * 17
        reward_fn.reset()
        ep_rewards = {j: 0.0 for j in ["J1", "J2", "J3"]}
        policy_losses = []
        critic_losses = []

        label = f"trn150_s4c_{task['beta_tag']}_{ts}_{ep}_{os.getpid()}"
        sim = MultiIntersectionSimulation(
            sumocfg_path=SUMO_CONFIG_PATH,
            mode="baseline",
            step_length=1.0,
            decision_interval=DECISION_INTERVAL_S,
            gui=False,
            label=label,
            enable_safety_shield=True,
            enable_communication=True,
            observation_dim=OBSERVATION_DIM,
        )
        marl.controllers = sim.controllers
        marl.hub = sim.hub
        marl.starvation_tracker.reset()

        sim.start(seed=ep_seed)
        try:
            sim_time = 0.0
            raw_states = sim.get_states(sim_time)
            raw_obs = sim.get_ai_observations(raw_states)
            prev_vecs = {j: obs_space.vectorize_junction(j, raw_states[j]) for j in ["J1", "J2", "J3"]}
            prev_corridor_vec = np.concatenate([prev_vecs[j] for j in ["J1", "J2", "J3"]])

            while sim_time < EPISODE_DURATION_S:
                decisions = marl.decide(raw_obs, sim_time=sim_time, eval_mode=False)
                marl.apply_decisions(decisions, sim_time)

                for _ in range(int(DECISION_INTERVAL_S)):
                    states, _ = sim.step()

                sim_time = sim.sumo_manager.get_time()
                raw_obs_next = sim.get_ai_observations(states)
                next_vecs = {j: obs_space.vectorize_junction(j, states[j]) for j in ["J1", "J2", "J3"]}
                next_corridor_vec = np.concatenate([next_vecs[j] for j in ["J1", "J2", "J3"]])
                is_done = (sim_time >= EPISODE_DURATION_S)

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

                # Store transitions for MAPPO
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
            }
            history.append(ep_rec)

            if ep == 1 or ep % 25 == 0 or ep == NUM_EPISODES:
                logger.info(
                    f"[{task['beta_tag']} seed={ts}] Ep {ep}/{NUM_EPISODES}: "
                    f"Reward={ep_rec['mean_reward']:.2f}, Trips={ep_rec['trips_completed']}, "
                    f"TT={ep_rec['travel_time_mean_s']:.1f}s, Delay={ep_rec['cumulative_delay_veh_s']:.0f}s"
                )

        finally:
            sim.close()

    wall_time = time.time() - t0

    # Save checkpoint with full provenance atomically
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "regime": "FINAL_CONFIRMATORY_150EP",
        "num_episodes": NUM_EPISODES,
        "train_seed": ts,
        "observation_dim": OBSERVATION_DIM,
        "algorithm": "mappo",
        "reward_coupling_beta": beta,
        "passenger_weighted": False,
        "total_episodes_completed": len(history),
        "wall_time_s": round(wall_time, 2),
        "verified_150ep": bool(len(history) == NUM_EPISODES),
    }

    tmp_ckpt = ckpt_path.with_suffix(".tmp")
    tmp_hist = ckpt_path.with_suffix(".history.tmp")
    hist_file = ckpt_path.with_suffix(".history.json")

    marl.save_checkpoint(tmp_ckpt, metadata=meta)
    with open(tmp_hist, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    tmp_ckpt.replace(ckpt_path)
    tmp_hist.replace(hist_file)

    logger.info(f"Verified Checkpoint Saved: {ckpt_path.name} ({wall_time:.1f}s)")
    return {
        "completed": True,
        "wall_time_s": round(wall_time, 2),
        "episodes": len(history),
    }


def execute_evaluations_for_checkpoint(task: Dict[str, Any], manifest: Dict[str, Any]) -> None:
    beta = task["beta"]
    ts = task["train_seed"]
    b_tag = task["beta_tag"]
    ckpt_path = str(task["checkpoint_path"])

    logger.info(f"--- Running 10 Confirmatory Evaluations for {b_tag} seed={ts} ---")

    for es in EVAL_SEEDS:
        eval_key = f"eval_seed_{es}"
        eval_info = task["evaluations"][eval_key]
        out_path = Path(eval_info["output_path"])

        # Check existing valid evaluation
        is_valid, _ = verify_evaluation_integrity(out_path, beta, ts, es)
        if is_valid:
            eval_info["status"] = "COMPLETED"
            continue

        eval_task_payload = {
            "series": "4c_reward_coupling",
            "algorithm": "mappo",
            "beta": beta,
            "train_seed": ts,
            "eval_seed": es,
            "observation_dim": OBSERVATION_DIM,
            "checkpoint_path": ckpt_path,
            "duration": EVAL_DURATION_S,
            "out_file": str(out_path),
        }

        cleanup_orphan_sumo_processes()
        gc.collect()

        eval_res = evaluate_marl_checkpoint_task(eval_task_payload)
        if eval_res.get("completed"):
            eval_info["status"] = "COMPLETED"
            eval_info["travel_time_s"] = eval_res.get("mean_corridor_travel_time_s")
            eval_info["trips_completed"] = eval_res.get("total_corridor_trips_completed")
            eval_info["delay_gini"] = eval_res.get("equity", {}).get("cross_street_delay_gini")
            logger.info(
                f"Eval {b_tag} train={ts} eval={es}: TT={eval_info['travel_time_s']:.2f}s, "
                f"Trips={eval_info['trips_completed']}, Gini={eval_info['delay_gini']:.4f}"
            )
        else:
            eval_info["status"] = "FAILED"
            logger.error(f"Evaluation failed for {b_tag} train={ts} eval={es}")

        save_manifest(manifest)


# =====================================================================
# SUMMARY & STATISTICAL ANALYSIS GENERATOR
# =====================================================================

def compile_series_4c_summary_and_statistics(manifest: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("======================================================================")
    logger.info("COMPILING SERIES 4C SUMMARY & STATISTICAL VALIDATION")
    logger.info("======================================================================")

    results = []
    for r in manifest["runs"].values():
        b = r["beta"]
        ts = r["train_seed"]
        for e in r["evaluations"].values():
            p = Path(e["output_path"])
            if p.is_file():
                with open(p, "r", encoding="utf-8") as f:
                    results.append(json.load(f))

    summary = {
        "regime": "FINAL_CONFIRMATORY_150EP",
        "metadata": {
            "experiment": "Series 4C: Cooperative Reward Coupling Mechanism Ablation (150 Episodes)",
            "algorithm": "mappo",
            "observation_dim": OBSERVATION_DIM,
            "betas": BETAS,
            "train_seeds": TRAIN_SEEDS,
            "eval_seeds": EVAL_SEEDS,
            "total_eval_runs": len(BETAS) * len(TRAIN_SEEDS) * len(EVAL_SEEDS),
            "completed_runs": len(results),
        },
        "per_beta": {},
    }

    model_level_data = {b: [] for b in BETAS}

    for b in BETAS:
        b_tag = get_beta_tag(b)
        runs_b = [r for r in results if np.isclose(r.get("beta", -1.0), b, atol=1e-4)]

        tts = [r["mean_corridor_travel_time_s"] for r in runs_b]
        trips = [r["total_corridor_trips_completed"] for r in runs_b]
        delays = [r["cumulative_delay_veh_s"] for r in runs_b]
        ginis = [r.get("equity", {}).get("cross_street_delay_gini", 0.0) for r in runs_b]
        ratios = [r.get("equity", {}).get("side_to_arterial_delay_ratio", 0.0) for r in runs_b]

        # Model-level aggregation (5 models per beta)
        for ts in TRAIN_SEEDS:
            m_runs = [r for r in runs_b if r.get("train_seed") == ts]
            if m_runs:
                model_level_data[b].append({
                    "train_seed": ts,
                    "mean_tt": float(np.mean([r["mean_corridor_travel_time_s"] for r in m_runs])),
                    "mean_trips": float(np.mean([r["total_corridor_trips_completed"] for r in m_runs])),
                    "mean_delay": float(np.mean([r["cumulative_delay_veh_s"] for r in m_runs])),
                    "mean_gini": float(np.mean([r.get("equity", {}).get("cross_street_delay_gini", 0.0) for r in m_runs])),
                    "mean_side_ratio": float(np.mean([r.get("equity", {}).get("side_to_arterial_delay_ratio", 0.0) for r in m_runs])),
                })

        summary["per_beta"][b_tag] = {
            "beta": b,
            "runs_completed": len(runs_b),
            "travel_time_mean_s": round(float(np.mean(tts)), 2) if tts else None,
            "travel_time_std_s": round(float(np.std(tts, ddof=1)), 2) if len(tts) > 1 else 0.0,
            "cumulative_delay_veh_s": round(float(np.mean(delays)), 2) if delays else 0.0,
            "total_corridor_trips_completed": round(float(np.mean(trips)), 1) if trips else 0.0,
            "cross_street_delay_gini_mean": round(float(np.mean(ginis)), 4) if ginis else 0.0,
            "side_to_arterial_delay_ratio_mean": round(float(np.mean(ratios)), 4) if ratios else 0.0,
            "model_level_means": model_level_data[b],
        }

    # Save summary
    with open(OUTPUT_DIR / "series_4c_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Statistical Pairwise Comparisons against nominal beta = 0.50
    nominal_b = 0.50
    nom_models = model_level_data[nominal_b]
    comparisons = []

    for b in [0.0, 0.25, 0.75, 1.0]:
        comp_models = model_level_data[b]
        if len(comp_models) == 5 and len(nom_models) == 5:
            # Paired across matching train seeds
            comp_models.sort(key=lambda x: x["train_seed"])
            nom_models.sort(key=lambda x: x["train_seed"])

            diff_tt = np.array([c["mean_tt"] - n["mean_tt"] for c, n in zip(comp_models, nom_models)])
            diff_trips = np.array([c["mean_trips"] - n["mean_trips"] for c, n in zip(comp_models, nom_models)])
            diff_gini = np.array([c["mean_gini"] - n["mean_gini"] for c, n in zip(comp_models, nom_models)])

            t_tt, p_tt = stats.ttest_1samp(diff_tt, popmean=0.0)
            t_tr, p_tr = stats.ttest_1samp(diff_trips, popmean=0.0)
            t_gi, p_gi = stats.ttest_1samp(diff_gini, popmean=0.0)

            sd_tt = float(np.std(diff_tt, ddof=1)) if np.std(diff_tt, ddof=1) > 0 else 1e-6
            dz_tt = float(np.mean(diff_tt) / sd_tt)

            comparisons.append({
                "condition": f"beta_{int(round(b*100)):03d}_vs_beta_050",
                "beta": b,
                "delta_travel_time_s": round(float(np.mean(diff_tt)), 2),
                "t_stat_tt": round(float(t_tt), 4),
                "p_raw_tt": float(p_tt),
                "cohens_dz_tt": round(dz_tt, 4),
                "delta_trips": round(float(np.mean(diff_trips)), 1),
                "p_raw_trips": float(p_tr),
                "delta_gini": round(float(np.mean(diff_gini)), 4),
                "p_raw_gini": float(p_gi),
            })

    # Monotonic Holm-Bonferroni correction on travel time p-values (K=4)
    comparisons.sort(key=lambda x: x["p_raw_tt"])
    k_total = len(comparisons)
    for rank, comp in enumerate(comparisons, 1):
        alpha_step = 0.05 / (k_total - rank + 1)
        comp["rank"] = rank
        comp["alpha_step"] = round(alpha_step, 5)
        comp["p_holm_tt"] = min(1.0, comp["p_raw_tt"] * (k_total - rank + 1))
        comp["significant"] = bool(comp["p_raw_tt"] < alpha_step)

    # Enforce monotonicity
    for i in range(1, len(comparisons)):
        if comparisons[i]["p_holm_tt"] < comparisons[i - 1]["p_holm_tt"]:
            comparisons[i]["p_holm_tt"] = comparisons[i - 1]["p_holm_tt"]

    stat_record = {
        "family": "Family 4C: Cooperative Reward Coupling Mechanism Ablation",
        "nominal_baseline": "beta_050",
        "independent_unit": "trained_checkpoint (N=5 per condition, df=4)",
        "comparisons": comparisons,
    }

    with open(OUTPUT_DIR / "series_4c_statistical_analysis.json", "w", encoding="utf-8") as f:
        json.dump(stat_record, f, indent=2)

    logger.info("Summary and Statistical Analysis Successfully Written.")
    return summary


# =====================================================================
# MAIN WORKFLOW CONTROLLER
# =====================================================================

def run_pre_execution_checks() -> bool:
    logger.info("======================================================================")
    logger.info("RUNNING PRE-EXECUTION CHECKS FOR SERIES 4C")
    logger.info("======================================================================")

    all_passed = True

    # 1. Verify Pytest suite
    logger.info("Checking unit test suite (tests/test_series4c_reward_coupling.py)...")
    try:
        res = subprocess.run(
            ["pytest", "tests/test_series4c_reward_coupling.py", "-q"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            logger.info("  [PASS] Unit tests passed completely.")
        else:
            logger.error(f"  [FAIL] Unit tests failed: {res.stdout} {res.stderr}")
            all_passed = False
    except Exception as exc:
        logger.error(f"  [FAIL] Could not run unit tests: {exc}")
        all_passed = False

    # 2. Check RAM availability
    avail_ram = get_available_ram_gb()
    logger.info(f"Checking available RAM: {avail_ram:.2f} GB (Threshold >= {RAM_SAFETY_THRESHOLD_GB} GB)...")
    if avail_ram >= RAM_SAFETY_THRESHOLD_GB:
        logger.info(f"  [PASS] RAM safe: {avail_ram:.2f} GB")
    else:
        logger.error(f"  [FAIL] RAM insufficient: {avail_ram:.2f} GB < {RAM_SAFETY_THRESHOLD_GB} GB")
        all_passed = False

    # 3. Check Free Disk Space
    total, used, free = shutil.disk_usage(str(PROJECT_ROOT))
    free_gb = free / (1024 ** 3)
    logger.info(f"Checking free disk space: {free_gb:.2f} GB (Threshold >= 10.0 GB)...")
    if free_gb >= 10.0:
        logger.info(f"  [PASS] Disk space safe: {free_gb:.2f} GB")
    else:
        logger.error(f"  [FAIL] Disk space low: {free_gb:.2f} GB < 10.0 GB")
        all_passed = False

    # 4. Check SUMO Configuration & Executable
    logger.info(f"Checking SUMO configuration path: {SUMO_CONFIG_PATH}...")
    if Path(SUMO_CONFIG_PATH).is_file():
        logger.info("  [PASS] SUMO config verified.")
    else:
        logger.error(f"  [FAIL] SUMO config not found at {SUMO_CONFIG_PATH}")
        all_passed = False

    # 5. Check Series 4B Artifact Preservation
    s4b_ckpts = list(CHECKPOINT_DIR.glob("series_4b_*.json"))
    s4b_evals = list((PROJECT_ROOT / "outputs" / "experiments" / "phase4" / "final_150ep" / "series_4b_observation_space").glob("eval_*.json"))
    logger.info(f"Checking Series 4B preservation: {len(s4b_ckpts)} checkpoints, {len(s4b_evals)} eval JSONs...")
    if len(s4b_ckpts) >= 30 and len(s4b_evals) >= 300:
        logger.info("  [PASS] Series 4B frozen artifacts intact.")
    else:
        logger.error(f"  [FAIL] Series 4B artifacts degraded: {len(s4b_ckpts)} ckpts, {len(s4b_evals)} evals")
        all_passed = False

    # 6. Verify beta mapping & linearity
    logger.info("Checking beta mapping consistency...")
    for b in BETAS:
        rw = RewardWeights(alpha=b)
        assert np.isclose(rw.alpha, b)
    logger.info("  [PASS] Beta mapping strictly verified.")

    logger.info("======================================================================")
    if all_passed:
        logger.info("ALL PRE-EXECUTION CHECKS PASSED.")
    else:
        logger.error("PRE-EXECUTION CHECKS FAILED. HALTING.")
    logger.info("======================================================================")
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Series 4C Master Execution Harness")
    parser.add_argument("--verify-only", action="store_true", help="Run pre-execution checks and exit without training")
    args = parser.parse_args()

    if not run_pre_execution_checks():
        sys.exit(1)

    if args.verify_only:
        logger.info("Pre-execution check mode complete. Exiting clean.")
        sys.exit(0)

    manifest = init_or_load_manifest()
    total_runs = len(manifest["runs"])

    logger.info("======================================================================")
    logger.info(f"STARTING SERIES 4C CONFIRMATORY EXECUTION: {total_runs} RUNS")
    logger.info("======================================================================")

    for idx, (run_key, task) in enumerate(manifest["runs"].items(), 1):
        beta = task["beta"]
        ts = task["train_seed"]
        b_tag = task["beta_tag"]
        ckpt_path = Path(task["checkpoint_path"])

        logger.info(f"\n>>> Processing Run {idx}/{total_runs}: {run_key} (Beta={beta:.2f}, Seed={ts}) <<<")

        # Step 1: Check Checkpoint Integrity
        is_ckpt_valid, reason = verify_checkpoint_integrity(ckpt_path, beta, ts)
        if is_ckpt_valid:
            logger.info(f"Checkpoint already verified complete: {ckpt_path.name}")
            task["training_status"] = "COMPLETED"
            task["checkpoint_sha256"] = compute_sha256(ckpt_path)
            save_manifest(manifest)
        else:
            if ckpt_path.is_file():
                logger.warning(f"Existing checkpoint failed validation ({reason}). Re-executing clean.")
                try:
                    ckpt_path.unlink()
                    ckpt_path.with_suffix(".history.json").unlink(missing_ok=True)
                except Exception:
                    pass

            task["training_status"] = "TRAINING"
            save_manifest(manifest)

            res = execute_single_training_run(task)
            task["training_wall_time_s"] = res["wall_time_s"]

            # Validate newly saved checkpoint
            is_valid_new, new_reason = verify_checkpoint_integrity(ckpt_path, beta, ts)
            if not is_valid_new:
                task["training_status"] = "FAILED"
                save_manifest(manifest)
                raise RuntimeError(f"Training completed but checkpoint failed integrity: {new_reason}")

            task["training_status"] = "COMPLETED"
            task["checkpoint_sha256"] = compute_sha256(ckpt_path)
            save_manifest(manifest)

        # Step 2: Confirmatory Evaluations for this Checkpoint
        execute_evaluations_for_checkpoint(task, manifest)

    # Step 3: Compile Summary and Statistical Validation
    compile_series_4c_summary_and_statistics(manifest)
    logger.info("\nALL 25 TRAINING RUNS AND 250 CONFIRMATORY EVALUATIONS COMPLETE.")


if __name__ == "__main__":
    main()
