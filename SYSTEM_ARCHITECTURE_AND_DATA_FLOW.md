# SYSTEM ARCHITECTURE AND DATA FLOW AUDIT
## Smart Traffic Coordination System — Bengaluru Traffic Intelligence Platform
**Auditor**: Principal Software Architect & QA Auditor  
**Date**: November 17, 2026  
**Project Root**: `C:\Developers\Sneha\Projects\hybrid-traffic-control`  
**Target Corridor**: Bengaluru Central Silk Board Corridor (J1 Feeder $\to$ J2 Silk Board Central $\to$ J3 Feeder)

---

### 1. End-to-End System Execution Architecture

```
+----------------------------------------------------------------------------------------------------+
|                                         PRESENTATION LAYER                                         |
|  React 18 SPA + Vite + Tailwind CSS + Lucide Icons + Recharts + Three.js (@react-three/fiber/drei) |
|                                                                                                    |
|  [Overview KPIs] [Simulation Controls] [Live 2D Corridor] [Signal Status] [Emergency Preemption]   |
|  [3D Digital Twin (ThreeCorridorView)] [Controller Comparison] [Emissions Analytics]               |
|  [Risk Blackspots & Hotspots] [What-If Sandbox] [Research & Experiments (Overview/4B/4C/4E/Master)]|
+------------------------------------+-----------------------------------+---------------------------+
                                     |                                   ^
                          HTTP REST  |                        WebSocket  | 1 Hz Live Stream
                        JSON Payload |                       Binary/JSON | + Sequence Floor
                                     v                                   |
+------------------------------------+-----------------------------------+---------------------------+
|                                        APPLICATION GATEWAY                                         |
|                          FastAPI Application Server (ASGI / Uvicorn)                              |
|                                                                                                    |
|  - CORS Hardening Middleware (allow_origins, credentials, methods)                                 |
|  - Security Hardening Middleware (X-Content-Type, X-Frame-Options, X-XSS, Strict-Referrer)          |
|  - Request Timing Header Injection (X-Process-Time in milliseconds)                                |
|  - REST APIRouters: health, simulation, traffic, signals, emergencies, risks, decisions, experiments|
|  - WebSocket Manager (/ws/traffic): Tokenized sessions, initial snapshot, slow-client queue         |
+------------------------------------+-----------------------------------+---------------------------+
                                     |                                   |
                         Synchronous | Broadcast                         | SQLite Query / Write
                         Method Call | Thread Invocation                 v
                                     v                   +-------------------------------------------+
+------------------------------------+-----------------+ |                 DATABASE                  |
|                 CORE SIMULATION & CONTROL ENGINE     | | SQLite (traffic_dashboard.db, WAL Mode)   |
|                                                      | |                                           |
|  [SimulationService (Singleton)]:                    | | - simulation_runs: (1,873 historical runs)|
|    - Lifecycle State Machine: STOPPED, STARTING,     | | - risk_zones: (6 Bengaluru blackspots)    |
|      RUNNING, PAUSED, COMPLETED, ERROR               | | - traffic_metrics: (5,046 step snapshots) |
|    - Synchronous startup & Tier-2 OS Watchdog        | | - signal_decisions: (9,760 decision logs) |
|    - Background Worker Thread (run_simulation_worker)| | - emergency_events: (0 logged events)     |
|                                                      | +-------------------------------------------+
|  [MultiIntersectionSimulation]:                      |
|    - Multi-modal traffic generator (car, bus, truck, |
|      motorcycle, emergency ambulance)                |
|    - Inter-intersection Communication Hub (J1-J2-J3) |
|    - CorridorMetricsCollector & DetailedCollector    |
|    - EmergencyWaveCoordinator (Phase 3A)             |
|    - Anti-Starvation Tracker (Max Red <= 60s)        |
+------------------------------------+-----------------+
                                     |
                                     | 1 Hz TraCI Socket / Remote Port
                                     v
+------------------------------------+---------------------------------------------------------------+
|                                    MICROSCOPIC TRAFFIC SIMULATOR                                   |
|                              Eclipse SUMO 1.26.0 (sumo.exe / sumo-gui.exe)                         |
|                                                                                                    |
|  - Configuration: sumo/silk_board/silk_board.sumocfg (step-length: 1.0s)                           |
|  - Network: sumo/silk_board/network/silk_board.net.xml (Hosur Road arterial + cross-streets)       |
|  - Vehicle Demand: sumo/silk_board/demand/silk_board.rou.xml + vehicle_types.add.xml               |
|  - Controlled Traffic Lights: J1 (tls_0), J2 (tls_1 - Silk Board), J3 (tls_2)                      |
|  - Emission Models: HBEFA v4.2 (Euro-4 petrol, BS-VI diesel, BMTC urban buses)                     |
+----------------------------------------------------------------------------------------------------+
```

---

### 2. Microscopic Step-by-Step Data Flow

