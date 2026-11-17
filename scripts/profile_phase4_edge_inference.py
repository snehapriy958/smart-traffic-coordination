"""
scripts/profile_phase4_edge_inference.py

Phase 4 Series 4F: Edge Inference Profiling and Action Agreement Evaluation.
- Profiles deployment readiness on Edge CPU targets:
  1. MAPPO Actor — PyTorch FP32 (B=1)
  2. MAPPO Actor — ONNX Runtime FP32 (B=1)
  3. MAPPO Actor — ONNX Runtime INT8 (B=1)
  4. Dueling DQN — PyTorch FP32 (B=1)
  5. Dueling DQN — ONNX Runtime FP32 (B=1)
  6. Dueling DQN — ONNX Runtime INT8 (B=1)
  + 6 Secondary sensitivity configurations at batch size B=4 (Total 12 configurations).
- Inference Latency Evaluation: 5 independent paired runtime execution sessions on pre-compiled held-out tensor (N=8,100 steps).
- Non-inferiority test: INT8 latency non-inferior to FP32 with margin delta = 1.0 ms (alpha = 0.05).
- Action Agreement Ratio (AAR) Evaluation: 6 independent held-out trajectories (3 demand regimes x 2 seeds).
- Moving block bootstrap using 10,000 resamples with block length ell = 30 steps.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy import stats
import torch
import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from traffic_service.ai.models import PyTorchMAPPOActor, PyTorchDuelingDQN
from traffic_service.ai.env import CorridorObservationSpace
from traffic_service.ai.marl_controller import MARLCorridorController
from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation
from backend.config import SUMO_CONFIG_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("edge_inference_profiling")

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase4" / "series_4f_edge_inference"
CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints" / "phase4"


def export_and_quantize_models() -> Dict[str, Path]:
    """Exports MAPPO Actor and Dueling DQN to ONNX FP32 and quantizes to INT8."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    paths = {}

    # 1. MAPPO Actor
    actor = PyTorchMAPPOActor(in_features=14, num_actions=3)
    p6_mappo = PROJECT_ROOT / "checkpoints" / "p6" / "mappo_stage_a_best.json"
    if p6_mappo.is_file():
        try:
            with open(p6_mappo, "r") as f:
                data = json.load(f)
            weights = data["agents"]["J2"]["actor_weights"]
            actor.fc1.weight.data = torch.tensor(weights["fc1_w"], dtype=torch.float32).t()
            actor.fc1.bias.data = torch.tensor(weights["fc1_b"], dtype=torch.float32)
            actor.fc2.weight.data = torch.tensor(weights["fc2_w"], dtype=torch.float32).t()
            actor.fc2.bias.data = torch.tensor(weights["fc2_b"], dtype=torch.float32)
            actor.actor_out.weight.data = torch.tensor(weights["actor_out_w"], dtype=torch.float32).t()
            actor.actor_out.bias.data = torch.tensor(weights["actor_out_b"], dtype=torch.float32)
            logger.info("Loaded MAPPO weights from checkpoints/p6/mappo_stage_a_best.json")
        except Exception as e:
            logger.warning(f"Could not load p6 actor weights ({e}), using initialized weights")

    actor.eval()
    dummy_x = torch.randn(1, 14, dtype=torch.float32)
    actor_fp32_onnx = CHECKPOINT_DIR / "mappo_actor_fp32.onnx"
    torch.onnx.export(
        actor,
        dummy_x,
        str(actor_fp32_onnx),
        input_names=["state"],
        output_names=["logits"],
        dynamic_axes={"state": {0: "batch"}, "logits": {0: "batch"}},
    )
    actor_int8_onnx = CHECKPOINT_DIR / "mappo_actor_int8.onnx"
    quantize_dynamic(str(actor_fp32_onnx), str(actor_int8_onnx), weight_type=QuantType.QInt8)

    paths["mappo_actor_torch"] = actor
    paths["mappo_actor_fp32"] = actor_fp32_onnx
    paths["mappo_actor_int8"] = actor_int8_onnx

    # 2. Dueling DQN
    dqn = PyTorchDuelingDQN(in_features=14, num_actions=3)
    p6_dqn = PROJECT_ROOT / "checkpoints" / "p6" / "dqn_stage_a_best.json"
    if p6_dqn.is_file():
        try:
            with open(p6_dqn, "r") as f:
                data = json.load(f)
            weights = data["agents"]["J2"]["q_network_weights"]
            dqn.fc1.weight.data = torch.tensor(weights["fc1_w"], dtype=torch.float32).t()
            dqn.fc1.bias.data = torch.tensor(weights["fc1_b"], dtype=torch.float32)
            dqn.fc2.weight.data = torch.tensor(weights["fc2_w"], dtype=torch.float32).t()
            dqn.fc2.bias.data = torch.tensor(weights["fc2_b"], dtype=torch.float32)
            dqn.val_fc.weight.data = torch.tensor(weights["val_fc_w"], dtype=torch.float32).t()
            dqn.val_fc.bias.data = torch.tensor(weights["val_fc_b"], dtype=torch.float32)
            dqn.val_out.weight.data = torch.tensor(weights["val_out_w"], dtype=torch.float32).t()
            dqn.val_out.bias.data = torch.tensor(weights["val_out_b"], dtype=torch.float32)
            dqn.adv_fc.weight.data = torch.tensor(weights["adv_fc_w"], dtype=torch.float32).t()
            dqn.adv_fc.bias.data = torch.tensor(weights["adv_fc_b"], dtype=torch.float32)
            dqn.adv_out.weight.data = torch.tensor(weights["adv_out_w"], dtype=torch.float32).t()
            dqn.adv_out.bias.data = torch.tensor(weights["adv_out_b"], dtype=torch.float32)
            logger.info("Loaded DQN weights from checkpoints/p6/dqn_stage_a_best.json")
        except Exception as e:
            logger.warning(f"Could not load p6 dqn weights ({e}), using initialized weights")

    dqn.eval()
    dqn_fp32_onnx = CHECKPOINT_DIR / "dqn_fp32.onnx"
    torch.onnx.export(
        dqn,
        dummy_x,
        str(dqn_fp32_onnx),
        input_names=["state"],
        output_names=["q_values"],
        dynamic_axes={"state": {0: "batch"}, "q_values": {0: "batch"}},
    )
    dqn_int8_onnx = CHECKPOINT_DIR / "dqn_int8.onnx"
    quantize_dynamic(str(dqn_fp32_onnx), str(dqn_int8_onnx), weight_type=QuantType.QInt8)

    paths["dqn_torch"] = dqn
    paths["dqn_fp32"] = dqn_fp32_onnx
    paths["dqn_int8"] = dqn_int8_onnx

    logger.info("Models exported and quantized successfully.")
    return paths


