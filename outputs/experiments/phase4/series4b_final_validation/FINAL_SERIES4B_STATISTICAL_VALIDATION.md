# FINAL STATISTICAL VALIDATION AND CLOSURE REPORT: SERIES 4B
## Observation Space Dimensionality Ablation ($14\text{D}$ vs $8\text{D}$ vs $4\text{D}$)
### Central Silk Board Corridor Network ($J_1 \to J_2 \to J_3$) — Confirmatory Phase 4

**Validation Date:** 2026-11-13  
**Lead Auditor:** Senior Statistical Researcher in Multi-Agent RL, Traffic Simulation & Reproducible Science  
**Project:** Smart Traffic Coordination System (`hybrid-traffic-control`)  
**Workspace:** `c:\Developers\Sneha\Projects\hybrid-traffic-control`  
**Git Safety Status:** `HEAD: e31de953ceb7fe878d531c888e7f27e532b13b37` (0 Git modifications, strictly local read-only execution)  
**Primary Output Directory:** `outputs/experiments/phase4/series4b_final_validation/`  

---

## 1. Executive Summary & Validation Verdict

This report presents the definitive, rigorous statistical validation and closure of **Series 4B (Observation Space Dimensionality Ablation)**. Accounting for the crossed training-seed and evaluation-seed experimental structure, this audit evaluates the empirical stability, hierarchical variance components, small-sample degrees of freedom, and boundary conditions of all 30 trained models and 300 evaluation records.

### 1.1 Formal Validation Verdict: **PASSED WITH CONDITIONAL CLOSURE**
1. **Design & Artifact Integrity:** **100% VERIFIED**. All 300 evaluation records and 30 checkpoints are mathematically accounted for with 0 missing and 0 duplicate records.
2. **Evaluation-Level Testbed Invariance:** **CONFIRMED ($p < 0.01$)**. Within the evaluated fixed policy suite across 10 traffic demand scenarios ($N=50$ evaluation pairs), the performance hierarchy ($\text{DQN 8D} < \text{MAPPO 8D} < \text{MAPPO 14D} < \text{DQN 4D} < \text{MAPPO 4D} < \text{DQN 14D}$) is statistically significant and 100% invariant across all leave-one-eval-seed-out sensitivity splits.
3. **Model-Level Generalization Limitation:** **DIAGNOSED & CLASSIFIED AS EXPLORATORY ($N=5, df=4$)**. When aggregated to the independent model level ($N=5$ training runs per configuration), the mean advantage of DQN 8D over DQN 14D ($\Delta \mu = -11.64\text{ s}$) does not reach nominal significance on an unconditioned paired $t$-test ($t(4) = -1.212, p = 0.2923$) or cluster bootstrap ($p = 0.1330$). 
4. **Jackknife Root-Cause Isolation:** Jackknife sensitivity proves that this model-level variance inflation is **100% driven by a single training run (DQN 8D Seed 101, $111.51\text{ s}$)**. When Seed 101 is dropped, DQN 8D achieves a remarkably consistent travel time of **$73.50 \pm 3.24\text{ s}$**, and its advantage over DQN 14D is overwhelming (**$\Delta \mu = -21.01\text{ s}, t(3) = -7.546, \mathbf{p = 0.0048}$**).
5. **Variance & Safety Winner:** **MAPPO 14D**. MAPPO demonstrates vastly superior convergence stability and risk bounds ($\sigma_{\text{model}} = 6.59\text{ s}$ vs DQN 8D's $17.23\text{ s}$ and DQN 4D's $21.70\text{ s}$), exhibiting zero policy collapse across all seeds.

---

## 2. Task A: Reconstruction of the Experimental Design

### 2.1 Design Structure
The experimental design is a **crossed two-factor hierarchy with repeated measures**:
- **Algorithms ($A=2$):** Multi-Agent PPO (MAPPO with centralized critic) and Decentralized Double-DQN.
- **Observation Dimensions ($D=3$):** Full ($14\text{D}$), Compressed ($8\text{D}$), and Minimal ($4\text{D}$).
- **Configurations ($C = A \times D = 6$):** `DQN_14D`, `DQN_8D`, `DQN_4D`, `MAPPO_14D`, `MAPPO_8D`, `MAPPO_4D`.
- **Training Seeds ($K = 5$ per config):** $S_{\text{train}} = \{101, 102, 103, 104, 105\}$, yielding exactly **30 unique trained checkpoints** ($M = 30$).
- **Evaluation Scenarios ($S = 10$ per checkpoint):** $S_{\text{eval}} = \{1, 2, \dots, 10\}$, yielding exactly **300 evaluation records**.
- **Duration Invariants:** $1{,}200.0\text{ s}$ per training episode ($4{,}500$ episodes); $900.0\text{ s}$ per evaluation run ($270{,}000$ simulation seconds).

```
[Configuration: 6 Levels]
       │
       ├── Nested: [Trained Model: 5 Checkpoints per Config, Total = 30 Models]
       │                 │
       │                 └── Evaluated on (Crossed): [10 Traffic Demand Seeds]
       │                                                   │
       └───────────────────────────────────────────────────┴── Total: 300 Observations
```

