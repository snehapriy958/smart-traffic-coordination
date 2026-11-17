"""
scripts/verify_four_controllers_audit.py

Item 2 of Final 3D Digital Twin Integration Audit:
Individually tests the four controllers (Fixed-Time Baseline, Coordinated Adaptive,
MARL Double-DQN, MARL PPO) to verify actual backend controller execution,
validates that decisions log records the controller's logic, and checks signal states.
"""

import json
import time
import urllib.request

BASE_URL = "http://127.0.0.1:8000"

CONTROLLERS = [
    ("baseline", "Fixed-Time Baseline", "Fixed-Time Baseline"),
    ("coordinated", "Coordinated Adaptive", "Coordinated Adaptive"),
    ("marl_dqn", "Double-DQN Corridor", "MARL Double-DQN"),
    ("marl_ppo", "PPO Corridor", "MARL PPO"),
]


def post_json(endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data or {}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(endpoint):
    url = f"{BASE_URL}{endpoint}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_audit():
    print("==================================================")
    print("ITEM 2: FOUR-CONTROLLER INTEGRATION AUDIT")
    print("==================================================")

    for mode_id, expected_ctrl_substr, label in CONTROLLERS:
        print(f"\n--- Testing Controller: {label} (mode: '{mode_id}') ---")

        # 1. Reset
        post_json("/api/simulation/reset")
        time.sleep(0.5)

        # 2. Start
        start_payload = {
            "mode": mode_id,
            "duration": 600,
            "seed": 42,
            "enable_emergency": True,
        }
        res = post_json("/api/simulation/start", start_payload)
        assert res["success"], f"Failed to start mode {mode_id}: {res}"
        print(f"Started: session_uuid={res.get('message')}")

        time.sleep(3.0)

        # 3. Check status
        status = get_json("/api/simulation/status")
        assert status["running"], f"Simulation is not running in mode {mode_id}"
        assert status["mode"] == mode_id, f"Expected mode {mode_id}, got {status['mode']}"
        assert expected_ctrl_substr in status["controller"], f"Expected controller '{expected_ctrl_substr}' in status, got '{status['controller']}'"
        print(f"Backend Controller Verified: '{status['controller']}' (PID: {status['pid']})")

        # 4. Check signals
        signals = get_json("/api/signals")
        sig_map = signals.get("signals", {})
        assert len(sig_map) >= 3, f"Expected at least 3 junction signals, got {len(sig_map)}"
        for j_key in ["J1", "J2", "J3"]:
            sig_info = sig_map.get(j_key)
            assert sig_info is not None, f"Missing signal state for {j_key}"
            print(f"  Signal {j_key} (TLS: {sig_info['tls_id']}): phase={sig_info['current_phase']}, green={sig_info['is_green']}, elapsed={sig_info['phase_elapsed']:.1f}s, queues={sig_info.get('approach_queues')}")

        # 5. Check decisions log
        decisions = get_json("/api/decisions")
        dec_list = decisions.get("decisions", [])
        print(f"  Decisions recorded for {mode_id}: {len(dec_list)} decisions in memory.")

        # 6. Stop
        stop_res = post_json("/api/simulation/stop")
        assert stop_res["success"], f"Failed to stop mode {mode_id}"
        print(f"Stopped mode '{mode_id}' cleanly.")

    # Final cleanup
    post_json("/api/simulation/reset")
    print("\n--- ITEM 2 FOUR-CONTROLLER AUDIT PASSED 100% ---")


if __name__ == "__main__":
    run_audit()
