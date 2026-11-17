# LIVE DEMONSTRATION READINESS CHECKLIST
## Operational Runbook, Demonstration Script, and Fail-Safe Procedures
**Auditor**: Senior Systems Architect & Evaluation Lead  
**Date**: November 17, 2026  
**Target Environment**: Windows 11 / PowerShell Local Host

---

### 1. Overall Demonstration Readiness Verdict

### **STATUS: DEMO-READY (GO)**

- **Backend**: FastAPI server initializes in $< 1.5\,\text{s}$ with SQLite database and all 28 REST endpoints active.
- **Frontend**: Vite production build compiled clean (3,337 modules transformed, 0 errors). Node tests 96/96 pass.
- **Simulation**: SUMO 1.26.0 TraCI interface verified with process-scoped PID management and zero socket freezes.
- **Research Artifacts**: Authoritative 10-seed master benchmark, Series 4B, and Series 4E datasets are completely verified and pre-rendered.

---

### 2. Startup Procedures (Two Dedicated Terminals)

#### Terminal 1 — Backend API & Telemetry Server:
```powershell
# Navigate to project root
cd C:\Developers\Sneha\Projects\hybrid-traffic-control

# Start FastAPI Uvicorn Server on Port 8000
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --log-level info
```
*Expected Output*:
```
[INFO] [main] Starting Smart Traffic Coordination backend application...
[INFO] [database] Initializing SQLite database schema...
[INFO] [main] Uvicorn running on http://127.0.0.1:8000
```

#### Terminal 2 — Frontend User Interface:
```powershell
# Navigate to frontend directory
cd C:\Developers\Sneha\Projects\hybrid-traffic-control\frontend

# Start Vite Development Server
npm run dev
```
*Expected Output*:
```
  VITE v5.4.21  ready in 480 ms
  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```
*Open in Browser*: Navigate to **`http://localhost:5173/`**.

---

### 3. Step-by-Step Live Demonstration Script (10–12 Minutes)

#### Step 1: System Health & Overview Dashboard (1.5 min)
- **Action**: Open `http://localhost:5173/`. Point out the top header:
  - WebSocket indicator: **CONNECTED** (Green).
  - SUMO Simulator: **Available (v1.26.0)**.
  - Active Session: UUID generated.
- **Key Talking Point**: "This platform models Bengaluru's notoriously congested Silk Board arterial corridor using microscopic SUMO traffic simulation and autonomous multi-agent reinforcement learning."

#### Step 2: Live 2D Corridor & Signal Timing (2 min)
- **Action**: On the "Live Corridor & Signals" tab, review the 3 junctions:
  - **J1 (Hosur North Feeder)**: Phase 2 Green.
  - **J2 (Central Silk Board)**: Phase 0 Arterial Green (highest queue volume).
  - **J3 (Hosur South Feeder)**: Phase 2 Green.
- **Observe**: Elapsed green timers and approach queues update live at 1 Hz via WebSocket.

#### Step 3: Controller Performance Benchmark (2 min)
- **Action**: Switch to the "Emissions & Benchmarks" tab.
- **Review**: Point to the **Authoritative 10-Seed Master Benchmark**:
  - **Fixed-Time Baseline**: $90.02\,\text{s}$ Travel Time, $12{,}373\,\text{veh}\cdot\text{s}$ Delay, $23.18\,\text{L}$ Fuel.
  - **Coordinated Adaptive**: **$49.87\,\text{s}$** Travel Time (**-44.6%**), **$5{,}836\,\text{veh}\cdot\text{s}$** Delay (**-52.8%**).
  - **Double-DQN (Stage A)**: **$56.64\,\text{s}$** Travel Time (**-37.1%**), $100\%$ completed trips.
  - **PPO (Stage A)**: $85.50\,\text{s}$ Travel Time (honest reporting of policy saturation).
- **Key Talking Point**: "We do not claim AI magically solves all traffic problems. Our rigorous 10-seed master benchmark shows that a domain-informed Coordinated Adaptive controller outperforms baseline by 44.6%, with Double-DQN achieving 37.1% reduction."

#### Step 4: Safety Shield & Manual Override (2 min)
- **Action**: Click "Manual Signal Override" in the top header.
- **Test**:
  1. Select Junction **J2**, Target Phase **2** (Cross-Street Green).
  2. Leave checkbox unchecked $\implies$ System blocks: *"You must confirm the safety override acknowledgment."*
  3. Check acknowledgment $\implies$ Submit override.
- **Observe**: Signal controller schedules a strict **4.0-second yellow clearance transition** before granting green. Minimum green (15.0s) and maximum green (60.0s) are respected.

#### Step 5: 3D Digital Twin & Camera Tracking (2.5 min)
- **Action**: Switch to the **"3D Digital Twin"** tab.
- **Explore**:
  - Click **"J2: Silk Board Hub"** camera preset to focus on Central Silk Board.
  - Click **"Flyover Inspection"** to inspect the elevated Hosur Road flyover and underpass spans.
  - Click on any moving vehicle in the viewport $\implies$ Click **"Follow (veh_id)"** to enter dynamic 3rd-person chase camera mode.
- **Key Talking Point**: "The 3D Digital Twin runs entirely in WebGL using Three.js, mapping real SUMO microscopic vehicle coordinates and heading angles with 60 FPS spatial interpolation."

#### Step 6: Research & Experiments Deep Dive (2 min)
- **Action**: Click the **"Research & Experiments"** tab:
  - **Overview**: 4 research series matrix.
  - **Series 4B**: Shows that 65% to 98% of variance is driven by training seeds rather than observation dimensionality.
  - **Series 4C Live Monitor**: Reads `manifest_series_4c.json` in real time, showing 3 completed runs, 30 certified evaluations, and active status.
  - **Series 4E**: Demonstrates that passenger-weighted rewards prioritize BMTC buses (45 passengers), increasing transit priority grant rates to 88.4%.

---

### 4. Fail-Safe Fallbacks & Contingency Procedures

| Scenario | Contingency Action |
|---|---|
| **SUMO not started or TraCI socket busy** | The dashboard gracefully defaults to **Archived Telemetry Replay Mode**, surfacing the completed 10-seed master benchmark and historical runs from SQLite without breaking. |
| **WebSocket disconnects** | `SnapshotRecoveryManager` automatically displays the "RETRYING" banner, polls the authoritative REST snapshot, and reconciles state without page reload. |
| **3D Canvas WebGL context loss** | `CorridorErrorBoundary` catches WebGL exceptions and provides a one-click "Reload 3D Viewport" button or fallback to the 2D Live Corridor. |
| **Series 4C Training Active** | Master pipeline runs in the background with process-scoped PID tracking (`SumoManager`). It does not interfere with the web server port 8000 or Vite port 5173. |
