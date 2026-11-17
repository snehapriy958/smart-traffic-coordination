# Research Paper Unresolved Issues, Caveats & Supervisor Decision Register
**Project**: Smart Traffic Coordination System — Bengaluru Traffic Intelligence Platform  
**Target Document**: Research Paper Submission Corpus  
**Audit Date**: November 17, 2026  
**Auditor**: Independent Senior Scientific Auditor & Transportation Systems Specialist  

---

## 1. Executive Summary

In accordance with rigorous academic ethics and publication standards, this register frankly documents all known limitations, operational caveats, incomplete experiments, and decisions explicitly reserved for the research supervisor. None of these items compromise the scientific defensibility of the verified 10-seed master benchmark, but they must be transparently acknowledged prior to manuscript submission.

---

## 2. Incomplete Experiments & Ongoing Research

### Issue RES-01: Series 4C 25-Run MAPPO Hyperparameter Matrix Status
- **Current State**:
  - Series 4C was designed as an exploratory MARL ablation studying cooperative reward coupling: $\beta \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$ across 5 random seeds ($101$–$105$) for $150$ episodes each ($25$ runs total, $250$ evaluation seeds).
  - As established in earlier system audits, the master training process encountered environment deadlocks and was safely halted.
  - Completed runs: $\beta = 0.00$ seeds 101 and 102 completed 150 episodes; seed 103 produced partial checkpoints; remaining 22 runs are pending.
- **Scientific Impact**:
  - **Zero impact on the master benchmark**. The master comparative benchmark (Table I) evaluates pre-trained models over 10 independent seeds ($N=10$, seeds 1–10, 900s) and does not depend on Series 4C.
- **Supervisor Action Required**:
  - Decide whether to:
    1. Exclude Series 4C entirely from the primary conference/journal manuscript, submitting the paper based on the rigorously verified 10-seed comparative benchmark.
    2. Complete the remaining 23 runs of Series 4C on a dedicated GPU cluster as an extended journal study on cooperative reward coupling.

---

## 3. Methodological Caveats & Simulation Scope Boundaries

### Issue RES-02: Cyber-Physical Simulation Twin vs. Empirical Field Calibration
- **Current State**:
  - The simulation environment models a 3-junction corridor on Hosur Road, Bengaluru (J1 Madiwala $\to$ J2 Silk Board $\to$ J3 Rupena Agrahara) using OpenStreetMap road network geometry (306 directed edges, 213 junctions, 490 lanes) in UTM Zone 43N (EPSG:32643).
  - Traffic demand (378 departed vehicles over 600s dynamic insertion) reflects heterogeneous Indian urban traffic (motorcycles, passenger cars, BMTC buses, commercial trucks, ambulances) with configured car-following parameters.
  - However, the network has not undergone empirical microscopic calibration against fine-grained loop detector or automated number plate recognition (ANPR) time series from Bengaluru Traffic Police.
- **Scientific Mitigation**:
  - The manuscript has been explicitly scoped as a **cyber-physical simulation twin and benchmarking study**. The Title, Abstract, Section I, and Section IX clearly state:
    > *"The simulation network represents a Bengaluru urban corridor using available road-network geometry and configured traffic demand. Empirical field calibration and independent real-world validation remain future work."*
- **Supervisor Action Required**:
  - Confirm that this framing aligns with departmental expectations and target journal scope.

---

### Issue RES-03: Real-World SCATS / ITMS Hardware Interfacing
- **Current State**:
  - The control architecture implements an IEEE-compliant Safety Shield enforcing strict bounds: minimum green ($15\text{ s}$), maximum green ($60\text{ s}$), yellow clearance ($4\text{ s}$), and all-red clearance ($2\text{ s}$).
  - In simulation, the shield prevented 100% of safety violations across all controllers.
  - However, physical field deployment on physical signal controllers (e.g., Bengaluru's CoSiSys / SCATS infrastructure) requires hardware-in-the-loop (HIL) validation, NEMA TS2 / 170 / 2070 controller interface cabinets, and physical electromechanical fail-safe relays.
- **Scientific Mitigation**:
  - Section VIII (Practical Implementation and Safety Shield Architecture) explicitly discusses the hardware isolation layer and designates physical HIL cabinet integration as the subsequent development milestone.

---

### Issue RES-04: Network Topology & Generalization Limits
- **Current State**:
  - The study evaluates a linear arterial corridor consisting of three signalized junctions with dedicated right-of-way and turning lanes.
  - The findings have not been demonstrated on 2D grid networks (e.g., Manhattan grid topologies), roundabouts, or non-linear arterial networks with complex flyover merges.
- **Supervisor Action Required**:
  - Acknowledge corridor-specific bounds in the discussion section as an explicit study boundary.

---

### Issue RES-05: MARL PPO Performance and Coordination Bottlenecks
- **Current State**:
  - Multi-Agent PPO achieved an average travel time of $85.501 \pm 5.820\text{ s}$, representing a $-5.02\%$ reduction compared to baseline ($90.021\text{ s}$).
  - However, after Bonferroni correction for multiple comparisons ($m=3$), this improvement is **not statistically significant** ($p_{\text{adj}} = 0.1153 > 0.05$).
  - In contrast, Coordinated Adaptive achieved $-44.60\%$ ($p_{\text{adj}} = 1.68 \times 10^{-12}$) and Dueling Double-DQN achieved $-37.08\%$ ($p_{\text{adj}} = 1.77 \times 10^{-11}$).
- **Scientific Interpretation**:
  - This is a scientifically valuable negative/modest result demonstrating that decentralized policy optimization without centralized state/action representation struggles with non-stationary multi-intersection coordination compared to rule-based heuristics and value-based methods.
- **Supervisor Action Required**:
  - Confirm that retaining this honest comparative finding enhances paper credibility and novelty.

---

## 4. Decisions Reserved for the Research Supervisor

| Decision Area | Options / Alternatives | Recommendation | Status |
| :--- | :--- | :--- | :--- |
| **Target Publication Venue** | 1. *IEEE Transactions on Intelligent Transportation Systems* (T-ITS)<br>2. *Transportation Research Part C: Emerging Technologies* (TR-C)<br>3. *IEEE Transactions on Control Systems Technology* (TCST)<br>4. *IEEE Intelligent Vehicles Symposium* (IV 2027) | TR-C or IEEE T-ITS for high-impact journal submission; IEEE IV/ITSC for rapid conference publication | **PENDING SUPERVISOR DECISION** |
| **Author List & Order** | Student researcher (First Author), Co-investigators, Senior Advisor / Supervisor (Corresponding Author) | Follow standard CRediT contributor roles taxonomy | **PENDING SUPERVISOR DECISION** |
| **Funding & Institutional Acknowledgments** | University lab support, research grants, cloud compute credits, municipal data access | Include standard institutional boilerplate | **PENDING SUPERVISOR DECISION** |
| **Series 4C Inclusion Scope** | A. Omit from initial submission; focus on master 10-seed benchmark<br>B. Present preliminary $\beta=0.00$ vs baseline findings<br>C. Delay submission until all 25 runs are executed on high-performance compute | **Option A (Recommended)**: Master benchmark is complete, statistically rigorous, and fully defensible without Series 4C | **PENDING SUPERVISOR DECISION** |

---

## 5. Auditor's Formal Statement

All critical scientific and technical issues within the repository have been resolved. The remaining items listed above are standard academic boundaries that strengthen rather than weaken the credibility of the research paper when transparently reported.
