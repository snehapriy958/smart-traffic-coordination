"""
scripts/archive_preliminary_5ep.py

Safely archives and labels all preliminary 5-episode checkpoints and evaluation outputs.
These artifacts are preserved for auditability and exploratory benchmarking,
but marked strictly as PRELIMINARY_5EP and excluded from final confirmatory research results.
"""

import json
from pathlib import Path
import shutil
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_EXP_DIR = PROJECT_ROOT / "outputs" / "experiments" / "phase4"
BASE_CKPT_DIR = PROJECT_ROOT / "checkpoints" / "phase4"

ARCHIVE_CKPT_DIR = BASE_CKPT_DIR / "preliminary_5ep"
ARCHIVE_EXP_DIR = BASE_EXP_DIR / "preliminary_5ep"

ARCHIVE_CKPT_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_EXP_DIR.mkdir(parents=True, exist_ok=True)

print(">>> Archiving 5-episode checkpoints and evaluations...")

# 1. Archive 5ep checkpoints
ckpts_archived = []
for p in BASE_CKPT_DIR.glob("series_*.json"):
    # read to verify
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
            dest = ARCHIVE_CKPT_DIR / p.name
            shutil.copy2(p, dest)
            ckpts_archived.append(p.name)
    except Exception as e:
        print(f"Error copying {p.name}: {e}")

manifest_ckpt = {
    "label": "PRELIMINARY_5EP",
    "description": "5-episode exploratory checkpoints. Excluded from confirmatory publication findings.",
    "archived_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    "checkpoint_count": len(ckpts_archived),
    "checkpoints": ckpts_archived,
}
with open(ARCHIVE_CKPT_DIR / "manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest_ckpt, f, indent=2)

print(f"Archived {len(ckpts_archived)} checkpoints to {ARCHIVE_CKPT_DIR}")

# 2. Archive 5ep evaluation results
for series_name in ["series_4e_passenger_reward", "series_4c_reward_coupling"]:
    src_dir = BASE_EXP_DIR / series_name
    if src_dir.is_dir():
        dest_dir = ARCHIVE_EXP_DIR / series_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        eval_files = list(src_dir.glob("eval_*.json"))
        sum_files = list(src_dir.glob("*summary*.json"))
        for f in eval_files + sum_files:
            shutil.copy2(f, dest_dir / f.name)
        
        meta = {
            "label": "PRELIMINARY_5EP",
            "series": series_name,
            "status": "EXPLORATORY_ONLY",
            "eval_runs_count": len(eval_files),
            "summary_present": len(sum_files) > 0,
            "archived_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(dest_dir / "PRELIMINARY_5EP_LABEL.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(f"Archived {len(eval_files)} runs from {series_name} to {dest_dir}")

print("Preliminary archive complete.")
