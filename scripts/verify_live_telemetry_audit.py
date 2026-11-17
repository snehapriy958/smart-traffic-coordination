"""
scripts/verify_live_telemetry_audit.py

Item 1 & 3 of Final 3D Digital Twin Integration Audit:
Verifies live TraCI vehicle telemetry streaming via REST and WebSocket,
checks coordinate integrity against network bounds, confirms clean reset.
"""

import json
import time
import urllib.request
import asyncio
import websockets

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/traffic"

NET_BOUNDS = {
    "min_x": -0.02,
    "max_x": 3381.80,
    "min_y": 2069.48,
    "max_y": 5087.69,
}

VALID_TYPES = {"car", "bmtc_bus", "motorcycle", "heavy_vehicle", "ambulance"}


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


async def test_websocket_stream():
    print("\n--- Testing WebSocket /ws/traffic Stream ---")
    received_frames = []
    async with websockets.connect(WS_URL) as ws:
        # Collect 5 consecutive frames
        for _ in range(5):
            msg = await ws.recv()
            data = json.loads(msg)
            received_frames.append(data)
            print(f"WS Frame: type={data.get('type')}, seq={data.get('sequence_number')}, sim_time={data.get('simulation_time')}, veh_count={len(data.get('vehicles', []))}")

    assert len(received_frames) == 5, f"Expected 5 frames, got {len(received_frames)}"
    for f in received_frames:
        assert "vehicles" in f, "WebSocket frame must contain 'vehicles' field"
        assert isinstance(f["vehicles"], list), "'vehicles' must be a list"
    print("WebSocket continuous vehicle telemetry streaming: PASS")
    return received_frames


def run_audit():
    print("==================================================")
    print("ITEM 1: LIVE VEHICLE TELEMETRY INDEPENDENT AUDIT")
    print("==================================================")

    # 1. Reset simulation first to ensure clean baseline
    reset_res = post_json("/api/simulation/reset")
    print("Initial reset:", reset_res)
    initial_veh = get_json("/api/traffic/vehicles")
    assert initial_veh["vehicles"] == [], f"Expected empty vehicles on reset, got {len(initial_veh['vehicles'])}"
    print("Clean state on reset (0 vehicles): PASS")

    # 2. Start simulation in coordinated mode
    start_res = post_json("/api/simulation/start", {
        "mode": "coordinated",
        "duration": 600,
        "seed": 42,
        "enable_emergency": True,
    })
    print("Simulation started:", start_res)
    assert start_res["success"], "Simulation start failed"

    # 3. Wait for vehicles to enter network
    print("Waiting 10 seconds for SUMO TraCI vehicles to spawn...")
    time.sleep(10.0)

    # 4. Query /api/traffic/vehicles
    veh_data = get_json("/api/traffic/vehicles")
    vehicles = veh_data.get("vehicles", [])
    sim_time = veh_data.get("simulation_time", 0.0)
    print(f"Queried /api/traffic/vehicles at T+{sim_time:.1f}s: {len(vehicles)} vehicles detected.")
    assert len(vehicles) > 0, "No vehicles returned from TraCI stream!"

    # 5. Verify vehicle attributes against ground-truth SUMO bounds
    for v in vehicles:
        vid = v["id"]
        vtype = v["type"]
        x = v["x"]
        y = v["y"]
        z = v["z"]
        angle = v["angle"]
        speed = v["speed"]

        assert isinstance(vid, str) and len(vid) > 0, f"Invalid vehicle ID: {vid}"
        assert vtype in VALID_TYPES, f"Unknown vehicle type: {vtype} for vehicle {vid}"
        assert NET_BOUNDS["min_x"] <= x <= NET_BOUNDS["max_x"], f"Vehicle {vid} X ({x}) outside network bounds"
        assert NET_BOUNDS["min_y"] <= y <= NET_BOUNDS["max_y"], f"Vehicle {vid} Y ({y}) outside network bounds"
        assert z in (0.0, 8.0, -4.5), f"Unexpected vertical elevation {z} for vehicle {vid}"
        assert 0.0 <= angle <= 360.0, f"Vehicle {vid} angle {angle} outside [0, 360]"
        assert speed >= 0.0, f"Vehicle {vid} speed {speed} < 0"

    print(f"Vehicle schema, coordinate bounds & type verification ({len(vehicles)} vehicles): PASS")

    # Sample top 5 vehicles
    print("Sample vehicle telemetry records:")
    for v in vehicles[:5]:
        print(f"  - ID: {v['id']}, Type: {v['type']}, Pos: ({v['x']}, {v['y']}, {v['z']}), Heading: {v['angle']} deg, Speed: {v['speed']:.2f} m/s ({v['speed']*3.6:.1f} km/h), Edge: {v.get('edge')}")

    # 6. Verify continuous WebSocket telemetry
    asyncio.run(test_websocket_stream())

    # 7. Stop simulation
    stop_res = post_json("/api/simulation/stop")
    print("Simulation stopped:", stop_res)

    # 8. Reset simulation and verify vehicle list is emptied
    post_json("/api/simulation/reset")
    post_reset_veh = get_json("/api/traffic/vehicles")
    assert post_reset_veh["vehicles"] == [], f"Expected 0 vehicles after reset, got {len(post_reset_veh['vehicles'])}"
    print("Post-run reset cleared all vehicles: PASS")
    print("\n--- ITEM 1 TELEMETRY AUDIT PASSED 100% ---")


if __name__ == "__main__":
    run_audit()