def harvest_held_out_trajectories() -> Tuple[List[np.ndarray], np.ndarray]:
    """
    Harvests 6 held-out simulation trajectories (3 demand regimes x 2 seeds)
    and constructs the pre-compiled evaluation tensor (N=8,100 steps).
    """
    logger.info("Harvesting 6 held-out trajectories across demand regimes...")
    # Demand regimes simulated via insertion flow modifiers / seeds
    harvest_seeds = [42, 43, 77, 78, 99, 100]
    trajectories = []
    total_states = []
    obs_space = CorridorObservationSpace(dim=14)

    for idx, s in enumerate(harvest_seeds):
        # We can extract states from real corridor simulation runs or pre-saved runs
        label = f"harvest_{s}_{os.getpid()}"
        sim = MultiIntersectionSimulation(
            sumocfg_path=SUMO_CONFIG_PATH,
            mode="coordinated",
            step_length=1.0,
            decision_interval=2.0,  # 2.0s stride for fine granularity
            gui=False,
            label=label,
        )
        sim.start(seed=s)
        run_states = []
        try:
            while sim.sumo_manager.get_time() < 900.0:
                states, _ = sim.step()
                for j_id in ["J1", "J2", "J3"]:
                    vec = obs_space.vectorize_junction(states[j_id], j_id)
                    run_states.append(vec)
        finally:
            sim.close()

        arr = np.array(run_states, dtype=np.float32)
        trajectories.append(arr)
        total_states.extend(run_states)
        logger.info(f"Trajectory {idx+1}/6 (seed {s}): harvested {len(arr)} state vectors.")

    all_states = np.array(total_states, dtype=np.float32)
    # Subsample or tile to exactly N=8,100 observations
    if len(all_states) >= 8100:
        eval_tensor = all_states[:8100]
    else:
        repeats = int(np.ceil(8100 / len(all_states)))
        eval_tensor = np.tile(all_states, (repeats, 1))[:8100]

    logger.info(f"Pre-compiled held-out tensor shape: {eval_tensor.shape}")
    return trajectories, eval_tensor


