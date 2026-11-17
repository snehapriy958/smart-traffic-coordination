# System Architecture Specification & Data Flow Diagram

**Project:** Smart Traffic Coordination System — Bengaluru Silk Board Corridor  
**Document:** System Architecture & Data Flow Reference  
**Audience:** System Architects, Examiners, Technical Reviewers

---

## 1. High-Level Architectural Overview

The Smart Traffic Coordination System is structured into seven distinct architectural layers designed for modularity, safety, and high-frequency real-time telemetry streaming:

```mermaid
flowchart TD
    subgraph L1["1. FRONTEND PRESENTATION LAYER (React 18 / Vite 5)"]
        direction TB
        UI_3D["ThreeCorridorView\n(3D Digital Twin - R3F / Three.js)\nFlyover (+8m), Underpass (-4.5m)"]
        UI_2D["LiveCorridorView\n(2D Live Topology SVG)\nQueue Densities, Aspect Heads"]
        UI_CTRL["SignalStatusPanel\n& Manual Override Modal"]
        UI_METRICS["MetricsOverview\n& EmissionsChart (Recharts)"]
        UI_COMP["ControllerComparison\n(Multi-Seed Benchmark Bars)"]
    end

    subgraph L2["2. COMMUNICATION & TELEMETRY LAYER"]
        direction LR
        WS_STREAM["WebSocket Telemetry Stream\n(/ws/traffic-stream @ 10 Hz)\nMonotonic Seq IDs, Drop-Oldest Buffer"]
        REST_API["FastAPI REST Endpoints\n(/api/simulation, /api/signals,\n/api/traffic, /api/experiments)"]
    end

    subgraph L3["3. BACKEND ORCHESTRATION LAYER (FastAPI / Python)"]
        direction TB
        SIM_SVC["SimulationService\nWorker Thread Lifecycle &\nStartup Watchdog with Graceful Kill"]
        STATE_EXT["StateExtractor\nInstantaneous Queues, Approach Speeds,\nHBEFA4 Mass Emissions (CO2, NOx, Fuel)"]
        WS_MGR["WebSocketManager\nClient Ring Buffers &\nAsync Broadcast Loop"]
    end

    subgraph L4["4. CONTROLLER & DECISION LAYER"]
        direction TB
        CTRL_BASE["Fixed-Time Baseline\n(90s Historical Silk Board Split)"]
        CTRL_ADAPT["Coordinated Adaptive\n(Queue-Pressure Split & Green Waves)"]
        CTRL_DQN["MARL Double-DQN (Stage A)\n(Dueling Q-Networks on 14-dim States)"]
        CTRL_PPO["MARL Actor-Critic PPO (Stage A)\n(Discrete Actor Head on 14-dim States)"]
    end

    subgraph L5["5. DETERMINISTIC SAFETY SHIELD"]
        direction TB
        SHIELD_MIN["Minimum Green Guardrail\n(Hard min_green = 15.0s lower bound)"]
        SHIELD_STARVE["Anti-Starvation Preemption\n(Hard max_red = 60.0s threshold;\nForced SWITCH on queued cross-street)"]
        SHIELD_YEL["Yellow Clearance Transitions\n(Mandatory 3.0s yellow duration)"]
        SHIELD_EMERG["Emergency Wave Coordinator\n(Dedicated green wave for ambulance_0)"]
    end

    subgraph L6["6. SIMULATION LAYER (Eclipse SUMO 1.26.0 / TraCI)"]
        direction LR
        SUMO_CORE["SUMO Micro-Simulation Engine\n(Step Length = 1.0s, Krauss Model sigma=0.5)"]
        TRACI_SOCK["TraCI TCP Loopback Interface\n(Scoped Subprocess Proxy, Dynamic Port)"]
        NET_J1["J1: Madiwala Checkpost\n(Depressed Underpass -4.5m)"]
        NET_J2["J2: Central Silk Board\n(Elevated Flyover +8.0m)"]
        NET_J3["J3: Rupena Agrahara\n(Dispersal Intersection)"]
    end

    subgraph L7["7. DATA & PERSISTENCE LAYER"]
        direction LR
        DB_SQLITE["SQLite Database\n(Timezone-Aware UTC SQLAlchemy Models)"]
        CKPT_STORE["PyTorch Checkpoints\n(checkpoints/marl_*.json)"]
        VALID_STORE["Validation Benchmark Store\n(outputs/validation/10seeds/)"]
    end

    %% Data flow connections
    UI_3D <--> REST_API
    UI_2D <--> WS_STREAM
    UI_CTRL <--> REST_API
    UI_METRICS <--> WS_STREAM
    UI_COMP <--> REST_API

    WS_STREAM <--> WS_MGR
    REST_API <--> SIM_SVC

    SIM_SVC --> STATE_EXT
    SIM_SVC --> TRACI_SOCK
    STATE_EXT --> WS_MGR
    STATE_EXT --> DB_SQLITE

    SIM_SVC --> L4
    L4 --> L5
    L5 --> TRACI_SOCK
    TRACI_SOCK <--> SUMO_CORE

    SUMO_CORE --- NET_J1
    SUMO_CORE --- NET_J2
    SUMO_CORE --- NET_J3

    L4 -.-> CKPT_STORE
    SIM_SVC -.-> VALID_STORE
```

