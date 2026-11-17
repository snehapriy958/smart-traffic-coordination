# Scientific Claim Verification Register & Retraction Audit

**Document ID:** HTC-AUDIT-PHASE8-CLAIMS  
**Timestamp:** 2026-11-17T13:53:00+05:30  
**Classification:** Authoritative Scientific Evidence Audit & Research Integrity Register  
**Auditor:** Principal Research Auditor & Scientific Integrity Committee  

---

## 1. Scope & Objective

This register classifies every major claim asserted in previous design documents, presentations, and draft summaries across the **Bengaluru Traffic Intelligence Platform (Hybrid Traffic Control)**. 

To preserve unimpeachable academic and scientific integrity, each claim is classified under one of four unambiguous evidential tiers:
1. **TIER 1: VERIFIED SCIENTIFIC FACT** — Backed by reproducible data, paired hypothesis testing, and complete artifacts.
2. **TIER 2: PRELIMINARY EMPIRICAL RESULT** — Preliminary empirical evidence from partial runs; directionally informative but incomplete.
3. **TIER 3: RETRACTED / ERRONEOUS CLAIM** — Unsupported by underlying data, cherry-picked from single seeds, or artifact of evaluation saturation.
4. **TIER 4: SCOPE DISCLAIMER / SIMULATION BOUNDARY** — Simulated microscopic research findings requiring explicit boundary disclaimers against real-world field claims.

---

## 2. Master Verification Register

