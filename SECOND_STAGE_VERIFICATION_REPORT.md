# SECOND-STAGE AUDIT & VERIFICATION REPORT
**Project**: Smart Traffic Coordination System — Bengaluru Traffic Intelligence Platform  
**Target Corridor**: Central Silk Board Junction Corridor (J1, J2, J3 along Hosur Road)  
**Audit Phase**: Independent Discrepancy Reconciliation & Browser Verification  
**Audit Date**: November 17, 2026  
**Auditor Roles**: Principal Systems Architect, Senior AI/ML Researcher, Traffic Simulation Specialist, Independent QA Auditor  
**Repository State**: Branch `project-evolution/industry-research-realworld` (Clean working tree, zero uncommitted code)  

---

## 1. Discrepancy Identification & Authoritative Resolutions

### Discrepancy 1: Controller Safety Guardrail Parameters
- **Observed Discrepancy**: The previous audit report (`FINAL_PROJECT_AUDIT.md`) stated:
  - Minimum green: $10.0\,\text{s}$
  - Maximum green: $60.0\,\text{s}$
  - Yellow clearance: $3.0\,\text{s}$
  Whereas the established research record specified:
  - Minimum green: $15.0\,\text{s}$
  - Maximum green: $60.0\,\text{s}$
  - Yellow clearance: $4.0\,\text{s}$ ($6.0\,\text{s}$ for J2)
- **Code & Network Ground Truth**:
  1. `sumo/silk_board/network/silk_board.net.xml`:
     - J1 (`1617743335`): Phase 0 (41s Green), Phase 1 (**4s Yellow**), Phase 2 (41s Green), Phase 3 (**4s Yellow**).
     - J2 (`GS_cluster_...`): Phase 0 (39s Green), Phase 1 (**6s Yellow**), Phase 2 (39s Green), Phase 3 (**6s Yellow**).
     - J3 (`6970466614`): Phase 0 (41s Green), Phase 1 (**4s Yellow**), Phase 2 (41s Green), Phase 3 (**4s Yellow**).
  2. `traffic_service/signal_controller.py`:
     - `min_green: float = 15.0`
     - `max_green: float = 60.0`
     - `yellow_duration: float = 4.0`
  3. `traffic_service/nema_controller.py`:
     - J1: `min_green = 15.0`, `max_green = 60.0`, `yellow_durations = {0: 4.0, 2: 4.0}`
     - J2: `min_green = 15.0`, `max_green = 60.0`, `yellow_durations = {0: 6.0, 2: 6.0}`
     - J3: `min_green = 15.0`, `max_green = 60.0`, `yellow_durations = {0: 4.0, 2: 4.0}`
  4. `traffic_service/ai/env.py`:
     - `min_green: float = 15.0`
     - `max_green: float = 60.0`
     - `can_switch = 1.0 if elapsed >= self.min_green else 0.0` (masks out `ACTION_SWITCH` until 15s elapsed).
  5. `traffic_service/resilience/transit_priority.py`:
     - `min_green_before_tsp: float = 15.0`
     - `max_green: float = 60.0`
- **Resolution**: **VERIFIED**. The codebase, SUMO phase definitions, and controllers have **always consistently enforced** `min_green = 15.0s`, `max_green = 60.0s`, and `yellow = 4.0s` (J1, J3) / `6.0s` (J2). The figures $10.0\,\text{s}$ and $3.0\,\text{s}$ in `FINAL_PROJECT_AUDIT.md` were typographical errors in the text of the previous audit report, not in the codebase.

---

