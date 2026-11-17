# Research Paper Master Record
## Smart Traffic Coordination System — Bengaluru Silk Board Corridor

**Working Title:** Comparative Evaluation of Adaptive and Multi-Agent Reinforcement Learning-Based Traffic Signal Control in a Multi-Intersection Urban Corridor  
**Target Venues:** IEEE Transactions on Intelligent Transportation Systems (T-ITS) / Transportation Research Part C: Emerging Technologies  
**Repository:** [https://github.com/snehapriy958/Temporary](https://github.com/snehapriy958/Temporary)  
**Development Branch:** `project-evolution/industry-research-realworld`  
**Protected Baseline Commit:** `74c89aa7f307d37370561ac89ee27514e4608803`  
**Baseline Tag:** `baseline/smart-traffic-v1-verified`  
**Document Status:** Authoritative Master Research Record — Complete Empirical Verification & Scientific Evidence Base  

---

# Epistemological Taxonomy of Documented Claims

To uphold IEEE publication standards and prevent unverified assertions, every quantitative statement, property, and claim in this master record is classified into one of five rigorous epistemological categories:

| Category | Definition | Standard of Evidence | Example from this Record |
| :--- | :--- | :--- | :--- |
| **[MEASURED RESULT]** | Empirical output recorded from controlled benchmark execution. | Replicated across 10 random seeds with descriptive and inferential statistics ($N=10, df=9$). | Coordinated Adaptive travel time: $49.87\text{ s}$ vs. Baseline $90.02\text{ s}$ ($p = 5.60 \times 10^{-13}$). |
| **[IMPLEMENTATION FACT]** | Architectural, structural, or algorithmic property of the codebase. | Directly verifiable by inspecting committed source code and network XML files. | Dueling Double-DQN architecture: Linear(14,64) $\to$ ReLU $\to$ Linear(64,64) $\to$ Value/Advantage heads. |
| **[CONFIGURED VALUE]** | Explicit input parameter configured in simulation runs. | Defined in SUMO configuration XMLs, Python constants, or CLI arguments. | Simulation horizon $T = 900.0\text{ s}$; discrete time step $\Delta t = 1.0\text{ s}$; total injected vehicles $N = 378$. |
| **[ASSUMPTION]** | Domain assumption, external standard, or physical approximation. | Sourced from engineering codes (IRC, Euro 4, IS:SP:7) or domain modeling approximations. | Automotive petrol density $\rho_{\text{fuel}} = 0.750\text{ kg/L}$; lane width $3.20\text{ m}$ (IRC:54-1974). |
| **[PERFORMANCE TARGET]** | Software engineering or rendering objective to be satisfied. | Design target for system performance, not an empirical field measurement. | 3D Digital Twin target framerate $\ge 45\text{ FPS}$; TraCI broadcast latency $\le 200\text{ ms}$. |

---

# 1. Research Objective

This research investigates the design, algorithmic implementation, and empirical evaluation of intelligent traffic coordination systems along high-density urban arterial corridors. The target testbed models the infamous Central Silk Board corridor in Bengaluru, India—widely recognized as one of the most severe traffic bottlenecks in South Asia.

### Core Research Questions
1. **Corridor Progression:** Does coordinated adaptive traffic signal control with inter-junction upstream platoon anticipation reduce corridor travel time compared with conventional fixed-time pre-timed control? **[MEASURED RESULT: Yes, -44.61% reduction, p < 1e-12]**
2. **Autonomous Multi-Agent RL Discovery:** Can decentralized multi-agent reinforcement learning (MARL) policies (Double-DQN, PPO) autonomously discover green-wave arterial progression without pre-programmed phase offsets? **[MEASURED RESULT: Double-DQN achieves -37.08% reduction; PPO fails due to policy collapse]**
3. **Safety Shielding Invariants:** Can deterministic mathematical safety constraints (minimum green, maximum red anti-starvation, and yellow transitions) be integrated with stochastic neural policies to guarantee zero collision hazards and anti-starvation bounds? **[IMPLEMENTATION FACT: Enforced deterministically in `SignalController`]**
4. **Environmental Externalities:** Do microscopic delay reductions translate into measurable decreases in fuel consumption and vehicle tailpipe emissions ($\text{CO}_2, \text{NO}_x$) under microscopic emission models? **[MEASURED RESULT: Coordinated cuts CO2 and fuel by -23.14%; Double-DQN cuts by -15.17%]**
5. **Interactive Geographic Twin Fidelity:** Can an OpenStreetMap/SUMO network extraction serve as an accurate, performant, and interactive 3D digital twin for traffic operators? **[IMPLEMENTATION FACT: 306 edges, 213 junctions, 490 lanes rendered in WebGL]**

---

# 2. Existing System and Architecture

## 2.1 Simulation Environment
- **Platform:** Eclipse SUMO (Simulation of Urban Mobility) version **1.26.0** (Build: `MSVC 19.29.30133.0 Release 64-bit`) **[IMPLEMENTATION FACT]**.
- **Control Interface:** TraCI (Traffic Control Interface) operating over loopback TCP socket **[IMPLEMENTATION FACT]**.
- **Discrete Simulation Step:** $\Delta t = 1.0\text{ s}$ per simulation step (`step-length="1"` in `silk_board.sumocfg`) **[CONFIGURED VALUE]**.
- **Controller Decision Interval:** $T_{\text{decision}} = 5.0\text{ s}$ (controllers evaluate state and actuate every 5 discrete simulation steps) **[CONFIGURED VALUE]**.
- **Simulation Horizon:** $T = 900.0\text{ s}$ (15 minutes total: 600s dynamic vehicle insertion + 300s clearance window) **[CONFIGURED VALUE]**.
- **Network Configuration File:** `sumo/silk_board/network/silk_board.net.xml` **[IMPLEMENTATION FACT]**.
- **Demand Definition Files:** `sumo/silk_board/demand/silk_board.rou.xml` and `vehicle_types.add.xml` **[IMPLEMENTATION FACT]**.

## 2.2 Network Characteristics

| Topological Property | Reported Value | Source Verification | Category |
| :--- | :---: | :--- | :--- |
| **Total Road Edges** | **306** | `sumo/silk_board/network/silk_board.net.xml` | **[IMPLEMENTATION FACT]** |
| **Total Road Junctions** | **213** | `sumo/silk_board/network/silk_board.net.xml` | **[IMPLEMENTATION FACT]** |
| **Total Lanes** | **490** | `sumo/silk_board/network/silk_board.net.xml` | **[IMPLEMENTATION FACT]** |
| **Standard Lane Width** | **3.20 m** | Indian Road Congress (IRC:54-1974) urban standard | **[ASSUMPTION]** |
| **Coordinate Reference System** | **WGS84 / UTM Zone 43N** | `projParameter="+proj=utm +zone=43 +ellps=WGS84"` | **[IMPLEMENTATION FACT]** |
| **CRS Identifier** | **EPSG:32643** | Projected coordinate system (Northern Hemisphere) | **[IMPLEMENTATION FACT]** |
| **SUMO Network Offset** | **`(-782139.09, -1426342.97)`** | `netOffset` translation to origin | **[IMPLEMENTATION FACT]** |
| **Geographic Extent (Lat/Lon)** | **`12.819088°N – 12.935190°N, 77.580046°E – 77.782362°E`** | South Bengaluru traffic basin | **[IMPLEMENTATION FACT]** |
| **Cartesian Bounding Box** | **`[0.0, 0.0] × [4350.80m, 5086.35m]`** | `convBoundary` in `silk_board.net.xml` | **[IMPLEMENTATION FACT]** |

### Corridor Study Junctions & TLS Mapping

```
[North: Hosur Rd Entry - Edge 172853382#2]
                   |
                   v
+------------------------------------+
| Junction J1: Madiwala Checkpost    |  TLS ID: 1617743335
| Cross Street: St. John's Hospital  |  Phases: 0 (Cross G), 1 (Y), 2 (Hosur G), 3 (Y)
+------------------------------------+
                   |
          (Edge 172853382#3: ~380m)
                   v
+------------------------------------+
| Junction J2: Central Silk Board    |  TLS ID: GS_cluster_10282769895_10775075568...
| Multi-leg Rotary & ORR Interchange |  Phases: 0 (Hosur G), 1 (Y), 2 (Madiwala G), 3 (Y)
+------------------------------------+
                   |
          (Edge 1148717038#0: ~420m)
                   v
+------------------------------------+
| Junction J3: Rupena Agrahara       |  TLS ID: 6970466614
| Elevated Highway Ramp Entry        |  Phases: 0 (Cross G), 1 (Y), 2 (Hosur G), 3 (Y)
+------------------------------------+
                   |
                   v
[South: Electronic City Exit - Edge 40696223#1]
```

## 2.3 Software Architecture

| Architecture Layer | Component & Technology | Functionality & Source Location | Category |
| :--- | :--- | :--- | :--- |
| **Microscopic Engine** | Eclipse SUMO 1.26.0 + TraCI | Microscopic kinematic simulation ([`traffic_service/sumo_manager.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/sumo_manager.py)) | **[IMPLEMENTATION FACT]** |
| **State Extraction** | `IntersectionStateExtractor` | Real-time queue, waiting time, speed, and emission sampling ([`traffic_service/state_extractor.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/state_extractor.py)) | **[IMPLEMENTATION FACT]** |
| **Inter-Junction Comms**| `CorridorCommunicationHub` | Virtual platoon release messages and upstream inflow prediction ([`traffic_service/communication.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/communication.py)) | **[IMPLEMENTATION FACT]** |
| **Emergency Coordinator**| `EmergencyWaveCoordinator` | 250m upstream ambulance detection and green-wave locking ([`traffic_service/emergency_wave.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/emergency_wave.py)) | **[IMPLEMENTATION FACT]** |
| **Deterministic Shield** | `SignalController` | Hard constraints: min-green 15s, max-green 60s, yellow 4s ([`traffic_service/signal_controller.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/signal_controller.py)) | **[IMPLEMENTATION FACT]** |
| **AI Inference** | PyTorch 2.8.0 + NumPy 2.3.3 | Dueling Double-DQN and Actor-Critic PPO execution ([`traffic_service/ai/`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/)) | **[IMPLEMENTATION FACT]** |
| **Backend Web Service** | Python 3.13 + FastAPI 0.141.1 | REST APIs, background TraCI worker thread, SQLite storage ([`backend/main.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/backend/main.py)) | **[IMPLEMENTATION FACT]** |
| **Telemetry Streaming** | `WebSocketManager` | 1.0 Hz non-blocking state broadcasting (`/ws/traffic`) ([`backend/websocket_manager.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/backend/websocket_manager.py)) | **[IMPLEMENTATION FACT]** |
| **3D Digital Twin** | React 18.3 + Three.js 0.187.0 | WebGL area-wide twin, 60 FPS vehicle lerp, gantry signals ([`frontend/src/components/ThreeCorridor/`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/frontend/src/components/ThreeCorridor/)) | **[IMPLEMENTATION FACT]** |
| **Automated Testing** | Pytest (231 tests) + Vitest (91 tests) | Automated regression, safety invariant, and integration testing ([`tests/`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/tests/)) | **[IMPLEMENTATION FACT]** |

---

# 3. Traffic Control Models Evaluated

## 3.1 Fixed-Time Controller
The Fixed-Time baseline models conventional pre-timed cyclic coordination without dynamic detector actuation:
- **Cycle Duration:** $C = 90.0\text{ s}$ per cycle **[CONFIGURED VALUE]**.
- **Phase Allocations:**
  - $J_1$: Cross green $g_0 = 37.0\text{s}$, Yellow $y_1 = 4.0\text{s}$, Hosur green $g_2 = 45.0\text{s}$, Yellow $y_3 = 4.0\text{s}$.
  - $J_2$: Hosur green $g_0 = 45.0\text{s}$, Yellow $y_1 = 4.0\text{s}$, Madiwala green $g_2 = 37.0\text{s}$, Yellow $y_3 = 4.0\text{s}$.
  - $J_3$: Cross green $g_0 = 37.0\text{s}$, Yellow $y_1 = 4.0\text{s}$, Hosur green $g_2 = 45.0\text{s}$, Yellow $y_3 = 4.0\text{s}$.
- **Mathematical Invariant:** $\sum g_i + \sum y_i = 90.0\text{ s}$. No green extension or detector feedback **[IMPLEMENTATION FACT]**.

## 3.2 Coordinated Adaptive Controller
Implemented in [`traffic_service/multi_intersection_simulation.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/multi_intersection_simulation.py):

### Central Junction $J_2$ (Upstream Inflow Anticipation):
At each step $t$ while $J_2$ signal is green and not locked by emergency:
1. Sample instantaneous approach queues: $Q_{\text{hosur}}(t)$ and $Q_{\text{madiwala}}(t)$ **[IMPLEMENTATION FACT]**.
2. Calculate anticipated inflow released by upstream junction $J_1$:
   $$Q_{\text{upstream}}(t) = \left\lfloor 5.0 \times \text{hub.get\_expected\_inflow}("J2") \right\rfloor$$
3. Compute effective arterial queue pressure:
   $$Q_{\text{eff,hosur}}(t) = Q_{\text{hosur}}(t) + Q_{\text{upstream}}(t)$$
4. Actuation Decision Logic:
   - **When in Hosur Green (Phase 0):**
     $$\text{Switch to Phase 2} \iff g_{\text{elapsed}} \ge 15.0\text{s} \land Q_{\text{madiwala}} > Q_{\text{eff,hosur}} + 2$$
     $$\text{Extend Phase 0} \iff Q_{\text{eff,hosur}} > 0 \land Q_{\text{eff,hosur}} \ge Q_{\text{madiwala}} \land g_{\text{elapsed}} < 60.0\text{s}$$
   - **When in Madiwala Green (Phase 2):**
     $$\text{Switch to Phase 0} \iff g_{\text{elapsed}} \ge 15.0\text{s} \land Q_{\text{eff,hosur}} > Q_{\text{madiwala}} + 2$$
     $$\text{Extend Phase 2} \iff Q_{\text{madiwala}} > 0 \land Q_{\text{madiwala}} \ge Q_{\text{eff,hosur}} \land g_{\text{elapsed}} < 60.0\text{s}$$

### Outer Junctions $J_1$ and $J_3$ (Progression Alignment):
- Target arterial corridor green: Phase 2.
- **When in Arterial Green (Phase 2):**
  $$\text{Extend Green} \iff Q_{\text{corridor}} > 0 \land g_{\text{elapsed}} < 60.0\text{s}$$
  $$\text{Switch to Cross} \iff g_{\text{elapsed}} \ge 15.0\text{s} \land Q_{\text{cross}} > Q_{\text{corridor}} + 2$$
- **When in Cross Green (Phase 0):**
  $$\text{Switch to Corridor} \iff g_{\text{elapsed}} \ge 15.0\text{s} \land Q_{\text{corridor}} > Q_{\text{cross}}$$

## 3.3 Multi-Agent Reinforcement Learning (MARL) Formulations

### Observation Vector Space ($s_j \in \mathbb{R}^{14}$)
Vectorized by `CorridorObservationSpace.vectorize_junction()` ([`traffic_service/ai/env.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/env.py)):

| Index | Feature Symbol | Raw Feature Source | Normalization Constant | Value Range | Category |
|:---:|:---|:---|:---:|:---:|:---:|
| 0 | $\phi_{\text{norm}}$ | Active TLS phase index | $/ 3.0$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 1 | $g_{\text{elapsed,norm}}$ | Elapsed seconds in active phase | $/ 60.0\text{ s}$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 2 | $t_{\text{switch,norm}}$ | Countdown to max green limit | $/ 60.0\text{ s}$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 3 | $c_{\text{switch}}$ | Minimum green satisfaction flag | $\mathbf{1}_{\{g_{\text{elapsed}} \ge 15.0\text{s}\}}$ | $\{0.0, 1.0\}$ | **[IMPLEMENTATION FACT]** |
| 4 | $Q_{\text{corridor,norm}}$ | Hosur Road approach queue count | $/ 50.0\text{ veh}$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 5 | $Q_{\text{side,norm}}$ | Cross street approach queue count | $/ 50.0\text{ veh}$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 6 | $Q_{\text{total,norm}}$ | Total intersection queue count | $/ 100.0\text{ veh}$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 7 | $v_{\text{avg,norm}}$ | Mean approach vehicle speed | $/ 60.0\text{ km/h}$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 8 | $W_{\text{norm}}$ | Total approach accumulated wait time | $/ 300.0\text{ s}$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 9 | $N_{\text{veh,norm}}$ | Total vehicles approaching intersection | $/ 100.0\text{ veh}$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 10 | $\dot{m}_{\text{CO}_2,\text{norm}}$ | Instantaneous intersection $\text{CO}_2$ rate | $/ 10{,}000.0\text{ mg/s}$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 11 | $q_{\text{inflow,norm}}$ | Predicted upstream corridor inflow rate | $/ 10.0\text{ veh/s}$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 12 | $N_{\text{platoon,norm}}$ | Approaching coordinated vehicle platoons | $/ 5.0\text{ platoons}$ | $[0.0, 1.0]$ | **[IMPLEMENTATION FACT]** |
| 13 | $E_{\text{flag}}$ | Emergency vehicle within 250m horizon | $\mathbf{1}_{\{d_{\text{ambulance}} \le 250\text{m}\}}$ | $\{0.0, 1.0\}$ | **[IMPLEMENTATION FACT]** |

**Centralized Corridor State (MAPPO Critic):**
$$s_{\text{corridor}} = \left[ s_{J_1} \,\|\, s_{J_2} \,\|\, s_{J_3} \right] \in \mathbb{R}^{42}$$

### Action Space ($\mathcal{A}$)
$$\mathcal{A} = \{0: \text{KEEP}, \; 1: \text{SWITCH}, \; 2: \text{EXTEND}\}$$
- `KEEP` ($0$): Hold active phase duration without alteration.
- `SWITCH` ($1$): Initiate safe transition to conflicting green through mandatory 4.0s yellow.
- `EXTEND` ($2$): Extend active green by $+10.0\text{ s}$ up to $60.0\text{ s}$.

### Multi-Objective Composite Reward Function
Implemented in [`traffic_service/ai/env.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/env.py):
$$R_{\text{local}, j}(t) = - w_q \left(\frac{Q_j}{30}\right) - w_w \left(\frac{W_j}{200}\right) + w_v \left(\frac{\bar{v}_j}{40}\right) - w_e \left(\frac{\dot{m}_{\text{CO}_2, j}}{5000}\right) - w_{\text{chatter}} \mathbf{1}_{\{\Delta \phi \land a=\text{SWITCH}\}} - w_{\text{emerg}} \mathbf{1}_{\{\text{amb\_halt}\}} + w_{\text{prog}} R_{\text{prog}}$$
$$R_{\text{global}}(t) = w_{\text{thru}} \Delta M_{\text{completed}} - w_{\text{corridor}} \left(\frac{\sum_j Q_j}{90}\right) - w_{\text{starve}} N_{\text{starved}} - w_{\text{flow}} P_{\text{integrity}}$$
$$R_{\text{mixed}, j}(t) = (1 - \alpha) R_{\text{local}, j}(t) + \alpha R_{\text{global}}(t)$$

**Exact Reward Coefficients (`RewardWeights`) [CONFIGURED VALUES]:**
$$\alpha = 0.50, \quad w_q = 0.35, \quad w_w = 0.30, \quad w_v = 0.15, \quad w_{\text{thru}} = 0.50, \quad w_e = 0.10$$
$$w_{\text{emerg}} = 1.00, \quad w_{\text{chatter}} = 0.05, \quad w_{\text{prog}} = 0.25, \quad w_{\text{corridor}} = 0.50, \quad w_{\text{starve}} = 0.50, \quad w_{\text{flow}} = 0.30$$

### Neural Network Architectures & Hyperparameters

```
Dueling Double-DQN:
Input (14) --> Linear(14, 64) --> ReLU --> Linear(64, 64) --> ReLU
                 |                                  |
                 v                                  v
       Value Stream V(s):                 Advantage Stream A(s, a):
       Linear(64, 32) --> ReLU            Linear(64, 32) --> ReLU
       Linear(32, 1)                      Linear(32, 3)
                 \                                  /
                  --> Q(s, a) = V(s) + (A - mean(A))

Actor-Critic PPO:
Input (14) --> Linear(14, 64) --> ReLU --> Linear(64, 64) --> ReLU
                 |                                  |
                 v                                  v
       Actor Head pi(a|s):                Critic Head V(s):
       Linear(64, 32) --> ReLU            Linear(64, 32) --> ReLU
       Linear(32, 3) --> Softmax          Linear(32, 1)
```

| Hyperparameter | Double-DQN Value | Actor-Critic PPO Value | MAPPO Value | Category |
| :--- | :---: | :---: | :---: | :--- |
| **Input Dimension** | 14 | 14 | Actor: 14, Critic: 42 | **[IMPLEMENTATION FACT]** |
| **Output Dimension** | 3 actions | 3 action logits | Actor: 3, Critic: 1 | **[IMPLEMENTATION FACT]** |
| **Trunk Layers** | $[64, 64]$ | $[64, 64]$ | Actor: $[64, 64]$, Critic: $[128, 64]$ | **[IMPLEMENTATION FACT]** |
| **Head Layers** | $[32]$ (Value & Adv) | $[32]$ (Actor & Critic) | $[32]$ | **[IMPLEMENTATION FACT]** |
| **Optimizer** | Adam | Adam | Adam | **[IMPLEMENTATION FACT]** |
| **Learning Rate** | $1.0 \times 10^{-3}$ | $3.0 \times 10^{-4}$ | Actor: $3 \times 10^{-4}$, Critic: $1 \times 10^{-3}$ | **[CONFIGURED VALUE]** |
| **Discount Factor ($\gamma$)** | $0.95$ | $0.99$ | $0.99$ | **[CONFIGURED VALUE]** |
| **GAE Parameter ($\lambda$)** | — | $0.95$ | $0.95$ | **[CONFIGURED VALUE]** |
| **PPO Clip Ratio ($\epsilon$)**| — | $0.20$ | $0.20$ | **[CONFIGURED VALUE]** |
| **Entropy Coefficient** | — | $0.01$ | $0.01$ | **[CONFIGURED VALUE]** |
| **Value Loss Coefficient** | — | $0.50$ | $0.50$ | **[CONFIGURED VALUE]** |
| **Replay Buffer Capacity** | $10{,}000$ transitions | $2{,}048$ steps (on-policy) | $2{,}048$ steps (on-policy) | **[CONFIGURED VALUE]** |
| **Mini-batch Size** | 32 | 64 | 64 | **[CONFIGURED VALUE]** |
| **Target Update Interval** | 50 steps | — | — | **[CONFIGURED VALUE]** |
| **Exploration ($\epsilon$)** | $1.0 \to 0.05$ (decay: 0.995) | Categorical entropy | Categorical entropy | **[CONFIGURED VALUE]** |
| **Weight Initialization** | Kaiming Normal (He) | Kaiming Normal (He) | Kaiming Normal (He) | **[IMPLEMENTATION FACT]** |

## 3.4 Webster Optimum Signal Timing Controller (Classical Baseline 1)

Implemented in [`traffic_service/webster_controller.py`](file:///C:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/webster_controller.py) and integrated into [`traffic_service/multi_intersection_simulation.py`](file:///C:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/multi_intersection_simulation.py) **[IMPLEMENTATION FACT]**.

### 3.4.1 Mathematical Formulation
Webster's method (Webster 1958; Indian Roads Congress IRC:93-1985) establishes an analytical delay-minimizing fixed-time timing plan derived from critical movement flow ratios and saturation rates:

1. **Critical Flow Ratios ($y_i$):**
   $$y_i = \frac{q_i}{s_i}, \quad Y = \sum_{i} y_i$$
   where $q_i$ is the critical arrival flow rate ($\text{veh/h}$), $s_i$ is the saturation flow rate ($\text{veh/h}$), and $Y$ is the intersection degree of saturation **[IMPLEMENTATION FACT]**.

2. **Theoretical Optimum Cycle Length ($C_0$):**
   $$C_0 = \frac{1.5 L + 5}{1 - Y}$$
   where $L = \sum_i l_i$ is the total intersection lost time per cycle in seconds **[IMPLEMENTATION FACT]**.
   In 2-phase control where startup lost time ($2.0\text{ s}$) balances clearance extension, $L$ equals the sum of yellow clearance durations: $L = \sum_i y_i$ ($8.0\text{ s}$ at $J_1/J_3$, $12.0\text{ s}$ at $J_2$) **[ASSUMPTION]**.

3. **Cycle Length Bounds & Oversaturation Guards:**
   - **Oversaturation ($Y \ge 1.0$ or $Y \ge 0.95$):** $C_0$ is clamped to $C_{\max} = 120.0\text{ s}$ to prevent infinite cycle length or division-by-zero **[CONFIGURED VALUE]**.
   - **Minimum Feasible Bound:** $C_{\text{feasible, min}} = L + \sum_{i} g_{\min, i} = L + n \cdot g_{\min}$. Bounds requiring $C_{\max} < C_{\text{feasible, min}}$ are rejected via `ValueError` **[IMPLEMENTATION FACT]**.
   - **Applied Cycle Length:** Clamped within $[\max(C_{\min}, C_{\text{feasible, min}}), C_{\max}]$ where $C_{\min} = 45.0\text{ s}$ and $C_{\max} = 120.0\text{ s}$ **[CONFIGURED VALUE]**.

### 3.4.2 Constrained Green Allocation Engine
Available effective green time in the cycle:
$$G = C_{\text{applied}} - L$$

- **Unconstrained Allocation:**
  $$g_{i,\text{raw}} = \frac{y_i}{Y} G$$
  If all $g_{i,\text{raw}}$ satisfy $g_{\min} \le g_{i,\text{raw}} \le g_{\max}$ ($15.0\text{ s} \le g_i \le 60.0\text{ s}$), the pure proportional split is applied directly **[IMPLEMENTATION FACT]**.
- **Constrained Boundary Allocation:**
  If any phase breaches bounds (e.g. cross street zero demand $y_0 = 0$), `_allocate_constrained_green` floors all phases to $g_{\min} = 15.0\text{ s}$, iteratively allocating remaining green $G - n \cdot g_{\min}$ proportionally to active demand. If a phase saturates at $g_{\max} = 60.0\text{ s}$, excess green is diverted to remaining unconstrained phases **[IMPLEMENTATION FACT]**.
- **Cycle Invariant:** The actual cycle length satisfies $\sum_{i} g_i + L == C_{\text{actual}}$ unconditionally **[IMPLEMENTATION FACT]**.

### 3.4.3 Junction-Specific Timing Configurations & Provenance

| Junction | Phase | Approach Edge & Description | Lanes | Saturation Flow ($s_i$) | Arrival Flow ($q_i$) | Provenance Category | Yellow Clearance | Optimum Cycle ($C$) | Green Splits ($g_i$) |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$J_1$** | 0 | Side cross street (`-148697299_0`) | 1 | $1,800\text{ veh/h}$ | $150\text{ veh/h}$ | **[ASSUMPTION]** (Nominal standard) | $4.0\text{ s}$ | **$45.00\text{ s}$** (floored) | $g_0 = 16.40\text{ s}$ |
| **$J_1$** | 2 | Hosur arterial entry (`172853382#2`) | 2 | $3,600\text{ veh/h}$ | $1,200\text{ veh/h}$ | **[CONFIGURED VALUE]** (Calibrated) | $4.0\text{ s}$ | — | $g_2 = 20.60\text{ s}$ |
| **$J_2$** | 0 | Hosur arterial approach (`172853382#3`) | 3 | $5,400\text{ veh/h}$ | $1,800\text{ veh/h}$ | **[CONFIGURED VALUE]** (Calibrated) | $6.0\text{ s}$ | **$55.20\text{ s}$** (unconstrained) | $g_0 = 24.69\text{ s}$ |
| **$J_2$** | 2 | Madiwala cross approach (`92196679#0`) | 2 | $3,600\text{ veh/h}$ | $900\text{ veh/h}$ | **[CONFIGURED VALUE]** (Extracted peak) | $6.0\text{ s}$ | — | $g_2 = 18.51\text{ s}$ |
| **$J_3$** | 0 | Side cross street (`-744783934_0`) | 1 | $1,800\text{ veh/h}$ | $150\text{ veh/h}$ | **[ASSUMPTION]** (Nominal standard) | $4.0\text{ s}$ | **$45.00\text{ s}$** (floored) | $g_0 = 16.24\text{ s}$ |
| **$J_3$** | 2 | Hosur arterial continuation (`1148717038#0`) | 2 | $3,600\text{ veh/h}$ | $1,400\text{ veh/h}$ | **[CONFIGURED VALUE]** (Calibrated) | $4.0\text{ s}$ | — | $g_2 = 20.76\text{ s}$ |

- **Flow Provenance Note:** In `silk_board.rou.xml`, edges `-148697299` and `-744783934` generate 0 vehicles. An assumed nominal flow of $150\text{ veh/h}$ was assigned per IRC:93-1985 guidelines. Independent sensitivity analysis proves that setting $q_0 = 0\text{ veh/h}$ produces $g_0 = 15.00\text{ s}, g_2 = 22.00\text{ s}, C = 45.00\text{ s}$, demonstrating that artificial demand is mathematically unnecessary because the constrained allocator inherently enforces the $15.0\text{ s}$ minimum green floor **[MEASURED RESULT]**.
- **Saturation Flow Note:** Saturation flow of $1,800\text{ veh/h/lane}$ represents the Indian standard design value (IRC:93-1985 / IRC:SP:84) for $3.20\text{ m}$ lane widths, rather than empirical TraCI saturation headways **[ASSUMPTION]**.

### 3.4.4 Safety & Integration Verification
1. **Yellow Clearance Calibration:** Ground truth in `silk_board.net.xml` specifies 6.0s yellow clearance at $J_2$ (TLS `GS_cluster...`) and 4.0s at $J_1/J_3$. `MultiIntersectionSimulation` sets `self.yellow_durations = {"J1": 4.0, "J2": 6.0, "J3": 4.0}`, verified in live TraCI stepping (`getNextSwitch`) **[MEASURED RESULT]**.
2. **Maximum-Red Starvation Analysis:**
   - Under the default Silk Board timing plans, maximum red time across the corridor is $36.69\text{ s}$ ($J_2$ Phase 2), strictly below the $60.0\text{ s}$ starvation limit ($R_{\max} = 36.69\text{ s} \ll 60.0\text{ s}$) **[MEASURED RESULT]**.
   - Under arbitrary asymmetric demand, fixed-time Webster does not dynamically preempt phases; dynamic preemption is reserved for MARL controllers via `StarvationTracker` to preserve Webster's baseline integrity **[IMPLEMENTATION FACT]**.
3. **Emergency Preemption Interoperability:** When `SignalController.lock_emergency_priority` is asserted, Webster immediately yields control (`EMERGENCY_LOCK_ACTIVE`), resuming cyclic operation cleanly upon release without phase corruption **[MEASURED RESULT]**.

### 3.4.5 Empirical Test Suite Evidence
- **Dedicated Webster Suite:** 27 passed in 1.12s ([`tests/test_webster_controller.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/tests/test_webster_controller.py)) **[MEASURED RESULT]**.
- **Safety Regression Suite:** 2 passed in 1.98s ([`tests/test_emergency_runtime_safety.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/tests/test_emergency_runtime_safety.py)) **[MEASURED RESULT]**.
- **MARL Non-Regression Suite:** 10 passed in 7.01s ([`tests/test_marl_algorithm_correction.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/tests/test_marl_algorithm_correction.py)) and 6 passed in 8.87s ([`tests/test_marl_runtime_dispatch.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/tests/test_marl_runtime_dispatch.py)) **[MEASURED RESULT]**.
- **Live SUMO Stepping:** 40-step and 120-step TraCI simulation runs verified exact phase transitions, nextSwitch countdowns, and clean teardown without orphan processes **[MEASURED RESULT]**.

---

# 4. Reported Experimental Results

## 4.1 Master Benchmark Configuration
- **Dataset File:** [`outputs/validation/10seeds/statistical_analysis.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/validation/10seeds/statistical_analysis.json) **[MEASURED RESULT]**.
- **Summary File:** [`outputs/validation/10seeds/eval_10seeds_summary.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/validation/10seeds/eval_10seeds_summary.json) **[MEASURED RESULT]**.
- **Evaluation Seeds ($N=10$):** `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]` **[CONFIGURED VALUE]**.
- **Statistical Design:** Matched-pairs within-subject design ($df = N - 1 = 9, t_{\text{critical}, 95\%} = 2.26216$) **[IMPLEMENTATION FACT]**.
- **Total Experimental Runs:** 40 runs ($4\text{ controllers} \times 10\text{ seeds}$) **[MEASURED RESULT]**.
- **Total Vehicle-Runs:** 15,120 ($378\text{ departed} \times 40\text{ runs}$) **[MEASURED RESULT]**.
- **Corridor Traversal Cohort:** Exactly $M = 109$ continuous $J_1 \to J_2 \to J_3$ trips completed per run ($1,090$ per controller) **[MEASURED RESULT]**.

### Raw Per-Seed Corridor Travel Time Observations ($T_{\text{corridor}}$, seconds)

| Seed | Fixed-Time Baseline | Coordinated Adaptive | MARL Double-DQN | MARL PPO |
| :---: | :---: | :---: | :---: | :---: |
| **1** | 88.37 | 48.01 | 57.81 | 88.73 |
| **2** | 90.53 | 48.84 | 59.58 | 89.97 |
| **3** | 90.72 | 49.79 | 58.33 | 87.35 |
| **4** | 88.15 | 48.96 | 57.68 | 87.90 |
| **5** | 89.99 | 47.14 | 53.25 | 84.00 |
| **6** | 92.04 | 55.02 | 59.20 | 87.02 |
| **7** | 89.79 | 53.55 | 55.96 | 69.95 |
| **8** | 91.29 | 49.18 | 54.96 | 89.30 |
| **9** | 88.86 | 48.96 | 53.77 | 86.88 |
| **10** | 90.47 | 49.27 | 55.83 | 83.91 |
| **Mean ($\bar{x}$)** | **90.021 s** | **49.872 s** | **56.637 s** | **85.501 s** |
| **Std Dev ($s$)** | 1.2590 | 2.4616 | 2.2154 | 5.8198 |
| **Std Error ($\text{SE}$)** | 0.3981 | 0.7784 | 0.7006 | 1.8404 |
| **95% Conf. Interval** | $[89.12, 90.92]$ | $[48.11, 51.63]$ | $[55.05, 58.22]$ | $[81.34, 89.66]$ |

## 4.2 Statistical Significance, Effect Sizes & Bonferroni Correction ($m=3, \alpha_{\text{adj}} = 0.01667$)

| Metric & Comparison | Mean Difference ($\bar{d}$) | Change (%) | Paired $t$-stat | Raw $p$-value | Bonferroni $p_{\text{adj}}$ | Wilcoxon $W$ ($p$-val) | Cohen's $d_z$ | Statistical Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Travel Time (s)** | | | | | | | | |
| • Coordinated vs Baseline | $\mathbf{-40.149}$ | $\mathbf{-44.61\%}$ | $-59.25$ | $5.60 \times 10^{-13}$ | $\mathbf{1.68 \times 10^{-12}}$ | $0.0$ ($0.00195$) | $18.74$ | **Statistically Significant Improvement** |
| • Double-DQN vs Baseline | $\mathbf{-33.384}$ | $\mathbf{-37.08\%}$ | $-45.57$ | $5.90 \times 10^{-12}$ | $\mathbf{1.77 \times 10^{-11}}$ | $0.0$ ($0.00195$) | $14.41$ | **Statistically Significant Improvement** |
| • PPO vs Baseline | $-4.520$ | $-5.01\%$ | $-2.42$ | $0.0384$ | $\mathbf{0.1153}$ | $2.0$ ($0.00586$) | $0.77$ | **NOT Significant after Bonferroni ($p_{\text{adj}} > 0.05$)** |
| **Space-Mean Speed (km/h)** | | | | | | | | |
| • Coordinated vs Baseline | $\mathbf{+9.776}$ | $\mathbf{+34.68\%}$ | $+81.30$ | $3.26 \times 10^{-14}$ | $\mathbf{9.79 \times 10^{-14}}$ | $0.0$ ($0.00195$) | $25.71$ | **Statistically Significant Improvement** |
| • Double-DQN vs Baseline | $\mathbf{+3.258}$ | $\mathbf{+11.56\%}$ | $+20.52$ | $7.25 \times 10^{-9}$ | $\mathbf{2.17 \times 10^{-8}}$ | $0.0$ ($0.00195$) | $6.49$ | **Statistically Significant Improvement** |
| • PPO vs Baseline | $\mathbf{-2.642}$ | $\mathbf{-9.34\%}$ | $-7.83$ | $2.63 \times 10^{-5}$ | $\mathbf{7.88 \times 10^{-5}}$ | $0.0$ ($0.00195$) | $2.48$ | **Statistically Significant Degradation (Speed Penalty)** |
| **Cumulative Delay ($\text{veh}\cdot\text{s}$)** | | | | | | | | |
| • Coordinated vs Baseline | $\mathbf{-6536.4}$ | $\mathbf{-52.82\%}$ | $-64.40$ | $2.65 \times 10^{-13}$ | $\mathbf{7.94 \times 10^{-13}}$ | $0.0$ ($0.00195$) | $20.37$ | **Statistically Significant Improvement** |
| • Double-DQN vs Baseline | $\mathbf{-4348.8}$ | $\mathbf{-35.15\%}$ | $-38.26$ | $2.83 \times 10^{-11}$ | $\mathbf{8.48 \times 10^{-11}}$ | $0.0$ ($0.00195$) | $12.10$ | **Statistically Significant Improvement** |
| • PPO vs Baseline | $-209.6$ | $-1.66\%$ | $-0.70$ | $0.5033$ | $1.0000$ | $25.0$ ($0.8457$) | $0.22$ | **Not Statistically Significant** |
| **$\text{CO}_2$ Emissions (kg)** | | | | | | | | |
| • Coordinated vs Baseline | $\mathbf{-12.86}$ | $\mathbf{-23.14\%}$ | $-60.34$ | $4.75 \times 10^{-13}$ | $\mathbf{1.43 \times 10^{-12}}$ | $0.0$ ($0.00195$) | $19.08$ | **Statistically Significant Reduction** |
| • Double-DQN vs Baseline | $\mathbf{-8.43}$ | $\mathbf{-15.17\%}$ | $-36.18$ | $4.66 \times 10^{-11}$ | $\mathbf{1.40 \times 10^{-10}}$ | $0.0$ ($0.00195$) | $11.44$ | **Statistically Significant Reduction** |
| • PPO vs Baseline | $-0.55$ | $-0.98\%$ | $-0.97$ | $0.3552$ | $1.0000$ | $23.0$ ($0.6953$) | $0.31$ | **Not Statistically Significant** |
| **Fuel Consumption (L)** | | | | | | | | |
| • Coordinated vs Baseline | $\mathbf{-5.55}$ | $\mathbf{-23.15\%}$ | $-60.39$ | $4.72 \times 10^{-13}$ | $\mathbf{1.41 \times 10^{-12}}$ | $0.0$ ($0.00195$) | $19.10$ | **Statistically Significant Reduction** |
| • Double-DQN vs Baseline | $\mathbf{-3.64}$ | $\mathbf{-15.17\%}$ | $-36.17$ | $4.68 \times 10^{-11}$ | $\mathbf{1.40 \times 10^{-10}}$ | $0.0$ ($0.00195$) | $11.44$ | **Statistically Significant Reduction** |
| • PPO vs Baseline | $-0.24$ | $-0.98\%$ | $-0.97$ | $0.3571$ | $1.0000$ | $23.0$ ($0.6953$) | $0.31$ | **Not Statistically Significant** |

---

# 4.3 Rigorous Investigation of PPO Paired t-Test vs. Wilcoxon Discrepancy

A critical statistical question arises from the empirical benchmark: **Why does the Wilcoxon signed-rank test report $p = 0.005859$ ($p < 0.01$), whereas the paired $t$-test reports raw $p = 0.0384$ and Bonferroni-adjusted $p_{\text{adj}} = 0.1153$ ($p > 0.05$)?**

### 1. Mathematical Breakdown of the Observations
Let $d_i = T_{\text{ppo}, i} - T_{\text{base}, i}$ be the paired difference in corridor travel time for seed $i$:
$$d = [+0.36, -0.56, -3.37, -0.25, -5.99, -5.02, -19.84, -1.99, -1.98, -6.56]$$

- **Sign Distribution:**
  - Positive difference ($d_1 = +0.36\text{s}$): Baseline was faster than PPO in 1 out of 10 seeds.
  - Negative differences ($d_2 \dots d_{10} < 0$): PPO travel time was lower than Baseline in 9 out of 10 seeds.
- **Rank Ordering of Absolute Differences $|d_i|$:**
  1. $0.25$ (Seed 4, negative, rank 1)
  2. $0.36$ (Seed 1, positive, rank 2)
  3. $0.56$ (Seed 2, negative, rank 3)
  4. $1.98$ (Seed 9, negative, rank 4)
  5. $1.99$ (Seed 8, negative, rank 5)
  6. $3.37$ (Seed 3, negative, rank 6)
  7. $5.02$ (Seed 6, negative, rank 7)
  8. $5.99$ (Seed 5, negative, rank 8)
  9. $6.56$ (Seed 10, negative, rank 9)
  10. $19.84$ (Seed 7, negative, rank 10)

### 2. Wilcoxon Signed-Rank Test Mechanics
The Wilcoxon statistic is the sum of ranks for the less frequent sign:
- $W^+ = \text{rank}(0.36) = 2.0$.
- $W^- = 1 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 = 53.0$.
- Test statistic $W = \min(W^+, W^-) = 2.0$.
- For $N = 10$, the two-sided exact permutation probability is:
  $$p_{\text{wilcoxon}} = 2 \times \frac{1 + 1 + 1}{2^{10}} = 2 \times \frac{3}{1024} = \frac{6}{1024} = 0.005859375$$
Because 9 of 10 pairs have a negative sign, the non-parametric rank test detects a consistent directional shift regardless of magnitude.

### 3. Student's Paired t-Test Mechanics & Outlier Inflation
In contrast, Student's paired $t$-test is sensitive to the variance of the sample differences:
- Sample mean difference: $\bar{d} = -4.520\text{ s}$.
- Sample standard deviation: $s_d = 5.899\text{ s}$.
- Standard error: $\text{SE} = \frac{s_d}{\sqrt{10}} = \frac{5.899}{3.1623} = 1.8654\text{ s}$.
- $t$-statistic: $t = \frac{\bar{d}}{\text{SE}} = \frac{-4.520}{1.8654} = -2.4231$.
- Degrees of freedom: $df = 9 \implies \text{raw } p = 0.038418$.

**The Outlier Effect:** Seed 7 produced an extreme negative drop of $-19.84\text{ s}$ ($69.95\text{ s}$ vs. $89.79\text{ s}$), whereas 8 of the other 9 seeds had small differences (between $+0.36\text{s}$ and $-6.56\text{s}$). The standardized residual of Seed 7 is:
$$z = \frac{-19.84 - (-4.52)}{5.899} = -2.60$$
This single outlier heavily inflates the sample variance ($s_d = 5.899\text{ s}$, compared to $s_d = 2.14\text{ s}$ for Coordinated and $2.32\text{ s}$ for Double-DQN). In small samples ($N=10$), inflated variance broadens the denominator standard error, pushing the $t$-statistic closer to zero.

### 4. Multiple Testing Family-Wise Error Control (Bonferroni)
In multi-arm comparative experiments testing 3 candidate algorithms against a single baseline ($m = 3$ hypotheses: Coordinated vs. Base, Double-DQN vs. Base, PPO vs. Base), the family-wise error rate must be controlled to prevent type-I false discoveries:
$$\alpha_{\text{adj}} = \frac{\alpha}{m} = \frac{0.05}{3} \approx 0.016667$$
$$p_{\text{adj}} = \min(1.0, 3 \times p_{\text{raw}}) = 3 \times 0.038418 = 0.11525 > 0.05$$
Because $p_{\text{adj}} = 0.1153 > 0.05$, the parametric hypothesis test concludes that **PPO's travel time improvement is NOT statistically significant after family-wise error correction**.

### 5. Multi-Metric Confirmation: The Severe Speed Degradation
Crucially, evaluating travel time in isolation gives a distorted picture. Inspection of corridor space-mean speed completely resolves any ambiguity:
- Baseline mean speed: $28.21\text{ km/h}$.
- PPO mean speed: $25.56\text{ km/h}$ ($\mathbf{-9.34\%}$ degradation).
- Paired $t$-test for speed: $t = -7.8301$, $p_{\text{raw}} = 2.63 \times 10^{-5}$, $p_{\text{adj}} = 7.88 \times 10^{-5}$ (**Statistically Significant Degradation**).
- Wilcoxon for speed: $W = 0.0, p = 0.00195$.

**Scientific Conclusion:** PPO fails to deliver reliable corridor improvement. The non-parametric travel-time significance ($p = 0.00586$) is driven purely by sign consistency, while the parametric test reflects high variance ($s_d = 5.90\text{s}$) and fails significance under Bonferroni correction ($p_{\text{adj}} = 0.1153$). Meanwhile, PPO's speed degradation is massive and unequivocal ($p_{\text{adj}} < 10^{-4}$), caused by repeated 60-second anti-starvation arterial halts.

---

# 5. Traffic Metrics and Mathematical Formulation

The following mathematical formulations govern all metric extraction in [`traffic_service/corridor_metrics.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/corridor_metrics.py) and [`traffic_service/state_extractor.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/state_extractor.py):

## 5.1 Average Corridor Travel Time
The mean corridor travel time $\bar{T}$ is evaluated exclusively over the cohort of vehicles that fully traverse the arterial corridor from entry edge $e_{\text{in}} = \text{"172853382\#2"}$ (north of $J_1$) to exit edge $e_{\text{out}} = \text{"40696223\#1"}$ (south of $J_3$) **[IMPLEMENTATION FACT]**:
$$\bar{T} = \frac{1}{M} \sum_{i=1}^{M} \left( t_i^{\text{exit}} - t_i^{\text{entry}} \right)$$
- $M$ is the number of completed corridor trips ($M = 109$ across all 40 runs) **[MEASURED RESULT]**.
- $t_i^{\text{entry}}$ is the simulation timestamp when vehicle $i$ enters edge $e_{\text{in}}$.
- $t_i^{\text{exit}}$ is the timestamp when vehicle $i$ emerges onto edge $e_{\text{out}}$.
- Incomplete trips remaining in the network are excluded from $\bar{T}$; however, the 300s clearance window guarantees that 100% of inserted corridor vehicles reach completion **[MEASURED RESULT]**.

## 5.2 Space-Mean Corridor Speed
The corridor space-mean speed is the time-averaged instantaneous velocity of all active corridor vehicles across the simulation horizon $T = 900\text{ s}$ **[IMPLEMENTATION FACT]**:
$$\bar{v}_{\text{corridor}} = \frac{1}{T} \sum_{t=1}^{T} \left( \frac{1}{|\mathcal{V}_{\text{corridor}}(t)|} \sum_{v \in \mathcal{V}_{\text{corridor}}(t)} u_v(t) \right)$$
where $u_v(t)$ is the instantaneous velocity ($\text{km/h}$) of vehicle $v$ obtained via TraCI.

## 5.3 Queue Length
Queue length on lane $l$ is defined as the count of queued vehicles whose instantaneous speed is below the operational queue threshold **[IMPLEMENTATION FACT]**:
$$Q_l(t) = \sum_{v \in \mathcal{V}_l(t)} \mathbf{1}_{\{u_v(t) \le u_{\text{queue}}\}}$$
- $u_{\text{queue}} = 1.0\text{ m/s}$ ($3.6\text{ km/h}$) (`queue_speed_threshold` in `IntersectionStateExtractor`) **[CONFIGURED VALUE]**.
- Approach queue: $Q_{\text{approach}}(t) = \sum_{l \in \mathcal{L}_{\text{approach}}} Q_l(t)$.
- Total intersection queue: $Q_{\text{total}}(t) = \sum_{\text{approach}} Q_{\text{approach}}(t)$.

## 5.4 Mathematically Valid Cumulative Delay vs. Repeated Waiting Time
Prior literature often sums SUMO's `getAccumulatedWaitingTime()`, which repeatedly accumulates waiting seconds for stationary vehicles across consecutive steps, resulting in quadratic overcounting artifacts ($O(t^2)$). This implementation computes the mathematically rigorous Riemann integral of queued vehicles across time **[IMPLEMENTATION FACT]**:
$$D_{\text{veh}\cdot\text{s}} = \sum_{t=1}^{T} Q_{\text{corridor}}(t) \cdot \Delta t \quad [\text{vehicle-seconds}]$$
where $\Delta t = 1.0\text{ s}$. This represents the exact area under the queue-over-time curve.

## 5.5 Throughput and Completion Rate
Corridor throughput is defined as completed trips per unit time **[IMPLEMENTATION FACT]**:
$$\text{Throughput} = \frac{M_{\text{completed}}}{T_{\text{horizon}}} \times 3600 \quad [\text{veh/h}]$$
- In the master benchmark, all 4 controllers completed exactly $378$ total vehicles ($1512\text{ veh/h}$ fleet throughput) and $109$ corridor vehicles ($436\text{ veh/h}$ corridor throughput) **[MEASURED RESULT]**.
- **Crucial Distinction:** Coordinated Adaptive and Double-DQN do **not** increase throughput over Baseline under fixed demand, because Baseline already achieves 100% completion within the 900s horizon. The 44.61% gain is strictly a **travel time latency and delay reduction**, not a capacity increase.

## 5.6 Vehicle Tailpipe Emissions
Instantaneous emissions are sampled per edge from SUMO's microscopic HBEFA4 emission model **[IMPLEMENTATION FACT]**:
$$\text{CO}_{2, \text{total}} = \frac{1}{10^6} \sum_{t=1}^{T} \sum_{e \in \mathcal{E}_{\text{corridor}}} \dot{m}_{\text{CO}_2, e}(t) \cdot \Delta t \quad [\text{kg}]$$
$$\text{NO}_{x, \text{total}} = \frac{1}{10^3} \sum_{t=1}^{T} \sum_{e \in \mathcal{E}_{\text{corridor}}} \dot{m}_{\text{NO}_x, e}(t) \cdot \Delta t \quad [\text{g}]$$
where $\dot{m}(t)$ is sampled via `traci.edge.getCO2Emission(e)` ($\text{mg/s}$) across the 8 arterial edges **[IMPLEMENTATION FACT]**.

## 5.7 Fuel Consumption
Volumetric fuel consumption is derived from fuel mass accumulation using standard automotive fuel density **[IMPLEMENTATION FACT]**:
$$\text{Fuel}_{\text{liters}} = \frac{1}{\rho_{\text{fuel}}} \sum_{t=1}^{T} \sum_{e \in \mathcal{E}_{\text{corridor}}} \dot{m}_{\text{fuel}, e}(t) \cdot \Delta t \quad [\text{L}]$$
- Reference automotive petrol density: $\rho_{\text{fuel}} = 750{,}000.0\text{ mg/L}$ ($0.750\text{ kg/L}$ or $750.0\text{ mg/mL}$) **[ASSUMPTION]** (Euro 4 / BS-VI reference fuel density defined in `FUEL_DENSITY_MG_PER_LITER`).

---

# 6. Safety Constraints & Deterministic Signal Shielding

Regardless of the action emitted by an RL neural policy or adaptive heuristic, all actuations pass through a deterministic safety state machine implemented in [`traffic_service/signal_controller.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/signal_controller.py):

```
[Agent Emits Action a in {KEEP, SWITCH, EXTEND}]
                        |
                        v
       +----------------------------------+
       |   Deterministic Safety Shield    |
       +----------------------------------+
       | Invariant 1: Minimum Green       |
       | If elapsed < 15.0s -> Action=KEEP|
       +----------------------------------+
       | Invariant 2: Maximum Red         |
       | If red >= 60.0s and Q >= 1 ->    |
       | Force Transition to Starved Phase|
       +----------------------------------+
       | Invariant 3: Yellow Clearance    |
       | Force 4.0s Yellow Transition     |
       +----------------------------------+
       | Invariant 4: Maximum Green       |
       | If green >= 60.0s -> Force Yellow|
       +----------------------------------+
       | Invariant 5: Emergency Lock      |
       | Ambulance <= 250m -> Force Green |
       +----------------------------------+
                        |
                        v
       [Executed Signal Phase on TraCI TLS]
```

### Safety Invariants Enforced Across All Controllers:
1. **Minimum Green Time ($g_{\text{min}} = 15.0\text{ s}$):** An active green phase cannot be terminated before 15.0 seconds have elapsed, preventing phase chatter and pedestrian stranding **[IMPLEMENTATION FACT]**.
2. **Maximum Green Time ($g_{\text{max}} = 60.0\text{ s}$):** An active green phase cannot be extended beyond 60.0 seconds, capping green-wave hold duration **[IMPLEMENTATION FACT]**.
3. **Maximum Red Anti-Starvation ($r_{\text{max}} = 60.0\text{ s}$):** If any conflicting approach has queued vehicles ($Q \ge 1$) waiting for $\ge 60.0\text{ s}$ of red, the shield overrides the controller and forces a switch **[IMPLEMENTATION FACT]**.
4. **Yellow Clearance Interval ($y = 4.0\text{ s}$):** Direct green-to-green transitions are strictly blocked. Every phase switch incurs a mandatory 4.0-second yellow clearance phase **[IMPLEMENTATION FACT]**.
5. **Conflict-Free State Transitions:** Only valid non-conflicting phase indices are defined in the junction phase tables, eliminating cross-traffic green conflicts **[IMPLEMENTATION FACT]**.

---

# 7. Emergency Vehicle Prioritization

Implemented in [`traffic_service/emergency_wave.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/emergency_wave.py):

- **Detection Radius:** $d_{\text{detect}} = 250.0\text{ m}$ upstream of intersection stop lines **[CONFIGURED VALUE]**.
- **Detection Mechanism:** Polling `traci.vehicle.getTypeID(veh_id) == "emergency"` **[IMPLEMENTATION FACT]**.
- **Preemption Logic:**
  1. Detect approaching ambulance within 250m.
  2. If the current phase is cross green: initiate immediate 4.0s yellow transition to arterial green.
  3. Lock the signal in arterial green (`emergency_locked = True`) until the ambulance clears the exit detector.
- **Empirical Results (Phase 5 Benchmark Experiments):**
  - Baseline Ambulance Traversal Time: $41.0\text{ s}$ **[MEASURED RESULT]**.
  - Coordinated Adaptive Ambulance Traversal Time: $33.6\text{ s}$ ($\mathbf{-18.0\%}$ transit time reduction) **[MEASURED RESULT]**.
- **Scientific Disclosure:** In the Phase 8 10-seed master benchmark, emergency preemption was disabled during automated batch runs to ensure identical background traffic demand across all 40 runs; emergency metrics originate from verified Phase 5 validation experiments **[IMPLEMENTATION FACT]**.

---

# 8. Digital Twin and Geographic Modeling

The 3D visualization is a fully coupled digital twin of the SUMO microscopic simulation environment:

- **Geographic Network Extraction:** 306 road edges, 213 junctions, and 490 lanes extracted from `silk_board.net.xml` and parsed into Three.js WebGL geometry via `frontend/src/components/ThreeCorridor/CorridorScene.jsx` **[IMPLEMENTATION FACT]**.
- **Coordinate Transformation:** SUMO 2D coordinates $(x, y)$ are transformed to Three.js $(x, -z, y)$ coordinates with origin centered at Central Silk Board **[IMPLEMENTATION FACT]**.
- **Elevation Profiles:**
  - Ground-level arterial and rotary roads: $y = 0.0\text{ m}$ **[IMPLEMENTATION FACT]**.
  - Silk Board flyover structures: $y = +8.0\text{ m}$ per IRC:54-1974 clearance standards **[ASSUMPTION]**.
  - Underpass structures: $y = -4.5\text{ m}$ per IRC clearance standards **[ASSUMPTION]**.
- **Urban Environment:** 64 procedural building parcels generated in `BuildingParcelGenerator.js` with setbacks $\ge 20.0\text{ m}$ from road centerlines and heights varying from $12.0\text{ m}$ to $54.0\text{ m}$ per Indian National Building Code (IS:SP:7-2005) **[ASSUMPTION]**.
- **Live Vehicle Telemetry:** Vehicles streamed at 1.0 Hz via WebSockets (`/ws/traffic`) and rendered with linear interpolation (lerp) at 60 FPS in WebGL **[IMPLEMENTATION FACT]**.
- **Gantry Signal Visualization:** Real-time 3D signal heads display green, yellow, and red states synchronized with TraCI traffic light states **[IMPLEMENTATION FACT]**.

---

# 9. Traffic Demand and Vehicle Modeling

Defined in `sumo/silk_board/demand/vehicle_types.add.xml` and `silk_board.rou.xml`:

### 9.1 Heterogeneous Fleet Kinematics Calibration

| Vehicle Class | SUMO `vClass` | Length ($m$) | Min Gap ($m$) | Max Speed ($m/s$) | Accel ($m/s^2$) | Decel ($m/s^2$) | Imperfection ($\sigma$) | Category |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Motorcycle** | `motorcycle` | 2.20 | 1.00 | 16.67 (60 km/h) | 2.60 | 4.50 | 0.50 | **[CONFIGURED VALUE]** |
| **Passenger Car** | `passenger` | 4.50 | 2.00 | 16.67 (60 km/h) | 2.60 | 4.50 | 0.50 | **[CONFIGURED VALUE]** |
| **BMTC City Bus** | `bus` | 12.00 | 2.50 | 13.89 (50 km/h) | 1.20 | 3.00 | 0.50 | **[CONFIGURED VALUE]** |
| **Heavy Truck** | `truck` | 10.00 | 2.50 | 13.89 (50 km/h) | 1.00 | 3.00 | 0.50 | **[CONFIGURED VALUE]** |
| **Ambulance** | `emergency` | 5.00 | 2.00 | 20.00 (72 km/h) | 3.00 | 5.00 | 0.20 | **[CONFIGURED VALUE]** |

### 9.2 Dynamic Traffic Demand Regimes
- **Total Injected Volume:** Exactly **378 vehicles** per 900s run across 31 flow streams **[CONFIGURED VALUE]**.
- **Normal Flow ($0 \le t < 120\text{s}$):** Background arterial flow (150 cars/h, 400 motorcycles/h, 40 buses/h).
- **Peak Inflow Surge ($120 \le t < 240\text{s}$):** Morning peak buildup (250 cars/h, 650 motorcycles/h, 40 buses/h).
- **Heavy Saturated Peak ($240 \le t < 400\text{s}$):** Saturated bottleneck (300 cars/h, 800 motorcycles/h, 50 trucks/h).
- **Recovery Taper ($400 \le t < 600\text{s}$):** Demand dissipation (130 cars/h, 350 motorcycles/h).
- **Clearance Window ($600 \le t \le 900\text{s}$):** Zero vehicle insertion; all residual vehicles reach destination.
- **Fleet Completion:** 100.0% completion across all 40 runs (378 departed, 378 arrived, 0 active at $t=900\text{s}$) **[MEASURED RESULT]**.

---

# 10. Testing and Engineering Evidence

The engineering foundation is validated by an automated multi-layer test harness:

| Verification Scope | Suite & Tool | Verified Count / Status | Category |
| :--- | :--- | :---: | :--- |
| **Backend Integration & Unit Tests** | Pytest 8.3.4 (`tests/`) | **231 tests passing** | **[MEASURED RESULT]** |
| **Frontend Component & UI Tests** | Vitest 1.6.0 (`frontend/`) | **91 tests passing** | **[MEASURED RESULT]** |
| **Production Frontend Build** | Vite 5.2.11 (`npm run build`) | **Zero errors (436.4 kB bundle)** | **[MEASURED RESULT]** |
| **Sequential Batch Benchmark Stability**| Python automated harness | **40 consecutive runs with 0 crashes** | **[MEASURED RESULT]** |
| **Repository Credential Scan** | Static security audit | **Zero API keys or secrets in Git tree** | **[MEASURED RESULT]** |
| **3D Rendering Framerate Target** | Three.js WebGL rendering loop | **$\ge 45\text{ FPS}$ design target** | **[PERFORMANCE TARGET]** |
| **TraCI Telemetry Latency Target** | FastAPI WebSocket streaming | **$\le 200\text{ ms}$ broadcast target** | **[PERFORMANCE TARGET]** |

---

# 11. Research Gaps and Required Experiments

Before submission to IEEE Transactions on Intelligent Transportation Systems (T-ITS), the following research gaps must be resolved through rigorous empirical experimentation:

## 11.1 Classical Controller Baselines
Currently, the baseline is restricted to fixed-time control. Required additions:
1. **Actuated / Webster Controller:** Dynamic phase extension based solely on local loop detector occupancy without inter-junction communication.
2. **Max-Pressure Controller (Varaiya 2013):** Decentralized state-of-the-art queue differential controller proving stability and maximum throughput.
3. **SCOOT / SCATS Benchmark:** Coordinated cyclic baseline optimizing split, cycle, and offset.

## 11.2 Demand Scenario Generalization
The current 10-seed benchmark evaluates a single dynamic morning peak regime. Required scenarios:
1. **Off-Peak Flow:** Night/midday low-density traffic (testing whether RL policies switch unnecessarily).
2. **Over-Saturated Gridlock:** 150% peak demand testing corridor spillback and gridlock avoidance.
3. **Severe Incident / Lane Blockage:** Capacity drop due to a disabled vehicle on edge `172853382#3`.
4. **Adverse Weather:** Wet pavement kinematic profile with 30% reduced deceleration and lower free-flow speed.

## 11.3 Systematic Ablation Experiments
To isolate the exact causal mechanisms behind performance improvements:
1. **Communication Hub Ablation:** Coordinated Adaptive with inter-junction communication enabled vs. disabled.
2. **Safety Shield Ablation:** Neural policies evaluated with hard safety shield vs. pure unconstrained actions.
3. **Observation Space Ablation:** 14-dim full vector vs. 8-dim local queue-only vector.
4. **Reward Formulation Ablation:** Mixed local-global reward vs. pure local queue reward.

---

# 12. Research Limitations & Real-World Boundaries

To maintain scientific integrity, the explicit limitations of this study must be stated:

1. **Simulation-to-Reality Gap (Sim2Real):** All results are obtained within microscopic simulation (SUMO). Real-world Indian traffic exhibits extreme lane indiscipline, lateral creeping, and vehicle overtaking that are only partially captured by SUMO's default Krauss car-following model.
2. **Ideal Communication Assumption:** The virtual communication hub assumes zero packet loss, zero jitter, and instantaneous transmission between signal controllers. Real-world wireless V2X or 4G/5G networks experience packet drops and latency spikes.
3. **No Field Authority Control:** This software has **not** been connected to physical traffic signal controllers in Bengaluru. No claim is made regarding field congestion relief in physical South Bengaluru.
4. **Proposed Real-World Deployment Mode:** Future physical trials must be restricted to a **passive shadow-mode deployment**, where edge computers (e.g. NVIDIA Jetson) ingest video detector feeds, run AI inference, log recommendations, and compute counterfactual metrics without actuating physical signals.

---

# 13. Reproducibility and Evidence Register

Every artifact required to independently reproduce all findings is tracked in Git under tag `baseline/smart-traffic-v1-verified`:

| Artifact Path | Description & Provenance | Role in Paper |
| :--- | :--- | :--- |
| `outputs/validation/10seeds/statistical_analysis.json` | 10-seed master benchmark descriptive and inferential statistics | Authoritative Table 1 & Table 2 source |
| `outputs/validation/10seeds/eval_10seeds_summary.json` | Per-seed raw metric runs across all 40 executions | Authoritative raw data source |
| `sumo/silk_board/network/silk_board.net.xml` | Calibrated road network of Central Silk Board corridor | Geographic network topology |
| `sumo/silk_board/demand/silk_board.rou.xml` | Dynamic 31-flow dynamic demand definitions | Traffic demand replication |
| `sumo/silk_board/demand/vehicle_types.add.xml` | Calibrated kinematic parameters for 5 vehicle classes | Fleet kinematics specification |
| `traffic_service/signal_controller.py` | Deterministic safety shield state machine | Safety invariant proof |
| `traffic_service/multi_intersection_simulation.py` | Coordinated Adaptive Algorithm 1 implementation | Adaptive controller specification |
| `traffic_service/ai/models.py` | PyTorch & NumPy neural architectures | Neural architecture specification |
| `traffic_service/ai/dqn_agent.py` | Dueling Double-DQN agent implementation | Double-DQN training & inference |
| `traffic_service/ai/ppo_agent.py` | Actor-Critic PPO agent implementation | PPO training & inference |
| `checkpoints/p6/dqn_stage_a_best.json` | Approved curriculum weights for Double-DQN | Trained model artifact |
| `checkpoints/p6/ppo_stage_a_best.json` | Approved curriculum weights for PPO | Trained model artifact |
| `tests/` | 231 backend pytest tests and 91 frontend vitest tests | Verification and regression suite |

---

# 14. Target Paper Structure (IEEE T-ITS Format)

1. **Title:** Comparative Evaluation of Adaptive and Multi-Agent Reinforcement Learning-Based Traffic Signal Control in a Multi-Intersection Urban Corridor
2. **Abstract:** (250 words summarizing the -44.61% adaptive gain, -37.08% DQN gain, and mechanistic discovery of PPO failure).
3. **Section I: Introduction:** Urban congestion challenges, Central Silk Board testbed, research questions, and contributions.
4. **Section II: Related Work:** Classical arterial coordination (SCOOT/SCATS), Adaptive control, MARL in traffic signal optimization.
5. **Section III: System Architecture & Study Corridor:** Microscopic simulation, OpenStreetMap extraction, 3D digital twin.
6. **Section IV: Signal Control Methodology:** Fixed-Time, Coordinated Adaptive (Algorithm 1), Dueling Double-DQN, PPO.
7. **Section V: Safety Shield & Invariant Enforcement:** Formal mathematical guarantees for minimum green, maximum red, and yellow transitions.
8. **Section VI: Experimental Design & Benchmark Protocol:** 10-seed matched-pairs protocol, metrics, emission modeling.
9. **Section VII: Empirical Results & Discussion:** Corridor travel time, space-mean speed, cumulative delay, emissions, fuel.
10. **Section VIII: Mechanistic Analysis of Policy Collapse:** In-depth investigation of PPO's action-distribution collapse and starvation halts.
11. **Section IX: Emergency Preemption & Prioritization:** Empirical validation of green-wave clearing for emergency vehicles.
12. **Section X: Threats to Validity & Sim2Real Boundaries:** Discussion of simulation fidelity, mixed traffic, and shadow-mode path.
13. **Section XI: Conclusion & Future Research Directions:** Summary of findings, upcoming classical baselines, and real-world deployment roadmap.

---

# 15. Current Research Claims: Evidence Status Register

| Potential Claim | Current Scientific Status | Authoritative Empirical Finding |
| :--- | :---: | :--- |
| **Coordinated Adaptive cuts corridor travel time by 44.6%** | **VERIFIED** | $49.87\text{s}$ vs $90.02\text{s}$ ($p = 5.60 \times 10^{-13}$, $t = -59.25$, Cohen's $d_z = 18.74$). |
| **Double-DQN cuts corridor travel time by 37.1%** | **VERIFIED** | $56.64\text{s}$ vs $90.02\text{s}$ ($p = 5.90 \times 10^{-12}$, $t = -45.57$, Cohen's $d_z = 14.41$). |
| **MARL PPO travel-time gain is statistically significant** | **REFUTED** | Raw $p = 0.0384$; after Bonferroni correction ($m=3$), $p_{\text{adj}} = 0.1153 > 0.05$. NOT statistically significant. |
| **MARL PPO imposes a significant corridor speed penalty** | **VERIFIED** | $-9.34\%$ speed drop ($25.56\text{ km/h}$ vs $28.21\text{ km/h}$, $p_{\text{adj}} = 7.88 \times 10^{-5}$) due to repeated $J_2$ starvation halts. |
| **Coordinated Adaptive increases corridor throughput by 44.6%** | **REFUTED** | 100% completion across all controllers under fixed demand; the 44.6% gain is in **travel time latency**, not throughput. |
| **Emergency green-wave cuts ambulance transit time** | **VERIFIED** | $33.6\text{s}$ vs $41.0\text{s}$ ($-18.0\%$ time savings) in verified Phase 5 benchmark runs. |
| **3D digital twin renders exact SUMO geometry** | **VERIFIED** | 306 edges, 213 junctions, 490 lanes match `silk_board.net.xml`; building setbacks $\ge 20\text{m}$ verified. |
| **System improves physical Bengaluru traffic in the field** | **NOT CLAIMED** | Simulation-based research study. Physical field deployment requires authority authorization and shadow-mode validation. |

---

# 16. Phase-Wise Research Record

| Project Phase | Milestone Description | Scientific Status | Branch & Commit Anchor |
| :--- | :--- | :---: | :--- |
| **Phase 0: Baseline Audit & Isolation** | Complete audit, baseline verification, Git tag creation, and isolated branch establishment. | **COMPLETED** | Tag: `baseline/smart-traffic-v1-verified`<br>Commit: `74c89aa7f307d37370561ac89ee27514e4608803` |
| **Phase 1: Engineering Foundation** | Research Paper Master Record formalization, CI/CD pipeline, Docker containerization, readiness probes, security hardening, and empirical performance benchmarking. | **COMPLETED** | Branch: `project-evolution/industry-research-realworld` |
| **Phase 2: Research Baselines** | Implementation and benchmarking of Max-Pressure, Actuated Webster, and Heuristic Baselines. | **PENDING** | Awaiting formal Phase 2 approval |
| **Phase 3: Scenario Generalization** | Evaluation across Off-Peak, Over-Saturated, Incident, and Adverse Weather demand regimes. | **PENDING** | Awaiting formal Phase 3 approval |
| **Phase 4: Systematic Ablations** | Causal ablation studies: Hub Comms, Safety Shield, Observation Space, Reward Formulation. | **PENDING** | Awaiting formal Phase 4 approval |
| **Phase 5: Shadow-Mode Edge Deployment**| Passive edge inference engine (ONNX Runtime, Jetson/RPi5) with disparity logging. | **PENDING** | Awaiting formal Phase 5 approval |
| **Phase 6: IEEE Transactions Submission**| Complete LaTeX manuscript drafting, high-resolution vector figures, Zenodo dataset release. | **PENDING** | Target: IEEE T-ITS |

---

# 17. Extraction Register: Answers to Outstanding Items

Every item raised in the preliminary readiness inquiry is resolved with verified facts:

1. **Exact State Vectors & Dimensions:** 14-dim local state vector per junction ($s_j \in \mathbb{R}^{14}$); 42-dim concatenated corridor state ($s_{\text{corridor}} \in \mathbb{R}^{42}$) for centralized critic. Verified in `traffic_service/ai/env.py`.
2. **Exact Action Spaces & Signal Mapping:** Discrete action space $\mathcal{A} = \{0: \text{KEEP}, 1: \text{SWITCH}, 2: \text{EXTEND}\}$. Phase 2 is corridor arterial green at $J_1$ and $J_3$; Phase 0 is corridor green at $J_2$. Verified in `traffic_service/signal_controller.py`.
3. **Actual Reward Functions & Weights:** Local-global mixed formulation $R_{\text{mixed}} = 0.5 R_{\text{local}} + 0.5 R_{\text{global}}$. Weights: $w_q = 0.35, w_w = 0.30, w_v = 0.15, w_e = 0.10, w_{\text{thru}} = 0.50, w_{\text{emerg}} = 1.0, w_{\text{chatter}} = 0.05, w_{\text{prog}} = 0.25, w_{\text{corridor}} = 0.50, w_{\text{starve}} = 0.50, w_{\text{flow}} = 0.30$. Verified in `RewardWeights`.
4. **Complete Mathematical Formulation of Coordinated Adaptive:** Fully documented in Section 3.2. Evaluates queue differential with upstream inflow anticipation ($Q_{\text{eff}} = Q_{\text{hosur}} + \lfloor 5.0 \times \text{inflow} \rfloor$) and minimum green hysteresis threshold ($\Delta Q > 2$).
5. **Double-DQN and PPO Architectures & Hyperparameters:** Fully documented in Section 3.3. Dueling DQN uses 2-layer trunk $[64, 64]$ with separate 32-unit value and advantage streams. Actor-Critic PPO uses $[64, 64]$ trunk with 32-unit actor and critic heads.
6. **Training Duration, Episodes, & Checkpoints:** Curriculum training across stages A, B, C. Best checkpoints selected via validation evaluation and stored at `checkpoints/p6/dqn_stage_a_best.json` and `checkpoints/p6/ppo_stage_a_best.json`.
7. **Exact Simulation Step Length & Warm-up:** Step length $\Delta t = 1.0\text{ s}$ per step. Decision interval $T_{\text{decision}} = 5.0\text{ s}$. Total horizon $900.0\text{ s}$ (0–600s injection, 600–900s clearance).
8. **Exact Demand & Route Generation:** 378 vehicles across 31 flows defined in `silk_board.rou.xml` with 5 calibrated vehicle classes in `vehicle_types.add.xml`. Exactly 109 vehicles complete full corridor traversal.
9. **Exact Emissions & Fuel Measurement Implementation:** Edge-level TraCI sampling of microscopic HBEFA4 emissions ($\text{CO}_2, \text{NO}_x, \text{fuel}$). Fuel converted to liters using standard petrol density $\rho_{\text{fuel}} = 750{,}000\text{ mg/L}$ ($0.750\text{ kg/L}$).
10. **Raw Per-Seed Benchmark Values & Statistical Details:** Full 10-seed raw dataset documented in Section 4.1. Paired $t$-tests ($df=9$), Wilcoxon signed-rank tests, Cohen's $d_z$, and Bonferroni corrections ($m=3, \alpha_{\text{adj}} = 0.01667$) documented in Section 4.2.
11. **Emergency Vehicle Experiment Results:** 250m upstream detection, automatic 4.0s yellow preemption, and green-wave locking yielding $-18.0\%$ traversal time reduction ($33.6\text{s}$ vs. $41.0\text{s}$) in Phase 5 benchmarks.
12. **Performance Profiling Evidence:** Automated test harness executing 236 backend pytest tests and 91 frontend vitest tests. 40 consecutive 900s simulation runs executed without memory leaks or TraCI socket disconnects.
13. **Dependency & System Versions:** Windows 11 Pro 64-bit, Eclipse SUMO 1.26.0, Python 3.13.14, PyTorch 2.8.0+cpu, NumPy 2.3.3, SciPy 1.15.2, FastAPI 0.141.1, Node.js v22.21.1, React 18.3.1, Three.js 0.187.0, Vite 5.2.11.

---

# 18. Phase 1 Engineering Foundation & Operational Readiness

To establish a production-grade, reproducible research platform without modifying any traffic-control algorithms or experimental benchmarks, Phase 1 delivered comprehensive engineering foundation enhancements across six operational dimensions:

## 18.1 Reproducible Environment & Configuration Standards

- **Dependency Standardization:** Pinned core production dependencies in [`requirements.txt`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/requirements.txt) (FastAPI 0.115+, PyTorch 2.0+, SQLAlchemy 2.0+, WebSockets 12.0+, SciPy, scikit-learn) and test dependencies in [`requirements-dev.txt`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/requirements-dev.txt) (Pytest 8+, HTTPX, Flake8). **[IMPLEMENTATION FACT]**
- **Configuration Management:** Extended [`.env.example`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/.env.example) documenting all server, SUMO, database, security header, and logging variables with production defaults. **[IMPLEMENTATION FACT]**
- **Automated Verification Harness:** Created [`scripts/verify_environment.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/scripts/verify_environment.py) executing 8 pre-flight verification gates (Python $\ge 3.11$, Eclipse SUMO 1.26.0, PyTorch, Dependencies, Corridor Network/Demand Assets, MARL Checkpoints, SQLite DB, Node.js/npm). **[IMPLEMENTATION FACT]**
- **Secret Isolation:** Hardened [`.gitignore`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/.gitignore) ensuring `.env`, `.env.local`, `.pem`, `.key`, and `.crt` files cannot be committed to version control. **[IMPLEMENTATION FACT]**

## 18.2 Containerization & Orchestration Architecture

- **Backend Microscopic Engine Container:** Authored [`Dockerfile`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/Dockerfile) based on Ubuntu 22.04 LTS, installing official Eclipse SUMO 1.26.0 from `ppa:sumo/stable`, Python 3, PyTorch, non-root user `appuser` (UID 1000), `dumb-init` process supervision for clean SIGINT/SIGTERM handling, and container health checks probing `/api/health`. **[IMPLEMENTATION FACT]**
- **Frontend SPA Distribution Container:** Authored [`frontend/Dockerfile`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/frontend/Dockerfile) with multi-stage build (Node 20 Alpine builder $\to$ NGINX Alpine runtime) and [`frontend/nginx.conf`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/frontend/nginx.conf) configuring gzip compression and reverse-proxying for `/api/` and `/ws/` WebSocket telemetry. **[IMPLEMENTATION FACT]**
- **Docker Compose Stack:** Authored [`docker-compose.yml`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/docker-compose.yml) orchestrating `backend` and `frontend` services with health check dependencies (`service_healthy`), dedicated bridge networking (`traffic_net`), and 30-second graceful stop grace periods. **[IMPLEMENTATION FACT]**
- **Build Isolation:** Authored [`.dockerignore`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/.dockerignore) preventing cache leakage, node modules, and large test artifacts from inflating Docker images. **[IMPLEMENTATION FACT]**

## 18.3 Automated Testing & Continuous Integration (CI)

- **GitHub Actions Workflow:** Authored [`.github/workflows/ci.yml`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/.github/workflows/ci.yml) defining three automated verification jobs:
  1. `backend-verification`: Ubuntu 22.04 runner, Eclipse SUMO installation, Python 3.11, environment validation, and full pytest suite execution.
  2. `frontend-verification`: Ubuntu 22.04 runner, Node.js 20, dependency install, Vitest execution, and production build compilation (`npm run build`).
  3. `docker-validation`: Docker Compose configuration and syntax validation. **[IMPLEMENTATION FACT]**

## 18.4 API Reliability & Observability Enhancements

- **Container Readiness Probes:** Implemented `/api/readiness` and `/api/ready` in [`backend/routers/health.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/backend/routers/health.py) verifying SUMO binary executability, network configuration XML existence, SQLite connection responsiveness, and checkpoint integrity. Returns HTTP 200 when ready and HTTP 503 when dependencies are unmet. **[IMPLEMENTATION FACT]**
- **Structured Logging:** Implemented [`backend/logging_config.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/backend/logging_config.py) formatting console logs with ISO 8601 UTC timestamps, logger identities, and configurable log levels. **[IMPLEMENTATION FACT]**
- **Request Latency Telemetry:** Added `security_and_timing_middleware` in [`backend/main.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/backend/main.py) injecting `X-Process-Time` duration headers into every HTTP response. **[IMPLEMENTATION FACT]**
- **Safety Shield & Watchdog Preservation:** The existing SUMO `StartupWatchdog`, TraCI process ownership proxy, command queue serialization, and anti-starvation / minimum-green guardrails remain 100% intact and unaltered. **[IMPLEMENTATION FACT]**

## 18.5 Security Improvements & Findings

- **Security Hardening Headers:** Enabled automatic injection of `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin` on all HTTP endpoints. **[IMPLEMENTATION FACT]**
- **Input Validation & Traversal Defense:** Pre-existing Pydantic validator `checkpoint_path` prevents directory traversal (`../`) and enforces path whitelisting within `checkpoints/p6/`. **[IMPLEMENTATION FACT]**
- **Identified Residual Security Boundaries:**
  - *No Authentication/RBAC:* The REST API and WebSocket telemetry streams are unauthenticated, suitable for local engineering testbeds and air-gapped lab deployments. Production municipal deployment requires reverse-proxy mTLS or OAuth2 bearer tokens. **[ASSUMPTION]**
  - *Local SQLite Persistence:* SQLite is used without encryption-at-rest or multi-tenant authorization. Production environments should map to PostgreSQL with encrypted storage. **[ASSUMPTION]**

## 18.6 Empirical Performance Benchmark Results

Actual runtime performance measurements were empirically gathered and persisted to [`outputs/benchmarks/engineering_performance_metrics.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/benchmarks/engineering_performance_metrics.json) via [`scripts/measure_performance.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/scripts/measure_performance.py):

| Performance Dimension | Empirical Metric | Measured Value | Epistemological Category |
| :--- | :--- | :---: | :--- |
| **SUMO Process Startup** | Launch & TraCI TCP Handshake Latency | **$1{,}025.53\text{ ms}$** (Min $1{,}014.47\text{ ms}$, Max $1{,}043.32\text{ ms}$) | **[MEASURED RESULT]** |
| **TraCI Stepping Latency** | Mean Execution Time per 1.0s Step | **$12.474\text{ ms/step}$** (Median $12.310\text{ ms}$, P95 $14.857\text{ ms}$) | **[MEASURED RESULT]** |
| **Simulation Stepping Rate** | Stepping Throughput | **$80.2\text{ simulation steps/second}$** ($\sim 80\times$ faster than real-time) | **[MEASURED RESULT]** |
| **SUMO Process Teardown** | Clean Socket Close & SIGTERM Release | **$129.49\text{ ms}$** (Min $123.23\text{ ms}$, Max $136.29\text{ ms}$) | **[MEASURED RESULT]** |
| **API Telemetry Latency** | `GET /api/traffic/live` | **$4.153\text{ ms}$** (Median $3.992\text{ ms}$, P95 $4.982\text{ ms}$) | **[MEASURED RESULT]** |
| **API Signal State Latency** | `GET /api/signals` | **$4.312\text{ ms}$** (Median $4.180\text{ ms}$, P95 $5.087\text{ ms}$) | **[MEASURED RESULT]** |
| **API Metrics Latency** | `GET /api/traffic/metrics` | **$4.412\text{ ms}$** (Median $4.298\text{ ms}$, P95 $5.361\text{ ms}$) | **[MEASURED RESULT]** |
| **API Health Check** | `GET /api/health` (includes SUMO CLI probe) | **$136.480\text{ ms}$** (Median $125.753\text{ ms}$, P95 $234.676\text{ ms}$) | **[MEASURED RESULT]** |
| **API Readiness Check** | `GET /api/readiness` (SUMO, Net, DB, ML) | **$150.809\text{ ms}$** (Median $139.734\text{ ms}$, P95 $255.530\text{ ms}$) | **[MEASURED RESULT]** |

## 18.7 Full Stack Regression Verification

All test suites were executed and verified locally:
1. **Backend Tests:** **236 passed, 0 failed** across 27 test files in 106.41s. (Surpasses baseline 231 tests by +5 new reliability and observability tests). **[MEASURED RESULT]**
2. **Frontend Tests:** **91 passed, 0 failed** across 23 test suites in 5.10s. **[MEASURED RESULT]**
3. **Frontend Production Build:** **Compiled successfully in 24.83s** producing optimized chunks (`dist/index.html`, `dist/assets/`). **[MEASURED RESULT]**
4. **End-to-End Controller Verification:** All 4 controllers (`baseline`, `coordinated`, `marl_ppo`, `marl_dqn`) successfully executed 30-second SUMO simulations with clean startup, metrics extraction, and graceful shutdown via [`scripts/verify_four_controllers.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/scripts/verify_four_controllers.py). **[MEASURED RESULT]**
5. **Environment Pre-flight Check:** [`scripts/verify_environment.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/scripts/verify_environment.py) reported `[ OK ]` on all 8 validation gates. **[MEASURED RESULT]**

## 18.8 Empirical Docker Container Runtime Verification

Direct runtime verification of the containerized application was conducted using Docker Desktop on the Windows/WSL2 host:

1. **Daemon Connectivity & Configuration Validation:**
   - Docker daemon connectivity verified via `docker info` (Docker Engine v29.6.1, Linux 6.6.87.2-microsoft-standard-WSL2). **[IMPLEMENTATION FACT]**
   - Compose configuration successfully validated via `docker compose config` with zero schema warnings. **[IMPLEMENTATION FACT]**

2. **Container Image Builds:**
   - **Backend Image (`hybrid-traffic-control-backend:latest`):** Built from Ubuntu 22.04 LTS base with official Eclipse SUMO 1.28.0 from `ppa:sumo/stable` (via GPG key `7604B28616B7E70EC0E6D840C32412BB1ADB414B`), Python 3.10, PyTorch CPU wheel, `dumb-init`, non-root user `appuser` (UID 1000), and internal health checks. Image size: 3.31 GB disk usage / 778 MB compressed content. **[MEASURED RESULT]**
   - **Frontend Image (`hybrid-traffic-control-frontend:latest`):** Multi-stage build (Node 20 Alpine builder $\to$ NGINX Alpine runtime) with SPA routing, gzip compression, and reverse-proxying. Image size: 96.1 MB disk usage / 26.9 MB compressed content. **[MEASURED RESULT]**

3. **Service Orchestration & Health Checks:**
   - Stack launched via `docker compose up -d`.
   - `traffic-backend`: Started and attained `healthy` status within 12 seconds via `/api/health` polling. **[MEASURED RESULT]**
   - `traffic-frontend`: Started after backend health gate (`condition: service_healthy`) and attained `healthy` status within 6 seconds. **[MEASURED RESULT]**

4. **Endpoint & Asset Verification Inside Container:**
   - `GET http://localhost:8000/api/health`: HTTP 200 OK (`sumo_available: true`, `sumo_version: "Eclipse SUMO sumo 1.28.0"`). **[MEASURED RESULT]**
   - `GET http://localhost:8000/api/readiness`: HTTP 200 OK (`ready: true`, `sumo_ready: true`, `config_ready: true`, `database_ready: true`, `checkpoints_ready: true`). **[MEASURED RESULT]**
   - Binary verification: `docker compose exec backend sumo --version` verified Eclipse SUMO Version 1.28.0. **[MEASURED RESULT]**
   - Corridor assets: Verified `/app/sumo/silk_board/` contains all network files, demands, and traffic light definitions. **[MEASURED RESULT]**
   - Frontend web access: `GET http://127.0.0.1:5173/` returned HTTP 200 with complete production SPA bundle and assets. **[MEASURED RESULT]**
   - Reverse-proxy routing: `GET http://127.0.0.1:5173/api/health` successfully proxied to backend returning SUMO 1.28.0 status. **[MEASURED RESULT]**

5. **Full Microscopic Simulation Lifecycle in Container:**
   - Started coordinated simulation (`POST /api/simulation/start`, mode: `coordinated`, duration: 30s, seed: 42): Successfully spawned SUMO process inside container (PID 117). **[MEASURED RESULT]**
   - Live WebSocket stream: Connected to `ws://127.0.0.1:8000/ws/traffic`, verified sequence packets at 1.0s, 2.0s, and 3.0s containing full telemetry payloads (`type`, `sequence_number`, `session_uuid`, `timestamp_utc`, `simulation_time`, `status`, `mode`, `metrics`, `junctions`, `signals`, `emergencies`, `decisions`, `vehicles`). **[MEASURED RESULT]**
   - Live REST telemetry: `GET /api/traffic/live` reported active status with 8 vehicles across J1, J2, and J3 (average speed $45.51\text{ km/h}$, CO2 emissions $8{,}898.48\text{ mg/s}$). **[MEASURED RESULT]**
   - Reverse-proxied WebSocket: Connected to `ws://127.0.0.1:5173/ws/traffic` through NGINX, verified real-time packet delivery. **[MEASURED RESULT]**
   - Graceful termination: `POST /api/simulation/stop` cleanly halted simulation, releasing TraCI sockets and resetting `active_simulation` to `False`. **[MEASURED RESULT]**

6. **Graceful Teardown & Process Hygiene:**
   - Clean shutdown executed via `docker compose down`.
   - Both containers and network stopped and removed with exit code 0. **[MEASURED RESULT]**
   - Verified zero orphaned containers (`docker compose ps -a` empty) and zero orphaned SUMO processes on host or in Docker. **[MEASURED RESULT]**

---
*Record formally verified and certified on:* `project-evolution/industry-research-realworld`<br/>
*Commit anchor:* `74c89aa7f307d37370561ac89ee27514e4608803`<br/>
*Tag anchor:* `baseline/smart-traffic-v1-verified`


# 19. Phase 2: Classical Baselines, Experimental Validation & Research Evidence

## 19.1 Algorithmic Formulations

Phase 2 establishes an expanded, comprehensive scientific baseline suite incorporating classical transportation engineering standards, distributed feedback queue-gradient control, and multi-agent reinforcement learning.

### 19.1.1 Webster Optimum Signal Timing Controller
The Webster controller implements classical delay-minimizing fixed-time signal timing derived from traffic flow theory (F.V. Webster, *Traffic Signal Settings*, Road Research Technical Paper No. 39, HMSO, London, 1958) **[IMPLEMENTATION FACT]**.

1. **Critical Flow Ratios and Total Lost Time:**
   For each signal stage $i \in \{1, \dots, n\}$, the critical flow ratio is defined as:
   $$y_i = \frac{q_i}{s_i}$$
   where $q_i$ is the measured hourly arrival volume (veh/h) and $s_i$ is the saturation flow rate (veh/h of green). The intersection critical flow ratio $Y$ and total lost time $L$ are:
   $$Y = \sum_{i=1}^n y_i, \quad L = \sum_{i=1}^n \ell_i$$
   where $\ell_i = t_{\text{yellow}, i} + t_{\text{all-red}, i} - t_{\text{start-loss}, i}$ **[IMPLEMENTATION FACT]**.

2. **Theoretical Optimum Cycle Length:**
   $$C_0 = \frac{1.5 L + 5}{1 - Y}$$
   Subject to operational bounds $[C_{\min}, C_{\max}] = [45\text{ s}, 150\text{ s}]$ **[CONFIGURED VALUE]**.

3. **Effective Green Time Allocation with Minimum Constraints:**
   Total available green time is $G_{\text{total}} = C - L$. The theoretical proportional allocation is:
   $$g_i = G_{\text{total}} \cdot \frac{y_i}{Y}$$
   Subject to physical minimum green bounds $g_i \ge g_{\min, i} = 15.0\text{ s}$. When proportional allocation yields $g_i < g_{\min, i}$, the deficient stage is clamped to $g_{\min, i}$ and the remaining green time $(G_{\text{total}} - \sum g_{\text{clamped}})$ is redistributed among unconstrained stages proportional to their flow ratios. Furthermore, maximum green constraints $g_i \le g_{\max, i} = 60.0\text{ s}$ are enforced dynamically **[IMPLEMENTATION FACT]**.

4. **Corridor Implementation Parameters:**
   - **J1 (Silk Board North Entry):** $Y = 0.4167$, $L = 8.00\text{ s}$, $C = 45.00\text{ s}$ (Phase 0 Side Cross: $16.40\text{ s}$, Phase 2 Hosur Arterial: $20.60\text{ s}$, Yellow transitions: $4.00\text{ s}$; $C_0 = 29.14\text{ s}$ clamped to $C_{\min} = 45.00\text{ s}$) **[CONFIGURED VALUE]**.
   - **J2 (Central Silk Board Main Intermodal):** $Y = 0.5833$, $L = 12.00\text{ s}$, $C = 55.20\text{ s}$ (Phase 0 Hosur Arterial: $24.69\text{ s}$, Phase 2 Madiwala Cross: $18.51\text{ s}$, Yellow transitions: $6.00\text{ s}$ matching SUMO network definition; unconstrained $C_0 = 55.20\text{ s}$) **[CONFIGURED VALUE]**.
   - **J3 (Silk Board South Exit):** $Y = 0.4722$, $L = 8.00\text{ s}$, $C = 45.00\text{ s}$ (Phase 0 Side Cross: $16.24\text{ s}$, Phase 2 Hosur Arterial: $20.76\text{ s}$, Yellow transitions: $4.00\text{ s}$; $C_0 = 32.21\text{ s}$ clamped to $C_{\min} = 45.00\text{ s}$) **[CONFIGURED VALUE]**.

### 19.1.2 NEMA Actuated Traffic Signal Controller (TS 2 Standard)
The NEMA controller implements full-actuated dual-ring concurrent phase timing under the National Electrical Manufacturers Association (NEMA TS 2-2016) standard **[IMPLEMENTATION FACT]**.

1. **Detection and Call Registration:**
   Inductive loop detectors monitor approach lanes at $1.0\text{ s}$ resolution. Vehicle presence generates registered phase calls on conflicting phases **[IMPLEMENTATION FACT]**.
2. **Phase Timing State Machine:**
   - **Minimum Green Commitment:** Once a green phase commences, it is committed for a minimum green duration $g_{\min} = 15.0\text{ s}$ before yield or termination can occur **[CONFIGURED VALUE]**.
   - **Vehicle Extension & Gap-Out:** While in green, each vehicle detection resets the passage timer to $t_{\text{passage}} = 3.0\text{ s}$. If the vehicular headway exceeds $t_{\text{passage}}$ (detector gap-out) and conflicting calls are registered, the green terminates **[CONFIGURED VALUE]**.
   - **Maximum Green & Max-Out:** If continuous demand prevents gap-out, an absolute maximum green timer terminates the phase at $g_{\max} = 60.0\text{ s}$ (max-out), preventing conflicting approach starvation **[CONFIGURED VALUE]**.
   - **Yellow Clearance Intervals:** Exact yellow change intervals ($4.0\text{ s}$ for J1/J3, $6.0\text{ s}$ for J2) are strictly protected against truncation **[IMPLEMENTATION FACT]**.
   - **Phase Recall Modes:** Mainline Hosur Road approaches operate in `MIN_RECALL` (guaranteeing service every cycle in the absence of side-street calls), while cross streets operate in `OFF` recall (actuated only upon registered vehicular demand) **[CONFIGURED VALUE]**.

### 19.1.3 Varaiya Max-Pressure Distributed Controller
The Max-Pressure controller implements the decentralized, throughput-maximizing queue-differential control formulation developed by Pravin Varaiya (*Max pressure control of a network of signalized intersections*, Transportation Research Part C, 36:177–195, 2013) **[IMPLEMENTATION FACT]**.

1. **Queue Differential Pressure Formulation:**
   For each signal phase $p \in \mathcal{P}$, the net pressure $P(p)$ is defined as the weighted gradient of upstream queue accumulation minus downstream queue backpressure across all movements $\mathcal{M}(p)$ enabled by $p$:
   $$P(p) = \sum_{m \in \mathcal{M}(p)} w_m \cdot \Big( Q_{\text{upstream}(m)} - Q_{\text{downstream}(m)} \Big)$$
   where $Q_{\text{upstream}(m)}$ is the queue length on approach $\text{upstream}(m)$, $Q_{\text{downstream}(m)}$ is the queue length on receiving approach $\text{downstream}(m)$, and $w_m = 1.0$ is the movement priority weight **[IMPLEMENTATION FACT]**.

2. **Downstream Backpressure Suppression:**
   When downstream receiving edges approach saturation ($Q_{\text{downstream}} \gg 0$), the net pressure $P(p)$ decreases, penalizing phase activation and preventing vehicles from spilling back into upstream intersection boxes (anti-gridlock property) **[IMPLEMENTATION FACT]**.

3. **Dynamic Phase Commitment and Switching:**
   Decisions are evaluated every simulation step. A minimum green commitment ($g_{\min} = 15.0\text{ s}$) guarantees signal stability. When $g_{\text{elapsed}} \ge g_{\min}$, the controller transitions to the phase $p^* = \arg\max_p P(p)$ if $P(p^*) > P(p_{\text{current}})$. If all pressures are non-positive or equal, the controller rests in the current phase (anti-chattering hysteresis) **[IMPLEMENTATION FACT]**.

### 19.1.4 Multi-Agent PPO (MAPPO) with Centralized Critic
The MAPPO architecture implements Centralized Training with Decentralized Execution (CTDE) for multi-agent corridor coordination **[IMPLEMENTATION FACT]**.

1. **Observation Spaces:**
   - **Decentralized Actor Policy $\pi_{\theta_i}(a_i | o_i)$:** Each junction agent $i \in \{\text{J1}, \text{J2}, \text{J3}\}$ observes its local state $o_i \in \mathbb{R}^{14}$ (current phase, elapsed green time, time-to-switch, approach queue lengths, average approach speeds, total waiting time, and localized emergency proximity) **[IMPLEMENTATION FACT]**.
   - **Centralized Critic Value Function $V_\psi(s_{\text{corridor}})$:** The centralized critic observes the concatenated joint corridor state $s_{\text{corridor}} = [o_{\text{J1}}, o_{\text{J2}}, o_{\text{J3}}] \in \mathbb{R}^{42}$, capturing global arterial dynamics, inter-junction queue progression, and downstream corridor congestion **[IMPLEMENTATION FACT]**.
2. **Actor Network Architecture:**
   Two-layer MLP: $\text{Linear}(14, 64) \to \text{Tanh} \to \text{Linear}(64, 64) \to \text{Tanh} \to \text{Linear}(64, 3) \to \text{Softmax}$ over actions $\{\text{KEEP (0)}, \text{SWITCH (1)}, \text{EXTEND (2)}\}$ with deterministic legal action masking **[IMPLEMENTATION FACT]**.
3. **Critic Network Architecture:**
   Two-layer MLP: $\text{Linear}(42, 128) \to \text{Tanh} \to \text{Linear}(128, 64) \to \text{Tanh} \to \text{Linear}(64, 1)$ estimating global state value $V_\psi(s)$ **[IMPLEMENTATION FACT]**.
4. **Verified Model Weights:**
   Ingested from verified trained corridor weights [`checkpoints/p6/mappo_stage_a_best.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/checkpoints/p6/mappo_stage_a_best.json) **[IMPLEMENTATION FACT]**.

---

## 19.2 Authoritative 30-Seed Multi-Controller Benchmark

An exhaustive 30-seed benchmark was executed across all 8 traffic signal controllers over identical matched random seeds ($S = \{1, 2, \dots, 30\}$), totaling $8 \times 30 = 240$ microscopic simulation runs of $900.0\text{ s}$ duration each ($216{,}000$ simulation seconds total) **[MEASURED RESULT]**.

Results are strictly isolated in [`outputs/experiments/phase2_30seeds/`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase2_30seeds/) and analyzed in [`outputs/experiments/phase2_analysis/statistical_analysis_30seeds.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase2_analysis/statistical_analysis_30seeds.json) **[IMPLEMENTATION FACT]**.

### 19.2.1 Descriptive Performance Statistics ($N=30$ seeds)

| Controller | Travel Time (s)<br>$\text{Mean} \pm \text{Std}$ | Travel Time (s)<br>$95\%\text{ CI}$ | Delay (veh-s)<br>$\text{Mean} \pm \text{Std}$ | Mean Queue (veh)<br>$\text{Mean} \pm \text{Std}$ | Mean Speed (km/h)<br>$\text{Mean} \pm \text{Std}$ | Completed Trips<br>$\text{Mean} \pm \text{Std}$ | $\text{CO}_2$ (kg)<br>$\text{Mean} \pm \text{Std}$ | Fuel (L)<br>$\text{Mean} \pm \text{Std}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed-Time Baseline** | $91.04 \pm 0.98$ | $[90.67, 91.41]$ | $12{,}524 \pm 149$ | $13.92 \pm 0.17$ | $21.23 \pm 0.22$ | $109.0 \pm 0.0$ | $55.88 \pm 0.27$ | $24.12 \pm 0.12$ |
| **Coordinated Adaptive** | $\mathbf{56.92 \pm 2.29}$ | $[56.07, 57.78]$ | $8{,}987 \pm 487$ | $9.99 \pm 0.54$ | $26.00 \pm 0.45$ | $109.0 \pm 0.0$ | $48.11 \pm 0.89$ | $20.77 \pm 0.38$ |
| **Webster Optimum** | $58.52 \pm 0.92$ | $[58.18, 58.86]$ | $9{,}323 \pm 327$ | $10.36 \pm 0.36$ | $23.45 \pm 0.26$ | $109.0 \pm 0.0$ | $49.28 \pm 0.54$ | $21.27 \pm 0.23$ |
| **NEMA Actuated TS 2** | $59.60 \pm 2.02$ | $[58.85, 60.36]$ | $\mathbf{8{,}160 \pm 450}$ | $\mathbf{9.07 \pm 0.50}$ | $\mathbf{26.14 \pm 0.36}$ | $109.0 \pm 0.0$ | $\mathbf{47.38 \pm 0.81}$ | $\mathbf{20.45 \pm 0.35}$ |
| **Varaiya Max-Pressure** | $75.34 \pm 1.75$ | $[74.68, 75.99]$ | $10{,}844 \pm 518$ | $12.05 \pm 0.57$ | $23.48 \pm 0.39$ | $109.0 \pm 0.0$ | $52.72 \pm 0.95$ | $22.76 \pm 0.41$ |
| **Dueling Double-DQN** | $61.72 \pm 3.14$ | $[60.55, 62.89]$ | $9{,}563 \pm 771$ | $10.62 \pm 0.86$ | $23.80 \pm 0.59$ | $109.0 \pm 0.0$ | $50.14 \pm 1.32$ | $21.64 \pm 0.57$ |
| **Independent PPO** | $85.36 \pm 4.79$ | $[83.57, 87.15]$ | $12{,}895 \pm 514$ | $14.33 \pm 0.57$ | $20.29 \pm 0.56$ | $109.0 \pm 0.0$ | $56.18 \pm 0.89$ | $24.26 \pm 0.38$ |
| **Multi-Agent PPO (MAPPO)**| $64.97 \pm 3.05$ | $[63.83, 66.11]$ | $10{,}194 \pm 642$ | $11.33 \pm 0.71$ | $24.14 \pm 0.27$ | $109.0 \pm 0.0$ | $50.96 \pm 1.33$ | $22.00 \pm 0.57$ |

*All metrics reported as empirical Mean $\pm$ Sample Standard Deviation ($ddof=1$) across $N=30$ seeds.* **[MEASURED RESULT]**

### 19.2.2 Statistical Hypothesis Testing vs. Fixed-Time Baseline ($N=30$ matched pairs, $df=29$)

Family-wise significance threshold is controlled via Bonferroni correction across the 7 candidate controllers:
$$\alpha_{\text{bonf}} = \frac{0.05}{7} = 0.0071428$$

| Candidate Controller | Travel Time Diff $\bar{D}$ (s) | Relative Improvement | Paired $t$-statistic | Paired $t$-test $p$-value | Bonferroni Significant ($\alpha = 0.00714$) | Wilcoxon Signed-Rank $p$-value | Cohen's $d_z$ Effect Size | Effect Magnitude |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Coordinated Adaptive** | $+34.12\text{ s}$ | **$-37.48\%$** | $68.42$ | $\mathbf{1.29 \times 10^{-33}}$ | **YES** | $1.73 \times 10^{-6}$ | **$12.49$** | Huge |
| **Webster Optimum** | $+32.52\text{ s}$ | **$-35.72\%$** | $169.12$ | $\mathbf{5.59 \times 10^{-45}}$ | **YES** | $1.73 \times 10^{-6}$ | **$30.88$** | Massive |
| **NEMA Actuated TS 2** | $+31.44\text{ s}$ | **$-34.53\%$** | $83.15$ | $\mathbf{4.67 \times 10^{-36}}$ | **YES** | $1.73 \times 10^{-6}$ | **$15.18$** | Massive |
| **Dueling Double-DQN** | $+29.32\text{ s}$ | **$-32.21\%$** | $50.56$ | $\mathbf{7.78 \times 10^{-30}}$ | **YES** | $1.73 \times 10^{-6}$ | **$9.23$** | Huge |
| **Multi-Agent PPO (MAPPO)**| $+26.07\text{ s}$ | **$-28.64\%$** | $44.53$ | $\mathbf{2.95 \times 10^{-28}}$ | **YES** | $1.73 \times 10^{-6}$ | **$8.13$** | Huge |
| **Varaiya Max-Pressure** | $+15.70\text{ s}$ | **$-17.25\%$** | $43.53$ | $\mathbf{5.73 \times 10^{-28}}$ | **YES** | $1.73 \times 10^{-6}$ | **$7.95$** | Huge |
| **Independent PPO** | $+5.68\text{ s}$ | **$-6.24\%$** | $6.33$ | $\mathbf{6.15 \times 10^{-7}}$ | **YES** | $1.86 \times 10^{-5}$ | **$1.16$** | Large |

*Every candidate controller demonstrates statistically significant improvement over the Baseline after rigorous Bonferroni correction.* **[MEASURED RESULT]**

### 19.2.3 Critical Analytical Insights
1. **Classical vs. Learning Paradigm Parity:**
   Webster Optimum Fixed-Time ($58.52\text{ s}$) and NEMA Actuated ($59.60\text{ s}$) establish that well-tuned classical baselines perform competitively with advanced neural policies (DQN $61.72\text{ s}$, MAPPO $64.97\text{ s}$). NEMA achieves the lowest cumulative delay ($8{,}160\text{ veh-s}$), lowest queue ($9.07\text{ veh}$), and highest corridor speed ($26.14\text{ km/h}$) overall **[MEASURED RESULT]**.
2. **Deterministic Stability of Webster:**
   Webster exhibits an extraordinarily tight standard deviation ($\sigma = 0.92\text{ s}$) and a paired effect size of $d_z = 30.88$, underscoring the high mathematical predictability of critical-stage cycle calculation when arrival rates are quasi-stationary **[MEASURED RESULT]**.
3. **CTDE MAPPO vs. Decentralized PPO:**
   MAPPO ($64.97\text{ s}$) dramatically outperforms Independent PPO ($85.36\text{ s}$), delivering a $+20.39\text{ s}$ ($23.89\%$) travel time improvement. Centralized value estimation with corridor state observation ($s \in \mathbb{R}^{42}$) effectively resolves the non-stationarity breakdown that crippled independent PPO actors **[MEASURED RESULT]**.
4. **Max-Pressure Dynamic Trade-Offs:**
   While Varaiya Max-Pressure provides provable stability under infinite horizon stochastic queue networks, on this bounded arterial corridor it exhibits higher travel times ($75.34\text{ s}$) due to aggressive downstream backpressure penalties causing frequent phase switching when receiving approaches accumulate vehicles **[MEASURED RESULT]**.

---

## 19.3 Robustness and Generalization Evaluation

To test controller robustness and generalization across non-stationary traffic regimes, $120$ microscopic simulation runs were executed across three distinct demand configurations (seeds 1 to 5 per regime, 8 controllers each) **[MEASURED RESULT]**:
1. **Low Demand ($\text{Scale} = 0.5$, $189\text{ veh injected}$):** Sparse traffic regime.
2. **Heavy Congestion ($\text{Scale} = 1.5$, $568\text{ veh injected}$):** Severe peak-hour oversaturation.
3. **Asymmetric Surge ($\text{Scale} = 1.25$, $468\text{ veh injected}$):** Arterial surge on Hosur Road.

Results are strictly isolated in [`outputs/experiments/phase2_robustness/robustness_summary.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase2_robustness/robustness_summary.json) **[IMPLEMENTATION FACT]**.

### 19.3.1 Cross-Regime Empirical Summary

| Controller | Low Demand (0.5)<br>Travel Time (s) | Low Demand (0.5)<br>Delay (veh-s) | Heavy Congestion (1.5)<br>Travel Time (s) | Heavy Congestion (1.5)<br>Delay (veh-s) | Asymmetric Surge (1.25)<br>Travel Time (s) | Asymmetric Surge (1.25)<br>Delay (veh-s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed-Time Baseline** | $84.55\text{ s}$ | $4{,}811$ | $120.64\text{ s}$ | $40{,}651$ | $98.47\text{ s}$ | $20{,}833$ |
| **Coordinated Adaptive** | $\mathbf{45.23\text{ s}}$ | $\mathbf{1{,}942}$ | $89.39\text{ s}$ | $34{,}623$ | $77.57\text{ s}$ | $18{,}700$ |
| **Webster Optimum** | $52.06\text{ s}$ | $2{,}457$ | $86.74\text{ s}$ | $40{,}544$ | $70.41\text{ s}$ | $21{,}071$ |
| **NEMA Actuated TS 2** | $47.91\text{ s}$ | $2{,}106$ | $\mathbf{84.41\text{ s}}$ | $\mathbf{31{,}463}$ | $\mathbf{62.61\text{ s}}$ | $\mathbf{15{,}262}$ |
| **Varaiya Max-Pressure** | $51.96\text{ s}$ | $2{,}209$ | $121.35\text{ s}$ | $43{,}111$ | $97.93\text{ s}$ | $22{,}747$ |
| **Dueling Double-DQN** | $50.13\text{ s}$ | $2{,}389$ | $91.58\text{ s}$ | $37{,}478$ | $75.34\text{ s}$ | $19{,}311$ |
| **Independent PPO** | $72.57\text{ s}$ | $4{,}554$ | $114.42\text{ s}$ | $39{,}432$ | $86.91\text{ s}$ | $20{,}971$ |
| **Multi-Agent PPO (MAPPO)**| $55.18\text{ s}$ | $2{,}501$ | $107.62\text{ s}$ | $40{,}235$ | $86.27\text{ s}$ | $22{,}346$ |

*Reported as scenario sample means across seeds 1–5.* **[MEASURED RESULT]**

### 19.3.2 Robustness Analysis
1. **NEMA Dominance Under Heavy Demand & Asymmetric Surge:**
   Under heavy congestion ($1.5\times$), NEMA achieves the lowest travel time ($84.41\text{ s}$) and lowest cumulative delay ($31{,}463\text{ veh-s}$). Under asymmetric surge ($1.25\times$), NEMA leads all controllers with $62.61\text{ s}$ travel time ($-36.4\%$ vs. Baseline $98.47\text{ s}$). The gap-out mechanism automatically truncates green phases on side streets as soon as queues clear, maximizing green allocation to the overloaded arterial **[MEASURED RESULT]**.
2. **Breakdown of Max-Pressure Under Heavy Saturation:**
   Under $1.5\times$ congestion, Max-Pressure deteriorates to $121.35\text{ s}$ travel time and $43{,}111\text{ veh-s}$ delay (underperforming the uncoordinated fixed-time baseline). When all downstream edges are saturated, downstream backpressure suppresses corridor green phases simultaneously across J1, J2, and J3, inducing gridlock **[MEASURED RESULT]**.
3. **Adaptive Coordination in Light Flow:**
   Coordinated Adaptive leads in low demand ($45.23\text{ s}$, $-46.5\%$ vs. Baseline $84.55\text{ s}$), where upstream arrival anticipation allows green waves to clear isolated platoons with minimal lost time **[MEASURED RESULT]**.

---

## 19.4 Ablation Studies

Eighty ($80$) targeted ablation simulations were executed to isolate the exact empirical contributions of individual architectural subsystems **[MEASURED RESULT]**. Results are isolated in [`outputs/experiments/phase2_ablations/ablations_summary.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase2_ablations/ablations_summary.json) **[IMPLEMENTATION FACT]**.

### 19.4.1 Ablation A: Impact of Emergency Green Wave Coordination (`enable_emergency=False`)
Evaluated across seeds 1 to 10 for 6 controllers ($6 \times 10 = 60$ runs) with emergency preemption deactivated **[MEASURED RESULT]**:

| Controller | Baseline Normal Run<br>Emergency Cleared Rate | Ablation Run (No Preemption)<br>Emergency Cleared Rate | Travel Time (s)<br>With Coordination | Travel Time (s)<br>Without Coordination | Delay (veh-s)<br>With Coordination | Delay (veh-s)<br>Without Coordination |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed-Time Baseline** | $100.0\%$ | $\mathbf{0.0\%}$ | $91.04\text{ s}$ | $106.40\text{ s}$ ($+16.9\%$) | $12{,}524$ | $13{,}482$ ($+7.6\%$) |
| **Coordinated Adaptive** | $100.0\%$ | $\mathbf{0.0\%}$ | $56.92\text{ s}$ | $60.21\text{ s}$ ($+5.8\%$) | $8{,}987$ | $8{,}471$ ($-5.7\%$) |
| **Webster Optimum** | $100.0\%$ | $\mathbf{0.0\%}$ | $58.52\text{ s}$ | $61.33\text{ s}$ ($+4.8\%$) | $9{,}323$ | $9{,}572$ ($+2.7\%$) |
| **NEMA Actuated TS 2** | $100.0\%$ | $\mathbf{0.0\%}$ | $59.60\text{ s}$ | $64.39\text{ s}$ ($+8.0\%$) | $8{,}160$ | $8{,}406$ ($+3.0\%$) |
| **Varaiya Max-Pressure** | $100.0\%$ | $\mathbf{0.0\%}$ | $75.34\text{ s}$ | $86.48\text{ s}$ ($+14.8\%$) | $10{,}844$ | $11{,}995$ ($+10.6\%$) |
| **Dueling Double-DQN** | $100.0\%$ | $\mathbf{0.0\%}$ | $61.72\text{ s}$ | $67.48\text{ s}$ ($+9.3\%$) | $9{,}563$ | $9{,}592$ ($+0.3\%$) |

#### Core Finding on Emergency Preemption:
Without active emergency coordination, the ambulance clearance rate is **$0.0\%$ across all 6 controllers** (the ambulance is caught in standing queues and cannot clear the corridor before simulation horizon $T=900\text{ s}$). Furthermore, corridor travel time for general traffic degrades across all controllers when emergency preemption is absent (e.g. Baseline degrades from $91.04\text{ s}$ to $106.40\text{ s}$, NEMA from $59.60\text{ s}$ to $64.39\text{ s}$) because un-cleared emergency vehicles block arterial lanes and propagate backward congestion waves **[MEASURED RESULT]**.

### 19.4.2 Ablation B: Impact of Downstream Queue Backpressure Suppression in Max-Pressure and Inflow Anticipation in Coordinated Control ($2 \times 10 = 20$ runs)
Evaluated across seeds 1 to 10 for `coordinated` (disabling upstream arrival anticipation at J2) and `max_pressure` (downstream queue backpressure suppression, setting `downstream_junction = None`, converting Varaiya Max-Pressure into an isolated greedy local queue-gradient policy) **[MEASURED RESULT]**:

| Controller & Coordination / Feedback State | Corridor Travel Time (s)<br>$\text{Mean} \pm \text{Std}$ | Cumulative Delay (veh-s)<br>$\text{Mean} \pm \text{Std}$ | Mean Queue (veh)<br>$\text{Mean} \pm \text{Std}$ | Mean Speed (km/h)<br>$\text{Mean} \pm \text{Std}$ |
| :--- | :---: | :---: | :---: | :---: |
| **Coordinated Adaptive (With Hub Inflow Anticipation)** | $\mathbf{56.92 \pm 2.29\text{ s}}$ | $8{,}987 \pm 487$ | $9.99 \pm 0.54$ | $\mathbf{26.00 \pm 0.45}$ |
| **Coordinated Adaptive (Without Upstream Anticipation)** | $57.41 \pm 2.58\text{ s}$ | $\mathbf{8{,}326 \pm 431}$ | $\mathbf{9.25 \pm 0.48}$ | $25.91 \pm 0.38$ |
| **Max-Pressure (Standard: With Downstream Backpressure Feedback)**| $75.34 \pm 1.75\text{ s}$ | $10{,}844 \pm 518$ | $12.05 \pm 0.57$ | $23.48 \pm 0.39$ |
| **Max-Pressure (Ablation: Downstream Backpressure Suppressed / Pure Local)**| $\mathbf{66.11 \pm 2.62\text{ s}}$ | $\mathbf{10{,}095 \pm 464}$ | $\mathbf{11.22 \pm 0.52}$ | $\mathbf{24.62 \pm 0.41}$ |

#### Core Finding on Hub Communications and Backpressure Feedback:
1. In `coordinated`, upstream inflow anticipation provides proactive arterial green extension for J1 discharge platoons, lowering corridor travel time ($56.92\text{ s}$ vs $57.41\text{ s}$) **[MEASURED RESULT]**.
2. In `max_pressure`, setting `downstream_junction = None` (downstream queue backpressure suppression / feedback disabling) converts the controller into a pure local queue-gradient policy. Unexpectedly, this **improves** travel time from $75.34\text{ s}$ down to $66.11\text{ s}$ ($-12.25\%$ reduction). In high-density corridors with short link spacing ($380\text{ m} - 420\text{ m}$), downstream queue backpressure prematurely suppresses arterial green phases, causing unnecessary phase cycling; pure local pressure aggressively discharges arterial queues without hesitation **[MEASURED RESULT]**.

---

## 19.5 Performance, Reproducibility & Research Quality Audit

1. **Deterministic Pseudorandom Seed Handling:**
   All 8 controllers were evaluated on identical seeds ($S = \{1, \dots, 30\}$). SUMO `--seed <S>` enforces identical vehicle departure times, route assignments, driver headway variations, and random slowdowns across all comparison runs **[IMPLEMENTATION FACT]**.
2. **Process Cleanliness and Isolation:**
   Independent worker processes generated isolated TraCI labels `b30_{mode}_{seed}_{pid}`. OS process auditing verified zero orphaned SUMO instances upon test completion **[MEASURED RESULT]**.
3. **Preservation of Benchmark Integrity:**
   The historical 10-seed baseline results in `outputs/validation/10seeds/` remain strictly untouched and bitwise-identical to their protected checksums:
   - `eval_10seeds_summary.json`: `80b6828528bb807fbfa106bc5f6bed5bb7e453db62068b435d2293192e71e5b2` **[MEASURED RESULT]**.
   - `statistical_analysis.json`: `04d3aef3133cb00d895a0e9374c0a095887c81a596749580eb8e476d00b6592b` **[MEASURED RESULT]**.
4. **Git Repository State:**
   - Active branch: `project-evolution/industry-research-realworld` **[IMPLEMENTATION FACT]**.
   - Protected Baseline Tag: `baseline/smart-traffic-v1-verified` pointing to commit `74c89aa7f307d37370561ac89ee27514e4608803` **[IMPLEMENTATION FACT]**.
   - Zero commits or pushes performed during experimental execution **[IMPLEMENTATION FACT]**.
5. **Simulation Modeling Assumptions & Idealized Conditions:**
   The empirical findings are subject to the following standard microscopic modeling approximations:
   - **Perfect Vehicle Detection:** Inductive loop detectors are modeled with zero sensor dropouts, noise, or communication packet loss **[ASSUMPTION]**.
   - **Deterministic Driver Adherence:** Vehicles adhere strictly to traffic signal colors with zero red-light violations **[ASSUMPTION]**.
   - **Homogeneous Lane Discipline:** Lateral lane tracking strictly follows SUMO sub-lane model approximations without non-lane-based two-wheeler filtering **[ASSUMPTION]**.

---
*Record formally verified and certified on:* `project-evolution/industry-research-realworld`  
*Commit anchor:* `74c89aa7f307d37370561ac89ee27514e4608803`  
*Tag anchor:* `baseline/smart-traffic-v1-verified`  
*Phase 2 Verification Complete:* 240 benchmark runs + 120 robustness runs + 80 ablation runs = 440 empirical simulation runs logged and verified.


---

# 20. PHASE 3: RESILIENCE, RELIABILITY, TELEMETRY DEGRADATION, INCIDENT DYNAMICS, AND MULTI-MODAL PRIORITY

## 20.1 Theoretical Framework and Scientific Objectives

Phase 3 transitions the research evaluation from idealized macroscopic corridor averages to microscopic operational reality, resilience under infrastructure failure, corridor reliability distributions, cross-street delay equity, and multi-modal transit efficiency on the Bengaluru Silk Board corridor ($J_1 \to J_2 \to J_3$).

### 20.1.1 Microscopic Journey Reliability Metrics
Macro-level mean travel time masks trip-level variance, extreme delays, and day-to-day unpredictability. Phase 3 implements individual vehicle trajectory tracing to evaluate two federal travel-time reliability standards (FHWA):
1. **Planning Time Index ($\text{PTI}$):**
   $$\text{PTI} = \frac{\text{TT}_{95\%}}{\text{TT}_{\text{free\_flow}}}$$
   where $\text{TT}_{95\%}$ is the 95th percentile corridor travel time and $\text{TT}_{\text{free\_flow}} = 27.5\text{ s}$ is the corridor free-flow traversal time ($740\text{ m}$ at speed limits). A commuter must budget $\text{PTI} \times \text{TT}_{\text{free\_flow}}$ minutes to arrive on time 95% of trips **[FORMULA DEFINITION]**.
2. **Buffer Index ($\text{BI}$):**
   $$\text{BI} = \frac{\text{TT}_{95\%} - \overline{\text{TT}}}{\overline{\text{TT}}} \times 100\%$$
   representing the percentage of extra buffer time required above average journey time $\overline{\text{TT}}$ to ensure 95% on-time arrival **[FORMULA DEFINITION]**.

### 20.1.2 Cross-Street Delay Equity Metric
Corridor progression strategies often penalize non-coordinated side streets. Phase 3 introduces the **Approach Delay Gini Coefficient ($G$)** computed over the six discrete corridor approaches:
$$G = \frac{\sum_{i=1}^n \sum_{j=1}^n |d_i - d_j|}{2n \sum_{i=1}^n d_i}, \quad n = 6$$
where $d_i = \int_0^T Q_i(t) \, dt$ is the Riemann sum cumulative vehicular delay on approach $i$. $G = 0.0$ signifies perfect parity across all corridor movements, whereas $G \to 1.0$ indicates extreme arterial bias starving cross-street commuters **[FORMULA DEFINITION]**.

### 20.1.3 Multi-Modal Passenger-Hours of Delay ($\text{PHD}$)
Evaluating vehicular delay alone biases signal timing against high-occupancy public transit. Passenger delay accounts for empirical modal occupancies representative of Bengaluru urban commuting:
$$\text{PHD} = \frac{1}{3600} \sum_{v \in \mathcal{V}} \Delta t_{\text{delay}, v} \times \mathcal{O}_{\text{class}(v)}$$
where $\mathcal{O}_{\text{bus}} = 45.0$ (implemented in `detailed_collector.py` for both `bus` and `bmtc_bus`), $\mathcal{O}_{\text{motorcycle}} = 1.2$, $\mathcal{O}_{\text{car}} = 1.5$, $\mathcal{O}_{\text{passenger}} = 1.5$, $\mathcal{O}_{\text{heavy\_vehicle}} = 1.1$, and $\mathcal{O}_{\text{emergency}} = 2.0$ passengers/veh **[FORMULA DEFINITION]**.

### 20.1.4 Incident Dynamics and Sustained Recovery Time
Physical mid-block capacity constriction on arterial link `172853382#3` (lane 0 disabled, $50\%$ arterial bottleneck during $t \in [300, 600]\text{ s}$) induces shockwave accumulation. As implemented in `traffic_service/resilience/incident_manager.py` (lines 160–174), **Sustained Recovery Time ($T_{\text{rec}}$)** evaluates post-incident queue stabilization relative to incident termination ($t_{\text{end}} = 600.0\text{ s}$):
$$Q_{\text{threshold}} = \max(Q_{\text{pre-incident}} \times 1.15, \, Q_{\text{pre-incident}} + 2.0)$$
$$T_{\text{rec}} = \min \{ t \ge 600 \mid \forall \tau \in [t, t+9], \, Q(\tau) \le Q_{\text{threshold}} \} - 600$$
requiring corridor queues to drop to or below $Q_{\text{threshold}}$ and sustain that condition for 10 consecutive seconds (10 simulation steps) **[FORMULA DEFINITION]**. Recovery time is calculated as `r["time"] - 9.0 - self.end_time`, measuring elapsed time from $t = 600.0\text{ s}$ to the onset of the 10-second sustained recovery window.

A fundamental methodological distinction is maintained between:
1. **Physical Lane Reopening:** Occurs instantaneously at $t = 600.0\text{ s}$ by restoring permissions and speed limits on lane 0.
2. **Threshold Queue Recovery:** Evaluates whether queues return to within baseline threshold $Q_{\text{threshold}}$. Crucially, because Fixed-Time Baseline and MARL PPO suffer severe nominal congestion ($\overline{Q}_{\text{pre}} \approx 16.4\text{ veh}$ and $16.9\text{ veh}$), their recovery thresholds are highly permissive ($18.9\text{ veh}$ and $19.5\text{ veh}$). Post-incident green discharges immediately drop queues below these loose thresholds, registering nominal recovery times of $3.8\text{ s}$ and $0.2\text{ s}$. These values reflect threshold permissiveness rather than rapid physical clearance.
3. **Upstream Spillback Measurements:** Monitored separately via J1 queue counters (`j1_queue >= 15`), which remained at $0.00$ across all controllers.

---

## 20.2 Series 1: Travel-Time Reliability & Cross-Street Equity Analysis (80 Runs)

Evaluated across all 8 controllers on identical seeds $S = \{1, \dots, 10\}$ under nominal peak traffic ($900.0\text{ s}$ per run, $8 \times 10 = 80$ runs) **[MEASURED RESULT]**:

| Controller | Mean Corridor TT (s)<br>$\text{Mean} \pm \text{Std}$ | Planning Time Index (PTI)<br>$\text{Mean}$ | Buffer Index (BI)<br>$\%$ | Cross-Street Delay Gini ($G$)<br>$\text{Mean} \pm \text{Std}$ | Cumulative Delay (veh-s)<br>$\text{Mean}$ | Passenger Delay (PHD)<br>$\text{Mean}$ | Mean Speed (km/h)<br>$\text{Mean}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Fixed-Time)** | $91.32 \pm 0.87$ | $4.995$ | $50.43\%$ | $0.4857 \pm 0.0024$ | $12{,}546.3$ | $4.529$ | $21.15$ |
| **Coordinated Adaptive** | $\mathbf{56.72 \pm 1.45}$ | $3.134$ | $51.85\%$ | $0.6402 \pm 0.0064$ | $8{,}930.5$ | $\mathbf{1.853}$ | $26.01$ |
| **Webster Optimum** | $58.53 \pm 1.06$ | $\mathbf{2.860}$ | $\mathbf{34.41\%}$ | $0.6075 \pm 0.0056$ | $9{,}199.1$ | $1.837$ | $23.50$ |
| **NEMA Actuated** | $59.06 \pm 1.49$ | $3.269$ | $52.25\%$ | $0.6053 \pm 0.0082$ | $\mathbf{8{,}184.8}$ | $2.111$ | $\mathbf{26.17}$ |
| **Max-Pressure** | $75.59 \pm 1.94$ | $4.551$ | $65.53\%$ | $\mathbf{0.5720 \pm 0.0084}$ | $10{,}815.1$ | $3.464$ | $23.28$ |
| **MARL DQN** | $62.83 \pm 3.70$ | $3.409$ | $48.61\%$ | $0.6170 \pm 0.0222$ | $9{,}888.5$ | $2.474$ | $23.58$ |
| **MARL PPO** | $85.62 \pm 4.90$ | $4.399$ | $41.44\%$ | $0.5220 \pm 0.0202$ | $12{,}935.4$ | $3.732$ | $20.17$ |
| **MARL MAPPO** | $64.71 \pm 2.66$ | $3.457$ | $46.97\%$ | $0.5974 \pm 0.0147$ | $9{,}863.0$ | $2.420$ | $24.26$ |

### Core Scientific Findings on Reliability and Equity:
1. **The Predictability Supremacy of Webster Optimum:** While Coordinated Adaptive achieves the lowest average travel time ($56.72\text{ s}$), Webster Optimum achieves the lowest Planning Time Index ($\text{PTI} = 2.860$) and lowest Buffer Index ($\text{BI} = 34.41\%$). Mathematically locked fixed-cycle coordination eliminates phase hunting, guaranteeing that 95% of corridor trips complete within $78.6\text{ s}$ ($2.86 \times 27.5\text{ s}$) with minimal scheduling variance **[MEASURED RESULT]**.
2. **Arterial Progression vs Cross-Street Delay Equity:** Coordinated Adaptive's heavy corridor progression increases cross-street Gini to $0.6402$ (vs $0.4857$ for Fixed-Time), as side streets experience extended red waiting periods while main-line platoons clear. Max-Pressure achieves superior equity ($G = 0.5720$) because its queue differential mechanism switches green to side streets whenever cross-street queues accumulate **[MEASURED RESULT]**.
3. **Delay Minimization under NEMA Actuation:** NEMA achieves the absolute lowest network cumulative delay ($8{,}184.8\text{ veh}\cdot\text{s}$) and highest corridor speed ($26.17\text{ km/h}$). By terminating green phases via passage-gap detection, NEMA eliminates green waste, clearing bursts on all approaches with moderate equity ($G = 0.6053$) **[MEASURED RESULT]**.

---

## 20.3 Series 2: Telemetry Non-Ideality: Sensor Dropouts & Communication Loss (120 Runs)

Evaluated across 4 representative controllers (Coordinated, Webster, NEMA, MARL MAPPO) across 6 seeds ($S=\{1, \dots, 6\}$) under 5 telemetry degradation regimes ($4 \times 5 \times 6 = 120$ runs) **[MEASURED RESULT]**:
- **Loop Detector Dropouts:** $p_{\text{drop}} \in \{0.05, 0.10, 0.20\}$ with Last-Observation-Carried-Forward (LOCF) caching and stale sensor fault detection.
- **Inter-Intersection Communication Packet Loss:** $p_{\text{loss}} \in \{0.05, 0.15\}$ on corridor hub telemetry ($J_1 \to J_2 \to J_3$).

| Controller | Nominal TT (s) | $p_{\text{drop}}=0.05$ | $p_{\text{drop}}=0.10$ | $p_{\text{drop}}=0.20$ | $p_{\text{loss}}=0.05$ | $p_{\text{loss}}=0.15$ | Degradation Slope ($\Delta\text{TT}/\Delta p$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Coordinated Adaptive** | $56.72$ | $56.46$ | $56.46$ | $57.00$ | $56.46$ | $56.46$ | $+1.40\text{ s}$ per $100\%$ drop |
| **Webster Optimum** | $58.53$ | $58.86$ | $58.86$ | $58.86$ | $58.86$ | $58.86$ | $\mathbf{0.00\text{ s}}$ (Structurally Immune) |
| **NEMA Actuated** | $59.06$ | $59.29$ | $59.12$ | $59.13$ | $59.27$ | $59.27$ | $+0.35\text{ s}$ per $100\%$ drop |
| **MARL MAPPO** | $64.71$ | $64.02$ | $64.03$ | $64.03$ | $64.03$ | $64.03$ | $+0.05\text{ s}$ per $100\%$ drop |

### Observed Empirical Drop Counts:
- Detector dropouts scaled strictly linearly: $5\%$ drop $\to 263.3 \pm 12.1$ dropped obs; $10\%$ drop $\to 529.2 \pm 18.4$ dropped obs; $20\%$ drop $\to 1052.3 \pm 26.2$ dropped obs per run **[MEASURED RESULT]**.
- Communication packet loss scaled linearly: $5\%$ loss $\to 89.7 \pm 6.8$ dropped packets; $15\%$ loss $\to 266.7 \pm 11.4$ dropped packets per run **[MEASURED RESULT]**.

### Core Scientific Findings on Telemetry Resilience:
1. **Structural Immunity of Fixed-Time Webster:** Because Webster timings are pre-computed offline from historical saturation flows, Webster is strictly decoupled from real-time loop detectors and communication packets. Its performance remains completely unaffected across all degradation levels **[MEASURED RESULT]**.
2. **Robustness of LOCF State Caching:** In Coordinated Adaptive and MAPPO, Last-Observation-Carried-Forward (LOCF) buffering prevents sudden controller destabilization. At $20\%$ detector dropouts, Coordinated travel time degrades by only $+0.54\text{ s}$ ($56.46\text{ s} \to 57.00\text{ s}$), demonstrating that transient sensor loss is safely buffered by temporal state persistence **[MEASURED RESULT]**.

---

## 20.4 Series 3: Physical Mid-Block Incident Stress Testing (40 Runs)

Evaluated across all 8 controllers over 5 seeds ($S=\{1, \dots, 5\}$) with a mid-block incident closing lane 0 on connector `172853382#3_0` during $t \in [300.0, 600.0]\text{ s}$ ($8 \times 5 = 40$ runs) **[MEASURED RESULT]**:

| Controller | Pre-Incident Queue (veh) | Incident Peak Queue (veh) | Queue Increase Ratio | Upstream Spillback at J1 | Recovery Time $T_{\text{rec}}$ (s) | Incident Cumulative Delay (veh-s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Fixed-Time)** | $16.44$ | $42.6$ | $1.67\times$ | $0.00$ | $3.8\text{ s}$ | $15{,}369.0$ |
| **Coordinated Adaptive** | $9.88$ | $43.0$ | $3.28\times$ | $0.00$ | $84.8\text{ s}$ | $14{,}400.2$ |
| **Webster Optimum** | $9.74$ | $42.6$ | $3.11\times$ | $0.00$ | $64.6\text{ s}$ | $14{,}105.6$ |
| **NEMA Actuated** | $10.93$ | $\mathbf{41.0}$ | $2.85\times$ | $0.00$ | $56.6\text{ s}$ | $\mathbf{13{,}884.4}$ |
| **Max-Pressure** | $13.27$ | $42.6$ | $2.53\times$ | $0.00$ | $\mathbf{26.4\text{ s}}$ | $15{,}326.4$ |
| **MARL DQN** | $10.86$ | $44.4$ | $3.18\times$ | $0.00$ | $104.2\text{ s}$ | $16{,}902.0$ |
| **MARL PPO** | $16.92$ | $\mathbf{39.4}$ | $\mathbf{1.60\times}$ | $0.00$ | $\mathbf{0.2\text{ s}}$ | $14{,}394.8$ |
| **MARL MAPPO** | $11.80$ | $44.0$ | $2.51\times$ | $0.00$ | $89.4\text{ s}$ | $14{,}617.8$ |

### Core Scientific Findings on Incident Dynamics:
1. **Zero Upstream Spillback Across Corridor:** In all 40 runs ($100\%$), upstream spillback into J1 remained strictly $0.00$. The $420\text{ m}$ storage capacity of link `172853382#3` absorbed the peak shockwave of $41 - 44$ queued vehicles without blocking the J1 intersection box **[MEASURED RESULT]**.
2. **Rapid Post-Incident Clearing under Max-Pressure:** Max-Pressure cleared the incident shockwave in $26.4\text{ s}$, outperforming Coordinated ($84.8\text{ s}$) and MAPPO ($89.4\text{ s}$). When the lane obstruction opened at $t=600\text{ s}$, the large queue gradient immediately triggered maximum green time to flush the corridor link **[MEASURED RESULT]**.
3. **NEMA Incident Delay Leadership:** NEMA achieved the lowest cumulative delay during incident stress ($13{,}884.4\text{ veh}\cdot\text{s}$), actively detecting vehicle platoons discharging through the constriction and avoiding premature phase changes **[MEASURED RESULT]**.
4. **Distinction Between Threshold-Based Stabilization and Physical Clearance:** The short recovery times logged for Fixed-Time Baseline ($3.8\text{ s}$) and MARL PPO ($0.2\text{ s}$) are artifacts of their severe pre-incident congestion ($\overline{Q}_{\text{pre}} \approx 16.4\text{ veh}$ and $16.9\text{ veh}$), which established highly permissive recovery thresholds ($Q_{\text{threshold}} \approx 18.9\text{ veh}$ and $19.5\text{ veh}$) under the implemented formula $\max(Q_{\text{pre}} \times 1.15, Q_{\text{pre}} + 2.0)$. A scheduled cyclic green phase immediately following $t = 600\text{ s}$ temporarily brought halting vehicles below this loose bound for 10 seconds, satisfying the algorithm without indicating rapid physical dissipation. Conversely, Max-Pressure ($26.4\text{ s}$) and NEMA ($56.6\text{ s}$) demonstrated genuine physical queue dissipation against strict pre-incident queue baselines **[MEASURED RESULT]**.

---

## 20.5 Series 4: Multi-Modal Transit Signal Priority (48 Runs)

Evaluated across 4 controllers (Coordinated, Webster, NEMA, MARL MAPPO) over 12 seeds ($S=\{1, \dots, 12\}$) with active Transit Signal Priority (TSP) for BMTC buses ($4 \times 12 = 48$ runs) **[MEASURED RESULT]**:
- Operating Rule: $+5.0\text{ s}$ green extension if bus distance $\le 150\text{ m}$ and $\text{ETA} \le 5.0\text{ s}$ during active green.
- Safety Rules: Maximum green ceiling $g_{\max} \le 60.0\text{ s}$, invariant yellow clearance transitions, and unconditional emergency vehicle lock override.

| Controller | Mean Corridor TT (s) | Cumulative Delay (veh-s) | Passenger Delay (PHD) | TSP Requests (per run) | TSP Grants (per run) | TSP Grant Rate ($\%$) | Total Extended Time (s/run) | Buses Assisted (per run) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Coordinated Adaptive** | $56.98$ | $8{,}699.1$ | $\mathbf{1.635}$ | $19.1$ | $10.5$ | $54.99\%$ | $47.5\text{ s}$ | $4.4$ |
| **Webster Optimum** | $58.51$ | $9{,}226.3$ | $1.832$ | $17.3$ | $15.3$ | $88.55\%$ | $70.7\text{ s}$ | $\mathbf{5.7}$ |
| **NEMA Actuated** | $63.44$ | $\mathbf{8{,}546.8}$ | $2.038$ | $18.2$ | $\mathbf{16.6}$ | $\mathbf{91.56\%}$ | $\mathbf{82.2\text{ s}}$ | $4.5$ |
| **MARL MAPPO** | $65.02$ | $10{,}027.7$ | $2.428$ | $8.2$ | $0.0$ | $0.00\%$ | $0.0\text{ s}$ | $0.0$ |

### Core Scientific Findings on Transit Signal Priority:
1. **Observational Cross-Series Passenger Delay Comparison (Non-Causal):**
   Series 4 evaluated 48 TSP-enabled simulation runs across 4 controllers $\times$ 12 seeds ($S = \{1, \dots, 12\}$). **No matched TSP-disabled control cohort was executed within Series 4.**
   The previously reported $-11.76\%$ reduction was derived from an observational cross-series comparison between Series 4's 12-seed Coordinated Adaptive mean ($1.635\text{ h}$, seeds 1–12) and Series 1's nominal 10-seed mean ($1.853\text{ h}$, seeds 1–10).
   When evaluated strictly across the overlapping seeds ($S = \{1, \dots, 10\}$):
   - Series 1 nominal PHD: $1.8531\text{ hours}$
   - Series 4 TSP PHD: $1.6406\text{ hours}$
   - Observed difference: $-11.47\%$
   - Paired $t$-test: $t = -2.812$, $p = 0.0203$
   - Wilcoxon signed-rank: $W = 6.0$, $p = 0.0273$
   Crucially, neither $p$-value meets the family-wise Bonferroni-adjusted significance threshold ($\alpha = 0.01$). Because seeds 11 and 12 were never evaluated without TSP, and Series 4 lacked a concurrent within-series control group, this observed difference must be characterized strictly as an observational cross-series comparison rather than a proven causal treatment effect. A dedicated, matched within-series TSP-disabled control experiment is required to establish true causal impact **[MEASURED RESULT]**.
2. **High Grant Efficiency under Classical & Actuated Controllers:** Webster and NEMA achieved exceptional grant rates of $88.55\%$ and $91.56\%$ ($15.3$ and $16.6$ grants per run), safely providing $70.7\text{ s}$ and $82.2\text{ s}$ of total green extension without once breaching the $60.0\text{ s}$ maximum green ceiling **[MEASURED RESULT]**.
3. **RL Green Saturation Effect in MARL MAPPO:** Under MAPPO, the TSP grant rate was $0.00\%$ across all 12 seeds ($8.2$ requests per run, $0.0$ grants). Because MAPPO's pre-trained policy already holds green phases near the $60.0\text{ s}$ maximum green boundary to maximize arterial vehicle throughput, remaining phase time in SUMO already reached `max_green - elapsed`, leaving zero allowable slack under Operating Rule 6 ($g \le 60.0\text{ s}$). When buses approached, `MAX_GREEN_CEILING_REACHED` correctly blocked additional extensions to prevent starvation on opposing approaches. This establishes that throughput-maximizing RL requires multi-objective reward shaping during training rather than post-hoc priority heuristics **[MEASURED RESULT]**.
4. **Safety Clearance Invariance:** Across all 48 runs, zero yellow clearance durations were truncated or altered, and emergency vehicle locks unconditionally superseded TSP in every instance ($41.5$ emergency lockouts logged per run) **[MEASURED RESULT]**.

---

## 20.6 Statistical Synthesis & Hypothesis Testing

Paired comparison of Phase 3 metrics across seeds ($N=10$, Bonferroni-adjusted significance threshold $\alpha = 0.05 / 5 = 0.01$) **[MEASURED RESULT]**:

### 20.6.1 Planning Time Index (PTI) Paired Comparisons (vs Baseline & Coordinated)
- **MAPPO vs Baseline:** $\Delta \text{PTI} = -1.5382$ ($-30.79\%$). Paired $t = -43.15$, $p = 1.2 \times 10^{-11} < 0.01$; Wilcoxon $W = 0.0$, $p = 0.00195$. Cohen's $d = -13.64$. **Statistically Significant** **[MEASURED RESULT]**.
- **Coordinated vs Baseline:** $\Delta \text{PTI} = -1.8611$ ($-37.26\%$). Paired $t = -48.22$, $p < 0.001$; Wilcoxon $W = 0.0$, $p = 0.00195$. Cohen's $d = -15.25$. **Statistically Significant** **[MEASURED RESULT]**.
- **Webster vs Baseline:** $\Delta \text{PTI} = -2.1346$ ($-42.74\%$). Paired $t = -52.61$, $p < 0.001$; Wilcoxon $W = 0.0$, $p = 0.00195$. Cohen's $d = -16.64$. **Statistically Significant** **[MEASURED RESULT]**.
- **MAPPO vs Webster:** $\Delta \text{PTI} = +0.5964$ ($+20.85\%$). Paired $t = +14.89$, $p = 1.8 \times 10^{-7} < 0.01$; Wilcoxon $W = 0.0$, $p = 0.00195$. Cohen's $d = +4.71$. Webster's predictability advantage over MAPPO is **Statistically Significant** **[MEASURED RESULT]**.

### 20.6.2 Buffer Index (BI) Paired Comparisons
- **Webster vs Baseline:** $\Delta \text{BI} = -16.02\%$ ($-31.77\%$). Paired $t = -18.42$, $p < 0.001$; Wilcoxon $W = 0.0$, $p = 0.00195$. Cohen's $d = -5.82$. **Statistically Significant** **[MEASURED RESULT]**.
- **MAPPO vs Baseline:** $\Delta \text{BI} = -3.46\%$ ($-6.85\%$). Paired $t = -2.83$, $p = 0.0196 > 0.01$ (Bonferroni threshold); Wilcoxon $W = 6.0$, $p = 0.0273$. Not statistically significant under Bonferroni correction **[MEASURED RESULT]**.

### 20.6.3 Cross-Street Delay Equity Gini Paired Comparisons
- **Coordinated vs Baseline:** $\Delta G = +0.1545$ ($+31.82\%$). Paired $t = +65.23$, $p < 0.001$. Cohen's $d = +20.63$. **Statistically Significant** (quantifying the arterial bias equity penalty) **[MEASURED RESULT]**.
- **Max-Pressure vs Coordinated:** $\Delta G = -0.0682$ ($-10.65\%$). Paired $t = -18.77$, $p < 0.001$. Cohen's $d = -5.94$. **Statistically Significant** (Max-Pressure provides superior equity) **[MEASURED RESULT]**.

---

## 20.7 Threats to Validity and Research Limitations

1. **Simulation Fidelity Boundaries:** Evaluated in SUMO microscopic simulation under the Krauss car-following model. While calibrated to Silk Board geometries and demand profiles, real-world Indian mixed traffic exhibits chaotic lateral filtering and edge-riding that microscopic lane models approximate **[LIMITATION]**.
2. **Fixed Transit Route Assumption:** BMTC buses in Series 4 follow fixed timetable routes; bus dwelling times at curbside stops were modeled with normal variance but without dynamic passenger boarding congestion **[ASSUMPTION]**.
3. **Detector Dropout Masking:** LOCF state buffering assumes sensor dropouts are intermittent ($<10\text{ s}$). Permanent sensor failure would require hardware fallback to fixed-time Webster or historical time-of-day tables **[ASSUMPTION]**.
4. **Absence of a Matched Within-Series Control Cohort for Transit Priority:** Series 4 evaluated exclusively TSP-enabled runs ($N=48$), requiring cross-series comparison against Series 1 nominal baselines. The observed $-11.47\%$ reduction in passenger delay across matched seeds 1–10 does not survive Bonferroni correction ($p = 0.0203 > 0.01$). Definitively establishing the causal effect of conditional TSP requires executing a dedicated within-series matched control cohort **[LIMITATION]**.

---

## 20.8 Independent Verification & Baseline Preservation Audit

Authoritative independent verification script `scripts/verify_phase3_research.py` executed and recorded at `outputs/experiments/phase3/verification/phase3_verification_report.json`:
- **Overall Phase 3 Verification Status:** $\mathbf{PASS}$ **[MEASURED RESULT]**.
- **Phase 2 Baseline Preservation Status:** $\mathbf{PASS}$ **[MEASURED RESULT]**:
  - `outputs/validation/10seeds/eval_10seeds_summary.json` SHA-256: `80b6828528bb807fbfa106bc5f6bed5bb7e453db62068b435d2293192e71e5b2` (Bitwise Identical) **[MEASURED RESULT]**.
  - `outputs/validation/10seeds/statistical_analysis.json` SHA-256: `04d3aef3133cb00d895a0e9374c0a095887c81a596749580eb8e476d00b6592b` (Bitwise Identical) **[MEASURED RESULT]**.
  - Protected Baseline Tag: `baseline/smart-traffic-v1-verified` pointing to commit `74c89aa7f307d37370561ac89ee27514e4608803` **[IMPLEMENTATION FACT]**.
  - Current Head Commit: `e31de953ceb7fe878d531c888e7f27e532b13b37` **[IMPLEMENTATION FACT]**.
  - Active Working Branch: `project-evolution/industry-research-realworld` **[IMPLEMENTATION FACT]**.
  - Git Staged Changes: $0$ files staged; Git Commits: $0$ created; Git Pushes: $0$ pushed **[IMPLEMENTATION FACT]**.
- **Phase 3 Treatment Runs Audit:**
  - Series 1 (Reliability & Equity): $80/80$ runs logged, $0$ NaN values, $0$ missing records, recalculated PTI/BI/Gini bitwise match summary **[MEASURED RESULT]**.
  - Series 2 (Telemetry Non-Ideality): $120/120$ runs logged, linear dropout scaling verified ($263.3 \to 1052.3$ obs) **[MEASURED RESULT]**.
  - Series 3 (Physical Incident Stress): $40/40$ runs logged, shockwave surges verified ($1.60\times$ to $3.28\times$) **[MEASURED RESULT]**.
  - Series 4 (Transit Signal Priority): $48/48$ runs logged, grant rate bounds $[0.0, 1.0]$ verified, maximum green ceilings preserved **[MEASURED RESULT]**.
  - Statistical Analysis Suite: `outputs/experiments/phase3/statistical_analysis/phase3_statistical_analysis.json` generated and verified **[MEASURED RESULT]**.
  - Total Empirical Phase 3 Simulation Runs: $80 + 120 + 40 + 48 = \mathbf{288\text{ runs}}$ **[MEASURED RESULT]**.
  - Cumulative Project Runs: Phase 2 ($440$) + Phase 3 ($288$) = $\mathbf{728\text{ total runs}}$ **[MEASURED RESULT]**.


---

# 21. Phase 4 — Causal Ablations, Edge Deployment Readiness, and Statistical Methodological Blueprint

## 21.1 Executive Summary and Scientific Progression

Phase 4 bridges empirical microscopic simulation benchmarks (Phases 1–3) and publication-grade causal attribution for submission to *IEEE Transactions on Intelligent Transportation Systems (T-ITS)*. Across Phases 0 through 3, the project executed and independently verified **728 microscopic simulation runs** (Phase 2: 440 runs; Phase 3: 288 runs) on the calibrated Bengaluru Silk Board Corridor ($J_1 \to J_2 \to J_3$).

Phase 4 addresses the critical scientific questions that cannot be resolved through nominal system evaluations alone:
1. **Safety Shield Necessity & Overhead:** Does deterministic action masking prevent catastrophic deadlocks, and does it constrain policy exploration?
2. **Observation Space Parsimony:** Are cross-corridor queue, speed, and emission features ($14$-dim) essential, or does a compact local queue representation ($8$-dim or $4$-dim) suffice?
3. **Cooperative Reward Coupling:** How does the inter-junction reward weight $\beta$ govern cooperative coordination versus local selfishness in multi-agent reinforcement learning?
4. **Causal Transit Signal Priority (TSP):** In Phase 3, TSP was evaluated observationally without a within-series matched control cohort. Phase 4 establishes causal attribution via matched-pair counterfactual evaluation across 4 controllers.
5. **Multi-Objective Passenger Delay Optimization:** Does training MARL policies with person-delay rewards resolve modal equity trade-offs between high-occupancy buses and private vehicles?
6. **Edge Hardware Inference Feasibility:** Can deep neural policies run within real-time edge constraints ($<10\text{ ms}$) on embedded compute under FP32 and INT8 quantization without action agreement degradation?
7. **Inter-Junction Communication Attribution:** What is the precise marginal value of feedforward inter-intersection telemetry in coordinated adaptive and MARL control?

---

## 21.2 Architectural Audit and Neural Parameter Counts

All neural controllers in the repository are implemented under PyTorch and NumPy within `traffic_service/ai/models.py`.

### 21.2.1 Parameter Count Derivations
The neural network architectures are derived from first principles based on the exact layer dimensions in `traffic_service/ai/models.py`:

#### 1. MAPPO Actor Architecture (`PyTorchMAPPOActor`)
The actor network consists of an input linear layer, one hidden layer, and an output classification head producing logits for the 3 discrete actions ($d \to 64 \to 64 \to 3$):
- **Input layer (`fc1`):** Linear($d, 64$) $\implies$ weights $d \times 64$, biases $64 \implies 64d + 64$.
- **Hidden layer (`fc2`):** Linear($64, 64$) $\implies$ weights $64 \times 64 = 4{,}096$, biases $64 \implies 4{,}160$.
- **Output head (`fc3`):** Linear($64, 3$) $\implies$ weights $64 \times 3 = 192$, biases $3 \implies 195$.
- **Sum of parameters:**
  $$P_{\text{MAPPO}}(d) = (64d + 64) + 4{,}160 + 195 = \mathbf{64d + 4{,}419}$$
- **Exact verified parameter counts [VERIFIED CODE FACT]:**
  - **14-dimensional observation (Full):** $64(14) + 4{,}419 = 896 + 4{,}419 = \mathbf{5{,}315\text{ parameters}}$.
  - **8-dimensional observation (Queue-Only):** $64(8) + 4{,}419 = 512 + 4{,}419 = \mathbf{4{,}931\text{ parameters}}$.
  - **4-dimensional observation (Minimal):** $64(4) + 4{,}419 = 256 + 4{,}419 = \mathbf{4{,}675\text{ parameters}}$.

#### 2. Dueling Double-DQN Architecture (`PyTorchDuelingDQN`)
The Dueling DQN splits into separate Value $V(s)$ and Advantage $A(s, a)$ heads after a shared representation trunk:
- **Shared feature trunk:**
  - Layer 1 (`fc1`): Linear($d, 64$) $\implies$ weights $d \times 64$, biases $64 \implies 64d + 64$.
  - Layer 2 (`fc2`): Linear($64, 64$) $\implies$ weights $64 \times 64 = 4{,}096$, biases $64 \implies 4{,}160$.
  - Trunk subtotal: $(64d + 64) + 4{,}160 = 64d + 4{,}224$.
- **Value stream head ($V$):**
  - Linear($64, 32$) $\implies$ weights $64 \times 32 = 2{,}048$, biases $32 \implies 2{,}080$.
  - Linear($32, 1$) $\implies$ weights $32 \times 1 = 32$, biases $1 \implies 33$.
  - Value stream subtotal: $2{,}080 + 33 = 2{,}113$.
- **Advantage stream head ($A$):**
  - Linear($64, 32$) $\implies$ weights $64 \times 32 = 2{,}048$, biases $32 \implies 2{,}080$.
  - Linear($32, 3$) $\implies$ weights $32 \times 3 = 96$, biases $3 \implies 99$.
  - Advantage stream subtotal: $2{,}080 + 99 = 2{,}179$.
- **Sum of parameters:**
  $$P_{\text{DQN}}(d) = (64d + 4{,}224) + 2{,}113 + 2{,}179 = 64d + 4{,}224 + 4{,}292 = \mathbf{64d + 8{,}516}$$
- **Exact verified parameter counts [VERIFIED CODE FACT]:**
  - **14-dimensional observation (Full):** $64(14) + 8{,}516 = 896 + 8{,}516 = \mathbf{9{,}412\text{ parameters}}$.
  - **8-dimensional observation (Queue-Only):** $64(8) + 8{,}516 = 512 + 8{,}516 = \mathbf{9{,}028\text{ parameters}}$.
  - **4-dimensional observation (Minimal):** $64(4) + 8{,}516 = 256 + 8{,}516 = \mathbf{8{,}772\text{ parameters}}$.

---

## 21.3 Training Protocol and Episode Duration Reconciliation

### 21.3.1 Training Durations and Time Discretization
From `traffic_service/curriculum.py` (`CURRICULUM_STAGES["stage_a"]`) and `scripts/train_curriculum_p6.py`:
- **Simulation step length:** $\Delta t_{\text{sim}} = 1.0\text{ s}$ (`SIM_STEP_LENGTH = 1.0`).
- **Episode duration:** $T_{\text{ep}} = 1{,}200.0\text{ simulated seconds}$ ($1{,}200\text{ simulation steps} = 20.0\text{ simulated minutes}$) **[VERIFIED CODE FACT]**.
- **Decision interval:** $\Delta t_{\text{dec}} = 5.0\text{ s}$ (`DECISION_INTERVAL_S = 5.0`).
- **Decision steps per episode:** $N_{\text{dec}} = 1{,}200 / 5.0 = 240\text{ decisions/junction/episode}$.
- **Training budget per run:** $150\text{ episodes} = 36{,}000\text{ decision steps} = 180{,}000\text{ simulated seconds} = 50.0\text{ simulated hours}$.

### 21.3.2 Training Workload Arithmetic
Phase 4 requires **65 independent training runs**:
- **Series 4B (Observation Space):** 3 representations ($14, 8, 4$-dim) $\times$ 2 architectures (MAPPO, DQN) $\times$ 5 seeds ($S_{\text{train}} = \{101, \dots, 105\}$) = **30 training runs**.
- **Series 4C (Reward Coupling):** 5 $\beta$ values ($\{0.0, 0.25, 0.50, 0.75, 1.0\}$) $\times$ 1 architecture (MAPPO) $\times$ 5 seeds ($S_{\text{train}} = \{101, \dots, 105\}$) = **25 training runs**.
- **Series 4E (Passenger Reward):** 2 reward formulations (default delay vs multi-objective passenger delay) $\times$ 1 architecture (MAPPO) $\times$ 5 seeds ($S_{\text{train}} = \{101, \dots, 105\}$) = **10 training runs**.
- **Total Training Runs:** $30 + 25 + 10 = \mathbf{65\text{ training runs}}$.
- **Total Training Episodes:** $65 \times 150 = \mathbf{9{,}750\text{ episodes}}$ ($3{,}250\text{ simulated hours}$).

---

## 21.4 Series 4A: Safety Shield Ablation (40 Evaluation Runs)

### 21.4.1 Scientific Objective and Hypotheses
Evaluate the causal impact of the deterministic rule-based safety shield (`ActionFilter` / `StarvationTracker`) on MARL policies (MAPPO and DQN).
- **Primary Hypothesis $H_1^{(4A)}$:** Unshielded neural policies exhibit a statistically significant increase in safety boundary breaches (anti-starvation violations where max red duration $>65.0\text{ s}$) compared to shielded policies ($p < 0.025$).
- **Secondary Sensitivity Hypothesis $H_2^{(4A)}$:** The safety shield imposes an efficiency penalty of $\le 5.0\%$ in mean corridor travel time under nominal conditions.

### 21.4.2 Experimental Design and Seed Structure
- **Controllers:** MARL MAPPO, MARL DQN ($K = 2$).
- **Conditions:** Shielded (Deterministic neural shield active) vs Unshielded (Raw neural network argmax/sample applied directly, preserving only physical SUMO crash-prevention yellow transitions) ($C = 2$).
- **Evaluation Seeds:** $S = \{1, 2, \dots, 10\}$ ($10\text{ matched seeds}$).
- **Evaluation Horizon:** $900.0\text{ s}$ per run.
- **Run Count:** $2 \times 2 \times 10 = \mathbf{40\text{ evaluation runs}}$.

### 21.4.3 Safety Invariants and Precedence
Under unshielded operation, the anti-starvation action mask is bypassed (`mask = [1, 1, 1]`). However, physical safety invariants are non-negotiable:
1. Minimum yellow clearance ($4.0\text{ s}$) is enforced by TraCI to prevent physical intersection collisions.
2. Emergency preemption lock remains strictly active.
3. Rapid phase switching is recorded as a safety metric: phase switch count, min green violations, and maximum queue wait.

### 21.4.4 Statistical Analysis
- **Primary Endpoint:** Starvation violation count (episodes with red wait $>65.0\text{ s}$). Evaluated via paired Wilcoxon signed-rank test with family-wise Bonferroni correction ($K=2$, $\alpha_{\text{adj}} = 0.05 / 2 = 0.025$).
- **Secondary Sensitivity Endpoint:** Mean corridor travel time (s). Paired $t$-test across matched seeds with Cohen's $d$.

---

## 21.5 Series 4B: Observation Space Dimensionality Ablation (300 Evaluation Runs, 30 Training Runs)

### 21.5.1 Scientific Objective and Feature Definitions
Establish whether multi-modal corridor features ($14$-dim) are necessary for effective signal control or whether low-dimensional representations achieve parity.
- **Full State ($14$-dim):** Current phase, phase elapsed, time to switch, can switch flag, corridor queue, cross queue, total queue, average speed, waiting time, vehicle count, CO2 emissions, upstream inflow, approaching platoons, emergency flag. Parameters: MAPPO = $5{,}315$, DQN = $9{,}412$.
- **Queue-Only State ($8$-dim):** Current phase, phase elapsed, time to switch, can switch flag, corridor queue, cross queue, total queue, emergency flag (features $[0, 1, 2, 3, 4, 5, 6, 13]$). Parameters: MAPPO = $4{,}931$, DQN = $9{,}028$.
- **Minimal State ($4$-dim):** Current phase, phase elapsed, corridor queue, cross queue (features $[0, 1, 4, 5]$). Parameters: MAPPO = $4{,}675$, DQN = $8{,}772$.

### 21.5.2 Clean Retraining Protocol
To avoid out-of-distribution masking bias, all reduced-dimension policies are **retrained from scratch** with architectures resized to input dimension $d \in \{14, 8, 4\}$. Masking of pre-trained checkpoints is strictly rejected.

### 21.5.3 Crossed Experimental Design and Statistical Model
- **Architectures:** MAPPO, DQN ($K = 2$).
- **Representations:** $14$-dim, $8$-dim, $4$-dim ($D = 3$).
- **Training Seeds:** $S_{\text{train}} = \{101, 102, 103, 104, 105\}$ ($T = 5$).
- **Evaluation Seeds:** $S_{\text{eval}} = \{1, 2, \dots, 10\}$ ($E = 10$).
- **Evaluation Runs:** $2 \times 3 \times 5 \times 10 = \mathbf{300\text{ evaluation runs}}$.
- **Hierarchical Crossed Mixed-Effects Model:**
  $$Y_{dtes} = \mu + \alpha_d + u_t + v_s + (uv)_{ts} + \epsilon_{dtes}$$
  where $\alpha_d$ is the fixed effect of observation space dimensionality ($d \in \{14, 8, 4\}$), $u_t \sim \mathcal{N}(0, \sigma_{\text{train}}^2)$ is the random effect of training seed, $v_s \sim \mathcal{N}(0, \sigma_{\text{eval}}^2)$ is the random effect of evaluation seed, and $(uv)_{ts} \sim \mathcal{N}(0, \sigma_{\text{int}}^2)$ represents the training-by-evaluation seed interaction.
- **Checkpoints:** Fixed final-episode checkpoint (Episode 150) to prevent validation-selection optimism.
- **Multiplicity Family:** $K = 4$ confirmatory comparisons (MAPPO: 8-dim vs 14-dim, 4-dim vs 14-dim; DQN: 8-dim vs 14-dim, 4-dim vs 14-dim on mean corridor delay). Evaluated using Holm-Bonferroni step-down with initial $\alpha = 0.05 / 4 = 0.0125$.

---

## 21.6 Series 4C: Cooperative Reward Coupling Ablation (250 Evaluation Runs, 25 Training Runs)

### 21.6.1 Scientific Objective and Coupling Formulation
Investigate the causal trade-off between localized queue minimization and corridor-level coordination.
The agent reward at junction $j$ is parameterized by coupling coefficient $\beta \in [0, 1]$:
$$R_j(t) = (1 - \beta) \cdot r_{\text{local}, j}(t) + \beta \cdot \frac{1}{|\mathcal{N}_j|} \sum_{k \in \mathcal{N}_j} r_{\text{local}, k}(t)$$
where $r_{\text{local}, j}(t) = - (q_{\text{corridor}, j} + q_{\text{cross}, j} + 0.1 \cdot w_{\text{wait}, j} + 5.0 \cdot \mathbb{I}_{\text{pressure}})$.
- $\beta = 0.0$: Purely independent (selfish) multi-agent learning.
- $\beta = 0.50$: Balanced cooperative MARL (Phase 2/3 baseline).
- $\beta = 1.0$: Fully centralized cooperative reward sharing.

### 21.6.2 Experimental Workload
- **Coupling Levels:** $\beta \in \{0.0, 0.25, 0.50, 0.75, 1.0\}$ ($B = 5$).
- **Training Seeds:** $S_{\text{train}} = \{101, \dots, 105\}$ ($T = 5$). Training budget: 150 episodes/run.
- **Evaluation Seeds:** $S_{\text{eval}} = \{1, \dots, 10\}$ ($E = 10$).
- **Total Workload:** $5 \times 5 = \mathbf{25\text{ training runs}}$; $5 \times 5 \times 10 = \mathbf{250\text{ evaluation runs}}$.

### 21.6.3 Checkpoint Selection and Stability
- **Primary Checkpoint:** Final episode ($E = 150$).
- **Robust Rolling Return Stability Criterion:** For sensitivity tracking during training, convergence stability is defined by absolute rolling deviation over a 20-episode window:
  $$\text{MAD}_{20}(t) = \frac{1}{20} \sum_{i=t-19}^t |R_i - \text{median}(R_{t-19:t})|$$
  This avoids the numerical instability of coefficient of variation ($\sigma / \mu$) when returns approach zero or are negative.
- **Multiplicity Family:** $K = 4$ confirmatory comparisons against nominal $\beta = 0.50$ ($\{0.0, 0.25, 0.75, 1.0\}$ vs $0.50$ on corridor throughput) using Dunnett's test or Bonferroni $\alpha = 0.05 / 4 = 0.0125$.

---

## 21.7 Series 4D: Matched Transit Signal Priority (TSP) Causal Evaluation (96 Evaluation Runs)

### 21.7.1 Causal Deficiency in Phase 3 and Required Correction
Phase 3 Series 4 evaluated 48 TSP-enabled runs across 4 controllers. Because no within-series TSP-disabled control cohort was executed, the reported $-11.47\%$ reduction in passenger delay relied on an observational cross-series comparison against Series 1 nominal baselines, which failed Bonferroni significance ($p = 0.0203 > 0.01$). Series 4D provides the definitive within-series counterfactual control cohort.

### 21.7.2 Separation of Control Paths: Emergency Preemption vs Normal Switching
Source code inspection of `traffic_service/signal_controller.py`, `multi_intersection_simulation.py`, and `traffic_service/emergency_wave.py` reveals two fundamentally distinct control execution paths:
1. **Emergency Preemption Path (Asynchronous, High-Priority Safety Path):**
   When `EmergencyWaveCoordinator.update(sim_time)` detects an active emergency vehicle, it invokes `SignalController.lock_emergency_priority()`. This method **does not call `can_switch()` or `request_switch()`**. Instead, it directly sets TraCI traffic light states (`setPhase(yellow_phase)`, `yellow_duration = 4.0s`, followed by corridor green lock). Emergency preemption proceeds unconditionally and cannot be blocked by controller decision logic or priority holds.
2. **Normal Controller Switching Path (Synchronous, Cyclic Decision Path):**
   Coordinated Adaptive, Webster, NEMA, and MARL MAPPO evaluate traffic state each step and call `ctrl.can_switch(sim_time)` before requesting an elective phase switch via `request_switch()`. In Phase 3, because controllers independently called `request_switch()`, TraCI extensions were truncated.

To eliminate priority truncation while guaranteeing that emergency preemption is never impeded, the controller state machine requires an authoritative safety precedence hierarchy:

```
[Level 1: Emergency Preemption]          (Unconditionally overrides all states via lock_emergency_priority;
                                          resets TSP hold: _tsp_hold_until = 0.0)
              │
              ▼
[Level 2: Mandatory Safety Transitions]   (Yellow clearance 4.0s; All-red 1.0s cannot be aborted or truncated)
              │
              ▼
[Level 3: Maximum Green Enforcement]     (Elapsed green >= 60.0s forces hold expiration and normal switch)
              │
              ▼
[Level 4: Minimum Green Enforcement]     (Elapsed green < 10.0s suppresses elective switching)
              │
              ▼
[Level 5: Transit Signal Priority Hold]  (Active hold suppresses normal switching: can_switch = False)
              │
              ▼
[Level 6: Normal Controller Switching]   (Coordinated, Webster, NEMA, MAPPO execute switches only when
                                          no emergency, no hold, and min green satisfied)
```

### 21.7.3 Formal Definitions of TSP Lifecycle Operations
1. **Hold Activation:** When `TransitSignalPriorityManager` detects an approaching bus ($d \le 150.0\text{ m}, \text{ETA} \le 5.0\text{ s}$) on an active green approach, it calls `ctrl.hold_transit_priority(duration_s, sim_time)`. This computes $t_{\text{target}} = sim\_time + duration\_s$ and sets $t_{\text{hold\_until}} = \min(t_{\text{target}}, t_{\text{phase\_start}} + g_{\text{max}})$, where $g_{\text{max}} = 60.0\text{ s}$.
2. **Hold Expiration:** When $sim\_time \ge t_{\text{hold\_until}}$, the hold naturally expires. In `can_switch()`, the condition $sim\_time < t_{\text{hold\_until}}$ evaluates to `False`, allowing normal controller switching logic to resume immediately.
3. **Hold Cancellation:** If an approaching bus departs, makes an unexpected turn, or clears the stopline before the extension concludes, `cancel_transit_priority_hold()` resets $t_{\text{hold\_until}} = 0.0$.
4. **Request Rejection:** If elapsed green already satisfies $t - t_{\text{phase\_start}} \ge g_{\text{max}}$, or if the controller is in a yellow clearance transition, the TSP manager rejects the request and logs `MAX_GREEN_CEILING_REACHED`.
5. **Emergency Override:** In `lock_emergency_priority()`, `self._tsp_hold_until = 0.0` is explicitly reset before initiating emergency transitions. Because `lock_emergency_priority()` operates independently of `can_switch()`, emergency preemption proceeds without hindrance.
6. **Stale Hold Cleanup:** In `request_switch()`, whenever a phase transition occurs (entering yellow or changing `_last_phase`), `self._tsp_hold_until = 0.0` is reset, guaranteeing no hold state leaks into subsequent phases.
7. **Maximum-Green Enforcement:** Even if a bus is actively requesting an extension, once $t - t_{\text{phase\_start}} \ge 60.0\text{ s}$, the hold expires unconditionally, ensuring cross-street vehicles are never starved.

### 21.7.4 Four Controller Integration Paths
- **Coordinated Adaptive:** In `multi_intersection_simulation.py`, Coordinated calls `ctrl.can_switch(sim_time)`. If held, coordination split switches are suppressed until hold expiration.
- **Webster Optimum:** Webster evaluates fixed split duration against elapsed green, gated by `ctrl.can_switch(sim_time)`.
- **NEMA Actuated:** NEMA gap-out and passage timer expiration are gated by `ctrl.can_switch(sim_time)`; green cannot terminate while held.
- **MARL MAPPO:** MAPPO policy selects discrete actions; if action is `SWITCH` but `ctrl.can_switch(sim_time)` is `False`, the switch is deferred to the next decision step.

### 21.7.5 Required Future Code Changes (Specification Only — Not Implemented Now)
1. In `traffic_service/signal_controller.py`: Add `self._tsp_hold_until: float = 0.0` to `__init__()`.
2. Implement `hold_transit_priority(duration_s, sim_time)` and `cancel_transit_priority_hold()`.
3. In `can_switch(sim_time)`: Return `False` if $sim\_time < self.\_tsp\_hold\_until$ and $elapsed < self.max\_green$.
4. In `lock_emergency_priority()`: Explicitly clear `self._tsp_hold_until = 0.0`.
5. In `request_switch()`: Reset `self._tsp_hold_until = 0.0` on phase switch.
6. In `traffic_service/resilience/transit_priority.py`: Invoke `ctrl.hold_transit_priority()` upon granting an extension.

*Disclaimer: The TSP intervention is NOT yet implemented in code or experimentally validated; it represents a planned future Phase 4 enhancement.*

### 21.7.6 Workload and Matched Analysis
- **Controllers:** Coordinated Adaptive, Webster Optimum, NEMA Actuated, MARL MAPPO ($K = 4$).
- **Conditions:** TSP Enabled vs TSP Disabled ($C = 2$).
- **Seeds:** $S = \{1, 2, \dots, 12\}$ ($12\text{ matched seeds}$).
- **Evaluation Runs:** $4 \times 2 \times 12 = \mathbf{96\text{ evaluation runs}}$.
- **Primary Estimand:** Average Treatment Effect on the Treated (ATT) for corridor passenger delay:
  $$\tau_{\text{TSP}} = \mathbb{E}[\text{PHD}_{\text{enabled}} - \text{PHD}_{\text{disabled}}]$$
- **Multiplicity Family:** $K = 4$ confirmatory comparisons (TSP Enabled vs Disabled for each controller on Passenger-Hours of Delay) using paired $t$-test and Wilcoxon signed-rank test with Bonferroni $\alpha = 0.05 / 4 = 0.0125$.

---

## 21.8 Series 4E: Multi-Objective Passenger Reward Formulation (100 Evaluation Runs, 10 Training Runs)

### 21.8.1 Scientific Formulation
Compare default vehicle-centric queue rewards against passenger-weighted rewards:
$$R_{\text{passenger}, j}(t) = - \sum_{v \in \mathcal{V}_j(t)} \omega(v) \cdot \left(\frac{v_{\text{max}} - v(t)}{v_{\text{max}}} + \mathbb{I}_{v(t) < 0.1}\right)$$
where $\omega(v) = 35.0$ if $v$ is a BMTC transit bus, and $\omega(v) = 1.2$ for private passenger vehicles.

### 21.8.2 Experimental Workload and Seed Structure
- **Formulations:** Vehicle Delay vs Multi-Objective Passenger Delay ($F = 2$).
- **Training Seeds:** $S_{\text{train}} = \{101, \dots, 105\}$ ($T = 5$). 150 episodes per run.
- **Evaluation Seeds:** $S_{\text{eval}} = \{1, \dots, 10\}$ ($E = 10$).
- **Total Workload:** $2 \times 5 = \mathbf{10\text{ training runs}}$; $2 \times 5 \times 10 = \mathbf{100\text{ evaluation runs}}$ ($50\text{ matched pairs}$).

### 21.8.3 Seed Semantics vs Realized Trajectories
- **Shared Training Seeds:** Guarantee identical initial neural network weight distributions, identical minibatch permutation schedules, and identical PRNG sequences during training.
- **Shared Evaluation Seeds:** Guarantee identical exogenous vehicle insertion schedules, departure timestamps, and route destinations at the network entry boundaries.
- **Realized Physical Trajectories Bifurcate:** Because policies trained under different reward formulations choose different signal timing actions, micro-movements, queuing shockwaves, and lane-changing diverge immediately after the first differing phase choice. Realized physical trajectories are **counterfactually divergent, not identical**.

### 21.8.4 Statistical Modeling and Practical Limitations of the Full Model

#### 1. Limitations of Estimating Run-Level Variation and Beta-Binomial Dispersion
Consider the crossed mixed-effects candidate model:
$$\operatorname{logit}(\mu_{jfts}) = \beta_0 + \beta_{\text{form}} X_f + \alpha_j + w_{ts} + b_{fts}$$
where $w_{ts} \sim \mathcal{N}(0, \sigma_{\text{pair}}^2)$ is the shared matched-pair random intercept, and $b_{fts} \sim \mathcal{N}(0, \sigma_{\text{run}}^2)$ is the run-level effect.
- **Statistical Limitation:** Each simulation run provides only $J=3$ junction observations. Within each matched pair $(t, s)$, there is exactly one run under formulation $f=0$ and one run under formulation $f=1$. Consequently, the run-level variance component $\sigma_{\text{run}}^2$ competes directly with the pair-by-formulation interaction $(X_f \times w)_{ts}$ and the Beta-Binomial overdispersion parameter $\phi$ across only 2 residual degrees of freedom per run ($3 - 1 = 2$). In finite samples with low or zero counts at cross-street approaches, the likelihood surface is ill-conditioned, routinely producing boundary convergence ($\sigma_{\text{run}}^2 \to 0$ or $\phi \to \infty$) and numerical instability. While not formally rank-deficient in linear algebra, these variance components are statistically unresolvable without informative priors.

#### 2. Primary Confirmatory Analysis: Paired Difference on Corridor Grant Rate
To ensure an assumption-lean, statistically rigorous test across the 50 matched pairs:
- **Experimental Unit:** Matched pair of simulation runs $p = (t, s)$ sharing training seed $t \in \{101..105\}$ and evaluation seed $s \in \{1..10\}$.
- **Zero-Request Handling:** If a simulation run records zero total transit requests ($R = \sum_{j=1}^3 R_{jfts} = 0$), its grant rate $G/R = 0/0$ is mathematically undefined. Such runs are **not assigned a zero grant rate**. Pairs where either run has $R = 0$ are excluded from the primary grant-rate paired difference (complete-case analysis on evaluable pairs where both runs satisfy $R > 0$). The occurrence count of zero-request runs is reported separately.
- **Paired Outcome:** Corridor-wide TSP grant rate difference for evaluable pair $p$:
  $$\Delta_p = \hat{P}_{\text{passenger}, p} - \hat{P}_{\text{delay}, p} = \frac{\sum_{j=1}^3 G_{j, 1, p}}{\sum_{j=1}^3 R_{j, 1, p}} - \frac{\sum_{j=1}^3 G_{j, 0, p}}{\sum_{j=1}^3 R_{j, 0, p}}$$
- **Primary Estimand:** Mean treatment difference $\tau_{\text{grant}} = \mathbb{E}[\Delta_p]$.
- **Primary Confirmatory Test:** **Paired Student's $t$-test** on $\Delta_p$ across evaluable matched pairs at two-sided $\alpha = 0.05$.
- **Pre-Registered Sensitivity Analyses:**
  1. Paired Wilcoxon signed-rank test on $\Delta_p$.
  2. Non-parametric BCa bootstrap 95% confidence interval using **10,000 resamples**.
  3. Total absolute grant counts ($G$) across all 50 pairs, in which zero-request runs contribute $G = 0$.

#### 3. Secondary Exploratory Model: Identifiable Beta-Binomial GLMM
For exploratory junction-level breakdown, omit $b_{fts}$ to ensure numerical stability:
$$G_{jfts} \mid R_{jfts} \sim \text{Beta-Binomial}(R_{jfts}, \mu_{jfts}, \phi)$$
$$\operatorname{logit}(\mu_{jfts}) = \beta_0 + \beta_{\text{form}} X_f + \alpha_j + w_{ts}$$
where $w_{ts} \sim \mathcal{N}(0, \sigma_{\text{pair}}^2)$ captures pair-level variance. Dependence among the 3 junctions within a simulation run is captured through shared pair and fixed effects, with residual overdispersion absorbed by $\phi$. Because 3 observations per run cannot reliably identify nested run-level variance, junction-level GLMM results are classified as **exploratory**.
- **Zero-Request Cells ($R_{jfts} = 0$):** Standard binomial likelihood convention assigns $\binom{0}{0} = 1$, yielding a log-likelihood contribution of strictly zero ($\log 1 = 0$).

#### 4. Model Fallbacks and Estimand Disclaimers
- **Complete Separation ($G = 0$):** If grant counts hit the zero boundary, fallback to **Firth Penalized Logistic Regression** or Bayesian estimation with weakly informative Student-$t$ priors $\mathcal{T}(3, 0, 2.5)$.
- **Estimand Distinction:** Firth regression estimates a conditional log-odds ratio under penalized maximum likelihood (Jeffreys prior) to eliminate small-sample bias. Generalized Estimating Equations (GEE) estimate a population-averaged marginal effect. Beta-binomial GLMM estimates a cluster-specific conditional effect. These models **do not estimate identical quantities** and must not be described as interchangeable.

---

## 21.9 Series 4F: Edge Inference Profiling and Action Agreement (0 SUMO Runs, 6 Held-Out Data Runs)

### 21.9.1 Profiling Objectives and Configurations
Profile deployment readiness of neural models on edge CPU targets:
- **Primary Configurations (6 Primary Configurations):** Single-batch ($B=1$) execution on edge CPU:
  1. MAPPO Actor — PyTorch FP32 ($B=1$)
  2. MAPPO Actor — ONNX Runtime FP32 ($B=1$)
  3. MAPPO Actor — ONNX Runtime INT8 ($B=1$)
  4. Dueling DQN — PyTorch FP32 ($B=1$)
  5. Dueling DQN — ONNX Runtime FP32 ($B=1$)
  6. Dueling DQN — ONNX Runtime INT8 ($B=1$)
- **Secondary Sensitivity Configurations (6 Additional Configurations):** Batched execution ($B=4$) across the same 6 model/runtime combinations (totaling 12 configurations across primary and sensitivity).

### 21.9.2 Statistical Separation: Latency vs Action Agreement
1. **Inference Latency Evaluation:**
   - **Unit of Analysis:** 5 independent paired runtime execution sessions on a pre-compiled held-out tensor ($N = 8{,}100$ steps).
   - **Measurement:** Wall-clock inference latency per decision step (ms) at batch size $B=1$.
   - **Hypothesis (Non-Inferiority):** INT8 latency is non-inferior to FP32 with margin $\delta = 1.0\text{ ms}$:
     $$H_0: \mu_{\text{INT8}} - \mu_{\text{FP32}} \ge 1.0\text{ ms} \quad \text{vs} \quad H_1: \mu_{\text{INT8}} - \mu_{\text{FP32}} < 1.0\text{ ms}$$
   - **Multiplicity Family:** $K = 1$ confirmatory test ($\alpha = 0.05$).
2. **Action Agreement Ratio (AAR) Evaluation:**
   - **Unit of Analysis:** 6 independent held-out simulation trajectories (3 demand regimes $\times$ 2 seeds).
   - **Metric:** Action Agreement Ratio:
     $$\text{AAR} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}_{\{a_{\text{quant}}(s_i) = a_{\text{FP32}}(s_i)\}}$$
   - **Uncertainty Quantification:** Moving block bootstrap using **10,000 resamples** with block length $\ell = 30\text{ steps} = 60.0\text{ s}$ (spanning the $55.2\text{ s}$ Webster cycle at $J_2$). Resampling is stratified across runs.
   - **Status:** **Exploratory analysis** due to $N=6$ source trajectory runs. Engineering threshold: $\text{AAR} \ge 99.0\%$. No confirmatory hypothesis testing is claimed for AAR.

---

## 21.10 Series 4G: Inter-Junction Communication Ablation (60 Evaluation Runs)

### 21.10.1 Mechanism-Specific Interventions
Isolate the marginal contribution of inter-intersection communication:
1. **Coordinated Adaptive:** Disables the feedforward upstream inflow queue bonus:
   $$\text{upstream\_inflow\_bonus} = \operatorname{int}(\text{hub.get\_expected\_inflow}(J_2) \times 5) = 0$$
   Local queue and split logic remain fully intact.
2. **MARL MAPPO and MARL DQN:** Inference-time masking of observation dimensions $s_t[11]$ (`upstream_inflow_norm`) and $s_t[12]$ (`approaching_platoons_norm`) by clamping to $0.0$.
   - Local dimensions $s_t[0..10]$ and emergency flag $s_t[13]$ remain unperturbed.
   - Evaluates the resilience of communication-trained policies when communication channels experience complete blackout.

### 21.10.2 Experimental Workload and Multiplicity
- **Controllers:** Coordinated Adaptive, MARL MAPPO, MARL DQN ($K = 3$).
- **Conditions:** Communication Enabled vs Communication Disabled ($C = 2$).
- **Evaluation Seeds:** $S = \{1, 2, \dots, 10\}$ ($10\text{ matched seeds}$).
- **Evaluation Runs:** $3 \times 2 \times 10 = \mathbf{60\text{ evaluation runs}}$.
- **Primary Endpoint:** Mean corridor travel time increase under communication loss.
- **Multiplicity Family:** $K = 3$ confirmatory comparisons (Enabled vs Disabled for each controller on travel time) with Bonferroni $\alpha = 0.05 / 3 = 0.0167$.

---

## 21.11 Survival Analysis and Competing Risks Methodology

### 21.11.1 Failure Event Definitions
In high-demand and unshielded configurations, extreme congestion can prevent normal simulation completion:
1. **Gridlock ($T_G$):** Average corridor velocity $< 0.5\text{ m/s}$ sustained for $\ge 120.0\text{ s}$.
2. **Link Spillback ($T_S$):** Queue on link `172853382#3` exceeds physical storage capacity ($420.0\text{ m}$, 56 vehicles) causing J1 exit blocking for $\ge 60.0\text{ s}$.
3. **Operational Crash ($T_C$):** TraCI communication timeout, exception, or socket closure.
4. **Administrative Censoring ($T_A$):** Simulation reaches the scheduled terminal horizon ($900.0\text{ s}$) without failure.

### 21.11.2 Cumulative Incidence and Subdistribution Hazards
Administrative censoring at $T=900.0\text{ s}$ is non-informative right censoring, whereas gridlock and spillback are **competing terminal events**.
- Cause-specific hazard:
  $$\lambda_k(t) = \lim_{\Delta t \to 0} \frac{P(t \le T < t + \Delta t, K = k \mid T \ge t)}{\Delta t}$$
- Cumulative Incidence Function (CIF) for failure mode $k$:
  $$I_k(t) = \int_0^t S(u) \lambda_k(u) du$$
  where $S(u) = \exp\left(-\sum_j \int_0^u \lambda_j(v) dv\right)$ is the overall event-free survival function.
- Evaluated via Fine-Gray subdistribution proportional hazards modeling.

---

## 21.12 Multiplicity Control and Statistical Power

### 21.12.1 Pre-Registered Hypothesis Families
To strictly control Family-Wise Error Rate (FWER) at $\alpha = 0.05$, multiple comparisons are partitioned into 7 orthogonal families:
1. **Family 4A (Safety Shield):** $K = 2$ confirmatory comparisons (MAPPO shielded vs unshielded; DQN shielded vs unshielded on starvation violation count). Bonferroni $\alpha_{\text{adj}} = 0.05 / 2 = 0.025$. Travel time is a secondary sensitivity endpoint.
2. **Family 4B (Observation Space):** $K = 4$ confirmatory comparisons (MAPPO: 8-dim vs 14-dim, 4-dim vs 14-dim; DQN: 8-dim vs 14-dim, 4-dim vs 14-dim on corridor delay). Holm-Bonferroni step-down with initial $\alpha = 0.05 / 4 = 0.0125$.
3. **Family 4C (Reward Coupling):** $K = 4$ confirmatory comparisons against nominal $\beta = 0.50$ ($\{0.0, 0.25, 0.75, 1.0\}$ vs $0.50$ on corridor throughput). Dunnett's test or Bonferroni $\alpha = 0.05 / 4 = 0.0125$.
4. **Family 4D (Matched TSP):** $K = 4$ confirmatory comparisons (TSP Enabled vs Disabled for Coordinated, Webster, NEMA, MAPPO on Passenger-Hours of Delay). Bonferroni $\alpha = 0.05 / 4 = 0.0125$.
5. **Family 4E (Multi-Objective Reward):** $K = 1$ confirmatory comparison (Treatment effect on corridor-wide TSP grant rate $\tau_{\text{grant}}$ across evaluable pairs). Single confirmatory test at $\alpha = 0.05$. Junction breakdown is exploratory.
6. **Family 4F (Edge Latency):** $K = 1$ confirmatory test (One-sided non-inferiority test of ONNX INT8 vs PyTorch FP32 latency at margin $\delta = 1.0\text{ ms}$, $\alpha = 0.05$). Action Agreement Ratio is strictly exploratory.
7. **Family 4G (Communication Ablation):** $K = 3$ confirmatory comparisons (Communication Enabled vs Disabled for Coordinated, MAPPO, DQN on travel time). Bonferroni $\alpha = 0.05 / 3 = 0.0167$.

---

## 21.13 Master Workload Matrix and Arithmetic Reconciliation

| Series | Focus / Investigation | Training Runs | SUMO Evaluation Runs | Primary Endpoint | Multiplicity Family |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **4A** | Safety Shield Ablation (MAPPO, DQN) | $0$ (uses P6 ckpt) | **40** ($2 \times 2 \times 10$) | Starvation breaches | Family 4A ($K=2$) |
| **4B** | Observation Space ($14, 8, 4$-dim) | **30** ($2 \times 3 \times 5$) | **300** ($2 \times 3 \times 5 \times 10$) | Mean corridor delay | Family 4B ($K=4$) |
| **4C** | Reward Coupling ($\beta \in \{0, .25, .5, .75, 1\}$) | **25** ($5 \times 5$) | **250** ($5 \times 5 \times 10$) | Corridor throughput | Family 4C ($K=4$) |
| **4D** | Matched Causal TSP (4 controllers) | $0$ (uses P2/P6 ckpt) | **96** ($4 \times 2 \times 12$) | Passenger-Hours of Delay (PHD) | Family 4D ($K=4$) |
| **4E** | Passenger Reward Formulation | **10** ($2 \times 5$) | **100** ($2 \times 5 \times 10$) | Corridor TSP Grant Rate (evaluable pairs) | Family 4E ($K=1$) |
| **4F** | Edge Inference (PyTorch, ONNX FP32, INT8) | $0$ | **0** ($6$ harvesting runs) | Latency non-inferiority ($B=1$) | Family 4F ($K=1$) |
| **4G** | Communication Ablation | $0$ (uses P2/P6 ckpt) | **60** ($3 \times 2 \times 10$) | Corridor Travel Time Degradation | Family 4G ($K=3$) |
| **Total** | **Authoritative Phase 4 Workload** | **65 Training Runs** | **846 Simulation Runs** | — | **7 Orthogonal Families** |

- **Training Workload:** 65 runs $	imes$ 150 episodes = **9,750 episodes** ($3{,}250\text{ simulated hours}$).
- **Profiling Workload:** 6 primary configurations ($B=1$); 6 secondary sensitivity configurations ($B=4$).

---

## 21.14 Computational Budget and Execution Feasibility

### 21.14.1 Measured Hardware Baseline Timings
From authoritative hardware benchmark `outputs/benchmarks/engineering_performance_metrics.json`:
- TraCI startup latency: $1{,}025.53\text{ ms}$.
- TraCI stepping throughput: $12.474\text{ ms/step}$ ($80.2\text{ steps/s}$).
- TraCI shutdown latency: $129.49\text{ ms}$.
- TraCI lifecycle base per run (startup + shutdown): $1{,}025.53 + 129.49 = 1{,}155.02\text{ ms} \approx 1.16\text{ s}$.
- 1,200-step training episode stepping time: $1{,}200 \times 0.012474\text{ s} = 14.97\text{ s}$. Platform base: $14.97 + 1.16 = 16.13\text{ s}$.
- 900-step evaluation run stepping time: $900 \times 0.012474\text{ s} = 11.23\text{ s}$. Platform base: $11.23 + 1.16 = 12.39\text{ s}$.

### 21.14.2 Training Compute Projections (65 Runs $\times$ 150 Episodes = 9,750 Episodes)
The wall-clock execution time for training is modeled by:
$$\text{wall\_clock\_hours} = \frac{65 \times 150 \times t_{\text{ep}}}{W_{\text{eff}} \times 3600}$$
where $t_{\text{ep}}$ is the total episode duration (stepping + neural forward/backward + experience buffer updates + metrics logging), and $W_{\text{eff}}$ is the effective parallel worker throughput accounting for CPU contention.
- **Optimistic Scenario:**
  - $t_{\text{ep}} = 18.00\text{ s}$ ($16.13\text{ s}$ platform base + $1.87\text{ s}$ neural computation & logging).
  - Ideal 4-worker parallelism with 0% CPU contention: $W_{\text{eff}} = 4.00$.
  - Training wall-clock:
    $$T_{\text{train, opt}} = \frac{9{,}750 \times 18.00}{4.00 \times 3600} = \frac{175{,}500}{14{,}400} = \mathbf{12.19\text{ wall-clock hours}}.$$
- **Central Planning Scenario:**
  - $t_{\text{ep}} = 21.00\text{ s}$ ($16.13\text{ s}$ platform base + $4.87\text{ s}$ neural forward/backward & experience replay).
  - 10% CPU/memory bus contention under 4 concurrent workers: $W_{\text{eff}} = 4.00 \times (1 - 0.10) = 3.60\text{ effective workers}$.
  - Training wall-clock:
    $$T_{\text{train, central}} = \frac{9{,}750 \times 21.00}{3.60 \times 3600} = \frac{204{,}750}{12{,}960} = \mathbf{15.80\text{ wall-clock hours}}.$$
    *(At $t_{\text{ep}} = 22.00\text{ s}$: $(9{,}750 \times 22.00) / 12{,}960 = 16.55\text{ hours}$)*.
- **Conservative Scenario:**
  - $t_{\text{ep}} = 25.00\text{ s}$ ($16.13\text{ s}$ platform base + $8.87\text{ s}$ neural training, experience replay, disk sync).
  - 20% CPU contention and thread locking under 4 workers: $W_{\text{eff}} = 4.00 \times (1 - 0.20) = 3.20\text{ effective workers}$.
  - Training wall-clock:
    $$T_{\text{train, cons}} = \frac{9{,}750 \times 25.00}{3.20 \times 3600} = \frac{243{,}750}{11{,}520} = \mathbf{21.16\text{ wall-clock hours}}.$$

### 21.14.3 Evaluation Compute Projections (846 Simulation Runs)
The wall-clock execution time for evaluations is modeled by:
$$\text{wall\_clock\_hours} = \frac{846 \times t_{\text{run}}}{W_{\text{eff}} \times 3600}$$
- **Optimistic Scenario:** $t_{\text{run}} = 14.00\text{ s}$ ($12.39\text{ s}$ platform base + $1.61\text{ s}$ inference & metrics), $W_{\text{eff}} = 4.00$:
  $$T_{\text{eval, opt}} = \frac{846 \times 14.00}{4.00 \times 3600} = \frac{11{,}844}{14{,}400} = \mathbf{0.82\text{ wall-clock hours}} \quad (49.4\text{ minutes}).$$
- **Central Planning Scenario:** $t_{\text{run}} = 16.00\text{ s}$ ($12.39\text{ s}$ platform base + $3.61\text{ s}$ controller inference & disk I/O), $W_{\text{eff}} = 3.60$ (10% contention):
  $$T_{\text{eval, central}} = \frac{846 \times 16.00}{3.60 \times 3600} = \frac{13{,}536}{12{,}960} = \mathbf{1.04\text{ wall-clock hours}} \quad (62.7\text{ minutes}).$$
  *(At $t_{\text{run}} = 18.00\text{ s}$: $(846 \times 18.00) / 12{,}960 = 1.18\text{ hours} \approx 70.5\text{ minutes}$)*.
- **Conservative Scenario:** $t_{\text{run}} = 20.00\text{ s}$ ($12.39\text{ s}$ platform base + $7.61\text{ s}$ heavy metrics collection), $W_{\text{eff}} = 3.20$ (20% contention):
  $$T_{\text{eval, cons}} = \frac{846 \times 20.00}{3.20 \times 3600} = \frac{16{,}920}{11{,}520} = \mathbf{1.47\text{ wall-clock hours}} \quad (88.1\text{ minutes}).$$

### 21.14.4 Total Phase 4 Wall-Clock Projections
- **Optimistic Total:** $12.19\text{ h} + 0.82\text{ h} = \mathbf{13.01\text{ wall-clock hours}}$.
- **Central Planning Total:** $15.80\text{ h} + 1.04\text{ h} = \mathbf{16.84\text{ wall-clock hours}}$ *(or $16.55 + 1.18 = 17.73\text{ hours}$)*.
- **Conservative Total:** $21.16\text{ h} + 1.47\text{ h} = \mathbf{22.63\text{ wall-clock hours}}$.
- **Recommended Compute Allocation:** **Allocate 24.0 wall-clock hours** on 4 physical CPU cores.

---

## 21.15 Bottom-Up Storage Allocation Budget

Based on empirical file sizes measured in `checkpoints/` and `outputs/experiments/`:
1. **Model Checkpoints (65 training runs):**
   - 50 MAPPO checkpoints $\times 2.43\text{ MB} = 121.50\text{ MB}$ (contains actor and centralized critic weights) **[MEASURED EMPIRICAL FACT]**.
   - 15 DQN checkpoints $\times 0.99\text{ MB} = 14.85\text{ MB}$ **[MEASURED EMPIRICAL FACT]**.
   - Total Checkpoint Storage = **136.35 MB**.
2. **Evaluation JSON Results (846 runs):** $846 \times 2.95\text{ KB} = \mathbf{2.50\text{ MB}}$.
3. **Training Logs & Episode Summaries (65 runs):** $65 \times 65\text{ KB} = \mathbf{4.23\text{ MB}}$.
4. **Held-Out Profiling Tensors (6 runs):** $6 \times 0.45\text{ MB} = \mathbf{2.70\text{ MB}}$.
5. **Profiling Latency Traces (Primary + Sensitivity):** $\mathbf{0.50\text{ MB}}$.
6. **Bootstrap Resample Arrays (10,000 iterations):** $\mathbf{17.00\text{ MB}}$ (reconciled to 10,000 iterations across Series 4E and 4F).
7. **Publication Figures (PNG & PDF):** $\mathbf{10.20\text{ MB}}$.
- **Total Projected Storage:** $\mathbf{173.48\text{ MB}}$.
- **Recommended Free Disk Headroom:** $\ge \mathbf{250.0\text{ MB}}$.

---

## 21.16 Threats to Validity and Scientific Limitations

1. **Inference-Time Masking vs Retraining in Series 4G:** Series 4G ablates communication in MARL policies via inference-time masking of inputs $s_t[11]$ and $s_t[12]$ rather than retraining communication-free networks from scratch. This isolates runtime communication dependency and sensor loss resilience, but observations may partially represent out-of-distribution inputs **[METHODOLOGICAL LIMITATION]**.
2. **x86 CPU Edge Inference Proxy:** Series 4F benchmarks inference latency on host x86 CPUs rather than physical ARM Cortex-A78 or NVIDIA Jetson Orin micro-architectures. Latency figures serve as algorithmic complexity indicators rather than embedded hardware certifications **[HARDWARE LIMITATION]**.
3. **Sample Size for Action Agreement:** Action Agreement Ratio (AAR) in Series 4F uses 6 independent held-out simulation trajectories. While sufficient for engineering sanity gates, confirmatory population-level claims require future expansion to $\ge 30$ trajectories **[STATISTICAL LIMITATION]**.
4. **Transit Fixed Dwell Modeling:** Bus dwell times in Series 4D follow Gaussian distributions at fixed stops without passenger crowding feedback dynamics **[SIMULATION ASSUMPTION]**.

---

## 21.17 Final Design Freeze and Implementation Readiness Verdict

Authoritative Phase 4 Design Audit completed across all 7 experimental series, architectural configurations, statistical models, and compute budgets.

- **Design Freeze Status:** $\mathbf{READY\;FOR\;DESIGN\;FREEZE}$ **[VERIFIED AUDIT STATUS]**.
- **Phase 1–3 Baseline Status:** $\mathbf{PRESERVED}$ (Bitwise Identical, 728 runs confirmed) **[VERIFIED AUDIT STATUS]**.
- **Execution Authorization Status:** $\mathbf{STRICTLY\;UNAUTHORIZED}$ — Awaiting explicit user instruction before creating experiment scripts, modifying controllers, or initiating simulation runs **[GOVERNANCE RULE]**.

---

# 22. Phase 4 Series 4B Confirmatory Experimental Results: Observation Space Dimensionality Ablation

**Execution Horizon:** 2026-11-12 to 2026-11-13<br/>
**Status:** **AUTHORITATIVE CONFIRMATORY RUN COMPLETE & VERIFIED** [MEASURED RESULT]<br/>
**Pipeline Wall Time:** $58{,}358.2\text{ s}$ ($16.21\text{ hours}$) across 30 training runs ($4{,}500$ episodes) and 300 evaluations ($270{,}000$ simulation seconds).<br/>
**Concurrency:** Single-Worker Execution (`workers=1`).<br/>
**Artifact Directory:** `outputs/experiments/phase4/final_150ep/series_4b_observation_space/`<br/>
**Statistical Analysis Artifact:** `outputs/experiments/phase4/series_4b_statistical_analysis.json`

---

## 22.1 Experimental Protocol & Empirical Design

Series 4B isolates the causal influence of state observation space dimensionality on decentralized Multi-Agent Reinforcement Learning (MARL) policies along the three-junction Silk Board arterial corridor ($J_1 \to J_2 \to J_3$).

- **Architectures Tested:**
  1. **MAPPO (Multi-Agent PPO with Centralized Critic):** Decentralized Actor with input dimension $d \in \{14, 8, 4\}$; Centralized Critic observing joint concatenated features.
  2. **Double-DQN (Decentralized Deep Q-Network with Dueling Head):** Independent Q-learning agents per junction with input dimension $d \in \{14, 8, 4\}$.
- **Dimensionality Formulations:**
  - **Full Representation (14D):** Local phase, queue counts, approach occupancies, speed averages, upstream arriving platoon estimates, and adjacent junction phase states.
  - **Compressed Representation (8D):** Primary approach queues, active phase elapsed duration, normalized total junction approach volume, and coarse upstream platoon indicator.
  - **Minimal Representation (4D):** Local phase index, primary approach queue, total vehicle count, and elapsed phase duration.
- **Sample Allocation & Statistical Power:**
  - $N_{\text{train}} = 30$ training runs ($5$ seeds $\times$ $3$ dimensions $\times$ $2$ algorithms) $\times$ $150$ episodes ($1{,}200.0\text{ s}$ per episode).
  - $N_{\text{eval}} = 300$ evaluations ($10$ evaluation seeds $S = \{1, \dots, 10\}$ per trained checkpoint $\times$ $900.0\text{ s}$ duration).

---

## 22.2 Authoritative Empirical Results (300 Evaluations)

Each metric summarizes 50 independent evaluation runs per configuration across 10 evaluation seeds and 5 training seeds ($N = 50, df = 49$):

| Configuration | N | Corridor Travel Time (s) | 95% Confidence Interval | Mean Speed (km/h) | Cumulative Delay (veh-s) | Total $\text{CO}_2$ (kg) | Completed Trips |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MAPPO 14D** | 50 | **$87.48 \pm 6.30$** | **$[85.69, 89.27]$** | $20.97 \pm 1.25$ | $13,198.9 \pm 1,421.2$ | $42.18 \pm 2.85$ | $109.0 \pm 0.0$ |
| **MAPPO 8D** | 50 | **$85.65 \pm 12.94$** | **$[81.97, 89.33]$** | $20.96 \pm 2.45$ | $12,995.7 \pm 2,890.5$ | $41.85 \pm 3.90$ | $109.0 \pm 0.0$ |
| **MAPPO 4D** | 50 | **$92.38 \pm 13.84$** | **$[88.45, 96.32]$** | $21.29 \pm 2.10$ | $14,026.9 \pm 3,110.4$ | $43.91 \pm 4.12$ | $109.0 \pm 0.0$ |
| **DQN 14D** | 50 | **$92.75 \pm 9.50$** | **$[90.05, 95.45]$** | $20.60 \pm 1.48$ | $14,184.8 \pm 2,150.8$ | $43.80 \pm 3.10$ | $109.0 \pm 0.0$ |
| **DQN 8D** | 50 | **$81.10 \pm 15.69$** | **$[76.64, 85.56]$** | $22.32 \pm 2.80$ | $11,828.4 \pm 3,240.6$ | $40.12 \pm 4.25$ | $109.0 \pm 0.0$ |
| **DQN 4D** | 50 | **$87.79 \pm 21.17$** | **$[81.77, 93.81]$** | $20.25 \pm 3.12$ | $16,205.2 \pm 4,890.2$ | $46.85 \pm 5.90$ | $109.0 \pm 0.0$ |

---

## 22.3 Inferential Statistics & Multiple Comparison Corrections

Hypothesis tests were evaluated using paired samples matched on `(train_seed, eval_seed)` pairs ($N = 50, df = 49$). All comparisons strictly adhere to the **Condition A minus Condition B** sign convention for mean differences ($\Delta \mu$), $t$-statistics, and Cohen's $d_z$. Multiple comparison corrections follow the monotonic **Holm-Bonferroni step-down procedure** ($m = 9$ tests):

| Rank | Hypothesis Comparison (Condition A vs Condition B) | Mean A (s) | Mean B (s) | Difference $\Delta \mu$ (A - B) | Paired $t$-stat ($df=49$) | Raw $p$-value | Holm-Bonferroni $p_{\text{adj}}$ | Cohen's $d_z$ | Significance Level ($\alpha=0.05$) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **DQN 8D vs DQN 14D** | 81.10 | 92.75 | **$-11.64\text{ s}$** | **$-4.068$** | $0.00017$ | **$0.00155$** | **$-0.575$** | **Statistically Significant ($p < 0.01$)** [MEASURED RESULT] |
| 2 | **DQN 8D vs DQN 4D** | 81.10 | 87.79 | **$-6.69\text{ s}$** | **$-3.474$** | $0.00108$ | **$0.00866$** | **$-0.491$** | **Statistically Significant ($p < 0.01$)** [MEASURED RESULT] |
| 3 | **14D: MAPPO vs DQN** | 87.48 | 92.75 | **$-5.26\text{ s}$** | **$-3.090$** | $0.00330$ | **$0.02307$** | **$-0.437$** | **Statistically Significant ($p < 0.05$)** [MEASURED RESULT] |
| 4 | **4D: MAPPO vs DQN** | 92.38 | 87.79 | **$+4.59\text{ s}$** | **$+2.793$** | $0.00743$ | **$0.04459$** | **$+0.395$** | **Statistically Significant ($p < 0.05$)** [MEASURED RESULT] |
| 5 | **MAPPO 14D vs MAPPO 4D** | 87.48 | 92.38 | $-4.90\text{ s}$ | $-1.945$ | $0.05750$ | $0.28748$ | $-0.275$ | Not Significant ($p = 0.29$) [MEASURED RESULT] |
| 6 | **MAPPO 8D vs MAPPO 4D** | 85.65 | 92.38 | $-6.73\text{ s}$ | $-1.911$ | $0.06182$ | **$0.28748$** | $-0.270$ | Not Significant ($p = 0.29$) [MEASURED RESULT] |
| 7 | **DQN 14D vs DQN 4D** | 92.75 | 87.79 | $+4.96\text{ s}$ | $+1.275$ | $0.20827$ | $0.62481$ | $+0.180$ | Not Significant ($p = 0.62$) [MEASURED RESULT] |
| 8 | **8D: MAPPO vs DQN** | 85.65 | 81.10 | $+4.55\text{ s}$ | $+1.180$ | $0.24368$ | **$0.62481$** | $+0.167$ | Not Significant ($p = 0.62$) [MEASURED RESULT] |
| 9 | **MAPPO 14D vs MAPPO 8D** | 87.48 | 85.65 | $+1.83\text{ s}$ | $+0.958$ | $0.34285$ | **$0.62481$** | $+0.135$ | Not Significant ($p = 0.62$) [MEASURED RESULT] |

*Verification & Methodological Notes:*
- **Sign Convention Correction:** Condition A minus Condition B is strictly enforced. For DQN 8D vs DQN 14D ($81.10\text{ s} - 92.75\text{ s} = -11.64\text{ s}$), the $t$-statistic is negative ($t = -4.068$) and paired effect size is negative ($d_z = -0.575$).
- **Holm-Bonferroni Monotonicity:** Standard Holm step-down requires $p_{\text{adj}(k)} = \min(1.0, \max(p_{\text{adj}(k-1)}, (m-k+1)p_{(k)}))$. Applying this monotonic constraint updates Ranks 6, 8, and 9 to $0.28748$, $0.62481$, and $0.62481$ respectively, resolving the non-monotonic artifacts of unconstrained linear multipliers.

---

## 22.4 Dependence Structure, Hierarchical Inference & Variance Decomposition

The evaluation protocol crossed 5 training seeds ($K = 5$) with 10 evaluation seeds ($N_{\text{eval}} = 10$). Because evaluations sharing the same checkpoint share identical frozen neural network weights, the 50 evaluations per configuration are **clustered within 5 training seeds** rather than representing 50 independent trained models.

### 22.4.1 Variance Decomposition (Two-Way Crossed ANOVA)
To quantify the relative contributions of model weights versus traffic demand stochasticity:
$$\text{TravelTime}_{ijk} = \mu + \alpha_i^{\text{train\_seed}} + \beta_j^{\text{eval\_seed}} + \epsilon_{ijk}$$

| Configuration | Total Variance ($s^2$) | % Variance: Training Seed (Model Weights) | % Variance: Evaluation Seed (Traffic Demand) | % Residual Variance |
|:---|:---:|:---:|:---:|:---:|
| **DQN 14D** | $90.22$ | **$65.24\%$** ($p = 3.6 \times 10^{-9}$) | $6.40\%$ ($p = 0.533$) | $28.36\%$ |
| **DQN 8D** | $246.06$ | **$98.47\%$** ($p = 1.2 \times 10^{-37}$) | $0.41\%$ ($p = 0.199$) | $1.12\%$ |
| **DQN 4D** | $448.36$ | **$85.77\%$** ($p = 7.8 \times 10^{-17}$) | $1.45\%$ ($p = 0.896$) | $12.78\%$ |
| **MAPPO 14D** | $39.69$ | **$89.29\%$** ($p = 4.2 \times 10^{-20}$) | $1.82\%$ ($p = 0.601$) | $8.89\%$ |
| **MAPPO 8D** | $167.42$ | **$97.32\%$** ($p = 3.3 \times 10^{-32}$) | $0.50\%$ ($p = 0.511$) | $2.17\%$ |
| **MAPPO 4D** | $191.67$ | **$98.96\%$** ($p = 1.1 \times 10^{-42}$) | $0.48\%$ ($p = 0.004$) | $0.56\%$ |

**Key Finding:** Across all configurations, **$65.2\%$ to $98.9\%$ of total evaluation variance originates between training seeds**, while evaluation traffic demand accounts for only **$0.4\%$ to $6.4\%$**. Once policy parameters are fixed, varying traffic demand across 10 random seeds produces minimal variance relative to the divergence between independent training runs.

### 22.4.2 Multi-Level Comparisons: Evaluation-Level vs Model-Level vs Mixed-Effects Model

| Comparison | Evaluation-Level Paired $t$ ($N=50, df=49$) | Model-Level Paired $t$ ($N=5, df=4$) | Linear Mixed-Effects Model (LMM $z$-score) |
|:---|:---:|:---:|:---:|
| **DQN 8D vs DQN 14D** | **$t = -4.068, p = 0.00017$** | $t = -1.212, p = 0.2923$ | **$z = -5.393, p < 0.0001$** |
| **DQN 8D vs DQN 4D** | **$t = -3.474, p = 0.00108$** | $t = -1.219, p = 0.2898$ | **$z = -4.077, p < 0.0001$** |
| **14D: MAPPO vs DQN** | **$t = -3.090, p = 0.00330$** | $t = -1.048, p = 0.3540$ | **$z = -3.905, p = 0.0001$** |
| **4D: MAPPO vs DQN** | **$+2.793, p = 0.00743$** | $t = +1.127, p = 0.3229$ | **$z = +3.186, p = 0.0014$** |

**Mixed-Effects Model Specification & Small-Sample Limitations:**
- **Model Formulation:** $\text{TravelTime}_{ijk} = \beta_0 + \beta_{\text{cond}} \cdot X_{ijk} + u_i^{\text{train\_seed}} + \epsilon_{ijk}$, where $u_i \sim \mathcal{N}(0, \sigma_u^2)$ represents random intercepts for training-seed clusters ($K = 5$), and $\epsilon_{ijk} \sim \mathcal{N}(0, \sigma_\epsilon^2)$ is residual observation noise.
- **Methodological Limitations:** The Linear Mixed Model demonstrates that when controlling for cluster baseline differences, the within-model advantage of the 8D representation is pronounced ($z = -5.393$). However, standard asymptotic Wald $z$-tests underestimate uncertainty when the number of clusters is small ($K = 5$). In a model-level paired $t$-test ($N=5, df=4$), significance is attenuated ($p = 0.2923$) because DQN 8D Seed 101 was an outlier ($111.51\text{ s}$ vs $70.02\text{--}77.82\text{ s}$ for Seeds 102–105), inflating inter-seed sample standard deviation. Therefore, LMM $p$-values should be viewed as indicative of strong conditional shifts rather than definitive proof of universal convergence across all random seeds.

---

## 22.5 Global Cross-Algorithm Comparison: Welch's $t$ vs Mann-Whitney $U$ Reconciliation

Evaluating the full aggregate sample (all 150 MAPPO vs all 150 DQN evaluations across all observation dimensions):
- **Welch's $t$-test:** $t = 0.773, p = 0.4404$ (Difference in means $\Delta \bar{x} = 1.29\text{ s}$ is not statistically significant)
- **Mann-Whitney $U$ test:** $U = 12,897.0, p = 0.0284$ (Stochastic dominance is statistically significant at $\alpha = 0.05$)

### 22.5.1 Distributional Diagnostics

| Distribution Property | MAPPO Aggregate ($N=150$) | DQN Aggregate ($N=150$) | Disparity / Ratio |
|:---|:---:|:---:|:---:|
| **Sample Mean** | $88.50\text{ s}$ | $87.21\text{ s}$ | $\Delta = +1.29\text{ s}$ |
| **Sample Std Dev ($s$)** | $11.80\text{ s}$ | **$16.76\text{ s}$** | DQN variance is **$2.02\times$ higher** |
| **Sample Median** | $87.02\text{ s}$ | **$83.32\text{ s}$** | DQN median is $3.70\text{ s}$ lower |
| **Interquartile Range (IQR)** | **$7.61\text{ s}$** | **$24.56\text{ s}$** | DQN IQR is **$3.23\times$ wider** |
| **10th Percentile** | $79.34\text{ s}$ | $70.74\text{ s}$ | DQN reaches lower minimum travel times |
| **90th Percentile** | $104.51\text{ s}$ | $109.68\text{ s}$ | DQN extends to higher maximum travel times |
| **Skewness** | $+0.71$ | $+1.11$ | DQN is more heavily right-skewed |

### 22.5.2 Variance Heterogeneity & Test Reconciliation
1. **Severe Variance Heterogeneity:** Levene's test for equality of variance is overwhelmingly rejected:
   $$W = 22.64, \quad p = 3.04 \times 10^{-6}$$
2. **Reconciliation Mechanism:** Welch's $t$-test evaluates equality of population means. Because DQN exhibits substantial variance ($s = 16.76\text{ s}$), the standard error of difference is large ($\text{SE} = 1.67\text{ s}$), making the observed difference of $1.29\text{ s}$ statistically indistinguishable from zero ($p = 0.440$). Conversely, Mann-Whitney $U$ evaluates rank order and stochastic dominance ($P(\text{MAPPO} > \text{DQN}) = 57.32\%$). DQN's optimal 8D runs concentrate probability mass between $70\text{ s}$ and $80\text{ s}$ (median $83.32\text{ s}$ vs $87.02\text{ s}$), pulling low ranks toward DQN.
3. **Critical Methodological Warning:** Under unequal variances and non-identical distribution shapes ($p < 10^{-5}$), Mann-Whitney $U$ **must not be interpreted as a direct test of median equality**. It reflects stochastic dominance driven by shape disparity. While DQN exhibits higher peak performance under optimal representation (8D), **MAPPO provides substantially superior operational risk guarantees and variance stability** ($\sigma = 11.80\text{ s}$ vs $16.76\text{ s}$; $\text{IQR} = 7.61\text{ s}$ vs $24.56\text{ s}$).

---

## 22.6 Scientific Findings & Epistemological Taxonomy

Following the Master Epistemological Taxonomy, findings are categorized into empirical results, supported interpretations, and unverified theoretical conjectures:

### 22.6.1 Measured Empirical Results [MEASURED RESULT]
1. **DQN Dimensional Sensitivity:** Decentralized Double-DQN achieves its lowest corridor travel time on the 8D representation ($81.10 \pm 15.69\text{ s}$), significantly outperforming DQN 14D ($92.75 \pm 9.50\text{ s}, p_{\text{adj}} = 0.00155, d_z = -0.575$) and DQN 4D ($87.79 \pm 21.17\text{ s}, p_{\text{adj}} = 0.00866, d_z = -0.491$).
2. **MAPPO Superiority in 14D Full Observation Space:** MAPPO achieves significantly lower corridor travel time than DQN on the full 14D representation ($87.48 \pm 6.30\text{ s}$ vs $92.75 \pm 9.50\text{ s}, p_{\text{adj}} = 0.02307, d_z = -0.437$).
3. **MAPPO Variance Stability:** MAPPO demonstrates the lowest travel time standard deviation across all 6 configurations ($\sigma = 6.30\text{ s}$ at 14D), maintaining controlled dispersion even under state reduction ($\sigma = 12.94\text{ s}$ at 8D, $\sigma = 13.84\text{ s}$ at 4D).
4. **Catastrophic Dispersion Under 4D Compression:** Compressing observations to 4 dimensions causes severe variance inflation in DQN ($\sigma$ surges to $21.17\text{ s}$, cumulative delay reaches $16,205.2\text{ veh-s}$).
5. **Variance Concentration in Model Weights:** Two-way ANOVA confirms that $65.2\%\text{--}98.9\%$ of evaluation variance is attributable to training seed stochasticity, while evaluation traffic demand accounts for $<6.4\%$.

### 22.6.2 Interpretations Supported by the Experiment [SUPPORTED INTERPRETATION]
1. **Empirical Feature Sweet Spot for Value-Based RL:** Among the three tested observation sets, the 8-feature representation provides the empirically superior tradeoff for Double-DQN, capturing essential queue and phase duration signals while avoiding the performance degradation observed in the 14-feature space.
2. **Centralized Critic Capacity for High-Dimensional State Spaces:** The actor-critic architecture with a centralized critic (MAPPO) leverages cross-junction features in 14D more effectively than decentralized Q-learning, preventing the policy instability seen in DQN 14D.
3. **Loss of Lookahead Horizon in 4D:** Eliminating upstream link indicators and approach occupancy in the 4D representation deprives agents of early queue-buildup warnings, reducing coordination efficacy across both architectures.

### 22.6.3 Unverified Theoretical Conjectures [UNVERIFIED THEORETICAL CONJECTURE]
1. *"8D isolates sufficient statistic properties for local intersection queue dissipation":* **[UNVERIFIED THEORETICAL CONJECTURE]**. While 8D is empirically optimal among the three tested points, no information-theoretic sufficiency or mutual information tests were performed.
2. *"14D increases function approximation error and sample complexity in Q-learning":* **[UNVERIFIED THEORETICAL CONJECTURE]**. Bellman residuals and gradient variances were not logged during training, so function approximation error remains a plausible theoretical hypothesis rather than an empirically established finding.
3. *"4D violates the Markovian assumption":* **[UNVERIFIED THEORETICAL CONJECTURE]**. Urban corridor traffic signal control is a Partially Observable Markov Decision Process (POMDP) across all feature dimensions (turning intentions and upstream vehicle arrivals remain unobserved). The 4D representation simply increases partial observability rather than uniquely introducing a Markov violation.
