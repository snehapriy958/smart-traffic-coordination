# Phase 2 — Step 2A: Webster Optimum Signal Timing Controller Implementation Report

**Document ID:** `PHASE_2_STEP_2A_WEBSTER_CONTROLLER`  
**Date:** 2026-11-09  
**Status:** Implemented & Verified  
**Branch:** `project-evolution/industry-research-realworld`  
**Protected Baseline Tag:** `baseline/smart-traffic-v1-verified` (Commit: `74c89aa7f307d37370561ac89ee27514e4608803`)  
**Scope:** Classical Baseline 1 (Webster 1958 Optimum Signal Timing)  

---

## 1. Executive Summary

As part of Phase 2 (Research Foundation & Classical Baselines), we implemented a mathematically verified, constraint-respecting, and independently testable **Webster Optimum Signal Timing Controller** for the Bengaluru Silk Board arterial corridor ($J_1 \rightarrow J_2 \rightarrow J_3$).

This controller establishes an authoritative classical baseline representing delay-minimizing fixed-time signal timing derived from critical movement flow ratios and saturation rates according to Webster's method (Webster 1958; Indian Roads Congress IRC:93-1985).

All implementations strictly observe the mandatory preservation rules:
- Zero modifications to existing controllers (Fixed-Time Baseline, Coordinated Adaptive, Dueling Double-DQN, Independent PPO).
- Zero modifications to trained checkpoints (`checkpoints/` and `checkpoints/p6/`).
- Zero modifications to authoritative 10-seed benchmark outputs (`outputs/validation/10seeds/`).
- Zero Git commits, pushes, or branch switches.

---

## 2. Mathematical Derivation & Formulation

### 2.1 Critical Flow Ratios
For each signalized phase $i \in \{0, 2\}$ at intersection $j$:
$$y_i = \frac{q_i}{s_i}$$
where:
- $q_i$: Critical arrival flow rate in vehicles per hour ($\text{veh/h}$).
- $s_i$: Saturation flow rate of the critical lane group in vehicles per hour ($\text{veh/h}$).
- $y_i$: Phase flow ratio.

The intersection degree of saturation (sum of critical flow ratios) is:
$$Y = \sum_{i} y_i$$

### 2.2 Theoretical Optimum Cycle Length ($C_0$)
Webster's fundamental formula minimizes total intersection vehicle delay:
$$C_0 = \frac{1.5 L + 5}{1 - Y}$$
where:
- $L$: Total intersection lost time per cycle in seconds ($\text{s}$):
  $$L = \sum_{i} l_i$$
  with $l_i = t_{sl, i} + t_{cl, i}$ (startup lost time $t_{sl} \approx 2.0\text{ s}$ and clearance lost time $t_{cl} \approx 2.0\text{ s}$ per phase per IRC:93-1985). In 2-phase control where yellow duration $y_i$ serves as clearance, $L = \sum_i y_i$ without double-counting yellow time ($8.0\text{ s}$ for J1/J3, $12.0\text{ s}$ for J2).

### 2.3 Boundary Constraints and Guardrails
1. **Oversaturation Protection ($Y \ge 1.0$ or $Y \ge 0.95$):**
   When $Y \ge 1.0$, the denominator $1 - Y \le 0$, causing $C_0 \to \infty$ or negative values. The controller detects oversaturation (`is_saturated = True`), avoids division-by-zero, and clamps cycle length to the configured upper bound $C_{\max} = 120.0\text{ s}$.
2. **Under-saturation / Minimum Cycle Bound ($C_{\min} = 45.0\text{ s}$):**
   When demand is low ($C_0 < C_{\min}$), cycle length is clamped to $C_{\min} = 45.0\text{ s}$ to guarantee adequate phase clearance and pedestrian/driver expectations.
3. **Zero Demand Handling ($Y = 0$):**
   If arrival flows on all phases are zero, $C_0$ defaults to $C_{\min}$, and green time is split equally among phases.
4. **Input Validation:**
   Non-negative flow constraint ($q_i \ge 0$), strictly positive saturation flow ($s_i > 0$), and finite number validation are enforced. Inputs with $\text{NaN}$, $\pm\infty$, or negative values raise explicit `ValueError` exceptions.
