# Smart Traffic Coordination System — Bengaluru Silk Board Corridor

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![SUMO 1.26+](https://img.shields.io/badge/SUMO-1.26%2B-orange.svg)](https://eclipse.dev/sumo/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-cyan.svg)](https://react.dev/)
[![Three.js](https://img.shields.io/badge/Three.js-R3F-black.svg)](https://threejs.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-231%20Backend%20%7C%2082%20Frontend-brightgreen.svg)]()

An intelligent multi-intersection traffic signal coordination and simulation platform modeled on the **Silk Board Corridor along Hosur Road (NH 44) in Bengaluru, Karnataka, India**.

The system integrates microscopic traffic simulation (Eclipse SUMO / TraCI), multi-strategy signal controllers (Fixed-Time, Coordinated Adaptive, Multi-Agent Double-DQN, Multi-Agent PPO), deterministic safety shielding, emergency corridor preemption, and real-time telemetry streaming to a React dashboard with an interactive Three.js 3D spatial digital twin.

---

## 1. Project Overview & Problem Statement

The Silk Board intersection in South Bengaluru is one of India's most notoriously congested urban traffic bottlenecks. Key operational challenges include:
1. **Bottleneck Convergence:** High-volume traffic merging from Outer Ring Road (BTM Layout), HSR Layout, Electronic City, and Hosur Road onto a constrained corridor.
2. **Uncoordinated Actuation:** Isolated pre-timed or local-actuated controllers cause secondary shockwaves, holding arterial green while downstream approaches spill back.
3. **Cross-Street Starvation:** Aggressive green-extension on major arterials frequently starves high-volume secondary approaches (such as Madiwala Market).
4. **Emergency Vehicle Blockage:** Emergency vehicles (e.g. ambulances) get trapped in static queues without dedicated preemption waves.

### Project Objectives
- Build a calibrated microscopic corridor simulation covering intersections **$J_1$ (Madiwala Checkpost)**, **$J_2$ (Central Silk Board)**, and **$J_3$ (Rupena Agrahara / Bommanahalli)**.
- Implement and benchmark four signal control paradigms under identical traffic demand profiles.
- Design a deterministic safety shield enforcing strict minimum green ($15.0\text{ s}$) and anti-starvation maximum red ($60.0\text{ s}$) guardrails.
- Implement an emergency vehicle green wave providing rapid preemption traversal with zero queue stoppages.
- Deliver a real-time full-stack dashboard with 10 Hz WebSocket telemetry and a 3D procedural digital twin.

---

## 2. System Architecture

The application is structured into seven distinct architectural layers:

```
+----------------------------------------------------------------------------------------------------+
|                                    APPLICATION ARCHITECTURE                                       |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  1. FRONTEND LAYER (React 18 / Vite)                                                               |
|     • 3D Spatial Digital Twin (Three.js / React Three Fiber): Extruded road ribbons, flyovers      |
|     • 2D Live Corridor Canvas (SVG): Real-time queue density, speeds, 3-aspect signal aspects      |
|     • Telemetry Panels: MetricsOverview, EmissionsChart, ControllerComparison, SignalStatusPanel   |
|                                         ▲                                                          |
|  2. COMMUNICATION LAYER                 │ HTTP REST (Port 8000) & WebSocket (10 Hz Stream)         |
|     • FastAPI REST Endpoints: /api/simulation, /api/signals, /api/traffic, /api/experiments       |
|     • Streaming Telemetry: /ws/traffic-stream (Monotonic sequence IDs, reconnect recovery)         |
|                                         │                                                          |
|  3. BACKEND SERVICE LAYER (FastAPI / Python)                                                       |
|     • SimulationService: Threaded worker lifecycle, startup watchdog, safe cleanup                |
|     • StateExtractor: Instantaneous approach queues, time-mean speeds, HBEFA4 emissions           |
|     • Database Engine: SQLite with timezone-aware SQLAlchemy models                                |
|                                         ▲                                                          |
|  4. SIMULATION LAYER                    │ TraCI TCP Socket Interface                               |
|     • Eclipse SUMO Micro-Simulator: Step length = 1.0s, Krauss car-following (sigma = 0.5)         |
|     • Network Geometry: 3 Signalized Intersections (J1: Madiwala, J2: Silk Board, J3: Bommanahalli)|
|     • Vehicle Demand: 378 vehicles / run, 5 classes (motorcycle, car, bus, truck, ambulance)       |
|                                         │                                                          |
|  5. CONTROLLER LAYER                    │ Signal Decisions (Phase 0, 1, 2, 3)                      |
|     • Fixed-Time Baseline: Rigid pre-timed splits (90s cycle)                                      |
|     • Coordinated Adaptive: Dynamic queue-proportional phase split & green-wave progression        |
|     • MARL Double-DQN (Stage A): Value-based Q-network with 14-dim local state vector              |
|     • MARL Actor-Critic PPO (Stage A): Discrete policy actor-critic with discrete action space     |
|                                         │                                                          |
|  6. DETERMINISTIC SAFETY SHIELD         │ Preemption Overrides & Action Masks                      |
|     • Minimum Green Guardrail: Hard 15.0-second constraint prevents signal flicker                 |
|     • Anti-Starvation Preemption: 60.0-second maximum red forces mandatory phase switch            |
|     • Safe Yellow Transitions: 3.0-second mandatory yellow clearance before every phase change     |
|     • Emergency Preemption Coordinator: Dynamic corridor green wave for approaching ambulances     |
|                                         │                                                          |
|  7. DATA & PERSISTENCE LAYER            │ JSON / SQLite                                            |
|     • Checkpoint Store: PyTorch JSON weight dictionaries (checkpoints/)                            |
|     • Validation Suite: outputs/validation/ (Historical 3-seed & 40-run 10-seed benchmarks)        |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Technology Stack

- **Microscopic Traffic Simulator:** Eclipse SUMO 1.26.0 / TraCI Python API
- **Backend API & Orchestration:** FastAPI 0.115+, Uvicorn, Python 3.11–3.13, Pydantic v2
- **Deep Reinforcement Learning:** PyTorch 2.6+, NumPy, SciPy (Dual Double-DQN & Actor-Critic PPO)
- **Database & Persistence:** SQLite 3, SQLAlchemy 2.0+ (Timezone-aware UTC)
- **Frontend SPA Dashboard:** React 18, Vite 5, Tailwind CSS, Lucide React, Recharts
- **Spatial 3D Digital Twin:** Three.js, React Three Fiber (`@react-three/fiber`), `@react-three/drei`
- **Testing & Quality Assurance:** Pytest 8+ (231 backend tests), Node.js native test runner (82 tests)

---

## 4. Key Implemented Features

1. **Microscopic Heterogeneous Simulation:** Accurate simulation of 5 Indian traffic vehicle types with calibrated Krauss car-following parameters:
   - `motorcycle`: Length 2.2m, max speed 60 km/h, accel 2.6 m/s$^2$, decel 4.5 m/s$^2$, $\sigma = 0.5$.
   - `car`: Length 4.5m, max speed 60 km/h, accel 2.6 m/s$^2$, decel 4.5 m/s$^2$, $\sigma = 0.5$.
   - `bmtc_bus`: Length 12.0m, max speed 50 km/h, accel 1.2 m/s$^2$, decel 3.0 m/s$^2$, $\sigma = 0.5$.
   - `heavy_vehicle`: Length 10.0m, max speed 50 km/h, accel 1.0 m/s$^2$, decel 3.0 m/s$^2$, $\sigma = 0.5$.
   - `ambulance`: Length 5.0m, max speed 72 km/h, accel 3.0 m/s$^2$, decel 5.0 m/s$^2$, $\sigma = 0.2$.
2. **Four Signal Controllers:**
   - **Fixed-Time Baseline:** Standard pre-timed cycle splits based on historical Silk Board signal plans.
   - **Coordinated Adaptive Controller:** Dynamic queue-proportional phase allocation with green-wave progression offsets.
   - **MARL Double-DQN (Stage A):** Multi-agent value-based Q-learning operating on 14-dimensional normalized junction observations.
   - **MARL Actor-Critic PPO (Stage A):** Multi-agent Proximal Policy Optimization operating on discrete actor-critic heads.
3. **Deterministic Safety Shield:**
   - **Minimum Green:** 15.0 seconds hard lower bound (`min_green = 15.0s`).
   - **Anti-Starvation Preemption:** 60.0 seconds maximum red threshold (`max_green = 60.0s`). Automatically overrides policy decisions to clear starved cross-street queues.
   - **Yellow Clearance:** Mandatory 3.0-second yellow transition on all signal switches.
4. **Emergency Vehicle Preemption:** Dedicated priority wave clearing inbound ambulances (`ambulance_0`) along the Hosur arterial corridor with zero queue stoppages.
5. **Interactive Visualization Stack:**
   - **3D Spatial Digital Twin:** Procedural 3D road ribbons with accurate vertical elevations: Ground level ($Y = 0$), elevated Silk Board Flyover ($Y = +8.0\text{ m}$) with concrete support pillars, and depressed Madiwala Underpass ($Y = -4.5\text{ m}$).
   - **2D Live Corridor Canvas:** Real-time arterial topology diagram with per-junction vehicle counts, queue density color thresholds, average speeds, 3-aspect illuminated signal lights, and emergency wave alerts over WebSockets at 10 Hz.

---

## 5. Methodological Scope & Truthfulness Disclosures

To maintain strict scientific and engineering integrity, the following boundaries must be clearly understood:
- **Simulation Environment:** This platform is an **OSM-derived SUMO synthetic micro-simulation** of the Silk Board road network. It is not an active control interface connected to live physical Bangalore Traffic Police signal hardware or live camera detector feeds.
- **3D Digital Twin Scope:** The 3D view renders procedural roadway ribbons, true elevation changes (flyover/underpass), lane markings, and junction landmarks. **It does not render animated moving 3D vehicle meshes.** Real-time vehicle counts, queues, and progression are monitored via the 2D live canvas.
- **MARL Checkpoint Scope:** The evaluated RL models are **Stage A curriculum checkpoints**. MARL PPO exhibits action-head saturation at intersections $J_1$ and $J_2$, causing it to rely on the 60-second anti-starvation safety guardrail.
- **Speed Metric Definition:** The reported speed metric (`avg_speed_kmh`) is the **network-wide time-mean of instantaneous approach speeds** sampled at 1.0-second intervals across all active intersection approach lanes. It is **not** the harmonic space-mean speed derived from corridor length ($L / \bar{T}_{\text{corridor}}$).

---

## 6. Experimental Benchmark Results

### A. Definitive 10-Seed Master Benchmark ($N = 10\text{ Seeds}, df = 9, 40\text{ Runs}, 15{,}120\text{ Vehicle-Runs}$)

Evaluated over full 900-second simulations across random seeds `1` through `10` covering Peak (0–300s), Shoulder (300–600s), and Off-Peak (600–900s) regimes:

| Controller | Mean Corridor Travel Time | Travel Time Imprv. | Space-Mean Speed | Speed Change | Mean Cumulative Delay | Delay Imprv. | Paired $t$-Test ($df=9$) | Bonferroni Adjusted $p$ ($m=3$) |
|:---|---:|---:|---:|---:|---:|---:|:---:|:---:|
| **Fixed-Time Baseline** | $90.02 \pm 0.40\text{ s}$ | Baseline | $28.21 \pm 0.12\text{ km/h}$ | Baseline | $12{,}373.2 \pm 42.7\text{ veh}\cdot\text{s}$ | Baseline | — | — |
| **Coordinated Adaptive** | **$49.87 \pm 0.78\text{ s}$** | **$-44.61\%$** | **$37.98 \pm 0.08\text{ km/h}$** | **$+34.68\%$** | **$5{,}836.8 \pm 93.8\text{ veh}\cdot\text{s}$** | **$-52.82\%$** | $t = -59.25, p < 10^{-12}$ | **$p_{\text{adj}} < 10^{-11}$ (Significant)** |
| **MARL Double-DQN (Stage A)** | **$56.64 \pm 0.70\text{ s}$** | **$-37.08\%$** | **$31.46 \pm 0.14\text{ km/h}$** | **$+11.56\%$** | **$8{,}024.4 \pm 90.1\text{ veh}\cdot\text{s}$** | **$-35.13\%$** | $t = -45.57, p < 10^{-11}$ | **$p_{\text{adj}} < 10^{-10}$ (Significant)** |
| **MARL PPO (Stage A)** | **$85.50 \pm 1.84\text{ s}$** | **$-5.01\%$** | **$25.56 \pm 0.29\text{ km/h}$** | **$-9.34\%$** *(Penalty)* | **$12{,}163.6 \pm 283.5\text{ veh}\cdot\text{s}$** | **$-1.66\%$** *(n.s.)* | $t = -2.42, p = 0.0384$ | **$p_{\text{adj}} = 0.1153$ (NOT Significant)** |

### B. Historical 3-Seed Benchmark ($N = 3\text{ Seeds}, df = 2, 12\text{ Runs}, 4{,}536\text{ Vehicle-Runs}$)

| Controller | Mean Corridor Travel Time | Travel Time Imprv. | Mean Speed | Cumulative Delay | Delay Imprv. | Paired $t$-Test ($df=2$) |
|:---|---:|---:|---:|---:|---:|:---:|
| **Fixed-Time Baseline** | $89.87\text{ s}$ | Baseline | $28.28\text{ km/h}$ | $12{,}357.7\text{ veh}\cdot\text{s}$ | Baseline | — |
| **Coordinated Adaptive** | **$48.88\text{ s}$** | **$-45.61\%$** | **$38.20\text{ km/h}$** | **$5{,}736.3\text{ veh}\cdot\text{s}$** | **$-53.58\%$** | $t = -106.41, p = 0.00009$ |
| **MARL Double-DQN** | **$58.57\text{ s}$** | **$-34.82\%$** | **$31.31\text{ km/h}$** | **$8{,}169.3\text{ veh}\cdot\text{s}$** | **$-33.88\%$** | $t = -56.24, p = 0.00032$ |
| **MARL PPO** | **$88.68\text{ s}$** | **$-1.31\%$** | **$24.96\text{ km/h}$** | **$12{,}826.7\text{ veh}\cdot\text{s}$** | **$+3.81\%$** | $t = -1.06, p = 0.40$ (Not Sig.) |

### C. Vehicle Population Accounting
- **Vehicles per run:** Exactly **378 vehicles** are generated per 900-second run.
- **Trip Completion Rate:** **100% completion rate** in all 40 simulation runs ($378\text{ departed}, 378\text{ arrived}, 0\text{ unfinished}$ at $t = 900\text{ s}$).
- **Corridor Traversal Trips:** Exactly **109 vehicles (28.8%)** follow continuous route `corridor_j1_j2_j3`.
- **Feeder-Turn Movements:** Exactly **269 vehicles (71.2%)** execute turning movements entering/exiting via side streets.

---

## 7. Quickstart Setup & Execution

### Prerequisites
- Python 3.11 – 3.13
- Eclipse SUMO $\ge 1.18.0$ (Ensure `SUMO_HOME` environment variable is configured)
- Node.js v18+ / v20+ / v22+

### 1. Start Backend API Server
```powershell
# From repository root
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation will be accessible at `http://localhost:8000/docs`.

### 2. Start Frontend SPA Dashboard
```powershell
# From repository root
npm --prefix frontend run dev
```
Navigate your browser to `http://localhost:5173/`.

### 3. Run Automated Regression Test Suites
```powershell
# 1. Backend Pytest suite (231 tests)
pytest tests/ -q

# 2. Frontend Vitest suite (82 tests)
npm --prefix frontend test -- --run

# 3. Production build verification
npm --prefix frontend run build
```

---

## 8. Project Documentation Directory

For complete audit records, mathematical specifications, viva guides, and presentation slide decks:
- [`docs/FINAL_PROJECT_STATUS.md`](docs/FINAL_PROJECT_STATUS.md): Comprehensive system architecture and model inventories.
- [`docs/MATHEMATICAL_FORMULATION_AND_CONTROLLER_SPECIFICATION.md`](docs/MATHEMATICAL_FORMULATION_AND_CONTROLLER_SPECIFICATION.md): Complete mathematical derivations, emission conversions, and RL formulation.
- [`docs/LIVE_DEMONSTRATION_RUNBOOK.md`](docs/LIVE_DEMONSTRATION_RUNBOOK.md): Step-by-step practical demonstration sequence and troubleshooting runbook.
- [`docs/TECHNICAL_VIVA_PREPARATION_GUIDE.md`](docs/TECHNICAL_VIVA_PREPARATION_GUIDE.md): 65 comprehensive technical questions and in-depth answers for viva defense.
- [`docs/EXPERIMENTAL_RESULTS_10_SEEDS.md`](docs/EXPERIMENTAL_RESULTS_10_SEEDS.md): Detailed 10-seed master experimental results and statistical proofs.
- [`docs/audits/FINAL_EVIDENCE_AUDIT.md`](docs/audits/FINAL_EVIDENCE_AUDIT.md): Final forensic evidence audit verifying seeds, metrics, and safety overrides.
- [`docs/ARTIFACT_MANIFEST.md`](docs/ARTIFACT_MANIFEST.md): Inventory of experimental datasets, checkpoints, and storage recommendations.
- [`docs/ARCHITECTURE_DIAGRAM.md`](docs/ARCHITECTURE_DIAGRAM.md): Full technical architecture specifications and Mermaid diagrams.
- [`docs/PRESENTATION_SLIDES_SPECIFICATION.md`](docs/PRESENTATION_SLIDES_SPECIFICATION.md): Slide-by-slide specification for final-year engineering review.
- [`docs/Smart_Traffic_Coordination_Final_Presentation.pptx`](docs/Smart_Traffic_Coordination_Final_Presentation.pptx): Generated 15-slide PowerPoint deck.

---

## 9. License & Attribution

Developed as a Final-Year Engineering Capstone Project. Built with Eclipse SUMO, FastAPI, PyTorch, React, and Three.js.