### Discrepancy 2: Emissions Methodology (HBEFA4 vs HBEFA3)
- **Observed Discrepancy**: The previous audit report referenced HBEFA3, while newer project documentation (`docs/PROJECT_AUDIT/19_P2_VERIFICATION_ADDENDUM.md`) cited HBEFA4.
- **Code & Configuration Ground Truth**:
  1. `sumo/silk_board/demand/vehicle_types.add.xml`: `<vType>` elements (`motorcycle`, `car`, `bmtc_bus`, `heavy_vehicle`, `ambulance`) do not specify an explicit `emissionClass` attribute.
  2. Under modern SUMO (versions $\ge 1.14$, including active SUMO 1.26.0), omitting `emissionClass` causes the engine to default to **HBEFA4/2.0** models:
     - `car` (`vClass="passenger"`) $\to$ `HBEFA4/PC_petrol_Euro-4`
     - `motorcycle` (`vClass="motorcycle"`) $\to$ `HBEFA4/MC_4S_gt250cc_preEuro`
  3. Metric Accumulation (`traffic_service/state_extractor.py`, `traffic_service/corridor_metrics.py`):
     - $\text{CO}_2\,(\text{kg}) = \frac{\sum \text{CO}_2\,(\text{mg/s}) \times \Delta t}{1{,}000{,}000}$
     - $\text{NO}_x\,(\text{g}) = \frac{\sum \text{NO}_x\,(\text{mg/s}) \times \Delta t}{1{,}000}$
     - $\text{Fuel}\,(\text{L}) = \frac{\sum \text{Fuel}\,(\text{mg})}{750{,}000}$ based on standard BS-VI / Euro-4 petrol reference density $\rho = 0.750\,\text{kg/L}$ ($750{,}000\,\text{mg/L}$) per DIN EN 228.
- **Resolution**: **VERIFIED**. Modern SUMO 1.26.0 computes emissions via **HBEFA4/2.0**. Earlier documentation mentioned HBEFA3 because SUMO versions prior to 1.14 used HBEFA3 by default. The mathematical conversions to physical units ($\text{kg}$, $\text{g}$, $\text{L}$) are physically sound and verified.

---

### Discrepancy 3: Benchmark Standard Deviations & Precision
- **Observed Discrepancy**: Standard deviations reported in `FINAL_PROJECT_AUDIT.md` (e.g., $90.021 \pm 1.19\,\text{s}$ for Baseline, $49.872 \pm 2.34\,\text{s}$ for Coordinated, $56.637 \pm 2.10\,\text{s}$ for Double-DQN, $85.501 \pm 5.52\,\text{s}$ for PPO) differed slightly from values in `statistical_analysis.json` ($1.259\,\text{s}$, $2.462\,\text{s}$, $2.215\,\text{s}$, $5.753\,\text{s}$).
- **Mathematical Root Cause**:
  - The previous audit computed the **population standard deviation** ($\sigma$, $N=10$, `ddof=0`):
    - Baseline: $\sigma = 1.1944\,\text{s} \approx 1.19\,\text{s}$
    - Coordinated: $\sigma = 2.3353\,\text{s} \approx 2.34\,\text{s}$
    - Double-DQN: $\sigma = 2.1017\,\text{s} \approx 2.10\,\text{s}$
    - PPO: $\sigma = 5.4578\,\text{s} \approx 5.52\,\text{s}$ (rounded from early run)
  - The authoritative inferential record (`outputs/validation/10seeds/statistical_analysis.json`) computes the **sample standard deviation** ($s$, degrees of freedom $N-1 = 9$, `ddof=1`):
    - Baseline: $s = 1.2590\,\text{s}$
    - Coordinated: $s = 2.4616\,\text{s}$
    - Double-DQN: $s = 2.2154\,\text{s}$
    - PPO: $s = 5.7534\,\text{s}$
- **Resolution**: **VERIFIED**. Both metrics originate from the exact same raw data points. For scientific and inferential reporting, the **sample standard deviation ($s$, ddof=1)** must be used.

---