5. **Infeasible Cycle Bounds Rejection:**
   The mathematical feasibility requirement for cycle bounds is:
   $$C_{\max} \ge C_{\text{feasible, min}} = L + \sum_{i} g_{\min, i}$$
   If $C_{\max} < L + n \cdot g_{\min}$, it is physically and mathematically impossible to assign minimum green to all phases while keeping the cycle length $\le C_{\max}$. The controller validates this invariant and raises an explicit `ValueError` immediately upon initialization rather than silently violating cycle or green limits.

### 2.4 Effective Green Time & Split Allocation
Total effective green time available in the cycle:
$$G = C_{\text{actual}} - L$$

Proportional allocation by flow ratio:
$$g_{i,\text{raw}} = \frac{y_i}{Y} G$$

To enforce civil engineering safety standards (`SignalController` invariants: $g_{\min} = 15.0\text{ s}$, $g_{\max} = 60.0\text{ s}$):
- If all raw splits satisfy $g_{\min} \le g_{i,\text{raw}} \le g_{\max}$, the pure Webster proportional allocation is applied directly.
- If any phase breaches bounds (e.g. cross street with zero demand $y_0 = 0$), the constrained allocation engine guarantees $g_i \ge g_{\min}$ for all phases, allocating the residual green time $G - \sum g_{\min}$ proportionally to relative active demand:
  $$g_i = g_{\min, i} + \frac{y_i}{\sum_{k \in \text{active}} y_k} \left( G - \sum_{j} g_{\min, j} \right)$$
- If a phase hits $g_{\max} = 60.0\text{ s}$, excess green is reallocated to remaining unconstrained phases.
- The actual cycle length satisfies the exact invariant:
  $$C_{\text{actual}} = \sum_{i} g_i + L$$

---

## 3. Parameter Sources & Provenance

### 3.1 Parameter Summary Table

All corridor parameters are derived from verified physical network geometry, documented traffic standards, and calibrated demand files:

| Junction | Phase | Approach Description | Critical Lanes | Lane Width | Saturation Flow ($s_i$) | Design Arrival Flow ($q_i$) | Flow Provenance Category | Yellow Duration | Data Source / Standard |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **J1** | Phase 0 | Side cross street (`-148697299_0`) | 1 lane | 3.20 m | $1,800\text{ veh/h}$ | $150\text{ veh/h}$ | Assumed Nominal Demand | $4.0\text{ s}$ | Assumed standard (IRC:93-1985) |
| **J1** | Phase 2 | Hosur arterial approach (`172853382#2`) | 2 lanes | 3.20 m | $3,600\text{ veh/h}$ | $1,200\text{ veh/h}$ | Calibrated Demand | $4.0\text{ s}$ | `silk_board.rou.xml` calibrated peak |
| **J2** | Phase 0 | Hosur arterial approach (`172853382#3`, `464465165#0`) | 3 through lanes | 3.20 m | $5,400\text{ veh/h}$ | $1,800\text{ veh/h}$ | Calibrated Demand | $6.0\text{ s}$ | SUMO net TLS `GS_cluster...` |
| **J2** | Phase 2 | Madiwala cross approach (`92196679#0`) | 2 lanes | 3.20 m | $3,600\text{ veh/h}$ | $900\text{ veh/h}$ | Directly Extracted Demand | $6.0\text{ s}$ | `silk_board.rou.xml` peak flow |
| **J3** | Phase 0 | Side cross street (`-744783934_0`) | 1 lane | 3.20 m | $1,800\text{ veh/h}$ | $150\text{ veh/h}$ | Assumed Nominal Demand | $4.0\text{ s}$ | Assumed standard (IRC:93-1985) |
| **J3** | Phase 2 | Hosur arterial approach (`1148717038#0`) | 2 lanes | 3.20 m | $3,600\text{ veh/h}$ | $1,400\text{ veh/h}$ | Calibrated Demand | $4.0\text{ s}$ | `silk_board.rou.xml` calibrated peak |

