# Research Contributions & Evidentiary Taxonomy

This work presents five structured research contributions categorized strictly by their evidentiary foundation to ensure zero unverified novelty claims:

### 1. Implemented Engineering Contribution: Heterogeneous Cyber-Physical Simulation Testbed
- **Description**: Implementation of an open, reproducible, microscopic simulation testbed of a major South Asian arterial corridor (Hosur Road J1-J2-J3, Bengaluru) modeling real-world OSM geometry (306 edges, 213 junctions, 490 lanes) in UTM Zone 43N (EPSG:32643) and realistic heterogeneous vehicle demand (67.99% motorcycles, 27.25% cars, 3.17% buses, 1.32% trucks, 0.26% emergency ambulance).
- **Evidentiary Basis**: Implemented and verified codebase artifacts in `sumo/silk_board/` and `traffic_service/multi_intersection_simulation.py`.
- **Boundary**: Synthetic demand configuration based on corridor geometry; empirical calibration against live field loop detector time series is scoped as future work.

### 2. Experimentally Supported Finding: Rigorous Multi-Controller Benchmarking ($N=10, df=9$)
- **Description**: Controlled empirical evaluation of four signal control paradigms over 10 identical random seeds (Seeds 1–10) across a 900.0s horizon, supported by paired Student's $t$-tests, Holm-Bonferroni corrections ($m=3$), non-parametric Wilcoxon signed-rank tests, and Cohen's $d_z$ effect sizes.
- **Evidentiary Basis**: 40 raw JSON execution records in `outputs/validation/10seeds/runs/*.json` and `statistical_analysis.json`.

### 3. Experimentally Supported & Literature-Bridging Finding: RL Coordination Limits in Mixed Traffic
- **Description**: Empirical demonstration that domain-aware queue-balancing heuristics ($-44.60\%$ travel time, $d_z=18.74$) and value-based Dueling Double-DQN ($-37.08\%$, $d_z=14.41$) significantly outperform decentralized policy-gradient MARL ($-5.02\%$, $p_{\text{adj}} = 0.1153 > 0.05$). This exposes the practical challenge of multi-agent credit assignment in linear corridors without centralized critics or communication.
- **Evidentiary Basis**: Corroborates Max-Pressure theory (Le et al., 2017) and demonstrates the non-stationarity bottlenecks identified in MARL literature.

### 4. Implemented Engineering & Verified Simulation Mechanism: Runtime Safety Shield
- **Description**: Formulation and implementation of a deterministic state-machine safety shield enforcing NEMA TS2 / IRC bounds ($15\text{ s}$ min green, $60\text{ s}$ max green, $4\text{ s}$ yellow, $2\text{ s}$ all-red, $120\text{ s}$ anti-starvation preemption, and emergency green-wave preemption).
- **Evidentiary Basis**: 0 safety violations across $36{,}000\text{ simulation steps}$ ($7{,}200$ decision cycles) in the master benchmark.
- **Boundary**: Validated in software simulation; electromechanical fail-safe relay integration on physical traffic controller cabinets is designated as future work.

### 5. Methodological & Analytical Contribution: Stoichiometrically Grounded Emissions Modeling
- **Description**: Rigorous coupling of HBEFA4/2.0 microscopic vehicle emissions with a petrol-equivalent volumetric fuel index ($\text{L}_{\text{petrol-eq}}$) scaled by $\rho_{\text{ref}} = 0.750\text{ kg/L}$, validated by internal carbon-mass conservation.
- **Evidentiary Basis**: Empirical ratio of $2.3164\text{ kg CO}_2 / \text{L}$ matches pure octane stoichiometry ($2.3116\text{ kg/L}$) within $0.208\%$.
- **Boundary**: Software emission engine validation; on-road PEMS physical tailpipe testing remains future work.
