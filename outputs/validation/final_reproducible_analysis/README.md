# Authoritative 10-Seed Master Benchmark: Reproducible Evidence Package

## 1. Overview
This directory contains the completely recomputed, independent, and reproducible statistical validation package for the 10-Seed Master Benchmark along the Silk Board corridor.

- **Sample Size**: $N = 10$ matched seeds (Seeds 1 through 10)
- **Controllers**: Fixed-Time Baseline, Coordinated Adaptive, Double-DQN (Stage A), PPO (Stage A)
- **Simulation Duration**: $900.0\,	ext{s}$
- **Corridor Traversal Demands**: 109 completed corridor trips per seed ($100\%$ trip completion)

## 2. Definitive Numerical Summary

| Controller | Mean Travel Time ($s$) | Sample Std ($s$, ddof=1) | Pop Std ($\sigma$, ddof=0) | 95% Confidence Interval | Travel Time Δ% | Delay Δ% | Fuel Δ% |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed-Time Baseline** | 90.021 | 1.259 | 1.194 | [89.12, 90.92] | Baseline | Baseline | Baseline |
| **Coordinated Adaptive** | **49.872** | **2.462** | **2.335** | [48.11, 51.63] | **-44.60%** | **-52.83%** | **-23.15%** |
| **Double-DQN (Stage A)** | **56.637** | **2.215** | **2.102** | [55.05, 58.22] | **-37.09%** | **-35.15%** | **-15.17%** |
| **PPO (Stage A)** | 85.501 | 5.820 | 5.521 | [81.34, 89.66] | -5.01% | -1.66% | -0.98% |

## 3. Inferential Paired Hypothesis Tests vs. Fixed-Time Baseline

| Controller | Paired $t$-stat | Raw $p$-value | Bonferroni $p$-adj ($lpha=0.0167$) | Cohen's $d_z$ | Wilcoxon $p$-value | Statistical Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Coordinated Adaptive** | -59.2485 | 5.6005e-13 | **1.6801e-12** | 18.74 | 1.9531e-03 | **Statistically Significant Improvement** |
| **Double-DQN (Stage A)** | -45.5692 | 5.9040e-12 | **1.7712e-11** | 14.41 | 1.9531e-03 | **Statistically Significant Improvement** |
| **PPO (Stage A)** | -2.4231 | 0.0384 | 0.1153 | 0.77 | 0.0059 | **Not Significant (p_adj >= 0.05)** |

## 4. Discrepancy Reconciliation Summary
- **Standard Deviation**: Reconciled the difference between sample SD ($s$, ddof=1) and population SD ($\sigma$, ddof=0). Both are published side-by-side above. Sample SD ($s$, ddof=1) is the mathematically correct metric for inferential publication.
- **PPO Limitation**: Confirmed single-agent PPO Stage A saturated at Junction 2, resulting in only a $-5.01\%$ travel time change ($p_{\text{adj}} = 0.1153$).

## 5. How to Re-Run and Reproduce
```bash
python outputs/validation/final_reproducible_analysis/reproduce_benchmark_analysis.py
```
