# Robustness, Ablation & Exploratory Experiments

### 1. Series 4B (Observation Space Ablations)
- Evaluated 4D, 8D, and 14D observation spaces for Double-DQN and MAPPO across 30 training runs (4,500 episodes).
- **Finding**: 8D normalized local queues and velocities provide the most stable training dynamics for DQN. 14D augmented states with neighbor features increase sample complexity without proportional performance gains.

### 2. Series 4C (Reward Coupling Hyperparameter Matrix)
- Investigated cooperative reward sharing: $r_i^{\text{coop}} = (1-\beta) r_i^{\text{local}} + \beta \frac{1}{|\mathcal{N}_i|} \sum_{j \in \mathcal{N}_i} r_j^{\text{local}}$ for $\beta \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$.
- **Status**: Formally documented as an ongoing/partial exploratory ablation study. Zero completed Series 4C runs are incorporated into the primary 10-seed master benchmark.
