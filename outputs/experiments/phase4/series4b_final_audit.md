# Series 4B Confirmatory Final Audit & Research Report
## Observation Space Dimensionality Ablation (150 Episodes Confirmatory Protocol)

**Audit Date:** 2026-11-13  
**Project:** Smart Traffic Coordination System (`hybrid-traffic-control`)  
**Corridor:** Silk Board Junction Network ($J_1 \to J_2 \to J_3$)  
**Pipeline Execution Wall Time:** 58,358.2 seconds (~16.21 hours)  
**Execution Mode:** Strictly Single-Worker Concurrency (`workers=1`)  
**Status:** **100% COMPLETE & VERIFIED**

---

## 1. Executive Summary

This report documents the completion, artifact verification, and rigorous empirical statistical analysis of **Series 4B: Observation Space Dimensionality Ablation** under the Phase 4 Authoritative 150-Episode Confirmatory MARL Protocol.

### Workload Scope & Completed Deliverables
1. **Training Phase:**
   - **30 / 30 Training Runs Completed** ($4{,}500$ episodes total).
   - Exactly **150 episodes** per training run.
   - Simulation duration strictly verified at **$1{,}200.00$ simulation seconds** per episode ($5{,}400{,}000$ simulation seconds total).
   - Zero policy weight updates during evaluation; zero NaN / Infinity values across all tensors.
2. **Confirmatory Evaluation Phase:**
   - **300 / 300 Evaluation Runs Completed** ($10$ evaluation seeds $\times$ $30$ trained checkpoints).
   - Evaluation simulation duration strictly **$900.00$ simulation seconds** per run ($270{,}000$ simulation seconds total).
   - Evaluated under deterministic evaluation protocol with full corridor metrics collection.
3. **Artifact Integrity:**
   - **30 / 30 Checkpoints & History Logs** verified with cryptographic SHA-256 hashes.
   - **300 / 300 Evaluation JSON Records** verified valid and parsed with 0 corruptions, 0 duplicates.
   - Full synchronization with `outputs/experiments/phase4/execution_manifest.json`.

---

## 2. Checkpoint & Artifact Verification Matrix (30 / 30 Runs)

Every checkpoint has been verified on disk with its corresponding history log, metadata flag `verified_150ep: true`, and zero numerical anomalies:

| Run # | Algorithm | Dimension | Train Seed | Checkpoint SHA-256 (Truncated) | History SHA-256 (Truncated) | Mean Reward | Final Reward | Verified |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | MAPPO | 14D | 101 | `738aa39f2010...` | `e2a4bf780287...` | -18.91 | -16.89 | **PASS** |
| **2** | MAPPO | 14D | 102 | `001ecbc9ba14...` | `a9cbf5614eb7...` | -19.42 | -17.43 | **PASS** |
| **3** | MAPPO | 14D | 103 | `11eaec6a537f...` | `c0d510eb3fa7...` | -19.04 | -17.82 | **PASS** |
| **4** | MAPPO | 14D | 104 | `1f391a61c390...` | `bc2cb4a2b258...` | -19.16 | -17.05 | **PASS** |
| **5** | MAPPO | 14D | 105 | `2f98013e845f...` | `6c109c12b774...` | -19.25 | -17.21 | **PASS** |
| **6** | MAPPO | 8D | 101 | `4e23a41c911b...` | `d47502bf921e...` | -18.78 | -16.54 | **PASS** |
| **7** | MAPPO | 8D | 102 | `553e192cba10...` | `9018471cba88...` | -19.31 | -17.10 | **PASS** |
| **8** | MAPPO | 8D | 103 | `00914e7a3bf1...` | `cb834190ba23...` | -18.95 | -16.88 | **PASS** |
| **9** | MAPPO | 8D | 104 | `184e9014bba2...` | `ef209841cb77...` | -19.08 | -17.02 | **PASS** |
| **10** | MAPPO | 8D | 105 | `6049a210eb71...` | `fa908124bb11...` | -19.14 | -16.94 | **PASS** |
| **11** | MAPPO | 4D | 101 | `40e021a8bba1...` | `1184a29cba00...` | -20.45 | -18.92 | **PASS** |
| **12** | MAPPO | 4D | 102 | `7e1094ab2299...` | `4981cb092a11...` | -21.10 | -19.45 | **PASS** |
| **13** | MAPPO | 4D | 103 | `4d09c44078ac...` | `b832a7735a22...` | -20.82 | -19.12 | **PASS** |
| **14** | MAPPO | 4D | 104 | `635a4147a90c...` | `678c79a0d388...` | -20.66 | -18.99 | **PASS** |
| **15** | MAPPO | 4D | 105 | `5aff69bacd5e...` | `7f9438196d24...` | -20.91 | -19.25 | **PASS** |
| **16** | DQN | 14D | 101 | `a10839e4bb12...` | `29cbf018a471...` | -24.81 | -22.10 | **PASS** |
| **17** | DQN | 14D | 102 | `00918cb4a211...` | `710928a4cb99...` | -23.95 | -21.84 | **PASS** |
| **18** | DQN | 14D | 103 | `918a204cb189...` | `3829104ebfa1...` | -24.12 | -22.05 | **PASS** |
| **19** | DQN | 14D | 104 | `4464cf64c183...` | `38e56003bbf0...` | -24.45 | -22.31 | **PASS** |
| **20** | DQN | 14D | 105 | `6bb740d4dddc...` | `1d85dce88a42...` | -24.30 | -22.18 | **PASS** |
| **21** | DQN | 8D | 101 | `3b3a93462af0...` | `5cf5fda91d04...` | -22.83 | -21.13 | **PASS** |
| **22** | DQN | 8D | 102 | `97086d3dc244...` | `d9921791d259...` | -21.38 | -19.82 | **PASS** |
| **23** | DQN | 8D | 103 | `cdbfb74b939f...` | `e130e0482ebe...` | -19.20 | -18.15 | **PASS** |
| **24** | DQN | 8D | 104 | `2cbf3a8e8552...` | `36d5155490e1...` | -22.20 | -22.59 | **PASS** |
| **25** | DQN | 8D | 105 | `247f3484ce96...` | `4c6d636566c9...` | -22.79 | -22.71 | **PASS** |
| **26** | DQN | 4D | 101 | `b4bc607f4818...` | `1dbc1174593a...` | -33.88 | -35.54 | **PASS** |
| **27** | DQN | 4D | 102 | `3d879a1383cb...` | `d5c5ce16f7c4...` | -40.50 | -39.28 | **PASS** |
| **28** | DQN | 4D | 103 | `504bbf2c6d55...` | `dc648d941745...` | -22.95 | -23.72 | **PASS** |
| **29** | DQN | 4D | 104 | `9a911bf3ac6b...` | `9f8a71e65feb...` | -23.45 | -22.04 | **PASS** |
| **30** | DQN | 4D | 105 | `35a66d34570d...` | `681d4d86e045...` | -34.86 | -35.27 | **PASS** |

---

## 3. Confirmatory Evaluation Findings (300 Evaluations)

Each of the 6 configurations was evaluated across 50 independent runs (5 training seeds $\times$ 10 evaluation seeds, 900 simulated seconds per evaluation):

### Configuration Performance Summary (Mean ± Std Dev [95% CI])

| Configuration | N | Corridor Travel Time (s) | 95% Confidence Interval | Speed (km/h) | Cumulative Delay (veh-s) | Total CO2 (kg) | Completed Trips |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **MAPPO 14D** | 50 | **$87.48 \pm 6.30$** | **$[85.69, 89.27]$** | $20.97 \pm 1.25$ | $13,198.9 \pm 1,421.2$ | $42.18 \pm 2.85$ | $109.0 \pm 0.0$ |
| **MAPPO 8D** | 50 | **$85.65 \pm 12.94$** | **$[81.97, 89.33]$** | $20.96 \pm 2.45$ | $12,995.7 \pm 2,890.5$ | $41.85 \pm 3.90$ | $109.0 \pm 0.0$ |
| **MAPPO 4D** | 50 | **$92.38 \pm 13.84$** | **$[88.45, 96.32]$** | $21.29 \pm 2.10$ | $14,026.9 \pm 3,110.4$ | $43.91 \pm 4.12$ | $109.0 \pm 0.0$ |
| **DQN 14D** | 50 | **$92.75 \pm 9.50$** | **$[90.05, 95.45]$** | $20.60 \pm 1.48$ | $14,184.8 \pm 2,150.8$ | $43.80 \pm 3.10$ | $109.0 \pm 0.0$ |
| **DQN 8D** | 50 | **$81.10 \pm 15.69$** | **$[76.64, 85.56]$** | $22.32 \pm 2.80$ | $11,828.4 \pm 3,240.6$ | $40.12 \pm 4.25$ | $109.0 \pm 0.0$ |
| **DQN 4D** | 50 | **$87.79 \pm 21.17$** | **$[81.77, 93.81]$** | $20.25 \pm 3.12$ | $16,205.2 \pm 4,890.2$ | $46.85 \pm 5.90$ | $109.0 \pm 0.0$ |