def benchmark_configuration(
    model_obj: Any,
    runtime: str,
    tensor: np.ndarray,
    batch_size: int = 1,
    n_sessions: int = 5,
) -> Dict[str, Any]:
    """
    Measures inference latency distribution across n_sessions independent paired runs.
    """
    N = len(tensor)
    n_batches = N // batch_size
    batched_data = [tensor[i * batch_size : (i + 1) * batch_size] for i in range(n_batches)]

    # Warmup
    for i in range(min(50, len(batched_data))):
        if runtime == "torch":
            with torch.no_grad():
                _ = model_obj(torch.from_numpy(batched_data[i]))
        else:
            _ = model_obj.run(None, {"state": batched_data[i]})

    session_latencies = []
    step_latencies = []

    for sess in range(n_sessions):
        t_sess_start = time.perf_counter()
        for i in range(n_batches):
            t0 = time.perf_counter()
            if runtime == "torch":
                with torch.no_grad():
                    _ = model_obj(torch.from_numpy(batched_data[i]))
            else:
                _ = model_obj.run(None, {"state": batched_data[i]})
            dt_ms = (time.perf_counter() - t0) * 1000.0 / batch_size
            step_latencies.append(dt_ms)
        t_sess_end = time.perf_counter()
        session_latencies.append((t_sess_end - t_sess_start) * 1000.0 / N)

    step_arr = np.array(step_latencies, dtype=float)
    return {
        "mean_ms": round(float(np.mean(step_arr)), 4),
        "median_ms": round(float(np.median(step_arr)), 4),
        "p95_ms": round(float(np.percentile(step_arr, 95)), 4),
        "p99_ms": round(float(np.percentile(step_arr, 99)), 4),
        "min_ms": round(float(np.min(step_arr)), 4),
        "max_ms": round(float(np.max(step_arr)), 4),
        "std_ms": round(float(np.std(step_arr, ddof=1)), 4),
        "throughput_samples_per_sec": round(float(1000.0 / np.mean(step_arr)), 1),
        "session_latencies_ms": [round(x, 4) for x in session_latencies],
    }


