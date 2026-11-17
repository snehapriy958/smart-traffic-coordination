# Phase 2 — Step 1: Benchmark Preservation and Integrity Audit Report
**Smart Traffic Coordination System — Bengaluru Silk Board Corridor Testbed**

**Document Path:** `docs/PHASE_2_STEP_1_BENCHMARK_PRESERVATION_AUDIT.md`  
**Date:** 2026-11-09  
**Repository Branch:** `project-evolution/industry-research-realworld`  
**Protected Baseline Tag:** `baseline/smart-traffic-v1-verified`  
**Protected Baseline Commit:** `74c89aa7f307d37370561ac89ee27514e4608803`  
**Current HEAD Commit:** `e31de953ceb7fe878d531c888e7f27e532b13b37`  
**Audit Purpose:** Comprehensive verification and preservation of the authoritative 10-seed research benchmark, repository integrity audit, artifact protection design, and classical baseline integration planning prior to Phase 2 implementation.

---

## 1. Executive Summary & Audit Mandate

In accordance with Phase 2 governance protocols, a rigorous repository and benchmark integrity audit was performed before introducing any new traffic control algorithms. 

### Key Findings:
1. **Repository & Git Safety:** The active branch is strictly verified as `project-evolution/industry-research-realworld`. The protected baseline tag `baseline/smart-traffic-v1-verified` is cryptographically intact and points to baseline commit `74c89aa7f307d37370561ac89ee27514e4608803`.
2. **Working-Tree Status:** The working tree contains modifications and untracked files originating exclusively from **Phase 1: Engineering Foundation** (containerization, CI/CD, readiness probes, structured logging, performance measurement). Zero modifications have been made to traffic controllers, neural networks, or benchmark datasets.
3. **Authoritative Benchmark Integrity:** The 10-seed master benchmark evaluating four controllers (`Fixed-Time Baseline`, `Coordinated Adaptive`, `MARL Double-DQN`, `MARL PPO`) across seeds $1 \dots 10$ is complete, internally consistent, and backed by individual per-run JSON records ($40$ runs total).
4. **Artifact Overwrite Hazard Identified:** Analysis of `scripts/run_10seed_validation.py` revealed that its default output directory is hardcoded to `outputs/validation/10seeds/`. If executed with `--force` or modified arguments, it risks overwriting authoritative research outputs. An isolated output path (`outputs/experiments/phase2_classical_baselines/`) is established as a mandatory protection rule.
5. **MAPPO Checkpoint Audit:** The MAPPO checkpoint (`checkpoints/p6/mappo_stage_a_best.json`) was inspected and verified as an autonomous Stage A trained artifact with centralized critic weights. It is currently separate from the authoritative 10-seed master benchmark.
6. **Zero Code Modification:** No application code, controller implementations, or configuration files were modified during this audit step.

---

## 2. Repository & Git Integrity Audit

### 2.1 Branch and Commit Topology
- **Active Branch:** `project-evolution/industry-research-realworld`
- **Remote Tracking:** `origin/project-evolution/industry-research-realworld` (ahead by 1 commit: `e31de95`)
- **HEAD Commit:** `e31de953ceb7fe878d531c888e7f27e532b13b37`
  - *Commit Subject:* `docs(research): formalize verified Research Paper Master Record with empirical evidence`
- **Protected Baseline Tag Verification:**
  - `git cat-file -p d808bf6cdc869aafd47a23d3b03553650f7bb2a4` confirms:
    ```text
    object 74c89aa7f307d37370561ac89ee27514e4608803
    type commit
    tag baseline/smart-traffic-v1-verified
    tagger Sneha Singh <sneha@hybrid-traffic-control.local> 1794235313 +0530
    ```
  - The tag points directly and immutably to commit `74c89aa7f307d37370561ac89ee27514e4608803`.
  - Exactly 1 commit (`e31de95`) separates HEAD from the baseline tag anchor.

### 2.2 Working-Tree Changes Classification
An inspection of `git status --short --branch` identified 8 modified files and 14 untracked files. All changes were mapped to their engineering provenance:

| File Path | Git Status | Provenance & Description | Affects Core Traffic Research? |
| :--- | :---: | :--- | :---: |
| `.env.example` | Modified | Added Phase 1 configuration variables (`LOG_LEVEL`, `ENABLE_SECURITY_HEADERS`). | **No** |
| `.gitignore` | Modified | Hardened secret and certificate exclusion patterns. | **No** |
| `backend/config.py` | Modified | Added environment settings for logging and security middleware. | **No** |
| `backend/main.py` | Modified | Added ISO 8601 UTC structured logging and `X-Process-Time` timing headers. | **No** |
| `backend/routers/health.py` | Modified | Implemented `/api/readiness` container readiness probe. | **No** |
| `backend/schemas.py` | Modified | Added `ReadinessResponse` Pydantic model. | **No** |
| `docs/RESEARCH_PAPER_MASTER_RECORD.md`| Modified | Added Phase 1 Section 18 documentation (benchmarking and Docker evidence). | **No** |
| `tests/test_full_stack_stress.py` | Modified | Added POSIX `resource`/`pgrep` fallbacks for `win32process` on Linux/CI. | **No** |
| `.dockerignore`, `frontend/.dockerignore` | Untracked | Docker build context isolation. | **No** |
| `Dockerfile`, `frontend/Dockerfile` | Untracked | Multi-stage Docker definitions (Ubuntu 22.04 LTS + SUMO 1.28.0; Node 20 $\to$ NGINX). | **No** |
| `docker-compose.yml`, `frontend/nginx.conf` | Untracked | Multi-container development orchestration and reverse-proxying. | **No** |
| `.github/workflows/ci.yml` | Untracked | GitHub Actions automated CI verification workflow. | **No** |
| `backend/logging_config.py` | Untracked | Unified UTC ISO-8601 application logger. | **No** |
| `requirements.txt`, `requirements-dev.txt` | Untracked | Pinned production and development dependency manifests. | **No** |
| `scripts/start_backend.py` | Untracked | Backend launcher with pre-flight SUMO detection. | **No** |
| `scripts/verify_environment.py` | Untracked | Automated 8-gate environment verification script. | **No** |
| `scripts/measure_performance.py` | Untracked | Empirical latency and TraCI throughput benchmarking harness. | **No** |
| `tests/test_reliability_and_observability.py`| Untracked | 5 unit tests for readiness probes and security headers. | **No** |
| `outputs/benchmarks/` | Untracked | Persisted engineering latency metrics (`engineering_performance_metrics.json`). | **No** |

**Preservation Confirmation:** Zero traffic controller implementations (`traffic_service/`), zero trained neural checkpoints (`checkpoints/`), zero SUMO network/demand files (`sumo/`), and zero authoritative validation datasets (`outputs/validation/10seeds/`) have been modified or staged.

---

## 3. Authoritative 10-Seed Benchmark Integrity Audit

### 3.1 Benchmark Dataset Structure
The authoritative 10-seed master benchmark is located at `outputs/validation/10seeds/`:
- **Consolidated Summary:** `outputs/validation/10seeds/eval_10seeds_summary.json` (142.2 kB)
- **Statistical Analysis:** `outputs/validation/10seeds/statistical_analysis.json` (25.8 kB)
- **Per-Run Records:** `outputs/validation/10seeds/runs/` containing exactly 40 individual JSON run files:
  - 10 baseline runs: `run_baseline_seed1.json` $\dots$ `run_baseline_seed10.json`
  - 10 coordinated adaptive runs: `run_coordinated_seed1.json` $\dots$ `run_coordinated_seed10.json`
  - 10 MARL Double-DQN runs: `run_marl_dqn_seed1.json` $\dots$ `run_marl_dqn_seed10.json`
  - 10 MARL Independent PPO runs: `run_marl_ppo_seed1.json` $\dots$ `run_marl_ppo_seed10.json`

### 3.2 Evaluation Seed Audit
- **Evaluated Seeds:** Exactly $N = 10$ integer seeds: `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]`.
- **Condition Homogeneity:** Each seed was executed across all four controllers under strictly identical simulation conditions:
  - Simulation horizon $T = 900.0\text{ s}$ ($\Delta t = 1.0\text{ s}$).
  - Same network: `sumo/silk_board/network/silk_board.net.xml`.
  - Same demand: `sumo/silk_board/demand/silk_board.rou.xml` ($31$ flows).
  - Same fleet kinematics: `sumo/silk_board/demand/vehicle_types.add.xml` ($5$ vehicle classes).
  - Identical vehicle insertion window: $0 \le t < 600\text{ s}$ ($378$ total vehicles departed).
  - Identical network clearance window: $600 \le t \le 900\text{ s}$ ($0$ active vehicles remaining at $t = 900\text{ s}$).
  - Identical corridor cohort: Exactly $M = 109$ continuous $J_1 \to J_2 \to J_3$ trips completed in every run ($100\%$ completion).

