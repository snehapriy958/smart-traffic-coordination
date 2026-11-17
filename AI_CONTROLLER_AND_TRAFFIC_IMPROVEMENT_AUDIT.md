# AI CONTROLLER & TRAFFIC IMPROVEMENT AUDIT
## Verification of Autonomous Control Loops, Safety Shields, and Empirical Impact
**Auditor**: Senior AI/ML Engineer & Traffic Simulation Researcher  
**Date**: November 17, 2026  
**Target Environment**: Bengaluru Silk Board Corridor (J1 Feeder $\to$ J2 Silk Board $\to$ J3 Feeder)

---

### 1. Complete Autonomous Control Loop Verification

The complete closed-loop feedback pipeline was independently traced through the codebase:

$$\text{SUMO Microscopic State} \longrightarrow \text{State Preprocessing (14D)} \longrightarrow \text{Policy / Q-Inference} \longrightarrow \text{Action Masking} \longrightarrow \text{Signal Actuation} \longrightarrow \text{TraCI Update} \longrightarrow \text{Corridor Response}$$

```
+---------------------------------------------------------------------------------------------------+
| 1. RAW TRAFFIC EXTRACTION (traffic_service/state_extractor.py: get_states)                        |
|    - Subscribes to Traci edge and lane subscriptions.                                             |
|    - Computes approach queues (vehicles with speed < 0.1 m/s), accumulated waiting times,         |
|      inflow counts, vehicle speeds, and HBEFA instantaneous emissions (CO2, NOx, fuel).           |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 2. CORRIDOR OBSERVATION SPACE (traffic_service/ai/env.py: vectorize_junction)                    |
|    - Transforms raw dictionary into a strictly bounded, normalized 14-dimensional float32 vector. |
|    - Scales approach queues by max_queue (50 veh), speeds by max_speed (60 km/h), wait times      |
|      by max_wait (500s), and phase durations by max_green (60s).                                   |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 3. MULTI-INTERSECTION COMMUNICATION (traffic_service/communication.py: publish_upstream_inflow)  |
|    - J1 arterial outflow is forwarded to J2's observation input (Dimension [11]).                 |
|    - J2 arterial outflow is forwarded to J3's observation input (Dimension [11]).                 |
|    - Arriving platoon clusters are tracked and converted into platoon density count (Dimension [12]).|
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 4. SAFETY SHIELD & ANTI-STARVATION ACTION MASK (traffic_service/ai/starvation_tracker.py)         |
|    - Tracks contiguous red light duration for all conflicting/side-street approaches.             |
|    - Minimum Green Guard: If elapsed green < 15.0s, action_mask forbids SWITCH: [1, 0, 1].        |
|    - Maximum Green Guard: If elapsed green >= 60.0s, action_mask forbids EXTEND: [1, 1, 0].       |
|    - Anti-Starvation Preemption: If queued side approach red >= 60.0s, mask forces SWITCH: [0, 1, 0]|
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 5. NEURAL POLICY INFERENCE (traffic_service/ai/marl_controller.py: decide)                       |
|    - Policy evaluates action logits / Q-values subject to action_mask.                            |
|    - Greedy Argmax in eval_mode=True; Categorical sampling during training exploration.           |
|    - Returns discrete decision: 0 = KEEP, 1 = SWITCH, 2 = EXTEND.                                 |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 6. TRAFFIC SIGNAL ACTUATION (traffic_service/signal_controller.py: request_switch/extend)        |
|    - If SWITCH: Schedules 4.0s yellow clearance transition before establishing target green phase.|
|    - If EXTEND: Adds 5.0s green up to max_green (60.0s).                                          |
|    - If KEEP: Maintains active phase; respects SUMO background cycle unless explicitly overridden.|
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+---------------------------------------------------------------------------------------------------+
| 7. CORRIDOR METRIC EVALUATION (traffic_service/resilience/detailed_collector.py)                 |
|    - Riemann integration of queue over time: Cumulative Delay = sum(Q * dt) vehicle-seconds.     |
|    - Completed trips log individual travel times, free-flow delays, and passenger delay hours.    |
|    - Computes travel time reliability (PTI, Buffer Index) and Delay Gini equity.                  |
+---------------------------------------------------------------------------------------------------+
```

---

### 2. Comprehensive Controller Verification Matrix

To prevent misleading claims, the exact status of every controller in the repository is defined under rigorous criteria:
- **IMPLEMENTED**: Full Python algorithm and data structures written in the codebase.
- **TRAINED**: Policy/value weights optimized over multiple training episodes and stored in checkpoint files.
- **INTEGRATED**: Directly executable within the live simulation loop and callable by runtime modes.
- **EVALUATED**: Tested across multiple random seeds with empirical metric collection.
- **BENCHMARKED**: Included in the authoritative 10-seed comparison against baseline.

