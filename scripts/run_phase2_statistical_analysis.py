"""
scripts/run_phase2_statistical_analysis.py

Rigorous statistical analysis of the 30-seed benchmark across 8 controllers:
1. Fixed-Time Baseline
2. Coordinated Adaptive
3. Webster Optimum Fixed-Time
4. NEMA Actuated TS 2
5. Varaiya Max-Pressure
6. Dueling Double-DQN
7. Independent PPO
8. Multi-Agent PPO (MAPPO)

Calculates:
- Parametric: Mean, Sample Std (ddof=1), 95% CI (Student's t, df=29)
- Non-parametric: Median, IQR, Min, Max
- Paired Hypothesis Tests vs. Baseline:
  - Paired t-test (two-sided, df=29)
  - Wilcoxon signed-rank test (two-sided)
  - Cohen's d_z effect size (paired)
  - Bonferroni-corrected alpha (0.05 / 7 = 0.00714)
- Outputs to `outputs/experiments/phase2_analysis/statistical_analysis_30seeds.json`
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
from scipy import stats

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("stat_analysis_30seeds")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase2_30seeds"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase2_analysis"

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

METRICS = [
    ("mean_corridor_travel_time_s", "Travel Time (s)", True),         # lower is better
    ("cumulative_delay_veh_s", "Cumulative Delay (veh-s)", True),     # lower is better
    ("mean_corridor_queue", "Mean Queue (veh)", True),                # lower is better
    ("mean_corridor_speed_kmh", "Mean Speed (km/h)", False),          # higher is better
    ("total_corridor_trips_completed", "Completed Trips", False),     # higher is better
    ("total_co2_kg", "CO2 Emissions (kg)", True),                     # lower is better
    ("total_fuel_liters", "Fuel Consumption (L)", True),              # lower is better
]


def compute_descriptive_stats(values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    arr = np.array(values, dtype=np.float64)
    n = len(arr)
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    se = std / np.sqrt(n) if n > 0 else 0.0
    median = float(np.median(arr))
    q25 = float(np.percentile(arr, 25))
    q75 = float(np.percentile(arr, 75))
    iqr = q75 - q25
    min_v = float(np.min(arr))
    max_v = float(np.max(arr))

    # 95% Confidence Interval using Student's t
    if n > 1:
        t_crit = stats.t.ppf(1.0 - alpha / 2.0, df=n - 1)
        ci_lower = float(mean - t_crit * se)
        ci_upper = float(mean + t_crit * se)
    else:
        ci_lower = mean
        ci_upper = mean

    return {
        "n": n,
        "mean": round(mean, 3),
        "std": round(std, 3),
        "se": round(se, 3),
        "median": round(median, 3),
        "q25": round(q25, 3),
        "q75": round(q75, 3),
        "iqr": round(iqr, 3),
        "min": round(min_v, 3),
        "max": round(max_v, 3),
        "ci_95": [round(ci_lower, 3), round(ci_upper, 3)],
    }


def compute_paired_comparison(
    baseline_vals: List[float],
    candidate_vals: List[float],
    lower_is_better: bool = True,
    alpha_family: float = 0.05,
    num_comparisons: int = 7,
) -> Dict[str, Any]:
    b_arr = np.array(baseline_vals, dtype=np.float64)
    c_arr = np.array(candidate_vals, dtype=np.float64)
    n = len(b_arr)

    # Difference vector: baseline - candidate
    diff = b_arr - c_arr
    mean_diff = float(np.mean(diff))
    std_diff = float(np.std(diff, ddof=1)) if n > 1 else 0.0

    # Paired t-test
    ttest_res = stats.ttest_rel(b_arr, c_arr)
    t_stat = float(ttest_res.statistic)
    p_t = float(ttest_res.pvalue)

    # Wilcoxon signed-rank test
    try:
        wilc_res = stats.wilcoxon(b_arr, c_arr, alternative="two-sided")
        w_stat = float(wilc_res.statistic)
        p_w = float(wilc_res.pvalue)
    except Exception:
        w_stat = None
        p_w = None

    # Cohen's d_z for paired samples: mean(diff) / std(diff)
    if std_diff > 1e-9:
        d_z = float(mean_diff / std_diff)
    else:
        d_z = 0.0

    # Percent improvement relative to baseline
    mean_b = float(np.mean(b_arr))
    if abs(mean_b) > 1e-9:
        if lower_is_better:
            pct_imp = float((mean_b - np.mean(c_arr)) / mean_b * 100.0)
        else:
            pct_imp = float((np.mean(c_arr) - mean_b) / mean_b * 100.0)
    else:
        pct_imp = 0.0

    alpha_bonf = alpha_family / num_comparisons
    sig_bonf = bool(p_t < alpha_bonf)

    return {
        "n_pairs": n,
        "mean_difference": round(mean_diff, 3),
        "std_difference": round(std_diff, 3),
        "percent_improvement": round(pct_imp, 2),
        "paired_t_test": {
            "t_statistic": round(t_stat, 4),
            "p_value": p_t,
            "df": n - 1,
            "significant_at_0_05": bool(p_t < 0.05),
            "significant_bonferroni": sig_bonf,
        },
        "wilcoxon_test": {
            "w_statistic": round(w_stat, 4) if w_stat is not None else None,
            "p_value": p_w,
            "significant_at_0_05": bool(p_w < 0.05) if p_w is not None else False,
        },
        "cohens_d_z": round(d_z, 4),
        "effect_magnitude": (
            "Large" if abs(d_z) >= 0.8 else ("Medium" if abs(d_z) >= 0.5 else ("Small" if abs(d_z) >= 0.2 else "Negligible"))
        ),
    }


def main():
    parser = argparse.ArgumentParser(description="Authoritative 30-Seed Statistical Analysis")
    parser.add_argument("--input-dir", type=str, default=str(INPUT_DIR))
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR))
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=== CONDUCTING 30-SEED STATISTICAL SIGNIFICANCE ANALYSIS ===")

    # 1. Load per-seed data for all controllers
    raw_data: Dict[str, Dict[int, Dict[str, Any]]] = {c: {} for c in CONTROLLERS}
    seeds_found = set()

    for ctrl in CONTROLLERS:
        for seed in range(1, 31):
            fpath = in_dir / f"{ctrl}_seed{seed}.json"
            if fpath.is_file():
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        d = json.load(f)
                        if d.get("completed", False):
                            raw_data[ctrl][seed] = d
                            seeds_found.add(seed)
                except Exception as e:
                    logger.warning(f"Failed reading {fpath}: {e}")

    logger.info(f"Loaded seeds: {sorted(list(seeds_found))} (count={len(seeds_found)})")
    for ctrl in CONTROLLERS:
        logger.info(f"  {ctrl:15s}: {len(raw_data[ctrl])}/30 completed runs")

    matched_seeds = sorted(list(seeds_found))

    # 2. Compute descriptive statistics
    descriptive_results = {}
    for ctrl in CONTROLLERS:
        descriptive_results[ctrl] = {}
        for m_key, m_label, _ in METRICS:
            vals = [
                raw_data[ctrl][s][m_key]
                for s in matched_seeds
                if s in raw_data[ctrl] and raw_data[ctrl][s].get(m_key) is not None
            ]
            if vals:
                descriptive_results[ctrl][m_key] = compute_descriptive_stats(vals)

    # 3. Compute paired comparisons vs Baseline
    comparisons_vs_baseline = {}
    candidate_controllers = [c for c in CONTROLLERS if c != "baseline"]

    for ctrl in candidate_controllers:
        comparisons_vs_baseline[ctrl] = {}
        for m_key, m_label, lower_is_better in METRICS:
            b_vals = []
            c_vals = []
            for s in matched_seeds:
                if (
                    s in raw_data["baseline"]
                    and s in raw_data[ctrl]
                    and raw_data["baseline"][s].get(m_key) is not None
                    and raw_data[ctrl][s].get(m_key) is not None
                ):
                    b_vals.append(raw_data["baseline"][s][m_key])
                    c_vals.append(raw_data[ctrl][s][m_key])

            if len(b_vals) >= 2:
                comparisons_vs_baseline[ctrl][m_key] = compute_paired_comparison(
                    baseline_vals=b_vals,
                    candidate_vals=c_vals,
                    lower_is_better=lower_is_better,
                    num_comparisons=len(candidate_controllers),
                )

    # 4. Save output artifact
    out_payload = {
        "metadata": {
            "title": "Authoritative 30-Seed Statistical Hypothesis Testing and Effect Size Report",
            "benchmark_directory": str(in_dir),
            "matched_seeds": matched_seeds,
            "total_matched_seeds": len(matched_seeds),
            "controllers": CONTROLLERS,
            "baseline_controller": "baseline",
            "alpha_family": 0.05,
            "bonferroni_corrected_alpha": round(0.05 / len(candidate_controllers), 6),
            "degrees_of_freedom": len(matched_seeds) - 1,
        },
        "descriptive_statistics": descriptive_results,
        "comparisons_vs_baseline": comparisons_vs_baseline,
    }

    out_file = out_dir / "statistical_analysis_30seeds.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)

    logger.info(f"Saved complete statistical analysis to: {out_file}")

    # 5. Print Summary Table
    print("\n" + "=" * 110)
    print(f"{'Controller':<16} | {'Travel Time (s)':<18} | {'Delay (veh-s)':<18} | {'Queue (veh)':<14} | {'Speed (km/h)':<14} | {'p-val (TT)':<10} | {'Cohen d_z':<8}")
    print("=" * 110)
    b_tt = descriptive_results.get("baseline", {}).get("mean_corridor_travel_time_s", {}).get("mean", 0.0)
    for ctrl in CONTROLLERS:
        tt_info = descriptive_results.get(ctrl, {}).get("mean_corridor_travel_time_s", {})
        d_info = descriptive_results.get(ctrl, {}).get("cumulative_delay_veh_s", {})
        q_info = descriptive_results.get(ctrl, {}).get("mean_corridor_queue", {})
        s_info = descriptive_results.get(ctrl, {}).get("mean_corridor_speed_kmh", {})

        tt_str = f"{tt_info.get('mean', 0.0):.2f} ± {tt_info.get('std', 0.0):.2f}"
        d_str = f"{d_info.get('mean', 0.0):.0f} ± {d_info.get('std', 0.0):.0f}"
        q_str = f"{q_info.get('mean', 0.0):.2f} ± {q_info.get('std', 0.0):.2f}"
        s_str = f"{s_info.get('mean', 0.0):.2f} ± {s_info.get('std', 0.0):.2f}"

        if ctrl == "baseline":
            p_str = "REF"
            dz_str = "REF"
        else:
            comp = comparisons_vs_baseline.get(ctrl, {}).get("mean_corridor_travel_time_s", {})
            pval = comp.get("paired_t_test", {}).get("p_value")
            dz = comp.get("cohens_d_z")
            p_str = f"{pval:.2e}" if pval is not None else "N/A"
            dz_str = f"{dz:.2f}" if dz is not None else "N/A"

        print(f"{ctrl:<16} | {tt_str:<18} | {d_str:<18} | {q_str:<14} | {s_str:<14} | {p_str:<10} | {dz_str:<8}")
    print("=" * 110 + "\n")


if __name__ == "__main__":
    main()
