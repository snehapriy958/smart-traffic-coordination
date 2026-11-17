"""
scripts/run_phase3_experiments.py

Master Phase 3 Experimentation Pipeline:
- Series 1: Travel-Time Reliability & Cross-Street Equity (8 controllers x 10 seeds = 80 runs)
- Series 2: Telemetry Non-Ideality: Dropouts & Packet Loss (4 controllers x 5 conditions x 6 seeds = 120 runs)
- Series 3: Physical Mid-Block Incident Stress Testing (8 controllers x 5 seeds = 40 runs)
- Series 4: Multi-Modal Transit Signal Priority (4 controllers x 12 seeds = 48 runs)

Total Phase 3 treatment runs = 288 runs.
All outputs are strictly isolated under `outputs/experiments/phase3/`.
"""

import argparse
from dataclasses import asdict
import json
import logging
import os
from pathlib import Path
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import SUMO_CONFIG_PATH
from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation
from traffic_service.resilience.detailed_collector import DetailedCorridorMetricsCollector
from traffic_service.resilience.noisy_extractor import (
    NoisyIntersectionStateExtractor,
    LossyCorridorCommunicationHub,
)
from traffic_service.resilience.incident_manager import MidBlockIncidentManager
from traffic_service.resilience.transit_priority import TransitSignalPriorityManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("phase3_experiments")

BASE_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase3"

ALL_CONTROLLERS = [
    "baseline",
    "coordinated",
    "webster",
    "nema",
    "max_pressure",
    "marl_dqn",
    "marl_ppo",
    "marl_mappo",
]

SUBSET_CONTROLLERS = [
    "coordinated",
    "webster",
    "nema",
    "marl_mappo",
]


# =====================================================================
# WORKER EXECUTION FUNCTION
# =====================================================================