### Discrepancy 4: Series 4E Passenger-Weighted Reward Claims
- **Observed Discrepancy**: The previous audit claimed that multi-objective passenger weighting increased the BMTC bus TSP grant rate from $36.7\%$ to $88.4\%$ and reduced passenger-hours of delay (PHD) by $14.2\%$.
- **Inspection of Raw Data Artifacts**:
  - Located `outputs/experiments/phase4/series_4e_passenger_reward/series_4e_summary.json` (100 total evaluation runs: 50 delay-centric, 50 passenger-weighted).
  - Inspection of `per_formulation` in `series_4e_summary.json`:
    - `delay_centric`: `travel_time_mean_s = 84.38`, `passenger_hours_of_delay_phd = 3.86`, `tsp_grant_rate_mean = 0.3666` ($36.66\%$).
    - `passenger_weighted`: `travel_time_mean_s = 84.38`, `passenger_hours_of_delay_phd = 3.86`, `tsp_grant_rate_mean = 0.3666` ($36.66\%$).
  - Inspection of all 50 matched evaluation pairs (`matched_pairs`):
    - $\Delta \text{grant\_rate} = 0.000$ across every single evaluation pair.
    - $\Delta \text{phd} = 0.000$ across every single evaluation pair.
  - The figure $88.4\%$ was traced to `train_seed 105` alone (which had an $88.8\%$ grant rate under **both** formulations due to seed-specific training variance), while $36.7\%$ was the overall mean across all seeds.
- **Resolution**: **UNVERIFIED & UNSUPPORTED**. The claim of a $36.7\% \to 88.4\%$ TSP grant rate increase and $14.2\%$ PHD reduction is **unsupported** by the actual completed Series 4E evaluation records. Under greedy evaluation, both checkpoints produced identical action sequences (0% SWITCH actions), yielding zero delta. **This claim must be retracted and excluded from all presentation materials.**

---

### Discrepancy 5: MAPPO Performance Claims (Series 4C)
- **Observed Discrepancy**: The previous audit asserted that MAPPO (Series 4C) resolves the single-agent PPO saturation at Junction 2.
- **Inspection of Manifest & Checkpoint Records**:
  - Target experiment: 25 training runs (5 betas $\times$ 5 seeds, 150 episodes each) and 250 evaluation runs.
  - Actual progress in `outputs/experiments/phase4/final_150ep/series_4c_reward_coupling/manifest_series_4c.json`:
    - **Only 3 of 25 runs completed** ($12.0\%$ completion): `beta_000_seed101`, `beta_000_seed102`, `beta_000_seed103`.
    - `beta_000_seed104` is stalled/interrupted (`TRAINING`, 0 evaluations).
    - Remaining 21 runs are `PENDING`.
    - Completed evaluations: 30 of 250 ($12.0\%$).
  - Mean travel times for the 3 completed runs across their 10 evaluation seeds:
    - `beta_000_seed101`: $80.43\,\text{s}$
    - `beta_000_seed102`: $88.16\,\text{s}$
    - `beta_000_seed103`: $99.38\,\text{s}$ (worse than Fixed-Time Baseline of $90.02\,\text{s}$)
    - Pooled mean across completed runs: **$89.32\,\text{s}$**.
- **Resolution**: **PARTIALLY VERIFIED (IN-PROGRESS RESEARCH)**. There is **insufficient empirical evidence** to claim that MAPPO outperforms single-agent PPO ($85.50\,\text{s}$) or Fixed-Time Baseline ($90.02\,\text{s}$). The completed subset exhibits high inter-seed variance ($80.4\text{s}$ to $99.4\text{s}$) and spatial coupling betas ($\beta > 0.00$) have not yet been evaluated.

---

### Discrepancy 6: Hallucinated Backend Route Path in Audit Text
- **Observed Discrepancy**: `FINAL_PROJECT_AUDIT.md` cited `traffic_service/api/` as the location of the backend REST routers.
- **File System Inspection**:
  - The path `traffic_service/api/` does not exist.
  - The actual FastAPI backend implementation is located in `backend/` (`backend/routers/health.py`, `backend/routers/simulation.py`, `backend/routers/traffic.py`, `backend/routers/signals.py`, `backend/routers/emergencies.py`, `backend/routers/risks.py`, `backend/routers/decisions.py`, `backend/routers/experiments.py`, `backend/websocket_manager.py`).
- **Resolution**: **VERIFIED**. The discrepancy was purely an erroneous file path citation in the previous audit text. All backend code and tests execute from `backend/`.

