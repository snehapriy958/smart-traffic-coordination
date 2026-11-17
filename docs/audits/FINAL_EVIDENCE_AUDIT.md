# FINAL EVIDENCE AUDIT: 10-SEED BENCHMARK AND SYSTEM INTEGRITY

**Audit Timestamp:** 2026-11-09T15:35:00+05:30  
**Repository Branch:** `marl-p6-2-curriculum-training` (HEAD: `0fa845e`)  
**Scope:** Forensic verification of 40-run simulation outputs, experimental seeds, paired demand, vehicle cohorts, statistical calculations, multiple-comparison corrections, PPO multi-junction policy distributions, safety overrides, runtime fallback rates, and Git repository state.

---

## 1. Executive Findings Matrix

| Audit Item | Status | Verified Finding |
|:---|:---:|:---|
| **1. Seed Diversity** | **VERIFIED** | Demand schedules and routes are deterministic; microscopic car-following stochasticity ($\sigma = 0.5$) generates genuine variance across seeds ($3.89\text{s}$ travel-time range in Baseline, $7.88\text{s}$ in Adaptive). |
| **2. Demand Pairing** | **VERIFIED** | For any seed $s \in [1, 10]$, all 4 controllers receive identical initial traffic, vehicle types, routes, and SUMO `--seed` parameter. Demand is strictly paired. |
| **3. Metric Accounting** | **VERIFIED & DISCLOSED** | Travel time is evaluated over the 109 corridor-crossing vehicles; speed is the network-wide time-mean of instantaneous approach speeds across all 3 junctions, NOT harmonic space-mean speed ($L/\text{travel\_time}$). |
| **4. Raw Data Recomputation** | **VERIFIED** | All descriptive summaries recomputed from the 40 raw JSON run files match `eval_10seeds_summary.json` to 4 decimal places. |
| **5. Inferential Statistics** | **VERIFIED** | Paired t-tests, degrees of freedom ($df=9$), 95% CIs, Cohen's $d_z$, and Wilcoxon signed-rank tests match verified standards. |
| **6. Multiple Comparisons** | **DISCLOSED & CORRECTED** | Multiple-comparison correction was **not applied** in Phase 8. When Bonferroni correction ($m=3$) is applied, PPO's travel time improvement is **NOT statistically significant** ($p_{adj} = 0.1153$). PPO's speed degradation **remains significant** ($p_{adj} < 0.001$). |
| **7. PPO Multi-Junction Actions** | **VERIFIED & DIAGNOSED** | Policy collapse is present at **both $J_1$ and $J_2$**: $J_1$ chose 97.0% KEEP, 0.0% EXTEND; $J_2$ chose 61.8% KEEP, 38.2% EXTEND, 0.0% SWITCH. $J_3$ remained dynamic (21.7% SWITCH). |
| **8. Anti-Starvation Safety** | **VERIFIED** | The 60-second guardrail triggered 66 times for PPO (preventing permanent gridlock at $J_2$) and only 9 times for DQN. Arterial highway starved twice per run under PPO, zero times under DQN. |
| **9. Controller Runtime Modes** | **VERIFIED** | All controllers executed in their intended modes without fallback ($0.0\%$ fallback frequency; zero NaNs or inference exceptions). |
| **10. Git and Repository Integrity** | **VERIFIED** | User modifications in `backend/models.py`, `tests/test_database.py`, and `README.md` are preserved. Zero destructive commands executed. |

---

## 2. Detailed Audit by Section

### Task 1 — Seed Diversity Verification
- **Demand Specification:** Defined in [`sumo/silk_board/demand/silk_board.rou.xml`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/sumo/silk_board/demand/silk_board.rou.xml).
- **Route Distribution:** Deterministic across all seeds. Exactly **109 vehicles (28.8%)** execute the full arterial trip `corridor_j1_j2_j3`, and **269 vehicles (71.2%)** execute feeder turning movements.
- **Departure Schedules:** Fixed `<flow>` intervals generate identical scheduled departure times. Across 39 of 40 runs, departures partitioned identically into 208 Peak, 170 Shoulder, and 0 Off-peak. In exactly 1 run (Baseline Seed 3), severe queue congestion delayed vehicle insertion by 1 second, shifting 1 vehicle to $t = 601\text{s}$ (208 Peak, 169 Shoulder, 1 Off-peak). In all 40 runs, total departed = 378 and total arrived = 378.
- **Microscopic Seed Diversity:** Controlled by Krauss car-following stochastic deceleration parameter $\sigma = 0.5$ in [`sumo/silk_board/demand/vehicle_types.add.xml`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/sumo/silk_board/demand/vehicle_types.add.xml) and `--seed <s>` passed to TraCI. This creates driver deceleration noise and spacing variations at every 1-second simulation step, producing genuine metric variance across seeds:
  - Baseline Travel Time: $88.15\text{s}$ (Seed 8) to $92.04\text{s}$ (Seed 2) ($\Delta = 3.89\text{s}$).
  - Coordinated Adaptive Travel Time: $47.14\text{s}$ (Seed 4) to $55.02\text{s}$ (Seed 8) ($\Delta = 7.88\text{s}$).
  - MARL DQN Travel Time: $53.25\text{s}$ (Seed 3) to $59.58\text{s}$ (Seed 10) ($\Delta = 6.33\text{s}$).
  - MARL PPO Travel Time: $69.95\text{s}$ (Seed 4) to $89.97\text{s}$ (Seed 2) ($\Delta = 20.02\text{s}$).

