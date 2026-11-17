# Smart Traffic Coordination System — Final Project Status

**Project:** Smart Traffic Coordination System – Bengaluru Silk Board Corridor  
**Repository:** `https://github.com/snehapriy958/Temporary`  
**Current Branch:** `marl-p6-2-curriculum-training`  
**Latest Git Commit:** `0fa845e` (`Add complete Smart Traffic Coordination project`)  
**Status Date:** 2026-11-09  
**Audit Baseline:** Phase 5 Independent Engineering Audit  

---

## 1. Executive Project Summary

The Smart Traffic Coordination System is an intelligent traffic signal control and monitoring platform designed for the highly congested Silk Board Corridor along Hosur Road in Bengaluru, Karnataka, India. The platform integrates:
1. **Macroscopic & Microscopic Traffic Simulation:** Powered by Eclipse SUMO 1.26.0 and TraCI, modeling realistic heterogeneous Indian urban traffic flows across five vehicle classes.
2. **Multi-Strategy Signal Controllers:**
   - Fixed-Time Baseline Controller.
   - Coordinated Adaptive Green-Wave Controller.
   - Multi-Agent Deep Q-Network (Double-DQN) Controller.
   - Multi-Agent Proximal Policy Optimization (PPO) Controller.
   - Multi-Agent PPO with Centralized Critic (MAPPO) architecture.
3. **Deterministic Safety Shield:** Guarantees signal safety via hard-coded 15-second minimum green bounds and a 60-second anti-starvation preemption mechanism for cross-street approaches.
4. **Emergency Vehicle Corridor Preemption:** Dedicated priority wave clearing inbound emergency vehicles (e.g., ambulances) through green-light corridors.
5. **Real-Time Telemetry & Digital Twin Visualization:**
   - **3D Spatial Digital Twin (Three.js / React Three Fiber):** Accurate geometric model of the corridor including the elevated Silk Board Flyover (+8.0m elevation), Madiwala Underpass (-4.5m depression), and concrete support piers.
   - **2D Live Corridor Canvas:** Real-time arterial topology diagram with per-junction vehicle counts, queue density color coding, speed monitors, signal aspect heads, and emergency alerts streaming over WebSockets at 10 Hz.
   - **REST API & Telemetry Engine (FastAPI):** Comprehensive asynchronous endpoints for simulation control, telemetry ingestion, accident risk zone mapping, and historical analytics.

---

## 2. System Architecture

