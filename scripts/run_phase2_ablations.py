"""
scripts/run_phase2_ablations.py

Executes Phase 2 Ablation Studies:
1. Ablation A: No Emergency Coordination (enable_emergency=False)
   - Evaluated across seeds 1 to 10 for 6 controllers:
     ['baseline', 'coordinated', 'webster', 'nema', 'max_pressure', 'marl_dqn']
   - 60 runs total.
2. Ablation B: Downstream Queue Backpressure Suppression / Feedback Disabling (downstream_junction=None for Max-Pressure; Upstream Inflow Anticipation Disabled for Coordinated)
   - Evaluated across seeds 1 to 10 for 2 controllers:
     ['coordinated', 'max_pressure']
   - 20 runs total.

Total: 80 simulation runs.
Results are strictly isolated in `outputs/experiments/phase2_ablations/`.
"""

import argparse
import dataclasses
import json
import logging
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import SUMO_CONFIG_PATH
from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ablation_benchmark")

ABLATION_A_CONTROLLERS = [
    "baseline",
    "coordinated",
    "webster",
    "nema",
    "max_pressure",
    "marl_dqn",
]

ABLATION_B_CONTROLLERS = [
    "coordinated",
    "max_pressure",
]

DEFAULT_SEEDS = list(range(1, 11))  # Seeds 1 to 10
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase2_ablations"


def run_single_ablation_sim(args: Tuple[str, str, int, float, str]) -> Dict[str, Any]:
    ablation_type, mode, seed, duration, out_dir_str = args
    ablation_dir = Path(out_dir_str) / ablation_type
    ablation_dir.mkdir(parents=True, exist_ok=True)
    out_file = ablation_dir / f"{mode}_seed{seed}.json"

    if out_file.is_file():
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("completed", False):
                    return data
        except Exception:
            pass

    t_start = time.time()
    label = f"abl_{ablation_type}_{mode}_{seed}_{os.getpid()}"

    enable_emergency = (ablation_type != "no_emergency")

    sim = MultiIntersectionSimulation(
        sumocfg_path=SUMO_CONFIG_PATH,
        mode=mode,
        step_length=1.0,
        gui=False,
        label=label,
        enable_emergency=enable_emergency,
    )

    # For Ablation B: Downstream Queue Backpressure Suppression / Feedback Disabling
    if ablation_type == "no_inter_intersection_comms":
        if mode == "coordinated":
            # Override hub expected inflow to 0.0 (no upstream anticipation for J2)
            sim.hub.get_expected_inflow = lambda j_id: 0.0
        elif mode == "max_pressure":
            # Suppress downstream queue backpressure (downstream_junction = None, turning into pure local queue-gradient)
            if sim.max_pressure_controller is not None:
                new_configs = {}
                for j_id, j_cfg in sim.max_pressure_controller.configs.items():
                    new_phases = {}
                    for p_id, p_cfg in j_cfg.phases.items():
                        new_mvs = [
                            dataclasses.replace(mv, downstream_junction=None, downstream_approach=None)
                            for mv in p_cfg.movements
                        ]
                        new_phases[p_id] = dataclasses.replace(p_cfg, movements=new_mvs)
                    new_j_cfg = dataclasses.replace(j_cfg, phases=new_phases)
                    new_configs[j_id] = new_j_cfg
                    if j_id in sim.max_pressure_controller.junction_controllers:
                        sim.max_pressure_controller.junction_controllers[j_id].config = new_j_cfg
                sim.max_pressure_controller.configs = new_configs

    try:
        sim.start(seed=seed)

        while sim.sumo_manager.get_time() < duration:
            sim.step()

        emergency_completed = sim.emergency_coordinator.metrics.completed
        emergency_dur = (
            sim.emergency_coordinator.metrics.total_traversal_duration
            if emergency_completed
            else None
        )
        summary = sim.metrics_collector.compute_summary(
            emergency_duration=emergency_dur,
            emergency_cleared=emergency_completed,
        )
        sim.close()

        t_elapsed = time.time() - t_start

        record = {
            "ablation": ablation_type,
            "controller": mode,
            "seed": seed,
            "enable_emergency": enable_emergency,
            "completed": True,
            "execution_wall_time_s": round(t_elapsed, 2),
            "simulation_duration_s": summary.simulation_duration,
            "total_vehicles_inserted": summary.total_vehicles_inserted,
            "total_corridor_trips_completed": summary.total_corridor_trips_completed,
            "mean_corridor_travel_time_s": summary.mean_corridor_travel_time_s,
            "mean_corridor_speed_kmh": summary.mean_corridor_speed_kmh,
            "cumulative_delay_veh_s": summary.cumulative_delay_veh_s,
            "cumulative_waiting_time_s": summary.cumulative_waiting_time_s,
            "mean_corridor_queue": summary.mean_corridor_queue,
            "max_corridor_queue": summary.max_corridor_queue,
            "total_co2_kg": summary.total_co2_kg,
            "total_nox_g": summary.total_nox_g,
            "total_fuel_liters": summary.total_fuel_liters,
            "emergency_traversal_duration_s": summary.emergency_traversal_duration_s,
            "emergency_cleared": summary.emergency_cleared,
        }

        tmp_file = out_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        tmp_file.replace(out_file)

        return record

    except Exception as e:
        logger.error(f"Error in ablation simulation ({ablation_type}, {mode}, seed={seed}): {e}", exc_info=True)
        try:
            sim.close()
        except Exception:
            pass
        return {
            "ablation": ablation_type,
            "controller": mode,
            "seed": seed,
            "completed": False,
            "error": str(e),
        }