---

## 2. Layer-by-Layer Technical Specification

### Layer 1: Frontend Presentation Layer (React 18 / Vite 5)
- **Framework:** React 18 SPA with Vite 5 compilation.
- **Components:**
  - `ThreeCorridorView.jsx`: WebGL / React Three Fiber interactive 3D spatial twin rendering true roadway elevations: Ground ($Y = 0$), elevated Silk Board Flyover ($Y = +8.0\text{ m}$) with cylindrical support piers, and depressed Madiwala Underpass ($Y = -4.5\text{ m}$).
  - `LiveCorridorView.jsx`: Real-time 2D SVG canvas displaying arterial topology, per-junction queue densities, live vehicle counts, approach speeds, and active signal aspects.
  - `SignalStatusPanel.jsx`: Visual 3-aspect signal heads (Red, Yellow, Green) and manual phase override dispatch controls.
  - `MetricsOverview.jsx` & `EmissionsChart.jsx`: Real-time KPI summary widgets and historical emissions area charts powered by Recharts.
  - `ControllerComparison.jsx`: Empirical benchmark comparison bar charts showing multi-seed comparative travel times, delays, and emissions.

### Layer 2: Communication & Telemetry Layer
- **REST Endpoints (FastAPI on Port 8000):**
  - `/api/simulation/start`, `/stop`, `/reset`, `/status`: Complete simulation lifecycle control.
  - `/api/signals/override`: Manual signal phase override with safety enforcement.
  - `/api/traffic/live`: Current arterial throughput, active counts, and speed metrics.
  - `/api/experiments/compare`: Statistical comparison across controllers.
- **WebSocket Telemetry Stream (`/ws/traffic-stream`):**
  - Broadcast rate: **10 Hz** (every 100 ms).
  - Sequence tracking: Monotonically increasing 64-bit integer sequence IDs (`seq_id`).
  - Buffering strategy: Ring buffer with drop-oldest eviction policy to prevent slow-client memory bloat.

### Layer 3: Backend Orchestration Layer (FastAPI / Python)
- **`SimulationService` (`backend/simulation_service.py`):**  
  Manages background worker threads, monitors execution via a dedicated `StartupWatchdog` thread, captures process PIDs, and guarantees graceful TraCI closure without orphaned `sumo.exe` instances.
- **`StateExtractor` (`traffic_service/state_extractor.py`):**  
  Samples microscopic approach queues (vehicles with speed $\le 1.39\text{ m/s}$), calculates instantaneous approach speeds, and computes cumulative HBEFA4 emissions.
- **`Database` (`backend/database.py`, `backend/models.py`):**  
  Persists simulation runs, metrics, and emergency events in SQLite using timezone-aware UTC timestamps.

### Layer 4: Controller & Decision Layer
- **Fixed-Time Baseline:** Uncoordinated pre-timed splits (90-second cycle) modeled on historical Silk Board signal plans.
- **Coordinated Adaptive Controller:** Dynamic queue-proportional phase allocation with green-wave coordination offsets across $J_1 \to J_2 \to J_3$.
- **MARL Double-DQN (Stage A):** Multi-agent value-based Q-learning operating on normalized 14-dimensional state vectors with target networks and experience replay.
- **MARL Actor-Critic PPO (Stage A):** Multi-agent Proximal Policy Optimization operating on discrete actor-critic heads.

### Layer 5: Deterministic Safety Shield
- **Minimum Green Time Guardrail:** Enforces `min_green = 15.0s`. Prevents rapid phase flapping.
- **Anti-Starvation Preemption:** Enforces `max_green = 60.0s`. When any approach red duration reaches $60.0\text{ s}$ with queued vehicles, the shield forces a transition to yellow and clears the starved approach.
- **Safe Yellow Clearance:** Mandatory 3.0-second yellow transition on all switches to prevent vehicular collisions.
- **Emergency Priority Preemption:** Dynamic arterial green wave that forces priority phases ahead of approaching emergency vehicles (`ambulance_0`).

### Layer 6: Simulation Layer (Eclipse SUMO / TraCI)
- **Engine:** Eclipse SUMO 1.26.0 running in discrete time-step mode ($\Delta t = 1.0\text{ s}$).
- **Car-Following Model:** Calibrated Krauss model with stochastic deceleration noise ($\sigma = 0.5$).
- **Network Scope:** 3 intersections along Hosur Road: $J_1$ (Madiwala Checkpost), $J_2$ (Central Silk Board), and $J_3$ (Rupena Agrahara).

### Layer 7: Data & Persistence Layer
- **Model Checkpoints:** PyTorch JSON weight dictionaries stored in `checkpoints/`.
- **Validation Benchmarks:** Master 10-seed datasets and historical 3-seed artifacts in `outputs/validation/`.

---
**Specification Approved by:** Antigravity Senior Engineering & Verification Auditor