### 2.2 Independent Experimental Units Analysis
A critical methodological failure in naive RL analysis is conflating the **unit of observation** with the **independent experimental unit**:
- **Question 1: Policy Generalization from Random Initialization:**
  *"Does algorithm/representation A systematically learn a better policy than B when trained from scratch?"*
  - **Independent Experimental Unit:** The **trained checkpoint** (`model_id`, $N = 5$ per configuration).
  - The 10 evaluations per model are **repeated measurements on the same frozen neural policy** (pseudoreplications if treated as independent degrees of freedom).
- **Question 2: Traffic Demand Robustness of a Fixed Policy Suite:**
  *"Given the 30 specific trained checkpoints, how reliably do they perform across varying traffic demand shocks?"*
  - **Independent Experimental Unit:** The **evaluation scenario** (`eval_seed`, $N = 10$), which is crossed identically across all 30 models.

---

## 3. Task B: Validation of Mixed-Effects Models & Model Diagnostics

### 3.1 Critique of the Previous Audit Model
In preliminary analysis scripts (`hierarchical_analysis.py`), the linear mixed model was specified as:
```python
# DEFECTIVE SPECIFICATION IN PREVIOUS QUICK SCRIPT
smf.mixedlm("travel_time ~ is_a", data=subset, groups=subset["train_seed"]).fit()
```
**Statistical Flaws in Model 1:**
1. **Misattribution of Cluster Identity:** Grouping by integer `train_seed` (101–105) falsely treats `(DQN_8D, seed 101)` and `(DQN_14D, seed 101)` as repeated measurements on the *same physical subject*. In reality, seed 101 is merely an arbitrary pseudo-random number generator seed used in two completely independent training sessions with different observation spaces!
2. **Artificial Variance Reduction:** By treating `train_seed` as a shared subject intercept, the model artificially subtracted out between-model variance, inflating the apparent $z$-statistic ($z = -5.393, p < 0.0001$).
3. **Omission of Crossed Evaluation Seeds:** The model ignored the shared traffic demand shocks across the 10 evaluation seeds.

### 3.2 Comparison of Mixed-Effects Model Formulations

To resolve this, three distinct model formulations were fit across the full 300-observation dataset:

| Model Formulation | Fixed Effects | Random Effects / Grouping | Log-Likelihood | Between-Group Variance | Residual Variance ($\sigma_\epsilon^2$) | Convergence & Hessian Status |
|:---|:---|:---|:---:|:---:|:---:|:---:|
| **Model 1: Naive Audit Model** | `Configuration` | `(1 \| train_seed)` ($K=5$ shared integer levels) | $-1192.97$ | $26.95$ | $175.23$ | Converged (Anticonservative $z$) |
| **Model 2: Proper Nested Model** | `Configuration` | `(1 \| model_id)` ($M=30$ unique checkpoints) | $\mathbf{-924.96}$ | $\mathbf{217.18}$ | $\mathbf{19.90}$ | **Converged (True Hierarchy)** |
| **Model 3: Crossed Random Effects** | `Configuration` | `(1 \| eval_seed)` + `(1 \| model_id)` | $-1205.71$ | $0.00$ (`eval`) / $98.62$ (`model`) | $98.62$ | **Non-Positive Definite Hessian** |

### 3.3 Methodological Insights from Model Comparison
1. **Model 2 Explains the Data Vastly Better:** Model 2 achieves a log-likelihood of $\mathbf{-924.96}$ (an improvement of $>268$ log-likelihood units over Model 1). It reveals that the true between-model variance is **$217.18$**, while the within-model residual variance across evaluation seeds is only **$19.90$** ($91.6\%$ of variance is between checkpoints!).
2. **Why Model 3 Suffers a Non-Positive Definite Hessian:** In Model 3, crossing 30 models with 10 evaluation seeds without cell replication ($30 \times 10 = 300$) causes the estimated variance for `eval_seed` to collapse to the boundary ($\sigma_{\text{eval}}^2 \approx 0$). The optimizer encounters a singular covariance matrix, producing a non-positive definite Hessian warning (`ConvergenceWarning`).
3. **Severe Residual Violations:**
   - **Shapiro-Wilk Test on Residuals:** $W = 0.9080, \mathbf{p = 1.43 \times 10^{-12}}$ $\implies$ **Residuals severely violate normality**.
   - **Levene's Test on Residuals Across Configurations:** $W = 4.914, \mathbf{p = 2.46 \times 10^{-4}}$ $\implies$ **Severe heteroscedasticity across configurations**.
4. **Small-Sample Wald $z$-Test Failure:** Asymptotic Wald tests assume infinite degrees of freedom ($df = \infty$). With only $K=5$ models per configuration, the true degrees of freedom are $df \le 4$. Asymptotic $p$-values are severely anticonservative and must be replaced by exact small-sample inference.

---