---

## 2. Verified vs. Unverified Claims Summary

```
┌────────────────────────────────────────────────────────┬─────────────────────┬────────────────────────────────────────────────────────┐
│ Claim / Feature Assertion                              │ Verification Status │ Evidentiary Basis                                      │
├────────────────────────────────────────────────────────┼─────────────────────┼────────────────────────────────────────────────────────┤
│ Coordinated Adaptive cuts travel time by 44.6%         │ VERIFIED            │ N=10 seed evaluation (p = 1.68e-11, Cohen's dz = 12.83)│
│ Double-DQN cuts corridor travel time by 37.1%          │ VERIFIED            │ N=10 seed evaluation (p = 1.40e-11, Cohen's dz = 13.07)│
│ Single-agent PPO (Stage A) saturated at J2             │ VERIFIED            │ N=10 seed evaluation (p_adj = 0.1153, not significant) │
│ Safety guardrails (15s min green, 60s max green)       │ VERIFIED            │ Present in SUMO net, SignalController, & env action mask│
│ HBEFA4/2.0 emissions and DIN EN 228 fuel modeling     │ VERIFIED            │ Default in SUMO 1.26.0, verified density 0.750 kg/L    │
│ Live WebSocket streaming & Three.js 3D Digital Twin    │ VERIFIED            │ Verified live in browser subagent (0 errors, 200 OK)   │
│ Series 4B observation dimensionality ablation (N=300)  │ VERIFIED            │ Frozen dataset, LMM variance decomposition verified    │
│ MAPPO conclusively beats single-agent PPO (Series 4C)  │ UNVERIFIED          │ Incomplete study: 3/25 runs done, mean 89.32s ≈ PPO    │
│ Passenger reward increases bus TSP to 88.4% (Series 4E)│ UNVERIFIED          │ Unsupported: delta=0.0 across all 50 matched pairs     │
│ Emergency vehicle database logging during live run     │ PARTIALLY VERIFIED  │ TraCI preemption verified live; DB table has 0 rows    │
└────────────────────────────────────────────────────────┴─────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 3. Authoritative Reconciled Benchmark Results ($N=10$, $900\,\text{s}$)

Recomputed directly from the 40 raw execution files in `outputs/validation/10seeds/`:

### A. Descriptive Statistics Across 10 Independent Random Seeds

| Controller | Mean Travel Time ($s$) | Sample Std ($s$, ddof=1) | Pop Std ($\sigma$, ddof=0) | Standard Error (SE) | 95% Confidence Interval | Mean Speed (km/h) | Cumulative Delay ($\text{veh}\cdot\text{s}$) | Fuel (L) | $\text{CO}_2$ (kg) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed-Time Baseline** | $90.021$ | $1.259$ | $1.194$ | $0.398$ | $[89.120, 90.922]$ | $28.205 \pm 0.373$ | $12{,}373.2 \pm 135.1$ | $23.993 \pm 0.084$ | $55.578 \pm 0.195$ |
| **Coordinated Adaptive** | **$49.872$** | $2.462$ | $2.335$ | $0.778$ | $[48.111, 51.633]$ | **$37.981 \pm 0.263$** | **$5{,}836.8 \pm 296.5$** | **$18.439 \pm 0.277$** | **$42.718 \pm 0.642$** |
| **Double-DQN (Stage A)**| **$56.637$** | $2.215$ | $2.102$ | $0.701$ | $[55.052, 58.222]$ | **$31.463 \pm 0.442$** | **$8{,}024.4 \pm 284.9$** | **$20.353 \pm 0.279$** | **$47.148 \pm 0.646$** |
| **PPO (Stage A)** | $85.501$ | $5.753$ | $5.458$ | $1.819$ | $[81.386, 89.616]$ | $25.563 \pm 1.018$ | $12{,}163.6 \pm 952.5$ | $23.757 \pm 0.768$ | $55.031 \pm 1.777$ |

### B. Inferential Paired Hypothesis Tests vs. Fixed-Time Baseline

| Controller | Mean Difference | % Change | Paired $t$-statistic | Raw $p$-value | Bonferroni-Adjusted $p$ ($\alpha = 0.0167$) | Cohen's $d_z$ | Inferential Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Coordinated Adaptive** | $-40.149\,\text{s}$ | **$-44.60\%$** | $-40.573$ | $1.68 \times 10^{-11}$ | **$5.04 \times 10^{-11}$** | $12.83$ | **Statistically Significant Improvement** |
| **Double-DQN (Stage A)** | $-33.384\,\text{s}$ | **$-37.09\%$** | $-41.343$ | $1.40 \times 10^{-11}$ | **$4.20 \times 10^{-11}$** | $13.07$ | **Statistically Significant Improvement** |
| **PPO (Stage A)** | $-4.520\,\text{s}$ | $-5.01\%$ | $-2.423$ | $0.0384$ | $0.1153$ | $0.77$ | **Not Statistically Significant after Bonferroni Correction** |

---

## 4. Reconciled Safety and Emissions Parameters

### A. Safety Parameters by Controller and Junction

| Component / Controller | Junction ID | Min Green ($s$) | Max Green ($s$) | Yellow Clearance ($s$) | Enforcement Mechanism |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **SUMO Network (`net.xml`)** | J1 (`1617743335`) | N/A | N/A | **$4.0\,\text{s}$** | Static phase definitions (Phases 1 & 3) |
| **SUMO Network (`net.xml`)** | J2 (`GS_cluster_...`)| N/A | N/A | **$6.0\,\text{s}$** | Static phase definitions (Phases 1 & 3) |
| **SUMO Network (`net.xml`)** | J3 (`6970466614`) | N/A | N/A | **$4.0\,\text{s}$** | Static phase definitions (Phases 1 & 3) |
| **SignalController Core** | J1, J2, J3 | **$15.0\,\text{s}$** | **$60.0\,\text{s}$** | **$4.0\,\text{s}$** (default) | `can_switch_phase()`, yellow sequencing |
| **NEMA Actuated Controller** | J1 | $15.0\,\text{s}$ | $60.0\,\text{s}$ | $4.0\,\text{s}$ | NEMA gap-out and max-recall timers |
| **NEMA Actuated Controller** | J2 | $15.0\,\text{s}$ | $60.0\,\text{s}$ | $6.0\,\text{s}$ | NEMA gap-out and max-recall timers |
| **NEMA Actuated Controller** | J3 | $15.0\,\text{s}$ | $60.0\,\text{s}$ | $4.0\,\text{s}$ | NEMA gap-out and max-recall timers |
| **Webster Controller** | J1, J2, J3 | $15.0\,\text{s}$ | $60.0\,\text{s}$ | $4.0\,\text{s}$ / $6.0\,\text{s}$ | Critical flow green-split bounds |
| **RL Action Environment (`env.py`)**| J1, J2, J3 | **$15.0\,\text{s}$** | **$60.0\,\text{s}$** | Inherited from `SignalController` | Action mask masks `ACTION_SWITCH` until $\ge 15.0\,\text{s}$ |
| **Transit Priority Manager** | Corridor | **$15.0\,\text{s}$** | **$60.0\,\text{s}$** | Unmodified yellow clearance | Green extension capped at max-green ceiling |

### B. Emissions Methodology Ground Truth

| Metric | SUMO Underlying Model | Source Extraction API | Raw Unit | Reporting Unit | Conversion Factor / Reference Standard |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Carbon Dioxide ($\text{CO}_2$)** | HBEFA4/2.0 | `traci.lane.getCO2Emission()` | $\text{mg/s}$ | $\text{kg}$ | $\sum (\text{mg/s} \times \Delta t) / 1{,}000{,}000.0$ |
| **Nitrogen Oxides ($\text{NO}_x$)** | HBEFA4/2.0 | `traci.lane.getNOxEmission()` | $\text{mg/s}$ | $\text{g}$ | $\sum (\text{mg/s} \times \Delta t) / 1{,}000.0$ |
| **Fuel Consumption** | HBEFA4/2.0 | `traci.lane.getFuelConsumption()`| $\text{mg/s}$ | $\text{L}$ | $\sum \text{mg} / 750{,}000.0$ ($\rho = 0.750\,\text{kg/L}$ per DIN EN 228) |

---

## 5. Experimental Series Status (4B, 4C, 4E)

### A. Series 4B (Observation Space Dimensionality Ablation): **VERIFIED (COMPLETE)**
- **Protocol**: 6 configurations (D8, D10, D12, D14, D16, D18) $\times$ 5 training seeds $\times$ 10 evaluation seeds = **300 total evaluations**.
- **Dataset**: Frozen in `outputs/experiments/phase4/series4b_final_validation/`.
- **Finding**: Hierarchical Linear Mixed-Effects Models (LMM) proved that $65.2\%$ to $98.9\%$ of performance variance is driven by training seed stochasticity rather than state dimensionality.

### B. Series 4C (Spatial Coupling Weight Sweep $\beta \in [0.00, 1.00]$): **PARTIALLY VERIFIED (IN-PROGRESS)**
- **Protocol**: 25 training runs $\times$ 150 episodes $\times$ 10 evaluation seeds = **250 total evaluations**.
- **Completed**: **3 of 25 training runs** ($12.0\%$), **30 of 250 evaluations** ($12.0\%$).
- **Active / Stalled**: Run 4 (`beta_000_seed104`) is marked `TRAINING` with 0 evaluations.
- **Pending**: 21 runs.
- **Mean Travel Time of Completed Subset**: $89.32\,\text{s}$ (Seed 101: 80.4s, Seed 102: 88.2s, Seed 103: 99.4s).
- **Verdict**: Incomplete. MAPPO cannot be claimed as superior to single-agent PPO until all 25 runs and statistical comparisons are computed.

### C. Series 4E (Multi-Objective Passenger Reward): **UNVERIFIED & UNSUPPORTED**
- **Protocol**: 100 evaluation runs (50 delay-centric, 50 passenger-weighted).
- **Findings**: The evaluation JSON files show identical metrics ($\Delta = 0.000$) between delay-centric and passenger-weighted models due to greedy evaluation action masking producing identical phase cycles.
- **Verdict**: The prior claim of a $36.7\% \to 88.4\%$ TSP grant rate increase was an artifact of comparing Seed 101 vs Seed 105, not the two formulations. **Marked UNVERIFIED.**

---

## 6. Test Integrity & Modification Findings

### A. Inspection of Git Diff for `tests/test_api.py`
- **Modified Test**: `test_experiments_compare()`
- **Modifications Made**:
  1. Made assertions dynamic based on whether the API serves the authoritative 10-seed master benchmark or fallback 5-seed benchmark.
  2. In the 10-seed branch, added assertions verifying travel times for all 4 controllers (`base == 90.02s`, `coord == 49.87s`, `dqn == 56.64s`, `ppo == 85.50s`) and ordinal rankings (`coord < dqn < base`).
  3. **Identified Gap**: In the 10-seed branch of the test, fuel consumption (`base["total_fuel_liters"]`), `cumulative_waiting_time_s`, and `cumulative_delay_veh_s` assertions were inadvertently omitted.
- **Test Integrity Verdict**: **VERIFIED WITH OBSERVATIONS**.
  - No tests were skipped (`@pytest.mark.skip` was not used).
  - The API was genuinely exercised via FastAPI `TestClient`.
  - All **14 tests independently executed and PASSED** in $4.57\,\text{s}$ (command: `pytest tests/test_api.py -v`).

---

## 7. Actual Browser-Level Verification Results

*Verified by independent browser QA subagent (`c4d366b9-ade6-4dc8-a8f5-6984416ee140`), host-attested origin `http://127.0.0.1:5173`, zero blocked origins, latest screenshot `final_step_39.png`:*

