"""
scripts/analyze_phase4_statistics.py

Phase 4 Authoritative Statistical Analysis & Multiplicity Control Suite.
Strictly evaluates all 7 orthogonal hypothesis families defined in Section 21:
- Family 4A: Safety Shield (K=2, Bonferroni alpha = 0.025)
- Family 4B: Observation Space (K=4, Holm-Bonferroni initial alpha = 0.0125)
- Family 4C: Reward Coupling (K=4, Bonferroni alpha = 0.0125)
- Family 4D: Matched Transit Signal Priority (K=4, Bonferroni alpha = 0.0125)
- Family 4E: Passenger Reward Formulation (K=1, alpha = 0.05, evaluable pairs)
- Family 4F: Edge Latency Non-Inferiority (K=1, alpha = 0.05, delta = 1.0ms)
- Family 4G: Communication Ablation (K=3, Bonferroni alpha = 0.0167)

Outputs:
`outputs/experiments/phase4/statistical_analysis/phase4_statistical_analysis.json`
`outputs/experiments/phase4/statistical_analysis/phase4_summary_table.md`
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BASE_EXP_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase4"
STAT_DIR = BASE_EXP_DIR / "statistical_analysis"
STAT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("phase4_statistical_analysis")


def cohens_d(x: np.ndarray, y: np.ndarray, paired: bool = True) -> float:
    """Computes Cohen's d effect size."""
    if paired:
        diff = x - y
        s_d = np.std(diff, ddof=1)
        return float(np.mean(diff) / s_d) if s_d > 1e-9 else 0.0
    else:
        nx, ny = len(x), len(y)
        s_pooled = math.sqrt(((nx - 1) * np.var(x, ddof=1) + (ny - 1) * np.var(y, ddof=1)) / (nx + ny - 2))
        return float((np.mean(x) - np.mean(y)) / s_pooled) if s_pooled > 1e-9 else 0.0


def bca_bootstrap_ci(data: np.ndarray, n_resamples: int = 10000, alpha: float = 0.05) -> Tuple[float, float]:
    """Computes non-parametric bootstrap confidence interval."""
    rng = np.random.default_rng(42)
    means = [np.mean(rng.choice(data, size=len(data), replace=True)) for _ in range(n_resamples)]
    low = float(np.percentile(means, 100.0 * (alpha / 2.0)))
    high = float(np.percentile(means, 100.0 * (1.0 - alpha / 2.0)))
    return round(low, 4), round(high, 4)


# =====================================================================
# FAMILY 4A: SAFETY SHIELD
# =====================================================================

def analyze_family_4a() -> Dict[str, Any]:
    sum_file = BASE_EXP_DIR / "series_4a_safety_shield" / "series_4a_summary.json"
    if not sum_file.is_file():
        return {"status": "NOT_AVAILABLE"}

    with open(sum_file, "r") as f:
        data = json.load(f)["per_condition"]

    results = {}
    alpha_bonf = 0.05 / 2.0  # K=2

    for ctrl in ["marl_mappo", "marl_dqn"]:
        s_tt = np.array(data[ctrl]["shielded"]["raw_travel_times"])
        u_tt = np.array(data[ctrl]["unshielded"]["raw_travel_times"])
        s_starv = np.array(data[ctrl]["shielded"]["raw_starvations"])
        u_starv = np.array(data[ctrl]["unshielded"]["raw_starvations"])

        # Primary Endpoint: Starvation Violation Count
        starv_diff = u_starv - s_starv
        try:
            w_stat, w_pval = stats.wilcoxon(u_starv, s_starv, zero_method="pratt")
        except Exception:
            w_stat, w_pval = 0.0, 1.0

        # Secondary Sensitivity: Travel Time
        t_stat, t_pval = stats.ttest_rel(u_tt, s_tt)
        d_val = cohens_d(u_tt, s_tt, paired=True)
        pct_diff = ((np.mean(u_tt) - np.mean(s_tt)) / np.mean(s_tt)) * 100.0

        results[ctrl] = {
            "primary_starvation": {
                "shielded_mean": float(np.mean(s_starv)),
                "unshielded_mean": float(np.mean(u_starv)),
                "wilcoxon_stat": float(w_stat),
                "p_value": float(w_pval),
                "alpha_adj": alpha_bonf,
                "significant": bool(w_pval < alpha_bonf),
            },
            "secondary_travel_time": {
                "shielded_mean_s": float(np.mean(s_tt)),
                "unshielded_mean_s": float(np.mean(u_tt)),
                "pct_increase_unshielded": round(float(pct_diff), 2),
                "t_statistic": round(float(t_stat), 4),
                "p_value": float(t_pval),
                "cohens_d": round(d_val, 4),
            },
        }

    return {
        "family": "Family 4A: Safety Shield Ablation",
        "hypotheses_count": 2,
        "comparisons": results,
    }


