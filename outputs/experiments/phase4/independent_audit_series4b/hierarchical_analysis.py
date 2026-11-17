import json
import math
import numpy as np
from pathlib import Path
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
import pandas as pd

def run_hierarchical_analysis():
    eval_dir = Path("outputs/experiments/phase4/final_150ep/series_4b_observation_space")
    files = list(eval_dir.glob("eval_*.json"))
    
    rows = []
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        rows.append({
            "algorithm": d["algorithm"],
            "observation_dim": d["observation_dim"],
            "config": f"{d['algorithm'].upper()}_{d['observation_dim']}D",
            "train_seed": int(d["train_seed"]),
            "eval_seed": int(d["eval_seed"]),
            "travel_time": float(d["mean_corridor_travel_time_s"]),
            "speed": float(d["mean_corridor_speed_kmh"]),
            "delay": float(d["cumulative_delay_veh_s"]),
        })
        
    df = pd.DataFrame(rows)
    print(f"Loaded DataFrame with {len(df)} rows.")

    # 1. Variance Decomposition (ANOVA on Travel Time per configuration)
    print("\n=== 1. VARIANCE DECOMPOSITION BY CONFIGURATION ===")
    variance_decomp = {}
    for cfg, group in df.groupby("config"):
        # Model: travel_time ~ C(train_seed) + C(eval_seed)
        model = smf.ols("travel_time ~ C(train_seed) + C(eval_seed)", data=group).fit()
        table = sm.stats.anova_lm(model, typ=2)
        ss_train = table.loc["C(train_seed)", "sum_sq"]
        ss_eval = table.loc["C(eval_seed)", "sum_sq"]
        ss_resid = table.loc["Residual", "sum_sq"]
        ss_total = ss_train + ss_eval + ss_resid
        
        eta_train = ss_train / ss_total
        eta_eval = ss_eval / ss_total
        eta_resid = ss_resid / ss_total
        
        variance_decomp[cfg] = {
            "total_variance": float(np.var(group["travel_time"], ddof=1)),
            "pct_var_train_seed": round(eta_train * 100.0, 2),
            "pct_var_eval_seed": round(eta_eval * 100.0, 2),
            "pct_var_residual": round(eta_resid * 100.0, 2),
            "f_train_seed": round(float(table.loc["C(train_seed)", "F"]), 3),
            "p_train_seed": float(table.loc["C(train_seed)", "PR(>F)"]),
            "f_eval_seed": round(float(table.loc["C(eval_seed)", "F"]), 3),
            "p_eval_seed": float(table.loc["C(eval_seed)", "PR(>F)"]),
        }
        print(f"{cfg}: TrainSeedVar={variance_decomp[cfg]['pct_var_train_seed']}% (p={variance_decomp[cfg]['p_train_seed']:.4f}) | EvalSeedVar={variance_decomp[cfg]['pct_var_eval_seed']}% (p={variance_decomp[cfg]['p_eval_seed']:.4f}) | Resid={variance_decomp[cfg]['pct_var_residual']}%")

    # 2. Aggregated Model-Level Analysis (N=5 independent models)
    print("\n=== 2. AGGREGATED MODEL-LEVEL COMPARISONS (N=5, df=4) ===")
    model_df = df.groupby(["config", "train_seed"])["travel_time"].mean().unstack(level=0)
    print("Model-level means (averaged across 10 eval seeds per model):")
    print(model_df.round(2))
    
    comparisons = [
        ("MAPPO 14D vs 8D", "MAPPO_14D", "MAPPO_8D"),
        ("MAPPO 14D vs 4D", "MAPPO_14D", "MAPPO_4D"),
        ("MAPPO 8D vs 4D",  "MAPPO_8D",  "MAPPO_4D"),
        ("DQN 14D vs 8D",   "DQN_14D",   "DQN_8D"),
        ("DQN 14D vs 4D",   "DQN_14D",   "DQN_4D"),
        ("DQN 8D vs 4D",    "DQN_8D",    "DQN_4D"),
        ("14D: MAPPO vs DQN", "MAPPO_14D", "DQN_14D"),
        ("8D: MAPPO vs DQN",  "MAPPO_8D",  "DQN_8D"),
        ("4D: MAPPO vs DQN",  "MAPPO_4D",  "DQN_4D"),
    ]
    
    model_level_results = []
    for name, col_a, col_b in comparisons:
        diff = model_df[col_a] - model_df[col_b]
        t_stat, p_val = stats.ttest_rel(model_df[col_a], model_df[col_b])
        d_z = float(np.mean(diff) / np.std(diff, ddof=1)) if np.std(diff, ddof=1) > 0 else 0.0
        
        # Linear Mixed Model on full data (Condition + (1|train_seed) + (1|eval_seed))
        subset = df[df["config"].isin([col_a, col_b])].copy()
        subset["is_a"] = (subset["config"] == col_a).astype(float)
        
        try:
            # Fit LMM with random intercepts
            lmm = smf.mixedlm("travel_time ~ is_a", data=subset, groups=subset["train_seed"]).fit()
            lmm_coef = float(lmm.params["is_a"])
            lmm_p = float(lmm.pvalues["is_a"])
            lmm_z = float(lmm.tvalues["is_a"])
        except Exception as e:
            lmm_coef, lmm_p, lmm_z = 0.0, 1.0, 0.0

        model_level_results.append({
            "comparison": name,
            "mean_A": round(float(model_df[col_a].mean()), 2),
            "mean_B": round(float(model_df[col_b].mean()), 2),
            "mean_diff": round(float(diff.mean()), 2),
            "std_diff": round(float(diff.std()), 2),
            "model_level_t_df4": round(float(t_stat), 3),
            "model_level_p": float(p_val),
            "model_level_cohens_dz": round(d_z, 3),
            "lmm_diff_coef": round(lmm_coef, 2),
            "lmm_z": round(lmm_z, 3),
            "lmm_p_value": lmm_p,
        })
        print(f"{name}: diff={diff.mean():.2f}s | N=5 t={t_stat:.3f} (p={p_val:.4f}) | LMM z={lmm_z:.3f} (p={lmm_p:.4f})")

    out_data = {
        "variance_decomposition": variance_decomp,
        "model_level_comparisons": model_level_results,
    }
    
    out_p = Path("outputs/experiments/phase4/independent_audit_series4b/hierarchical_model_results.json")
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2)
        
    print(f"\nHierarchical model results saved to {out_p}")
    return out_data

if __name__ == "__main__":
    run_hierarchical_analysis()