1. **Top Bar & Connectivity**:
   - WebSocket stream: **CONNECTED**.
   - SUMO daemon: **Online (v1.26)**.
   - Simulation state engine: Responsive (Controller Mode selector, duration, seed, green wave toggle, Start/Reset controls).
2. **Browser Console**:
   - **0 console errors**, **0 console warnings** across all page views, tab switches, and component renders.
3. **Network Requests**:
   - 100% of REST API requests returned **HTTP 200 OK** (`/api/health`, `/simulation/status`, `/traffic/metrics`, `/traffic/live`, `/signals`, `/emergencies`, `/risks`, `/experiments/compare`, `/traffic/vehicles`).
4. **3D Digital Twin (Phase 3B)**:
   - Three.js `<canvas>` loads and renders the 3-intersection Hosur Road corridor scene.
   - Spatial navigation camera buttons (`Area Overview`, `Corridor Overview`, `J1`, `J2`, `J3`) smoothly translate perspective.
   - Controller overlay selector (`Coordinated Adaptive`, `Fixed-Time`, `Double-DQN`, `PPO`) updates telemetry overlays in real time.
5. **Controller Comparison & Emission Analytics**:
   - Interactive toggle between **Authoritative 10-Seed Master Benchmark** and **Historical 5-Seed Benchmark** operates instantaneously.
   - Comparative bar charts render travel times, speeds, delay, queue, and fuel volumes correctly.
