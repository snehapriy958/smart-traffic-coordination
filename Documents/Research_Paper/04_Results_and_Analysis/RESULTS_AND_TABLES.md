# Authoritative Results, Statistical Tables & Empirical Findings

**Document ID:** HTC-RESEARCH-RESULTS  
**Target Publication Venues:** IEEE Transactions on Intelligent Transportation Systems (T-ITS) / Transportation Research Part C  
**Classification:** Master Scientific Evidence Package & Statistical Results  

---

## 1. Master 10-Seed Comparative Benchmark Evaluation

All four controllers were evaluated across exactly 10 paired stochastic evaluation seeds ($1 \dots 10$) using identical vehicle insertion schedules, driver imperfection parameters, and network topologies under a 15-minute simulation horizon ($T = 900.0\text{ s}$).

### Table 1: Master Corridor Benchmark Performance Matrix ($N = 10$ seeds per controller)

| Performance Metric | Fixed-Time Baseline | Coordinated Adaptive | Double-DQN (Dueling) | PPO (Actor-Critic) |
| :--- | :---: | :---: | :---: | :---: |
| **Corridor Travel Time (s)** | $90.02 \pm 1.26$ | $\mathbf{49.87 \pm 2.46}$ | $56.64 \pm 2.22$ | $85.50 \pm 5.82$ |
| *Relative Change vs Baseline* | — | $\mathbf{-44.60\%}$ | $\mathbf{-37.08\%}$ | $-5.02\%$ |
| *Paired $t$-test ($df=9$)* | — | $t = -59.25$ | $t = -45.57$ | $t = -2.42$ |
| *p-value (Raw)* | — | $\mathbf{5.60 \times 10^{-13}}$ | $\mathbf{5.90 \times 10^{-12}}$ | $0.0384$ |
| *p-value (Bonferroni $\alpha=0.0167$)* | — | $\mathbf{1.68 \times 10^{-12}}$ (Sig.) | $\mathbf{1.77 \times 10^{-11}}$ (Sig.) | $0.1153$ (Not Sig.) |
| *Cohen's Effect Size ($d_z$)* | — | $\mathbf{18.74}$ (Huge) | $\mathbf{14.41}$ (Huge) | $0.77$ (Medium) |
| **Completed Corridor Trips** | $109.0 \pm 0.0$ | $109.0 \pm 0.0$ | $109.0 \pm 0.0$ | $109.0 \pm 0.0$ |
| *Total Network Arrivals (Vehicles)* | $378.0$ | $378.0$ | $378.0$ | $378.0$ |
| **Cumulative Delay ($\text{veh}\cdot\text{s}$)** | $12{,}373.2 \pm 135.1$ | $\mathbf{5{,}836.8 \pm 296.5}$ | $8{,}024.4 \pm 284.9$ | $12{,}163.6 \pm 896.6$ |
| *Relative Change vs Baseline* | — | $\mathbf{-52.83\%}$ | $\mathbf{-35.15\%}$ | $-1.69\%$ |
| **Average Corridor Speed (km/h)** | $28.21 \pm 0.37$ | $\mathbf{37.98 \pm 0.26}$ | $31.46 \pm 0.44$ | $25.56 \pm 0.91$ |
| *Relative Change vs Baseline* | — | $\mathbf{+34.66\%}$ | $\mathbf{+11.55\%}$ | $-9.37\%$ |
| **$\text{CO}_2$ Emissions (kg)** | $55.58 \pm 0.20$ | $\mathbf{42.72 \pm 0.64}$ | $47.15 \pm 0.65$ | $55.03 \pm 1.70$ |
| *Relative Change vs Baseline* | — | $\mathbf{-23.14\%}$ | $\mathbf{-15.17\%}$ | $-0.98\%$ |
| **Fuel Consumption (L_petrol-eq)** | $23.99 \pm 0.08$ | $\mathbf{18.44 \pm 0.28}$ | $20.35 \pm 0.28$ | $23.76 \pm 0.73$ |
| *Relative Change vs Baseline* | — | $\mathbf{-23.15\%}$ | $\mathbf{-15.17\%}$ | $-0.98\%$ |

*Note: All values report Sample Mean $\pm$ Sample Standard Deviation ($s$). $N = 10$, degrees of freedom $df = 9$. Bonferroni threshold for 3 pairwise comparisons against baseline is $\alpha / 3 = 0.0167$.*

### Table 1b: Vehicle Fleet Composition & Microscopic Modal Split ($T = 900.0\text{ s}$)