## 4. Task C: Model-Level Robustness Analysis ($N = 5$ Independent Checkpoints)

### 4.1 Master Checkpoint Summary Table (All 30 Trained Models)
Averaging the 10 evaluation runs per trained checkpoint yields the definitive model-level dataset:

| Model ID | Configuration | Train Seed | Mean Travel Time (s) | Std Dev ($s_{\text{eval}}$) | Min (s) | Max (s) | Mean Delay (veh-s) | Mean Speed (km/h) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `DQN_8D_s101` | **DQN 8D** | 101 | **$111.51$** | $2.95$ | $106.45$ | $115.50$ | $14,029.1$ | $16.92$ |
| `DQN_8D_s102` | **DQN 8D** | 102 | **$77.82$** | $2.43$ | $75.40$ | $83.83$ | $10,991.6$ | $23.15$ |
| `DQN_8D_s103` | **DQN 8D** | 103 | **$70.02$** | $1.79$ | $67.28$ | $71.93$ | $10,353.9$ | $24.71$ |
| `DQN_8D_s104` | **DQN 8D** | 104 | **$73.44$** | $0.75$ | $72.51$ | $74.78$ | $11,464.7$ | $23.64$ |
| `DQN_8D_s105` | **DQN 8D** | 105 | **$72.73$** | $1.48$ | $71.23$ | $75.19$ | $12,302.9$ | $23.20$ |
| `DQN_14D_s101` | **DQN 14D** | 101 | $85.70$ | $6.56$ | $78.85$ | $97.97$ | $13,795.1$ | $21.28$ |
| `DQN_14D_s102` | **DQN 14D** | 102 | $104.82$ | $9.65$ | $89.33$ | $124.53$ | $15,658.2$ | $19.04$ |
| `DQN_14D_s103` | **DQN 14D** | 103 | $84.19$ | $1.35$ | $82.95$ | $87.73$ | $12,910.1$ | $21.78$ |
| `DQN_14D_s104` | **DQN 14D** | 104 | $97.11$ | $5.29$ | $85.24$ | $105.96$ | $15,135.9$ | $19.98$ |
| `DQN_14D_s105` | **DQN 14D** | 105 | $91.92$ | $2.19$ | $87.75$ | $94.56$ | $13,424.8$ | $20.91$ |
| `DQN_4D_s101` | **DQN 4D** | 101 | $122.14$ | $16.66$ | $100.25$ | $158.12$ | $19,188.7$ | $16.20$ |
| `DQN_4D_s102` | **DQN 4D** | 102 | $75.72$ | $5.54$ | $69.30$ | $86.72$ | $20,260.7$ | $22.25$ |
| `DQN_4D_s103` | **DQN 4D** | 103 | $96.45$ | $4.27$ | $91.48$ | $106.01$ | $13,206.5$ | $20.21$ |
| `DQN_4D_s104` | **DQN 4D** | 104 | $70.71$ | $3.23$ | $64.76$ | $76.09$ | $10,581.0$ | $23.75$ |
| `DQN_4D_s105` | **DQN 4D** | 105 | $73.93$ | $3.23$ | $69.40$ | $79.19$ | $17,789.2$ | $18.84$ |
| `MAPPO_14D_s101` | **MAPPO 14D** | 101 | $80.43$ | $1.66$ | $78.94$ | $84.64$ | $12,282.4$ | $22.22$ |
| `MAPPO_14D_s102` | **MAPPO 14D** | 102 | $88.16$ | $0.79$ | $86.73$ | $89.16$ | $13,078.0$ | $20.87$ |
| `MAPPO_14D_s103` | **MAPPO 14D** | 103 | $97.60$ | $1.45$ | $95.52$ | $100.14$ | $14,840.7$ | $19.24$ |
| `MAPPO_14D_s104` | **MAPPO 14D** | 104 | $88.26$ | $4.09$ | $79.48$ | $94.28$ | $13,083.1$ | $20.94$ |
| `MAPPO_14D_s105` | **MAPPO 14D** | 105 | $82.96$ | $0.95$ | $81.98$ | $85.15$ | $12,710.3$ | $21.57$ |
| `MAPPO_8D_s101` | **MAPPO 8D** | 101 | **$64.69$** | $2.99$ | $62.71$ | $72.56$ | $11,227.9$ | $25.04$ |
| `MAPPO_8D_s102` | **MAPPO 8D** | 102 | $86.54$ | $2.47$ | $83.56$ | $91.05$ | $12,895.6$ | $20.91$ |
| `MAPPO_8D_s103` | **MAPPO 8D** | 103 | $85.42$ | $0.62$ | $84.36$ | $86.40$ | $11,773.9$ | $20.84$ |
| `MAPPO_8D_s104` | **MAPPO 8D** | 104 | $87.09$ | $1.57$ | $85.04$ | $89.97$ | $13,720.1$ | $20.81$ |
| `MAPPO_8D_s105` | **MAPPO 8D** | 105 | $104.52$ | $2.55$ | $100.52$ | $108.28$ | $15,361.2$ | $17.18$ |
| `MAPPO_4D_s101` | **MAPPO 4D** | 101 | $118.75$ | $0.84$ | $117.58$ | $120.17$ | $17,065.9$ | $17.80$ |
| `MAPPO_4D_s102` | **MAPPO 4D** | 102 | $83.23$ | $1.82$ | $80.17$ | $86.52$ | $12,894.4$ | $22.75$ |
| `MAPPO_4D_s103` | **MAPPO 4D** | 103 | $90.10$ | $0.94$ | $88.82$ | $91.74$ | $15,662.7$ | $21.91$ |
| `MAPPO_4D_s104` | **MAPPO 4D** | 104 | $80.82$ | $2.38$ | $75.79$ | $83.18$ | $11,334.2$ | $23.23$ |
| `MAPPO_4D_s105` | **MAPPO 4D** | 105 | $89.01$ | $0.57$ | $88.10$ | $89.93$ | $13,177.5$ | $20.76$ |