6. **Research & Experiments Sub-Tabs**:
   - `Overview & Matrix`: Renders complete empirical study matrix (Series 4A–4G).
   - `Series 4B`: Displays frozen dimensionality ablation and LMM variance charts.
   - `Series 4C Live Monitor`: Streams active execution terminal and 25-run manifest status.
   - `Series 4E`: Displays passenger reward comparison with clear notation of empirical parity.
   - `Master Benchmark (N=10)`: Renders Bonferroni-corrected significance table.
7. **UI Structure**:
   - Clean, centered responsive container layout (388px mobile kiosk style) inside desktop viewport.

---

## 8. Assessment of Explainable Corridor Intelligence

### Existing Infrastructure
- `backend/routers/decisions.py` exposes `GET /api/decisions`.
- `backend/simulation_service.py` logs `DecisionItemSchema` with:
  - `sim_time`, `junction_id`, `current_phase`, `target_phase`, `action` (`KEEP`, `SWITCH`, `EXTEND`), `reason`, and `is_override`.
- `frontend/src/components/SignalStatusPanel.jsx` already displays real-time phase countdowns, min/max green meters ($15\text{s}/60\text{s}$), and per-approach queue lengths.

### Minimum Safe Implementation (No Disconnected Component, No Retraining)
To expose the complete causal chain without adding new routes, retraining controllers, or modifying reward functions:
- Extend `SignalStatusPanel.jsx` with an expandable **"Decision Rationale & Causal Chain"** drawer under each junction card:
  1. **Observed Traffic State**: Display upstream queue and conflicting cross-street queue.
  2. **Active Controller & Selected Action**: Badge indicating current controller (`Coordinated Adaptive` / `Double-DQN`) and selected action (`HOLD GREEN`, `SWITCH PHASE`).
  3. **Decision Reason**: Display the text from `sim_service._record_decision` (e.g., *"Arterial green-wave hold: platoon approaching J2 from J1"*).
  4. **Phase Transition**: Display `Phase X` $\to$ `Phase Y` transition status.
  5. **Resulting Effect**: Display instantaneous queue change ($\Delta Q$).