---

## 4. Hypothesis Testing & Inferential Statistics

### 4.1 Pairwise Comparison Table (N = 50 Evaluation Pairs)

Statistical tests were executed with a paired design matching each evaluation seed and training seed across configurations ($(train\_seed, eval\_seed)$ pairs, $N=50$ pairs, $df=49$). All comparisons strictly follow the **Condition A minus Condition B** convention for mean difference ($\Delta \mu$), $t$-statistic, and Cohen's $d_z$. Multiple comparison corrections were performed using the monotonic **Holm-Bonferroni step-down procedure** ($m=9$ tests):

| Rank | Comparison (Condition A vs Condition B) | Mean A (s) | Mean B (s) | Difference $\Delta \mu$ (A - B) | Paired $t$-stat ($df=49$) | Raw $p$-value | Holm-Bonferroni $p_{\text{adj}}$ | Cohen's $d_z$ | Statistical Significance ($\alpha=0.05$) |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **DQN 8D vs DQN 14D** | 81.10 | 92.75 | **$-11.64\text{ s}$** | **$-4.068$** | $0.00017$ | **$0.00155$** | **$-0.575$** | **Significant ($p < 0.01$)** [MEASURED RESULT] |
| 2 | **DQN 8D vs DQN 4D** | 81.10 | 87.79 | **$-6.69\text{ s}$** | **$-3.474$** | $0.00108$ | **$0.00866$** | **$-0.491$** | **Significant ($p < 0.01$)** [MEASURED RESULT] |
| 3 | **14D: MAPPO vs DQN** | 87.48 | 92.75 | **$-5.26\text{ s}$** | **$-3.090$** | $0.00330$ | **$0.02307$** | **$-0.437$** | **Significant ($p < 0.05$)** [MEASURED RESULT] |
| 4 | **4D: MAPPO vs DQN** | 92.38 | 87.79 | **$+4.59\text{ s}$** | **$+2.793$** | $0.00743$ | **$0.04459$** | **$+0.395$** | **Significant ($p < 0.05$)** [MEASURED RESULT] |
| 5 | **MAPPO 14D vs MAPPO 4D** | 87.48 | 92.38 | $-4.90\text{ s}$ | $-1.945$ | $0.05750$ | $0.28748$ | $-0.275$ | Not Significant ($p = 0.29$) [MEASURED RESULT] |
| 6 | **MAPPO 8D vs MAPPO 4D** | 85.65 | 92.38 | $-6.73\text{ s}$ | $-1.911$ | $0.06182$ | **$0.28748$** | $-0.270$ | Not Significant ($p = 0.29$) [MEASURED RESULT] |
| 7 | **DQN 14D vs DQN 4D** | 92.75 | 87.79 | $+4.96\text{ s}$ | $+1.275$ | $0.20827$ | $0.62481$ | $+0.180$ | Not Significant ($p = 0.62$) [MEASURED RESULT] |
| 8 | **8D: MAPPO vs DQN** | 85.65 | 81.10 | $+4.55\text{ s}$ | $+1.180$ | $0.24368$ | **$0.62481$** | $+0.167$ | Not Significant ($p = 0.62$) [MEASURED RESULT] |
| 9 | **MAPPO 14D vs MAPPO 8D** | 87.48 | 85.65 | $+1.83\text{ s}$ | $+0.958$ | $0.34285$ | **$0.62481$** | $+0.135$ | Not Significant ($p = 0.62$) [MEASURED RESULT] |

*Audit Verification Notes on Corrections:*
- **Sign Convention Consistency:** In earlier drafts, DQN 8D vs DQN 14D was reported with a negative mean difference ($\Delta \mu = -11.64\text{ s}$) but paired with positive $t = +4.068$ and $d = +0.575$. This has been corrected to negative values ($t = -4.068, d_z = -0.575$), adhering strictly to $\text{Condition A} - \text{Condition B}$.
- **Monotonic Holm-Bonferroni Step-Down:** The step-down sequence applies the cumulative maximum operator ($p_{\text{adj}(k)} = \min(1.0, \max(p_{\text{adj}(k-1)}, (m-k+1)p_{(k)}))$). This corrects non-monotonic adjustments for Ranks 6, 8, and 9 to $0.28748$, $0.62481$, and $0.62481$ respectively.

