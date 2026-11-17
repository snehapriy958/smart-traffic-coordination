# outputs/experiments/phase4/series4b_final_validation/run_statistical_validation.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import json
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

from outputs.experiments.phase4.series4b_final_validation.reconstruct_design import reconstruct_design

def run_validation():
    print("=== STARTING FULL STATISTICAL VALIDATION OF SERIES 4B ===")
    df, model_summary = reconstruct_design()
    out_dir = Path("outputs/experiments/phase4/series4b_final_validation")

    # -------------------------------------------------------------
    # 1. TASK B: CROSSED EFFECTS & MIXED MODELS
    # -------------------------------------------------------------
    print("\n--- Fitting Mixed-Effects Models & Diagnostics ---")

    # Model 1: Original Audit model (grouped by train_seed 101-105)
    # Fit across full dataset with reference DQN_14D
    m1 = smf.mixedlm("travel_time ~ C(config, Treatment('DQN_14D'))", data=df, groups=df["train_seed"]).fit()

    # Model 2: Proper Nested Model (grouped by unique model_id, 30 levels)
    m2 = smf.mixedlm("travel_time ~ C(config, Treatment('DQN_14D'))", data=df, groups=df["model_id"]).fit()

    # Model 3: Crossed Random Effects Model (eval_seed as group, model_id as variance component)
    m3 = smf.mixedlm("travel_time ~ C(config, Treatment('DQN_14D'))", 
                     data=df, 
                     groups=df["eval_seed"], 
                     vc_formula={"model": "0 + C(model_id)"}).fit()

    # Residuals & Diagnostics for Model 3
    resid_m3 = m3.resid
    sw_stat, sw_p = stats.shapiro(resid_m3)
    lev_groups = [resid_m3[df["config"] == c] for c in sorted(df["config"].unique())]
    lev_stat, lev_p = stats.levene(*lev_groups)

    # Parametric & Cluster Bootstrap for Model-Level Differences (10,000 resamples)
    print("\n--- Running Cluster Bootstrap (10,000 resamples) ---")
    model_pivot = model_summary.pivot(index="train_seed", columns="config", values="mean_travel_time")
    
    np.random.seed(42)
    n_boot = 10000
    seeds = model_pivot.index.values

    comparisons = [
        ("DQN 8D vs DQN 14D", "DQN_8D", "DQN_14D"),
        ("DQN 8D vs DQN 4D",  "DQN_8D", "DQN_4D"),
        ("14D: MAPPO vs DQN", "MAPPO_14D", "DQN_14D"),
        ("8D: MAPPO vs DQN",  "MAPPO_8D",  "DQN_8D"),
        ("4D: MAPPO vs DQN",  "MAPPO_4D",  "DQN_4D"),
        ("MAPPO 14D vs 8D",   "MAPPO_14D", "MAPPO_8D"),
        ("MAPPO 14D vs 4D",   "MAPPO_14D", "MAPPO_4D"),
        ("MAPPO 8D vs 4D",    "MAPPO_8D",  "MAPPO_4D"),
        ("DQN 14D vs 4D",     "DQN_14D",   "DQN_4D"),
    ]

    boot_results = {}
    for name, c_a, c_b in comparisons:
        boot_diffs = []
        for _ in range(n_boot):
            resamp = np.random.choice(seeds, size=len(seeds), replace=True)
            b_df = model_pivot.loc[resamp]
            boot_diffs.append(float(b_df[c_a].mean() - b_df[c_b].mean()))
        
        boot_diffs = np.array(boot_diffs)
        ci_lower, ci_upper = np.percentile(boot_diffs, [2.5, 97.5])
        emp_p = 2.0 * min(np.mean(boot_diffs >= 0), np.mean(boot_diffs <= 0))
        boot_results[name] = {
            "mean_boot_diff": round(float(np.mean(boot_diffs)), 2),
            "std_boot_diff": round(float(np.std(boot_diffs)), 2),
            "ci95_boot": [round(float(ci_lower), 2), round(float(ci_upper), 2)],
            "empirical_p_value": round(float(emp_p), 4)
        }

    # Extract estimates from Model 3
    m3_params_dict = {}
    for param in m3.params.index:
        m3_params_dict[param] = {
            "coef": round(float(m3.params[param]), 4),
            "std_err": round(float(m3.bse[param]), 4) if not np.isnan(m3.bse[param]) else None,
            "z": round(float(m3.tvalues[param]), 4) if not np.isnan(m3.tvalues[param]) else None,
            "p_value": round(float(m3.pvalues[param]), 6) if not np.isnan(m3.pvalues[param]) else None
        }

    crossed_effects_results = {
        "model_specifications": {
            "model_1_audit": {
                "formula": "travel_time ~ Configuration",
                "grouping": "train_seed (5 levels, shared numeric seed across models)",
                "log_likelihood": round(float(m1.llf), 2),
                "aic": round(float(m1.aic), 2),
                "bic": round(float(m1.bic), 2),
                "group_var": round(float(m1.cov_re.iloc[0, 0]), 4),
                "residual_var": round(float(m1.scale), 4),
                "critique": "Mathematically inappropriate. Treats independent training runs as repeated measures on the same subject simply because they share a pseudo-random seed integer."
            },
            "model_2_nested": {
                "formula": "travel_time ~ Configuration",
                "grouping": "model_id (30 levels, unique trained checkpoint)",
                "log_likelihood": round(float(m2.llf), 2),
                "aic": round(float(m2.aic), 2),
                "bic": round(float(m2.bic), 2),
                "group_var": round(float(m2.cov_re.iloc[0, 0]), 4),
                "residual_var": round(float(m2.scale), 4),
                "critique": "Correct hierarchical nesting of evaluation runs within trained checkpoints. Correctly reflects that between-model variance is large while evaluation variance is small."
            },
            "model_3_crossed": {
                "formula": "travel_time ~ Configuration + (1 | model_id) + (1 | eval_seed)",
                "grouping": "eval_seed (10 crossed groups) with variance component for model_id (30 levels)",
                "log_likelihood": round(float(m3.llf), 2),
                "aic": round(float(m3.aic), 2),
                "bic": round(float(m3.bic), 2),
                "converged": bool(m3.converged),
                "hessian_positive_definite": False,
                "residual_var": round(float(m3.scale), 4),
                "estimates": m3_params_dict,
                "diagnostics": {
                    "shapiro_wilk_residuals": {"W": round(float(sw_stat), 4), "p_value": float(sw_p)},
                    "levene_residuals_by_config": {"W": round(float(lev_stat), 4), "p_value": float(lev_p)},
                    "convergence_warning": "The Hessian matrix at estimated parameter values is not positive definite due to near-zero variance across evaluation seeds."
                }
            }
        },
        "cluster_bootstrap_10k": boot_results
    }

    crossed_json_path = out_dir / "crossed_effects_results.json"
    with open(crossed_json_path, "w", encoding="utf-8") as fp:
        json.dump(crossed_effects_results, fp, indent=2)
    print(f"Saved crossed effects results to {crossed_json_path}")

    # -------------------------------------------------------------
    # 2. TASK C & D & E: MODEL-LEVEL ROBUSTNESS & SENSITIVITY
    # -------------------------------------------------------------
    print("\n--- Running Model-Level Robustness & Sensitivity ---")
    
    # Configuration stats at model level (N=5 models)
    config_model_stats = {}
    for col in sorted(model_pivot.columns):
        vals = model_pivot[col].values
        n = len(vals)
        mean = float(np.mean(vals))
        std = float(np.std(vals, ddof=1))
        sem = float(std / np.sqrt(n))
        ci_t = stats.t.interval(0.95, df=n-1, loc=mean, scale=sem)
        config_model_stats[col] = {
            "n_models": n,
            "mean_travel_time": round(mean, 2),
            "std_travel_time": round(std, 2),
            "sem_travel_time": round(sem, 2),
            "ci95_t_distribution": [round(float(ci_t[0]), 2), round(float(ci_t[1]), 2)],
            "median_travel_time": round(float(np.median(vals)), 2),
            "iqr_travel_time": round(float(stats.iqr(vals)), 2),
            "min_travel_time": round(float(np.min(vals)), 2),
            "max_travel_time": round(float(np.max(vals)), 2),
            "checkpoint_means": {f"seed_{s}": round(float(model_pivot.loc[s, col]), 2) for s in model_pivot.index}
        }

    # Model-level inferential tests
    model_comparisons = []
    for name, c_a, c_b in comparisons:
        a_vals = model_pivot[c_a].values
        b_vals = model_pivot[c_b].values
        diff = a_vals - b_vals
        mean_diff = float(np.mean(diff))
        std_diff = float(np.std(diff, ddof=1))
        sem_diff = float(std_diff / np.sqrt(len(diff)))
        
        # Paired t-test (df=4)
        t_pair, p_pair = stats.ttest_rel(a_vals, b_vals)
        ci_pair = stats.t.interval(0.95, df=4, loc=mean_diff, scale=sem_diff)
        d_z = float(mean_diff / std_diff) if std_diff > 0 else 0.0

        # Independent Welch t-test (df ~ 6-8)
        t_welch, p_welch = stats.ttest_ind(a_vals, b_vals, equal_var=False)

        # Wilcoxon signed-rank
        try:
            w_stat, w_p = stats.wilcoxon(diff)
            w_stat_val = float(w_stat)
            w_p_val = float(w_p)
        except Exception:
            w_stat_val, w_p_val = None, None

        model_comparisons.append({
            "comparison": name,
            "condition_A": c_a,
            "condition_B": c_b,
            "mean_diff": round(mean_diff, 2),
            "std_diff": round(std_diff, 2),
            "paired_t_stat_df4": round(float(t_pair), 3),
            "paired_p_value": round(float(p_pair), 4),
            "ci95_paired_t": [round(float(ci_pair[0]), 2), round(float(ci_pair[1]), 2)],
            "cohens_dz": round(d_z, 3),
            "welch_t_stat": round(float(t_welch), 3),
            "welch_p_value": round(float(p_welch), 4),
            "wilcoxon_stat": w_stat_val,
            "wilcoxon_p_value": round(w_p_val, 4) if w_p_val is not None else None,
            "statistically_significant_df4": bool(p_pair < 0.05)
        })

    # Leave-One-Model-Out Jackknife Analysis (Drop each train seed 101 to 105)
    leave_one_model_out = {}
    for drop_seed in [101, 102, 103, 104, 105]:
        sub_pivot = model_pivot.drop(index=drop_seed)
        sub_diff_8_14 = sub_pivot["DQN_8D"] - sub_pivot["DQN_14D"]
        sub_diff_8_4  = sub_pivot["DQN_8D"] - sub_pivot["DQN_4D"]
        
        t_8_14, p_8_14 = stats.ttest_rel(sub_pivot["DQN_8D"], sub_pivot["DQN_14D"])
        t_8_4, p_8_4   = stats.ttest_rel(sub_pivot["DQN_8D"], sub_pivot["DQN_4D"])

        leave_one_model_out[f"drop_train_seed_{drop_seed}"] = {
            "dqn_8d_mean": round(float(sub_pivot["DQN_8D"].mean()), 2),
            "dqn_8d_std": round(float(sub_pivot["DQN_8D"].std()), 2),
            "dqn_14d_mean": round(float(sub_pivot["DQN_14D"].mean()), 2),
            "dqn_4d_mean": round(float(sub_pivot["DQN_4D"].mean()), 2),
            "dqn_8d_vs_14d": {
                "mean_diff": round(float(sub_diff_8_14.mean()), 2),
                "t_stat_df3": round(float(t_8_14), 3),
                "p_value": round(float(p_8_14), 4),
                "significant": bool(p_8_14 < 0.05)
            },
            "dqn_8d_vs_4d": {
                "mean_diff": round(float(sub_diff_8_4.mean()), 2),
                "t_stat_df3": round(float(t_8_4), 3),
                "p_value": round(float(p_8_4), 4),
                "significant": bool(p_8_4 < 0.05)
            }
        }

    # Leave-One-Evaluation-Seed-Out Jackknife Analysis (Drop each eval seed 1 to 10)
    leave_one_eval_out = {}
    base_rank = df.groupby("config")["travel_time"].mean().sort_values().index.tolist()
    for drop_eval in range(1, 11):
        sub_eval = df[df["eval_seed"] != drop_eval]
        sub_means = sub_eval.groupby("config")["travel_time"].mean().to_dict()
        sub_rank = sub_eval.groupby("config")["travel_time"].mean().sort_values().index.tolist()
        leave_one_eval_out[f"drop_eval_seed_{drop_eval}"] = {
            "config_means": {k: round(float(v), 2) for k, v in sub_means.items()},
            "ranking": sub_rank,
            "ranking_matches_baseline": bool(sub_rank == base_rank),
            "dqn_8d_is_rank_1": bool(sub_rank[0] == "DQN_8D")
        }

    # Two-Way ANOVA across all 300 evaluations
    ols_full = smf.ols("travel_time ~ C(config) + C(eval_seed) + C(config):C(eval_seed)", data=df).fit()
    anova_full = sm.stats.anova_lm(ols_full, typ=2)
    anova_dict = {
        "ss_config": round(float(anova_full.loc["C(config)", "sum_sq"]), 2),
        "f_config": round(float(anova_full.loc["C(config)", "F"]), 3),
        "p_config": float(anova_full.loc["C(config)", "PR(>F)"]),
        "ss_eval_seed": round(float(anova_full.loc["C(eval_seed)", "sum_sq"]), 2),
        "f_eval_seed": round(float(anova_full.loc["C(eval_seed)", "F"]), 3),
        "p_eval_seed": float(anova_full.loc["C(eval_seed)", "PR(>F)"]),
        "ss_interaction": round(float(anova_full.loc["C(config):C(eval_seed)", "sum_sq"]), 2),
        "f_interaction": round(float(anova_full.loc["C(config):C(eval_seed)", "F"]), 3),
        "p_interaction": float(anova_full.loc["C(config):C(eval_seed)", "PR(>F)"]),
        "ss_residual": round(float(anova_full.loc["Residual", "sum_sq"]), 2),
    }

    robustness_results = {
        "configuration_model_level_stats": config_model_stats,
        "model_level_comparisons_df4": model_comparisons,
        "leave_one_model_out_jackknife": leave_one_model_out,
        "leave_one_evaluation_seed_out_jackknife": leave_one_eval_out,
        "two_way_anova_crossed": anova_dict
    }

    rob_json_path = out_dir / "robustness_analysis.json"
    with open(rob_json_path, "w", encoding="utf-8") as fp:
        json.dump(robustness_results, fp, indent=2)
    print(f"Saved robustness analysis results to {rob_json_path}")
    print("=== FULL STATISTICAL VALIDATION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_validation()
