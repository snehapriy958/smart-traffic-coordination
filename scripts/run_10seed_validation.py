"""
scripts/run_10seed_validation.py

Autonomous, Isolated, and Reproducible 10-Seed Evaluation Runner:
- Evaluates 4 signal controllers:
  1. Fixed-Time Baseline ('baseline')
  2. Coordinated Adaptive ('coordinated')
  3. Trained MARL DQN ('marl_dqn')
  4. Trained MARL PPO ('marl_ppo')
- Evaluates seeds 1 through 10 (40 simulation runs total).
- 900-second horizon per run (covering Peak 0-300s, Shoulder 300-600s, Off-Peak 600-900s).
- Isolated outputs under outputs/validation/10seeds/ with individual per-run JSON records.
- Comprehensive metric collection: travel time, speed, delay, queue, emissions, phase switches,
  RL decision distributions (KEEP, SWITCH, EXTEND), and anti-starvation preemption logs.
- Paired statistical hypothesis tests (Student's t-test, Wilcoxon signed-rank, 95% CIs).
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

import numpy as np
from scipy import stats
import traci

from backend.config import SUMO_CONFIG_PATH
from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation
from traffic_service.state_extractor import (
    FUEL_DENSITY_MG_PER_LITER,
    FUEL_DENSITY_MG_PER_ML,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("10SeedValidation")

# Network edges for Hosur arterial corridor (J1 -> J2 -> J3)
CORRIDOR_EDGES = [
    "172853382#2", "172853382#3", "464465165#0", "92196679#0",
    "1148717038#0", "40696223#1", "-148697299", "-744783934",
]
ENTRY_EDGE = "172853382#2"
EXIT_EDGE = "40696223#1"

REGIMES = [
    ("peak", 0, 300),
    ("shoulder", 300, 600),
    ("off_peak", 600, 900),
]


def run_single_simulation(
    mode: str,
    seed: int,
    duration: int = 900,
    output_dir: Path = Path("outputs/validation/10seeds"),
) -> Dict[str, Any]:
    """Runs a single 900s simulation and records complete metrics."""
    logger.info(f"==> Launching [{mode.upper()}] on Seed {seed} for {duration}s...")
    start_wall = time.time()

    runs_dir = output_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_file = runs_dir / f"run_{mode}_seed{seed}.json"

    # Tracking structures
    corridor_entry_times: Dict[str, float] = {}
    corridor_travel_times: List[Tuple[float, float]] = []
    all_departed: List[Tuple[float, str]] = []
    all_arrived: List[Tuple[float, str]] = []
    veh_departure_times: Dict[str, float] = {}
    net_travel_times: List[Tuple[float, float]] = []
    step_records: List[Dict[str, Any]] = []

    # Decision and phase switch tracking
    decisions_by_j: Dict[str, List[Dict[str, Any]]] = {"J1": [], "J2": [], "J3": []}
    phase_switches_by_j: Dict[str, int] = {"J1": 0, "J2": 0, "J3": 0}
    last_phase_by_j: Dict[str, Optional[int]] = {"J1": None, "J2": None, "J3": None}

    sim = MultiIntersectionSimulation(
        sumocfg_path=SUMO_CONFIG_PATH,
        mode=mode,
        step_length=1.0,
        gui=False,
    )

    # Intercept decide method for MARL controllers to log every decision
    if sim.marl_controller is not None:
        orig_decide = sim.marl_controller.decide

        def wrapped_decide(ai_obs, sim_time, eval_mode=True):
            res = orig_decide(ai_obs, sim_time, eval_mode=eval_mode)
            for j_id, d in res.items():
                decisions_by_j[j_id].append({
                    "time": sim_time,
                    "action": d.get("action"),
                    "action_name": d.get("action_name"),
                    "q_value": d.get("q_value"),
                    "starvation_prevention": d.get("is_starvation_prevention", False),
                })
            return res

        sim.marl_controller.decide = wrapped_decide

    try:
        sim.start(seed=seed)
        current_time = 0.0

        while current_time < duration:
            sim.step()
            current_time = sim.sumo_manager.get_time()
            t = int(current_time)

            # 1. TraCI Departures & Arrivals
            dep_ids = traci.simulation.getDepartedIDList()
            arr_ids = traci.simulation.getArrivedIDList()

            for vid in dep_ids:
                all_departed.append((t, vid))
                veh_departure_times[vid] = t

            for vid in arr_ids:
                all_arrived.append((t, vid))
                if vid in veh_departure_times:
                    net_travel_times.append((t, max(1.0, t - veh_departure_times[vid])))

            # 2. Corridor trip tracking (J1 -> J2 -> J3)
            try:
                entry_vehs = traci.edge.getLastStepVehicleIDs(ENTRY_EDGE)
                exit_vehs = traci.edge.getLastStepVehicleIDs(EXIT_EDGE)
            except Exception:
                entry_vehs, exit_vehs = [], []

            for vid in entry_vehs:
                if vid not in corridor_entry_times:
                    corridor_entry_times[vid] = t
            for vid in exit_vehs:
                if vid in corridor_entry_times:
                    ent_t = corridor_entry_times.pop(vid)
                    corridor_travel_times.append((t, max(1.0, t - ent_t)))

            # 3. Emissions accumulation
            step_co2 = 0.0
            step_nox = 0.0
            step_fuel_mg = 0.0
            for edge_id in CORRIDOR_EDGES:
                try:
                    step_co2 += traci.edge.getCO2Emission(edge_id)
                    step_nox += traci.edge.getNOxEmission(edge_id)
                    step_fuel_mg += traci.edge.getFuelConsumption(edge_id)
                except Exception:
                    pass

            # 4. State extraction & phase switch counting
            states = sim.get_states(current_time)
            for j_id, ctrl in sim.controllers.items():
                curr_p = ctrl.get_phase()
                if last_phase_by_j[j_id] is not None and curr_p != last_phase_by_j[j_id]:
                    phase_switches_by_j[j_id] += 1
                last_phase_by_j[j_id] = curr_p

            j1_q = states["J1"].total_queue if "J1" in states else 0
            j2_q = states["J2"].total_queue if "J2" in states else 0
            j3_q = states["J3"].total_queue if "J3" in states else 0
            total_corridor_q = j1_q + j2_q + j3_q

            total_wait = sum(s.total_waiting_time for s in states.values())
            speeds = [s.average_speed_kmh for s in states.values() if s.vehicle_count > 0]
            avg_speed = (sum(speeds) / len(speeds)) if speeds else 0.0
            active_count = traci.vehicle.getIDCount()

            step_records.append({
                "time": t,
                "active_vehicles": active_count,
                "j1_q": j1_q,
                "j2_q": j2_q,
                "j3_q": j3_q,
                "corridor_q": total_corridor_q,
                "total_wait": total_wait,
                "avg_speed": avg_speed,
                "co2_mg": step_co2,
                "nox_mg": step_nox,
                "fuel_mg": step_fuel_mg,
            })

    finally:
        sim.close()

    wall_duration = time.time() - start_wall

    # Extract Starvation Events
    starvation_events = []
    if sim.marl_controller is not None and hasattr(sim.marl_controller, "starvation_tracker"):
        for e in sim.marl_controller.starvation_tracker.events:
            starvation_events.append({
                "timestamp": e.timestamp,
                "junction_id": e.junction_id,
                "starved_approach": e.starved_approach,
                "red_duration_s": e.red_duration_s,
                "queue_count": e.queue_count,
                "current_phase": e.current_phase,
                "target_phase": e.target_phase,
                "action_enforced": e.action_enforced,
            })

    # Summary helper
    def summarize_interval(t_start: int, t_end: int) -> Dict[str, Any]:
        records = [r for r in step_records if t_start < r["time"] <= t_end]
        if not records:
            return {}

        dep = [v for t, v in all_departed if t_start < t <= t_end]
        arr = [v for t, v in all_arrived if t_start < t <= t_end]
        corridor_completed = [dur for t, dur in corridor_travel_times if t_start < t <= t_end]
        net_completed = [dur for t, dur in net_travel_times if t_start < t <= t_end]

        queues = [r["corridor_q"] for r in records]
        mean_q = sum(queues) / len(queues) if queues else 0.0
        max_q = max(queues) if queues else 0

        speeds = [r["avg_speed"] for r in records if r["active_vehicles"] > 0]
        mean_spd = sum(speeds) / len(speeds) if speeds else 0.0

        waits = [r["total_wait"] for r in records]
        mean_wait = sum(waits) / len(waits) if waits else 0.0
        cum_delay = sum(queues) * 1.0

        tot_co2_kg = sum(r["co2_mg"] for r in records) / 1_000_000.0
        tot_fuel_l = sum(r["fuel_mg"] for r in records) / FUEL_DENSITY_MG_PER_LITER

        unfinished = records[-1]["active_vehicles"]

        avg_corridor_tt = (
            sum(corridor_completed) / len(corridor_completed) if corridor_completed else None
        )
        avg_net_tt = (
            sum(net_completed) / len(net_completed) if net_completed else None
        )

        return {
            "interval": [t_start, t_end],
            "departed": len(dep),
            "arrived": len(arr),
            "corridor_trips": len(corridor_completed),
            "unfinished": unfinished,
            "avg_corridor_travel_time_s": round(avg_corridor_tt, 2) if avg_corridor_tt else None,
            "avg_net_travel_time_s": round(avg_net_tt, 2) if avg_net_tt else None,
            "avg_speed_kmh": round(mean_spd, 2),
            "avg_waiting_time_s": round(mean_wait, 2),
            "cumulative_delay_veh_s": round(cum_delay, 1),
            "avg_queue_veh": round(mean_q, 2),
            "max_queue_veh": int(max_q),
            "co2_kg": round(tot_co2_kg, 4),
            "fuel_liters": round(tot_fuel_l, 4),
        }

    # Action counts breakdown
    action_counts_by_j = {}
    for j_id in ["J1", "J2", "J3"]:
        acts = [d["action_name"] for d in decisions_by_j[j_id]]
        action_counts_by_j[j_id] = {
            "total_decisions": len(acts),
            "KEEP": acts.count("KEEP"),
            "SWITCH": acts.count("SWITCH"),
            "EXTEND": acts.count("EXTEND"),
        }

    result = {
        "mode": mode,
        "seed": seed,
        "duration_s": duration,
        "wall_time_s": round(wall_duration, 2),
        "status": "COMPLETED",
        "phase_switches": phase_switches_by_j,
        "action_counts": action_counts_by_j,
        "starvation_events_count": len(starvation_events),
        "starvation_events": starvation_events,
        "regimes": {
            "peak": summarize_interval(0, 300),
            "shoulder": summarize_interval(300, 600),
            "off_peak": summarize_interval(600, 900),
        },
        "full_900s": summarize_interval(0, 900),
    }

    with open(run_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    logger.info(
        f"==> [{mode.upper()} Seed {seed}] Completed in {wall_duration:.1f}s | "
        f"Corridor TT={result['full_900s']['avg_corridor_travel_time_s']}s | "
        f"Speed={result['full_900s']['avg_speed_kmh']}km/h | "
        f"Delay={result['full_900s']['cumulative_delay_veh_s']}veh-s | "
        f"StarvEvents={len(starvation_events)}"
    )
    return result


def compute_statistical_analysis(
    all_results: List[Dict[str, Any]],
    output_dir: Path,
) -> Dict[str, Any]:
    """Computes paired Student's t-test and Wilcoxon signed-rank analysis across 10 seeds."""
    by_mode = {}
    for r in all_results:
        m = r["mode"]
        s = r["seed"]
        if m not in by_mode:
            by_mode[m] = {}
        by_mode[m][s] = r["full_900s"]

    seeds = sorted(list(by_mode["baseline"].keys()))
    N = len(seeds)
    df = N - 1
    t_crit = float(stats.t.ppf(0.975, df=df))

    analysis = {
        "metadata": {
            "sample_size": N,
            "degrees_of_freedom": df,
            "t_critical_95pct": round(t_crit, 5),
            "seeds": seeds,
        },
        "descriptive_statistics": {},
        "paired_comparisons": {},
    }

    metrics = [
        ("avg_corridor_travel_time_s", "Corridor Travel Time (s)", True),
        ("avg_speed_kmh", "Corridor Speed (km/h)", False),
        ("cumulative_delay_veh_s", "Cumulative Delay (veh-s)", True),
        ("co2_kg", "CO2 Emissions (kg)", True),
        ("fuel_liters", "Fuel Consumption (L)", True),
    ]

    for m in ["baseline", "coordinated", "marl_dqn", "marl_ppo"]:
        if m not in by_mode:
            continue
        analysis["descriptive_statistics"][m] = {}
        for key, name, _ in metrics:
            vals = [by_mode[m][s][key] for s in seeds]
            mean_v = float(np.mean(vals))
            std_v = float(np.std(vals, ddof=1))
            se_v = std_v / math.sqrt(N)
            ci_low = mean_v - t_crit * se_v
            ci_high = mean_v + t_crit * se_v
            analysis["descriptive_statistics"][m][key] = {
                "name": name,
                "values": vals,
                "mean": round(mean_v, 4),
                "std": round(std_v, 4),
                "se": round(se_v, 4),
                "ci_95": [round(ci_low, 4), round(ci_high, 4)],
            }

    # Paired comparisons against baseline
    for m in ["coordinated", "marl_dqn", "marl_ppo"]:
        if m not in by_mode:
            continue
        analysis["paired_comparisons"][m] = {}
        for key, name, lower_is_better in metrics:
            base_vals = [by_mode["baseline"][s][key] for s in seeds]
            cand_vals = [by_mode[m][s][key] for s in seeds]

            diffs = [c - b for c, b in zip(cand_vals, base_vals)]
            pct_changes = [(c - b) / b * 100 for c, b in zip(cand_vals, base_vals)]

            mean_diff = float(np.mean(diffs))
            mean_pct = float(np.mean(pct_changes))
            std_diff = float(np.std(diffs, ddof=1))
            se_diff = std_diff / math.sqrt(N)

            t_res = stats.ttest_rel(cand_vals, base_vals)
            t_stat = float(t_res.statistic)
            p_val = float(t_res.pvalue)

            ci_low = mean_diff - t_crit * se_diff
            ci_high = mean_diff + t_crit * se_diff

            # Wilcoxon signed rank test
            try:
                w_res = stats.wilcoxon(cand_vals, base_vals, alternative="two-sided")
                w_stat = float(w_res.statistic)
                w_pval = float(w_res.pvalue)
            except Exception:
                w_stat, w_pval = None, None

            # Cohen's dz
            cohen_dz = abs(mean_diff) / std_diff if std_diff > 0 else 0.0

            # Determine improvement vs degradation
            if lower_is_better:
                improved = mean_diff < 0
            else:
                improved = mean_diff > 0

            analysis["paired_comparisons"][m][key] = {
                "metric_name": name,
                "paired_differences": [round(d, 4) for d in diffs],
                "mean_difference": round(mean_diff, 4),
                "mean_percentage_change": round(mean_pct, 2),
                "std_difference": round(std_diff, 4),
                "standard_error": round(se_diff, 4),
                "t_statistic": round(t_stat, 4),
                "p_value": p_val,
                "ci_95": [round(ci_low, 4), round(ci_high, 4)],
                "wilcoxon_stat": w_stat,
                "wilcoxon_p_value": w_pval,
                "cohen_dz": round(cohen_dz, 4),
                "significant_at_alpha_0_05": p_val < 0.05,
                "improved": improved,
            }

    stat_file = output_dir / "statistical_analysis.json"
    with open(stat_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    return analysis


def main():
    parser = argparse.ArgumentParser(description="Autonomous 10-Seed Traffic Validation")
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(1, 11)), help="Random seeds to evaluate")
    parser.add_argument("--controllers", nargs="+", default=["baseline", "coordinated", "marl_dqn", "marl_ppo"])
    parser.add_argument("--duration", type=int, default=900, help="Simulation duration in seconds")
    parser.add_argument("--output-dir", type=str, default="outputs/validation/10seeds")
    parser.add_argument("--force", action="store_true", help="Force rerun even if results exist")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Safety Check: Verify historical 3-seed benchmark is preserved
    hist_file = Path("outputs/validation/historical_3seeds/extended_eval_results.json")
    if not hist_file.exists():
        logger.error(f"SAFETY ERROR: Historical benchmark copy not found at {hist_file}!")
        sys.exit(1)
    logger.info(f"SAFETY CHECK: Historical benchmark preserved at {hist_file} (Untouched).")

    # 2. Execution Loop
    total_runs = len(args.controllers) * len(args.seeds)
    completed_runs = []
    failed_runs = []

    logger.info(f"Starting Extended Validation: {len(args.controllers)} controllers x {len(args.seeds)} seeds = {total_runs} runs.")

    for mode in args.controllers:
        for seed in args.seeds:
            run_file = runs_dir / f"run_{mode}_seed{seed}.json"

            # Check if already completed
            if run_file.exists() and not args.force:
                try:
                    with open(run_file, "r", encoding="utf-8") as f:
                        r = json.load(f)
                    if r.get("status") == "COMPLETED":
                        logger.info(f"Skipping already completed run: [{mode.upper()} Seed {seed}]")
                        completed_runs.append(r)
                        continue
                except Exception:
                    pass

            try:
                res = run_single_simulation(mode=mode, seed=seed, duration=args.duration, output_dir=out_dir)
                completed_runs.append(res)
            except Exception as exc:
                err_msg = f"Run FAILED: mode={mode}, seed={seed}, error={exc}"
                logger.error(err_msg)
                logger.error(traceback.format_exc())
                failed_entry = {
                    "mode": mode,
                    "seed": seed,
                    "status": "FAILED",
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                    "timestamp": time.time(),
                }
                failed_runs.append(failed_entry)
                with open(out_dir / "error_log.json", "w", encoding="utf-8") as f:
                    json.dump(failed_runs, f, indent=2)

    logger.info(f"Execution Completed: {len(completed_runs)} successful, {len(failed_runs)} failed.")

    # 3. Save Consolidated Summary
    summary_data = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_planned_runs": total_runs,
            "total_successful_runs": len(completed_runs),
            "total_failed_runs": len(failed_runs),
            "controllers": args.controllers,
            "seeds": args.seeds,
            "duration_s": args.duration,
        },
        "runs": completed_runs,
    }
    with open(out_dir / "eval_10seeds_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    # 4. Statistical Analysis
    if len(completed_runs) == total_runs:
        logger.info("Computing complete 10-seed paired statistical analysis...")
        analysis = compute_statistical_analysis(completed_runs, out_dir)
        logger.info("Statistical analysis saved to outputs/validation/10seeds/statistical_analysis.json")
    else:
        logger.warning(f"Partial results: {len(completed_runs)}/{total_runs} runs completed. Skipping full analysis.")


if __name__ == "__main__":
    main()