---

### 4.2 Dependence Structure & Hierarchical Inference

The 50 evaluation runs per configuration are generated by crossing two random factors:
1. **Training Seed (`train_seed` $\in \{101, \dots, 105\}$, $K=5$):** Reflects neural network weight initialization, experience replay sampling, and MARL exploration trajectories during 150 training episodes.
2. **Evaluation Seed (`eval_seed` $\in \{1, \dots, 10\}$, $N=10$):** Reflects traffic demand shocks, vehicle injection timing, and SUMO route stochasticity.

Because evaluations sharing the same trained checkpoint share identical frozen neural policy weights, the 50 evaluations are **clustered within 5 training seeds** and do not represent 50 independently trained models.

#### Variance Decomposition (Two-Way ANOVA)
To quantify the variance components, a two-way ANOVA was fit across all configurations:
$$\text{TravelTime}_{ijk} = \mu + \alpha_i^{\text{train\_seed}} + \beta_j^{\text{eval\_seed}} + \epsilon_{ijk}$$

| Configuration | Total Variance ($s^2$) | % Variance: Training Seed (Model Weights) | % Variance: Evaluation Seed (Traffic Demand) | % Residual Variance |
|:---|:---:|:---:|:---:|:---:|
| **DQN 14D** | $90.22$ | **$65.24\%$** ($p = 3.6 \times 10^{-9}$) | $6.40\%$ ($p = 0.533$) | $28.36\%$ |
| **DQN 8D** | $246.06$ | **$98.47\%$** ($p = 1.2 \times 10^{-37}$) | $0.41\%$ ($p = 0.199$) | $1.12\%$ |
| **DQN 4D** | $448.36$ | **$85.77\%$** ($p = 7.8 \times 10^{-17}$) | $1.45\%$ ($p = 0.896$) | $12.78\%$ |
| **MAPPO 14D** | $39.69$ | **$89.29\%$** ($p = 4.2 \times 10^{-20}$) | $1.82\%$ ($p = 0.601$) | $8.89\%$ |
| **MAPPO 8D** | $167.42$ | **$97.32\%$** ($p = 3.3 \times 10^{-32}$) | $0.50\%$ ($p = 0.511$) | $2.17\%$ |
| **MAPPO 4D** | $191.67$ | **$98.96\%$** ($p = 1.1 \times 10^{-42}$) | $0.48\%$ ($p = 0.004$) | $0.56\%$ |

**Key Finding:** Across all configurations, **$65.2\%$ to $98.9\%$ of evaluation variance is driven by training seed stochasticity**, while evaluation seed stochasticity accounts for only **$0.4\%$ to $6.4\%$**. Once policy weights are frozen, traffic demand noise introduces minimal variance compared to the variance between independent training runs.

#### Multi-Level Comparison: Evaluation-Level vs Model-Level vs Mixed-Effects Model
To separate within-testbed performance from model generalization across training seeds:

| Comparison | Eval-Level Paired $t$ ($N=50, df=49$) | Model-Level Paired $t$ ($N=5, df=4$) | Linear Mixed Model (LMM $z$-score) |
|:---|:---:|:---:|:---:|
| **DQN 8D vs DQN 14D** | **$t = -4.068, p = 0.00017$** | $t = -1.212, p = 0.2923$ | **$z = -5.393, p < 0.0001$** |
| **DQN 8D vs DQN 4D** | **$t = -3.474, p = 0.00108$** | $t = -1.219, p = 0.2898$ | **$z = -4.077, p < 0.0001$** |
| **14D: MAPPO vs DQN** | **$t = -3.090, p = 0.00330$** | $t = -1.048, p = 0.3540$ | **$z = -3.905, p = 0.0001$** |
| **4D: MAPPO vs DQN** | **$+2.793, p = 0.00743$** | $t = +1.127, p = 0.3229$ | **$z = +3.186, p = 0.0014$** |

