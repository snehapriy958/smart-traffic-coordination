# Controller Comparison & Behavioral Analysis

## 1. Primary Findings
1. **Coordinated Adaptive** achieves the best overall corridor performance, cutting travel time by 44.60% and delay by 52.82%. Its pressure heuristic acts rapidly to prevent queue spillback across tightly-spaced arterial links.
2. **Dueling Double-DQN** achieves substantial improvements (-37.08% travel time, -35.13% delay), demonstrating that value-based single-agent or weakly-coupled agents learn effective local phase extension policies.
3. **Multi-Agent PPO** fails to achieve statistically significant improvement (-5.02%, p_adj = 0.1153) and exhibits lower average speed (-9.37%). Without centralized critics or parameter sharing, individual actor-critic agents suffer from non-stationary transition dynamics and uncoordinated phase cycling.