### Task 2 — Demand Pairing Verification
For each seed $s \in [1, 10]$:
- Network file, route definitions, vehicle classes, and simulation horizon ($900\text{s}$) are identical.
- SUMO random seed passed via `--seed <s>` is identical across all four controllers.
- Therefore, the incoming traffic arrival profile before signal actuation is strictly identical. Downstream differences reflect solely controller decisions, ensuring strict paired experimental control.

### Task 3 — Vehicle Cohorts, Route Distances, and Metric Reconciliations
- **Corridor Travel Time (`avg_corridor_travel_time_s`):**
  - Evaluated exclusively over the cohort of **109 vehicles** traversing the full arterial route `corridor_j1_j2_j3`.
  - Traversal measured from entry on edge `172853382#2` to exit on edge `40696223#1`.
  - Total lane length of the 4 corridor edges is $386.24\text{ m}$ (excluding internal junction connections).
- **Network Travel Time (`avg_net_travel_time_s`):**
  - Evaluated over all **378 vehicles** across all network routes from departure to arrival.
- **Speed (`avg_speed_kmh`):**
  - **Important Methodological Disclosure:** `avg_speed_kmh` is **NOT** the harmonic space-mean speed derived from corridor length ($L / \bar{T}_{\text{corridor}}$).
  - Instead, it is the **network-wide time-mean of instantaneous approach speeds** sampled at 1-second intervals across all active junction incoming lanes, converted to km/h.
  - Approach speeds naturally range from $0\text{ km/h}$ (stopped at red) to $45\text{--}55\text{ km/h}$ (moving at green).
- **Aggregation Consistency:** The vehicle cohorts (109 corridor, 378 network) and edge definitions are 100% consistent across all 40 simulation runs.

### Task 4 & 5 — Independent Statistical Recomputation ($N=10, df=9, t_{\text{crit}} = \pm 2.26216$)

#### Descriptive Statistics:
- **Fixed-Time Baseline:**
  - Travel Time: $\bar{X} = 90.0210\text{ s}, s = 1.2590\text{ s}, SE = 0.3981\text{ s}, 95\%\text{ CI} = [89.12, 90.92]\text{ s}$.
  - Speed: $\bar{X} = 28.2050\text{ km/h}, s = 0.3729\text{ km/h}, SE = 0.1179\text{ km/h}, 95\%\text{ CI} = [27.94, 28.47]\text{ km/h}$.
  - Cumulative Delay: $\bar{X} = 12{,}373.2\text{ veh}\cdot\text{s}, s = 135.1\text{ veh}\cdot\text{s}, SE = 42.7\text{ veh}\cdot\text{s}$.
- **Coordinated Adaptive:**
  - Travel Time: $\bar{X} = 49.8720\text{ s}, s = 2.4616\text{ s}, SE = 0.7784\text{ s}, 95\%\text{ CI} = [48.11, 51.63]\text{ s}$ ($-44.61\%$).
  - Speed: $\bar{X} = 37.9810\text{ km/h}, s = 0.2632\text{ km/h}, SE = 0.0832\text{ km/h}, 95\%\text{ CI} = [37.79, 38.17]\text{ km/h}$ ($+34.68\%$).
  - Cumulative Delay: $\bar{X} = 5{,}836.8\text{ veh}\cdot\text{s}, s = 296.5\text{ veh}\cdot\text{s}, SE = 93.8\text{ veh}\cdot\text{s}$ ($-52.82\%$).