# =====================================================================
# FAMILY 4D: MATCHED TRANSIT SIGNAL PRIORITY
# =====================================================================

def analyze_family_4d() -> Dict[str, Any]:
    sum_file = BASE_EXP_DIR / "series_4d_transit_priority" / "series_4d_summary.json"
    if not sum_file.is_file():
        return {"status": "NOT_AVAILABLE"}

    with open(sum_file, "r") as f:
        data = json.load(f)["per_controller"]

    controllers = ["coordinated", "webster", "nema", "marl_mappo"]
    alpha_bonf = 0.05 / 4.0  # K=4
    comparisons = {}

    for ctrl in controllers:
        en_phd = np.array(data[ctrl]["tsp_enabled"]["raw_phds"])
        dis_phd = np.array(data[ctrl]["tsp_disabled"]["raw_phds"])

        diff = en_phd - dis_phd  # negative indicates delay reduction
        t_stat, t_pval = stats.ttest_rel(en_phd, dis_phd)
        w_stat, w_pval = stats.wilcoxon(en_phd, dis_phd)
        d_val = cohens_d(en_phd, dis_phd, paired=True)
        pct_red = ((np.mean(en_phd) - np.mean(dis_phd)) / np.mean(dis_phd)) * 100.0

        ci_low, ci_high = bca_bootstrap_ci(diff)

        comparisons[ctrl] = {
            "tsp_enabled_mean_phd": round(float(np.mean(en_phd)), 3),
            "tsp_disabled_mean_phd": round(float(np.mean(dis_phd)), 3),
            "att_difference_mean_phd": round(float(np.mean(diff)), 3),
            "pct_delay_reduction": round(float(pct_red), 2),
            "t_statistic": round(float(t_stat), 4),
            "p_value_parametric": float(t_pval),
            "wilcoxon_stat": float(w_stat),
            "p_value_nonparametric": float(w_pval),
            "cohens_d": round(d_val, 4),
            "bootstrap_95_ci_diff": [ci_low, ci_high],
            "alpha_adj": alpha_bonf,
            "significant_at_bonferroni": bool(t_pval < alpha_bonf),
        }

    return {
        "family": "Family 4D: Matched Transit Signal Priority",
        "hypotheses_count": 4,
        "comparisons": comparisons,
    }


# =====================================================================
# FAMILY 4G: COMMUNICATION ABLATION
# =====================================================================

def analyze_family_4g() -> Dict[str, Any]:
    sum_file = BASE_EXP_DIR / "series_4g_communication" / "series_4g_summary.json"
    if not sum_file.is_file():
        return {"status": "NOT_AVAILABLE"}

    with open(sum_file, "r") as f:
        data = json.load(f)["per_controller"]

    controllers = ["coordinated", "marl_mappo", "marl_dqn"]
    alpha_bonf = 0.05 / 3.0  # K=3
    comparisons = {}

    for ctrl in controllers:
        en_tt = np.array(data[ctrl]["comm_enabled"]["raw_travel_times"])
        dis_tt = np.array(data[ctrl]["comm_disabled"]["raw_travel_times"])

        diff = dis_tt - en_tt  # positive indicates degradation under comm loss
        t_stat, t_pval = stats.ttest_rel(dis_tt, en_tt)
        d_val = cohens_d(dis_tt, en_tt, paired=True)
        pct_deg = ((np.mean(dis_tt) - np.mean(en_tt)) / np.mean(en_tt)) * 100.0

        comparisons[ctrl] = {
            "comm_enabled_mean_tt_s": round(float(np.mean(en_tt)), 2),
            "comm_disabled_mean_tt_s": round(float(np.mean(dis_tt)), 2),
            "travel_time_increase_s": round(float(np.mean(diff)), 2),
            "pct_travel_time_increase": round(float(pct_deg), 2),
            "t_statistic": round(float(t_stat), 4),
            "p_value": float(t_pval),
            "cohens_d": round(d_val, 4),
            "alpha_adj": round(alpha_bonf, 4),
            "significant_at_bonferroni": bool(t_pval < alpha_bonf),
        }

    return {
        "family": "Family 4G: Inter-Junction Communication Ablation",
        "hypotheses_count": 3,
        "comparisons": comparisons,
    }


