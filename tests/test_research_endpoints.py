"""
tests/test_research_endpoints.py

Regression test suite for Phase 4 Research and Experiments endpoints:
- GET /api/experiments/research-overview
- GET /api/experiments/series-4b
- GET /api/experiments/series-4c/status
- GET /api/experiments/series-4c/history
- GET /api/experiments/series-4e
- GET /api/experiments/benchmark/master
- GET /api/experiments/benchmark/historical
"""

import pytest
from backend.routers.experiments import (
    get_research_overview,
    get_series_4b_results,
    get_series_4c_live_status,
    get_series_4c_history,
    get_series_4e_results,
    get_master_benchmark,
    get_historical_benchmark,
)


def test_get_research_overview():
    res = get_research_overview()
    assert res.phase.startswith("Phase 4")
    assert len(res.series_list) >= 7
    series_ids = [s.series_id for s in res.series_list]
    assert "Series 4A" in series_ids
    assert "Series 4B" in series_ids
    assert "Series 4C" in series_ids
    assert "Series 4E" in series_ids
    assert res.overall_progress["total_evaluations_completed"] > 0


def test_get_series_4b_results():
    res = get_series_4b_results()
    assert res.status == "COMPLETE_AND_FROZEN"
    assert res.total_training_runs == 30
    assert res.total_evaluation_records == 300
    assert "MAPPO_14D" in res.configurations
    assert "DQN_14D" in res.configurations
    assert "DQN_4D" in res.configurations
    assert res.hierarchical_inference is not None
    assert isinstance(res.pairwise_comparisons, list)


def test_get_series_4c_live_status():
    res = get_series_4c_live_status()
    assert res.series.startswith("Series 4C")
    assert res.algorithm == "mappo"
    assert res.total_planned_runs == 25
    assert len(res.betas) == 5
    assert len(res.runs_summary) == 25
    if res.current_run:
        assert res.current_run["current_episode"] >= 1
        assert res.current_run["total_episodes"] == 150


def test_get_series_4c_history():
    res = get_series_4c_history()
    assert res.run_key.startswith("beta_")
    assert res.total_episodes == 150
    assert isinstance(res.episodes, list)


def test_get_series_4e_results():
    res = get_series_4e_results()
    assert res.status == "COMPLETED_PRELIMINARY"
    dump = res.model_dump()
    assert "per_formulation" in dump
    assert "delay_centric" in res.per_formulation or "passenger_weighted" in res.per_formulation


def test_get_master_benchmark():
    res = get_master_benchmark()
    assert res.seeds_count == 10
    assert res.benchmark_duration_s == 900
    assert len(res.controllers) == 4
    names = [c.controller_name for c in res.controllers]
    assert any("Fixed-Time" in n for n in names)
    assert any("Coordinated" in n for n in names)
    assert any("Double-DQN" in n for n in names)
    assert any("PPO" in n for n in names)


def test_get_historical_benchmark():
    res = get_historical_benchmark()
    assert len(res) == 4
    names = [c.controller_name for c in res]
    assert any("Baseline" in n for n in names)
