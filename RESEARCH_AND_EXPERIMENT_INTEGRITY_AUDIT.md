# RESEARCH & EXPERIMENT INTEGRITY AUDIT
## Empirical Provenance, Seed Design, Variance Decomposition, and Statistical Rigor
**Auditor**: Lead Traffic Simulation Researcher & Statistical QA Auditor  
**Date**: November 17, 2026  
**Artifact Repositories**: `checkpoints/phase4/`, `outputs/experiments/phase4/`, `outputs/validation/10seeds/`

---

### 1. Master Research Series Overview

The research program investigates the application of Multi-Agent Reinforcement Learning (MARL) to high-density arterial corridors under heterogeneous, multi-modal Indian traffic conditions. All series maintain strict isolation of configurations, seeds, checkpoints, and evaluation artifacts:

```
                                      PHASE 4 RESEARCH ARCHITECTURE
                                                     |
         +-------------------------------------------+-------------------------------------------+
         |                                           |                                           |
         v                                           v                                           v
    SERIES 4B                                   SERIES 4C                                   SERIES 4E
Observation Dimensionality                   Reward Coupling                             Passenger Weighting
[FROZEN & CERTIFIED]                    [ACTIVE RESUMPTION: 3/25]                      [EVALUATED & CERTIFIED]
- 6 Configurations (14D, 8D, 4D)         - 5 Betas (0.00, 0.25, 0.50, 0.75, 1.00)       - Delay-Centric vs Passenger
- 2 Algorithms (MAPPO, DQN)              - 5 Training Seeds (101-105)                   - BMTC Bus (45p) vs Car (1.5p)
- 30 Checkpoints, 300 Evaluations        - 25 Runs x 150 Episodes = 3,750 Episodes      - 10 Checkpoints, 100 Evaluations
- Hierarchical Variance Audit            - 250 Confirmatory Evaluations                 - Matched-Pairs Analysis
```

---

### 2. Audit: Master 10-Seed Authoritative Benchmark

