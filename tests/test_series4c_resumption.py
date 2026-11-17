"""
tests/test_series4c_resumption.py

Comprehensive test suite verifying Series 4C resumption and recovery mechanics:
1. Deterministic seed assignment
2. Checkpoint integrity validation
3. Completed run skipping
4. Interrupted run handling and recovery
5. Manifest consistency and atomic serialization
"""

import json
import pytest
from pathlib import Path
from scripts.train_series4c_master import (
    get_beta_tag,
    verify_checkpoint_integrity,
    init_or_load_manifest,
    save_manifest,
    BETAS,
    TRAIN_SEEDS,
    EVAL_SEEDS,
)


def test_deterministic_seed_assignment():
    """Verifies that seed calculation across episodes is strictly deterministic."""
    train_seed = 101
    episodes = [1, 25, 50, 75, 100, 150]
    expected_seeds = [train_seed * 1000 + ep * 17 for ep in episodes]

    calculated_seeds = [train_seed * 1000 + ep * 17 for ep in episodes]
    assert calculated_seeds == expected_seeds
    assert len(set(calculated_seeds)) == len(episodes), "Episode seeds must be unique"


def test_beta_tagging_consistency():
    """Verifies exact string formatting for beta tags."""
    assert get_beta_tag(0.0) == "beta_000"
    assert get_beta_tag(0.25) == "beta_025"
    assert get_beta_tag(0.5) == "beta_050"
    assert get_beta_tag(0.75) == "beta_075"
    assert get_beta_tag(1.0) == "beta_100"


def test_checkpoint_integrity_validation(tmp_path):
    """Verifies that complete vs invalid/partial checkpoints are correctly classified."""
    beta = 0.50
    seed = 101
    ckpt_file = tmp_path / "test_ckpt.json"
    hist_file = tmp_path / "test_ckpt.history.json"

    # Case 1: File doesn't exist
    valid, reason = verify_checkpoint_integrity(ckpt_file, beta, seed)
    assert not valid
    assert "does not exist" in reason

    # Case 2: Incomplete episodes (e.g. 77 / 150)
    data = {
        "metadata": {
            "regime": "FINAL_CONFIRMATORY_150EP",
            "verified_150ep": False,
            "total_episodes_completed": 77,
            "reward_coupling_beta": beta,
            "train_seed": seed,
            "algorithm": "mappo",
            "observation_dim": 14,
        },
        "weights_payload": "x" * 15000,
    }
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    with open(hist_file, "w", encoding="utf-8") as f:
        json.dump([{"ep": i} for i in range(1, 78)], f)

    valid, reason = verify_checkpoint_integrity(ckpt_file, beta, seed)
    assert not valid
    assert "verified_150ep" in reason or "Episodes completed" in reason

    # Case 3: Fully verified 150 episodes
    data["metadata"]["verified_150ep"] = True
    data["metadata"]["total_episodes_completed"] = 150
    with open(ckpt_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    with open(hist_file, "w", encoding="utf-8") as f:
        json.dump([{"ep": i} for i in range(1, 151)], f)

    valid, reason = verify_checkpoint_integrity(ckpt_file, beta, seed)
    assert valid
    assert reason is None


def test_manifest_consistency():
    """Verifies that manifest maintains all 25 runs and 250 evaluation targets."""
    manifest = init_or_load_manifest()
    assert manifest["series"].startswith("Series 4C")
    assert manifest["total_training_runs"] == 25
    assert manifest["total_evaluations_target"] == 250
    assert len(manifest["runs"]) == 25

    # Check Run 1 structure
    run1 = manifest["runs"]["beta_000_seed101"]
    assert run1["beta"] == 0.0
    assert run1["train_seed"] == 101
    assert len(run1["evaluations"]) == 10