def execute_simulation_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a single parametrized Phase 3 simulation run.
    Safely intercepts TraCI observations and handles telemetry/incident/TSP layers.
    """
    series = task["series"]
    controller = task["controller"]
    seed = task["seed"]
    duration = task.get("duration", 900.0)
    out_file = Path(task["out_file"])

    # Check cache
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
    label = f"p3_{series}_{controller}_{seed}_{os.getpid()}_{int(time.time()*1000)%10000}"

    try:
        sim = MultiIntersectionSimulation(
            sumocfg_path=SUMO_CONFIG_PATH,
            mode=controller,
            step_length=1.0,
            gui=False,
            label=label,
        )

        # 1. Attach Detailed Metrics Collector
        detailed_collector = DetailedCorridorMetricsCollector(
            entry_edge="172853382#2",
            exit_edge="40696223#1",
            step_length=1.0,
        )
        sim.metrics_collector = detailed_collector

        # 2. Setup Telemetry Non-Ideality if requested
        p_drop = float(task.get("p_drop", 0.0))
        p_loss = float(task.get("p_loss", 0.0))

        if p_drop > 0.0:
            sim.extractors = {
                j_id: NoisyIntersectionStateExtractor(
                    base_extractor=ext,
                    p_drop=p_drop,
                    seed=seed + idx * 100,
                )
                for idx, (j_id, ext) in enumerate(sim.extractors.items())
            }

        if p_loss > 0.0:
            lossy_hub = LossyCorridorCommunicationHub(
                corridor_sequence=["J1", "J2", "J3"],
                p_loss=p_loss,
                seed=seed + 777,
            )
            sim.hub = lossy_hub
            sim.emergency_coordinator.communication_hub = lossy_hub
            if sim.marl_controller is not None:
                sim.marl_controller.communication_hub = lossy_hub

        # 3. Setup Incident Manager if requested
        enable_incident = bool(task.get("enable_incident", False))
        incident_mgr: Optional[MidBlockIncidentManager] = None
        if enable_incident:
            incident_mgr = MidBlockIncidentManager(
                edge_id="172853382#3",
                target_lane_index=0,
                start_time=300.0,
                end_time=600.0,
                normal_speed=16.67,
            )

        # 4. Setup Transit Signal Priority Manager if requested
        enable_tsp = bool(task.get("enable_tsp", False))
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

        # 5. Execute Simulation Loop
        sim.start(seed=seed)
        try:
            while sim.sumo_manager.get_time() < duration:
                states, _ = sim.step()
                sim_time = sim.sumo_manager.get_time()

                if incident_mgr is not None:
                    incident_mgr.update(sim_time, states)

                if tsp_mgr is not None:
                    tsp_mgr.update(sim_time)

            t_elapsed = time.time() - t_start
            emergency_completed = sim.emergency_coordinator.metrics.completed
            emergency_dur = (
                sim.emergency_coordinator.metrics.total_traversal_duration
                if emergency_completed
                else None
            )

            # Extract detailed summary
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
            }

            # Append series-specific extensions
            if p_drop > 0.0 or p_loss > 0.0:
                record["degradation_params"] = {
                    "p_drop": p_drop,
                    "p_loss": p_loss,
                    "detector_dropped_obs": sum(
                        getattr(ext, "dropped_observations", 0) for ext in sim.extractors.values()
                    ),
                    "detector_stale_faults": sum(
                        getattr(ext, "stale_fault_count", 0) for ext in sim.extractors.values()
                    ),
                    "comm_packets_dropped": getattr(sim.hub, "total_packets_dropped", 0),
                    "comm_stale_rejected": getattr(sim.hub, "stale_packets_rejected", 0),
                }

            if incident_mgr is not None:
                inc_summary = incident_mgr.compute_summary()
                record["incident"] = asdict(inc_summary)

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
        return {
            "series": series,
            "controller": controller,
            "seed": seed,
            "completed": False,
            "error": str(exc),
        }


# =====================================================================
# SERIES GENERATION & EXECUTION
# =====================================================================

def run_series_1_reliability_equity(workers: int, duration: float = 900.0) -> Dict[str, Any]:
    """Series 1: 8 controllers x 10 seeds (80 runs)."""
    out_dir = BASE_OUTPUT_DIR / "reliability_equity"
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== STARTING SERIES 1: RELIABILITY & CROSS-STREET EQUITY (80 RUNS) ===")

    tasks = []
    for ctrl in ALL_CONTROLLERS:
        for seed in range(1, 11):
            tasks.append({
                "series": "reliability_equity",
                "controller": ctrl,
                "seed": seed,
                "duration": duration,
                "out_file": str(out_dir / f"{ctrl}_seed_{seed}.json"),
            })

    results = run_tasks_in_parallel(tasks, workers)
    summary = aggregate_series_1_summary(results, duration)
    summary_path = out_dir / "reliability_equity_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved Series 1 summary to {summary_path}")
    return summary


def run_series_2_telemetry_degradation(workers: int, duration: float = 900.0) -> Dict[str, Any]:
    """Series 2: 4 controllers x 5 conditions x 6 seeds (120 runs)."""
    out_dir = BASE_OUTPUT_DIR / "telemetry_degradation"
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== STARTING SERIES 2: TELEMETRY NON-IDEALITY (120 RUNS) ===")

    tasks = []
    # 1. Detector dropouts: 0.05, 0.10, 0.20
    for p_drop in [0.05, 0.10, 0.20]:
        tag = f"drop_{int(p_drop*100):02d}"
        for ctrl in SUBSET_CONTROLLERS:
            for seed in range(1, 7):
                tasks.append({
                    "series": "telemetry_degradation",
                    "controller": ctrl,
                    "seed": seed,
                    "duration": duration,
                    "p_drop": p_drop,
                    "p_loss": 0.0,
                    "out_file": str(out_dir / f"{tag}_{ctrl}_seed_{seed}.json"),
                })

    # 2. Inter-intersection packet loss: 0.05, 0.15
    for p_loss in [0.05, 0.15]:
        tag = f"loss_{int(p_loss*100):02d}"
        for ctrl in SUBSET_CONTROLLERS:
            for seed in range(1, 7):
                tasks.append({
                    "series": "telemetry_degradation",
                    "controller": ctrl,
                    "seed": seed,
                    "duration": duration,
                    "p_drop": 0.0,
                    "p_loss": p_loss,
                    "out_file": str(out_dir / f"{tag}_{ctrl}_seed_{seed}.json"),
                })

    results = run_tasks_in_parallel(tasks, workers)
    summary = aggregate_series_2_summary(results, duration)
    summary_path = out_dir / "telemetry_degradation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved Series 2 summary to {summary_path}")
    return summary


def run_series_3_incident_stress(workers: int, duration: float = 900.0) -> Dict[str, Any]:
    """Series 3: 8 controllers x 5 seeds with mid-block incident (40 runs)."""
    out_dir = BASE_OUTPUT_DIR / "incident_stress"
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== STARTING SERIES 3: PHYSICAL INCIDENT STRESS TESTING (40 RUNS) ===")

    tasks = []
    for ctrl in ALL_CONTROLLERS:
        for seed in range(1, 6):
            tasks.append({
                "series": "incident_stress",
                "controller": ctrl,
                "seed": seed,
                "duration": duration,
                "enable_incident": True,
                "out_file": str(out_dir / f"{ctrl}_seed_{seed}.json"),
            })

    results = run_tasks_in_parallel(tasks, workers)
    summary = aggregate_series_3_summary(results, duration)
    summary_path = out_dir / "incident_stress_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved Series 3 summary to {summary_path}")
    return summary


def run_series_4_transit_priority(workers: int, duration: float = 900.0) -> Dict[str, Any]:
    """Series 4: 4 controllers x 12 seeds with Transit Signal Priority (48 runs)."""
    out_dir = BASE_OUTPUT_DIR / "transit_priority"
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== STARTING SERIES 4: MULTI-MODAL TRANSIT SIGNAL PRIORITY (48 RUNS) ===")

    tasks = []
    for ctrl in SUBSET_CONTROLLERS:
        for seed in range(1, 13):
            tasks.append({
                "series": "transit_priority",
                "controller": ctrl,
                "seed": seed,
                "duration": duration,
                "enable_tsp": True,
                "out_file": str(out_dir / f"tsp_{ctrl}_seed_{seed}.json"),
            })

    results = run_tasks_in_parallel(tasks, workers)
    summary = aggregate_series_4_summary(results, duration)
    summary_path = out_dir / "transit_priority_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved Series 4 summary to {summary_path}")
    return summary


# =====================================================================
# PARALLEL RUNNER & AGGREGATORS
# =====================================================================

def run_tasks_in_parallel(tasks: List[Dict[str, Any]], workers: int) -> List[Dict[str, Any]]:
    """Runs a batch of simulation tasks using ProcessPoolExecutor."""
    results: List[Dict[str, Any]] = []
    total = len(tasks)
    t0 = time.time()
    completed = 0

    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_map = {executor.submit(execute_simulation_task, t): t for t in tasks}
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


def aggregate_series_1_summary(results: List[Dict[str, Any]], duration: float) -> Dict[str, Any]:
    """Synthesizes reliability and equity statistics across the 8 controllers."""
    summary: Dict[str, Any] = {
        "metadata": {
            "experiment": "Series 1: Reliability & Cross-Street Equity",
            "duration_s": duration,
            "controllers": ALL_CONTROLLERS,
            "seeds": list(range(1, 11)),
            "total_runs": len(results),
            "completed_runs": sum(1 for r in results if r.get("completed")),
        },
        "per_controller": {},
    }

    for ctrl in ALL_CONTROLLERS:
        runs = [r for r in results if r.get("controller") == ctrl and r.get("completed")]
        runs.sort(key=lambda r: r["seed"])
        if not runs:
            continue

        tts = [r["mean_corridor_travel_time_s"] for r in runs if r["mean_corridor_travel_time_s"] is not None]
        ptis = [r["reliability"]["planning_time_index_pti"] for r in runs]
        bis = [r["reliability"]["buffer_index_bi_percent"] for r in runs]
        ginis = [r["equity"].get("cross_street_delay_gini", r["equity"].get("approach_delay_gini_coefficient", 0.0)) for r in runs]
        vhds = [r["multi_modal"]["vehicle_hours_of_delay_vhd"] for r in runs]
        phds = [r["multi_modal"]["passenger_hours_of_delay_phd"] for r in runs]
        delays = [r["cumulative_delay_veh_s"] for r in runs]
        queues = [r["mean_corridor_queue"] for r in runs]
        speeds = [r["mean_corridor_speed_kmh"] for r in runs]
        co2s = [r["total_co2_kg"] for r in runs]
        fuels = [r["total_fuel_liters"] for r in runs]

        summary["per_controller"][ctrl] = {
            "runs_completed": len(runs),
            "travel_time_mean_s": round(float(np.mean(tts)), 2),
            "travel_time_std_s": round(float(np.std(tts, ddof=1)), 2) if len(tts) > 1 else 0.0,
            "planning_time_index_pti": round(float(np.mean(ptis)), 4),
            "buffer_index_bi_percent": round(float(np.mean(bis)), 2),
            "cross_street_delay_gini": round(float(np.mean(ginis)), 4),
            "cross_street_delay_gini_std": round(float(np.std(ginis, ddof=1)), 4) if len(ginis) > 1 else 0.0,
            "vehicle_hours_of_delay_vhd": round(float(np.mean(vhds)), 3),
            "passenger_hours_of_delay_phd": round(float(np.mean(phds)), 3),
            "cumulative_delay_veh_s": round(float(np.mean(delays)), 2),
            "mean_corridor_queue": round(float(np.mean(queues)), 2),
            "mean_corridor_speed_kmh": round(float(np.mean(speeds)), 2),
            "total_co2_kg": round(float(np.mean(co2s)), 2),
            "total_fuel_liters": round(float(np.mean(fuels)), 2),
            "raw_ptis": ptis,
            "raw_bis": bis,
            "raw_ginis": ginis,
            "raw_phds": phds,
            "raw_travel_times": tts,
        }
    return summary


def aggregate_series_2_summary(results: List[Dict[str, Any]], duration: float) -> Dict[str, Any]:
    """Synthesizes degradation trends across dropouts and packet losses."""
    summary: Dict[str, Any] = {
        "metadata": {
            "experiment": "Series 2: Telemetry Non-Ideality",
            "duration_s": duration,
            "controllers": SUBSET_CONTROLLERS,
            "total_runs": len(results),
            "completed_runs": sum(1 for r in results if r.get("completed")),
        },
        "detector_dropouts": {},
        "packet_losses": {},
    }

    # Group by condition
    for p_drop in [0.05, 0.10, 0.20]:
        tag = f"drop_{int(p_drop*100):02d}"
        summary["detector_dropouts"][tag] = {}
        for ctrl in SUBSET_CONTROLLERS:
            runs = [
                r for r in results
                if r.get("controller") == ctrl
                and r.get("degradation_params", {}).get("p_drop") == p_drop
                and r.get("completed")
            ]
            if runs:
                tts = [r["mean_corridor_travel_time_s"] for r in runs if r["mean_corridor_travel_time_s"] is not None]
                delays = [r["cumulative_delay_veh_s"] for r in runs]
                summary["detector_dropouts"][tag][ctrl] = {
                    "travel_time_mean_s": round(float(np.mean(tts)), 2) if tts else None,
                    "cumulative_delay_veh_s": round(float(np.mean(delays)), 2),
                    "mean_queue": round(float(np.mean([r["mean_corridor_queue"] for r in runs])), 2),
                    "dropped_obs_mean": round(float(np.mean([r["degradation_params"]["detector_dropped_obs"] for r in runs])), 1),
                    "stale_faults_mean": round(float(np.mean([r["degradation_params"]["detector_stale_faults"] for r in runs])), 1),
                }

    for p_loss in [0.05, 0.15]:
        tag = f"loss_{int(p_loss*100):02d}"
        summary["packet_losses"][tag] = {}
        for ctrl in SUBSET_CONTROLLERS:
            runs = [
                r for r in results
                if r.get("controller") == ctrl
                and r.get("degradation_params", {}).get("p_loss") == p_loss
                and r.get("completed")
            ]
            if runs:
                tts = [r["mean_corridor_travel_time_s"] for r in runs if r["mean_corridor_travel_time_s"] is not None]
                delays = [r["cumulative_delay_veh_s"] for r in runs]
                summary["packet_losses"][tag][ctrl] = {
                    "travel_time_mean_s": round(float(np.mean(tts)), 2) if tts else None,
                    "cumulative_delay_veh_s": round(float(np.mean(delays)), 2),
                    "mean_queue": round(float(np.mean([r["mean_corridor_queue"] for r in runs])), 2),
                    "dropped_packets_mean": round(float(np.mean([r["degradation_params"]["comm_packets_dropped"] for r in runs])), 1),
                }
    return summary


def aggregate_series_3_summary(results: List[Dict[str, Any]], duration: float) -> Dict[str, Any]:
    """Synthesizes physical incident stress test and recovery dynamics."""
    summary: Dict[str, Any] = {
        "metadata": {
            "experiment": "Series 3: Physical Incident Stress Testing",
            "duration_s": duration,
            "incident_window_s": [300.0, 600.0],
            "connector_edge": "172853382#3",
            "controllers": ALL_CONTROLLERS,
            "total_runs": len(results),
            "completed_runs": sum(1 for r in results if r.get("completed")),
        },
        "per_controller": {},
    }

    for ctrl in ALL_CONTROLLERS:
        runs = [r for r in results if r.get("controller") == ctrl and r.get("completed")]
        if not runs:
            continue

        pre_qs = [r["incident"]["pre_incident_mean_queue"] for r in runs]
        during_qs = [r["incident"]["during_incident_mean_queue"] for r in runs]
        post_qs = [r["incident"]["post_incident_mean_queue"] for r in runs]
        peak_qs = [r["incident"]["peak_queue_during_incident"] for r in runs]
        q_ratios = [r["incident"]["queue_increase_ratio"] for r in runs]
        rec_times = [r["incident"]["recovery_time_s"] for r in runs if r["incident"]["recovery_time_s"] is not None]
        spillbacks = [1 if r["incident"]["spillback_detected_at_j1"] else 0 for r in runs]
        delays = [r["cumulative_delay_veh_s"] for r in runs]

        summary["per_controller"][ctrl] = {
            "runs": len(runs),
            "pre_incident_mean_queue": round(float(np.mean(pre_qs)), 2),
            "during_incident_mean_queue": round(float(np.mean(during_qs)), 2),
            "post_incident_mean_queue": round(float(np.mean(post_qs)), 2),
            "peak_queue_mean": round(float(np.mean(peak_qs)), 1),
            "queue_increase_ratio_mean": round(float(np.mean(q_ratios)), 2),
            "recovery_time_mean_s": round(float(np.mean(rec_times)), 1) if rec_times else None,
            "recovery_success_rate": round(len(rec_times) / len(runs), 2),
            "spillback_rate_at_j1": round(sum(spillbacks) / len(runs), 2),
            "cumulative_delay_veh_s": round(float(np.mean(delays)), 2),
        }
    return summary


def aggregate_series_4_summary(results: List[Dict[str, Any]], duration: float) -> Dict[str, Any]:
    """Synthesizes Transit Signal Priority performance and modal shift benefits."""
    summary: Dict[str, Any] = {
        "metadata": {
            "experiment": "Series 4: Multi-Modal Transit Signal Priority",
            "duration_s": duration,
            "controllers": SUBSET_CONTROLLERS,
            "seeds": list(range(1, 13)),
            "total_runs": len(results),
            "completed_runs": sum(1 for r in results if r.get("completed")),
        },
        "per_controller": {},
    }

    for ctrl in SUBSET_CONTROLLERS:
        runs = [r for r in results if r.get("controller") == ctrl and r.get("completed")]
        if not runs:
            continue

        tts = [r["mean_corridor_travel_time_s"] for r in runs if r["mean_corridor_travel_time_s"] is not None]
        delays = [r["cumulative_delay_veh_s"] for r in runs]
        phds = [r["multi_modal"]["passenger_hours_of_delay_phd"] for r in runs]
        tsp_reqs = [r["transit_priority"]["total_requests"] for r in runs]
        tsp_grants = [r["transit_priority"]["granted_requests"] for r in runs]
        tsp_times = [r["transit_priority"]["total_extended_time_s"] for r in runs]
        buses_assisted = [len(r["transit_priority"]["buses_assisted"]) for r in runs]

        summary["per_controller"][ctrl] = {
            "runs": len(runs),
            "mean_corridor_travel_time_s": round(float(np.mean(tts)), 2) if tts else None,
            "cumulative_delay_veh_s": round(float(np.mean(delays)), 2),
            "passenger_hours_of_delay_phd": round(float(np.mean(phds)), 3),
            "tsp_requests_mean": round(float(np.mean(tsp_reqs)), 1),
            "tsp_grants_mean": round(float(np.mean(tsp_grants)), 1),
            "tsp_grant_rate": round(float(np.mean([g / max(1, r) for g, r in zip(tsp_grants, tsp_reqs)])), 4),
            "tsp_total_extended_time_mean_s": round(float(np.mean(tsp_times)), 1),
            "buses_assisted_mean": round(float(np.mean(buses_assisted)), 1),
        }
    return summary


# =====================================================================
# MAIN ENTRYPOINT
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description="Phase 3 Master Experimentation Suite")
    parser.add_argument("--workers", type=int, default=6, help="Parallel worker processes (default: 6)")
    parser.add_argument("--duration", type=float, default=900.0, help="Simulation duration in seconds (default: 900.0)")
    parser.add_argument(
        "--series",
        nargs="+",
        type=int,
        default=[1, 2, 3, 4],
        help="Which experiment series to run (1: Reliability/Equity, 2: Telemetry, 3: Incident, 4: TSP)",
    )
    args = parser.parse_args()

    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    t_global_start = time.time()
    logger.info("======================================================================")
    logger.info("PHASE 3 MASTER EXPERIMENT EXECUTION PIPELINE")
    logger.info(f"Workers: {args.workers} | Duration: {args.duration}s | Series: {args.series}")
    logger.info("======================================================================")

    if 1 in args.series:
        run_series_1_reliability_equity(workers=args.workers, duration=args.duration)

    if 2 in args.series:
        run_series_2_telemetry_degradation(workers=args.workers, duration=args.duration)

    if 3 in args.series:
        run_series_3_incident_stress(workers=args.workers, duration=args.duration)

    if 4 in args.series:
        run_series_4_transit_priority(workers=args.workers, duration=args.duration)

    t_global_elapsed = time.time() - t_global_start
    logger.info("======================================================================")
    logger.info(f"ALL SELECTED PHASE 3 EXPERIMENTS COMPLETE IN {t_global_elapsed:.1f}s ({t_global_elapsed/60:.2f} min)")
    logger.info("======================================================================")


if __name__ == "__main__":
    main()
