"""
scripts/evaluate_marl.py

Multi-Controller Comparative Evaluation Benchmark:
1. Fixed-Time Baseline (Uncoordinated static phase durations)
2. Coordinated Adaptive (Queue pressure + inflow anticipation + emergency green wave)
3. MARL Double-DQN (Multi-Agent Deep Q-Network with communication exchange)
4. MARL PPO (Multi-Agent Proximal Policy Optimization with GAE advantage estimation)

Runs genuine multi-seed SUMO simulations (no preset improvement factors).
Saves comprehensive summary to outputs/corridor/marl_multi_controller_summary.csv
and detailed per-seed outputs to outputs/corridor/marl_multi_seed_detailed.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path
import statistics
import sys
import time
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate_marl")

SUMO_CONFIG = PROJECT_ROOT / "sumo" / "silk_board" / "silk_board.sumocfg"
CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "corridor"
SUMMARY_FILE = OUTPUT_DIR / "marl_multi_controller_summary.csv"
FULL_STATS_FILE = OUTPUT_DIR / "marl_multi_controller_full_stats.csv"
DETAILED_FILE = OUTPUT_DIR / "marl_multi_seed_detailed.json"

METRIC_DEFINITIONS = [
    ("mean_corridor_travel_time_s", "Corridor Travel Time (s)", False),
    ("mean_corridor_speed_kmh", "Average Speed (km/h)", True),
    ("total_corridor_waiting_time_s", "Total Waiting Time (s)", False),
    ("mean_corridor_queue", "Mean Corridor Queue (veh)", False),
    ("max_corridor_queue", "Max Corridor Queue (veh)", False),
    ("total_corridor_trips_completed", "Completed Corridor Trips", True),
    ("total_co2_kg", "Total CO2 Emissions (kg)", False),
    ("total_fuel_liters", "Total Fuel Consumed (L)", False),
    ("emergency_traversal_duration_s", "Ambulance Traversal Duration (s)", False),
]


def run_single_simulation(mode: str, seed: int, duration: int = 600) -> Dict[str, Any]:
    """Runs a single simulation episode in the given mode with the specified seed."""
    logger.info(f"--> Simulating {mode.upper()} [Seed {seed}] for {duration}s...")
    sim = MultiIntersectionSimulation(
        sumocfg_path=SUMO_CONFIG,
        mode=mode,
        step_length=1.0,
        decision_interval=5.0,
        enable_emergency=True,
    )
    summary = sim.run_full_simulation(duration_seconds=duration, seed=seed)

    # Save run step metrics if output dir available
    mode_dir = OUTPUT_DIR / mode
    mode_dir.mkdir(parents=True, exist_ok=True)
    sim.metrics_collector.export_csv(mode_dir / f"seed_{seed}.csv")

    return {
        "seed": seed,
        "mode": mode,
        "mean_corridor_travel_time_s": round(summary.mean_corridor_travel_time_s, 2),
        "mean_corridor_speed_kmh": round(summary.mean_corridor_speed_kmh, 2),
        "total_corridor_waiting_time_s": round(summary.total_corridor_waiting_time_s, 2),
        "mean_corridor_queue": round(summary.mean_corridor_queue, 2),
        "max_corridor_queue": int(summary.max_corridor_queue),
        "total_corridor_trips_completed": int(summary.total_corridor_trips_completed),
        "total_co2_kg": round(summary.total_co2_kg, 2),
        "total_fuel_liters": round(summary.total_fuel_liters, 2),
        "emergency_traversal_duration_s": round(summary.emergency_traversal_duration_s, 2),
        "j1_mean_queue": round(summary.j1_mean_queue, 2),
        "j2_mean_queue": round(summary.j2_mean_queue, 2),
        "j3_mean_queue": round(summary.j3_mean_queue, 2),
    }


def compute_metric_stats(values: List[float]) -> Tuple[float, float]:
    """Computes sample mean and standard deviation."""
    if not values:
        return 0.0, 0.0
    m = statistics.mean(values)
    s = statistics.stdev(values) if len(values) > 1 else 0.0
    return round(m, 2), round(s, 2)


def calculate_improvement_pct(baseline: float, current: float, higher_is_better: bool = False) -> float:
    """Calculates percentage improvement vs baseline."""
    if baseline == 0.0:
        return 0.0
    if higher_is_better:
        return round(((current - baseline) / baseline) * 100.0, 1)
    return round(((baseline - current) / baseline) * 100.0, 1)


def evaluate_all_controllers(
    seeds: List[int] = [1, 2, 3, 4, 5],
    duration: int = 600,
    controllers: List[str] = ["baseline", "coordinated", "marl_dqn", "marl_ppo"],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Executes multi-seed evaluation for all specified controllers.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_runs: Dict[str, List[Dict[str, Any]]] = {c: [] for c in controllers}

    start_time = time.time()
    for mode in controllers:
        logger.info("=" * 80)
        logger.info(f"EVALUATING CONTROLLER: {mode.upper()}")
        logger.info("=" * 80)
        for seed in seeds:
            res = run_single_simulation(mode=mode, seed=seed, duration=duration)
            all_runs[mode].append(res)

    total_eval_time = round(time.time() - start_time, 2)
    logger.info(f"All simulations completed in {total_eval_time}s.")

    # Compute statistics across seeds
    stats_by_controller: Dict[str, Dict[str, Tuple[float, float]]] = {}
    for mode in controllers:
        stats_by_controller[mode] = {}
        for metric_key, _, _ in METRIC_DEFINITIONS:
            vals = [r[metric_key] for r in all_runs[mode]]
            stats_by_controller[mode][metric_key] = compute_metric_stats(vals)

    # Build CSV summary rows
    summary_rows = []
    full_stats_rows = []

    has_dqn = "marl_dqn" in controllers
    has_ppo = "marl_ppo" in controllers

    for metric_key, label, higher_is_better in METRIC_DEFINITIONS:
        b_mean, b_std = stats_by_controller["baseline"][metric_key]
        c_mean, c_std = stats_by_controller["coordinated"][metric_key]
        dqn_mean, dqn_std = stats_by_controller["marl_dqn"][metric_key] if has_dqn else (None, None)
        ppo_mean, ppo_std = stats_by_controller["marl_ppo"][metric_key] if has_ppo else (None, None)

        # Handle zero-completed trips: a travel time of 0.0 means 0 trips finished, not 0s duration
        dqn_trips_completed = stats_by_controller["marl_dqn"]["total_corridor_trips_completed"][0] if has_dqn else 0
        ppo_trips_completed = stats_by_controller["marl_ppo"]["total_corridor_trips_completed"][0] if has_ppo else 0

        dqn_val_clean = dqn_mean
        if metric_key in ("mean_corridor_travel_time_s", "emergency_traversal_duration_s") and dqn_mean == 0.0:
            dqn_val_clean = None

        ppo_val_clean = ppo_mean
        if metric_key in ("mean_corridor_travel_time_s", "emergency_traversal_duration_s") and ppo_mean == 0.0:
            ppo_val_clean = None

        c_gain = calculate_improvement_pct(b_mean, c_mean, higher_is_better)
        dqn_gain = calculate_improvement_pct(b_mean, dqn_val_clean, higher_is_better) if dqn_val_clean is not None else ""
        ppo_gain = calculate_improvement_pct(b_mean, ppo_val_clean, higher_is_better) if ppo_val_clean is not None else ""

        summary_rows.append({
            "metric": metric_key,
            "label": label,
            "baseline": b_mean,
            "coordinated": c_mean,
            "marl_dqn": dqn_val_clean if dqn_val_clean is not None else "",
            "marl_ppo": ppo_val_clean if ppo_val_clean is not None else "",
            "coord_vs_base_pct": c_gain,
            "dqn_vs_base_pct": dqn_gain,
            "ppo_vs_base_pct": ppo_gain,
            "status_marl": "Trained & Evaluated (SUMO 1.28.0)",
        })

        full_stats_rows.append({
            "metric": metric_key,
            "label": label,
            "baseline_mean": b_mean,
            "baseline_std": b_std,
            "coordinated_mean": c_mean,
            "coordinated_std": c_std,
            "dqn_mean": dqn_mean if dqn_mean is not None else "",
            "dqn_std": dqn_std if dqn_std is not None else "",
            "ppo_mean": ppo_mean if ppo_mean is not None else "",
            "ppo_std": ppo_std if ppo_std is not None else "",
            "coord_vs_base_pct": c_gain,
            "dqn_vs_base_pct": dqn_gain,
            "ppo_vs_base_pct": ppo_gain,
        })

    # Save Summary CSV
    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    # Save Full Stats CSV
    with open(FULL_STATS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(full_stats_rows[0].keys()))
        writer.writeheader()
        writer.writerows(full_stats_rows)

    # Save Detailed JSON
    detailed_payload = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seeds": seeds,
        "duration_s": duration,
        "total_eval_wall_clock_s": total_eval_time,
        "summary": summary_rows,
        "full_stats": full_stats_rows,
        "runs": all_runs,
    }
    with open(DETAILED_FILE, "w", encoding="utf-8") as f:
        json.dump(detailed_payload, f, indent=2)

    return summary_rows, detailed_payload


def print_comparison_table(rows: List[Dict[str, Any]]) -> None:
    """Prints a terminal-friendly comparison table."""
    print("\n" + "=" * 115)
    print("EMPIRICAL MULTI-CONTROLLER BENCHMARK RESULTS (5-SEED SUMO SIMULATION)")
    print("Corridor: Bengaluru Hosur Road (J1 Central Silk Board -> J2 Madiwala -> J3 St. Johns)")
    print("=" * 115)

    header = f"{'METRIC':<33} | {'BASELINE':<10} | {'COORDINATED':<12} | {'MARL DQN':<10} | {'MARL PPO':<10} | {'DQN GAIN':<10} | {'PPO GAIN':<10}"
    print(header)
    print("-" * 115)

    for r in rows:
        dqn_val = f"{r['marl_dqn']:.2f}" if isinstance(r['marl_dqn'], (int, float)) else str(r['marl_dqn'])
        ppo_val = f"{r['marl_ppo']:.2f}" if isinstance(r['marl_ppo'], (int, float)) else str(r['marl_ppo'])
        dqn_g = (
            f"+{r['dqn_vs_base_pct']}%"
            if isinstance(r['dqn_vs_base_pct'], (int, float)) and r['dqn_vs_base_pct'] >= 0
            else f"{r['dqn_vs_base_pct']}%" if isinstance(r['dqn_vs_base_pct'], (int, float)) else ""
        )
        ppo_g = (
            f"+{r['ppo_vs_base_pct']}%"
            if isinstance(r['ppo_vs_base_pct'], (int, float)) and r['ppo_vs_base_pct'] >= 0
            else f"{r['ppo_vs_base_pct']}%" if isinstance(r['ppo_vs_base_pct'], (int, float)) else ""
        )
        
        print(
            f"{r['label']:<33} | "
            f"{r['baseline']:>10.2f} | "
            f"{r['coordinated']:>12.2f} | "
            f"{dqn_val:>10} | "
            f"{ppo_val:>10} | "
            f"{dqn_g:>10} | "
            f"{ppo_g:>10}"
        )

    print("=" * 115)
    print(f"Results written to: {SUMMARY_FILE}")
    print(f"Detailed seed runs: {DETAILED_FILE}\n")


def recompute_from_cache(json_file: Path = DETAILED_FILE) -> List[Dict[str, Any]]:
    """Recomputes summary statistics and CSV files from an existing detailed JSON run log."""
    if not json_file.is_file():
        raise FileNotFoundError(f"Detailed runs cache not found: {json_file}")

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_runs = data.get("runs", {})
    controllers = list(all_runs.keys())

    stats_by_controller: Dict[str, Dict[str, Tuple[float, float]]] = {}
    for mode in controllers:
        stats_by_controller[mode] = {}
        for metric_key, _, _ in METRIC_DEFINITIONS:
            vals = [r[metric_key] for r in all_runs[mode]]
            stats_by_controller[mode][metric_key] = compute_metric_stats(vals)

    summary_rows = []
    full_stats_rows = []
    has_dqn = "marl_dqn" in controllers
    has_ppo = "marl_ppo" in controllers

    for metric_key, label, higher_is_better in METRIC_DEFINITIONS:
        b_mean, b_std = stats_by_controller["baseline"][metric_key]
        c_mean, c_std = stats_by_controller["coordinated"][metric_key]
        dqn_mean, dqn_std = stats_by_controller["marl_dqn"][metric_key] if has_dqn else (None, None)
        ppo_mean, ppo_std = stats_by_controller["marl_ppo"][metric_key] if has_ppo else (None, None)

        # Handle zero-completed trips: a travel time of 0.0 means 0 trips finished, not 0s duration
        dqn_val_clean = dqn_mean
        if metric_key in ("mean_corridor_travel_time_s", "emergency_traversal_duration_s") and dqn_mean == 0.0:
            dqn_val_clean = None

        ppo_val_clean = ppo_mean
        if metric_key in ("mean_corridor_travel_time_s", "emergency_traversal_duration_s") and ppo_mean == 0.0:
            ppo_val_clean = None

        c_gain = calculate_improvement_pct(b_mean, c_mean, higher_is_better)
        dqn_gain = calculate_improvement_pct(b_mean, dqn_val_clean, higher_is_better) if dqn_val_clean is not None else ""
        ppo_gain = calculate_improvement_pct(b_mean, ppo_val_clean, higher_is_better) if ppo_val_clean is not None else ""

        summary_rows.append({
            "metric": metric_key,
            "label": label,
            "baseline": b_mean,
            "coordinated": c_mean,
            "marl_dqn": dqn_val_clean if dqn_val_clean is not None else "",
            "marl_ppo": ppo_val_clean if ppo_val_clean is not None else "",
            "coord_vs_base_pct": c_gain,
            "dqn_vs_base_pct": dqn_gain,
            "ppo_vs_base_pct": ppo_gain,
            "status_marl": "Trained & Evaluated (SUMO 1.28.0)",
        })

        full_stats_rows.append({
            "metric": metric_key,
            "label": label,
            "baseline_mean": b_mean,
            "baseline_std": b_std,
            "coordinated_mean": c_mean,
            "coordinated_std": c_std,
            "dqn_mean": dqn_val_clean if dqn_val_clean is not None else "",
            "dqn_std": dqn_std if dqn_std is not None else "",
            "ppo_mean": ppo_val_clean if ppo_val_clean is not None else "",
            "ppo_std": ppo_std if ppo_std is not None else "",
            "coord_vs_base_pct": c_gain,
            "dqn_vs_base_pct": dqn_gain,
            "ppo_vs_base_pct": ppo_gain,
        })

    with open(SUMMARY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    with open(FULL_STATS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(full_stats_rows[0].keys()))
        writer.writeheader()
        writer.writerows(full_stats_rows)

    return summary_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Multi-Intersection Traffic Controllers")
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3, 4, 5], help="Random seeds for evaluation")
    parser.add_argument("--duration", type=int, default=600, help="Episode duration in seconds")
    parser.add_argument(
        "--controllers",
        nargs="+",
        default=["baseline", "coordinated", "marl_dqn", "marl_ppo"],
        help="List of controllers to evaluate",
    )
    parser.add_argument("--from-cache", action="store_true", help="Recompute tables from cached multi-seed JSON")
    args = parser.parse_args()

    if args.from_cache:
        rows = recompute_from_cache()
    else:
        rows, _ = evaluate_all_controllers(seeds=args.seeds, duration=args.duration, controllers=args.controllers)

    print_comparison_table(rows)


if __name__ == "__main__":
    main()
