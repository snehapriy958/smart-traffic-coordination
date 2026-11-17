# Extended Experimental Validation Plan (10 Seeds)

## 1. Overview and Scientific Motivation

In Phase 4 and Phase 5, an extended 900-second simulation benchmark was conducted across four controllers:
1. **Fixed-Time Baseline**
2. **Coordinated Adaptive Controller**
3. **MARL DQN Controller (Stage A)**
4. **MARL PPO Controller (Stage A)**

The initial evaluation used $N = 3$ random seeds ($\text{Seeds } [1, 2, 3]$). While this provided initial evidence of performance trends, $N = 3$ offers only $df = 2$ degrees of freedom in paired hypothesis testing ($t_{\text{crit}} = 4.30265$ at $\alpha = 0.05$). Under such low statistical power, moderate effect sizes cannot achieve statistical significance, and sample variance can obscure controller behavior.

This plan outlines the experimental design, execution framework, statistical methodology, and fault-tolerance procedures required to scale the evaluation to **$N = 10$ random seeds** ($40$ total simulation runs) using seeds **`[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]`**.

> [!IMPORTANT]
> **Execution Gate:** In accordance with project safety constraints, this document defines the execution plan only. Execution will commence only upon explicit user approval.

---

## 2. Experimental Design and Scope

### 2.1 Configuration Matrix

| Parameter | Specification | Details |
|---|---|---|
| **Controllers Evaluated** | 4 | Fixed-Time Baseline, Coordinated Adaptive, MARL DQN, MARL PPO |
| **Random Seeds** | 10 | Seeds `[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]` |
| **Continuity** | Preserved | Seeds 1, 2, 3 are retained for direct comparison with the Phase 5 benchmark |
| **Simulation Duration** | 900 seconds | Covers Peak (0–300s), Shoulder (300–600s), Off-Peak (600–900s) |
| **Total Simulation Runs** | **40 runs** | 4 controllers $\times$ 10 seeds |
| **Total Injected Vehicles** | **15,120 vehicle-run instances** | 378 vehicles/run $\times$ 40 runs |
| **Network & Geometry** | Identical | [`sumo/silk_board/network/silk_board.net.xml`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/sumo/silk_board/network/silk_board.net.xml) |
| **Traffic Demand** | Identical | [`sumo/silk_board/demand/silk_board.rou.xml`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/sumo/silk_board/demand/silk_board.rou.xml) |
| **Checkpoints Evaluated** | Unchanged | `checkpoints/marl_dqn_corridor.json`, `checkpoints/marl_ppo_corridor.json` |

### 2.2 Paired-Demand Structure
For each seed $s \in \{1, \dots, 10\}$:
1. SUMO initializes stochastic driver imperfection and vehicle insertion timing using `--seed <s>`.
2. All 4 controllers face the **identical sequence of vehicle departures, route assignments, driver attributes, and insertion timings**.
3. This creates a strictly matched-pair experimental block:
   $$\text{Run}(c, s) \quad \text{for } c \in \{\text{Fixed}, \text{Adaptive}, \text{DQN}, \text{PPO}\}$$

---

## 3. Computational Resources and Runtime Estimation

Based on empirical benchmarks on the local Windows 11 host environment (Intel Core i7 / 16 GB RAM):

| Resource / Phase | Metric per Run | Total for 40 Runs |
|---|---|---|
| **TraCI Step Wall Time** | $\approx 26.0 - 32.0\text{ seconds}$ | $\approx 17.3 - 21.3\text{ minutes}$ |
| **Host CPU Utilization** | 1 logical core ($\approx 12 - 18\%$) | Sequential execution (no core oversubscription) |
| **Memory Footprint** | $\approx 250\text{ MB}$ (Python) + $\approx 140\text{ MB}$ (SUMO) | $< 500\text{ MB}$ persistent RAM |
| **Disk Storage (Artifacts)** | $\approx 45\text{ KB}$ JSON per run | $\approx 2.5\text{ MB}$ total directory size |

Execution will run sequentially to guarantee deterministic scheduling and eliminate CPU contention between parallel SUMO instances.

---

## 4. Artifact Separation and Directory Layout

To protect the integrity of historical benchmark data, extended evaluation results will be written to a dedicated, workspace-local directory structure:

```
outputs/
└── validation/
    └── 10seeds/
        ├── run_fixed_seed1.json
        ├── run_fixed_seed2.json
        ├── ...
        ├── run_adaptive_seed1.json
        ├── ...
        ├── run_dqn_seed1.json
        ├── ...
        ├── run_ppo_seed1.json
        ├── ...
        ├── eval_10seeds_raw_data.json
        └── eval_10seeds_summary.json
```

> [!NOTE]
> The historical artifact `extended_eval_results.json` will remain untouched as the official 3-seed historical record.

---

## 5. Metrics Collection Specification

For each simulation run, the following metrics will be collected and recorded at both overall and regime levels:

### 5.1 System-Wide Performance Metrics
- **Departed Vehicles ($N_{\text{dep}}$):** Total vehicles inserted onto the corridor network (378 expected).
- **Arrived Vehicles ($N_{\text{arr}}$):** Vehicles completing their trip and exiting the network.
- **Unfinished Trips ($N_{\text{unf}}$):** $N_{\text{unf}} = N_{\text{dep}} - N_{\text{arr}}$ (0 expected at $t=900\text{s}$).
- **Corridor Travel Time ($\bar{T}$):** Mean travel time (seconds) across the 109 full-corridor trips ($J_1 \to J_2 \to J_3$).
- **Average Corridor Speed ($\bar{v}$):** Mean space-mean speed ($\text{km/h}$) across all vehicles.
- **Average Waiting Time ($\bar{W}$):** Mean accumulated vehicle waiting time ($v < 0.1\text{ m/s}$).
- **True Cumulative Delay:** Integral of queued vehicles over time: $\sum Q \cdot \Delta t$ ($\text{veh}\cdot\text{s}$).
- **Environmental Impact:** Cumulative $\text{CO}_2$ emissions (kg) and fuel consumption (liters at $0.750\text{ kg/L}$).

### 5.2 Regime-Specific Breakdown
Metrics will be aggregated across three operational demand regimes:
1. **Peak Regime ($0 \le t < 300\text{s}$):** Saturated high-density arterial arrival flow.
2. **Shoulder Regime ($300 \le t < 600\text{s}$):** Moderate transition volume with cross-street feeder bursts.
3. **Off-Peak Regime ($600 \le t \le 900\text{s}$):** Zero departures; residual queue clearance.

### 5.3 Controller Action and Starvation Diagnostics
To evaluate controller behavior:
- Total phase switches per junction ($J_1, J_2, J_3$).
- Action distribution counts (`KEEP`, `SWITCH`, `EXTEND`).
- Starvation preemption event counts (`STARVATION_PREVENTION: Forced SWITCH`).
- Maximum continuous red time observed per approach.

---

## 6. Statistical Hypothesis Testing Framework

### 6.1 Hypotheses
For each candidate controller $c \in \{\text{Adaptive}, \text{DQN}, \text{PPO}\}$ evaluated against the Fixed-Time Baseline $b$:

- **Null Hypothesis ($H_0$):** The mean paired difference in metric $X$ (e.g. Travel Time) between controller $c$ and baseline $b$ is zero:
  $$H_0: \mu_d = 0, \quad \text{where } d_i = X_{c, i} - X_{b, i}$$
- **Alternative Hypothesis ($H_1$):** The mean paired difference is non-zero:
  $$H_1: \mu_d \ne 0 \quad (\text{two-tailed})$$

### 6.2 Parametric Test: Paired Student's $t$-Test
With $N = 10$ pairs:
- **Degrees of Freedom:** $df = N - 1 = 9$
- **Critical $t$-value ($\alpha = 0.05$):** $t_{\text{crit}} = \pm 2.26216$ (substantially more powerful than $df=2, t_{\text{crit}} = 4.30265$)
- **Sample Mean Difference:**
  $$\bar{d} = \frac{1}{N}\sum_{i=1}^N d_i$$
- **Sample Standard Deviation of Differences:**
  $$s_d = \sqrt{\frac{1}{N-1}\sum_{i=1}^N (d_i - \bar{d})^2}$$
- **Standard Error:**
  $$SE = \frac{s_d}{\sqrt{N}}$$
- **Test Statistic:**
  $$t = \frac{\bar{d}}{SE}$$
- **$95\%$ Confidence Interval:**
  $$\text{CI}_{95\%} = \left[ \bar{d} - 2.26216 \cdot SE, \; \bar{d} + 2.26216 \cdot SE \right]$$

### 6.3 Non-Parametric Test: Wilcoxon Signed-Rank Test
For non-parametric robustness:
- Differences $d_i = X_{c, i} - X_{b, i}$ are ranked by absolute magnitude $|d_i|$.
- Signed ranks $W^+$ and $W^-$ are summed:
  $$W = \min(W^+, W^-)$$
- With $N = 10$ and $\alpha = 0.05$ (two-tailed), the exact critical value is $W_{\text{crit}} = 8$. A test statistic $W \le 8$ rejects the null hypothesis.

---

## 7. Fault Tolerance, Process Isolation, and Error Handling

1. **Dynamic Ephemeral Port Allocation:** Each run binds to an available ephemeral loopback port in range $12000 - 19999$ to prevent TraCI socket collisions.
2. **Watchdog Timeout:** Runs are guarded by a 180-second timeout. Any hung process is terminated via `taskkill`.
3. **Automatic Retry:** Up to 2 retries per seed if a socket exception occurs.
4. **Process Cleanup Verification:** Ensures zero lingering `sumo.exe` processes exist before launching the next seed.
5. **Memory Cleanup:** Invokes `gc.collect()` after each run.

---

## 8. Automated Runner Specification

A self-contained execution script [`scripts/run_10seed_validation.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/scripts/run_10seed_validation.py) will be deployed when approval is granted.

### CLI Interface
```powershell
# Run full 10-seed experiment across all 4 controllers (40 runs)
python scripts/run_10seed_validation.py --seeds 1 2 3 4 5 6 7 8 9 10 --output-dir outputs/validation/10seeds
```

---

## 9. Next Steps and Execution Triggers

This validation plan is fully reconciled and ready for implementation. Execution will commence only after user authorization.
