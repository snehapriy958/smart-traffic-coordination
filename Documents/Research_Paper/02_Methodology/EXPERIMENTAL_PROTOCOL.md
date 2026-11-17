# Experimental Protocol & Evaluation Design

## 1. Protocol Architecture
- **Controllers**: 4 signal controllers (Fixed-Time Baseline, Coordinated Adaptive, Dueling Double-DQN, Multi-Agent PPO).
- **Random Seeds**: 10 matched seeds (Seeds 1, 2, 3, 4, 5, 6, 7, 8, 9, 10).
- **Total Execution Runs**: $4 \times 10 = 40$ isolated runs.
- **Horizon**: $900.0\text{ s}$ per run.
- **Execution Script**: `scripts/run_10seed_validation.py`.
- **Output Storage**: `outputs/validation/10seeds/runs/run_{mode}_seed{seed}.json`.

## 2. Statistical Testing Standards
All metrics are evaluated under rigorous hypothesis testing:
1. **Paired Differences**: $\Delta_i = x_{i, \text{controller}} - x_{i, \text{baseline}}$ computed across identical seed $i$.
2. **Two-Tailed Paired Student's t-Test**: Evaluated at $df = N - 1 = 9$ with $t_{\text{crit}} = 2.26216$ ($lpha = 0.05$).
3. **Multiple Testing Correction**: Holm-Bonferroni adjustment across $m = 3$ pairwise comparisons against baseline (adjusted threshold $\alpha_{\text{adj}} = 0.0167$).
4. **Effect Size**: Cohen's $d_z = \frac{|\bar{\Delta}|}{s_{\Delta}}$ for paired samples ($d_z > 0.8$ denotes large effect; $> 2.0$ denotes massive effect).
5. **Non-Parametric Validation**: Two-sided Wilcoxon signed-rank test.