- **MARL Double-DQN (Stage A):**
  - Travel Time: $\bar{X} = 56.6370\text{ s}, s = 2.2154\text{ s}, SE = 0.7006\text{ s}, 95\%\text{ CI} = [55.05, 58.22]\text{ s}$ ($-37.08\%$).
  - Speed: $\bar{X} = 31.4630\text{ km/h}, s = 0.4416\text{ km/h}, SE = 0.1397\text{ km/h}, 95\%\text{ CI} = [31.15, 31.78]\text{ km/h}$ ($+11.56\%$).
  - Cumulative Delay: $\bar{X} = 8{,}024.4\text{ veh}\cdot\text{s}, s = 284.9\text{ veh}\cdot\text{s}, SE = 90.1\text{ veh}\cdot\text{s}$ ($-35.13\%$).
- **MARL PPO (Stage A):**
  - Travel Time: $\bar{X} = 85.5010\text{ s}, s = 5.8198\text{ s}, SE = 1.8404\text{ s}, 95\%\text{ CI} = [81.34, 89.66]\text{ s}$ ($-5.01\%$).
  - Speed: $\bar{X} = 25.5630\text{ km/h}, s = 0.9127\text{ km/h}, SE = 0.2886\text{ km/h}, 95\%\text{ CI} = [24.91, 26.22]\text{ km/h}$ ($-9.34\%$).
  - Cumulative Delay: $\bar{X} = 12{,}163.6\text{ veh}\cdot\text{s}, s = 896.6\text{ veh}\cdot\text{s}, SE = 283.5\text{ veh}\cdot\text{s}$ ($-1.66\%$).

#### Paired Differences and Hypothesis Tests vs Baseline:
- **Coordinated Adaptive vs. Baseline:**
  - Travel Time: Mean diff $= -40.15\text{ s} (-44.61\%)$, $t = -59.25, p = 5.60 \times 10^{-13}$, $95\%\text{ CI} = [-41.68, -38.62]\text{ s}$, Wilcoxon $W = 0.0, p = 0.00195$, Cohen's $d_z = 18.74$.
  - Speed: Mean diff $= +9.78\text{ km/h} (+34.68\%)$, $t = +81.30, p = 3.26 \times 10^{-14}$, $95\%\text{ CI} = [+9.50, +10.05]\text{ km/h}$, Wilcoxon $W = 0.0, p = 0.00195$, Cohen's $d_z = 25.71$.
  - Cumulative Delay: Mean diff $= -6{,}536.4\text{ veh}\cdot\text{s} (-52.82\%)$, $t = -64.40, p = 2.65 \times 10^{-13}$, Wilcoxon $W = 0.0, p = 0.00195$, Cohen's $d_z = 20.37$.
- **MARL DQN vs. Baseline:**
  - Travel Time: Mean diff $= -33.38\text{ s} (-37.08\%)$, $t = -45.57, p = 5.90 \times 10^{-12}$, $95\%\text{ CI} = [-35.04, -31.73]\text{ s}$, Wilcoxon $W = 0.0, p = 0.00195$, Cohen's $d_z = 14.41$.
  - Speed: Mean diff $= +3.26\text{ km/h} (+11.56\%)$, $t = +20.52, p = 7.25 \times 10^{-9}$, $95\%\text{ CI} = [+2.90, +3.62]\text{ km/h}$, Wilcoxon $W = 0.0, p = 0.00195$, Cohen's $d_z = 6.49$.
  - Cumulative Delay: Mean diff $= -4{,}348.8\text{ veh}\cdot\text{s} (-35.13\%)$, $t = -38.26, p = 2.83 \times 10^{-11}$, Wilcoxon $W = 0.0, p = 0.00195$, Cohen's $d_z = 12.10$.
- **MARL PPO vs. Baseline:**
  - Travel Time: Mean diff $= -4.52\text{ s} (-5.01\%)$, $t = -2.4231, p = 0.03842$, $95\%\text{ CI} = [-8.74, -0.30]\text{ s}$, Wilcoxon $W = 2.0, p = 0.00586$, Cohen's $d_z = 0.77$.
  - Speed: Mean diff $= -2.64\text{ km/h} (-9.34\%)$, $t = -7.8301, p = 2.63 \times 10^{-5}$, $95\%\text{ CI} = [-3.41, -1.88]\text{ km/h}$, Wilcoxon $W = 0.0, p = 0.00195$, Cohen's $d_z = 2.48$ (**Statistically significant degradation**).
  - Cumulative Delay: Mean diff $= -209.6\text{ veh}\cdot\text{s} (-1.66\%)$, $t = -0.6972, p = 0.5033$, $95\%\text{ CI} = [-889.7, +470.5]\text{ veh}\cdot\text{s}$, Wilcoxon $W = 25.0, p = 0.8457$, Cohen's $d_z = 0.22$ (**Not statistically significant**).

