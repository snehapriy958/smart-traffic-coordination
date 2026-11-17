# Cumulative Corridor Delay Analysis

Cumulative delay is computed via discrete Riemann sum:
$$D_{\text{cum}} = \sum_{t=1}^{900} (Q_{J1}(t) + Q_{J2}(t) + Q_{J3}(t)) \cdot 1.0\text{ s} \quad [\text{veh}\cdot\text{s}]$$

- **Fixed-Time Baseline**: $12{,}373.20 \pm 135.07\text{ veh}\cdot\text{s}$ (SEM = 42.71 veh*s)
- **Coordinated Adaptive**: $5{,}836.80 \pm 296.48\text{ veh}\cdot\text{s}$ ($-52.82\%$, $t = -64.40, p = 2.65 \times 10^{-13}, d_z = 20.37$)
- **Dueling Double-DQN**: $8{,}024.40 \pm 284.89\text{ veh}\cdot\text{s}$ ($-35.13\%$, $t = -38.26, p = 2.83 \times 10^{-11}, d_z = 12.10$)
- **Multi-Agent PPO**: $12{,}163.60 \pm 896.60\text{ veh}\cdot\text{s}$ ($-1.66\%$, $t = -0.70, p_{\text{adj}} = 1.0000$, Not Significant)

### Regimes Breakdown (Fixed-Time vs Adaptive):
- Peak (0-300s): $5{,}183.7\text{ veh}\cdot\text{s}$ (Baseline) $\to$ $1{,}777.4\text{ veh}\cdot\text{s}$ (Adaptive, $-65.7\%$)
- Shoulder (300-600s): $6{,}849.4\text{ veh}\cdot\text{s}$ (Baseline) $\to$ $4{,}007.6\text{ veh}\cdot\text{s}$ (Adaptive, $-41.5\%$)
- Off-Peak (600-900s): $340.1\text{ veh}\cdot\text{s}$ (Baseline) $\to$ $51.8\text{ veh}\cdot\text{s}$ (Adaptive, $-84.8\%$)