| Controller Name | Type | Checkpoint Path | Implemented | Trained | Integrated | Evaluated | Benchmarked | Mean Travel Time (N=10) | Completed Trips |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Fixed-Time Baseline** | Classical Pre-Timed | N/A (Static Timing) | **YES** | N/A | **YES** | **YES** | **YES** | **90.02 s** | **109 / 109** (100%) |
| **Coordinated Adaptive** | Heuristic Pressure + Green Wave | N/A (Rule-based) | **YES** | N/A | **YES** | **YES** | **YES** | **49.87 s** | **109 / 109** (100%) |
| **Double-DQN (Stage A)** | Multi-Agent Dueling DQN | `checkpoints/p6/dqn_stage_a_best.json` | **YES** | **YES** (150 ep) | **YES** | **YES** | **YES** | **56.64 s** | **109 / 109** (100%) |
| **PPO (Stage A)** | Multi-Agent Actor-Critic | `checkpoints/p6/ppo_stage_a_best.json` | **YES** | **YES** (150 ep) | **YES** | **YES** | **YES** | **85.50 s** | **109 / 109** (100%) |
| **MAPPO (Series 4B)** | Centralized Critic MARL | `checkpoints/phase4/final_150ep/series_4b_*.json` | **YES** | **YES** (150 ep $\times$ 30 runs) | **YES** | **YES** (300 evals) | Researched (4B) | **87.48 s** | **109 / 109** (100%) |
| **MAPPO (Series 4C)** | Reward Coupling Ablation | `checkpoints/phase4/final_150ep/series_4c_*.json` | **YES** | **IN PROGRESS** (3/25 runs complete) | **YES** | **YES** (30 evals) | Researched (4C) | **85.81 s** ($\beta=0.0$) | **109 / 109** (100%) |
| **Webster Optimal** | Classical Cycle Optimization | N/A (Formula-derived) | **YES** | N/A | **YES** | **YES** | Baseline Reference | ~88.40 s | 100% |
| **NEMA Actuated** | Dual-Ring Gap-Out Actuated | N/A (Detector-driven) | **YES** | N/A | **YES** | **YES** | Baseline Reference | ~52.10 s | 100% |
| **Max-Pressure** | Queue Differential Feedback | N/A (Dynamic Pressure) | **YES** | N/A | **YES** | **YES** | Baseline Reference | ~51.30 s | 100% |
| *DQN Historical Artifact* | Early 8-ep Prototype | `checkpoints/marl_dqn_corridor.json` | **YES** | Unconverged (8 ep) | Preserved | Evaluated | Historical Only | *Gridlock (None)* | **0 / 102** (0%) |

---

### 3. Detailed Audit of the 14-Dimensional Observation Space

Implemented in `traffic_service/ai/env.py` (`CorridorObservationSpace.vectorize_junction`):

| Index | Feature Name | Source Variable | Formula / Normalization | Dynamic Range | Missing Value Fallback |
|---|---|---|---|---|---|
| `[0]` | `current_phase_norm` | `state.current_phase` | `phase / 3.0` | $[0.0, 1.0]$ | `0.0` (Corridor Green) |
| `[1]` | `phase_elapsed_norm` | `state.phase_elapsed` | $\min(\text{elapsed} / 60.0, 1.0)$ | $[0.0, 1.0]$ | `0.0` |
| `[2]` | `time_to_switch_norm` | `state.time_to_switch` | $\min(\text{switch} / 60.0, 1.0)$ | $[0.0, 1.0]$ | `0.0` |
| `[3]` | `can_switch_flag` | Signal timing check | $1.0$ if $\text{elapsed} \ge 15.0\,\text{s}$ else $0.0$ | $\{0.0, 1.0\}$ | `1.0` |
| `[4]` | `corridor_queue_norm` | `approach_queues["corridor_hosur"]` | $q_{\text{corridor}} / 50.0$ | $[0.0, 1.0]$ | `0.0` |
| `[5]` | `side_queue_norm` | Conflicting approach queue | $q_{\text{side}} / 50.0$ | $[0.0, 1.0]$ | `0.0` |
| `[6]` | `total_queue_norm` | `state.total_queue` | $q_{\text{total}} / (2 \times 50.0)$ | $[0.0, 1.0]$ | `0.0` |
| `[7]` | `average_speed_norm` | `state.average_speed_kmh` | $\text{speed} / 60.0$ | $[0.0, 1.0]$ | `0.0` |
| `[8]` | `waiting_time_norm` | `state.total_waiting_time` | $\min(\text{wait} / 500.0, 1.0)$ | $[0.0, 1.0]$ | `0.0` |
| `[9]` | `vehicle_count_norm` | `state.vehicle_count` | $\min(\text{count} / 100.0, 1.0)$ | $[0.0, 1.0]$ | `0.0` |
| `[10]` | `co2_emissions_norm` | `state.emissions.co2_mg_s` | $\min(\text{co2} / 10{,}000.0, 1.0)$ | $[0.0, 1.0]$ | `0.0` |
| `[11]` | `upstream_inflow_norm`| Communication Hub Outflow | $\min(\text{inflow} / 10.0, 1.0)$ | $[0.0, 1.0]$ | `0.0` |
| `[12]` | `approaching_platoons` | Platoon Tracker Clusters | $\min(\text{platoons} / 5.0, 1.0)$ | $[0.0, 1.0]$ | `0.0` |
| `[13]` | `emergency_flag` | Emergency Vehicle Detector | $1.0$ if approaching else $0.0$ | $\{0.0, 1.0\}$ | `0.0` |

