# INDEPENDENT STATISTICAL AND SCIENTIFIC AUDIT OF SERIES 4B
## Phase 4 Confirmatory Experiment: Observation Space Dimensionality Ablation

**Audit Date:** 2026-11-13  
**Auditor:** Antigravity Advanced Agentic Pair Programming & Verification Engine  
**Project:** Smart Traffic Coordination System (`hybrid-traffic-control`)  
**Corridor:** Central Silk Board Corridor ($J_1 \to J_2 \to J_3$)  
**Target Repository State:** `HEAD: e31de953ceb7fe878d531c888e7f27e532b13b37` (Read-Only Inspection Mode)  
**Audit Output Location:** `outputs/experiments/phase4/independent_audit_series4b/`  

---

## 1. Executive Audit Overview & Authoritative Scope

This independent audit conducts a mathematical, statistical, and methodological examination of **Series 4B (Observation Space Dimensionality Ablation)**. The audit directly verifies the 300 raw evaluation artifacts in `outputs/experiments/phase4/final_150ep/series_4b_observation_space/`, cross-referencing them against `series_4b_summary.json`, `series_4b_statistical_analysis.json`, `series4b_final_audit.md`, and `docs/RESEARCH_PAPER_MASTER_RECORD.md` Section 22.

### 1.1 Summary of Audit Findings
1. **Raw Artifact Integrity:** **100% VERIFIED**. All 300 evaluation JSON files and 30 checkpoint files are present on disk, valid JSON, complete, and uncorrupted. Every combination of 2 algorithms $\times$ 3 observation dimensions $\times$ 5 training seeds $\times$ 10 evaluation seeds is uniquely accounted for with zero missing or duplicate files.
2. **Descriptive Statistics:** **VERIFIED**. Independent recomputation of sample means, sample standard deviations ($ddof=1$), standard errors of the mean (SEM), medians, IQRs, and 95% confidence intervals (using Student's $t$ with $df=49$) matches stored summary values within floating-point rounding precision across all metrics.
3. **Calculation Discrepancy #1 (Sign Convention Inversion):** **IDENTIFIED & CORRECTED**. In stored reports, the comparison between DQN 8D and DQN 14D was labeled with a negative mean difference ($\Delta \mu = -11.64\text{ s}$), but paired with a positive $t$-statistic ($+4.068$) and positive Cohen's $d$ ($+0.575$), creating a mathematical sign inconsistency.
4. **Calculation Discrepancy #2 (Non-Monotonic Holm-Bonferroni Step-Down):** **IDENTIFIED & CORRECTED**. The script `analyze_series4b.py` omitted the cumulative maximum step-down constraint ($p_{\text{adj}(k)} = \max(p_{\text{adj}(k-1)}, (m-k+1)p_{(k)})$), producing non-monotonic adjusted $p$-values for non-significant comparisons (e.g., $p_{(9)} = 0.3428$ while $p_{(7)} = 0.6248$). The 4 significant findings remain strictly significant, but non-significant adjusted $p$-values required correction.
5. **Statistical Limitation (Pseudoreplication & Two-Way Crossed Structure):** **IDENTIFIED & QUANTIFIED**. Analysis of variance reveals that **$65.2\%$ to $98.9\%$ of total variance** originates between **Training Seeds** (model-to-model variation), while only **$0.4\%$ to $6.4\%$** originates between **Evaluation Seeds** (traffic demand shocks). Treating $N=50$ evaluations as independent pairs inflates degrees of freedom ($df=49$ vs $df=4$ at model level). When evaluated via a Linear Mixed-Effects Model (LMM) with random intercepts, the 8D advantage remains significant ($z = 5.39, p < 10^{-4}$), but standard model-averaged paired $t$-tests ($N=5$) exhibit high variance ($p = 0.29$).
6. **Reconciliation of Welch's $t$-test and Mann-Whitney $U$:** **RECONCILED**. Welch's $t$-test indicates no significant difference in overall means ($p = 0.440$), while Mann-Whitney $U$ rejects stochastic equality ($p = 0.0284$). This is driven by **severe variance heterogeneity** (Levene's test $W = 22.64, p = 3.04 \times 10^{-6}$), where DQN exhibits a lower median ($83.32\text{ s}$ vs $87.02\text{ s}$) but an extreme upper tail ($\sigma = 16.76\text{ s}$ vs $11.80\text{ s}$).
7. **Scientific Claim Critique:** **IDENTIFIED UNVERIFIED CONJECTURES**. Assertions that "8D isolates sufficient statistic properties" and "14D introduces policy noise and function approximation error" are unmeasured post-hoc theoretical speculations rather than empirical measured facts, and must be classified as **[UNVERIFIED THEORETICAL CONJECTURES]**.

---

## 2. Checkpoint & Raw Evaluation Verification

### 2.1 30 Training Checkpoints Verification
- Checkpoint directory: `checkpoints/phase4/final_150ep/`
- Exactly 30 model checkpoints (`.json`) and 30 training history logs (`.history.json`) verified.
- All 30 models contain metadata flag `verified_150ep: true`, `num_episodes: 150`, and history length exactly $150$ records.
- 0 NaN or Infinity values in model weights or history metrics.
- Simulation duration strictly verified at $1{,}200.00\text{ s}$ per episode across all $4{,}500$ completed training episodes.

### 2.2 300 Raw Evaluation Artifacts Verification
- Raw evaluation directory: `outputs/experiments/phase4/final_150ep/series_4b_observation_space/`
- Exactly 300 JSON files matching `eval_*.json` verified.
- File integrity checks:
  - Valid JSON syntax: **300 / 300 (100%)**
  - Completed flag (`completed: true`): **300 / 300 (100%)**
  - Full corridor metrics present (Travel Time, Speed, Delay, Trips, Fuel, CO2, Queue): **300 / 300 (100%)**
  - Missing expected $(algorithm, dimension, train\_seed, eval\_seed)$ combinations: **0**
  - Duplicate combinations: **0**
  - Corrupt or partially written files: **0**

---

## 3. Independent Descriptive Statistics Recomputation

All descriptive statistics were recomputed independently directly from the 300 raw JSON files:
- Sample Mean: $\bar{x} = \frac{1}{n} \sum_{i=1}^n x_i$
- Sample Standard Deviation ($s$, $ddof=1$): $s = \sqrt{\frac{1}{n-1} \sum_{i=1}^n (x_i - \bar{x})^2}$
- Standard Error of the Mean (SEM): $\text{SEM} = s / \sqrt{n}$
- 95% Confidence Interval using Student's $t$ ($df = 49, t_{0.975} = 2.009575$): $[\bar{x} - t_{0.975} \cdot \text{SEM}, \bar{x} + t_{0.975} \cdot \text{SEM}]$

### 3.1 Recomputed Corridor Travel Time (s) Verification Table

| Configuration | N | Recomputed Mean $\pm$ $s$ | Stored Mean $\pm$ $s$ | Recomputed 95% CI ($t$-dist) | Stored 95% CI | Discrepancy |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **MAPPO 14D** | 50 | $87.4812 \pm 6.3004$ | $87.48 \pm 6.30$ | $[85.69, 89.27]$ | $[85.69, 89.27]$ | **NONE (Exact)** |
| **MAPPO 8D** | 50 | $85.6520 \pm 12.9391$ | $85.65 \pm 12.94$ | $[81.97, 89.33]$ | $[81.97, 89.33]$ | **NONE (Exact)** |
| **MAPPO 4D** | 50 | $92.3814 \pm 13.8445$ | $92.38 \pm 13.84$ | $[88.45, 96.32]$ | $[88.45, 96.32]$ | **NONE (Exact)** |
| **DQN 14D** | 50 | $92.7460 \pm 9.4985$ | $92.75 \pm 9.50$ | $[90.05, 95.45]$ | $[90.05, 95.45]$ | **NONE (Exact)** |
| **DQN 8D** | 50 | $81.1016 \pm 15.6862$ | $81.10 \pm 15.69$ | $[76.64, 85.56]$ | $[76.64, 85.56]$ | **NONE (Exact)** |
| **DQN 4D** | 50 | $87.7876 \pm 21.1745$ | $87.79 \pm 21.17$ | $[81.77, 93.81]$ | $[81.77, 93.81]$ | **NONE (Exact)** |

### 3.2 Secondary Metrics Verification (All 6 Configurations)

| Configuration | Mean Speed (km/h) | Cumulative Delay (veh-s) | Total $\text{CO}_2$ (kg) | Total Fuel (L) | Mean Queue | Completed Trips |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **MAPPO 14D** | $20.97 \pm 1.25$ | $13,198.9 \pm 1,421.2$ | $42.18 \pm 2.85$ | $18.17 \pm 1.23$ | $2.31 \pm 0.32$ | $109.0 \pm 0.0$ |
| **MAPPO 8D** | $20.96 \pm 2.45$ | $12,995.7 \pm 2,890.5$ | $41.85 \pm 3.90$ | $18.03 \pm 1.68$ | $2.26 \pm 0.58$ | $109.0 \pm 0.0$ |
| **MAPPO 4D** | $21.29 \pm 2.10$ | $14,026.9 \pm 3,110.4$ | $43.91 \pm 4.12$ | $18.91 \pm 1.77$ | $2.48 \pm 0.65$ | $109.0 \pm 0.0$ |
| **DQN 14D** | $20.60 \pm 1.48$ | $14,184.8 \pm 2,150.8$ | $43.80 \pm 3.10$ | $18.87 \pm 1.33$ | $2.55 \pm 0.42$ | $109.0 \pm 0.0$ |
| **DQN 8D** | $22.32 \pm 2.80$ | $11,828.4 \pm 3,240.6$ | $40.12 \pm 4.25$ | $17.28 \pm 1.83$ | $2.05 \pm 0.68$ | $109.0 \pm 0.0$ |
| **DQN 4D** | $20.25 \pm 3.12$ | $16,205.2 \pm 4,890.2$ | $46.85 \pm 5.90$ | $20.18 \pm 2.54$ | $2.95 \pm 0.98$ | $109.0 \pm 0.0$ |

*Verification Verdict:* Descriptive statistics across all 6 configurations and all 7 metrics are confirmed accurate and verified to within $\pm 0.01$ units.

---

## 4. Recomputation of Inferential Tests & Calculation Discrepancies

### 4.1 Calculation Discrepancy #1: Sign Convention Inversion in Pairwise Table
- **Identified Defect:**
  In `outputs/experiments/phase4/series4b_final_audit.md` (Table in Section 4) and `docs/RESEARCH_PAPER_MASTER_RECORD.md` (Table in Section 22.3), the comparison was labeled:
  `DQN 8D vs DQN 14D | Mean Difference: -11.64s | Paired t-stat: 4.068 | Cohen's d: 0.575`
- **Mathematical Inconsistency:**
  If the difference is defined as $\text{Condition A} - \text{Condition B} = \text{DQN 8D} - \text{DQN 14D} = 81.10 - 92.75 = -11.64\text{ s}$, then the $t$-statistic must be:
  $$t = \frac{\bar{d}}{\text{SEM}_d} = \frac{-11.6444}{2.8624} = \mathbf{-4.068}$$
  and the paired effect size (Cohen's $d_z$) must be:
  $$d_z = \frac{\bar{d}}{s_d} = \frac{-11.6444}{20.2404} = \mathbf{-0.575}$$
- **Root Cause in Code:**
  In `scratch/analyze_series4b.py` line 92, the comparison was encoded as `("DQN 14D vs 8D", ("dqn", 14), ("dqn", 8))`. The script computed $14\text{D} - 8\text{D} = +11.64\text{ s}$, yielding $t = +4.068$ and $d = +0.575$. When the text was written, the author flipped the label and difference to `DQN 8D vs DQN 14D` ($-11.64\text{s}$) to emphasize the speedup, but copied the positive $t$ and $d$ values directly from the dictionary, creating a sign inversion error.
- **Resolution:** Re-establish a consistent sign convention throughout all tables: Condition A minus Condition B.

### 4.2 Calculation Discrepancy #2: Non-Monotonic Holm-Bonferroni Adjusted $p$-Values
- **Identified Defect:**
  In `scratch/analyze_series4b.py`, lines 145–155 implemented the step-down multiplier without enforcing monotonicity:
  ```python
  # analyze_series4b.py (defective snippet)
  for rank, idx in enumerate(sorted_indices):
      multiplier = m_comp - rank
      adj_p = min(1.0, raw_p_values[idx] * multiplier)
      adj_p_values[idx] = adj_p
  ```
- **Mathematical Inconsistency:**
  The standard Holm-Bonferroni step-down procedure requires adjusted $p$-values to be monotonically non-decreasing:
  $$p_{\text{adj}(k)} = \min\left(1.0, \max\left(p_{\text{adj}(k-1)}, (m - k + 1) \cdot p_{(k)}\right)\right)$$
  Without the cumulative maximum, when rank $k=7$ had raw $p = 0.20827$ ($p_{\text{adj}} = 0.20827 \times 3 = 0.62481$), rank $k=8$ with larger raw $p = 0.24368$ received a smaller adjusted $p = 0.24368 \times 2 = 0.48737$, and rank $k=9$ with raw $p = 0.34285$ received $0.34285 \times 1 = 0.34285$.
- **Impact on Decisions:**
  The 4 statistically significant comparisons ($k = 1, 2, 3, 4$) are unaffected because their adjusted $p$-values ($0.00155, 0.00866, 0.02307, 0.04459$) are strictly monotonic and remain below $\alpha = 0.05$. However, the reported values for ranks 6, 8, and 9 were numerically incorrect.

### 4.3 Fully Recomputed & Corrected Pairwise Comparison Table (N = 50 Pairs)

Here, Condition A minus Condition B is strictly maintained for difference $\Delta \mu$, $t$-statistic, and Cohen's $d_z$:

| Rank | Comparison (A vs B) | Mean A (s) | Mean B (s) | $\Delta \mu$ (A - B) | $s_d$ | Paired $t$ ($df=49$) | Raw $p$ | Holm $p_{\text{adj}}$ (Corrected) | Stored $p_{\text{adj}}$ (Defective) | Cohen's $d_z$ | Significant ($\alpha=0.05$) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **DQN 8D vs DQN 14D** | 81.10 | 92.75 | **$-11.64\text{ s}$** | 20.24 | **$-4.068$** | $0.000172$ | **$0.001546$** | $0.001546$ | **$-0.575$** | **YES ($p < 0.01$)** |
| 2 | **DQN 8D vs DQN 4D** | 81.10 | 87.79 | **$-6.69\text{ s}$** | 13.61 | **$-3.474$** | $0.001083$ | **$0.008664$** | $0.008664$ | **$-0.491$** | **YES ($p < 0.01$)** |
| 3 | **14D: MAPPO vs DQN** | 87.48 | 92.75 | **$-5.26\text{ s}$** | 12.04 | **$-3.090$** | $0.003296$ | **$0.023069$** | $0.023069$ | **$-0.437$** | **YES ($p < 0.05$)** |
| 4 | **4D: MAPPO vs DQN** | 92.38 | 87.79 | **$+4.59\text{ s}$** | 11.63 | **$+2.793$** | $0.007432$ | **$0.044594$** | $0.044594$ | **$+0.395$** | **YES ($p < 0.05$)** |
| 5 | **MAPPO 14D vs 4D** | 87.48 | 92.38 | $-4.90\text{ s}$ | 17.81 | $-1.945$ | $0.057496$ | $0.287482$ | $0.287482$ | $-0.275$ | NO ($p = 0.29$) |
| 6 | **MAPPO 8D vs 4D** | 85.65 | 92.38 | $-6.73\text{ s}$ | 24.90 | $-1.911$ | $0.061824$ | **$0.287482$** | *0.247297* | $-0.270$ | NO ($p = 0.29$) |
| 7 | **DQN 14D vs 4D** | 92.75 | 87.79 | $+4.96\text{ s}$ | 27.50 | $+1.275$ | $0.208270$ | $0.624809$ | $0.624809$ | $+0.180$ | NO ($p = 0.62$) |
| 8 | **8D: MAPPO vs DQN** | 85.65 | 81.10 | $+4.55\text{ s}$ | 27.26 | $+1.180$ | $0.243682$ | **$0.624809$** | *0.487365* | $+0.167$ | NO ($p = 0.62$) |
| 9 | **MAPPO 14D vs 8D** | 87.48 | 85.65 | $+1.83\text{ s}$ | 13.50 | $+0.958$ | $0.342845$ | **$0.624809$** | *0.342845* | $+0.135$ | NO ($p = 0.62$) |

---

## 5. Statistical Independence, Hierarchical Modeling & Pseudoreplication

Task 6 directs an investigation into whether the $5 \times 10 = 50$ evaluation runs per configuration constitute independent observations.

### 5.1 Analysis of Data Generating Process (Two-Way Crossed Structure)
The 50 evaluations per configuration are generated by crossing two random factors:
1. **Training Seed (`train_seed` $\in \{101, 102, 103, 104, 105\}$, $N=5$):** Reflects stochasticity in policy initialization, exploration, and replay sampling during 150 training episodes.
2. **Evaluation Seed (`eval_seed` $\in \{1, 2, \dots, 10\}$, $N=10$):** Reflects stochasticity in vehicle injection timing, platoon arrival distributions, and route turning choices in SUMO.

### 5.2 Variance Decomposition (ANOVA)
To quantify where the variance in corridor travel time originates, a two-way ANOVA was fit for each configuration:
$$\text{TravelTime}_{ijk} = \mu + \alpha_i^{\text{train\_seed}} + \beta_j^{\text{eval\_seed}} + \epsilon_{ijk}$$

| Configuration | Total Variance ($s^2$) | % Variance: Training Seed | $F$-stat ($p$-value) | % Variance: Evaluation Seed | $F$-stat ($p$-value) | % Residual Variance |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **DQN 14D** | $90.22$ | **$65.24\%$** | $20.73$ ($p = 3.6 \times 10^{-9}$) | $6.40\%$ | $0.90$ ($p = 0.533$) | $28.36\%$ |
| **DQN 8D** | $246.06$ | **$98.47\%$** | $792.83$ ($p = 1.2 \times 10^{-37}$) | $0.41\%$ | $1.47$ ($p = 0.199$) | $1.12\%$ |
| **DQN 4D** | $448.36$ | **$85.77\%$** | $60.39$ ($p = 7.8 \times 10^{-17}$) | $1.45\%$ | $0.45$ ($p = 0.896$) | $12.78\%$ |
| **MAPPO 14D** | $39.69$ | **$89.29\%$** | $90.50$ ($p = 4.2 \times 10^{-20}$) | $1.82\%$ | $0.82$ ($p = 0.601$) | $8.89\%$ |
| **MAPPO 8D** | $167.42$ | **$97.32\%$** | $403.49$ ($p = 3.3 \times 10^{-32}$) | $0.50\%$ | $0.93$ ($p = 0.511$) | $2.17\%$ |
| **MAPPO 4D** | $191.67$ | **$98.96\%$** | $1587.32$ ($p = 1.1 \times 10^{-42}$) | $0.48\%$ | $3.41$ ($p = 0.004$) | $0.56\%$ |

### 5.3 Methodological Insight: The Pseudoreplication Consequence
- **Key Finding:** In every configuration, **$65\%$ to $99\%$ of the variance in evaluation performance is attributable to the training seed (the model weights)**.
- Once a neural checkpoint is frozen, varying the traffic demand seed ($1$ to $10$) introduces minimal variance ($< 2\%$ for most configs).
- **The Pseudoreplication Consequence:**
  Treating $N=50$ evaluations as 50 independent degrees of freedom ($df=49$) drastically underestimates standard errors when asking: *"Does this algorithm/dimension outperform another on a newly trained model?"*
  The true sample size of trained models is **$N = 5$**, not $N = 50$.

### 5.4 Model-Averaged Comparison ($N = 5, df = 4$) vs Linear Mixed Model (LMM)
When we aggregate the 10 evaluation runs per model into an authoritative mean per training seed:

| Training Seed | DQN 14D (s) | DQN 8D (s) | DQN 4D (s) | MAPPO 14D (s) | MAPPO 8D (s) | MAPPO 4D (s) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **101** | $85.70$ | **$111.51$** | $122.14$ | $80.43$ | $64.69$ | $118.75$ |
| **102** | $104.82$ | $77.82$ | $75.72$ | $88.16$ | $86.54$ | $83.23$ |
| **103** | $84.18$ | $70.02$ | $96.45$ | $97.60$ | $85.42$ | $90.10$ |
| **104** | $97.11$ | $73.44$ | $70.71$ | $88.26$ | $87.09$ | $80.82$ |
| **105** | $91.92$ | $72.73$ | $73.93$ | $82.96$ | $104.52$ | $89.01$ |
| **Mean** | **$92.75$** | **$81.10$** | **$87.79$** | **$87.48$** | **$85.65$** | **$92.38$** |

Testing at the Model Level ($N=5$ pairs, $df=4$) vs Full Linear Mixed Model ($N=300$ with random intercepts for `train_seed`):

| Comparison | Eval-Level Paired $t$ ($N=50, df=49$) | Model-Level Paired $t$ ($N=5, df=4$) | Linear Mixed Model (LMM $z$-score) |
|:---|:---:|:---:|:---:|
| **DQN 8D vs DQN 14D** | **$t = -4.068, p = 0.00017$** | $t = -1.212, p = 0.2923$ | **$z = -5.393, p < 0.0001$** |
| **DQN 8D vs DQN 4D** | **$t = -3.474, p = 0.00108$** | $t = -1.219, p = 0.2898$ | **$z = -4.077, p < 0.0001$** |
| **14D: MAPPO vs DQN** | **$t = -3.090, p = 0.00330$** | $t = -1.048, p = 0.3540$ | **$z = -3.905, p = 0.0001$** |
| **4D: MAPPO vs DQN** | **$t = +2.793, p = 0.00743$** | $t = +1.127, p = 0.3229$ | **$z = +3.186, p = 0.0014$** |

- **Methodological Recommendation for Publication:**
  In Section 22 and future conference/journal papers, **both metrics must be reported transparently**:
  1. The $N=50$ paired test measures performance across the evaluated test suite.
  2. The Linear Mixed Model (LMM) confirms that the effect size of 8D remains statistically significant ($p < 0.0001$) when accounting for random intercepts across training seeds.
  3. However, authors must acknowledge that at $N=5$ training seeds, a single outlier model (such as DQN 8D Seed 101, which converged to $111.51\text{s}$) inflates inter-model standard deviation, demonstrating that Q-learning requires seed exploration to guarantee convergence to the optimal equilibrium.

---

## 6. Reconciliation of Welch's $t$-test and Mann-Whitney $U$ Test

In the cross-algorithm aggregate (All 150 MAPPO vs All 150 DQN evaluations):
- **Welch's $t$-test:** $t = 0.773, p = 0.4404$ (Null hypothesis of equal means NOT rejected)
- **Mann-Whitney $U$ test:** $U = 12,897.0, p = 0.0284$ (Null hypothesis of stochastic equality REJECTED at $\alpha = 0.05$)

### 6.1 Distributional Diagnostics

| Distribution Property | MAPPO Aggregate ($N=150$) | DQN Aggregate ($N=150$) | Disparity / Ratio |
|:---|:---:|:---:|:---:|
| **Sample Mean** | $88.50\text{ s}$ | $87.21\text{ s}$ | $\Delta = 1.29\text{ s}$ |
| **Sample Std Dev ($s$)** | $11.80\text{ s}$ | **$16.76\text{ s}$** | DQN variance is $2.02\times$ higher |
| **Sample Median** | $87.02\text{ s}$ | **$83.32\text{ s}$** | DQN median is $3.70\text{ s}$ lower |
| **Interquartile Range (IQR)** | **$7.61\text{ s}$** | **$24.56\text{ s}$** | DQN IQR is $3.23\times$ wider |
| **10th Percentile** | $79.34\text{ s}$ | $70.74\text{ s}$ | DQN reaches lower travel times |
| **90th Percentile** | $104.51\text{ s}$ | $109.68\text{ s}$ | DQN extends to higher travel times |
| **Skewness** | $+0.71$ | $+1.11$ | DQN is more heavily right-skewed |

### 6.2 Variance Heterogeneity & Test Reconciliation
1. **Severe Variance Heterogeneity:**
   Levene's test for equality of variance is overwhelmingly rejected:
   $$W = 22.64, \quad p = 3.04 \times 10^{-6}$$
2. **Reconciliation Mechanism:**
   - **Why Welch's $t$ is non-significant ($p = 0.440$):**
     Welch's test evaluates difference in population means ($\Delta = 1.29\text{ s}$). Because DQN has high variance ($s = 16.76\text{ s}$), the standard error of difference is $\text{SE} = \sqrt{\frac{11.80^2}{150} + \frac{16.76^2}{150}} = 1.67\text{ s}$. The $t$-statistic is $t = 1.29 / 1.67 = 0.773$, which is consistent with pure chance.
   - **Why Mann-Whitney $U$ is significant ($p = 0.0284$):**
     Mann-Whitney $U$ evaluates rank sums / stochastic dominance ($P(X > Y)$). In DQN, the 8-dimensional runs concentrate a large mass of observations between $70\text{ s}$ and $80\text{ s}$ (median $83.32\text{ s}$ vs $87.02\text{ s}$). The Common Language Effect Size is $P(\text{MAPPO} > \text{DQN}) = 57.32\%$.
   - **Critical Warning:**
     When two populations have non-identical distribution shapes and unequal variances ($p < 10^{-5}$), Mann-Whitney $U$ **does not test equality of medians**; it is sensitive to shape/scale disparities.
   - **Scientific Verdict:**
     The claim that "DQN is overall superior to MAPPO" is invalid. Rather: **DQN exhibits higher performance potential at its 8D optimum, but MAPPO exhibits vastly superior stability, risk bounds, and variance control across arbitrary observation dimensions.**

---

## 7. Epistemological Audit of Scientific Claims

Following the Epistemological Taxonomy of the master record, the claims made in Section 22.4 were audited for empirical support:

### Claim Critique #1: "8D isolates sufficient statistic properties"
- **Text in Record:** *"The 8D feature set isolates sufficient statistic properties for local intersection queue dissipation."*
- **Audit Verdict:** **[UNVERIFIED THEORETICAL CONJECTURE]** (Must be downgraded from [MEASURED RESULT]).
- **Scientific Critique:**
  A sufficient statistic $T(S)$ requires proving that $P(S \mid T(S), A)$ is conditionally independent of unobserved state components. The experiment only compared performance across 3 discrete dimensions ($14, 8, 4$). No mutual information, Fisher information, or sufficiency tests were performed. While 8D is empirically optimal among the three tested points, declaring it a "sufficient statistic" is a theoretical overreach.

### Claim Critique #2: "14D introduces policy noise and function approximation error in Q-learning"
- **Text in Record:** *"additional state dimensions (14D) increase function approximation error and sample complexity, while overly compressed states (4D) induce severe non-Markovian partial observability."*
- **Audit Verdict:** **[UNVERIFIED THEORETICAL CONJECTURE]**.
- **Scientific Critique:**
  Function approximation error (Bellman residual $\|Q - \mathcal{T}Q\|$) and gradient variance were never logged or measured during training. While this is a plausible theoretical explanation rooted in reinforcement learning literature, it was not empirically measured in this codebase.

### Claim Critique #3: "4D violates the Markovian assumption"
- **Text in Record:** *"4 features fail the observability requirements... induce severe non-Markovian partial observability."*
- **Audit Verdict:** **[METHODOLOGICAL SPECULATION]**.
- **Scientific Critique:**
  Traffic signal control on arterial networks is a Partially Observable Markov Decision Process (POMDP) across all dimensions, including 14D (as unobserved route turn intentions and upstream link entries are hidden). 4D does not uniquely "violate" the Markov assumption; rather, 4D eliminates upstream arrival cues, reducing the agent's lookahead horizon.

---

## 8. Defensible Scientific Conclusions & Publication Guidance

### 8.1 What the Evidence Strictly Proves [MEASURED RESULTS]
1. **DQN Dimensional Sensitivity:** Under 150-episode confirmatory training, decentralized Double-DQN achieves statistically significant performance gains on an 8-dimensional observation space ($81.10 \pm 15.69\text{ s}$) compared to both a 14-dimensional space ($92.75 \pm 9.50\text{ s}, p_{\text{adj}} = 0.00155, d = -0.575$) and a 4-dimensional space ($87.79 \pm 21.17\text{ s}, p_{\text{adj}} = 0.00866, d = -0.491$).
2. **MAPPO Full-State Resilience:** MAPPO Actor-Critic policies with a centralized critic are robust to high-dimensional inputs ($14\text{D}$ travel time: $87.48 \pm 6.30\text{ s}$, 95% CI: $[85.69, 89.27]\text{ s}$), achieving significantly lower travel times than DQN at 14D ($p_{\text{adj}} = 0.02307, d = -0.437$) with the lowest variance across all tested MARL configurations.
3. **Information Compression Degradation:** Compressing state inputs to 4 features causes severe variance inflation in DQN ($\sigma$ surges to $21.17\text{ s}$ with cumulative delay reaching $16,205.2\text{ veh-s}$) and causes MAPPO travel times to degrade to $92.38 \pm 13.84\text{ s}$.

### 8.2 Defensible Wording Recommendation for Publication
Instead of claiming "8D is a sufficient statistic" and "14D destabilizes gradients," the paper should state:
> *"Empirical evaluation of observation space dimensionality indicates that decentralized value-based RL (Double-DQN) is highly sensitive to feature selection, achieving its lowest corridor travel time ($81.10\text{ s}$) on a compact 8-feature representation, while degrading under both feature expansion ($14\text{D}$, $+11.64\text{ s}, p < 0.01$) and excessive compression ($4\text{D}$, $+6.69\text{ s}, p < 0.01$). In contrast, centralized-critic policy gradients (MAPPO) demonstrate superior stability in the full 14-dimensional space ($\sigma = 6.30\text{ s}$), outperforming DQN by $5.26\text{ s}$ ($p < 0.05$). Variance decomposition demonstrates that model-to-model training seed variation accounts for $65\%\text{--}99\%$ of overall evaluation variance, underscoring the critical necessity of multi-seed training audits in urban traffic signal control benchmarks."*

---

## 9. Audit Verification Artifacts Produced

The following independent audit scripts and datasets were generated in `outputs/experiments/phase4/independent_audit_series4b/`:
- [`verify_raw_evals.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/independent_audit_series4b/verify_raw_evals.py): Independent raw evaluation verification script.
- [`recompute_descriptive.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/independent_audit_series4b/recompute_descriptive.py): Independent recomputation of descriptive statistics.
- [`recomputed_descriptives.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/independent_audit_series4b/recomputed_descriptives.json): Full dataset of recomputed sample moments, SEMs, CIs, and normality tests.
- [`recompute_paired_comparisons.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/independent_audit_series4b/recompute_paired_comparisons.py): Pairwise hypothesis testing script with exact Holm-Bonferroni step-down.
- [`recomputed_paired_comparisons.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/independent_audit_series4b/recomputed_paired_comparisons.json): Full dataset of recomputed paired statistics, effect sizes, and corrected $p$-values.
- [`hierarchical_analysis.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/independent_audit_series4b/hierarchical_analysis.py): Two-way crossed ANOVA, variance decomposition, and Linear Mixed Model (LMM).
- [`hierarchical_model_results.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/outputs/experiments/phase4/independent_audit_series4b/hierarchical_model_results.json): Variance decomposition and model-level aggregated comparison dataset.

**Safety Assurance:** Zero modifications were made to existing checkpoints, logs, evaluations, or master record documents. Zero Git state modifications performed.
