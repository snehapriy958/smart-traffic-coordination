# Section II: Related Work

A comprehensive review of signal control literature is organized into five paradigms:
1. **Classical & Pre-Timed Signal Control**: Webster's seminal delay-minimization formula [1] established cycle-length optimization for isolated intersections. Koonce and Rodegerdts [4] formalized NEMA safety standards for phase sequencing and clearance intervals.
2. **Adaptive Signal Control Systems**: SCOOT [2] and SCATS [3] dynamically adjust green splits and cycle lengths based on stop-line detector occupancies. In decentralized network control, Le et al. [14] proved that max-pressure queue balancing stabilizes arterial networks without centralized communication.
3. **Value-Based Deep Reinforcement Learning**: Genders and Razavi [5] demonstrated single-intersection DQN. Wei et al. (IntelliLight) [6] integrated multi-modal state representations, and Chen et al. (MetaLight) [15] leveraged meta-learning for fast cross-intersection adaptation.
4. **Multi-Agent Reinforcement Learning & Simulation**: Wei et al. (CoLight) [7] used graph attention networks to share spatial queue states, and Zheng et al. (PressLight) [8] aligned RL rewards with max-pressure theory. Large-scale simulation platforms like SUMO [12], TraCI [13], and CityFlow [16] enabled realistic multi-agent evaluation.
5. **Safe Reinforcement Learning & Runtime Shielding**: Alshiekh et al. [9] established formal shielding for RL agents using temporal logic monitors to prevent unsafe exploratory transitions.