```
+----------------------------------------------------------------------------------------------------+
|                                    APPLICATION ARCHITECTURE                                       |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|    +-----------------------------+                   +----------------------------------------+    |
|    |     REACT FRONTEND (Vite)   |                   |          FASTAPI BACKEND SERVER        |    |
|    |                             |                   |                                        |    |
|    |  • ThreeCorridorView (3D)   |◄──── REST / WS ───►  • /api/simulation (Start/Stop/Reset)  |    |
|    |  • LiveCorridorView (2D)    |     (10 Hz Stream)|  • /api/signals (Status/Override)      |    |
|    |  • SignalStatusPanel        |                   |  • /api/traffic (Live Metrics)         |    |
|    |  • OverviewKPIs & Emissions |                   |  • /ws/traffic-stream (WebSocket)      |    |
|    +-----------------------------+                   +-------------------+--------------------+    |
|                                                                          │                         |
|                                                                          ▼                         |
|                                                      +----------------------------------------+    |
|                                                      |          SIMULATION SERVICE            |    |
|                                                      |                                        |    |
|                                                      |  • Thread-safe command queue           |    |
|                                                      |  • Session UUID & Lifecycle Watchdog   |    |
|                                                      |  • Telemetry aggregator (10 Hz)        |    |
|                                                      +-------------------+--------------------+    |
|                                                                          │                         |
|                                                                          ▼                         |
|                                                      +----------------------------------------+    |
|                                                      |     MULTI-INTERSECTION SIMULATION      |    |
|                                                      |                                        |    |
|                                                      |  • J1: Madiwala Checkpost              |    |
|                                                      |  • J2: Central Silk Board              |    |
|                                                      |  • J3: Bommanahalli / Rupena Agrahara  |    |
|                                                      |  • State Extractor & Corridor Metrics  |    |
|                                                      |  • Safety Shield & Anti-Starvation     |    |
|                                                      +-------------------+--------------------+    |
|                                                                          │                         |
|                                          +-------------------------------+--------------------+    |
|                                          │                                                    │    |
|                                          ▼                                                    ▼    |
|                         +----------------------------------+          +-----------------------+    |
|                         |      CONTROLLER DISPATCH         |          |   ECLIPSE SUMO (TraCI)|    |
|                         |                                  |          |                       |    |
|                         |  • Baseline Fixed-Time           |◄──TraCI──► • silk_board.net.xml  |    |
|                         |  • Coordinated Adaptive          |  Socket  | • silk_board.rou.xml  |    |
|                         |  • MARL DQN (Trained Checkpoint) |          | • vehicle_types.add   |    |
|                         |  • MARL PPO (Trained Checkpoint) |          | • 378 vehicles/run    |    |
|                         +----------------------------------+          +-----------------------+    |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Corridor Network & Traffic Demand Model

### 3.1 Network Topology
The network models a contiguous 1.25 km arterial section of Hosur Road (NH 44) in South Bengaluru:
- **Junction J1 (Madiwala Feeder / Checkpost):** Feeds northbound traffic into the corridor; connects with the depressed Madiwala Underpass (-4.5m relative elevation).
- **Junction J2 (Central Silk Board Junction):** High-conflict rotary intersection connecting Hosur Road, Outer Ring Road (BTM Layout), and HSR Layout. Spanned by the +8.0m elevated Silk Board Flyover.
- **Junction J3 (Bommanahalli / Rupena Agrahara):** Downstream southern exit intersection managing traffic discharging toward Electronic City.

### 3.2 Vehicle Population & Trip Accounting Definitions
To maintain scientific accuracy, the following verified definitions must be applied across all reporting:
- **Vehicles Per Simulation Run:** Exactly **378 vehicles** are generated in each 900-second simulation run according to the 31 `<flow>` definitions and 1 discrete vehicle (`ambulance_0`) in `sumo/silk_board/demand/silk_board.rou.xml`.
- **Vehicle-Run Instances:** In a 12-run experimental suite (4 controllers $\times$ 3 seeds), there are exactly **4,536 vehicle-run instances** ($12 \times 378$).
- **Corridor Traversal Trips:** Exactly **109 vehicles** follow the continuous full-corridor arterial route `corridor_j1_j2_j3` ($J_1 \rightarrow J_2 \rightarrow J_3$).
- **Feeder-Turn Movements:** Exactly **269 vehicles** execute turning movements entering or exiting via arterial feeder links (e.g., Madiwala side roads, BTM Layout, Hosur cross-streets).
- **Departures & Arrivals:** In a complete 900-second run, all 378 vehicles depart and all 378 vehicles arrive at their destinations ($0\text{ unfinished}$), because vehicle insertion ends at $t = 600\text{ s}$, providing 300 seconds of off-peak network clearance.

### 3.3 Vehicle Classes
Heterogeneous vehicle classes are defined in `sumo/silk_board/demand/vehicle_types.add.xml` using calibrated Krauss car-following parameters:
1. `motorcycle`: Length 2.2m, max speed 16.67 m/s (60 km/h), accel 2.6 m/s$^2$, decel 4.5 m/s$^2$, $\sigma = 0.5$.
2. `car`: Length 4.5m, max speed 16.67 m/s (60 km/h), accel 2.6 m/s$^2$, decel 4.5 m/s$^2$, $\sigma = 0.5$.
3. `bmtc_bus`: Length 12.0m, max speed 13.89 m/s (50 km/h), accel 1.2 m/s$^2$, decel 3.0 m/s$^2$, $\sigma = 0.5$.
4. `heavy_vehicle`: Length 10.0m, max speed 13.89 m/s (50 km/h), accel 1.0 m/s$^2$, decel 3.0 m/s$^2$, $\sigma = 0.5$.
5. `ambulance`: Length 5.0m, max speed 20.0 m/s (72 km/h), accel 3.0 m/s$^2$, decel 5.0 m/s$^2$, $\sigma = 0.2$.

---

## 4. Signal Controller Implementation Status

| Controller | Implementation Source | Checkpoint File | Runtime API Availability | Verified Performance Characterization |
| :--- | :--- | :--- | :---: | :--- |
| **Fixed-Time Baseline** | `traffic_service/signal_controller.py` | None (Static) | `baseline` | Rigid uncoordinated fixed splits (90s cycle). Prone to standing queues (up to 59 veh) during peak loading. |
| **Coordinated Adaptive** | `traffic_service/multi_intersection_simulation.py` | None (Rule-Based) | `coordinated` | **Highest overall efficiency.** Dynamically adjusts cycle lengths and establishes green-wave offsets between J1, J2, and J3. Reduces arterial travel time by 45.61% and delay by 53.58%. |
| **MARL Double-DQN** | `traffic_service/ai/dqn_agent.py` | `checkpoints/marl_dqn_corridor.json` | `marl_dqn` | **Significant improvement over Baseline.** Independent agents per junction using Dueling Double-DQN networks with $\epsilon = 0.0972$. Reduces travel time by 34.82% and delay by 33.88%. |
| **MARL PPO** | `traffic_service/ai/ppo_agent.py` | `checkpoints/marl_ppo_corridor.json` | `marl_ppo` | **Conservative control policy.** Independent Actor-Critic PPO agents. Travel time improvement (1.31%) is not statistically significant. Prioritizes side-street queue clearance via anti-starvation preemption. |
| **MAPPO** | `traffic_service/ai/mappo_agent.py` | `checkpoints/p6/mappo_stage_a_best.json` | **Offline / Benchmarking Only** | Centralized Critic with Decentralized Actors. Fully validated in unit tests (`tests/test_mappo.py`), but deliberately not exposed in the runtime `SimulationMode` API enum. |

---

## 5. Visualization Stack & Capabilities

### 5.1 3D Spatial Digital Twin (`ThreeCorridorView.jsx` / `CorridorScene.jsx`)
- **Implemented Capabilities:**
  - Procedural road geometry extruded from SUMO network coordinates (`corridorNetworkGeometry.json`).
  - True elevation modeling: Ground level ($Y = 0.0\text{m}$), Silk Board Flyover ($Y = +8.0\text{m}$), Madiwala Underpass ($Y = -4.5\text{m}$).
  - Cylindrical concrete support pillars under elevated flyover spans.
  - Dashed white lane divider markings.
  - Interactive camera control via OrbitControls with smooth preset navigation (`Corridor Overview`, `J1 Feeder`, `J2 Silk Board`, `J3 Downstream`).
  - Layer visibility toggles (Ground, Flyover, Underpass, Dividers, Pillars, Junctions, Markers).
  - 3D-to-screen projected HTML junction markers.
- **Truthful Boundary:** The 3D scene renders **static infrastructure only**. It does **not** render moving 3D vehicle models or 3D traffic light heads.

### 5.2 2D Live Corridor Dashboard (`LiveCorridorView.jsx` / `SignalStatusPanel.jsx`)
- Real-time schematic topology linking J1, J2, and J3.
- Live vehicle counts per junction.
- Queue length monitors with dynamic density styling (Emerald: $\le 2\text{ veh}$, Amber: $3-7\text{ veh}$, Rose: $> 7\text{ veh}$).
- Corridor speed gauges and waiting time accumulation.
- 3-aspect virtual traffic light visualizers (illuminated Red, Yellow, Green heads).
- Active phase names, elapsed time counters, and minimum/maximum green bounds.
- Emergency vehicle preemption banners and locked junction indicators.
- Telemetry updates stream at 10 Hz over WebSockets with reconnection and snapshot recovery.

---

## 6. Safety Shield and Emergency Architecture

1. **Minimum Green Enforcement:** Every signal transition is evaluated against a hard-coded $15.0\text{-second}$ minimum green duration (`min_green = 15.0`). Overrides or AI action switches requested before $15\text{s}$ has elapsed are strictly rejected by the controller.
2. **Anti-Starvation Preemption:** If any side-street approach is held at red for $60.0\text{ seconds}$ while vehicles are queued, the safety shield overrides the AI policy and forces an immediate yellow clearance followed by a green phase switch to prevent intersection starvation.
3. **Emergency Wave Preemption:** Inbound emergency vehicles (`ambulance`) trigger an automated corridor wave that preempts conflicting movements, establishes continuous green along the arterial, and locks downstream signals until clearance is confirmed.

---

## 7. Current Test & Build Health

The repository has achieved complete regression pass rates:
- **Backend Tests (pytest):** 231 passed out of 231 tests (100% pass rate in 102.66s).
- **Frontend Tests (Vitest):** 82 passed out of 82 tests (100% pass rate across 5 test suites).
- **Production Build:** Vite v5.4.21 builds cleanly in 14.70s with 0 errors.
- **Process Teardown:** Zero orphaned SUMO instances remain in system memory after execution.
