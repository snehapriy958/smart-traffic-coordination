import json
import math
import numpy as np
from pathlib import Path
from scipy import stats

def recompute_paired():
    eval_dir = Path("outputs/experiments/phase4/final_150ep/series_4b_observation_space")
    files = list(eval_dir.glob("eval_*.json"))
    
    records = {}
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        key = (d["algorithm"], d["observation_dim"], d["train_seed"], d["eval_seed"])
        records[key] = d

    # Nine pairwise comparisons
    # Let's specify exact (name, condition A, condition B)
    # Definition: diff = A - B
    # A negative diff means Condition A has lower travel time (faster/better)
    comparisons = [
        # MAPPO Dimension Ablations
        ("MAPPO 14D vs 8D", ("mappo", 14), ("mappo", 8)),
        ("MAPPO 14D vs 4D", ("mappo", 14), ("mappo", 4)),
        ("MAPPO 8D vs 4D",  ("mappo", 8),  ("mappo", 4)),
        # DQN Dimension Ablations
        ("DQN 14D vs 8D",   ("dqn", 14),   ("dqn", 8)),
        ("DQN 14D vs 4D",   ("dqn", 14),   ("dqn", 4)),
        ("DQN 8D vs 4D",    ("dqn", 8),    ("dqn", 4)),
        # Cross-Algorithm comparisons (MAPPO vs DQN at each dimension)
        ("14D: MAPPO vs DQN", ("mappo", 14), ("dqn", 14)),
        ("8D: MAPPO vs DQN",  ("mappo", 8),  ("dqn", 8)),
        ("4D: MAPPO vs DQN",  ("mappo", 4),  ("dqn", 4)),
    ]

    results = []
    for name, (a_algo, a_dim), (b_algo, b_dim) in comparisons:
        arr_a = []
        arr_b = []
        pairs_meta = []
        for ts in [101, 102, 103, 104, 105]:
            for es in range(1, 11):
                ra = records.get((a_algo, a_dim, ts, es))
                rb = records.get((b_algo, b_dim, ts, es))
                if ra and rb:
                    arr_a.append(ra["mean_corridor_travel_time_s"])
                    arr_b.append(rb["mean_corridor_travel_time_s"])
                    pairs_meta.append((ts, es))
                    
        a = np.array(arr_a, dtype=float)
        b = np.array(arr_b, dtype=float)
        diff = a - b
        n = len(diff)
        
        mean_a = float(np.mean(a))
        std_a = float(np.std(a, ddof=1))
        mean_b = float(np.mean(b))
        std_b = float(np.std(b, ddof=1))
        
        mean_d = float(np.mean(diff))
        std_d = float(np.std(diff, ddof=1))
        sem_d = std_d / math.sqrt(n)
        
        # Paired t-test
        t_stat = mean_d / sem_d
        p_val_t = 2.0 * stats.t.sf(abs(t_stat), df=n-1)
        
        # scipy ttest_rel verification
        sp_t, sp_p = stats.ttest_rel(a, b)
        
        # Wilcoxon signed-rank test
        # zero_method='wilcox' or 'pratt'
        try:
            w_stat, w_p = stats.wilcoxon(a, b)
        except Exception as e:
            w_stat, w_p = 0.0, 1.0
            
        # Cohen's dz: mean_d / std_d
        cohens_dz = mean_d / std_d if std_d > 0 else 0.0
        
        # Cohen's d using pooled SD: mean_d / s_pooled
        s_pooled = math.sqrt((std_a**2 + std_b**2) / 2.0)
        cohens_d_pooled = mean_d / s_pooled if s_pooled > 0 else 0.0
        
        # 95% CI of the difference
        t_crit = stats.t.ppf(0.975, df=n-1)
        ci_d_low = mean_d - t_crit * sem_d
        ci_d_high = mean_d + t_crit * sem_d
        
        results.append({
            "name": name,
            "condition_A": f"{a_algo.upper()}_{a_dim}D",
            "condition_B": f"{b_algo.upper()}_{b_dim}D",
            "n_pairs": n,
            "mean_A": mean_a,
            "std_A": std_a,
            "mean_B": mean_b,
            "std_B": std_b,
            "mean_diff_A_minus_B": mean_d,
            "std_diff": std_d,
            "sem_diff": sem_d,
            "ci95_diff": (ci_d_low, ci_d_high),
            "paired_t_stat": t_stat,
            "scipy_t": sp_t,
            "raw_p_value": p_val_t,
            "wilcoxon_stat": w_stat,
            "wilcoxon_p": w_p,
            "cohens_dz": cohens_dz,
            "cohens_d_pooled": cohens_d_pooled,
        })
        
    # Standard Holm-Bonferroni correction
    # Sort by raw p-value ascending
    sorted_pairs = sorted(enumerate(results), key=lambda x: x[1]["raw_p_value"])
    m = len(results)
    
    # Compute step-down adjusted p-values
    # p_adj[k] = min(1.0, max(p_adj[k-1], p_val[k] * (m - k + 1)))
    running_max = 0.0
    for rank, (orig_idx, item) in enumerate(sorted_pairs):
        k = rank + 1
        mult = m - k + 1
        adj_p = min(1.0, item["raw_p_value"] * mult)
        running_max = max(running_max, adj_p)
        results[orig_idx]["holm_rank"] = k
        results[orig_idx]["p_adj_holm"] = running_max
        results[orig_idx]["sig_005"] = bool(running_max < 0.05)
        results[orig_idx]["sig_001"] = bool(running_max < 0.01)

    out_p = Path("outputs/experiments/phase4/independent_audit_series4b/recomputed_paired_comparisons.json")
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"Recomputed paired comparisons saved to {out_p}")
    return results

if __name__ == "__main__":
    recompute_paired()