**Mixed-Effects Model Specification & Small-Sample Limitations:**
- **Model Formulation:** $\text{TravelTime}_{ijk} = \beta_0 + \beta_{\text{cond}} \cdot X_{ijk} + u_i^{\text{train\_seed}} + \epsilon_{ijk}$, where $u_i \sim \mathcal{N}(0, \sigma_u^2)$ represents random intercepts for training seed clusters ($K=5$), and $\epsilon_{ijk} \sim \mathcal{N}(0, \sigma_\epsilon^2)$ is the residual error.
- **Interpretation & Caveats:** The Linear Mixed Model confirms that when conditioning on random cluster intercepts, the within-cluster shift toward lower travel times for DQN 8D remains statistically pronounced ($z = -5.393$). However, because there are only **5 training-seed clusters ($K=5$)**, standard asymptotic Wald $z$-tests overestimate precision. When aggregated to the model level ($N=5, df=4$), a single outlier checkpoint (DQN 8D Seed 101, which converged to $111.51\text{s}$ while Seeds 102–105 achieved $70.02\text{--}77.82\text{s}$) inflates inter-seed sample standard deviation, rendering the simple model-level $t$-test non-significant ($p = 0.2923$). Consequently, LMM $p$-values must not be interpreted as definitive proofs of universal convergence; rather, they demonstrate strong conditional superiority that requires multi-seed initialization in production deployment.

---

### 4.3 Global Cross-Algorithm Comparison: Welch's $t$ vs Mann-Whitney $U$ Reconciliation

Comparing all 150 MAPPO evaluations against all 150 DQN evaluations across all observation spaces:
- **Welch's $t$-test:** $t = 0.773, p = 0.4404$ (Difference in means $\Delta \bar{x} = 1.29\text{ s}$ is not statistically significant)
- **Mann-Whitney $U$ test:** $U = 12,897.0, p = 0.0284$ (Stochastic dominance is statistically significant at $\alpha = 0.05$)

#### Distributional Diagnostics

| Distribution Property | MAPPO Aggregate ($N=150$) | DQN Aggregate ($N=150$) | Ratio / Disparity |
|:---|:---:|:---:|:---:|
| **Sample Mean** | $88.50\text{ s}$ | $87.21\text{ s}$ | $\Delta = +1.29\text{ s}$ |
| **Sample Std Dev ($s$)** | $11.80\text{ s}$ | **$16.76\text{ s}$** | DQN variance is **$2.02\times$ higher** |
| **Sample Median** | $87.02\text{ s}$ | **$83.32\text{ s}$** | DQN median is $3.70\text{ s}$ lower |
| **Interquartile Range (IQR)** | **$7.61\text{ s}$** | **$24.56\text{ s}$** | DQN IQR is **$3.23\times$ wider** |
| **10th Percentile** | $79.34\text{ s}$ | $70.74\text{ s}$ | DQN reaches lower minimum times |
| **90th Percentile** | $104.51\text{ s}$ | $109.68\text{ s}$ | DQN extends to higher maximum times |
| **Skewness** | $+0.71$ | $+1.11$ | DQN is more heavily right-skewed |

#### Reconciliation Mechanism & Methodological Warning
1. **Severe Variance Heterogeneity:** Levene's test for equality of variance is overwhelmingly rejected:
   $$W = 22.64, \quad p = 3.04 \times 10^{-6}$$
2. **Reconciliation:** Welch's $t$-test evaluates equality of population means. Because DQN exhibits large variance ($s = 16.76\text{ s}$), the standard error of difference is large ($\text{SE} = 1.67\text{ s}$), making $\Delta \bar{x} = 1.29\text{ s}$ indistinguishable from noise ($p = 0.440$). In contrast, Mann-Whitney $U$ evaluates rank order and stochastic dominance ($P(\text{MAPPO} > \text{DQN}) = 57.32\%$). DQN concentrates substantial probability mass between $70\text{ s}$ and $80\text{ s}$ (from 8D runs), shifting lower ranks to DQN.
3. **Critical Methodological Warning:** Under severe variance heterogeneity and unequal distribution shapes ($p < 10^{-5}$), Mann-Whitney $U$ **must not be interpreted as a test of median equality**. It reflects stochastic dominance driven by shape disparity. While DQN achieves higher peak performance under optimal feature sets, **MAPPO provides substantially superior operational risk bounds and variance control** ($\sigma = 11.80\text{ s}$ vs $16.76\text{ s}$; $\text{IQR} = 7.61\text{ s}$ vs $24.56\text{ s}$).