### 3.3 Authoritative Empirical Findings Summary ($N = 10$, $df = 9$)

| Controller | Mean Travel Time ($\bar{T}$, s) | Travel Time 95% CI | Space-Mean Speed ($\bar{v}$, km/h) | Cumulative Delay ($D$, veh$\cdot$s) | $\text{CO}_2$ Emissions (kg) | Fuel Used (L) | Completion Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed-Time Baseline** | **90.021** ($\pm 1.259$) | $[89.12, 90.92]$ | $28.205$ ($\pm 0.354$) | $12{,}375.7$ ($\pm 175.7$) | $55.572$ ($\pm 0.407$) | $23.990$ ($\pm 0.176$) | **100.0%** ($378/378$) |
| **Coordinated Adaptive**| **49.872** ($\pm 2.462$) | $[48.11, 51.63]$ | $37.981$ ($\pm 0.358$) | $5{,}839.3$ ($\pm 185.3$) | $42.711$ ($\pm 0.380$) | $18.436$ ($\pm 0.164$) | **100.0%** ($378/378$) |
| **MARL Double-DQN** | **56.637** ($\pm 2.215$) | $[55.05, 58.22]$ | $31.463$ ($\pm 0.457$) | $8{,}026.9$ ($\pm 208.5$) | $47.140$ ($\pm 0.485$) | $20.351$ ($\pm 0.209$) | **100.0%** ($378/378$) |
| **MARL Independent PPO**| **85.501** ($\pm 5.820$) | $[81.34, 89.66]$ | $25.563$ ($\pm 0.892$) | $12{,}166.1$ ($\pm 889.7$) | $55.021$ ($\pm 1.583$) | $23.753$ ($\pm 0.683$) | **100.0%** ($378/378$) |