---

### Task 6 — Multiple-Comparison Correction Analysis

**Audit Disclosure:** In Phase 8, pairwise t-tests were reported with raw, unadjusted p-values against an uncorrected $\alpha = 0.05$.

When comparing 3 candidate controllers against 1 baseline control ($m = 3$ comparisons per endpoint):
1. **Bonferroni Adjustment ($\alpha_{\text{adj}} = \alpha / 3 = 0.01667$):**
   - **Coordinated Adaptive Travel Time:** $p_{\text{adj}} = 3 \times (5.60 \times 10^{-13}) = 1.68 \times 10^{-12} \ll 0.001$ (**Robustly Significant**).
   - **MARL DQN Travel Time:** $p_{\text{adj}} = 3 \times (5.90 \times 10^{-12}) = 1.77 \times 10^{-11} \ll 0.001$ (**Robustly Significant**).
   - **MARL PPO Travel Time:** Raw $p = 0.03842 \implies p_{\text{adj}} = 3 \times 0.03842 = \mathbf{0.11526 > 0.05}$ (**NOT Statistically Significant**).
   - **MARL PPO Speed Penalty:** Raw $p = 2.63 \times 10^{-5} \implies p_{\text{adj}} = 7.89 \times 10^{-5} \ll 0.01$ (**Statistically Significant Degradation**).
2. **Scientific Conclusion:**  
   Under family-wise error control, **MARL PPO does NOT demonstrate statistically significant travel-time superiority over the Fixed-Time Baseline**. The only statistically significant effect for PPO is a **statistically significant $-9.34\%$ speed penalty**.

---

### Task 7 — Multi-Junction PPO Action Distribution Audit

Audited across all 10 seeds ($1,810$ decisions per junction, $5,430$ total decisions per controller):

| Controller | Junction | Total Decisions | KEEP (%) | SWITCH (%) | EXTEND (%) | Policy Diagnosis |
|:---|:---:|---:|---:|---:|---:|:---|
| **MARL PPO** | **J1** | 1,810 | **1,756 (97.0%)** | 54 (3.0%) | 0 (0.0%) | **Severe KEEP collapse; EXTEND completely dead** |
| | **J2** | 1,810 | **1,118 (61.8%)** | **0 (0.0%)** | **692 (38.2%)** | **Complete SWITCH collapse; zero voluntary phase changes** |
| | **J3** | 1,810 | 911 (50.3%) | 392 (21.7%) | 507 (28.0%) | Dynamic tripartite policy |
| **MARL DQN** | **J1** | 1,810 | 859 (47.5%) | 430 (23.8%) | 521 (28.8%) | Balanced active switching |
| | **J2** | 1,810 | 666 (36.8%) | 412 (22.8%) | 732 (40.4%) | Balanced active switching (412 switches vs 0 for PPO) |
| | **J3** | 1,810 | 179 (9.9%) | 108 (6.0%) | 1,523 (84.1%) | Outflow-holding policy |

