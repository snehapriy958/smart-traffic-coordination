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
| **Phase 1: Engineering Foundation** | Research Paper Master Record formalization, CI/CD pipeline, Docker containerization. | **IN PROGRESS** | Branch: `project-evolution/industry-research-realworld` |
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
12. **Performance Profiling Evidence:** Automated test harness executing 231 backend pytest tests and 91 frontend vitest tests. 40 consecutive 900s simulation runs executed without memory leaks or TraCI socket disconnects.
13. **Dependency & System Versions:** Windows 11 Pro 64-bit, Eclipse SUMO 1.26.0, Python 3.13.14, PyTorch 2.8.0+cpu, NumPy 2.3.3, SciPy 1.15.2, FastAPI 0.141.1, Node.js v22.21.1, React 18.3.1, Three.js 0.187.0, Vite 5.2.11.

---
*Record formally verified and certified on:* `project-evolution/industry-research-realworld`  
*Commit anchor:* `74c89aa7f307d37370561ac89ee27514e4608803`  
*Tag anchor:* `baseline/smart-traffic-v1-verified`  
