# System Architecture

## 1. High-Level Cyber-Physical Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                           MICRO-SIMULATION LAYER (SUMO)                           |
|  - OpenStreetMap Net (306 Edges, 213 Junctions, 490 Lanes, UTM 43N EPSG:32643)   |
|  - Microscopic Fleet: 378 Departed (68% Motorcycles, 27% Cars, 3% Buses, 1% HGV) |
|  - Kinematic Vehicle Following: Krauss Model with Heterogeneous Dimensions        |
|  - Environmental Emission Engine: HBEFA4/2.0 Microscopic Models                   |
+-----------------------------------------------------------------------------------+
                                        |  TraCI Protocol (TCP / Socket)
                                        v
+-----------------------------------------------------------------------------------+
|                        TELEMETRY & STATE EXTRACTION LAYER                         |
|  - Halting Queue Extraction: Approach vehicles with v <= 0.1 m/s                  |
|  - Mean Velocity & Corridor Travel Time Tracking (t_exit - t_entry)               |
|  - Cumulative Delay Riemann Sum: D_cum = sum(Q(t) * dt) [veh*s]                   |
|  - Microscopic Mass Flow Accumulation: CO2 (mg) and Fuel (mg)                     |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                            CONTROL & AI DECISION LAYER                            |
|  [Mode Selection]:                                                                |
|   1. Fixed-Time Baseline (Pre-timed 120s cycle)                                   |
|   2. Coordinated Adaptive (Queue-balancing pressure heuristic)                    |
|   3. Dueling Double-DQN (8D state, 3 transition actions: KEEP, SWITCH, EXTEND, target net) |
|   4. Multi-Agent PPO (14D local+neighbor state, actor-critic, clipped obj)        |
+-----------------------------------------------------------------------------------+
                                        |  Proposed Phase Action
                                        v
+-----------------------------------------------------------------------------------+
|                            RUNTIME SAFETY SHIELD LAYER                            |
|  - Minimum Green Constraint: g_elapsed >= 15 seconds                              |
|  - Maximum Green Constraint: g_elapsed <= 60 seconds (forced switch)              |
|  - Clearance Enforcer: Yellow (4s) + All-Red (2s) transitional phases             |
|  - Anti-Starvation Preemption: T_red <= 120s max red threshold                    |
|  - Emergency Vehicle Preemption: Green wave override for ambulance               |
+-----------------------------------------------------------------------------------+
                                        |  Safe Actuator Command
                                        v
+-----------------------------------------------------------------------------------+
|                          SUMO TRAFFIC SIGNAL ACTUATOR                             |
|  - TLS Phase State Execution (J1: 1617743335, J2: cluster_..., J3: 6970466614)   |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                    BACKEND API & LIVE MONITORING (FastAPI / WS)                   |
|  - REST Endpoints (/api/v1/corridor/metrics, /api/v1/decisions)                   |
|  - WebSocket State Stream (10 Hz broadcast to Frontend Canvas / React UI)        |
+-----------------------------------------------------------------------------------+
```
