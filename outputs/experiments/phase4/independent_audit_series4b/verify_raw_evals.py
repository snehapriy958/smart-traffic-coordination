import json
import math
from pathlib import Path
from collections import defaultdict, Counter

def verify_eval_files():
    eval_dir = Path("outputs/experiments/phase4/final_150ep/series_4b_observation_space")
    files = list(eval_dir.glob("eval_*.json"))
    print(f"Total files matching eval_*.json: {len(files)}")
    
    expected_combos = set()
    algos = ["mappo", "dqn"]
    dims = [14, 8, 4]
    train_seeds = [101, 102, 103, 104, 105]
    eval_seeds = list(range(1, 11))
    
    for a in algos:
        for d in dims:
            for ts in train_seeds:
                for es in eval_seeds:
                    expected_combos.add((a, d, ts, es))
                    
    print(f"Total expected combinations: {len(expected_combos)}")
    
    actual_combos = set()
    duplicate_combos = []
    invalid_files = []
    records = []
    
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            a = data.get("algorithm")
            d = data.get("observation_dim")
            ts = data.get("train_seed")
            es = data.get("eval_seed")
            combo = (a, d, ts, es)
            
            if combo in actual_combos:
                duplicate_combos.append((f.name, combo))
            actual_combos.add(combo)
            
            # Check required fields
            req_fields = [
                "regime", "series", "algorithm", "train_seed", "eval_seed",
                "observation_dim", "checkpoint_path", "completed", "execution_wall_time_s",
                "total_corridor_trips_completed", "mean_corridor_travel_time_s",
                "mean_corridor_speed_kmh", "cumulative_delay_veh_s"
            ]
            missing_fields = [rf for rf in req_fields if rf not in data]
            if missing_fields or not data.get("completed"):
                invalid_files.append((f.name, "missing fields or not completed", missing_fields))
                
            # Check numerical sanity (no NaN, no Inf)
            nan_inf = [k for k, v in data.items() if isinstance(v, (int, float)) and (math.isnan(v) or math.isinf(v))]
            if nan_inf:
                invalid_files.append((f.name, "nan_or_inf", nan_inf))
                
            records.append(data)
        except Exception as e:
            invalid_files.append((f.name, "parse_error", str(e)))
            
    print(f"Unique actual combinations found: {len(actual_combos)}")
    print(f"Missing combinations: {len(expected_combos - actual_combos)}")
    print(f"Unexpected combinations: {len(actual_combos - expected_combos)}")
    print(f"Duplicates: {len(duplicate_combos)}")
    print(f"Invalid files: {len(invalid_files)}")
    
    return records

if __name__ == "__main__":
    verify_eval_files()