| Microscopic Vehicle Class | SUMO Class (`vClass`) | Active HBEFA4 Emission Model | Network Departures ($N=378$) | Network Share (%) | Corridor Trips ($N=109$) | Corridor Share (%) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Motorcycles / Two-Wheelers** | `motorcycle` | `HBEFA4/MC_4S_gt250cc_preEuro` | 257 | $67.99\%$ | 73 | $66.97\%$ |
| **Passenger Cars** | `passenger` | `HBEFA4/PC_petrol_Euro-4` | 103 | $27.25\%$ | 31 | $28.44\%$ |
| **BMTC Public Transit Buses** | `bus` | `HBEFA4/UBus_Std_gt15-18t_Euro-VI_A-C` | 12 | $3.17\%$ | 2 | $1.83\%$ |
| **Heavy Commercial Trucks** | `truck` | `HBEFA4/RT_le7.5t_Euro-VI_A-C` | 5 | $1.32\%$ | 2 | $1.83\%$ |
| **Emergency Ambulances** | `emergency` | `HBEFA4/LCV_diesel_N1-III_Euro-6ab` | 1 | $0.26\%$ | 1 | $0.92\%$ |
| **Total Fleet** | — | — | **378** | **$100.00\%$** | **109** | **$100.00\%$** |

*Note: All 378 network departed vehicles successfully arrived at their destinations within the 900s simulation horizon (100% completion rate). Ambulances are an independent emergency class, not subsumed under heavy vehicles.*

---

## 2. Series 4B: Observation Space Ablation & Hierarchical Variance Decomposition

Series 4B evaluated the impact of state space representation ($\mathcal{O}_{8\text{D}}$ vs. $\mathcal{O}_{14\text{D}}$) across 5 independent training seeds ($101 \dots 105$) with 10 confirmatory evaluation seeds ($1 \dots 10$) each ($N = 50$ runs per configuration; 100 total runs).

### Table 2: Model-Level vs. Pooled Evaluation Breakdown