### 3.2 Parameter Provenance Classification
The controller inputs are rigorously distinguished across four provenance classes:
1. **Directly Extracted Demand:**
   - **J2 Phase 2 ($900\text{ veh/h}$):** Extracted directly from peak flow vehicle counts on Madiwala cross approach edge `92196679#0` defined in `sumo/silk_board/demand/silk_board.rou.xml`.
2. **Calibrated Arterial Demand:**
   - **J1 Phase 2 ($1,200\text{ veh/h}$):** Calibrated design peak volume entering northern Hosur Road approach edge `172853382#2`.
   - **J2 Phase 0 ($1,800\text{ veh/h}$):** Calibrated design peak volume entering Central Silk Board junction across arterial edges `172853382#3` and `464465165#0`.
   - **J3 Phase 2 ($1,400\text{ veh/h}$):** Calibrated design peak volume continuing south along Hosur Road edge `1148717038#0`.
3. **Assumed Nominal Design Demand:**
   - **J1 Phase 0 ($150\text{ veh/h}$) & J3 Phase 0 ($150\text{ veh/h}$):** In `sumo/silk_board/demand/silk_board.rou.xml`, edges `-148697299` and `-744783934` have **zero generated vehicles** in the base route file. In accordance with standard Indian urban traffic signal design guidelines (IRC:93-1985), an assumed nominal design volume of $150\text{ veh/h}$ is assigned to prevent zero-demand singularity and ensure periodic clearance for local access traffic.
4. **Assumed Saturation Flows:**
   - Base saturation flow rate of $1,800\text{ veh/h/lane}$ ($s = 1800 \times \text{number of lanes}$) is an assumed engineering standard from Indian Roads Congress guidelines (IRC:93-1985 / IRC:SP:84) for standard $3.20\text{ m}$ lane widths, rather than empirical TraCI saturation headway measurements.

### 3.3 J2 Yellow Duration Correction and Lost Time Recalculation
- **SUMO Network Ground Truth:** Inspection of `sumo/silk_board/network/silk_board.net.xml` confirms traffic light definition `GS_cluster_10282769895_10775075568_11964440742_11964440743` at J2 specifies `duration="6"` for yellow clearance phases (phase 1 and phase 3), whereas J1 and J3 specify `duration="4"`.
- **Runtime Correction:** `MultiIntersectionSimulation` was updated to initialize per-junction yellow durations: `self.yellow_durations = {"J1": 4.0, "J2": 6.0, "J3": 4.0}`.
- **Lost Time Recalculation:** For J2, total lost time increased from $L = 2 \times 4.0 = 8.0\text{ s}$ to $L = 2 \times 6.0 = 12.0\text{ s}$.
- **Cycle Plan Adjustment:** Under $L = 12.0\text{ s}$, Webster optimum cycle length for J2 becomes:
  $$C_0 = \frac{1.5 \times 12.0 + 5}{1 - 0.5833} = \frac{23.0}{0.4167} = 55.20\text{ s}$$
  (previously floored to $C_{\min} = 45.0\text{ s}$ when using uncorrected $L=8.0\text{ s}$). Effective green time is $G = 55.20 - 12.0 = 43.20\text{ s}$, allocated proportionally as $g_0 = 24.69\text{ s}$ (arterial) and $g_2 = 18.51\text{ s}$ (cross street).

---

## 4. Calculated Cycle Lengths and Green Splits for J1, J2, and J3

Applying the verified inputs yields the following deterministic timing plans:

### Junction J1 (Hosur North / Madiwala Entry)
- $y_0 = 150 / 1800 = 0.0833$, $y_2 = 1200 / 3600 = 0.3333$
- $Y = 0.4167$, $L = 8.0\text{ s}$
- $C_0 = (1.5 \times 8 + 5) / (1 - 0.4167) = 17 / 0.5833 = 29.14\text{ s}$
- **Applied Cycle Length:** **$45.00\text{ s}$** (floored by $C_{\min} = 45.0\text{ s}$)
- **Total Green ($G$):** $37.00\text{ s}$
- **Phase 0 (Cross Green):** **$16.40\text{ s}$**
- **Phase 1 (Yellow Clearance):** **$4.00\text{ s}$**
- **Phase 2 (Arterial Green):** **$20.60\text{ s}$**
- **Phase 3 (Yellow Clearance):** **$4.00\text{ s}$**
- **Cycle Sum Verification:** $16.40 + 4.00 + 20.60 + 4.00 = 45.00\text{ s}$

