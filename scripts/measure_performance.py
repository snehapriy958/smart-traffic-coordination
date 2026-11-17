"""
scripts/measure_performance.py

Rigorous Empirical Benchmarking Script for Phase 1 Engineering Foundation.
Measures and records ACTUAL runtime performance:
1. Eclipse SUMO process launch and TraCI handshake latency (ms)
2. TraCI simulation stepping latency (ms/step) & throughput (steps/sec)
3. REST API endpoint response latencies (ms)
4. Clean process shutdown and resource deallocation latency (ms)
Outputs JSON artifact to outputs/benchmarks/engineering_performance_metrics.json
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.sumo_env import require_sumo_env
from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation
from fastapi.testclient import TestClient
from backend.main import app

SUMO_CONFIG = PROJECT_ROOT / "sumo" / "silk_board" / "silk_board.sumocfg"


def benchmark_sumo_traci_lifecycle(iterations: int = 3, steps_per_run: int = 30) -> Dict[str, Any]:
    """Measures actual SUMO launch, TraCI connection, stepping, and shutdown latency."""
    startup_times_ms: List[float] = []
    shutdown_times_ms: List[float] = []
    step_times_ms: List[float] = []

    print(f"\n[1/3] Benchmarking SUMO/TraCI Lifecycle ({iterations} runs, {steps_per_run} steps each)...")

    for i in range(iterations):
        sim = MultiIntersectionSimulation(
            sumocfg_path=SUMO_CONFIG,
            mode="coordinated",
            gui=False,
            step_length=1.0,
            decision_interval=5.0,
            enable_emergency=True,
        )

        # 1. Startup & TraCI Connect
        t0 = time.perf_counter()
        sim.start(seed=42 + i)
        t_startup = (time.perf_counter() - t0) * 1000.0
        startup_times_ms.append(t_startup)
        assert sim.sumo_manager.is_running, f"SUMO failed to start on run {i}"

        # 2. Stepping
        for _ in range(steps_per_run):
            t_step_0 = time.perf_counter()
            _, ok = sim.step()
            assert ok, "sim.step failed"
            t_step = (time.perf_counter() - t_step_0) * 1000.0
            step_times_ms.append(t_step)

        # 3. Shutdown
        t_shut_0 = time.perf_counter()
        sim.close()
        t_shut = (time.perf_counter() - t_shut_0) * 1000.0
        shutdown_times_ms.append(t_shut)
        assert not sim.sumo_manager.is_running, f"SUMO failed to terminate on run {i}"

        print(f"  Run {i+1}/{iterations}: Startup={t_startup:.2f}ms, Shutdown={t_shut:.2f}ms, Avg Step={statistics.mean(step_times_ms[-steps_per_run:]):.2f}ms")

    step_times_ms.sort()
    p95_idx = int(0.95 * len(step_times_ms))

    return {
        "startup_latency_ms": {
            "mean": round(statistics.mean(startup_times_ms), 2),
            "min": round(min(startup_times_ms), 2),
            "max": round(max(startup_times_ms), 2),
            "samples": len(startup_times_ms),
        },
        "stepping_latency_ms": {
            "mean": round(statistics.mean(step_times_ms), 3),
            "median": round(statistics.median(step_times_ms), 3),
            "p95": round(step_times_ms[p95_idx], 3),
            "min": round(min(step_times_ms), 3),
            "max": round(max(step_times_ms), 3),
            "throughput_steps_per_sec": round(1000.0 / statistics.mean(step_times_ms), 1),
            "samples": len(step_times_ms),
        },
        "shutdown_latency_ms": {
            "mean": round(statistics.mean(shutdown_times_ms), 2),
            "min": round(min(shutdown_times_ms), 2),
            "max": round(max(shutdown_times_ms), 2),
            "samples": len(shutdown_times_ms),
        },
    }


def benchmark_api_endpoints(iterations: int = 50) -> Dict[str, Any]:
    """Measures actual REST API request latencies via FastAPI TestClient."""
    print(f"\n[2/3] Benchmarking FastAPI Endpoints ({iterations} requests each)...")
    client = TestClient(app)

    endpoints = [
        ("GET /api/health", "/api/health"),
        ("GET /api/readiness", "/api/readiness"),
        ("GET /api/simulation/status", "/api/simulation/status"),
        ("GET /api/signals", "/api/signals"),
        ("GET /api/traffic/live", "/api/traffic/live"),
        ("GET /api/traffic/metrics", "/api/traffic/metrics"),
        ("GET /api/risks", "/api/risks"),
    ]

    results: Dict[str, Any] = {}

    for label, path in endpoints:
        durations_ms: List[float] = []
        # Warmup
        client.get(path)

        for _ in range(iterations):
            t0 = time.perf_counter()
            resp = client.get(path)
            dur = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200, f"Request to {path} returned {resp.status_code}"
            durations_ms.append(dur)

        durations_ms.sort()
        p95_idx = int(0.95 * len(durations_ms))
        results[label] = {
            "mean_ms": round(statistics.mean(durations_ms), 3),
            "median_ms": round(statistics.median(durations_ms), 3),
            "p95_ms": round(durations_ms[p95_idx], 3),
            "min_ms": round(min(durations_ms), 3),
            "max_ms": round(max(durations_ms), 3),
            "requests_per_sec": round(1000.0 / statistics.mean(durations_ms), 1),
            "samples": len(durations_ms),
        }
        print(f"  {label:<30}: Mean={results[label]['mean_ms']:.3f}ms | Median={results[label]['median_ms']:.3f}ms | P95={results[label]['p95_ms']:.3f}ms")

    return results


def main() -> None:
    print("=" * 80)
    print("SMART TRAFFIC SYSTEM — EMPIRICAL PERFORMANCE MEASUREMENT SUITE")
    print("=" * 80)

    # 1. Lifecycle & TraCI
    lifecycle_metrics = benchmark_sumo_traci_lifecycle(iterations=3, steps_per_run=30)

    # 2. API Endpoints
    api_metrics = benchmark_api_endpoints(iterations=50)

    # Compile structured metrics artifact
    full_report = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": {
            "python": sys.version,
            "platform": sys.platform,
        },
        "sumo_traci_lifecycle": lifecycle_metrics,
        "rest_api_latencies": api_metrics,
    }

    out_dir = PROJECT_ROOT / "outputs" / "benchmarks"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "engineering_performance_metrics.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    print("\n" + "=" * 80)
    print("EMPIRICAL BENCHMARK SUMMARY (ACTUAL MEASURED VALUES)")
    print("=" * 80)
    print(f"SUMO Startup Latency       : {lifecycle_metrics['startup_latency_ms']['mean']:.2f} ms (Min: {lifecycle_metrics['startup_latency_ms']['min']:.2f} ms, Max: {lifecycle_metrics['startup_latency_ms']['max']:.2f} ms)")
    print(f"SUMO Stepping Latency      : {lifecycle_metrics['stepping_latency_ms']['mean']:.3f} ms/step (Median: {lifecycle_metrics['stepping_latency_ms']['median']:.3f} ms, P95: {lifecycle_metrics['stepping_latency_ms']['p95']:.3f} ms)")
    print(f"SUMO Stepping Throughput   : {lifecycle_metrics['stepping_latency_ms']['throughput_steps_per_sec']:.1f} steps/second")
    print(f"SUMO Shutdown Latency      : {lifecycle_metrics['shutdown_latency_ms']['mean']:.2f} ms (Min: {lifecycle_metrics['shutdown_latency_ms']['min']:.2f} ms, Max: {lifecycle_metrics['shutdown_latency_ms']['max']:.2f} ms)")
    print(f"API /api/health Latency    : {api_metrics['GET /api/health']['mean_ms']:.3f} ms (P95: {api_metrics['GET /api/health']['p95_ms']:.3f} ms)")
    print(f"API /api/readiness Latency : {api_metrics['GET /api/readiness']['mean_ms']:.3f} ms (P95: {api_metrics['GET /api/readiness']['p95_ms']:.3f} ms)")
    print(f"API /api/traffic/live      : {api_metrics['GET /api/traffic/live']['mean_ms']:.3f} ms (P95: {api_metrics['GET /api/traffic/live']['p95_ms']:.3f} ms)")
    print(f"Report saved to: {out_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