| Architecture | Training Seed | Evals ($N$) | Mean TT (s) | Sample SD (s) | Min TT (s) | Max TT (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **DQN 8D** | 101 | 10 | $47.92$ | $1.76$ | $45.69$ | $50.72$ |
| **DQN 8D** | 102 | 10 | $84.09$ | $0.80$ | $82.72$ | $85.57$ |
| **DQN 8D** | 103 | 10 | $52.33$ | $0.94$ | $51.27$ | $54.12$ |
| **DQN 8D** | 104 | 10 | $64.08$ | $0.98$ | $62.61$ | $65.41$ |
| **DQN 8D** | 105 | 10 | $51.50$ | $0.84$ | $50.31$ | $53.05$ |
| *DQN 8D Pooled* | *All (5 models)* | *50* | *$59.98$* | *$15.30$* | *$45.69$* | *$85.57$* |
| **DQN 14D** | 101 | 10 | $46.51$ | $1.77$ | $44.33$ | $49.27$ |
| **DQN 14D** | 102 | 10 | $40.75$ | $0.95$ | $39.51$ | $42.27$ |
| **DQN 14D** | 103 | 10 | $42.74$ | $0.95$ | $41.35$ | $44.18$ |
| **DQN 14D** | 104 | 10 | $83.69$ | $1.04$ | $82.35$ | $85.69$ |
| **DQN 14D** | 105 | 10 | $44.06$ | $0.78$ | $42.81$ | $45.28$ |
| *DQN 14D Pooled* | *All (5 models)* | *50* | *$51.55$* | *$15.48$* | *$39.51$* | *$85.69$* |

### Table 3: Hierarchical Variance Decomposition (Linear Mixed-Effects Model)

| Parameter / Statistical Test | Statistical Value | Methodological Interpretation |
| :--- | :---: | :--- |
| **Naive Pooled Two-Sample $t$-test** | $t = 3.63, \mathbf{p = 0.0004}$ | **SPURIOUS.** Treats $N=50$ as independent samples; ignores clustering. |
| **Between-Model Random Variance ($\sigma^2_{\text{model}}$)** | **$217.18 \text{ s}^2$** | Training seed stochasticity accounts for **$91.60\%$** of total variance. |
| **Residual Evaluation Variance ($\sigma^2_{\text{eval}}$)** | **$19.90 \text{ s}^2$** | Evaluation traffic noise accounts for only **$8.40\%$** of total variance. |
| **Intraclass Correlation Coefficient (ICC)** | **$0.916$** | Extreme intra-cluster correlation across evaluations of the same checkpoint. |
| **LMM Model-Level Fixed Effect ($\Delta_{14\text{D} - 8\text{D}}$)** | **$-8.43 \pm 5.56 \text{ s}$** | Difference in mean corridor travel time between 14D and 8D. |
| **LMM Wald Test Statistic & p-value** | $t = -1.52, \mathbf{p = 0.133}$ | **NOT STATISTICALLY SIGNIFICANT at model level** ($df=8$). |
| **Cluster Bootstrap (10,000 resamples) 95% CI** | **$[-24.11, +7.25] \text{ s}$** | 95% confidence interval crosses zero; confirms lack of significance. |

---

## 3. Series 4C: Cooperative Reward Coupling Ablation (Preliminary Empirical Status)

Series 4C evaluates MAPPO under varying cooperative reward coupling coefficients $\beta \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$.

### Table 4: Completed Runs Summary ($\beta = 0.00$, Uncoupled Baseline)

| Training Seed | Episodes Completed | Confirmatory Evals ($N$) | Mean TT (s) | Sample SD (s) | Min TT (s) | Max TT (s) | Checkpoint SHA-256 Verified |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 101 | 150 | 10 | $80.43$ | $1.66$ | $78.94$ | $84.64$ | YES (`27fe48d0e5...`) |
| 102 | 150 | 10 | $88.16$ | $0.79$ | $86.73$ | $89.16$ | YES (`e767c29ae7...`) |
| 103 | 150 | 10 | $99.38$ | $0.81$ | $98.49$ | $100.97$ | YES (`88ca384d14...`) |
| **Pooled $\beta = 0.00$** | **450** | **30** | **$89.32$** | **$7.99$** | **$78.94$** | **$100.97$** | **3 / 3 Verified** |

### Status of Remaining Ablation Matrix:
- **Completed:** 3 of 25 training runs; 30 of 250 evaluations.
- **Pending:** 22 runs ($\beta = 0.00$ seeds 104–105; $\beta \in \{0.25, 0.50, 0.75, 1.00\}$ with 5 seeds each).
- **Finding:** Uncoupled MAPPO ($\beta = 0.00$, $89.32 \text{ s}$) yields travel times indistinguishable from the Fixed-Time baseline ($90.02 \text{ s}$, $p = 0.68$). Full reward coupling ablation remains classified as in-progress future research.

---

## 4. Series 4E: Multi-Objective Transit Signal Priority (TSP) Audit & Retraction

Series 4E compared delay-centric vs. passenger-weighted reward formulations across 100 evaluation runs ($5 \text{ seeds} \times 10 \text{ evals} \times 2 \text{ formulations}$).

### Table 5: Authoritative Series 4E Multi-Seed Results ($N = 50$ per formulation)

| Metric | Delay-Centric Formulation | Passenger-Weighted Formulation | Absolute Difference ($\Delta$) | Statistical Significance |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Corridor Travel Time (s)** | $84.38 \text{ s}$ | $84.38 \text{ s}$ | $\mathbf{0.00 \text{ s}}$ | $p = 1.00$ (Identical) |
| **Passenger Hours of Delay (PHD)** | $3.86 \text{ PHD}$ | $3.86 \text{ PHD}$ | $\mathbf{0.00 \text{ PHD}}$ | $p = 1.00$ (Identical) |
| **Mean TSP Priority Requests** | $36.2 \text{ req}$ | $36.2 \text{ req}$ | $\mathbf{0.0 \text{ req}}$ | — |
| **Mean TSP Priority Grants** | $12.9 \text{ grants}$ | $12.9 \text{ grants}$ | $\mathbf{0.0 \text{ grants}}$ | — |
| **Overall Mean TSP Grant Rate** | **$36.66\%$** | **$36.66\%$** | $\mathbf{0.00\%}$ | $p = 1.00$ (Identical) |
| *Cherry-Picked Seed 105 Grant Rate* | *$88.35\%$* | *$88.35\%$* | *$0.00\%$* | *Single-Seed Outlier* |

*Retraction Notice: The previous narrative claim of an "88.4% TSP grant rate" was derived exclusively from training seed 105 ($88.35\%$). Across all 5 random training seeds, the true empirical average grant rate is 36.66%. Under deterministic evaluation, greedy action selection saturated identically across both formulations ($\Delta = 0.00$).*

---

## 5. Microscopic Tailpipe Emissions & Stoichiometric Validation

### Table 6: Environmental Stoichiometric Consistency Check

| Parameter | Theoretical Chemistry (DIN EN 228 Petrol) | SUMO Simulation Output (Fixed-Time Baseline) | Relative Error ($\delta$) |
| :--- | :---: | :---: | :---: |
| **Fuel Density ($\rho_{\text{fuel}}$)** | $0.750 \text{ kg/L}$ | $0.750 \text{ kg/L}$ (Configured) | $0.00\%$ |
| **Combustion Reaction Ratio** | $\text{C}_8\text{H}_{18} + 12.5 \, \text{O}_2 \to 8 \, \text{CO}_2 + 9 \, \text{H}_2\text{O}$ | HBEFA v4.2 Microscopic Factor | — |
| **Stoichiometric Conversion Yield** | **$2.3116 \text{ kg CO}_2 / \text{L petrol}$** | **$2.3164 \text{ kg CO}_2 / \text{L petrol}$** | **$0.208\%$** |

*Conclusion: The microscopic emissions and fuel consumption figures satisfy stoichiometric conservation of mass within $< 0.21\%$, confirming physical and numerical consistency.*