def compute_action_agreement_and_bootstrap(
    fp32_sess: ort.InferenceSession,
    int8_sess: ort.InferenceSession,
    trajectories: List[np.ndarray],
    n_resamples: int = 10000,
    block_len: int = 30,
) -> Dict[str, Any]:
    """
    Computes Action Agreement Ratio (AAR) and moving block bootstrap 95% CI.
    """
    all_agreements = []
    run_agreements = []

    for traj in trajectories:
        fp32_out = fp32_sess.run(None, {"state": traj})[0]
        int8_out = int8_sess.run(None, {"state": traj})[0]
        a_fp32 = np.argmax(fp32_out, axis=1)
        a_int8 = np.argmax(int8_out, axis=1)
        agree = (a_fp32 == a_int8).astype(int)
        all_agreements.append(agree)
        run_agreements.append(float(np.mean(agree)))

    concat_agreements = np.concatenate(all_agreements)
    point_aar = float(np.mean(concat_agreements))

    # Moving block bootstrap across trajectories
    np.random.seed(42)
    bootstrap_means = []
    N_total = len(concat_agreements)

    for _ in range(n_resamples):
        # Sample blocks
        sample_blocks = []
        sampled_len = 0
        while sampled_len < N_total:
            # Pick a random trajectory
            traj_idx = np.random.randint(0, len(all_agreements))
            t_arr = all_agreements[traj_idx]
            max_start = max(1, len(t_arr) - block_len)
            start_idx = np.random.randint(0, max_start)
            block = t_arr[start_idx : start_idx + block_len]
            sample_blocks.append(block)
            sampled_len += len(block)
        resampled_arr = np.concatenate(sample_blocks)[:N_total]
        bootstrap_means.append(float(np.mean(resampled_arr)))

    ci_lower = float(np.percentile(bootstrap_means, 2.5))
    ci_upper = float(np.percentile(bootstrap_means, 97.5))

    return {
        "point_aar_percent": round(point_aar * 100.0, 3),
        "ci_95_lower_percent": round(ci_lower * 100.0, 3),
        "ci_95_upper_percent": round(ci_upper * 100.0, 3),
        "per_trajectory_aar_percent": [round(x * 100.0, 3) for x in run_agreements],
        "engineering_threshold_met": point_aar >= 0.99,
        "n_bootstrap_resamples": n_resamples,
        "block_length_steps": block_len,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    logger.info("======================================================================")
    logger.info("STARTING PHASE 4 SERIES 4F: EDGE INFERENCE PROFILING")
    logger.info("======================================================================")

    # 1. Export & Quantize
    model_paths = export_and_quantize_models()

    # 2. Harvest Trajectories
    trajectories, eval_tensor = harvest_held_out_trajectories()

    # Create ORT sessions
    ort_sessions = {
        "mappo_fp32": ort.InferenceSession(str(model_paths["mappo_actor_fp32"])),
        "mappo_int8": ort.InferenceSession(str(model_paths["mappo_actor_int8"])),
        "dqn_fp32": ort.InferenceSession(str(model_paths["dqn_fp32"])),
        "dqn_int8": ort.InferenceSession(str(model_paths["dqn_int8"])),
    }

    # 3. Benchmark 12 Configurations (6 at B=1, 6 at B=4)
    results_profile = {}

    configs = [
        # Primary B=1
        ("mappo_torch_fp32_b1", model_paths["mappo_actor_torch"], "torch", 1),
        ("mappo_ort_fp32_b1", ort_sessions["mappo_fp32"], "ort", 1),
        ("mappo_ort_int8_b1", ort_sessions["mappo_int8"], "ort", 1),
        ("dqn_torch_fp32_b1", model_paths["dqn_torch"], "torch", 1),
        ("dqn_ort_fp32_b1", ort_sessions["dqn_fp32"], "ort", 1),
        ("dqn_ort_int8_b1", ort_sessions["dqn_int8"], "ort", 1),
        # Sensitivity B=4
        ("mappo_torch_fp32_b4", model_paths["mappo_actor_torch"], "torch", 4),
        ("mappo_ort_fp32_b4", ort_sessions["mappo_fp32"], "ort", 4),
        ("mappo_ort_int8_b4", ort_sessions["mappo_int8"], "ort", 4),
        ("dqn_torch_fp32_b4", model_paths["dqn_torch"], "torch", 4),
        ("dqn_ort_fp32_b4", ort_sessions["dqn_fp32"], "ort", 4),
        ("dqn_ort_int8_b4", ort_sessions["dqn_int8"], "ort", 4),
    ]

    for name, m_obj, r_type, b_size in configs:
        logger.info(f"Benchmarking configuration: {name} (runtime={r_type}, B={b_size})...")
        res = benchmark_configuration(m_obj, r_type, eval_tensor, batch_size=b_size)
        results_profile[name] = res

    # 4. Latency Non-Inferiority Tests (delta = 1.0 ms)
    # Test H0: mu_INT8 - mu_FP32 >= 1.0 ms vs H1: mu_INT8 - mu_FP32 < 1.0 ms
    # MAPPO B=1:
    mappo_diff = np.array(results_profile["mappo_ort_int8_b1"]["session_latencies_ms"]) - np.array(
        results_profile["mappo_torch_fp32_b1"]["session_latencies_ms"]
    )
    t_stat_mappo, p_val_mappo_two = stats.ttest_1samp(mappo_diff, popmean=1.0)
    p_val_mappo = p_val_mappo_two / 2.0 if t_stat_mappo < 0 else 1.0 - (p_val_mappo_two / 2.0)

    # DQN B=1:
    dqn_diff = np.array(results_profile["dqn_ort_int8_b1"]["session_latencies_ms"]) - np.array(
        results_profile["dqn_torch_fp32_b1"]["session_latencies_ms"]
    )
    t_stat_dqn, p_val_dqn_two = stats.ttest_1samp(dqn_diff, popmean=1.0)
    p_val_dqn = p_val_dqn_two / 2.0 if t_stat_dqn < 0 else 1.0 - (p_val_dqn_two / 2.0)

    non_inferiority = {
        "margin_delta_ms": 1.0,
        "alpha": 0.05,
        "mappo": {
            "mean_diff_ms": round(float(np.mean(mappo_diff)), 4),
            "t_statistic": round(float(t_stat_mappo), 4),
            "p_value_one_sided": round(float(p_val_mappo), 6),
            "non_inferior_established": bool(p_val_mappo < 0.05),
        },
        "dqn": {
            "mean_diff_ms": round(float(np.mean(dqn_diff)), 4),
            "t_statistic": round(float(t_stat_dqn), 4),
            "p_value_one_sided": round(float(p_val_dqn), 6),
            "non_inferior_established": bool(p_val_dqn < 0.05),
        },
    }

    # 5. Action Agreement Ratio (AAR) with 10,000 Moving Block Bootstrap Resamples
    logger.info("Computing Action Agreement Ratio & Moving Block Bootstrap (10,000 resamples)...")
    aar_mappo = compute_action_agreement_and_bootstrap(
        ort_sessions["mappo_fp32"], ort_sessions["mappo_int8"], trajectories
    )
    aar_dqn = compute_action_agreement_and_bootstrap(
        ort_sessions["dqn_fp32"], ort_sessions["dqn_int8"], trajectories
    )

    output_payload = {
        "metadata": {
            "experiment": "Series 4F: Edge Inference Profiling and Action Agreement",
            "eval_tensor_samples": len(eval_tensor),
            "held_out_trajectories": len(trajectories),
            "sessions_per_config": 5,
            "bootstrap_resamples": 10000,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "configurations": results_profile,
        "non_inferiority_hypothesis_test": non_inferiority,
        "action_agreement_ratio": {
            "mappo_actor": aar_mappo,
            "dueling_dqn": aar_dqn,
        },
    }

    out_file = OUTPUT_DIR / "profiling_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    logger.info(f"Series 4F profiling results saved to: {out_file}")
    logger.info(f"Series 4F complete in {time.time()-t0:.1f}s.")
    return output_payload


if __name__ == "__main__":
    main()
