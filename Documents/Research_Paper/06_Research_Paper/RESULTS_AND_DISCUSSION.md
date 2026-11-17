# Section VI: Results & Discussion

### A. Traffic Efficiency Performance
- Coordinated Adaptive achieved $-44.60\%$ travel time reduction ($49.87\text{ s}$ vs. $90.02\text{ s}$, $p = 5.60 \times 10^{-13}, d_z = 18.74$) and $-52.82\%$ cumulative delay reduction ($5{,}836.8\text{ veh}\cdot\text{s}$ vs. $12{,}373.2\text{ veh}\cdot\text{s}$).
- Dueling Double-DQN achieved $-37.08\%$ travel time reduction ($56.64\text{ s}$, $p = 5.90 \times 10^{-12}, d_z = 14.41$) and $-35.13\%$ delay reduction ($8{,}024.4\text{ veh}\cdot\text{s}$).
- Decentralized PPO achieved $-5.02\%$ travel time reduction ($85.50\text{ s}$, $p_{\text{adj}} = 0.1153 > 0.05$, not statistically significant).

### B. Environmental Emissions & Chemical Stoichiometry
- Coordinated Adaptive reduced CO2 emissions by $-23.14\%$ ($42.72\text{ kg}$ vs. $55.58\text{ kg}$) and fuel consumption by $-23.15\%$ ($18.44\text{ L}_{\text{petrol-eq}}$ vs. $23.99\text{ L}_{\text{petrol-eq}}$).
- The ratio $\frac{55.578\text{ kg CO}_2}{23.993\text{ L}} = 2.3164\text{ kg/L}$ aligns with theoretical octane combustion ($2.3116\text{ kg/L}$) within $0.208\%$, demonstrating mass conservation.
