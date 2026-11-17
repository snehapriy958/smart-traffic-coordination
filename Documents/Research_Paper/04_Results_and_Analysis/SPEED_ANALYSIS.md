# Corridor Velocity & Speed Discrepancy Resolution

## 1. Authoritative Metric Values ($N=10$)
- **Fixed-Time Baseline**: $28.205 \pm 0.373\text{ km/h}$ ($7.835\text{ m/s}$)
- **Coordinated Adaptive**: $37.981 \pm 0.263\text{ km/h}$ ($10.550\text{ m/s}$, $+34.66\%$)
- **Dueling Double-DQN**: $31.463 \pm 0.442\text{ km/h}$ ($8.740\text{ m/s}$, $+11.55\%$)
- **Multi-Agent PPO**: $25.563 \pm 0.913\text{ km/h}$ ($7.101\text{ m/s}$, $-9.37\%$)

## 2. Investigation of the 6.216 m/s vs 28.21 km/h Discrepancy
- **Audit Findings**:
  - In `outputs/validation/10seeds/runs/*.json`, the recorded field is `full_900s["avg_speed_kmh"]`.
  - For baseline, the exact 10-seed mean is $28.205\text{ km/h}$, which corresponds to $\frac{28.205}{3.6} = 7.835\text{ m/s}$.
  - The figure $6.216\text{ m/s}$ ($22.38\text{ km/h}$) was an erroneous conversational transcription artifact that did not appear in any 10-seed run file.
  - Therefore, $28.21\text{ km/h}$ ($7.835\text{ m/s}$) is confirmed as the unique authoritative baseline speed.
