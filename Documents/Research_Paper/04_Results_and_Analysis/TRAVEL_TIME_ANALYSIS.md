# Corridor Travel Time Analysis

Corridor travel time $\tau_i = t_{\text{arr}, i} - t_{\text{dep}, i}$ measures the duration required for a vehicle to traverse the complete 3-intersection arterial corridor from J1 entry to J3 exit ($N = 109$ corridor trips):

- **Baseline**: $90.02 \pm 1.26\text{ s}$ (range: 88.37s - 92.15s across 10 seeds).
- **Coordinated Adaptive**: $49.87 \pm 2.46\text{ s}$ ($-44.60\%$, paired $t = -59.25, p < 10^{-12}$).
- **Double-DQN**: $56.64 \pm 2.22\text{ s}$ ($-37.08\%$, paired $t = -45.57, p < 10^{-11}$).
- **MARL PPO**: $85.50 \pm 5.82\text{ s}$ ($-5.02\%$, paired $t = -2.42, p_{\text{adj}} = 0.1153 > 0.05$).