---

## 9. Remaining Demo Blockers & Low-Risk Prioritized Fix List

### Remaining Blockers Before Live Public Pitch
1. **Series 4E Presentation Material**: The previous audit slide/notes claiming an $88.4\%$ bus priority grant rate must be updated to state that Series 4E showed action saturation under greedy evaluation, motivating current research into stochastic exploration during evaluation.
2. **Emergency Events Table**: The SQLite database `emergency_events` table has 0 rows from past automated runs. While TraCI preemption works live, one recorded emergency run should be committed to the database so the historical emergency table is not empty.
3. **Missing Assertions in `test_api.py`**: Add back the fuel and delay assertions to the 10-seed branch in `test_experiments_compare`.

### Prioritized Fix List

```
┌────┬──────────┬────────────────────────────────────────────────────────┬──────────────┬────────────────────────┐
│ ID │ Priority │ Action Item                                            │ Risk Level   │ Implementation Target  │
├────┼──────────┼────────────────────────────────────────────────────────┼──────────────┼────────────────────────┤
│ F1 │ P0       │ Update presentation script to cite 10-seed master      │ Zero Risk    │ Presentation Slides /  │
│    │          │ benchmark values (44.6% travel time, 52.8% delay drop) │              │ Pitch Talking Points   │
│    │          │ and retract the unverified 88.4% Series 4E claim.      │              │                        │
├────┼──────────┼────────────────────────────────────────────────────────┼──────────────┼────────────────────────┤
│ F2 │ P1       │ Restore fuel & delay assertions to 10-seed branch in   │ Very Low     │ `tests/test_api.py`    │
│    │          │ `tests/test_api.py` to ensure complete coverage.       │              │                        │
├────┼──────────┼────────────────────────────────────────────────────────┼──────────────┼────────────────────────┤
│ F3 │ P1       │ Pre-seed 1 emergency vehicle preemption record in      │ Low Risk     │ `traffic_dashboard.db` │
│    │          │ `traffic_dashboard.db` via POST /api/emergencies.      │              │                        │
├────┼──────────┼────────────────────────────────────────────────────────┼──────────────┼────────────────────────┤
│ F4 │ P2       │ Integrate Decision Rationale drawer inside existing     │ Low Risk     │ `frontend/src/         │
│    │          │ `SignalStatusPanel.jsx` component.                     │              │ components/Signal...`  │
├────┼──────────┼────────────────────────────────────────────────────────┼──────────────┼────────────────────────┤
│ F5 │ P2       │ Resume Series 4C master worker from Run 4 (seed 104)   │ Low Risk     │ `scripts/              │
│    │          │ with dynamic loopback socket port allocation.          │              │ train_series4c_...`    │
└────┴──────────┴────────────────────────────────────────────────────────┴──────────────┴────────────────────────┘
```

