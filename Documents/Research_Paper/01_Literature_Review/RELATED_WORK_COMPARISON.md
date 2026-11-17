# Related Work Comparison Matrix

| System / Citation | Year | Control Paradigm | Heterogeneous Fleet | Multi-Intersection | Safety Shielding | Empirical Verification | Statistical Tests ($N \ge 10$) |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Webster [1]** | 1958 | Fixed-Time Delay Minimization | No | No | Parameter bounds | Isolated simulation | None |
| **Hunt et al. (SCOOT) [2]** | 1981 | Centralized Adaptive Heuristic | No | Yes (Arterial) | Min/max green | Field deployment | Case study |
| **Lowrie (SCATS) [3]** | 1990 | Plan-selection Adaptive | No | Yes (Grid) | Stage constraints | Field deployment | Case study |
| **Koonce & Rodegerdts [4]** | 2008 | NEMA Standards Guide | No | Yes | Standard clearance | Engineering spec | N/A |
| **Genders & Razavi [5]** | 2016 | Deep Q-Learning (DQN) | No | Single | None | Simulation | $N = 3$ |
| **Wei et al. (IntelliLight) [6]** | 2018 | Phase-Gate DQN | No | Single | None | Simulation | $N = 5$ |
| **Wei et al. (CoLight) [7]** | 2019 | Graph Attention MARL | No | Yes (Synthetic grid) | None | Simulation | $N = 5$ |
| **Zheng et al. (PressLight) [8]** | 2019 | Max-Pressure RL | No | Yes (Synthetic grid) | None | Simulation | $N = 5$ |
| **Alshiekh et al. [9]** | 2018 | Safe RL via Shielding | No | Generic RL | Formal reactive shield | Benchmarks | $N = 5$ |
| **Al-Dabbagh et al. [10]** | 2021 | Multi-Objective RL | No | Single | Soft penalty | Simulation | $N = 5$ |
| **Notter et al. (HBEFA4) [11]**| 2019 | Microscopic Emission Modeling| Yes | N/A | N/A | Chassis dynamometer | Rigorous |
| **Lopez et al. (SUMO) [12]** | 2018 | Microscopic Traffic Engine | Yes | Arbitrary | Internal clearance | Open-source | Continuous |
| **Krajzewicz et al. [13]** | 2012 | TraCI Simulator Interface | Yes | Arbitrary | None | Simulation | Benchmark |
| **Le et al. [14]** | 2017 | Decentralized Max-Pressure | No | Yes (Network) | Parameter bounds | Simulation | Asymptotic |
| **Chen et al. (MetaLight) [15]**| 2019 | Meta-RL Signal Control | No | Yes (Corridor) | None | Simulation | $N = 5$ |
| **Zhang et al. (CityFlow) [16]**| 2019 | Multi-Agent City Simulator | No | Large-scale grid | None | Simulation | Benchmark |
| **This Work (Bengaluru Twin)** | **2026** | **Hybrid MARL + Safety Shield** | **Yes (68% 2W)** | **Yes (Hosur Arterial)** | **Formal Deterministic** | **Cyber-Physical Twin** | **$N = 10, df = 9$, Paired $t$, Wilcoxon, Bonferroni** |
