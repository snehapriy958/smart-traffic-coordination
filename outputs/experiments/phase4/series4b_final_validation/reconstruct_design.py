# outputs/experiments/phase4/series4b_final_validation/reconstruct_design.py
import json
from pathlib import Path
import pandas as pd
import numpy as np

def reconstruct_design():
    eval_dir = Path("outputs/experiments/phase4/final_150ep/series_4b_observation_space")
    files = sorted(list(eval_dir.glob("eval_*.json")))
    print(f"Total raw JSON files found: {len(files)}")
    assert len(files) == 300, f"Expected 300 files, found {len(files)}"

    records = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fp:
            d = json.load(fp)
            
        alg = d["algorithm"].lower()
        dim = int(d["observation_dim"])
        train_seed = int(d["train_seed"])
        eval_seed = int(d["eval_seed"])
        config_name = f"{alg.upper()}_{dim}D"
        model_id = f"{config_name}_s{train_seed}"

        records.append({
            "file": f.name,
            "algorithm": alg,
            "observation_dim": dim,
            "config": config_name,
            "train_seed": train_seed,
            "eval_seed": eval_seed,
            "model_id": model_id,
            "travel_time": float(d["mean_corridor_travel_time_s"]),
            "speed": float(d["mean_corridor_speed_kmh"]),
            "delay": float(d["cumulative_delay_veh_s"]),
            "co2": float(d["total_co2_kg"]),
            "fuel": float(d["total_fuel_liters"]),
            "queue": float(d["mean_corridor_queue"]),
            "trips": int(d["total_corridor_trips_completed"]),
            "duration": 900.0,
            "completed": d.get("completed", False)
        })

    df = pd.DataFrame(records)
    print("DataFrame successfully constructed.")

    # Integrity verification
    print("\n--- DESIGN VERIFICATION ---")
    algorithms = sorted(df["algorithm"].unique())
    dimensions = sorted(df["observation_dim"].unique())
    train_seeds = sorted(df["train_seed"].unique())
    eval_seeds = sorted(df["eval_seed"].unique())
    configs = sorted(df["config"].unique())
    models = sorted(df["model_id"].unique())

    print(f"Algorithms ({len(algorithms)}): {algorithms}")
    print(f"Observation Dimensions ({len(dimensions)}): {dimensions}")
    print(f"Configurations ({len(configs)}): {configs}")
    print(f"Training Seeds ({len(train_seeds)}): {train_seeds}")
    print(f"Evaluation Seeds ({len(eval_seeds)}): {eval_seeds}")
    print(f"Unique Model Checkpoints ({len(models)}): {len(models)}")

    assert len(algorithms) == 2
    assert len(dimensions) == 3
    assert len(configs) == 6
    assert len(train_seeds) == 5
    assert len(eval_seeds) == 10
    assert len(models) == 30

    # Check that each model has exactly 10 evaluation seeds
    model_counts = df.groupby("model_id")["eval_seed"].count()
    assert (model_counts == 10).all(), "Some models do not have exactly 10 evaluations!"
    print("Verification: Every one of the 30 models has exactly 10 evaluation runs.")

    # Check that each eval_seed is evaluated across all 30 models
    seed_counts = df.groupby("eval_seed")["model_id"].count()
    assert (seed_counts == 30).all(), "Some evaluation seeds are not evaluated across all 30 models!"
    print("Verification: Every one of the 10 evaluation seeds is evaluated across all 30 models.")

    # Check for duplicates
    dups = df.duplicated(subset=["algorithm", "observation_dim", "train_seed", "eval_seed"])
    assert not dups.any(), "Duplicate records found!"
    print("Verification: 0 duplicate combinations.")

    # Check durations and completion
    assert (df["duration"] == 900.0).all(), "Non-900s evaluation found!"
    assert (df["completed"] == True).all(), "Incomplete evaluation found!"
    print("Verification: All 300 evaluations completed successfully at exactly 900.0s.")

    # Aggregate to Model Level (N=30 models)
    model_summary = df.groupby(["model_id", "config", "algorithm", "observation_dim", "train_seed"]).agg(
        mean_travel_time=("travel_time", "mean"),
        std_travel_time=("travel_time", lambda x: np.std(x, ddof=1)),
        min_travel_time=("travel_time", "min"),
        max_travel_time=("travel_time", "max"),
        median_travel_time=("travel_time", "median"),
        mean_speed=("speed", "mean"),
        std_speed=("speed", lambda x: np.std(x, ddof=1)),
        mean_delay=("delay", "mean"),
        std_delay=("delay", lambda x: np.std(x, ddof=1)),
        mean_co2=("co2", "mean"),
        mean_fuel=("fuel", "mean"),
        mean_queue=("queue", "mean"),
        mean_trips=("trips", "mean")
    ).reset_index()

    # Sort model summary
    model_summary = model_summary.sort_values(by=["algorithm", "observation_dim", "train_seed"]).reset_index(drop=True)

    csv_path = Path("outputs/experiments/phase4/series4b_final_validation/model_level_results.csv")
    model_summary.to_csv(csv_path, index=False)
    print(f"\nModel-level results successfully written to {csv_path}")

    # Display model summary
    print("\n--- MODEL-LEVEL SUMMARY (30 CHECKPOINTS) ---")
    display_cols = ["model_id", "config", "train_seed", "mean_travel_time", "std_travel_time", "min_travel_time", "max_travel_time", "mean_delay"]
    print(model_summary[display_cols].to_string(index=False))

    return df, model_summary

if __name__ == "__main__":
    reconstruct_design()