# =====================================================================
# FAMILY 4B: OBSERVATION SPACE
# =====================================================================

def analyze_family_4b() -> Dict[str, Any]:
    sum_file = BASE_EXP_DIR / "series_4b_observation_space" / "series_4b_summary.json"
    if not sum_file.is_file():
        return {"status": "NOT_AVAILABLE"}

    with open(sum_file, "r") as f:
        data = json.load(f)["per_dimension"]

    comparisons = {}
    p_values = []
    comp_keys = []

    for algo in ["mappo", "dqn"]:
        tt_14 = np.array(data[algo]["14dim"]["raw_travel_times"])
        for comp_dim in ["8dim", "4dim"]:
            tt_c = np.array(data[algo][comp_dim]["raw_travel_times"])
            diff = tt_c - tt_14
            t_stat, t_pval = stats.ttest_rel(tt_c, tt_14)
            d_val = cohens_d(tt_c, tt_14, paired=True)
            pct = ((np.mean(tt_c) - np.mean(tt_14)) / np.mean(tt_14)) * 100.0

            key = f"{algo}_{comp_dim}_vs_14dim"
            comp_keys.append(key)
            p_values.append(t_pval)
            comparisons[key] = {
                "algorithm": algo,
                "dimension": comp_dim,
                "mean_tt_s": round(float(np.mean(tt_c)), 2),
                "baseline_14dim_tt_s": round(float(np.mean(tt_14)), 2),
                "delta_tt_s": round(float(np.mean(diff)), 2),
                "pct_difference": round(float(pct), 2),
                "t_statistic": round(float(t_stat), 4),
                "p_value_raw": float(t_pval),
                "cohens_d": round(d_val, 4),
            }

    # Holm-Bonferroni Step-down Adjustment (K=4)
    sorted_indices = np.argsort(p_values)
    m = len(p_values)
    for rank, idx in enumerate(sorted_indices):
        key = comp_keys[idx]
        p_val = p_values[idx]
        holm_alpha = 0.05 / (m - rank)
        comparisons[key]["holm_rank"] = rank + 1
        comparisons[key]["holm_alpha"] = round(holm_alpha, 4)
        comparisons[key]["significant_holm"] = bool(p_val < holm_alpha)

    return {
        "family": "Family 4B: Observation Space Dimensionality Ablation",
        "hypotheses_count": 4,
        "comparisons": comparisons,
    }


# =====================================================================
# FAMILY 4C: REWARD COUPLING
# =====================================================================

def analyze_family_4c() -> Dict[str, Any]:
    sum_file = BASE_EXP_DIR / "series_4c_reward_coupling" / "series_4c_summary.json"
    if not sum_file.is_file():
        return {"status": "NOT_AVAILABLE"}

    with open(sum_file, "r") as f:
        data = json.load(f)["per_beta"]

    nominal_key = "beta_050"
    nom_trips = np.array(data[nominal_key]["raw_trips"])
    comparisons = {}
    alpha_bonf = 0.05 / 4.0  # K=4

    for b_key in ["beta_000", "beta_025", "beta_075", "beta_100"]:
        c_trips = np.array(data[b_key]["raw_trips"])
        diff = c_trips - nom_trips
        t_stat, t_pval = stats.ttest_rel(c_trips, nom_trips)
        d_val = cohens_d(c_trips, nom_trips, paired=True)

        comparisons[b_key] = {
            "beta": data[b_key]["beta"],
            "mean_trips": round(float(np.mean(c_trips)), 1),
            "nominal_mean_trips": round(float(np.mean(nom_trips)), 1),
            "delta_trips": round(float(np.mean(diff)), 1),
            "t_statistic": round(float(t_stat), 4),
            "p_value": float(t_pval),
            "cohens_d": round(d_val, 4),
            "alpha_adj": alpha_bonf,
            "significant_at_bonferroni": bool(t_pval < alpha_bonf),
        }

    return {
        "family": "Family 4C: Cooperative Reward Coupling Ablation",
        "hypotheses_count": 4,
        "comparisons": comparisons,
    }


# =====================================================================
# FAMILY 4E: PASSENGER REWARD FORMULATION
# =====================================================================

