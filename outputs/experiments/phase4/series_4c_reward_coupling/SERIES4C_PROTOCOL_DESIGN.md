# Series 4C: Cooperative Reward Coupling Mechanism Ablation
## Confirmatory Experimental Protocol & Implementation Audit

**Author:** Senior Reinforcement Learning Researcher & Traffic Simulation Engineer  
**Project:** Smart Traffic Coordination System — Central Silk Board Corridor ($J_1 \to J_2 \to J_3$)  
**Status:** Protocol Specification & Code Audit (Ready for Execution)  
**Parent Study:** Phase 4 Confirmatory MARL Pipeline  

---

## 1. Existing Reward Implementation Analysis

### 1.1 Architecture & Reward Ingestion
The multi-agent system controls three coordinated intersections ($J_1$: Silk Board Entry, $J_2$: Madiwala Central, $J_3$: HSR Layout Exit) along the Hosur Road arterial corridor.
Reward signals are computed at every decision interval ($\Delta t = 5.0\text{ s}$) via `MultiIntersectionReward` in [`traffic_service/ai/env.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/env.py#L197-L410) and ingested by `MARLCorridorController` in [`traffic_service/ai/marl_controller.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/marl_controller.py).

During training in [`scripts/train_phase4_150ep.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/scripts/train_phase4_150ep.py#L212-L238):
1. Telemetry from the SUMO simulation is extracted as raw observation dictionaries `raw_obs_next`.
2. `reward_fn.compute_mixed_rewards(...)` evaluates both local and corridor-wide metrics, returning `mixed_r: Dict[str, float]` and `breakdowns: Dict[str, RewardBreakdown]`.
3. For **MAPPO**, scalar reward `mixed_r[j]` is stored in each agent's PPO rollout buffer alongside local observation $s_j \in \mathbb{R}^{14}$, global corridor state $s_{\text{corridor}} \in \mathbb{R}^{42}$, discrete action $a_j \in \{0, 1, 2\}$, action mask, and log probability.
4. For **Double-DQN**, transition $(s_j, a_j, \text{mixed\_r}[j], s'_j, \text{done})$ is pushed into each agent's experience replay buffer.

### 1.2 Local Reward Computation ($R_{\text{local}, j}$)
In [`traffic_service/ai/env.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/env.py#L348-L384), each junction $j$ evaluates localized traffic conditions:
$$R_{\text{local}, j} = \text{clip}\Big(r_{q, j} + r_{w, j} + r_{s, j} + r_{c, j} + r_{\text{chatter}, j} + r_{\text{emerg}, j} + r_{\text{prog}, j}, -10.0, 10.0\Big)$$

Where:
- **Queue penalty:** $r_{q, j} = -w_{\text{queue}} \cdot \min\left(\frac{q_j}{30.0}, 1.0\right)$ with $w_{\text{queue}} = 0.35$.
- **Wait time penalty:** $r_{w, j} = -w_{\text{wait}} \cdot \min\left(\frac{\text{wait}_j}{200.0}, 1.0\right)$ with $w_{\text{wait}} = 0.30$.
- **Speed incentive:** $r_{s, j} = +w_{\text{speed}} \cdot \min\left(\frac{v_j}{40.0}, 1.0\right)$ with $w_{\text{speed}} = 0.15$.
- **Emission penalty:** $r_{c, j} = -w_{\text{emissions}} \cdot \min\left(\frac{\text{CO2}_{g, j}}{5.0}, 1.0\right)$ with $w_{\text{emissions}} = 0.10$.
- **Chatter penalty:** $r_{\text{chatter}, j} = -0.05$ if phase switched under elective switch action (`ACTION_SWITCH`), preventing high-frequency oscillation.
- **Emergency penalty:** $r_{\text{emerg}, j} = -1.0$ if an active emergency vehicle is halted in queue.
- **Platoon progression incentive:** $r_{\text{prog}, j} \in [-0.5, 0.5]$ rewarded when arriving coordinated platoons are served on green.

### 1.3 Global Reward Computation ($R_{\text{global}}$)
In [`traffic_service/ai/env.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/env.py#L319-L343), global coordination is not merely an average of local terms; it evaluates macro-corridor externalities:
$$R_{\text{global}} = \text{clip}\Big(r_{\text{throughput}} + r_{\text{cdelay}} + r_{\text{starve}} + r_{\text{flow}}, -10.0, 10.0\Big)$$

Where:
- **Corridor throughput bonus:** $r_{\text{throughput}} = +w_{\text{throughput}} \cdot \min\left(\frac{\Delta_{\text{completed\_trips}}}{5.0}, 1.0\right)$ with $w_{\text{throughput}} = 0.50$.
- **Aggregate corridor queue penalty:** $r_{\text{cdelay}} = -w_{\text{cdelay}} \cdot \min\left(\frac{\sum_{j} q_j}{60.0}, 1.0\right)$ with $w_{\text{cdelay}} = 0.50$.
- **Anti-starvation penalty:** $r_{\text{starve}} = -w_{\text{starvation}} \cdot \min\left(\sum_{j} \text{penalty}_j, 2.0\right)$ with $w_{\text{starvation}} = 0.50$, triggered when any individual approach exceeds maximum tolerable red duration ($60.0\text{ s}$).
- **Upstream arterial flow integrity:** $r_{\text{flow}} = -0.30$ if entry junction $J_1$ holds an arterial queue ($\ge 5\text{ veh}$) on red while corridor trips are zero, penalizing artificial gating.

### 1.4 Normalization, Scaling, and Bounds
- Individual components are normalized to $[0, 1]$ before weight application.
- Component weights sum to structured trade-offs ($\sum w \approx 1.0 - 1.5$).
- Both $R_{\text{local}, j}$ and $R_{\text{global}}$ are individually hard-clipped to $[-10.0, 10.0]$.
- The combined mixed reward $R_{\text{mixed}, j}$ is clipped to $[-15.0, 15.0]$.
- This bounding ensures numerical stability, prevents exploding advantages in PPO, and avoids gradient saturation in deep networks.

---

## 2. Proposed $\beta$ Formulation vs. Codebase Implementation

### 2.1 Theoretical Formulation
The conceptual reward coupling formulation is:
$$R_{\text{mixed}, j} = (1 - \beta) \cdot R_{\text{local}, j} + \beta \cdot R_{\text{global}}$$
across candidate values:
$$\beta \in \{0.0, 0.25, 0.50, 0.75, 1.0\}$$

### 2.2 Codebase Reality & Reconciliation
1. **Parameter Name:**  
   In [`traffic_service/ai/env.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/env.py#L43), the parameter is defined in `RewardWeights` as `alpha: float = 0.5`.  
   In [`scripts/train_phase4_150ep.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/scripts/train_phase4_150ep.py#L121), the training function accepts `reward_coupling_beta: float = 0.50` and initializes:
   ```python
   reward_weights = RewardWeights(
       alpha=reward_coupling_beta,
       passenger_weighted=passenger_weighted,
   )
   ```
   Thus, $\beta$ and $\alpha$ are mathematically identical and cleanly mapped.

2. **Peer-Averaging vs. Macro-Corridor Objective:**  
   The Master Record Section 21.6.1 mentions $R_{\text{global}} = \frac{1}{|\mathcal{N}_j|} \sum_{k} r_k$. However, the codebase implementation in `compute_mixed_rewards()` uses the macro-corridor objective ($r_{\text{throughput}} + r_{\text{cdelay}} + r_{\text{starve}} + r_{\text{flow}}$).
   - *Audit Decision:* Retain `compute_mixed_rewards()` macro-corridor formulation. It directly penalizes network-level bottlenecks and starvation while rewarding end-to-end trips, and preserves exact compatibility with the Series 4B baseline ($\beta = 0.50$).

3. **Boundary Verification:**  
   - $\beta = 0.0$: $R_{\text{mixed}, j} = R_{\text{local}, j}$ (Purely decentralized, selfish agents).
   - $\beta = 1.0$: $R_{\text{mixed}, j} = R_{\text{global}}$ (Purely centralized team reward).
   - $\beta = 0.50$: Nominal baseline balancing local intersection clearing with corridor green waves.

---

## 3. Experimental Design & Sample Allocation

### 3.1 Primary Configuration: MAPPO Observation Space 14D
Following the Master Record (Section 21.3.2 and 21.6.2) and the conclusive Series 4B findings:
- **Algorithm:** MAPPO (Centralized Training with Decentralized Execution).
- **Observation Space:** 14-dimensional normalized state vector ($d = 14$).
- **Safety Shield:** Active (`ActionFilter` + `StarvationTracker`).
- **Communication:** Active (Corridor Inter-Junction Hub).
- **Episode Budget:** 150 episodes per training run ($1{,}200\text{ s}$ per episode, $5.0\text{ s}$ decision step).

### 3.2 Sample Structure
- **Coupling Levels ($B = 5$):** $\beta \in \{0.0, 0.25, 0.50, 0.75, 1.0\}$.
- **Training Seeds ($T = 5$):** $S_{\text{train}} = \{101, 102, 103, 104, 105\}$.
- **Independent Trained Models ($N_{\text{models}}$):** $5 \times 5 = \mathbf{25\text{ checkpoints}}$.
- **Confirmatory Evaluation Seeds ($E = 10$):** $S_{\text{eval}} = \{1, 2, \dots, 10\}$.
- **Evaluation Duration:** $900.0\text{ simulation seconds}$ per run.
- **Total Confirmatory Evaluations:** $25\text{ models} \times 10\text{ scenarios} = \mathbf{250\text{ evaluation records}}$.

### 3.3 Dual-Algorithm Consideration (MAPPO vs. Double-DQN)
- Master Record Section 21.3.2 allocates 25 training runs for Series 4C (MAPPO only).
- Expanding to Double-DQN would require $50$ training runs ($7{,}500$ episodes) and $500$ evaluations.
- *Recommendation:* Execute the 25 MAPPO runs as the primary confirmatory series. If DQN is evaluated, it should be framed as a secondary sensitivity cohort, acknowledging the bimodal convergence risk identified in Series 4B.

---

## 4. Compute Time & Resource Budget

| Phase | Runs / Items | Duration per Run | Measured Throughput | Total Estimated Time |
| :--- | :--- | :--- | :--- | :--- |
| **Clean Training** | 25 models ($3{,}750$ ep) | 150 episodes ($1{,}200\text{ s}$ sim) | $\approx 12.8\text{ s}$ / episode | $\approx 13.3\text{ hours}$ |
| **Confirmatory Eval** | 250 runs | $900\text{ s}$ simulation | $\approx 8.7\text{ s}$ / eval | $\approx 36.3\text{ minutes}$ |
| **Statistical Analysis** | 1 pipeline | All 250 JSONs | $\approx 10\text{ s}$ | $\approx 1\text{ minute}$ |
| **Total Pipeline** | **25 trains + 250 evals** | — | — | **$\approx 14.0\text{ hours}$** |

*Hardware Constraints:*  
- Dedicated single sequential worker to eliminate Windows SUMO port/RAM race conditions.
- Available RAM threshold strictly guarded at $\ge 1.2\text{ GB}$.
- Checkpoints saved atomically with SHA256 integrity validation and `.history.json` sidecars.

---

## 5. Hypotheses & Multi-Objective Evaluation Metrics

### 5.1 Scientific Hypotheses
1. **Hypothesis $H_1^{(4C)}$ (Corridor Coordination Advantage):**  
   Nominal cooperative coupling ($\beta = 0.50$) achieves significantly higher completed corridor trips and lower mean corridor travel time compared to selfish local control ($\beta = 0.0$), demonstrating the causal necessity of cooperative reward signals ($p < 0.0125$, Holm-Bonferroni adjusted).
2. **Hypothesis $H_2^{(4C)}$ (Credit Assignment Degradation):**  
   Pure global reward ($\beta = 1.0$) increases policy gradient variance and induces free-rider dynamics, leading to higher travel time variance and lower throughput compared to balanced coupling ($\beta = 0.50$).
3. **Hypothesis $H_3^{(4C)}$ (Arterial vs. Cross-Street Equity Trade-off):**  
   Increasing $\beta \to 1.0$ disproportionately favors Hosur Road arterial progression over cross-street traffic, resulting in a statistically significant increase in Cross-Street Delay Gini Coefficient ($G_{\text{delay}}$) and Side-to-Arterial Delay Ratio ($R_{\text{side/art}}$).

### 5.2 Metric Definitions

#### A. Efficiency & Network Flow
- **Mean Corridor Travel Time:** Mean, median, standard deviation, and 95th percentile ($p95$).
- **Total Corridor Trips Completed:** Total vehicles successfully traversing $J_1 \to J_2 \to J_3$.
- **Mean Corridor Speed (km/h):** Harmonic average speed across Hosur Road edges.
- **Cumulative Vehicle Delay (veh-s):** Total seconds spent below free-flow speed.

#### B. Junction Fairness & Equity (Mandated Priority)
- **Cross-Street Delay Gini Coefficient ($G_{\text{delay}}$):**
  $$G_{\text{delay}} = \frac{\sum_{i=1}^{n} \sum_{k=1}^{n} |D_i - D_k|}{2 n \sum_{i=1}^{n} D_i}$$
  computed across all 6 corridor approaches (Hosur Road arterial + cross-street approaches for $J_1, J_2, J_3$).
- **Side-Street to Arterial Delay Ratio ($R_{\text{side/art}}$):**
  $$R_{\text{side/art}} = \frac{D_{\text{side, } J_1} + D_{\text{madiwala, } J_2} + D_{\text{side, } J_3}}{D_{\text{hosur, } J_1} + D_{\text{hosur, } J_2} + D_{\text{hosur, } J_3}}$$
- **Junction Delay Disparity:** Variance of cumulative delay across the three intersection controllers:
  $$\sigma_J^2 = \text{Var}(D_{J_1}, D_{J_2}, D_{J_3})$$
- **Starvation Breaches:** Count of episodes or cycles where any queued approach exceeds the $60.0\text{ s}$ red threshold.

#### C. Travel Time Reliability & Emissions
- **Planning Time Index ($\text{PTI}$):** $t_{p95} / t_{\text{free-flow}}$ (where $t_{\text{free-flow}} = 27.5\text{ s}$).
- **Buffer Index ($\text{BI}$):** $\frac{t_{p95} - t_{\text{mean}}}{t_{\text{mean}}} \times 100\%$.
- **Tail Risk ($p99$):** 99th-percentile travel time.
- **Environmental:** Total $\text{CO}_2$ emissions (kg) and total fuel consumption (liters).

### 5.3 Inferential Statistical Architecture
Learning from the Series 4B audit:
- **Unit of Randomization:** The trained neural model ($N = 5$ per $\beta$). Evaluation seeds represent repeated measurements nested within trained models.
- **Hierarchical Linear Model:**
  $$Y_{bte} = \mu + \beta_b + u_{t(b)} + v_e + \epsilon_{bte}$$
- **Multiplicity Control:** 4 confirmatory comparisons against nominal baseline ($\beta = 0.50$) using monotonic Holm-Bonferroni step-down:
  1. $\beta = 0.0$ vs $\beta = 0.50$
  2. $\beta = 0.25$ vs $\beta = 0.50$
  3. $\beta = 0.75$ vs $\beta = 0.50$
  4. $\beta = 1.0$ vs $\beta = 0.50$
- **Effect Sizes:** Paired Cohen's $d_z$ at the model level ($df = 4$) and $95\%$ BCa bootstrap confidence intervals ($10{,}000$ resamples).

---

## 6. Exact File Structure & Pipeline Architecture

```
outputs/experiments/phase4/
├── final_150ep/
│   ├── series_4b_observation_space/     [FROZEN Series 4B Artifacts]
│   └── series_4c_reward_coupling/       [Planned Confirmatory Series 4C]
│       ├── eval_mappo_beta_000_train101_eval1.json ... (250 files)
│       ├── series_4c_summary.json
│       ├── series_4c_statistical_analysis.json
│       └── series_4c_final_audit.md
├── series_4c_reward_coupling/
│   └── SERIES4C_PROTOCOL_DESIGN.md      [This Protocol Document]

checkpoints/phase4/final_150ep/
├── series_4b_*.json                     [FROZEN Series 4B Checkpoints]
├── series_4c_mappo_beta_000_seed101.json
├── series_4c_mappo_beta_000_seed101.history.json
└── ... (25 checkpoints + 25 history sidecars)

tests/
├── test_series4c_reward_coupling.py     [Verified unit tests for beta invariants & Gini]
└── test_phase4_ablation_mechanisms.py

scripts/
├── train_series4c_master.py             [Sequential single-worker execution harness]
└── analyze_series4c_statistical_validation.py
```

---

## 7. Pre-Execution Verification Suite

Before launching the 14-hour training run, the following verification suite must pass:
1. **Mathematical Invariant Test:**  
   `test_reward_coupling_beta_zero_pure_local`: Confirms $R_{\text{mixed}} \equiv R_{\text{local}}$ at $\beta = 0.0$.
2. **Global Sharing Test:**  
   `test_reward_coupling_beta_one_pure_global`: Confirms $R_{\text{mixed}, J_1} \equiv R_{\text{mixed}, J_2} \equiv R_{\text{mixed}, J_3} \equiv R_{\text{global}}$ at $\beta = 1.0$.
3. **Convex Linearity Test:**  
   `test_reward_coupling_convex_combination_linearity`: Confirms exact interpolation across $\beta \in [0.0, 0.25, 0.50, 0.75, 1.0]$.
4. **Numerical Stability Test:**  
   `test_reward_numerical_bounds_under_extreme_traffic`: Verifies strict bounding $[-15.0, 15.0]$ without NaNs/Infs under 500-vehicle extreme congestion.
5. **Equity Function Test:**  
   `test_gini_coefficient_exact_properties`: Confirms Gini is $0.0$ for identical delays and bounded for extreme inequality.
6. **Dry-Run Training Test:**  
   Execute 1 episode with dummy seed to verify checkpoint saving, `.history.json` generation, SHA256 hashing, and memory footprint.

*(Status: Tests 1–5 already implemented and verified passing in `tests/test_series4c_reward_coupling.py`).*

---

## 8. Risks, Mitigations & Decision Log

| Risk | Consequence | Mitigation Strategy |
| :--- | :--- | :--- |
| **Credit Assignment Noise at $\beta = 1.0$** | High policy variance, free-rider problem, sluggish convergence | Centralized critic $V(s_{\text{corridor}})$ in MAPPO stabilizes value estimation; compare policy loss curves in `.history.json`. |
| **Side-Street Starvation at high $\beta$** | Side-street queues exceed $60\text{ s}$ as agents maximize arterial throughput | Active deterministic safety shield (`StarvationTracker`) enforces maximum red caps independently of agent policy. |
| **RAM Exhaustion on Windows** | OS memory crash during 14-hour run | Hard RAM safeguard at $1.2\text{ GB}$ in training harness; explicit `gc.collect()` and single sequential worker. |
| **Collision with Preliminary 75-step Artifacts** | Nov 10 preliminary files in `outputs/experiments/phase4/series_4c_reward_coupling/` could contaminate confirmatory analysis | Confirmatory run strictly routes all 150-ep artifacts to `outputs/experiments/phase4/final_150ep/series_4c_reward_coupling/` and stamps `"regime": "FINAL_CONFIRMATORY_150EP"`. |
| **Pseudoreplication in Statistics** | Inflated degrees of freedom ($df=49$ vs $df=4$) | Statistical analysis mandates model-level paired aggregation ($N=5$ independent checkpoints per condition) and cluster bootstrap. |