- **File**: [`outputs/validation/10seeds/eval_10seeds_summary.json`](file:///C:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/validation/10seeds/eval_10seeds_summary.json)
- **Protocol**: 10 independent evaluation seeds ($1, 2, \dots, 10$), 900 seconds duration, 109 completed corridor trips per seed.
- **Verification Result**:

| Controller | Status | Checkpoint Provenance | Travel Time (s) | Speed (km/h) | Delay (veh*s) | Fuel (L) | Completion |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| **Fixed-Time Baseline** | Reproduced | Default SUMO signal splits | $90.02 \pm 1.19$ | $28.21 \pm 0.45$ | $12,373.2 \pm 312$ | $23.18 \pm 0.4$ | 100% |
| **Coordinated Adaptive**| Reproduced | Dynamic Queue Offset heuristic | $\mathbf{49.87 \pm 2.34}$ | $\mathbf{37.98 \pm 0.82}$ | $\mathbf{5,836.8 \pm 245}$ | $\mathbf{18.44 \pm 0.3}$ | 100% |
| **Double-DQN (Stage A)**| Reproduced | `checkpoints/p6/dqn_stage_a_best.json` | $56.64 \pm 2.10$ | $31.46 \pm 0.68$ | $8,024.4 \pm 341$ | $20.35 \pm 0.3$ | 100% |
| **PPO (Stage A)** | Reproduced | `checkpoints/p6/ppo_stage_a_best.json` | $85.50 \pm 5.52$ | $25.56 \pm 0.94$ | $12,163.6 \pm 489$ | $23.76 \pm 0.5$ | 100% |

- **Integrity**: Every seed contains identical vehicle departure schedules and routes. Zero data leakage across seeds.

---

### 3. Audit: Series 4B (Observation Dimensionality Ablation)

- **Research Question**: Does expanding local observation from 4D (queue + phase) to 8D (+ wait time, speed) and 14D (+ upstream inflow, platoons, emergency flag) improve coordination?
- **Artifacts**: 30 checkpoints in `checkpoints/phase4/final_150ep/series_4b_*.json`, 300 evaluation records in `outputs/experiments/phase4/final_150ep/series_4b_observation_space/`.
- **Status**: **FROZEN & FULLY CERTIFIED**.
- **Key Statistical Finding (Variance Decomposition Audit)**:
  An independent statistical audit revealed that **65.2% to 98.9% of total variance is driven by the training seed** rather than the observation dimensionality:

$$\text{Variance Source:}\quad \text{Training Seed (Model-Level)} \gg \text{Evaluation Seed} > \text{Residual}$$

  - Evaluation-level comparisons ($N=50$) showed false statistical significance ($p < 0.001$) due to **pseudoreplication**.
  - Proper model-level paired analysis ($N=5$ checkpoints, $df=4$) demonstrated:
    - MAPPO 14D vs 8D: Diff = $+1.83\,\text{s}$, $t(4) = 0.281$, $p = 0.793$ (Not statistically significant).
    - MAPPO 14D vs 4D: Diff = $-4.90\,\text{s}$, $t(4) = -0.562$, $p = 0.604$ (Not statistically significant).
    - Linear Mixed-Effects Model (LMM) with random intercepts for training seed confirms that training initialization dominates sample variation.

---

### 4. Audit: Series 4C (Reward Coupling Mechanism Ablation)

- **Research Question**: How does the cooperative reward coupling coefficient $\beta \in [0.0, 1.0]$ in $r_j = (1-\beta) r_j^{\text{local}} + \beta R^{\text{global}}$ affect corridor progression vs cross-street starvation?
- **Experimental Design**:
  - 5 coupling betas: $\beta \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$
  - 5 training seeds per beta: $101, 102, 103, 104, 105$
  - 150 training episodes per run $\implies 25 \times 150 = 3{,}750$ total training episodes
  - 10 confirmatory evaluation seeds per checkpoint $\implies 250$ total evaluations
- **Actual Measured State**:

| Run Key | Beta ($\beta$) | Training Seed | Checkpoint SHA-256 | Training Episodes | Evaluations Completed | Status |
|---|:---:|:---:|---|:---:|:---:|:---:|
| `beta_000_seed101` | 0.00 | 101 | `43277318c3c250a1...` | 150 / 150 | 10 / 10 | **COMPLETED** |
| `beta_000_seed102` | 0.00 | 102 | `c84ab4a1f5efc3df...` | 150 / 150 | 10 / 10 | **COMPLETED** |
| `beta_000_seed103` | 0.00 | 103 | `35c3d2da3e55c110...` | 150 / 150 | 10 / 10 | **COMPLETED** |
| `beta_000_seed104` | 0.00 | 104 | N/A | 2 / 150 | 0 / 10 | **READY TO RESUME** |
| Runs 5–25 | 0.00–1.00 | 101–105 | N/A | 0 / 150 | 0 / 10 | **PENDING** |

- **Verification Summary**:
  - Total Runs Completed: **3 / 25**
  - Total Evaluations Completed: **30 / 250**
  - Checkpoints Verified Valid on Disk: 3 (each 2,412,800 bytes with complete `.history.json` sidecars).
  - All 30 completed evaluation JSON files verified complete with valid schemas.

---

### 5. Audit: Series 4E (Passenger-Weighted Reward Formulation)

- **Research Question**: Does scaling reinforcement learning reward penalties by vehicle passenger occupancy (BMTC bus = 45 passengers vs passenger car = 1.5 passengers) reduce corridor-wide Passenger-Hours of Delay (PHD)?
- **Status**: **COMPLETED & CERTIFIED**.
- **Results**:
  - Matched-pairs evaluation across 5 training seeds $\times$ 10 evaluation seeds = 100 evaluations total.
  - **Transit Signal Priority (TSP) Grant Rate**: Increased from $36.7\%$ (delay-centric) to **$88.4\%$** (passenger-weighted).
  - **Passenger-Hours of Delay (PHD)**: Reduced by **14.2%** under high-transit demand scenarios.
  - Checkpoint integrity: All 10 models verified intact.
