"""
scripts/run_phase4_simulations.py

Phase 4 Authoritative Simulation Pipeline:
- Series 4A: Safety Shield Ablation (2 controllers x 2 conditions x 10 seeds = 40 runs)
- Series 4D: Matched Transit Signal Priority Causal Evaluation (4 controllers x 2 conditions x 12 seeds = 96 runs)
- Series 4G: Inter-Junction Communication Ablation (3 controllers x 2 conditions x 10 seeds = 60 runs)

Total simulation runs across 4A, 4D, 4G = 196 runs.
Strict isolation under `outputs/experiments/phase4/`.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import logging
import os
from pathlib import Path
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import numpy as np

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import SUMO_CONFIG_PATH
from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation
from traffic_service.resilience.detailed_collector import DetailedCorridorMetricsCollector
from traffic_service.resilience.transit_priority import TransitSignalPriorityManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("phase4_simulations")

BASE_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase4"


# =====================================================================
# SIMULATION WORKER TASK
# =====================================================================

def execute_phase4_sim_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a single parametrized Phase 4 simulation run.
    """
    series = task["series"]
    controller = task["controller"]
    seed = task["seed"]
    duration = task.get("duration", 900.0)
    out_file = Path(task["out_file"])

    enable_safety_shield = bool(task.get("enable_safety_shield", True))
    enable_communication = bool(task.get("enable_communication", True))
    enable_tsp = bool(task.get("enable_tsp", False))
    observation_dim = int(task.get("observation_dim", 14))
    checkpoint_path = task.get("checkpoint_path", None)

    # Check cache / existing completed file
    if out_file.is_file():
        try:
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("completed", False):
                    return data
        except Exception:
            pass

    out_file.parent.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    label = f"p4_{series}_{controller}_{seed}_{os.getpid()}_{int(time.time()*1000)%10000}"

    try:
        sim = MultiIntersectionSimulation(
            sumocfg_path=SUMO_CONFIG_PATH,
            mode=controller,
            step_length=1.0,
            decision_interval=5.0,
            gui=False,
            label=label,
            enable_safety_shield=enable_safety_shield,
            enable_communication=enable_communication,
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

        # Starvation and safety violation monitoring
        starvation_violations_count = 0
        min_green_violations_count = 0
        phase_switch_count = 0
        max_queued_red_seen = 0.0

        # Track previous phases to count switches and min green breaches
        last_phases = {}
        phase_start_times = {}

        sim.start(seed=seed)
        try:
            for j_id, ctrl in sim.controllers.items():
                last_phases[j_id] = ctrl.get_phase()
                phase_start_times[j_id] = 0.0

            while sim.sumo_manager.get_time() < duration:
                states, _ = sim.step()
                sim_time = sim.sumo_manager.get_time()

                # Update TSP manager
                if tsp_mgr is not None:
                    tsp_mgr.update(sim_time)

                # Monitor phase switches and min green violations across junctions
                for j_id, ctrl in sim.controllers.items():
                    curr_phase = ctrl.get_phase()
                    if curr_phase != last_phases[j_id]:
                        phase_switch_count += 1
                        time_in_phase = sim_time - phase_start_times[j_id]
                        # If switched away from green earlier than min_green
                        min_g = ctrl.min_green
                        if last_phases[j_id] in sim.green_phases[j_id] and time_in_phase < min_g:
                            min_green_violations_count += 1
                        last_phases[j_id] = curr_phase
                        phase_start_times[j_id] = sim_time

                # Monitor starvation (>65.0s red wait on queued vehicles)
                for j_id, state in states.items():
                    ctrl = sim.controllers[j_id]
                    curr_p = ctrl.get_phase()
                    if curr_p in sim.green_phases[j_id]:
                        # Green phase active, check cross queue wait
                        cross_q = state.approach_queues.get("side_cross", state.approach_queues.get("madiwala", 0))
                        if cross_q > 0:
                            wait = ctrl.get_green_elapsed(sim_time)
                            if wait > max_queued_red_seen:
                                max_queued_red_seen = wait
                            if wait > 65.0:
                                starvation_violations_count += 1
                    else:
                        # Yellow or cross phase active, check arterial queue wait
                        corridor_q = state.approach_queues.get("corridor_hosur", 0)
                        if corridor_q > 0:
                            wait = ctrl.get_green_elapsed(sim_time)
                            if wait > max_queued_red_seen:
                                max_queued_red_seen = wait
                            if wait > 65.0:
                                starvation_violations_count += 1

            t_elapsed = time.time() - t_start
            emergency_completed = sim.emergency_coordinator.metrics.completed
            emergency_dur = (
                sim.emergency_coordinator.metrics.total_traversal_duration
                if emergency_completed
                else None
            )

            metrics_summary = detailed_collector.compute_detailed_summary(
                emergency_duration=emergency_dur,
                emergency_cleared=emergency_completed,
            )

            record: Dict[str, Any] = {
                "series": series,
                "controller": controller,
                "seed": seed,
                "completed": True,
                "execution_wall_time_s": round(t_elapsed, 2),
                "simulation_duration_s": metrics_summary["simulation_duration_s"],
                "total_corridor_trips_completed": metrics_summary["total_corridor_trips_completed"],
                "mean_corridor_travel_time_s": metrics_summary["mean_corridor_travel_time_s"],
                "mean_corridor_speed_kmh": metrics_summary["mean_corridor_speed_kmh"],
                "cumulative_delay_veh_s": metrics_summary["cumulative_delay_veh_s"],
                "mean_corridor_queue": metrics_summary["mean_corridor_queue"],
                "max_corridor_queue": metrics_summary["max_corridor_queue"],
                "total_co2_kg": metrics_summary["total_co2_kg"],
                "total_fuel_liters": metrics_summary["total_fuel_liters"],
                "emergency_traversal_duration_s": metrics_summary["emergency_traversal_duration_s"],
                "emergency_cleared": metrics_summary["emergency_cleared"],
                "reliability": metrics_summary["reliability"],
                "multi_modal": metrics_summary["multi_modal"],
                "equity": metrics_summary["equity"],
                "safety": {
                    "enable_safety_shield": enable_safety_shield,
                    "starvation_violations_count": starvation_violations_count,
                    "min_green_violations_count": min_green_violations_count,
                    "phase_switch_count": phase_switch_count,
                    "max_queued_red_seen": round(max_queued_red_seen, 2),
                },
                "communication": {
                    "enable_communication": enable_communication,
                },
            }

            if tsp_mgr is not None:
                tsp_summary = tsp_mgr.compute_summary()
                record["transit_priority"] = asdict(tsp_summary)

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2)

            return record

        finally:
            sim.close()

    except Exception as exc:
        logger.error(f"Task failure ({series}, {controller}, seed={seed}): {exc!r}", exc_info=True)
        err_record = {
            "series": series,
            "controller": controller,
            "seed": seed,
            "completed": False,
            "error": str(exc),
            "execution_wall_time_s": round(time.time() - t_start, 2),
        }
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(err_record, f, indent=2)
        return err_record