def main():
    parser = argparse.ArgumentParser(description="Phase 2 Ablation Studies Benchmark")
    parser.add_argument("--workers", type=int, default=6, help="Parallel worker processes")
    parser.add_argument("--duration", type=float, default=900.0, help="Simulation duration (s)")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS, help="Seeds list")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("=== STARTING PHASE 2 ABLATION STUDIES ===")
    logger.info(f"Seeds: {args.seeds}")
    logger.info(f"Workers: {args.workers}")

    # Build tasks
    tasks = []
    # Ablation A
    for ctrl in ABLATION_A_CONTROLLERS:
        for seed in args.seeds:
            tasks.append(("no_emergency", ctrl, seed, args.duration, str(OUTPUT_DIR)))
    # Ablation B
    for ctrl in ABLATION_B_CONTROLLERS:
        for seed in args.seeds:
            tasks.append(("no_inter_intersection_comms", ctrl, seed, args.duration, str(OUTPUT_DIR)))

    logger.info(f"Total ablation runs to execute: {len(tasks)}")

    t0 = time.time()
    results: List[Dict[str, Any]] = []
    completed_count = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        future_map = {executor.submit(run_single_ablation_sim, t): t for t in tasks}
        for future in as_completed(future_map):
            abl_type, ctrl, seed, _, _ = future_map[future]
            try:
                res = future.result()
                results.append(res)
                if res.get("completed", False):
                    completed_count += 1
                    tt = res.get("mean_corridor_travel_time_s")
                    tt_str = f"{tt:.2f}s" if tt is not None else "N/A"
                    logger.info(
                        f"[{completed_count}/{len(tasks)}] Done: {abl_type:28s} | {ctrl:15s} | Seed={seed} | "
                        f"TravelTime={tt_str:8s} | EmCleared={res.get('emergency_cleared')} | "
                        f"EmDur={res.get('emergency_traversal_duration_s')}"
                    )
                else:
                    logger.error(f"FAILED: {abl_type} | {ctrl} | Seed={seed} | Error: {res.get('error')}")
            except Exception as e:
                logger.error(f"Worker exception ({abl_type}, {ctrl}, seed {seed}): {e}")

    total_time = time.time() - t0
    logger.info(f"=== ALL {completed_count}/{len(tasks)} ABLATION RUNS FINISHED IN {total_time:.2f}s ({total_time/60:.2f} min) ===")

    # Aggregate Ablations Summary
    ablations_summary = {
        "metadata": {
            "experiment": "Phase 2 Ablation Studies",
            "duration_s": args.duration,
            "seeds": args.seeds,
            "total_runs": len(results),
            "completed_runs": completed_count,
            "total_wall_time_s": round(total_time, 2),
        },
        "ablations": {},
    }

    ablation_types = ["no_emergency", "no_inter_intersection_comms"]
    for abl_type in ablation_types:
        abl_runs_all = [r for r in results if r.get("ablation") == abl_type and r.get("completed", False)]
        ctrls_in_abl = sorted(list({r["controller"] for r in abl_runs_all}))

        ablations_summary["ablations"][abl_type] = {
            "controllers": {},
        }

        for ctrl in ctrls_in_abl:
            ctrl_runs = [r for r in abl_runs_all if r["controller"] == ctrl]
            ctrl_runs.sort(key=lambda r: r["seed"])

            tts = [r["mean_corridor_travel_time_s"] for r in ctrl_runs if r.get("mean_corridor_travel_time_s") is not None]
            delays = [r["cumulative_delay_veh_s"] for r in ctrl_runs]
            queues = [r["mean_corridor_queue"] for r in ctrl_runs]
            speeds = [r["mean_corridor_speed_kmh"] for r in ctrl_runs]
            trips = [r["total_corridor_trips_completed"] for r in ctrl_runs]
            em_cleared_count = sum(1 for r in ctrl_runs if r.get("emergency_cleared") is True)
            em_durs = [r["emergency_traversal_duration_s"] for r in ctrl_runs if r.get("emergency_traversal_duration_s") is not None]

            ablations_summary["ablations"][abl_type]["controllers"][ctrl] = {
                "n_runs": len(ctrl_runs),
                "emergency_cleared_rate": em_cleared_count / len(ctrl_runs) if ctrl_runs else 0.0,
                "emergency_traversal_duration_s": {
                    "mean": float(sum(em_durs) / len(em_durs)) if em_durs else None,
                    "values": em_durs,
                },
                "travel_time_s": {
                    "mean": float(sum(tts) / len(tts)) if tts else 0.0,
                    "min": float(min(tts)) if tts else 0.0,
                    "max": float(max(tts)) if tts else 0.0,
                    "values": tts,
                },
                "cumulative_delay_veh_s": {
                    "mean": float(sum(delays) / len(delays)) if delays else 0.0,
                    "values": delays,
                },
                "mean_queue": {
                    "mean": float(sum(queues) / len(queues)) if queues else 0.0,
                    "values": queues,
                },
                "mean_speed_kmh": {
                    "mean": float(sum(speeds) / len(speeds)) if speeds else 0.0,
                    "values": speeds,
                },
                "completed_trips": {
                    "mean": float(sum(trips) / len(trips)) if trips else 0.0,
                    "values": trips,
                },
            }

    summary_file = OUTPUT_DIR / "ablations_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(ablations_summary, f, indent=2)

    logger.info(f"Saved master ablations summary to: {summary_file}")


if __name__ == "__main__":
    main()
