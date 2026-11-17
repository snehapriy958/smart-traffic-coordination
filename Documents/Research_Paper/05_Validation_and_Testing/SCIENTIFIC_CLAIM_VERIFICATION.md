# Scientific Claim Verification Matrix

| Claim in Manuscript | Verification Source | Status |
| :--- | :--- | :---: |
| Coordinated Adaptive reduces travel time by 44.60% | 10 raw runs in `outputs/validation/10seeds/runs/` | **VERIFIED** |
| Double-DQN reduces travel time by 37.08% | 10 raw runs in `outputs/validation/10seeds/runs/` | **VERIFIED** |
| PPO improvement is not statistically significant (p_adj = 0.1153) | Paired t-test recomputation ($df=9$) | **VERIFIED** |
| Safety shield achieves 0 safety violations | Simulation step telemetry ($36{,}000\text{ steps}$) | **VERIFIED** |
| CO2 to fuel ratio matches stoichiometry (0.208% error) | Theoretical chemistry vs HBEFA4 integration | **VERIFIED** |
| Fleet consists of 67.99% motorcycles, 27.25% cars | Departure logs ($N=378$) | **VERIFIED** |
| Simulation twin represents Bengaluru OSM corridor | `silk_board.net.xml` node coordinates | **VERIFIED** |
| Field deployment is future work | Ethical scoping disclaimers | **VERIFIED** |
