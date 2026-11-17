"""
scripts/run_phase2_30seeds_benchmark.py

Authoritative 30-Seed Classical and RL Controller Benchmark Execution Pipeline.
Evaluates 8 traffic controllers across 30 identical matched random seeds (1 to 30)
under the Bengaluru Silk Board microscopic corridor simulation:
1. Fixed-Time Baseline
2. Coordinated Adaptive
3. Webster Optimum Fixed-Time
4. NEMA Actuated TS 2
5. Varaiya Max-Pressure
6. Dueling Double-DQN
7. Independent PPO
8. Multi-Agent PPO (MAPPO)

Outputs are strictly isolated in `outputs/experiments/phase2_30seeds/`.
"""

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import SUMO_CONFIG_PATH
from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("benchmark_30seeds")

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

DEFAULT_SEEDS = list(range(1, 31))  # Seeds 1 to 30
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase2_30seeds"


def run_single_simulation(args: Tuple[str, int, float, str]) -> Dict[str, Any]:
    """Worker function executing one 900-second simulation run."""
    mode, seed, duration, out_dir_str = args
    out_dir = Path(out_dir_str)
    out_file = out_dir / f"{mode}_seed{seed}.json"

    # If already successfully executed, return cached record
    if out_file.is_file():
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("completed", False):
                    return data
        except Exception:
            pass

    t_start = time.time()
    label = f"b30_{mode}_{seed}_{os.getpid()}"

    sim = MultiIntersectionSimulation(
        sumocfg_path=SUMO_CONFIG_PATH,
        mode=mode,
        step_length=1.0,
        gui=False,
        label=label,
    )

    try:
        summary = sim.run_full_simulation(duration_seconds=int(duration), seed=seed)
        t_elapsed = time.time() - t_start

        record = {
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
            "j1_mean_queue": summary.j1_mean_queue,
            "j2_mean_queue": summary.j2_mean_queue,
            "j3_mean_queue": summary.j3_mean_queue,
        }

        # Atomically write per-seed result
        tmp_file = out_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        tmp_file.replace(out_file)

        return record

    except Exception as e:
        logger.error(f"Error in simulation ({mode}, seed={seed}): {e}", exc_info=True)
        return {
            "controller": mode,
            "seed": seed,
            "completed": False,
            "error": str(e),
        }


def main():
    parser = argparse.ArgumentParser(description="Authoritative 30-Seed Benchmark Execution")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel SUMO workers")
    parser.add_argument("--duration", type=float, default=900.0, help="Simulation duration in seconds")
    parser.add_argument("--controllers", nargs="+", default=CONTROLLERS, help="Controllers to benchmark")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS, help="Seed list")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"=== STARTING AUTHORITATIVE 30-SEED BENCHMARK ===")
    logger.info(f"Controllers: {args.controllers}")
    logger.info(f"Seeds: {len(args.seeds)} seeds ({args.seeds[0]}..{args.seeds[-1]})")
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Output Directory: {OUTPUT_DIR}")

    tasks = [
        (ctrl, seed, args.duration, str(OUTPUT_DIR))
        for ctrl in args.controllers
        for seed in args.seeds
    ]
    logger.info(f"Total simulations to execute: {len(tasks)}")

    t0 = time.time()
    results: List[Dict[str, Any]] = []
    completed_count = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        future_map = {executor.submit(run_single_simulation, t): t for t in tasks}
        for future in as_completed(future_map):
            ctrl, seed, _, _ = future_map[future]
            try:
                res = future.result()
                results.append(res)
                if res.get("completed", False):
                    completed_count += 1
                    tt = res.get("mean_corridor_travel_time_s")
                    tt_str = f"{tt:.2f}s" if tt is not None else "N/A"
                    logger.info(
                        f"[{completed_count}/{len(tasks)}] Done: {ctrl:15s} | Seed={seed:2d} | "
                        f"TravelTime={tt_str:8s} | CompletedTrips={res.get('total_corridor_trips_completed', 0)} | "
                        f"Queue={res.get('mean_corridor_queue', 0):.2f}"
                    )
                else:
                    logger.error(f"FAILED: {ctrl} | Seed={seed} | Error: {res.get('error')}")
            except Exception as e:
                logger.error(f"Worker exception for {ctrl} seed {seed}: {e}")

    total_time = time.time() - t0
    logger.info(f"=== ALL {completed_count}/{len(tasks)} SIMULATIONS FINISHED IN {total_time:.2f}s ({total_time/60:.2f} min) ===")

    # Aggregate Master Summary
    summary_data = {
        "benchmark_metadata": {
            "experiment": "Authoritative 30-Seed Benchmark",
            "simulation_horizon_s": args.duration,
            "controllers_evaluated": args.controllers,
            "seeds": args.seeds,
            "total_runs": len(results),
            "completed_runs": completed_count,
            "total_wall_time_s": round(total_time, 2),
        },
        "per_controller_results": {},
    }

    for ctrl in args.controllers:
        ctrl_runs = [r for r in results if r.get("controller") == ctrl and r.get("completed", False)]
        ctrl_runs.sort(key=lambda r: r["seed"])
        
        tts = [r["mean_corridor_travel_time_s"] for r in ctrl_runs if r.get("mean_corridor_travel_time_s") is not None]
        delays = [r["cumulative_delay_veh_s"] for r in ctrl_runs]
        queues = [r["mean_corridor_queue"] for r in ctrl_runs]
        co2s = [r["total_co2_kg"] for r in ctrl_runs]
        fuels = [r["total_fuel_liters"] for r in ctrl_runs]
        speeds = [r["mean_corridor_speed_kmh"] for r in ctrl_runs]
        trips = [r["total_corridor_trips_completed"] for r in ctrl_runs]

        summary_data["per_controller_results"][ctrl] = {
            "total_runs": len(ctrl_runs),
            "seeds": [r["seed"] for r in ctrl_runs],
            "metrics": {
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
                "total_fuel_liters": {
                    "mean": float(sum(fuels) / len(fuels)) if fuels else 0.0,
                    "values": fuels,
                },
            },
        }

    summary_file = OUTPUT_DIR / "benchmark_30seeds_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    logger.info(f"Saved master 30-seed summary to: {summary_file}")


if __name__ == "__main__":
    main()