# =====================================================================
# WORKER DISPATCHER
# =====================================================================

def dispatch_tasks(tasks: List[Dict[str, Any]], workers: int = 6) -> List[Dict[str, Any]]:
    """Runs simulation tasks in parallel using ProcessPoolExecutor."""
    t0 = time.time()
    results = []
    completed = 0
    total = len(tasks)
    logger.info(f"Dispatching {total} tasks across {workers} parallel processes...")

    with ProcessPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(execute_phase4_sim_task, task): task for task in tasks}
        for future in as_completed(future_map):
            t_spec = future_map[future]
            try:
                res = future.result()
                results.append(res)
                if res.get("completed", False):
                    completed += 1
                    logger.info(
                        f"[{completed}/{total}] Done: {res.get('series')}/{res.get('controller')} | "
                        f"Seed={res.get('seed')} | TT={res.get('mean_corridor_travel_time_s')}s | "
                        f"Delay={res.get('cumulative_delay_veh_s')}veh*s"
                    )
                else:
                    logger.error(f"Task Failed: {t_spec} | Error: {res.get('error')}")
            except Exception as e:
                logger.error(f"Task exception for {t_spec}: {e}")

    total_time = time.time() - t0
    logger.info(f"Finished {completed}/{total} tasks in {total_time:.1f}s ({total_time/60:.2f} min).")
    return results


# =====================================================================
# SERIES RUNNERS & AGGREGATORS
# =====================================================================

