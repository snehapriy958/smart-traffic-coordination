# Research Questions & Hypotheses

## 1. Research Questions (RQ)

- **RQ-1 (Travel Efficiency)**: Can adaptive queue-balancing heuristics or reinforcement learning agents significantly reduce corridor travel times and halting queue delays along a heterogeneous arterial corridor compared to optimized pre-timed coordination?
- **RQ-2 (Value vs. Policy RL)**: How do decentralized value-based RL (Dueling Double-DQN) and policy-gradient RL (Multi-Agent PPO) perform relative to domain-heuristic controllers when subjected to non-stationary multi-intersection queues?
- **RQ-3 (Safety Invariance)**: Can a deterministic runtime safety shield enforce 100% safety bounds (min/max green, yellow clearance, zero phase starvation) without degrading policy performance?
- **RQ-4 (Emissions & Energy)**: To what degree does arterial signal progression reduce carbon emissions (CO2) and fuel consumption in mixed-traffic fleets, and does the observed reduction satisfy theoretical combustion stoichiometry?

---

## 2. Research Hypotheses & Evidence Classifications

- **H1 (Efficiency Improvement)**: Coordinated Adaptive and Dueling Double-DQN controllers achieve statistically significant reductions in corridor travel time ($p < 0.0167$, Bonferroni-corrected) and cumulative queue delay compared to Fixed-Time control across matched random seeds.
  - **Classification: SUPPORTED (by Simulation Experimentation)**
  - *Empirical Evidence*: 
    - Coordinated Adaptive: $-44.60\%$ travel time ($p = 5.60 \times 10^{-13}, d_z = 18.74$), $-52.82\%$ cumulative delay ($p = 2.65 \times 10^{-13}, d_z = 20.37$).
    - Dueling Double-DQN: $-37.08\%$ travel time ($p = 5.90 \times 10^{-12}, d_z = 14.41$), $-35.13\%$ cumulative delay ($p = 2.83 \times 10^{-11}, d_z = 12.10$).
    - Both pass two-tailed paired $t$-test at $df = 9$ and Wilcoxon signed-rank test ($W = 0.0, p = 0.00195$).

- **H2 (PPO Coordination Bottleneck)**: Decentralized PPO without shared value baselines or centralized critics fails to achieve statistically significant improvement over Fixed-Time control across matched random seeds due to non-stationary multi-agent transition dynamics.
  - **Classification: SUPPORTED (by Simulation Experimentation)**
  - *Empirical Evidence*: 
    - Multi-Agent PPO travel time reduction is modest ($-5.02\%$, $85.50\text{ s}$ vs. $90.02\text{ s}$).
    - Raw $p$-value is $0.0384$, which fails significance under Holm-Bonferroni correction ($p_{\text{adj}} = 0.1153 > 0.05$).
    - Delay reduction is negligible ($-1.66\%, p = 0.5033$), and mean speed is significantly worse ($-9.37\%, p = 7.88 \times 10^{-5}$).

- **H3 (Zero Safety Violations)**: Enclosing the controller action space within an explicit state-machine safety shield guarantees zero clearance violations (minimum green $\ge 15\text{ s}$, maximum green $\le 60\text{ s}$, yellow $\ge 4\text{ s}$, all-red $\ge 2\text{ s}$, anti-starvation $\le 120\text{ s}$) across all evaluation seeds.
  - **Classification: SUPPORTED (in Microscopic Simulation); NOT YET TESTED (in Physical Field Deployment)**
  - *Empirical Evidence*: Across all 40 master benchmark runs ($36{,}000\text{ s}$ total simulation time, $7{,}200$ decision steps), exactly 0 clearance or starvation violations occurred.
  - *Scope Boundary*: Electrical/actuator fail-safe verification on physical NEMA TS2 / 2070 traffic signal control cabinets remains future work.

- **H4 (Stoichiometric Mass Conservation)**: Empirical simulation $\text{CO}_2$ emissions and volumetric fuel consumption under the HBEFA4 model satisfy stoichiometric carbon-mass conservation within $1.0\%$ of theoretical hydrocarbon combustion.
  - **Classification: SUPPORTED (in Simulation Physics Engine); NOT YET TESTED (via Real-World Tailpipe Sensors)**
  - *Empirical Evidence*: Empirical ratio is $2.3164\text{ kg CO}_2 / \text{L}_{\text{petrol-eq}}$ compared to theoretical pure octane combustion ($2.3116\text{ kg/L}$), yielding an error of $0.208\% < 1.0\%$.
  - *Scope Boundary*: On-road portable emissions measurement systems (PEMS) physical field testing remains future work.