#### Root Cause of PPO Failure:
Neural forward passes on the trained PPO checkpoint [`checkpoints/marl_ppo_corridor.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/checkpoints/marl_ppo_corridor.json) reveal that for realistic traffic observations with queuing:
- At $J_2$, the actor network outputs probabilities: $P(\text{KEEP}) = 0.4613, P(\text{SWITCH}) = 0.2253, P(\text{EXTEND}) = 0.3134$.
- In evaluation mode (`argmax`), action `1` (`SWITCH`) is never selected because both `KEEP` and `EXTEND` dominate.
- At $J_1$, the actor network outputs $P(\text{KEEP}) = 0.3438 > P(\text{SWITCH}) = 0.3401 > P(\text{EXTEND}) = 0.3161$, causing `KEEP` to dominate 97.0% of all decisions.
- Therefore, PPO suffered policy collapse at **both $J_1$ and $J_2$**, but in different failure modes ($J_1$ frozen on KEEP, $J_2$ locked between KEEP and EXTEND).

---

### Task 8 — 60-Second Maximum-Green Safety Mechanism Audit
- **Mechanism Implementation:** Governed by `StarvationTracker` in [`traffic_service/ai/starvation_tracker.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/starvation_tracker.py).
- **Operation:** When an approach faces continuous red $\ge 60.0\text{s}$ with queue $\ge 1$, the tracker masks out all actions except `SWITCH` (`[0.0, 1.0, 0.0]`), forcing a transition to yellow and logging a `StarvationEvent`.
- **Empirical Overrides Across 10 Seeds:**
  - **MARL PPO:** **66 total safety interventions** (average 6.6 per run).
    - `J2:corridor_hosur`: **20 events** (exactly 2 per run in every seed). Arterial traffic was halted on red for $60.0\text{s}$ twice per run, building queues of up to 31 vehicles.
    - `J2:madiwala`: **46 events** (4.6 per run). Cross-street was held on red for $60.0\text{s}$ four to five times per run.
    - **Audit Finding:** The safety mechanism worked exactly as intended. Without this safety override, $J_2$ would have remained permanently locked on green for one approach, completely halting the other approach and crashing the simulation.
  - **MARL DQN:** **9 total safety interventions** across all 10 seeds (average 0.9 per run).
    - `J2:corridor_hosur`: **0 events** (arterial highway was NEVER starved).
    - `J2:madiwala`: **9 events** (minor cross-street interventions only).

---

### Task 9 — Controller Runtime Modes and Fallback Audit
- **Fixed-Time Baseline:** Mode `baseline`. Relies entirely on pre-timed internal SUMO TLS schedules. Fallback frequency: **0.0%**.
- **Coordinated Adaptive:** Mode `coordinated`. Executes queue-proportional phase allocation with green-wave progression via `_run_coordinated_control`. Fallback frequency: **0.0%**.
- **MARL DQN:** Mode `marl_dqn`. Loads `checkpoints/marl_dqn_corridor.json`. Evaluates $1,810$ decisions per run across 3 `DQNAgent` instances. Fallback frequency: **0.0%** (zero exceptions, zero NaNs, zero fallback decisions).
- **MARL PPO:** Mode `marl_ppo`. Loads `checkpoints/marl_ppo_corridor.json`. Evaluates $1,810$ decisions per run across 3 `PPOAgent` instances. Fallback frequency: **0.0%** (zero exceptions, zero NaNs, zero fallback decisions).

---

### Task 10 — Repository and Git State Audit
- **Branch:** `marl-p6-2-curriculum-training` (aligned with `origin/main` at `0fa845e`).
- **Unstaged User Modifications:**
  - `README.md`
  - `backend/models.py`
  - `tests/test_database.py`
  - All three files remain intact and preserved.
- **Experimental Artifacts on Disk:**
  - `outputs/validation/historical_3seeds/extended_eval_results.json` (SHA-256 verified).
  - `outputs/validation/10seeds/runs/` (40 raw run JSON files).
  - `outputs/validation/10seeds/eval_10seeds_summary.json` (Summary dataset).
  - `outputs/validation/10seeds/statistical_analysis.json` (Master statistical dataset).
  - `scripts/run_10seed_validation.py` (Autonomous execution runner).
- **Commit Safety:** No unapproved commits, pushes, resets, stashes, or cleanups were executed.

---

## 3. Unresolved Issues and Limitations

1. **PPO Checkpoint Maturity:**  
   The checkpoint evaluated in Phase 8 is a **Stage A curriculum checkpoint**. Because Stage A pre-training focused on basic flow stabilization with strong domain prior biases, PPO suffered policy saturation at $J_1$ and $J_2$. Advancing to Stage B (congestion dynamics) and Stage C (corridor wave coordination) with entropy regularization is required to produce a functional PPO controller.
2. **Speed Calculation Definition:**  
   The reported speed metric ($28.20\text{ km/h}$ Baseline vs. $37.98\text{ km/h}$ Adaptive) represents the **time-mean of instantaneous approach speeds across all 3 intersections**, not the corridor-wide space-mean speed derived from travel time ($L/\bar{T}_{\text{corridor}}$). This distinction must be explicitly stated in any academic publication or final-year defense presentation.
3. **PPO Travel Time Significance:**  
   While raw pairwise testing yielded $p = 0.0384$, family-wise error control (Bonferroni $p_{\text{adj}} = 0.1153$) reveals that **MARL PPO has no statistically defensible travel-time improvement over baseline**. Its only statistically significant impact is a $-9.34\%$ speed penalty caused by repeated 60-second anti-starvation halts.

---
**Audit Approved by:** Antigravity Senior Engineering & Verification Auditor
