# Experiment Data Provenance and Traceability Register

## 1. Overview and Purpose

This document establishes the authoritative data provenance, file registry, and experiment lineage for the **Smart Traffic Coordination System – Bengaluru Silk Board Corridor**.

It documents the origin, location, parameterization, and validation status of all empirical datasets, simulation scripts, route definitions, and checkpoints across the project history.

---

## 2. Definitive Experiment Lineage and Dataset Inventory

| Dataset Identifier | Horizon | Seeds Evaluated | File System Location | Generating Entry Point | Audit Status | Description / Role |
|---|---:|---|---|---|:---:|---|
| **Phase 4/5 Extended Benchmark** | **900s** | **`[1, 2, 3]`** | `C:\Users\Sneha Singh\.gemini\antigravity\brain\1bc986a7-c556-43f9-8c53-6ea55756f37e\scratch\extended_eval_results.json` | `scratch/scratch_run_eval.py` | **AUTHENTIC GROUND TRUTH** | Official 12-run multi-regime evaluation across 4 controllers. $100\%$ trip completion (378 departed / 378 arrived). |
| **Stage P5 Multi-Seed Evaluation** | 600s | `[1, 2, 3, 4, 5]` | [`results/p5/p5_evaluation_results.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/results/p5/p5_evaluation_results.json) | [`scripts/evaluate_p5_controllers.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/scripts/evaluate_p5_controllers.py) | **HISTORICAL** | Earlier 20-run evaluation. Recorded MARL P5 starvation failure (0 completed trips for PPO). |
| **Stage P5 Per-Run CSV Traces** | 600s | `[1, 2, 3, 4, 5]` | [`results/p5/per_run_csvs/`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/results/p5/per_run_csvs/) (20 files) | `traffic_service/corridor_metrics.py` | **HISTORICAL** | Second-by-second telemetry traces (queues, speeds, delay, emissions). |
| **Stage P5 Training Checkpoints** | 120s/ep | `[42, 84, 126]` | [`checkpoints/p5_training/`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/checkpoints/p5_training/) | `scripts/train_p5_multi_seed.py` | **ARCHIVED** | Multi-seed pilot training models. Strictly decoupled from evaluation seeds `[1, 2, 3, 4, 5]`. |
| **Stage P6 Curriculum Stage A** | 300s/ep | `[11, 22, 33, 44, 55]` | [`results/p6/stage_a_stage_summary.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/results/p6/stage_a_stage_summary.json) | [`scripts/train_curriculum_p6.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/scripts/train_curriculum_p6.py) | **ACTIVE TRAINING** | Pre-training checkpoints for Stage A (`checkpoints/marl_ppo_corridor.json`, `marl_dqn_corridor.json`). |
| **Phase 7 Fabricated Claims** | 900s | *`[42, 43, 44]`* | None (Retracted) | Synthetic text generation | **DEBUNKED & RETRACTED** | Reporting error confusing default demo seed 42 with actual evaluation seeds `[1, 2, 3]`. |

---

## 3. Network, Route, and Model File Mapping

### 3.1 Genuine Source Code and Network Paths