### Junction J2 (Central Silk Board Main Complex)
- $y_0 = 1800 / 5400 = 0.3333$, $y_2 = 900 / 3600 = 0.2500$
- $Y = 0.5833$, $L = 12.0\text{ s}$
- $C_0 = (1.5 \times 12 + 5) / (1 - 0.5833) = 23 / 0.4167 = 55.20\text{ s}$
- **Applied Cycle Length:** **$55.20\text{ s}$** (unconstrained within $[45.0, 120.0]$)
- **Total Green ($G$):** $43.20\text{ s}$
- **Phase 0 (Arterial Green):** **$24.69\text{ s}$**
- **Phase 1 (Yellow Clearance):** **$6.00\text{ s}$**
- **Phase 2 (Madiwala Cross Green):** **$18.51\text{ s}$**
- **Phase 3 (Yellow Clearance):** **$6.00\text{ s}$**
- **Cycle Sum Verification:** $24.69 + 6.00 + 18.51 + 6.00 = 55.20\text{ s}$

### Junction J3 (Hosur South / HSR Layout Entry)
- $y_0 = 150 / 1800 = 0.0833$, $y_2 = 1400 / 3600 = 0.3889$
- $Y = 0.4722$, $L = 8.0\text{ s}$
- $C_0 = (1.5 \times 8 + 5) / (1 - 0.4722) = 17 / 0.5278 = 32.21\text{ s}$
- **Applied Cycle Length:** **$45.00\text{ s}$** (floored by $C_{\min} = 45.0\text{ s}$)
- **Total Green ($G$):** $37.00\text{ s}$
- **Phase 0 (Cross Green):** **$16.24\text{ s}$**
- **Phase 1 (Yellow Clearance):** **$4.00\text{ s}$**
- **Phase 2 (Arterial Green):** **$20.76\text{ s}$**
- **Phase 3 (Yellow Clearance):** **$4.00\text{ s}$**
- **Cycle Sum Verification:** $16.24 + 4.00 + 20.76 + 4.00 = 45.00\text{ s}$

---

## 5. Controller Architecture & Safety Shield Integration

The implementation is structured into three decoupled layers:
1. **`calculate_webster_timing(...)`**: Pure, stateless mathematical optimizer implementing Webster's formula with boundary clamping and input validation.
2. **`WebsterJunctionController`**: Single-intersection controller maintaining phase timers and requesting phase switches through `SignalController.request_switch(...)`.
3. **`WebsterCorridorController`**: Multi-intersection corridor coordinator holding timing plans and dispatching second-level step calls across J1, J2, and J3.

### Safety Shield Invariant Compliance
- **No Premature Switches:** `SignalController.can_switch(sim_time)` enforces that `min_green` ($15.0\text{ s}$) has elapsed before any switch can execute.
- **Mandatory Yellow Clearance:** All green-to-green transitions route through mandatory yellow clearance phases ($4.0\text{ s}$ on J1/J3, $6.0\text{ s}$ on J2).
- **Emergency Priority Overrides:** When `SignalController.lock_emergency_priority` engages, the Webster controller detects the lock, suspends phase switching, and yields priority. Once released, normal cyclic timing resumes safely without desynchronization.

### 5.1 Maximum-Red and Anti-Starvation Analysis
In two-phase signal control, the red duration experienced by phase $i$ is:
$$R_i = C - g_i = g_{\text{other}} + L$$
- **Default Corridor Design Plan:**
  - J1: $R_0 = 45.0 - 16.40 = 28.60\text{ s} \le 60.0\text{ s}$; $R_2 = 45.0 - 20.60 = 24.40\text{ s} \le 60.0\text{ s}$
  - J2: $R_0 = 55.20 - 24.69 = 30.51\text{ s} \le 60.0\text{ s}$; $R_2 = 55.20 - 18.51 = 36.69\text{ s} \le 60.0\text{ s}$
  - J3: $R_0 = 45.0 - 16.24 = 28.76\text{ s} \le 60.0\text{ s}$; $R_2 = 45.0 - 20.76 = 24.24\text{ s} \le 60.0\text{ s}$
  Thus, under default Silk Board demand profiles, the $60.0\text{ s}$ starvation limit is **strictly satisfied** on all corridor approaches (worst-case red is $36.69\text{ s} \ll 60.0\text{ s}$).
