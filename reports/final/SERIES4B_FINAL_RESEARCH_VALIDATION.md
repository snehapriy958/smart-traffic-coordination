# SERIES 4B FINAL RESEARCH VALIDATION REPORT
**Experiment**: Series 4B — State Observation Dimensionality Ablation Study  
**Algorithms**: MAPPO and Double-DQN  
**Dimensionality Variants**: 4D, 8D, and 14D per junction  
**Experimental Design**: 6 Configurations $\times$ 5 Training Seeds (101–105) $\times$ 150 Episodes $\times$ 10 Evaluation Seeds (1–10) = **300 Total Evaluations**  
**Dataset Status**: **FROZEN & CERTIFIED** in `outputs/experiments/phase4/series4b_final_validation/`  
**Date**: November 17, 2026  
**Auditor Roles**: Senior Reinforcement Learning Researcher, Biostatistician, Independent Auditor  

---

## 1. Executive Summary & Core Scientific Findings

Series 4B is the largest completed empirical ablation in the project, consisting of 30 distinct trained neural network checkpoints and 300 independent microscopic simulation evaluations along the Silk Board corridor.

### Primary Scientific Findings:
1. **The Pseudoreplication Trap (Model-Level vs Evaluation-Level Variance)**:
   - When evaluating traffic RL policies, running $M=10$ evaluation seeds on $K=5$ trained models yields $N=50$ evaluation records per configuration.
   - Naive evaluation-level statistical tests (treating $N=50$ as independent observations) erroneously report highly significant differences ($p < 0.001$) between observation dimensions.
   - However, hierarchical Linear Mixed-Effects Modeling (LMM) and 10,000-iteration Cluster Bootstrap prove that **$91.6\%$ of the total variance is driven by training seed stochasticity** (between-model variance $\sigma_{\text{model}}^2 = 217.18$), while only **$8.4\%$** is attributable to evaluation seed noise ($\sigma_{\text{eval}}^2 = 19.90$).
2. **DQN 8D vs. DQN 14D Generalization**:
   - In evaluation-level summary tables, DQN 8D exhibited the lowest raw mean travel time ($81.1\,\text{s}$ vs $92.7\,\text{s}$ for DQN 14D).
   - At the proper **model level ($K=5$ independent models, $\text{df}=4$)**, the cluster bootstrap difference is $\Delta = -11.75\,\text{s}$ with a $95\%$ bootstrap confidence interval of **$[-24.11, +7.25]$** and an empirical $p$-value of **$p = 0.133$**.
   - **Conclusion**: There is **no statistically significant advantage** of DQN 8D over DQN 14D at the model population level.
3. **MAPPO 14D Variance Reduction**:
   - MAPPO 14D demonstrated substantially lower variance across its 5 trained models compared to DQN 14D. However, its mean difference over DQN 14D ($\Delta = -5.33\,\text{s}$, $95\%\,\text{CI} = [-12.84, +4.51]$, $p = 0.276$) is not statistically significant.

---

## 2. Configuration Model-Level Summary Table ($K=5$ Models per Config)

```
┌───────────────┬─────────────────────────┬─────────────────────────┬─────────────────────────┬──────────────────────┐
│ Configuration │ Mean Travel Time ($s$)   │ Between-Model SD ($s$)  │ Evaluation-Level SD ($s$)│ Mean Corridor Delay  │
├───────────────┼─────────────────────────┼─────────────────────────┼─────────────────────────┼──────────────────────┤
│ DQN 4D        │ 87.79 ± 7.55 s          │ 16.89 s                 │ 17.65 s                 │ 11,842 veh·s         │
│ DQN 8D        │ 81.10 ± 8.76 s          │ 19.58 s                 │ 20.31 s                 │ 10,784 veh·s         │
│ DQN 14D       │ 92.75 ± 6.64 s          │ 14.85 s                 │ 15.68 s                 │ 12,965 veh·s         │
│ MAPPO 4D      │ 92.38 ± 8.64 s          │ 19.32 s                 │ 20.08 s                 │ 12,876 veh·s         │
│ MAPPO 8D      │ 85.65 ± 7.22 s          │ 16.15 s                 │ 16.92 s                 │ 11,452 veh·s         │
│ MAPPO 14D     │ 87.48 ± 3.48 s          │  7.78 s                 │  9.12 s                 │ 11,731 veh·s         │
└───────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┴──────────────────────┘
```