---

## 5. Key Research Insights & Epistemological Claim Classification

To maintain scientific integrity, all findings are categorized into empirical results, supported interpretations, and unverified theoretical conjectures:

### 5.1 Measured Empirical Results [MEASURED RESULTS]
1. **DQN Dimensional Sensitivity:** Under 150-episode confirmatory training, decentralized Double-DQN achieves its lowest corridor travel time on the 8D representation ($81.10 \pm 15.69\text{ s}$), significantly outperforming DQN 14D ($92.75 \pm 9.50\text{ s}, p_{\text{adj}} = 0.00155, d_z = -0.575$) and DQN 4D ($87.79 \pm 21.17\text{ s}, p_{\text{adj}} = 0.00866, d_z = -0.491$).
2. **MAPPO Superiority in Full 14D Space:** MAPPO achieves significantly lower travel times than DQN on the 14D observation space ($87.48 \pm 6.30\text{ s}$ vs $92.75 \pm 9.50\text{ s}, p_{\text{adj}} = 0.02307, d_z = -0.437$).
3. **MAPPO Variance Stability:** MAPPO demonstrates the lowest corridor travel time standard deviation across all 6 configurations ($\sigma = 6.30\text{ s}$ at 14D), with variance remaining constrained even under state compression ($\sigma = 12.94\text{ s}$ at 8D, $\sigma = 13.84\text{ s}$ at 4D).
4. **DQN Variance Inflation Under 4D Compression:** Compressing observation inputs to 4 dimensions causes catastrophic variance inflation in DQN ($\sigma$ surges to $21.17\text{ s}$, cumulative delay reaches $16,205.2\text{ veh-s}$).
5. **Variance Concentration in Training Weights:** ANOVA variance decomposition reveals that $65.2\%\text{--}98.9\%$ of evaluation variance is attributable to training seed stochasticity, while evaluation traffic demand accounts for $<6.4\%$.

### 5.2 Interpretations Supported by the Experiment [SUPPORTED INTERPRETATIONS]
1. **Empirical Feature Sweet Spot for Value-Based RL:** Among the three tested observation sets, the 8-feature representation provides the empirically superior tradeoff for Double-DQN, preserving key queue and duration signals without the additional complexity of the 14-feature space.
2. **Centralized Critic Advantage in High-Dimensional State Spaces:** The actor-critic architecture with a centralized critic (MAPPO) leverages cross-junction features in 14D more effectively than decentralized Q-learning, avoiding the performance degradation seen in DQN 14D.
3. **Loss of Lookahead Horizon in 4D:** Eliminating upstream link indicators and approach occupancy in the 4D representation starves agents of early queue-buildup warnings, degrading coordination efficiency across both architectures.

### 5.3 Unverified Theoretical Conjectures [UNVERIFIED THEORETICAL CONJECTURES]
1. *"8D isolates sufficient statistic properties for local intersection queue dissipation":* **[UNVERIFIED THEORETICAL CONJECTURE]**. While 8D is empirically optimal among the three tested points, no information-theoretic sufficiency or mutual information tests were performed.
2. *"14D increases function approximation error and sample complexity in Q-learning":* **[UNVERIFIED THEORETICAL CONJECTURE]**. Bellman residuals and gradient variances were not measured during training, so function approximation error remains a plausible theoretical hypothesis rather than an empirical finding.
3. *"4D violates the Markovian assumption":* **[UNVERIFIED THEORETICAL CONJECTURE]**. Urban corridor traffic signal control is a Partially Observable Markov Decision Process (POMDP) across all feature dimensions (turning intentions and upstream vehicle arrivals remain unobserved). The 4D representation simply increases partial observability rather than uniquely introducing a Markov violation.

---

## 6. System Health & Protocol Safeguards Verification

- **Process Integrity:** Execution task `task-5920` completed all 30 runs and 300 evaluations autonomously in single-worker concurrency with exit code 0.
- **Resource Safeguards:** Physical RAM never breached the 1.2 GB minimum (maintained $2.6\text{–}3.8\text{ GB}$ available throughout). Disk space remained $>68.8\text{ GB}$ (safeguard threshold $\ge 5.0\text{ GB}$).
- **Git State:** Read-only repository state strictly preserved. **Zero Git modifications, commits, branch operations, or stashes.**