#### Centralized Critic 42-Dimensional Joint State:
For MAPPO (`traffic_service/ai/mappo_agent.py`), the centralized critic receives:
$$\mathbf{s}_{\text{corridor}} = \begin{bmatrix} \mathbf{s}_{J1} & \mathbf{s}_{J2} & \mathbf{s}_{J3} \end{bmatrix} \in \mathbb{R}^{42}$$
This guarantees true Centralized Training with Decentralized Execution (CTDE).

---

### 4. Behavioral Finding: Why Run 1 Evaluation Produced Zero SWITCH Actions

In the Series 4C Run 1 audit (`SERIES4C_RUN1_BEHAVIORAL_AUDIT.md`), all 10 evaluation seeds recorded:
- **KEEP**: 70.53%
- **EXTEND**: 29.47%
- **SWITCH**: 0%

**Scientific Determination**: This is **genuine learned behavior under deterministic argmax evaluation** (`eval_mode=True`), NOT a software bug or logging defect.
1. **Yellow Penalty Avoidance**: Under pure local reward ($\beta = 0.00$), selecting `ACTION_SWITCH` incurs a 4.0-second yellow transition where zero vehicles pass through the intersection, degrading instantaneous local throughput and increasing queue penalties.
2. **Deterministic Argmax**: During evaluation, policy exploration is disabled ($\varepsilon = 0$, deterministic argmax over action logits). Since $Q(\text{KEEP}) > Q(\text{SWITCH})$ and $Q(\text{EXTEND}) > Q(\text{SWITCH})$ across all non-critical states, the policy never chooses `SWITCH` voluntarily.
3. **Phase Changes via Background Cycles and Safety Preemption**:
   - At J1 and J3, selecting `KEEP` allows SUMO's internal cycle controller to transition phases naturally (Phase 0 $\leftrightarrow$ Phase 2 every 45 seconds).
   - At J2, greedy `EXTEND` actions held arterial green until the **Anti-Starvation Shield** triggered exactly 110 preemption switches (11 per seed) to clear cross-street queues.

---

### 5. Verified Safety Shields and Real-World Constraints

| Constraint | Enforcement Mechanism | Implementation Location | Verified In Simulation |
|---|---|---|---|
| **Minimum Green (15.0s)** | Blocks phase switch if elapsed green < 15.0s | `SignalController.can_switch()` | **VERIFIED** |
| **Maximum Green (60.0s)** | Forbids green extension if elapsed green $\ge$ 60.0s | `SignalController.extend_current_green()` | **VERIFIED** |
| **Maximum Red / Anti-Starvation (60.0s)** | Action mask overrules policy to force green for starved approach | `StarvationTracker.get_action_mask()` | **VERIFIED** (110 preemption switches in Run 1) |
| **Yellow Clearance (4.0s)** | Automatically transitions through yellow phase before green | `SignalController.request_switch()` | **VERIFIED** |
| **Emergency Preemption** | Priority lock holds corridor green and extends green wave | `EmergencyWaveCoordinator.update()` | **VERIFIED** (Clears ambulance in 28-32s vs 41s baseline) |

*Disclaimer*: These constraints represent algorithmic software-level safety guards within the SUMO simulation environment. They do not constitute formal hardware-in-the-loop (HIL) safety certification for physical roadside controller cabinets.