---

## 3. Hierarchical Linear Mixed-Effects Model (LMM) Decomposition

To rigorously separate model training variance from evaluation seed variance, three nested models were evaluated:
- **Model 1 (Audit Baseline)**: Grouped by numeric seed integer (Treats independent training runs as repeated measures). Log-Likelihood = $-1192.97$, Residual Variance = $175.23$. Rejected as mathematically inappropriate.
- **Model 2 (Nested Model ID)**: Correctly nests 10 evaluation runs within each unique trained checkpoint (30 levels):
  $$\text{TravelTime}_{ij} = \mu + \text{Config}_i + u_{\text{model}(i)} + \epsilon_{ij}, \quad u_{\text{model}} \sim \mathcal{N}(0, \sigma_{\text{model}}^2), \quad \epsilon_{ij} \sim \mathcal{N}(0, \sigma_{\text{eval}}^2)$$
  - **Between-Model Variance ($\sigma_{\text{model}}^2$)**: **$217.18$** ($91.60\%$ of total variance)
  - **Within-Model Residual Variance ($\sigma_{\text{eval}}^2$)**: **$19.90$** ($8.40\%$ of total variance)
  - **Intraclass Correlation (ICC)**:
    $$\text{ICC} = \frac{\sigma_{\text{model}}^2}{\sigma_{\text{model}}^2 + \sigma_{\text{eval}}^2} = \frac{217.18}{217.18 + 19.90} = \mathbf{0.916}$$
- **Model 3 (Crossed Random Effects)**: Model ID (30 levels) + Evaluation Seed (10 levels). Confirmed that crossed evaluation seed variance is negligible ($\le 0.05$).

---

## 4. 10,000-Iteration Cluster Bootstrap Comparisons

Pairs resampled across clusters (trained models) with $B = 10{,}000$ iterations:

| Comparison | Mean Difference ($s$) | Bootstrap Std ($s$) | 95% Bootstrap CI | Empirical $p$-value | Model-Level Significance |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **DQN 8D vs. DQN 14D** | $-11.75\,\text{s}$ | $8.52\,\text{s}$ | $[-24.11, +7.25]$ | $0.1330$ | **Not Significant ($p \ge 0.05$)** |
| **DQN 8D vs. DQN 4D** | $-6.69\,\text{s}$ | $4.90\,\text{s}$ | $[-17.44, +1.57]$ | $0.1448$ | **Not Significant ($p \ge 0.05$)** |
| **14D: MAPPO vs. DQN** | $-5.33\,\text{s}$ | $4.51\,\text{s}$ | $[-12.84, +4.51]$ | $0.2758$ | **Not Significant ($p \ge 0.05$)** |
| **8D: MAPPO vs. DQN** | $+4.57\,\text{s}$ | $12.01\,\text{s}$ | $[-23.27, +23.55]$ | $0.5914$ | **Not Significant ($p \ge 0.05$)** |
| **4D: MAPPO vs. DQN** | $+4.60\,\text{s}$ | $3.66\,\text{s}$ | $[-2.47, +11.58]$ | $0.2122$ | **Not Significant ($p \ge 0.05$)** |
| **MAPPO 14D vs. 8D** | $+1.91\,\text{s}$ | $5.88\,\text{s}$ | $[-10.18, +12.11]$ | $0.7470$ | **Not Significant ($p \ge 0.05$)** |
| **MAPPO 14D vs. 4D** | $-4.82\,\text{s}$ | $7.73\,\text{s}$ | $[-22.70, +6.96]$ | $0.5936$ | **Not Significant ($p \ge 0.05$)** |

---

## 5. Methodological Guidelines for Research Paper
1. **Never Cite Evaluation-Level $p$-values as Proof of Model Superiority**: Citing $N=50$ inflated sample sizes in deep RL without clustering violates statistical independence assumptions.
2. **Report Model-Level Point Estimates & Bootstrap Intervals**: Disclose that DQN 8D and MAPPO 14D show promising empirical trends, but between-seed model training variance dominates.
3. **Framing the Contribution**: Series 4B provides a valuable methodological contribution: it empirically demonstrates the necessity of multi-model hierarchical evaluations in urban traffic signal RL.

---

## 6. Phase 6 Verification Verdict: **VERIFIED & FROZEN**
Series 4B artifacts, checkpoints, and statistical decompositions are fully verified, preserved, and scientifically sound.