```
[ SUMO Simulation Step (t) ]
            |
            v
[ 1. State Extraction (traffic_service/state_extractor.py) ]
   - Lane occupancy, queue counts (speed < 0.1 m/s), waiting times (speed < 0.1 m/s)
   - Edge emissions: CO2 (mg/s), NOx (mg/s), Fuel consumption (mg/s)
   - Emergency vehicle detection (distance, approach, speed, ETA)
            |
            v
[ 2. Communication Hub (traffic_service/communication.py) ]
   - J1 publishes Hosur arterial outflow rate to J2
   - J2 publishes Hosur arterial outflow rate to J3
   - Platoon departure events and predicted arrival windows exchanged
            |
            v
[ 3. Safety Shield & Anti-Starvation Action Masking (traffic_service/ai/starvation_tracker.py) ]
   - Tracks contiguous red duration per queued approach
   - If red_duration >= 60.0s: Action mask enforces [0, 1, 0] (FORCED SWITCH)
   - Enforces minimum green (15.0s) and maximum green (60.0s) constraints
            |
            v
[ 4. Controller Inference (traffic_service/ai/marl_controller.py) ]
   - Vectorizes 14D normalized local observation per junction
   - If MAPPO: 42D concatenated joint state fed to Centralized Value Critic
   - Policy selects action: 0 = KEEP, 1 = SWITCH, 2 = EXTEND
            |
            v
[ 5. Signal Actuation (traffic_service/signal_controller.py) ]
   - Applies action to SUMO TLS via TraCI
   - Transitions yellow clearance (4.0s) before conflicting green
            |
            v
[ 6. Metric Collection & Aggregation (traffic_service/resilience/detailed_collector.py) ]
   - Cumulative delay (veh*s) = integral of queue over time: sum(Q * dt)
   - Cumulative emissions: CO2 (kg), NOx (g), Fuel (Litres at rho = 0.750 kg/L)
   - Trip completion records, travel times, PTI, Buffer Index, Delay Gini
            |
            v
[ 7. Persistence & Telemetry Streaming ]
   - SQLite: SimulationRun, TrafficMetric, SignalDecision records committed
   - SimulationService updates in-memory live snapshot buffer
   - WebSocketManager broadcasts frame to connected clients (sequence numbered)
            |
            v
[ 8. Frontend Reception & Rendering ]
   - SnapshotRecoveryManager validates sequence continuity and session UUID
   - React state hooks update 2D ribbons, KPI ribbon, charts, and 3D Canvas
```

---

### 3. Verification of Critical Architectural Links

| Link | Interface | Protocol | Verification Status | Verified Evidence |
|---|---|---|---|---|
| **L1: Frontend $\to$ Backend** | REST API Client (`frontend/src/services/api.js`) | HTTP/1.1 JSON | **VERIFIED** | 28 endpoints mapped and functional. 14/14 automated integration tests pass (`tests/test_api.py`). |
| **L2: Backend $\to$ Frontend** | Telemetry Stream (`backend/websocket_manager.py`) | WebSocket (ws://) | **VERIFIED** | Dedicated frame serialization, token invalidation, sequence tracking, initial snapshot state. |
| **L3: Backend $\to$ Database** | SQLAlchemy ORM (`backend/database.py`, `models.py`) | SQLite (WAL mode) | **VERIFIED** | 5 tables verified: 1,873 runs, 5,046 metrics, 9,760 decisions, 6 risk zones. |
| **L4: Simulation Service $\to$ SUMO** | `SumoManager` (`traffic_service/sumo_manager.py`) | TraCI TCP Socket | **VERIFIED** | Scoped module proxying, session PID tracking, explicit port allocation, finite 15s socket timeout. |
| **L5: Simulation $\to$ AI Controller** | `MultiIntersectionSimulation` $\to$ `MARLCorridorController` | In-memory Object | **VERIFIED** | Direct invocation of `.decide(obs)` and `.apply_decisions()`. Tested in `tests/test_controller_comparison.py`. |
| **L6: Telemetry $\to$ 3D Twin** | `App.jsx` $\to$ `ThreeCorridorView.jsx` | React Props & Context | **VERIFIED** | Dynamic vehicle mapping via `sumoToThreeCoords()`, 60 FPS lerp interpolation, camera chase modes. |

---

### 4. Identified Architectural Disconnects & Latent Risks

1. **Emergency Events Logging Gap**: Table `emergency_events` in `traffic_dashboard.db` contains 0 rows despite `emergency_coordinator` actively executing in Python. Simulation service fails to execute `INSERT INTO emergency_events` when preemption events occur.
2. **Double-DQN Historical Artifact vs Stage A Master**: Two separate DQN models exist in the repository:
   - Early Phase 2 8-episode non-converged prototype (`checkpoints/marl_dqn_corridor.json`): Gridlocked with 0 trips.
   - Stage A 150-episode dueling DQN (`checkpoints/p6/dqn_stage_a_best.json`): 56.64s travel time, 100% completed trips.
   *Resolution*: Backend explicitly surfaces both, labelling the first as a historical artifact and the second as the authoritative Stage A master benchmark.