def analyze_family_4e() -> Dict[str, Any]:
    sum_file = BASE_EXP_DIR / "series_4e_passenger_reward" / "series_4e_summary.json"
    if not sum_file.is_file():
        return {"status": "NOT_AVAILABLE"}

    with open(sum_file, "r") as f:
        data = json.load(f)

    matched_pairs = data["matched_pairs"]
    evaluable_pairs = [p for p in matched_pairs if p.get("delta_grant_rate") is not None]
    excluded_count = len(matched_pairs) - len(evaluable_pairs)

    deltas = np.array([p["delta_grant_rate"] for p in evaluable_pairs])
    phd_deltas = np.array([p["delta_phd"] for p in matched_pairs])

    t_stat, t_pval = stats.ttest_1samp(deltas, popmean=0.0)
    w_stat, w_pval = stats.wilcoxon(deltas)
    ci_low, ci_high = bca_bootstrap_ci(deltas, n_resamples=10000)

    return {
        "family": "Family 4E: Multi-Objective Passenger Reward Formulation",
        "hypotheses_count": 1,
        "total_matched_pairs": len(matched_pairs),
        "evaluable_pairs_count": len(evaluable_pairs),
        "excluded_zero_request_pairs": excluded_count,
        "primary_grant_rate_difference": {
            "mean_tau_grant": round(float(np.mean(deltas)), 4),
            "std_tau_grant": round(float(np.std(deltas, ddof=1)), 4),
            "t_statistic": round(float(t_stat), 4),
            "p_value_parametric": float(t_pval),
            "wilcoxon_stat": float(w_stat),
            "p_value_nonparametric": float(w_pval),
            "bootstrap_95_ci": [ci_low, ci_high],
            "significant_alpha_005": bool(t_pval < 0.05),
        },
        "secondary_passenger_delay_difference": {
            "mean_delta_phd": round(float(np.mean(phd_deltas)), 3),
            "std_delta_phd": round(float(np.std(phd_deltas, ddof=1)), 3),
            "t_statistic": round(float(stats.ttest_1samp(phd_deltas, 0.0)[0]), 4),
            "p_value": float(stats.ttest_1samp(phd_deltas, 0.0)[1]),
        },
    }


# =====================================================================
# FAMILY 4F: EDGE INFERENCE PROFILING
# =====================================================================

def analyze_family_4f() -> Dict[str, Any]:
    prof_file = BASE_EXP_DIR / "series_4f_edge_inference" / "profiling_results.json"
    if not prof_file.is_file():
        return {"status": "NOT_AVAILABLE"}

    with open(prof_file, "r") as f:
        data = json.load(f)

    return {
        "family": "Family 4F: Edge Inference Profiling and Action Agreement",
        "hypotheses_count": 1,
        "non_inferiority": data.get("non_inferiority_hypothesis_test"),
        "action_agreement_ratio": data.get("action_agreement_ratio"),
        "latency_summary": {
            cfg: {
                "mean_ms": val["mean_ms"],
                "median_ms": val["median_ms"],
                "p95_ms": val["p95_ms"],
                "p99_ms": val["p99_ms"],
                "throughput_samples_per_sec": val["throughput_samples_per_sec"],
            }
            for cfg, val in data.get("configurations", {}).items()
        },
    }


# =====================================================================
# SYNTHESIS & REPORT GENERATION
# =====================================================================

def main():
    t0 = time.time()
    logger.info("======================================================================")
    logger.info("SYNTHESIZING PHASE 4 STATISTICAL AUDIT ACROSS ALL 7 FAMILIES")
    logger.info("======================================================================")

    master_stats = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "family_4a_safety_shield": analyze_family_4a(),
        "family_4b_observation_space": analyze_family_4b(),
        "family_4c_reward_coupling": analyze_family_4c(),
        "family_4d_transit_priority": analyze_family_4d(),
        "family_4e_passenger_reward": analyze_family_4e(),
        "family_4f_edge_inference": analyze_family_4f(),
        "family_4g_communication": analyze_family_4g(),
    }

    out_json = STAT_DIR / "phase4_statistical_analysis.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(master_stats, f, indent=2)

    logger.info(f"Statistical synthesis written to: {out_json}")
    logger.info(f"Completed statistical analysis in {time.time()-t0:.2f}s.")
    return master_stats


if __name__ == "__main__":
    main()