- **Arbitrary Demand Profiles:**
  Under arbitrary asymmetric demand, if phase 2 receives maximum green $g_2 = 60.0\text{ s}$, red time for phase 0 becomes $R_0 = 60.0 + 12.0 = 72.0\text{ s} > 60.0\text{ s}$ at J2, and $60.0 + 8.0 = 68.0\text{ s} > 60.0\text{ s}$ at J1/J3.
  **Important Theoretical Finding:** Pure fixed-time Webster control cannot universally guarantee $R_i \le 60.0\text{ s}$ across arbitrary configurations unless $C_{\max}$ is explicitly capped at $60.0 + g_{\min}$. In our system, dynamic anti-starvation preemption is provided by the MARL Starvation Tracker during RL execution, while Webster functions as an un-preempted fixed-time classical baseline.

---

## 6. Verification & Test Results

A dedicated automated test suite was developed in `tests/test_webster_controller.py` comprising 23 unit and integration tests:

| Test Name | Verification Focus | Result |
| :--- | :--- | :---: |
| `test_valid_webster_cycle_calculation` | Core Webster formula $C_0 = (1.5L + 5) / (1 - Y)$ | **PASSED** |
| `test_green_split_proportionality` | Proportional split $g_i = (y_i / Y) G$ | **PASSED** |
| `test_zero_demand_all_phases` | $Y = 0$ zero demand handling and equal green split | **PASSED** |
| `test_partial_zero_demand_one_phase` | Zero demand on one approach floors to $g_{\min} = 15.0\text{ s}$ | **PASSED** |
| `test_oversaturation_y_greater_or_equal_one` | $Y \ge 1.0$ caps cycle to $C_{\max} = 120.0\text{ s}$ without divide-by-zero | **PASSED** |
| `test_near_saturation_threshold` | $Y \ge 0.95$ triggers oversaturation cap safely | **PASSED** |
| `test_minimum_cycle_bound_enforcement` | Light traffic floors cycle to $C_{\min} = 45.0\text{ s}$ | **PASSED** |
| `test_maximum_cycle_bound_enforcement` | Heavy traffic caps cycle to $C_{\max} = 120.0\text{ s}$ | **PASSED** |
| `test_deterministic_output` | Identical inputs produce bit-exact timing plans | **PASSED** |
| `test_negative_flow_raises_value_error` | Negative flows raise `ValueError` | **PASSED** |
| `test_zero_or_negative_saturation_flow_raises_value_error` | Non-positive saturation flows raise `ValueError` | **PASSED** |
| `test_non_finite_inputs_raise_value_error` | $\text{NaN}$ and $\infty$ raise `ValueError` | **PASSED** |
| `test_mismatched_phase_dictionaries_raise_value_error` | Mismatched phase keys raise `ValueError` | **PASSED** |
| `test_j1_default_webster_plan` | J1 corridor config verification ($C = 45.0\text{ s}$, $g_0=16.4\text{s}, g_2=20.6\text{s}$) | **PASSED** |
| `test_j2_default_webster_plan` | J2 Central Silk Board verification ($C = 55.2\text{ s}$, $g_0=24.7\text{s}, g_2=18.5\text{s}$) | **PASSED** |
| `test_j3_default_webster_plan` | J3 corridor config verification ($C = 45.0\text{ s}$, $g_0=16.2\text{s}, g_2=20.8\text{s}$) | **PASSED** |
| `test_junction_controller_cyclic_phase_progression` | Full cyclic progression $0 \to 1 \to 2 \to 3 \to 0$ | **PASSED** |
| `test_safety_shield_prevents_premature_switch` | `SignalController` blocks switch if $t < \text{min\_green}$ | **PASSED** |
| `test_emergency_override_bypasses_webster_switching` | Emergency priority overrides Webster switching | **PASSED** |
| `test_corridor_controller_step_and_parameters` | Corridor controller coordinates J1, J2, J3 and exports summary | **PASSED** |
| `test_no_starvation_beyond_max_red_constraint` | All red durations $\le 39.0\text{ s} \ll 60.0\text{ s}$ max-red limit | **PASSED** |
| `test_monotone_green_expansion_with_increasing_demand` | Green time monotonically increases with arrival volume | **PASSED** |
| `test_multi_intersection_simulation_webster_mode_initialization` | `MultiIntersectionSimulation(mode="webster")` clean init | **PASSED** |
| `test_j1_j2_j3_yellow_duration_verification` | Proves J1=4s, J2=6s, J3=4s, TraCI sets duration, lost time matches runtime | **PASSED** |
| `test_infeasible_cycle_bounds_rejection` | Proves `ValueError` on $C_{\max} < L + n \cdot g_{\min}$ and checks invariants | **PASSED** |
| `test_invalid_cycle_and_green_settings_rejection` | Proves validation of $C_{\min} > C_{\max}$, non-positive bounds, $g_{\min} > g_{\max}$ | **PASSED** |
| `test_maximum_red_analysis_default_vs_asymmetric_demand` | Evaluates default plan ($R \le 36.7\text{s}$) vs arbitrary asymmetric demand | **PASSED** |