| Claim ID | Category | Original Claim Statement | Evidential Status | Ground Truth Data & Verification Findings | Required Rectification |
|---|---|---|---|---|---|
| **CLM-01** | Coordinated Control | Coordinated Adaptive Controller achieves $-44.60\%$ travel time reduction over Fixed-Time. | **TIER 1: VERIFIED** | Validated across 10-seed master benchmark ($N=10$). Fixed-Time: $90.02 \pm 1.26 \text{ s}$; Coordinated Adaptive: $49.87 \pm 2.46 \text{ s}$ ($p = 1.68 \times 10^{-11}$, Cohen's $d_z = 12.83$). | Retain as primary non-RL classical coordination baseline in research publications. |
| **CLM-02** | Deep RL | Double-DQN achieves statistically significant $-37.09\%$ travel time reduction. | **TIER 1: VERIFIED** | Validated across 10-seed master benchmark ($N=10$). Double-DQN: $56.64 \pm 2.22 \text{ s}$ vs Fixed-Time $90.02 \pm 1.26 \text{ s}$ ($p = 1.40 \times 10^{-11}$, Cohen's $d_z = 13.07$). | Retain as primary single-agent/multi-intersection RL benchmark. |
| **CLM-03** | PPO Baseline | Single-agent PPO outperforms Fixed-Time baseline significantly. | **TIER 2: CONDITIONAL / NOT SIGNIFICANT** | PPO achieves $85.50 \pm 5.75 \text{ s}$ ($-5.01\%$). Raw paired $t$-test yields $p = 0.0384$. However, under Bonferroni multiple-comparison correction ($\alpha / 3 = 0.0167$), adjusted $p = 0.1153$. It is **not statistically significant**. | Frame PPO as a baseline that fails to achieve robust coordination over fixed-time under default hyperparameters. |
| **CLM-04** | Transit Priority | Multi-objective Transit Signal Priority (TSP) achieves $88.4\%$ grant rate and substantial delay reduction. | **TIER 3: RETRACTED (CHERRY-PICKED)** | In `series_4e_summary.json` ($N=100$), the overall TSP grant rate across all 50 evaluation runs is **$36.66\%$** ($12.9 / 36.2$ requests). The $88.4\%$ figure was cherry-picked exclusively from Seed 105 (mean $88.35\%$). Moreover, delay-centric and passenger-weighted formulations yielded identical aggregate means ($84.38 \text{ s}$ TT, $3.86 \text{ PHD}$, $36.66\%$ grant rate) due to greedy evaluation action saturation. | **Formally retract the $88.4\%$ claim.** State the full multi-seed average ($36.66\%$) and report the zero-effect size ($\Delta = 0.0$) with discussion of action-mask saturation. |
| **CLM-05** | State Space | 14D observation space significantly outperforms 8D observation space. | **TIER 2: CONDITIONAL / SEED-DOMINATED** | Series 4B pooled evaluations showed 14D ($51.55 \text{ s}$) vs 8D ($59.98 \text{ s}$) with a naive $t$-test $p = 0.0004$. However, Linear Mixed Model (LMM) and 10k cluster bootstrap revealed that **$91.6\%$ of variance** is between-model training seed variance ($\sigma^2_{\text{model}} = 217.18$ vs $\sigma^2_{\text{eval}} = 19.90$). At the model level, the difference is **not statistically significant** ($p = 0.133$, 95% CI $[-24.11, +7.25]$). | Clarify that while 14D achieves higher peak performance in specific models, training seed stochasticity dominates state representation effects. |
| **CLM-06** | Cooperative MARL | MAPPO with cooperative reward coupling ($\beta$) outperforms uncoupled controllers. | **TIER 2: PRELIMINARY / UNCONFIRMED** | Only 3 of 25 runs completed ($\beta = 0.00$, seeds 101–103). Uncoupled pooled performance ($N=30$) is $89.32 \pm 7.99 \text{ s}$, which is statistically indistinguishable from Fixed-Time ($90.02 \text{ s}$, $p = 0.68$). Runs for $\beta \in \{0.25, 0.50, 0.75, 1.00\}$ are pending. | State clearly that cooperative reward coupling ablation is ongoing research; no superiority claims can yet be made for MAPPO. |
| **CLM-07** | Field Deployment | System is actively controlling live traffic intersections on Hosur Road, Bengaluru. | **TIER 4: SCOPE DISCLAIMER** | The platform is an offline microscopic simulation digital twin built using SUMO 1.26.0 and TraCI, calibrated on Bengaluru road geometries and peak vehicle flows. It does not interface with live Bengaluru Traffic Police ITMS/SCATS physical controllers. | State clearly: *"Evaluated in a high-fidelity microscopic simulation environment calibrated on Bengaluru arterial road geometry."* Never claim physical deployment. |
| **CLM-08** | Environmental Impact | System achieves $30\%+$ reduction in fuel consumption and vehicle emissions. | **TIER 1: VERIFIED (IN SIMULATION)** | Across the 10-seed master benchmark, Coordinated Adaptive reduces fuel from $21.57 \text{ L}$ to $14.18 \text{ L}$ ($-34.26\%$, $p < 10^{-9}$), $\text{CO}_2$ from $49.95 \text{ kg}$ to $32.84 \text{ kg}$ ($-34.25\%$, $p < 10^{-9}$), and $\text{NO}_x$ from $223.1 \text{ g}$ to $146.7 \text{ g}$ ($-34.25\%$, $p < 10^{-9}$). Physical combustion chemistry ($2.316 \text{ kg CO}_2 / \text{L petrol}$) verified within $0.18\%$. | Retain as valid simulation-based environmental assessment. |

---

## 3. Deep-Dive Audit: The Series 4E TSP Claim Retraction

### A. Anatomical Audit of the Erroneous Claim
Previous project narratives cited:
> *"The multi-objective passenger-weighted reward achieved an 88.4% Transit Signal Priority grant rate, expediting bus transit across the corridor."*

### B. Audit Evidence from `series_4e_summary.json`
Direct inspection of `outputs/experiments/phase4/series_4e_passenger_reward/series_4e_summary.json` ($N = 100$ total evaluation runs; 50 delay-centric, 50 passenger-weighted) proves:
1. **Overall Grant Rate:** Mean TSP grant rate across all 50 evaluation runs for both formulations is **$36.66\%$** ($0.3666$).
2. **Seed Breakdown (Delay-Centric):**
   - Seed 101 (evals 1–10): Mean grant rate = $21.49\%$
   - Seed 102 (evals 11–20): Mean grant rate = $2.20\%$
   - Seed 103 (evals 21–30): Mean grant rate = $9.70\%$
   - Seed 104 (evals 31–40): Mean grant rate = $61.54\%$
   - Seed 105 (evals 41–50): Mean grant rate = **$88.35\%$**
3. **Formulation Equivalence:**
   - Delay-Centric: Travel Time = $84.38 \text{ s}$, PHD = $3.86$, Grants Mean = $12.9 / 36.2$ ($36.66\%$)
   - Passenger-Weighted: Travel Time = $84.38 \text{ s}$, PHD = $3.86$, Grants Mean = $12.9 / 36.2$ ($36.66\%$)
   - Mean Difference: $\mathbf{\Delta = 0.000}$ across all 50 matched evaluation pairs.

### C. Scientific Explanation
During evaluation, the trained policy operates in deterministic greedy mode (`eval_mode=True`). At decision boundaries where transit priority requests are active, the action selection saturated onto identical dominant phase extensions regardless of whether the policy was trained with linear delay penalties or passenger-weighted delay penalties. The reported 88.4% was taken exclusively from Seed 105.

### D. Formal Retraction Action
The claim of 88.4% TSP grant rate is formally retracted. In all research drafts and reports, the finding shall be accurately reported as:
> *"Across 100 confirmatory evaluation runs across 5 random training seeds, the multi-objective transit priority formulation achieved an overall average grant rate of 36.66% with 3.86 passenger hours of delay. Under deterministic evaluation, passenger weighting did not produce statistically distinct corridor outcomes compared to raw delay minimization ($\Delta = 0.00$), demonstrating that queue pressure dominated transit preference in the uncoupled policy regime."*

---

## 4. Summary of Supported Claims for Research Publication

The project possesses a robust, scientifically defensible core supported by rigorous data:
1. **Classical Coordination Dominance:** Coordinated Adaptive control achieves a remarkable $-44.60\%$ travel time reduction ($p < 10^{-10}$) and $-34.25\%$ emissions reduction over fixed-time control.
2. **Double-DQN Viability:** Double-DQN achieves a verified $-37.09\%$ reduction ($p < 10^{-10}$) and $-27.47\%$ emissions reduction, proving that deep Q-learning can learn effective offset and split timing.
3. **PPO Coordination Deficit:** Off-the-shelf single-agent PPO fails to outperform classical fixed-time baseline under statistical rigor (Bonferroni-adjusted $p = 0.115$).
4. **Hierarchical Variance Insight:** In arterial corridor RL, between-model training seed stochasticity accounts for over $90\%$ of performance variance, demonstrating that multi-seed confirmatory protocols are mandatory to avoid false discovery.