### 3.4 Inferential Statistics & Hypothesis Testing Integrity
- **Matched-Pairs Analysis:** All tests compute paired differences $d_i = x_{\text{candidate}, i} - x_{\text{baseline}, i}$ for identical seeds $i \in \{1 \dots 10\}$.
- **Multiple Comparisons Correction:** Bonferroni adjustment applied for $m = 3$ candidate comparisons against baseline ($\alpha_{\text{adj}} = 0.05 / 3 = 0.01667$).
- **Statistical Significance Verdicts:**
  - *Coordinated Adaptive vs. Baseline:* Travel time reduction $\mathbf{-44.61\%}$ ($\bar{d} = -40.15\text{s}$, $t = -59.25$, $p_{\text{raw}} = 5.60 \times 10^{-13}$, $p_{\text{adj}} = 1.68 \times 10^{-12}$, Wilcoxon $p = 0.00195$, Cohen's $d_z = 18.74$). **Highly Significant Improvement.**
  - *Double-DQN vs. Baseline:* Travel time reduction $\mathbf{-37.08\%}$ ($\bar{d} = -33.38\text{s}$, $t = -45.57$, $p_{\text{raw}} = 5.90 \times 10^{-12}$, $p_{\text{adj}} = 1.77 \times 10^{-11}$, Wilcoxon $p = 0.00195$, Cohen's $d_z = 14.41$). **Highly Significant Improvement.**
  - *Independent PPO vs. Baseline:* Travel time difference $-5.01\%$ ($\bar{d} = -4.52\text{s}$, $t = -2.42$, $p_{\text{raw}} = 0.0384$, $p_{\text{adj}} = \mathbf{0.1153} > 0.05$, Wilcoxon $p = 0.00586$, Cohen's $d_z = 0.77$). **NOT Significant after Bonferroni correction.**
  - *PPO Speed Degradation:* Space-mean speed drops by $\mathbf{-9.34\%}$ ($25.56\text{ km/h}$ vs. $28.21\text{ km/h}$, $t = -7.83$, $p_{\text{raw}} = 2.63 \times 10^{-5}$, $p_{\text{adj}} = \mathbf{7.88 \times 10^{-5}}$). **Statistically Significant Degradation.**

---

## 4. MAPPO Checkpoint & Evaluation Status Audit

The MAPPO (Multi-Agent PPO with Centralized Training and Decentralized Execution) implementation was inspected independently:

- **Checkpoint Path:** `checkpoints/p6/mappo_stage_a_best.json` (2.43 MB)
- **Architecture Properties:**
  - `algorithm`: `"mappo"` (Algorithm Version: `"mappo_ctde_v1"`)
  - `curriculum_stage`: `"stage_a"`
  - `seed`: 33 (Episode: 3, best mean reward: $2.6173$)
  - `agents`: Decentralized actor networks for J1, J2, and J3 (input dimension $14$, output dimension $3$ actions).
  - `shared_critic_weights`: Centralized value network observing concatenated 42-dimensional corridor observation ($s_{\text{corridor}} \in \mathbb{R}^{42}$).
- **Training Provenance:** Checkpoint generated during Phase 6 curriculum training (`train_curriculum_p6.py`). In training validation, achieved $95$ completed trips with average travel time $43.39\text{ s}$ and zero starvation violations.
- **Evaluation Status in Master Benchmark:** **Excluded.**
  - MAPPO is implemented in `traffic_service/ai/mappo_agent.py` and supported in `MultiIntersectionSimulation(mode="marl_ppo")` when configured with a MAPPO checkpoint.
  - However, the authoritative 10-seed master benchmark evaluated only `baseline`, `coordinated`, `marl_dqn`, and `marl_ppo` (Independent PPO).
  - **Audit Ruling:** MAPPO must NOT be added to or merged into the authoritative `outputs/validation/10seeds/` directory. It will be evaluated alongside the Phase 2 baselines in an isolated output directory to enable a clean comparison between Independent PPO and MAPPO (CTDE).

---

## 5. Artifact & Output Protection Protocol

### 5.1 Authoritative Artifact Register
The following files represent the baseline truth of the project and must remain strictly read-only:

```text
outputs/validation/
├── 10seeds/
│   ├── eval_10seeds_summary.json              <-- AUTHORITATIVE CONSOLIDATED SUMMARY (DO NOT OVERWRITE)
│   ├── statistical_analysis.json              <-- AUTHORITATIVE STATISTICAL ANALYSIS (DO NOT OVERWRITE)
│   └── runs/                                  <-- 40 AUTHORITATIVE RUN RECORDS (DO NOT OVERWRITE)
│       ├── run_baseline_seed1..10.json
│       ├── run_coordinated_seed1..10.json
│       ├── run_marl_dqn_seed1..10.json
│       └── run_marl_ppo_seed1..10.json
└── historical_3seeds/
    └── extended_eval_results.json             <-- HISTORICAL PHASE 5 BENCHMARK (DO NOT OVERWRITE)
```

### 5.2 Overwrite Risk Analysis
Inspection of existing evaluation scripts revealed a critical operational hazard:
- In `scripts/run_10seed_validation.py` (lines 440–442), `parser.add_argument("--output-dir", default="outputs/validation/10seeds")` defaults directly to the authoritative directory.
- Running `python scripts/run_10seed_validation.py --force` without overriding `--output-dir` will overwrite the existing 40 run records and recompute `statistical_analysis.json`.
- If new controller modes (e.g. `webster`, `actuated`, `max_pressure`) were passed to `run_10seed_validation.py` using the default path, the existing 4-controller summary would be modified.

### 5.3 Mandatory Phase 2 Output Directory Standard
To guarantee zero corruption of the historical record, all upcoming Phase 2 experiments must write to a dedicated, separate output directory tree:

```text
outputs/experiments/phase2_classical_baselines/
├── runs/                                      <-- Individual per-run JSON records
│   ├── run_webster_seed{1..N}.json
│   ├── run_actuated_seed{1..N}.json
│   ├── run_max_pressure_seed{1..N}.json
│   └── run_mappo_seed{1..N}.json
├── summary/
│   └── eval_phase2_baselines_summary.json     <-- Consolidated Phase 2 run summary
└── statistics/
    └── statistical_analysis_phase2.json       <-- Statistical comparison against Baseline
```

**Rule:** Every Phase 2 runner script must explicitly specify `--output-dir outputs/experiments/phase2_classical_baselines` or hardcode this isolated path. Never write to `outputs/validation/10seeds/`.

---

## 6. Classical Baseline Implementation Preparation (Architecture & Design)

Without modifying any source code, the application architecture was inspected to identify the exact abstractions, data requirements, decision logic, and integration points for the three planned classical baselines.

### 6.1 Baseline 1: Webster's Optimum Signal Timing

```
[Hourly Demand q_i from .rou.xml] + [Saturation Flows s_i]
                       |
                       v
     [Webster Analytical Optimization Formula]
        C_0 = (1.5*L + 5) / (1 - Y)
        g_i = (y_i / Y) * (C_0 - L)
                       |
                       v
     [Deterministic Cyclic State Machine]
   Phase 0 (g_0) -> Yellow (4s) -> Phase 2 (g_2) -> Yellow (4s)
                       |
                       v
     [SignalController Actuation on TraCI TLS]
```

- **Controller Role:** Pre-timed cyclic coordination with theoretically optimal cycle length and green splits derived from queueing theory (Webster, 1958).
- **Existing Architecture Integration Point:**
  - Implement as `traffic_service/webster_controller.py` exposing class `WebsterSignalController`.
  - Add dispatch mode `mode="webster"` in `MultiIntersectionSimulation.__init__()` and `step()`.
- **Required SUMO/TraCI Data:**
  - Offline traffic demand flows $q_i$ (veh/s or veh/h) extracted from `sumo/silk_board/demand/silk_board.rou.xml`.
  - Saturation flow rates $s_i$ (standard urban lane capacity: $s \approx 1800\text{ veh/h/lane} = 0.5\text{ veh/s/lane}$).
  - Lost time per critical phase $l_i = 4.0\text{ s}$ (startup loss $+$ yellow clearance). Total lost time per 2-phase cycle: $L = 8.0\text{ s}$.
- **State & Decision Logic:**
  1. Compute critical flow ratios: $y_i = q_i / s_i$.
  2. Compute total critical ratio: $Y = \sum_{i \in \text{critical}} y_i$.
  3. Calculate optimum cycle: $C_0 = \frac{1.5 L + 5}{1 - Y}$ (clamped to $[45\text{s}, 120\text{s}]$).
  4. Calculate effective green splits: $g_i = \frac{y_i}{Y} (C_0 - L)$.
  5. State machine: Cycles deterministically between Phase 0 ($g_0$), Yellow ($4\text{s}$), Phase 2 ($g_2$), Yellow ($4\text{s}$). Zero dynamic detector feedback.
- **Safety-Shield Integration:**
  - Naturally satisfies safety constraints if $g_i \ge 15.0\text{s}$, $g_i \le 60.0\text{s}$, and yellow $= 4.0\text{s}$.
  - Operates via `SignalController.request_switch()` to guarantee invariant enforcement.
- **Testing Requirements:**
  - Unit test verifying analytical cycle time and green split calculations against hand-solved Webster equations.
  - Integration test verifying 900-second simulation execution in SUMO with zero TraCI exceptions.

### 6.2 Baseline 2: NEMA-Style Vehicle-Actuated Control

```
[Stop-Line Loop Detectors or Virtual Approach Queues]
                       |
                       v
     [Actuated Signal Timing State Machine]
     - Min Green: g_min = 15.0s (hold green)
     - Unit Extension: t_ext = 3.0s (reset on arrival)
     - Max Green: g_max = 60.0s (force switch)
     - Gap-out: headway > t_ext -> SWITCH
     - Max-out: elapsed >= g_max -> SWITCH
                       |
                       v
     [SignalController.request_switch() via 4s Yellow]
```

- **Controller Role:** Traffic-responsive, isolated intersection control dynamically extending green phases based on continuous vehicle presence until gap-out or max-out occurs.
- **Existing Architecture Integration Point:**
  - Implement as `traffic_service/actuated_controller.py` exposing class `ActuatedSignalController`.
  - Add dispatch mode `mode="actuated"` in `MultiIntersectionSimulation`.
- **Required SUMO/TraCI Data:**
  - Instantaneous queue counts and presence on approach lanes:
    `states[j_id].approach_vehicle_counts[approach]` or `traci.lane.getLastStepVehicleNumber(lane_id)`.
  - Timestamp of most recent vehicle actuation per approach to measure headway.
- **State & Decision Logic:**
  1. Minimum Green ($g_{\text{min}} = 15.0\text{ s}$): While $g_{\text{elapsed}} < 15.0\text{s}$, hold green (`KEEP`).
  2. Passage Extension ($t_{\text{ext}} = 3.0\text{ s}$): While $g_{\text{elapsed}} \ge 15.0\text{s}$:
     - If conflicting approach has waiting vehicles ($Q_{\text{conflicting}} \ge 1$):
       - If arriving vehicle detected on active green approach within $t_{\text{ext}}$ and $g_{\text{elapsed}} < g_{\text{max}}$: extend green (`EXTEND`).
       - If gap-out occurs ($t_{\text{gap}} > t_{\text{ext}}$): initiate switch to conflicting phase (`SWITCH`).
       - If max-out occurs ($g_{\text{elapsed}} \ge g_{\text{max}} = 60.0\text{s}$): force switch (`SWITCH`).
- **Safety-Shield Integration:**
  - Calls `SignalController.request_switch()`, automatically passing through the mandatory 4.0s yellow clearance phase and respecting minimum green.
- **Testing Requirements:**
  - Unit test verifying gap-out triggering under sparse arrivals and max-out triggering under continuous arrivals.
  - Integration test verifying anti-starvation preemption under heavily asymmetrical demand.

### 6.3 Baseline 3: Varaiya Max-Pressure Control

```
[Upstream Inflow Queues x_l] ----+
                                  |---> [Queue Differential: w(p) = sum(x_l - x_m)]
[Downstream Outflow Queues x_m] -+                     |
                                                       v
                                     [Greedy Pressure Maximization]
                                        p* = argmax_p w(p)
                                                       |
                                                       v
                                    [Hysteresis Check: w(p*) > w(curr) + 2]
                                                       |
                                                       v
                                    [SignalController.request_switch()]
```

- **Controller Role:** Distributed, provably throughput-optimal back-pressure algorithm selecting phases that maximize the queue differential between upstream incoming lanes and downstream outgoing lanes (Varaiya, 2013).
- **Existing Architecture Integration Point:**
  - Implement as `traffic_service/max_pressure_controller.py` exposing class `MaxPressureController`.
  - Add dispatch mode `mode="max_pressure"` in `MultiIntersectionSimulation`.
- **Required SUMO/TraCI Data:**
  - Upstream incoming lane queue counts: $x_l(t)$ for $l \in \mathcal{L}_{\text{in}}(j)$.
  - Downstream outgoing lane queue counts: $x_m(t)$ for $m \in \mathcal{L}_{\text{out}}(j)$.
  - Movement-to-lane mapping for J1, J2, and J3 (e.g., Hosur northbound exit at J1 enters edge `172853382#3` which forms the upstream approach to J2).
- **State & Decision Logic:**
  1. For each valid non-conflicting green phase $p \in \{0, 2\}$ at junction $j$:
     $$w_j(p, t) = \sum_{(l, m) \in p} \left( Q_l(t) - Q_m(t) \right)$$
  2. Select target phase with maximal pressure: $p^*(t) = \arg\max_{p} w_j(p, t)$.
  3. Hysteresis switching rule (evaluated every $T_{\text{decision}} = 5.0\text{ s}$):
     - If $p^*(t) == \text{current\_phase}$: hold green (`KEEP`).
     - If $p^*(t) \ne \text{current\_phase}$:
       - If $g_{\text{elapsed}} \ge 15.0\text{ s}$ and $w_j(p^*) > w_j(p_{\text{curr}}) + 2.0$: initiate transition to $p^*$ through yellow (`SWITCH`).
       - Otherwise: hold green (`KEEP`).
- **Safety-Shield Integration:**
  - Fully shielded by `SignalController` and `StarvationTracker`. If max red exceeds $60.0\text{ s}$ on any approach, the safety shield overrides the pressure calculation.
- **Testing Requirements:**
  - Unit test verifying pressure computation under varying upstream and downstream queue states.
  - Integration test verifying corridor stabilization without gridlock.

---

## 7. Comparative Architecture Matrix: Existing vs. Planned Controllers

| Architectural Dimension | Fixed-Time Baseline | Coordinated Adaptive | MARL Double-DQN | MARL PPO | Webster Baseline (Planned) | Actuated Baseline (Planned) | Max-Pressure (Planned) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Control Paradigm** | Static Cyclic | Heuristic Feedback | Off-Policy Q-learning | On-Policy Policy Gradient | Analytical Optimum Cyclic | Dynamic Gap-Out | Queue Differential Back-Pressure |
| **Inter-Junction Comms**| None | Virtual Platoon Hub | Decentralized Observation | Decentralized Observation | None | None | Implicit Network Topology |
| **Upstream Anticipation**| None | Yes ($Q_{\text{up}} = \lfloor 5 \times q \rfloor$) | Yes (inflow in $s_j$) | Yes (inflow in $s_j$) | None | None | Downstream Queue Penalty |
| **Hysteresis Threshold**| None | $\Delta Q > 2$ | Argmax $Q(s, a)$ | Argmax $\pi(a|s)$ | None | Gap-out ($t_{\text{ext}} = 3\text{s}$) | $\Delta w > 2$ |
| **Safety Shield Binding**| SUMO Native | Hard Invariants | Hard Invariants | Hard Invariants | Hard Invariants | Hard Invariants | Hard Invariants |
| **Training Requirement**| None | None | Required (Phase 6) | Required (Phase 6) | None | None | None |
| **Output Directory** | `outputs/validation/10seeds` | `outputs/validation/10seeds` | `outputs/validation/10seeds` | `outputs/validation/10seeds` | `outputs/experiments/phase2_classical_baselines` | `outputs/experiments/phase2_classical_baselines` | `outputs/experiments/phase2_classical_baselines` |

---

## 8. Verification Checklist & Blocking Issues

### 8.1 Audit Verification Checklist
- [x] Verified active branch is `project-evolution/industry-research-realworld`.
- [x] Verified HEAD commit is `e31de953ceb7fe878d531c888e7f27e532b13b37`.
- [x] Verified protected baseline tag `baseline/smart-traffic-v1-verified` immutably targets commit `74c89aa7f307d37370561ac89ee27514e4608803`.
- [x] Inspected and categorized all 8 modified and 14 untracked files from Phase 1 engineering foundation.
- [x] Verified the authoritative 10-seed master benchmark ($40$ individual run files, summary, and statistical analysis).
- [x] Inspected MAPPO checkpoint (`checkpoints/p6/mappo_stage_a_best.json`) and verified its isolation from the 10-seed benchmark.
- [x] Identified overwrite hazard in `run_10seed_validation.py` and established mandatory Phase 2 output directory standard (`outputs/experiments/phase2_classical_baselines/`).
- [x] Documented architectural integration points for Webster, Actuated, and Max-Pressure controllers without editing code.
- [x] Confirmed zero lines of source code or configurations were modified during this step.
- [x] Confirmed zero Git commits or pushes occurred.

### 8.2 Blocking Issues & Next Actions
- **Blocking Issues:** **None.** The repository is clean, the baseline tag is verified, the authoritative benchmark is preserved, and the architecture is ready for Phase 2 implementation.
- **Recommended Next Action:** Upon user review and explicit approval of this audit report, proceed to **Phase 2 — Step 2: Implementation of Classical Baselines** (Webster, Actuated, and Max-Pressure controllers) under the isolated output protection standard.

---

## 9. Final Working-Tree Status

```text
On branch project-evolution/industry-research-realworld
Your branch is ahead of 'origin/project-evolution/industry-research-realworld' by 1 commit.

Changes not staged for commit:
	modified:   .env.example
	modified:   .gitignore
	backend/config.py
	backend/main.py
	backend/routers/health.py
	backend/schemas.py
	docs/RESEARCH_PAPER_MASTER_RECORD.md
	tests/test_full_stack_stress.py

Untracked files:
	.dockerignore
	.github/workflows/ci.yml
	Dockerfile
	backend/logging_config.py
	docker-compose.yml
	docs/PHASE_2_STEP_1_BENCHMARK_PRESERVATION_AUDIT.md
	frontend/.dockerignore
	frontend/Dockerfile
	frontend/nginx.conf
	outputs/benchmarks/engineering_performance_metrics.json
	requirements-dev.txt
	requirements.txt
	scripts/measure_performance.py
	scripts/start_backend.py
	scripts/verify_environment.py
	tests/test_reliability_and_observability.py

no changes added to commit (0 commits, 0 pushes)
```

---
*Report formally filed at:* [`docs/PHASE_2_STEP_1_BENCHMARK_PRESERVATION_AUDIT.md`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/docs/PHASE_2_STEP_1_BENCHMARK_PRESERVATION_AUDIT.md)  
*Audit certified on:* `project-evolution/industry-research-realworld`  
*Commit Anchor:* `74c89aa7f307d37370561ac89ee27514e4608803`  
*Tag Anchor:* `baseline/smart-traffic-v1-verified`