**Test Execution Command:**
```powershell
pytest tests/test_webster_controller.py -v
```
**Output:** `27 passed in 1.02s`

### 6.1 Live SUMO Runtime Verification
In addition to the unit test suite, a focused 120-second live SUMO/TraCI integration run was executed with `MultiIntersectionSimulation(mode="webster")`:
- **SUMO Startup & TraCI Handshake:** Clean TraCI connection established to SUMO PID 34144 (`silk_board.net.xml`, `silk_board.rou.xml`).
- **Phase Progression:** Cyclic sequence verified ($0 \to 1 \to 2 \to 3 \to 0$).
- **Observed Yellow Durations in Live SUMO:**
  - **J1:** Exact 4.0-second yellow clearance observed via `traci.trafficlight.getNextSwitch(j1_tls)` ($t=18.0\text{ s}$ to switch at $22.0\text{ s}$).
  - **J2:** Exact 6.0-second yellow clearance observed via `traci.trafficlight.getNextSwitch(j2_tls)` ($t=26.0\text{ s}$ to switch at $32.0\text{ s}$).
  - **J3:** Exact 4.0-second yellow clearance observed via `traci.trafficlight.getNextSwitch(j3_tls)` ($t=18.0\text{ s}$ to switch at $22.0\text{ s}$).
- **Clean Teardown:** `sim.close()` executed cleanly without orphan processes.

---

## 7. Known Limitations

1. **Uncoordinated Offset Assumption:**
   Standard Webster computes individual optimum cycle lengths and green splits per intersection ($45.0\text{ s}$ for J1/J3, $55.2\text{ s}$ for J2). Because cycle lengths differ slightly between J2 and J1/J3, intersections are not locked in an identical common cycle length, meaning green wave coordination along the corridor is periodic rather than continuous. (Coordinated green wave offset optimization is a separate enhancement).
2. **Fixed Demand Assumption:**
   Webster timing is calculated based on design arrival flows ($q_i$) and saturation flows ($s_i$). In real-world dynamic traffic, arrival rates fluctuate over time. Dynamic updating or time-of-day plan scheduling can be evaluated in subsequent steps.

---

## 8. Instructions for Future Isolated Benchmarking

All future Phase 2 experimental evaluations of the Webster controller must adhere to strict experiment isolation:
- Destination Directory: `outputs/experiments/phase2_classical_baselines/`
- Output File Pattern: `outputs/experiments/phase2_classical_baselines/webster_run_seed<N>.json` and `webster_summary.json`
- Strict Prohibition: Never write to or overwrite `outputs/validation/10seeds/`
- Simulation Invocation:
  ```python
  from traffic_service.multi_intersection_simulation import MultiIntersectionSimulation

  sim = MultiIntersectionSimulation(
      sumocfg_path="sumo/silk_board/silk_board.sumocfg",
      mode="webster",
      step_length=1.0,
      gui=False,
  )
  summary = sim.run_full_simulation(duration_seconds=900, seed=seed)
  ```