---

## 10. Final Demo Readiness Verdict

### System Classification: **PARTIALLY VERIFIED WITH VERIFIED CORE DEMO CAPABILITY**

```
┌───────────────────────────────────────────────┬─────────────────────────────┐
│ Category                                      │ Verdict                     │
├───────────────────────────────────────────────┼─────────────────────────────┤
│ Corridor Simulation & TraCI Control           │ VERIFIED                    │
│ Backend API & Telemetry Broadcast             │ VERIFIED                    │
│ Frontend Dashboard & 3D Digital Twin          │ VERIFIED                    │
│ Coordinated Adaptive Controller Performance   │ VERIFIED                    │
│ Double-DQN Controller Performance             │ VERIFIED                    │
│ Single-Agent PPO Saturation Disclosure        │ VERIFIED                    │
│ Safety Guardrails (15s/60s/4s & 6s)           │ VERIFIED                    │
│ HBEFA4/2.0 Emissions Modeling                 │ VERIFIED                    │
│ MAPPO Superiority over PPO (Series 4C)        │ UNVERIFIED (In-Progress)    │
│ Passenger Reward TSP Improvement (Series 4E)  │ UNVERIFIED (Unsupported)    │
│ Overall Live Demo Readiness                   │ VERIFIED FOR LIVE DEMO      │
└───────────────────────────────────────────────┴─────────────────────────────┘
```

The core software, microscopic SUMO simulation, real-time WebSocket telemetry, 3D Digital Twin, Coordinated Adaptive controller ($-44.6\%$ travel time reduction), and Double-DQN controller ($-37.1\%$ travel time reduction) are **genuinely functional, empirically verified across 10 random seeds, and ready for live demonstration**. In-progress research investigations (Series 4C and 4E) must be presented honestly according to the verified data.
