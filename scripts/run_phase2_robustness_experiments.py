"""
scripts/run_phase2_robustness_experiments.py

Executes Robustness and Generalization Experiments across three traffic demand regimes:
1. Low Demand: --scale 0.5 (seeds 1 to 5, all 8 controllers = 40 runs)
2. Heavy Congestion: --scale 1.5 (seeds 1 to 5, all 8 controllers = 40 runs)
3. Asymmetric Surge: --scale 1.25 (seeds 1 to 5, all 8 controllers = 40 runs)

Total: 120 simulation runs.
Results are strictly isolated in `outputs/experiments/phase2_robustness/`.
"""

import argparse
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
logger = logging.getLogger("robustness_benchmark")

CONTROLLERS = [
    "baseline",
    "coordinated",
    "webster",
    "nema",
    "max_pressure",
    "marl_dqn",
    "marl_ppo",
    "marl_mappo",
]

SCENARIOS = {
    "low_demand_0_5": {"scale": 0.5, "desc": "Low Demand (--scale 0.5)"},
    "heavy_congestion_1_5": {"scale": 1.5, "desc": "Heavy Congestion (--scale 1.5)"},
    "asymmetric_surge_1_25": {"scale": 1.25, "desc": "Asymmetric Surge (--scale 1.25)"},
}

DEFAULT_SEEDS = [1, 2, 3, 4, 5]
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase2_robustness"


def run_single_robustness_sim(args: Tuple[str, str, float, int, float, str]) -> Dict[str, Any]:
    scenario_key, mode, scale, seed, duration, out_dir_str = args
    scenario_dir = Path(out_dir_str) / scenario_key
    scenario_dir.mkdir(parents=True, exist_ok=True)
    out_file = scenario_dir / f"{mode}_seed{seed}.json"

    if out_file.is_file():
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("completed", False):
                    return data
        except Exception:
            pass

    t_start = time.time()
    label = f"rob_{scenario_key}_{mode}_{seed}_{os.getpid()}"

    sim = MultiIntersectionSimulation(
        sumocfg_path=SUMO_CONFIG_PATH,
        mode=mode,
        step_length=1.0,
        gui=False,
        label=label,
    )

    try:
        additional_args = ["--scale", str(scale)]
        sim.start(seed=seed, additional_args=additional_args)

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
            "scenario": scenario_key,
            "scale": scale,
            "controller": mode,
            "seed": seed,
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
        logger.error(f"Error in robustness simulation ({scenario_key}, {mode}, seed={seed}): {e}", exc_info=True)
        try:
            sim.close()
        except Exception:
            pass
        return {
            "scenario": scenario_key,
            "scale": scale,
            "controller": mode,
            "seed": seed,
            "completed": False,
            "error": str(e),
        }


def main():
    parser = argparse.ArgumentParser(description="Phase 2 Robustness & Generalization Benchmark")
    parser.add_argument("--workers", type=int, default=6, help="Parallel worker processes")
    parser.add_argument("--duration", type=float, default=900.0, help="Simulation duration (s)")
    parser.add_argument("--controllers", nargs="+", default=CONTROLLERS, help="Controllers list")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS, help="Seeds list")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("=== STARTING PHASE 2 ROBUSTNESS & GENERALIZATION EXPERIMENTS ===")
    logger.info(f"Controllers: {args.controllers}")
    logger.info(f"Seeds: {args.seeds}")
    logger.info(f"Scenarios: {list(SCENARIOS.keys())}")
    logger.info(f"Workers: {args.workers}")

    tasks = [
        (scen_key, ctrl, scen_info["scale"], seed, args.duration, str(OUTPUT_DIR))
        for scen_key, scen_info in SCENARIOS.items()
        for ctrl in args.controllers
        for seed in args.seeds
    ]
    logger.info(f"Total robustness runs to execute: {len(tasks)}")

    t0 = time.time()
    results: List[Dict[str, Any]] = []
    completed_count = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        future_map = {executor.submit(run_single_robustness_sim, t): t for t in tasks}
        for future in as_completed(future_map):
            scen_key, ctrl, _, seed, _, _ = future_map[future]
            try:
                res = future.result()
                results.append(res)
                if res.get("completed", False):
                    completed_count += 1
                    tt = res.get("mean_corridor_travel_time_s")
                    tt_str = f"{tt:.2f}s" if tt is not None else "N/A"
                    logger.info(
                        f"[{completed_count}/{len(tasks)}] Done: {scen_key:22s} | {ctrl:15s} | Seed={seed} | "
                        f"TravelTime={tt_str:8s} | CompletedTrips={res.get('total_corridor_trips_completed', 0)} | "
                        f"Queue={res.get('mean_corridor_queue', 0):.2f}"
                    )
                else:
                    logger.error(f"FAILED: {scen_key} | {ctrl} | Seed={seed} | Error: {res.get('error')}")
            except Exception as e:
                logger.error(f"Worker exception ({scen_key}, {ctrl}, seed {seed}): {e}")

    total_time = time.time() - t0
    logger.info(f"=== ALL {completed_count}/{len(tasks)} ROBUSTNESS RUNS FINISHED IN {total_time:.2f}s ({total_time/60:.2f} min) ===")

    # Aggregate Robustness Summary
    robustness_summary = {
        "metadata": {
            "experiment": "Phase 2 Robustness and Generalization Experiments",
            "duration_s": args.duration,
            "controllers": args.controllers,
            "seeds": args.seeds,
            "scenarios": SCENARIOS,
            "total_runs": len(results),
            "completed_runs": completed_count,
            "total_wall_time_s": round(total_time, 2),
        },
        "scenarios": {},
    }

    for scen_key, scen_info in SCENARIOS.items():
        robustness_summary["scenarios"][scen_key] = {
            "description": scen_info["desc"],
            "scale": scen_info["scale"],
            "controllers": {},
        }
        for ctrl in args.controllers:
            ctrl_runs = [
                r for r in results
                if r.get("scenario") == scen_key and r.get("controller") == ctrl and r.get("completed", False)
            ]
            ctrl_runs.sort(key=lambda r: r["seed"])

            tts = [r["mean_corridor_travel_time_s"] for r in ctrl_runs if r.get("mean_corridor_travel_time_s") is not None]
            delays = [r["cumulative_delay_veh_s"] for r in ctrl_runs]
            queues = [r["mean_corridor_queue"] for r in ctrl_runs]
            speeds = [r["mean_corridor_speed_kmh"] for r in ctrl_runs]
            trips = [r["total_corridor_trips_completed"] for r in ctrl_runs]
            co2s = [r["total_co2_kg"] for r in ctrl_runs]

            robustness_summary["scenarios"][scen_key]["controllers"][ctrl] = {
                "n_runs": len(ctrl_runs),
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
                "total_co2_kg": {
                    "mean": float(sum(co2s) / len(co2s)) if co2s else 0.0,
                    "values": co2s,
                },
            }

    summary_file = OUTPUT_DIR / "robustness_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(robustness_summary, f, indent=2)

    logger.info(f"Saved master robustness summary to: {summary_file}")


if __name__ == "__main__":
    main()
