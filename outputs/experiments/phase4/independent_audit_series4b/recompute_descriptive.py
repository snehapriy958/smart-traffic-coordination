import json
import math
import numpy as np
from pathlib import Path
from collections import defaultdict
from scipy import stats

def recompute_descriptives():
    eval_dir = Path("outputs/experiments/phase4/final_150ep/series_4b_observation_space")
    files = list(eval_dir.glob("eval_*.json"))
    
    records = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        records.append(data)
        
    configs = [
        ("mappo", 14),
        ("mappo", 8),
        ("mappo", 4),
        ("dqn", 14),
        ("dqn", 8),
        ("dqn", 4),
    ]
    
    metrics = [
        "mean_corridor_travel_time_s",
        "mean_corridor_speed_kmh",
        "cumulative_delay_veh_s",
        "total_co2_kg",
        "total_fuel_liters",
        "mean_corridor_queue",
        "max_corridor_queue",
        "total_corridor_trips_completed",
    ]
    
    results = {}
    for algo, dim in configs:
        cfg_name = f"{algo.upper()}_{dim}D"
        cfg_recs = [r for r in records if r["algorithm"] == algo and r["observation_dim"] == dim]
        
        cfg_dict = {"N": len(cfg_recs), "metrics": {}}
        for m in metrics:
            vals = np.array([r[m] for r in cfg_recs if r.get(m) is not None], dtype=float)
            n = len(vals)
            
            mean_v = float(np.mean(vals))
            # sample std (ddof=1)
            std_s = float(np.std(vals, ddof=1))
            # population std (ddof=0)
            std_p = float(np.std(vals, ddof=0))
            
            sem = std_s / math.sqrt(n)
            
            # Student's t critical value for df = n - 1
            t_crit = stats.t.ppf(0.975, df=n-1)
            ci95_low_t = mean_v - t_crit * sem
            ci95_high_t = mean_v + t_crit * sem
            
            # Normal critical value
            z_crit = 1.959963984540054
            ci95_low_z = mean_v - z_crit * sem
            ci95_high_z = mean_v + z_crit * sem
            
            median_v = float(np.median(vals))
            p25 = float(np.percentile(vals, 25))
            p75 = float(np.percentile(vals, 75))
            min_v = float(np.min(vals))
            max_v = float(np.max(vals))
            
            # Skewness and kurtosis
            skew_v = float(stats.skew(vals))
            kurt_v = float(stats.kurtosis(vals)) # excess kurtosis
            
            # Shapiro-Wilk test for normality
            shapiro_stat, shapiro_p = stats.shapiro(vals)
            
            cfg_dict["metrics"][m] = {
                "n": n,
                "mean": mean_v,
                "std_sample_ddof1": std_s,
                "std_pop_ddof0": std_p,
                "sem": sem,
                "t_crit_df49": t_crit,
                "ci95_t": (ci95_low_t, ci95_high_t),
                "ci95_z": (ci95_low_z, ci95_high_z),
                "median": median_v,
                "iqr": p75 - p25,
                "min": min_v,
                "max": max_v,
                "skewness": skew_v,
                "excess_kurtosis": kurt_v,
                "shapiro_wilk_stat": shapiro_stat,
                "shapiro_wilk_p": shapiro_p,
                "is_normal_005": bool(shapiro_p >= 0.05),
            }
            
        results[cfg_name] = cfg_dict
        
    out_p = Path("outputs/experiments/phase4/independent_audit_series4b/recomputed_descriptives.json")
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"Recomputed descriptives saved to {out_p}")
    return results

if __name__ == "__main__":
    recompute_descriptives()