| Component | Verified Local File Path | Role |
|---|---|---|
| **SUMO Network** | [`sumo/silk_board/network/silk_board.net.xml`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/sumo/silk_board/network/silk_board.net.xml) | Actual 3-intersection Hosur Road network ($J_1, J_2, J_3$). |
| **Traffic Demand** | [`sumo/silk_board/demand/silk_board.rou.xml`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/sumo/silk_board/demand/silk_board.rou.xml) | 31 flows + 1 ambulance vehicle ($0 \le t \le 600\text{s}$, 378 vehicles). |
| **Vehicle Types** | [`sumo/silk_board/demand/vehicle_types.add.xml`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/sumo/silk_board/demand/vehicle_types.add.xml) | Krauss car-following parameters (`sigma="0.5"`). |
| **Simulation Config** | [`sumo/silk_board/silk_board.sumocfg`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/sumo/silk_board/silk_board.sumocfg) | Entry configuration file. |
| **Simulation Engine** | [`traffic_service/multi_intersection_simulation.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/multi_intersection_simulation.py) | TraCI coordination engine and safety preemption. |
| **MARL Controller** | [`traffic_service/ai/marl_controller.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/marl_controller.py) | PPO and Double-DQN action selection and execution. |
| **Starvation Tracker**| [`traffic_service/ai/starvation_tracker.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/starvation_tracker.py) | 60-second anti-starvation constraint and action masking. |
| **DQN Checkpoint** | [`checkpoints/marl_dqn_corridor.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/checkpoints/marl_dqn_corridor.json) | Stage A Double-DQN weights evaluated in benchmark. |
| **PPO Checkpoint** | [`checkpoints/marl_ppo_corridor.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/checkpoints/marl_ppo_corridor.json) | Stage A Actor-Critic PPO weights evaluated in benchmark. |

### 3.2 Correction of Ghost Paths Identified in Early Reports
The following paths appeared in earlier unverified drafts and are formally clarified:
- `backend/traffic_generator.py` $\implies$ **Does not exist**. Traffic demand is generated via SUMO flows in `sumo/silk_board/demand/silk_board.rou.xml`.
- `sumo/corridor.rou.xml` $\implies$ **Does not exist**. The actual route file is `sumo/silk_board/demand/silk_board.rou.xml`.
- `backend/marl_controller.py` $\implies$ **Relocated**. The actual controller is `traffic_service/ai/marl_controller.py`.

---

## 4. Root Cause Analysis of Phase 7 Reporting Drift

The discrepancy between the Phase 5 Engineering Audit and Phase 7 documentation was investigated and traced through four contributing factors:

1. **Artifact Location Confusion:**
   The extended evaluation script (`scratch/scratch_run_eval.py`) wrote its output to the agent's brain scratch directory:
   `C:\Users\Sneha Singh\.gemini\antigravity\brain\1bc986a7-c556-43f9-8c53-6ea55756f37e\scratch\extended_eval_results.json`
   When the Phase 7 audit attempted to inspect `scratch/extended_eval_results.json` in the workspace root, the file was not found. Rather than searching the environment or checking task logs, synthetic numbers were generated.

2. **Conflation of Default Argument with Seed Array:**
   In `traffic_service/multi_intersection_simulation.py`, the default method signature is:
   `def run_full_simulation(self, duration_seconds: int = 600, seed: int = 42):`
   The recurrence of default argument `seed=42` led to an assumption that the 3-seed evaluation used seeds `[42, 43, 44]`, whereas the evaluation runner explicitly executed `seeds = [1, 2, 3]`.

3. **Conflation of a 120-Second Smoke Test with 900-Second Results:**
   During Phase 7, a quick 120-second smoke test was run to verify controller hooks (`duration=120`), producing 25 decision points at J2 (`EXTEND: 14, KEEP: 11, SWITCH: 0`). This was inadvertently described in Phase 7 documentation as the full 900-second action trace.

4. **In-Flight Queue Misinterpretation:**
   During peak intervals ($0-300\text{s}$), $62-83$ vehicles are actively in-flight on the network. In Phase 7, temporary in-flight counts were erroneously interpreted as "unfinished/dropped trips" at simulation termination, ignoring the fact that the 300-second clearance window ($600-900\text{s}$) clears 100% of vehicles.

---

## 5. Governance and Verification Rules for Future Experiments

To prevent data drift in upcoming phases (including the planned 10-seed experiment):

1. **Workspace-Local Artifact Storage:**
   All future experiment runners must output artifacts directly inside the workspace directory tree:
   `outputs/validation/10seeds/`
   and NEVER solely in ephemeral agent scratch directories.

2. **Self-Documenting Manifests:**
   Every output JSON must include a top-level `provenance` block recording:
   - Script name and git commit SHA.
   - Host environment and SUMO version.
   - Exact seed list array.
   - Route and network file SHA-256 hashes.

3. **Automated Assertion on Artifact Existence:**
   Documentation updates must run automated validation scripts that read the exact output JSON and verify every printed number against the raw data.