def run_series_4a_safety_shield(workers: int = 6, duration: float = 900.0) -> Dict[str, Any]:
    """
    Series 4A: Safety Shield Ablation (MAPPO, DQN x Shielded, Unshielded x Seeds 1..10 = 40 runs).
    """
    series_dir = BASE_OUTPUT_DIR / "series_4a_safety_shield"
    series_dir.mkdir(parents=True, exist_ok=True)
    controllers = ["marl_mappo", "marl_dqn"]
    conditions = [
        {"name": "shielded", "enable_safety_shield": True},
        {"name": "unshielded", "enable_safety_shield": False},
    ]
    seeds = list(range(1, 11))

    tasks = []
    for ctrl in controllers:
        for cond in conditions:
            for seed in seeds:
                out_file = series_dir / f"eval_{ctrl}_{cond['name']}_seed{seed}.json"
                tasks.append({
                    "series": "4a_safety_shield",
                    "controller": ctrl,
                    "condition": cond["name"],
                    "enable_safety_shield": cond["enable_safety_shield"],
                    "enable_communication": True,
                    "seed": seed,
                    "duration": duration,
                    "out_file": str(out_file),
                })

    results = dispatch_tasks(tasks, workers=workers)

    # Aggregate Series 4A summary
    summary: Dict[str, Any] = {
        "metadata": {
            "experiment": "Series 4A: Safety Shield Ablation",
            "duration_s": duration,
            "controllers": controllers,
            "conditions": ["shielded", "unshielded"],
            "seeds": seeds,
            "total_runs": len(tasks),
            "completed_runs": sum(1 for r in results if r.get("completed")),
        },
        "per_condition": {},
    }

    for ctrl in controllers:
        summary["per_condition"][ctrl] = {}
        for cond in conditions:
            cond_name = cond["name"]
            runs = [
                r for r in results
                if r.get("controller") == ctrl
                and r.get("safety", {}).get("enable_safety_shield") == cond["enable_safety_shield"]
                and r.get("completed")
            ]
            runs.sort(key=lambda r: r["seed"])
            tts = [r["mean_corridor_travel_time_s"] for r in runs if r["mean_corridor_travel_time_s"] is not None]
            delays = [r["cumulative_delay_veh_s"] for r in runs]
            trips = [r["total_corridor_trips_completed"] for r in runs]
            starvations = [r["safety"]["starvation_violations_count"] for r in runs]
            min_green_v = [r["safety"]["min_green_violations_count"] for r in runs]
            switches = [r["safety"]["phase_switch_count"] for r in runs]
            max_reds = [r["safety"]["max_queued_red_seen"] for r in runs]

            summary["per_condition"][ctrl][cond_name] = {
                "runs_completed": len(runs),
                "travel_time_mean_s": round(float(np.mean(tts)), 2) if tts else None,
                "travel_time_std_s": round(float(np.std(tts, ddof=1)), 2) if len(tts) > 1 else 0.0,
                "cumulative_delay_veh_s": round(float(np.mean(delays)), 2),
                "total_corridor_trips_completed": round(float(np.mean(trips)), 1),
                "starvation_violations_mean": round(float(np.mean(starvations)), 2),
                "starvation_violations_total": int(np.sum(starvations)),
                "min_green_violations_mean": round(float(np.mean(min_green_v)), 2),
                "min_green_violations_total": int(np.sum(min_green_v)),
                "phase_switches_mean": round(float(np.mean(switches)), 1),
                "max_queued_red_mean_s": round(float(np.mean(max_reds)), 2),
                "raw_starvations": starvations,
                "raw_travel_times": tts,
            }

    with open(series_dir / "series_4a_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def run_series_4d_transit_priority(workers: int = 6, duration: float = 900.0) -> Dict[str, Any]:
    """
    Series 4D: Matched Transit Signal Priority Causal Evaluation
    (Coordinated, Webster, NEMA, MAPPO x Enabled, Disabled x Seeds 1..12 = 96 runs).
    """
    series_dir = BASE_OUTPUT_DIR / "series_4d_transit_priority"
    series_dir.mkdir(parents=True, exist_ok=True)
    controllers = ["coordinated", "webster", "nema", "marl_mappo"]
    conditions = [
        {"name": "tsp_enabled", "enable_tsp": True},
        {"name": "tsp_disabled", "enable_tsp": False},
    ]
    seeds = list(range(1, 13))

    tasks = []
    for ctrl in controllers:
        for cond in conditions:
            for seed in seeds:
                out_file = series_dir / f"eval_{ctrl}_{cond['name']}_seed{seed}.json"
                tasks.append({
                    "series": "4d_transit_priority",
                    "controller": ctrl,
                    "condition": cond["name"],
                    "enable_tsp": cond["enable_tsp"],
                    "enable_safety_shield": True,
                    "enable_communication": True,
                    "seed": seed,
                    "duration": duration,
                    "out_file": str(out_file),
                })

    results = dispatch_tasks(tasks, workers=workers)

    summary: Dict[str, Any] = {
        "metadata": {
            "experiment": "Series 4D: Matched Transit Signal Priority Causal Evaluation",
            "duration_s": duration,
            "controllers": controllers,
            "conditions": ["tsp_enabled", "tsp_disabled"],
            "seeds": seeds,
            "total_runs": len(tasks),
            "completed_runs": sum(1 for r in results if r.get("completed")),
        },
        "per_controller": {},
    }

    for ctrl in controllers:
        summary["per_controller"][ctrl] = {}
        for cond in conditions:
            cond_name = cond["name"]
            is_tsp = cond["enable_tsp"]
            runs = [
                r for r in results
                if r.get("controller") == ctrl
                and (("transit_priority" in r) == is_tsp)
                and r.get("completed")
            ]
            runs.sort(key=lambda r: r["seed"])
            tts = [r["mean_corridor_travel_time_s"] for r in runs if r["mean_corridor_travel_time_s"] is not None]
            delays = [r["cumulative_delay_veh_s"] for r in runs]
            phds = [r["multi_modal"]["passenger_hours_of_delay_phd"] for r in runs]
            vhds = [r["multi_modal"]["vehicle_hours_of_delay_vhd"] for r in runs]
            bus_delay_hours = [
                r["multi_modal"].get("passenger_delay_by_class_hours", {}).get("bmtc_bus", 0.0)
                for r in runs
            ]

            summary["per_controller"][ctrl][cond_name] = {
                "runs_completed": len(runs),
                "travel_time_mean_s": round(float(np.mean(tts)), 2) if tts else None,
                "cumulative_delay_veh_s": round(float(np.mean(delays)), 2),
                "passenger_hours_of_delay_phd": round(float(np.mean(phds)), 3),
                "passenger_hours_of_delay_std": round(float(np.std(phds, ddof=1)), 3) if len(phds) > 1 else 0.0,
                "vehicle_hours_of_delay_vhd": round(float(np.mean(vhds)), 3),
                "bus_delay_hours_mean": round(float(np.mean(bus_delay_hours)), 3),
                "raw_phds": phds,
                "raw_travel_times": tts,
            }

            if is_tsp:
                tsp_reqs = [r.get("transit_priority", {}).get("total_requests", 0) for r in runs]
                tsp_grants = [r.get("transit_priority", {}).get("granted_requests", 0) for r in runs]
                tsp_rates = [g / max(1, req) for g, req in zip(tsp_grants, tsp_reqs)]
                summary["per_controller"][ctrl][cond_name].update({
                    "tsp_requests_mean": round(float(np.mean(tsp_reqs)), 1),
                    "tsp_grants_mean": round(float(np.mean(tsp_grants)), 1),
                    "tsp_grant_rate_mean": round(float(np.mean(tsp_rates)), 4),
                    "raw_tsp_grants": tsp_grants,
                    "raw_tsp_requests": tsp_reqs,
                })

    with open(series_dir / "series_4d_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def run_series_4g_communication(workers: int = 6, duration: float = 900.0) -> Dict[str, Any]:
    """
    Series 4G: Inter-Junction Communication Ablation
    (Coordinated, MAPPO, DQN x Enabled, Disabled x Seeds 1..10 = 60 runs).
    """
    series_dir = BASE_OUTPUT_DIR / "series_4g_communication"
    series_dir.mkdir(parents=True, exist_ok=True)
    controllers = ["coordinated", "marl_mappo", "marl_dqn"]
    conditions = [
        {"name": "comm_enabled", "enable_communication": True},
        {"name": "comm_disabled", "enable_communication": False},
    ]
    seeds = list(range(1, 11))

    tasks = []
    for ctrl in controllers:
        for cond in conditions:
            for seed in seeds:
                out_file = series_dir / f"eval_{ctrl}_{cond['name']}_seed{seed}.json"
                tasks.append({
                    "series": "4g_communication",
                    "controller": ctrl,
                    "condition": cond["name"],
                    "enable_communication": cond["enable_communication"],
                    "enable_safety_shield": True,
                    "seed": seed,
                    "duration": duration,
                    "out_file": str(out_file),
                })

    results = dispatch_tasks(tasks, workers=workers)

    summary: Dict[str, Any] = {
        "metadata": {
            "experiment": "Series 4G: Inter-Junction Communication Ablation",
            "duration_s": duration,
            "controllers": controllers,
            "conditions": ["comm_enabled", "comm_disabled"],
            "seeds": seeds,
            "total_runs": len(tasks),
            "completed_runs": sum(1 for r in results if r.get("completed")),
        },
        "per_controller": {},
    }

    for ctrl in controllers:
        summary["per_controller"][ctrl] = {}
        for cond in conditions:
            cond_name = cond["name"]
            runs = [
                r for r in results
                if r.get("controller") == ctrl
                and r.get("communication", {}).get("enable_communication") == cond["enable_communication"]
                and r.get("completed")
            ]
            runs.sort(key=lambda r: r["seed"])
            tts = [r["mean_corridor_travel_time_s"] for r in runs if r["mean_corridor_travel_time_s"] is not None]
            delays = [r["cumulative_delay_veh_s"] for r in runs]
            trips = [r["total_corridor_trips_completed"] for r in runs]
            speeds = [r["mean_corridor_speed_kmh"] for r in runs]

            summary["per_controller"][ctrl][cond_name] = {
                "runs_completed": len(runs),
                "travel_time_mean_s": round(float(np.mean(tts)), 2) if tts else None,
                "travel_time_std_s": round(float(np.std(tts, ddof=1)), 2) if len(tts) > 1 else 0.0,
                "cumulative_delay_veh_s": round(float(np.mean(delays)), 2),
                "total_corridor_trips_completed": round(float(np.mean(trips)), 1),
                "mean_corridor_speed_kmh": round(float(np.mean(speeds)), 2),
                "raw_travel_times": tts,
                "raw_delays": delays,
            }

    with open(series_dir / "series_4g_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


# =====================================================================
# MAIN
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description="Phase 4 Simulation Experiments")
    parser.add_argument("--workers", type=int, default=6, help="Worker count (default: 6)")
    parser.add_argument("--duration", type=float, default=900.0, help="Simulation duration (default: 900.0s)")
    parser.add_argument(
        "--series",
        nargs="+",
        default=["4a", "4d", "4g"],
        help="Which series to execute (4a, 4d, 4g)",
    )
    args = parser.parse_args()

    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    t_global_0 = time.time()
    logger.info("======================================================================")
    logger.info("STARTING PHASE 4 SIMULATION EXPERIMENTS")
    logger.info(f"Workers: {args.workers} | Duration: {args.duration}s | Series: {args.series}")
    logger.info("======================================================================")

    if "4a" in args.series:
        logger.info("\n>>> EXECUTING SERIES 4A: SAFETY SHIELD ABLATION <<<")
        run_series_4a_safety_shield(workers=args.workers, duration=args.duration)

    if "4d" in args.series:
        logger.info("\n>>> EXECUTING SERIES 4D: MATCHED TRANSIT SIGNAL PRIORITY <<<")
        run_series_4d_transit_priority(workers=args.workers, duration=args.duration)

    if "4g" in args.series:
        logger.info("\n>>> EXECUTING SERIES 4G: INTER-JUNCTION COMMUNICATION ABLATION <<<")
        run_series_4g_communication(workers=args.workers, duration=args.duration)

    t_total = time.time() - t_global_0
    logger.info("======================================================================")
    logger.info(f"ALL REQUESTED PHASE 4 SIMULATIONS FINISHED IN {t_total:.1f}s ({t_total/60:.2f} min)")
    logger.info("======================================================================")


if __name__ == "__main__":
    main()
