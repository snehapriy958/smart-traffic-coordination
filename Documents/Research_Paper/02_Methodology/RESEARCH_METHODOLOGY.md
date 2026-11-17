# Research Methodology & Workflow

## 1. End-to-End Scientific Workflow
The investigation follows a strict multi-tier cyber-physical experimental workflow:
1. **Network Compilation**: Extraction of OpenStreetMap geometry for the Hosur Road arterial corridor (Bengaluru, India), converted via `netconvert` into a microscopic multi-lane network (306 directed edges, 213 junctions, 490 lanes) in UTM Zone 43N (EPSG:32643).
2. **Heterogeneous Demand Generation**: Specification of multi-class microscopic vehicle flows (motorcycles, passenger cars, BMTC buses, commercial trucks, ambulances) with empirical car-following parameters reflecting aggressive South Asian urban driving dynamics.
3. **Controller Formulation**: Implementation of 4 distinct control architectures:
   - Fixed-Time Baseline (Webster-optimized fixed cycle)
   - Coordinated Adaptive (queue-balancing pressure heuristic)
   - Dueling Double-DQN (value-based RL with experience replay and target networks)
   - Decentralized PPO (actor-critic policy gradients with clipped surrogate objective)
4. **Safety Shielding Enforcement**: Interposition of a formal deterministic state machine monitoring signal elapsed times and clearance phases, overriding unsafe RL actions.
5. **Confirmatory Benchmarking**: Execution of 10 independent evaluation seeds (seeds 1-10) over a 900.0s horizon (Peak 0-300s, Shoulder 300-600s, Off-Peak 600-900s).
6. **Hierarchical Statistical Testing**: Computation of sample means, standard deviations, standard errors, 95% confidence intervals, two-tailed paired t-tests, Holm-Bonferroni corrections for multiple comparisons (m=3), non-parametric Wilcoxon signed-rank tests, and Cohen's d_z effect sizes.