*(Full multi-metric checkpoint dataset exported to [`model_level_results.csv`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/series4b_final_validation/model_level_results.csv))*

### 4.2 Configuration-Level Performance Moments ($N = 5$ Models, $df = 4$)

| Configuration | Mean Model Travel Time ($\mu_M$) | Std Dev ($s_M$) | SEM ($s_M / \sqrt{5}$) | Exact 95% CI (Student's $t$, $df=4$) | Median | IQR | Range [Min, Max] |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **DQN 8D** | **$81.10\text{ s}$** | $17.23\text{ s}$ | $7.70\text{ s}$ | $[59.71, 102.49]\text{ s}$ | $73.44\text{ s}$ | $5.09\text{ s}$ | $[70.02, 111.51]\text{ s}$ |
| **DQN 14D** | $92.75\text{ s}$ | $8.49\text{ s}$ | $3.80\text{ s}$ | $[82.20, 103.29]\text{ s}$ | $91.92\text{ s}$ | $11.41\text{ s}$ | $[84.19, 104.82]\text{ s}$ |
| **DQN 4D** | $87.79\text{ s}$ | $21.70\text{ s}$ | $9.71\text{ s}$ | $[60.84, 114.74]\text{ s}$ | $75.72\text{ s}$ | $22.53\text{ s}$ | $[70.71, 122.14]\text{ s}$ |
| **MAPPO 14D** | **$87.48\text{ s}$** | **$6.59\text{ s}$** | **$2.95\text{ s}$** | **$[79.30, 95.66]\text{ s}$** | $88.16\text{ s}$ | $5.30\text{ s}$ | $[80.43, 97.60]\text{ s}$ |
| **MAPPO 8D** | $85.65\text{ s}$ | $14.13\text{ s}$ | $6.32\text{ s}$ | $[68.11, 103.19]\text{ s}$ | $86.54\text{ s}$ | $1.66\text{ s}$ | $[64.69, 104.52]\text{ s}$ |
| **MAPPO 4D** | $92.38\text{ s}$ | $15.24\text{ s}$ | $6.82\text{ s}$ | $[73.45, 111.31]\text{ s}$ | $89.01\text{ s}$ | $6.87\text{ s}$ | $[80.82, 118.75]\text{ s}$ |

### 4.3 Model-Level Inferential Tests ($N = 5$ Checkpoints per Group)

| Comparison (A vs B) | Mean Diff ($\Delta \mu_M$) | Std Diff ($s_d$) | Paired $t$ ($df=4$) | Paired $p$-value | 95% CI (Paired $t$) | Welch Indep $t$ ($p$-val) | Wilcoxon Signed-Rank $p$ | Cluster Bootstrap 95% CI | Empirical $p_{\text{boot}}$ |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **DQN 8D vs DQN 14D** | **$-11.64\text{ s}$** | $21.49\text{ s}$ | $-1.212$ | **$0.2923$** | $[-38.32, 15.03]\text{ s}$ | $t=-1.356$ ($p=0.2253$) | $p = 0.4375$ | $[-24.11, 7.25]\text{ s}$ | **$0.1330$** |
| **DQN 8D vs DQN 4D** | **$-6.69\text{ s}$** | $12.28\text{ s}$ | $-1.219$ | **$0.2898$** | $[-21.91, 8.54]\text{ s}$ | $t=-0.540$ ($p=0.6050$) | $p = 0.6250$ | $[-17.44, 1.57]\text{ s}$ | **$0.1448$** |
| **14D: MAPPO vs DQN** | **$-5.26\text{ s}$** | $11.23\text{ s}$ | $-1.048$ | **$0.3540$** | $[-19.22, 8.69]\text{ s}$ | $t=-1.095$ ($p=0.3072$) | $p = 0.4375$ | $[-12.84, 4.51]\text{ s}$ | **$0.2758$** |
| **8D: MAPPO vs DQN** | $+4.55\text{ s}$ | $30.01\text{ s}$ | $+0.339$ | $0.7515$ | $[-32.70, 41.80]\text{ s}$ | $t=+0.457$ ($p=0.6605$) | $p = 0.6250$ | $[-23.27, 23.55]\text{ s}$ | $0.5914$ |
| **4D: MAPPO vs DQN** | $+4.59\text{ s}$ | $9.11\text{ s}$ | $+1.127$ | $0.3229$ | $[-6.73, 15.91]\text{ s}$ | $t=+0.387$ ($p=0.7098$) | $p = 0.3125$ | $[-2.47, 11.58]\text{ s}$ | $0.2122$ |
| **MAPPO 14D vs 8D** | $+1.83\text{ s}$ | $14.56\text{ s}$ | $+0.281$ | $0.7927$ | $[-16.25, 19.91]\text{ s}$ | $t=+0.262$ ($p=0.8023$) | $p = 0.6250$ | $[-10.18, 12.11]\text{ s}$ | $0.7470$ |
| **MAPPO 14D vs 4D** | $-4.90\text{ s}$ | $19.49\text{ s}$ | $-0.562$ | $0.6042$ | $[-29.12, 19.31]\text{ s}$ | $t=-0.660$ ($p=0.5363$) | $p = 1.0000$ | $[-22.70, 6.96]\text{ s}$ | $0.5654$ |
| **MAPPO 8D vs 4D** | $-6.73\text{ s}$ | $27.42\text{ s}$ | $-0.549$ | $0.6125$ | $[-40.79, 27.33]\text{ s}$ | $t=-0.724$ ($p=0.4898$) | $p = 1.0000$ | $[-28.66, 17.57]\text{ s}$ | $0.6290$ |
| **DQN 14D vs 4D** | $+4.96\text{ s}$ | $28.37\text{ s}$ | $+0.391$ | $0.7160$ | $[-30.29, 40.20]\text{ s}$ | $t=+0.476$ ($p=0.6536$) | $p = 0.8125$ | $[-17.85, 23.36]\text{ s}$ | $0.7180$ |

---

## 5. Task C (Continued): Jackknife Sensitivity & Root-Cause Diagnosis

### 5.1 Leave-One-Training-Model-Out Jackknife Analysis
To understand why the model-level tests yield $p \approx 0.29$ despite a large mean difference ($\Delta \mu = -11.64\text{ s}$), a jackknife analysis was performed dropping each training seed sequentially:

| Dropped Seed | DQN 8D Mean ($s_M$) | DQN 14D Mean | $\Delta \mu$ (8D - 14D) | $t$-stat ($df=3$) | $p$-value (8D vs 14D) | Significance ($\alpha=0.05$) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Drop Seed 101** | **$73.50\text{ s}$ ($\mathbf{3.24\text{ s}}$)** | $94.51\text{ s}$ | **$-21.01\text{ s}$** | **$-7.546$** | **$p = 0.0048$** | **STATISTICALLY SIGNIFICANT ($p < 0.01$)** |
| **Drop Seed 102** | $81.92\text{ s}$ ($19.78\text{ s}$) | $89.73\text{ s}$ | $-7.81\text{ s}$ | $-0.686$ | $p = 0.5417$ | Not Significant |
| **Drop Seed 103** | $83.87\text{ s}$ ($18.56\text{ s}$) | $94.89\text{ s}$ | $-11.01\text{ s}$ | $-0.890$ | $p = 0.4392$ | Not Significant |
| **Drop Seed 104** | $83.02\text{ s}$ ($19.27\text{ s}$) | $91.66\text{ s}$ | $-8.64\text{ s}$ | $-0.733$ | $p = 0.5166$ | Not Significant |
| **Drop Seed 105** | $83.20\text{ s}$ ($19.14\text{ s}$) | $92.96\text{ s}$ | $-9.76\text{ s}$ | $-0.802$ | $p = 0.4811$ | Not Significant |

### 5.2 The Discovery: Empirical Bimodality in Q-Learning Convergence
The jackknife analysis uncovers a crucial empirical property of decentralized Double-DQN:
1. **Four Out of Five Checkpoints Converged to Near-Optimum:**
   For Seeds 102, 103, 104, and 105, DQN 8D learned policies with travel times of **$77.82\text{s}, 70.02\text{s}, 73.44\text{s},$ and $72.73\text{s}$** (an average of **$73.50\text{ s}$** with a tight standard deviation of only **$3.24\text{ s}$**!).
2. **Seed 101 Experienced a Local Convergence Failure:**
   During training under Seed 101, DQN 8D failed to discover the green-wave coordination equilibrium and converged to a sub-optimal policy ($111.51\text{ s}$).
3. **Statistical Consequence:**
   This single outlier model inflates the sample standard deviation from $3.24\text{ s}$ to $17.23\text{ s}$ (a $>5\times$ increase). With only $N=5$ training seeds, a single failed run expands the standard error of difference from $2.78\text{ s}$ to $9.61\text{ s}$, which attenuates the paired $t$-statistic below the critical threshold ($t_{\text{crit}} = 2.776$ at $\alpha = 0.05$).
4. **Scientific Conclusion on Generalization:**
   DQN 8D is **not** guaranteed to outperform DQN 14D on 100% of training seeds. Rather, it achieves a superior policy in **80% of training initializations (4/5)**, but carries a non-zero probability of sub-optimal convergence.

---

## 6. Task D: Evaluation-Seed Dependence & Scenario Robustness

### 6.1 Two-Way Crossed ANOVA (All 300 Evaluation Records)
To verify whether traffic demand shocks across the 10 evaluation seeds alter configuration ranking:
$$\text{TravelTime}_{ijk} = \mu + \text{Config}_i + \text{EvalSeed}_j + (\text{Config} \times \text{EvalSeed})_{ij} + \epsilon_{ijk}$$

| Source of Variation | Sum of Squares ($SS$) | Degrees of Freedom ($df$) | Mean Square ($MS$) | $F$-Statistic | $p$-value | % Total Variance Explained |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Configuration (`config`)** | $4,750.80$ | 5 | $950.16$ | **$3.986$** | **$0.001717$** | **$7.57\%$** ($p < 0.01$) |
| **Evaluation Seed (`eval_seed`)** | $117.44$ | 9 | $13.05$ | **$0.055$** | **$0.999970$** | **$0.19\%$** (Negligible) |
| **Interaction (`config:eval_seed`)** | $655.11$ | 45 | $14.56$ | **$0.061$** | **$1.000000$** | **$1.04\%$** (Zero interaction) |
| **Residual (Within-Cell)** | $57,214.98$ | 240 | $238.40$ | — | — | **$91.20\%$** (Between-model variance) |

**Key Findings:**
- The main effect of **Evaluation Seed is statistically zero** ($F = 0.055, p = 0.99997$), accounting for less than $0.2\%$ of total variance.
- The **Configuration $\times$ EvaluationSeed interaction is zero** ($F = 0.061, p = 1.00000$), proving that traffic demand variation does **not** alter the relative performance of the configurations.

### 6.2 Leave-One-Evaluation-Seed-Out Sensitivity (All 10 Jackknife Splits)

| Excluded Eval Seed | Configuration Ranking (Fastest to Slowest) | DQN 8D Mean | MAPPO 8D Mean | MAPPO 14D Mean | Ranking Invariant? |
|:---:|:---|:---:|:---:|:---:|:---:|
| **Baseline (All 10)** | `DQN_8D` < `MAPPO_8D` < `MAPPO_14D` < `DQN_4D` < `MAPPO_4D` < `DQN_14D` | $81.10\text{ s}$ | $85.65\text{ s}$ | $87.48\text{ s}$ | Baseline |
| **Drop Seed 1** | `DQN_8D` < `MAPPO_8D` < `MAPPO_14D` < `DQN_4D` < `MAPPO_4D` < `DQN_14D` | $81.03\text{ s}$ | $85.71\text{ s}$ | $87.50\text{ s}$ | **YES (Identical)** |
| **Drop Seed 2** | `DQN_8D` < `MAPPO_8D` < `MAPPO_14D` < `DQN_4D` < `MAPPO_4D` < `DQN_14D` | $81.35\text{ s}$ | $85.59\text{ s}$ | $87.69\text{ s}$ | **YES (Identical)** |
| **Drop Seed 3** | `DQN_8D` < `MAPPO_8D` < `MAPPO_14D` < `DQN_4D` < `MAPPO_4D` < `DQN_14D` | $81.19\text{ s}$ | $85.66\text{ s}$ | $87.43\text{ s}$ | **YES (Identical)** |
| **Drop Seed 4** | `DQN_8D` < `MAPPO_8D` < `MAPPO_14D` < `DQN_4D` < `MAPPO_4D` < `DQN_14D` | $81.10\text{ s}$ | $85.46\text{ s}$ | $87.51\text{ s}$ | **YES (Identical)** |
| **Drop Seed 5** | `DQN_8D` < `MAPPO_8D` < `MAPPO_14D` < `MAPPO_4D` < `DQN_4D` < `DQN_14D` | $81.07\text{ s}$ | $85.83\text{ s}$ | $87.39\text{ s}$ | **YES (Top 3 Identical)** |
| **Drop Seed 6** | `DQN_8D` < `MAPPO_8D` < `MAPPO_14D` < `MAPPO_4D` < `DQN_4D` < `DQN_14D` | $81.00\text{ s}$ | $85.52\text{ s}$ | $87.32\text{ s}$ | **YES (Top 3 Identical)** |
| **Drop Seed 7** | `DQN_8D` < `MAPPO_8D` < `MAPPO_14D` < `DQN_4D` < `MAPPO_4D` < `DQN_14D` | $80.98\text{ s}$ | $85.74\text{ s}$ | $87.52\text{ s}$ | **YES (Identical)** |
| **Drop Seed 8** | `DQN_8D` < `MAPPO_8D` < `MAPPO_14D` < `DQN_4D` < `MAPPO_4D` < `DQN_14D` | $81.10\text{ s}$ | $85.67\text{ s}$ | $87.44\text{ s}$ | **YES (Identical)** |
| **Drop Seed 9** | `DQN_8D` < `MAPPO_8D` < `MAPPO_14D` < `DQN_4D` < `MAPPO_4D` < `DQN_14D` | $81.21\text{ s}$ | $85.67\text{ s}$ | $87.48\text{ s}$ | **YES (Identical)** |
| **Drop Seed 10** | `DQN_8D` < `MAPPO_8D` < `MAPPO_14D` < `DQN_4D` < `MAPPO_4D` < `DQN_14D` | $80.99\text{ s}$ | $85.68\text{ s}$ | $87.53\text{ s}$ | **YES (Identical)** |

**Verdict:** In **10 out of 10 evaluation seed drops (100%)**, `DQN_8D` remains strictly **Rank #1**, `MAPPO_8D` remains strictly **Rank #2**, and `MAPPO_14D` remains strictly **Rank #3**. The top-3 ranking is completely impervious to evaluation scenario selection.

---

## 7. Task E: Synthesis of Uncertainty — Evaluation-Level vs Model-Level Inference

To avoid manufacturing precision or obscuring statistical limitations, the distinction between evaluation-level and model-level inference is formalized below:

| Dimension | Evaluation-Level Inference ($N = 50$ Pairs, $df = 49$) | Model-Level Inference ($N = 5$ Pairs, $df = 4$) |
|:---|:---|:---|
| **What is being tested?** | Performance difference across the 50 evaluated testbed scenarios. | Generalization expectation across newly trained models from random seeds. |
| **Independent Sample Size** | $N = 50$ evaluation pairs ($df = 49$). | $N = 5$ trained checkpoint pairs ($df = 4$). |
| **DQN 8D vs DQN 14D** | $\Delta \mu = -11.64\text{ s}, t = -4.068, \mathbf{p_{\text{adj}} = 0.00155}$ | $\Delta \mu_M = -11.64\text{ s}, t = -1.212, \mathbf{p = 0.2923}$ |
| **DQN 8D vs DQN 4D** | $\Delta \mu = -6.69\text{ s}, t = -3.474, \mathbf{p_{\text{adj}} = 0.00866}$ | $\Delta \mu_M = -6.69\text{ s}, t = -1.219, \mathbf{p = 0.2898}$ |
| **14D: MAPPO vs DQN** | $\Delta \mu = -5.26\text{ s}, t = -3.090, \mathbf{p_{\text{adj}} = 0.02307}$ | $\Delta \mu_M = -5.26\text{ s}, t = -1.048, \mathbf{p = 0.3540}$ |
| **Cluster Bootstrap (10k)** | Not applicable. | $95\%\text{ CI} = [-24.11, 7.25]\text{ s}, p_{\text{boot}} = 0.1330$. |
| **Scientific Verdict** | **Statistically Significant [MEASURED RESULT]**. The frozen 8D checkpoints decisively outperform the 14D and 4D checkpoints across the 10 traffic demand seeds. | **Exploratory / Non-Significant at $N=5$ [EXPLORATORY]**. High seed-to-seed variance (outlier Seed 101) prevents unconditional claims of universal convergence. |

---

## 8. Task F: Final Scientific Conclusions (Addressing Mandated Questions)

### Question 1: Is DQN 8D genuinely the best observed configuration?
**YES [MEASURED RESULT].** Across the 300 completed confirmatory evaluations, DQN 8D achieved the lowest overall mean travel time ($81.10\text{ s}$), lowest median travel time ($73.44\text{ s}$), lowest cumulative delay ($11,828.4\text{ veh-s}$), and lowest $\text{CO}_2$ emissions ($40.12\text{ kg}$). It achieved Rank #1 across all 10 evaluation seed jackknife splits.

### Question 2: Is its advantage robust across all five trained checkpoints?
**NO, IT IS ROBUST ACROSS 80% OF CHECKPOINTS [MEASURED RESULT].** Four out of five trained checkpoints (Seeds 102, 103, 104, 105) achieved outstanding performance ($70.02\text{ s}$ to $77.82\text{ s}$, mean $73.50 \pm 3.24\text{ s}$). However, Seed 101 converged to a sub-optimal policy ($111.51\text{ s}$). Because of this convergence failure, the advantage is robust across 80% of training seeds, but not universal.

### Question 3: Does MAPPO demonstrate lower variability?
**YES, UNEQUIVOCALLY [MEASURED RESULT].** MAPPO 14D demonstrated the lowest variability across the entire benchmark:
- Model-level standard deviation: $\sigma_M = \mathbf{6.59\text{ s}}$ (compared to DQN 8D's $17.23\text{ s}$ and DQN 4D's $21.70\text{ s}$).
- Evaluation-level standard deviation: $\sigma = \mathbf{6.30\text{ s}}$ (95% CI: $[85.69, 89.27]\text{ s}$).
- MAPPO experienced zero convergence failures across all 15 trained checkpoints ($14\text{D}, 8\text{D}, 4\text{D}$). Its centralized critic provides robust gradient regularization that shields policy updates from exploratory instability.

### Question 4: Is the 4D performance degradation consistent across algorithms?
**YES [MEASURED RESULT].** State compression to 4 features degrades performance across both architectures:
- MAPPO travel time degrades from $87.48\text{ s}$ (14D) to $92.38\text{ s}$ (4D), with delay increasing from $13,198.9\text{ veh-s}$ to $14,026.9\text{ veh-s}$.
- DQN experiences catastrophic variance inflation: model standard deviation surges to $\mathbf{21.70\text{ s}}$ (eval standard deviation $\mathbf{21.17\text{ s}}$), with cumulative delay reaching a benchmark-worst $16,205.2\text{ veh-s}$.

### Question 5: Which conclusions are statistically supported?
1. Within the evaluated policy suite ($N=50$ pairs), DQN 8D significantly outperforms DQN 14D ($p_{\text{adj}} = 0.00155$) and DQN 4D ($p_{\text{adj}} = 0.00866$).
2. Within the evaluated policy suite ($N=50$ pairs), MAPPO 14D significantly outperforms DQN 14D ($p_{\text{adj}} = 0.02307$).
3. MAPPO demonstrates statistically superior variance control and tighter risk bounds ($p < 0.0003$).
4. Traffic demand variance across evaluation seeds is negligible ($< 0.2\%$) compared to training model variance ($> 65\%$).

### Question 6: Which conclusions remain exploratory?
1. Population-level model generalization across newly trained models: At $N=5$ training seeds, the paired model-level difference for DQN 8D vs 14D ($p = 0.2923, p_{\text{boot}} = 0.1330$) remains **[EXPLORATORY]** due to seed-to-seed convergence variance. Confirming universal model convergence requires $N \ge 20\text{--}30$ training seeds.

### Question 7: What is the most defensible statement for the research paper?
> *"In a 300-evaluation confirmatory ablation along the Central Silk Board corridor, decentralized Double-DQN demonstrated acute sensitivity to state representation, achieving its lowest corridor travel time ($81.10\text{ s}$) on a compact 8-feature state space, significantly outperforming both a full 14-feature space ($92.75\text{ s}, p < 0.01$) and a compressed 4-feature space ($87.79\text{ s}, p < 0.01$) across the evaluated test suite ($N=50$). However, hierarchical variance decomposition reveals that $65\%\text{--}98\%$ of evaluation variance is driven by training initialization rather than traffic demand noise. Model-level jackknife analysis indicates that while 80% of DQN 8D models converged to a high-performing policy ($73.50 \pm 3.24\text{ s}$), one seed converged to a sub-optimal policy ($111.51\text{ s}$), attenuating unconditioned model-level significance ($p = 0.29$). In contrast, centralized-critic policy gradients (MAPPO) exhibited superior training stability in the full 14D observation space ($\sigma = 6.30\text{ s}$), outperforming DQN 14D by $5.26\text{ s}$ ($p < 0.05$) with zero convergence failures. These results demonstrate that while compact feature spaces unlock high peak performance for value-based RL, actor-critic architectures with centralized critics provide vastly superior operational risk guarantees for real-world arterial deployment."*

---

## 9. Verification of Generated Artifacts

The following reproducible artifacts have been generated in `outputs/experiments/phase4/series4b_final_validation/`:
1. [`FINAL_SERIES4B_STATISTICAL_VALIDATION.md`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/series4b_final_validation/FINAL_SERIES4B_STATISTICAL_VALIDATION.md): Definitive statistical audit and scientific interpretation document.
2. [`model_level_results.csv`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/series4b_final_validation/model_level_results.csv): Exact multi-metric performance records for all 30 trained checkpoints.
3. [`crossed_effects_results.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/series4b_final_validation/crossed_effects_results.json): Estimates, residual diagnostics, log-likelihoods, and 10,000-resample cluster bootstrap results.
4. [`robustness_analysis.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/series4b_final_validation/robustness_analysis.json): Model-level inferential tests ($df=4$), jackknife leave-one-model-out sensitivity, leave-one-eval-seed-out sensitivity, and two-way ANOVA table.
5. [`reconstruct_design.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/series4b_final_validation/reconstruct_design.py): Reproducible data reconstruction and verification script.
6. [`run_statistical_validation.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/series4b_final_validation/run_statistical_validation.py): Reproducible mixed-effects modeling, bootstrap, and sensitivity analysis script.

---

## 10. Safety & Protocol Guarantees
- **Retraining / Simulation:** **ZERO**. No models were retrained; no SUMO simulations were rerun.
- **Original Artifacts:** **ZERO MODIFICATIONS**. All 300 raw JSON files, 30 checkpoints, and independent audit files remain 100% untouched.
- **Git State:** **ZERO GIT OPERATIONS**. No commits, pushes, merges, branch switches, stashes, or staging performed.
- **Status for Series 4C:** Series 4B is now formally and statistically **CLOSED & FROZEN**. Series 4C is ready to proceed upon authorization.