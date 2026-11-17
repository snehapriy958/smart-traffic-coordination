# Experimental Results, Statistical Methodology, and Limitations

**Project:** Smart Traffic Coordination System – Bengaluru Silk Board Corridor  
**Evaluation Scope:** Extended 900-second ($15\text{-minute}$) simulation runs across three random seeds (`1, 2, 3`)  
**Simulation Environment:** Eclipse SUMO 1.26.0 / TraCI  
**Document Status:** Verified against Phase 5 Independent Engineering Audit  

---

## 1. Experimental Protocol

### 1.1 Invariants and Controlled Conditions
All evaluations were executed under strictly controlled, identical conditions:
- **Network Configuration:** `sumo/silk_board/network/silk_board.net.xml` (1.25 km corridor; J1, J2, J3).
- **Demand Schedule:** `sumo/silk_board/demand/silk_board.rou.xml` (31 flows, 1 discrete ambulance).
- **Vehicle Type Specifications:** `sumo/silk_board/demand/vehicle_types.add.xml` (Krauss driver imperfection $\sigma = 0.5$).
- **Simulation Duration:** $900.0\text{ seconds}$ per run with fixed step size $\Delta t = 1.0\text{ s}$.
- **Emission Modeling:** SUMO internal HBEFA4 emission formulations integrated once per simulation step:
  $$\text{CO}_2\text{ (kg)} = \frac{\sum (\text{CO}_2\text{ rate in mg/s} \times \Delta t)}{1{,}000{,}000}$$
  $$\text{NO}_x\text{ (g)} = \frac{\sum (\text{NO}_x\text{ rate in mg/s} \times \Delta t)}{1{,}000}$$
  $$\text{Fuel (L)} = \frac{\sum (\text{fuel rate in mg/s} \times \Delta t)}{750{,}000} \quad (\text{reference density } \rho = 0.750\text{ kg/L})$$

### 1.2 Vehicle Population Definitions
- **Inserted per run:** Exactly **378 vehicles**.
- **Completed trips per run:** Exactly **378 vehicles arrived** by $t = 900\text{ s}$ ($0\text{ unfinished}$).
- **Corridor traversal trips:** Exactly **109 vehicles** traversed the entire Hosur corridor route (`corridor_j1_j2_j3`).
- **Feeder-turn movements:** Exactly **269 vehicles** performed turning movements onto or off arterial feeders.
- **Total simulated vehicle-run instances:** $12 \times 378 = \mathbf{4{,}536\text{ instances}}$ across the 12 evaluation runs.

---

## 2. Comprehensive 900-Second Simulation Results

### 2.1 Raw Empirical Metrics Across Seeds

| Controller | Seed | Departed | Arrived | Unfinished | Corridor Trips | Corridor TT (s) | Speed (km/h) | Delay (veh$\cdot$s) | Mean Queue | Max Queue | $\text{CO}_2$ (kg) | Fuel (L) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline** | 1 | 378 | 378 | 0 | 109 | 88.37 | 28.74 | 12221.0 | 13.58 | 58 | 55.3005 | 23.8731 |
| | 2 | 378 | 378 | 0 | 109 | 90.53 | 28.13 | 12340.0 | 13.71 | 59 | 55.6380 | 24.0188 |
| | 3 | 378 | 378 | 0 | 109 | 90.72 | 27.96 | 12512.0 | 13.90 | 59 | 55.7498 | 24.0674 |
| **Coordinated** | 1 | 378 | 378 | 0 | 109 | 48.01 | 38.35 | 5641.0 | 6.27 | 24 | 42.4605 | 18.3280 |
| | 2 | 378 | 378 | 0 | 109 | 48.84 | 38.10 | 5842.0 | 6.49 | 27 | 42.9155 | 18.5237 |
| | 3 | 378 | 378 | 0 | 109 | 49.79 | 38.16 | 5726.0 | 6.36 | 27 | 42.5813 | 18.3791 |
| **MARL PPO** | 1 | 378 | 378 | 0 | 109 | 88.73 | 25.17 | 12773.0 | 14.19 | 45 | 56.4295 | 24.3618 |
| | 2 | 378 | 378 | 0 | 109 | 89.97 | 24.77 | 13110.0 | 14.57 | 48 | 56.5755 | 24.4257 |
| | 3 | 378 | 378 | 0 | 109 | 87.35 | 24.95 | 12597.0 | 14.00 | 43 | 55.8115 | 24.0946 |
| **MARL DQN** | 1 | 378 | 378 | 0 | 109 | 57.81 | 31.38 | 8212.0 | 9.12 | 41 | 47.7937 | 20.6323 |
| | 2 | 378 | 378 | 0 | 109 | 59.58 | 31.24 | 8356.0 | 9.28 | 43 | 48.0034 | 20.7223 |
| | 3 | 378 | 378 | 0 | 109 | 58.33 | 31.30 | 7940.0 | 8.82 | 36 | 46.8471 | 20.2233 |

### 2.2 Descriptive Statistics ($N=3$ Seeds, $df=2$)

| Controller | Metric | Mean | Std Dev ($s$) | Median | Min | Max | 95% Confidence Interval |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline** | Corridor Travel Time (s) | 89.87 | 1.31 | 90.53 | 88.37 | 90.72 | $[86.63, 93.12]$ |
| | Corridor Speed (km/h) | 28.28 | 0.41 | 28.13 | 27.96 | 28.74 | $[27.26, 29.30]$ |
| | Cumulative Delay (veh$\cdot$s) | 12357.67 | 146.30 | 12340.00 | 12221.00 | 12512.00 | $[11994.23, 12721.11]$ |
| | Mean Corridor Queue (veh) | 13.73 | 0.16 | 13.71 | 13.58 | 13.90 | $[13.33, 14.13]$ |
| | Max Corridor Queue (veh) | 58.67 | 0.58 | 59.00 | 58 | 59 | $[57.23, 60.10]$ |
| | $\text{CO}_2$ Emissions (kg) | 55.56 | 0.23 | 55.64 | 55.30 | 55.75 | $[54.98, 56.14]$ |
| | Fuel Consumption (L) | 23.99 | 0.10 | 24.02 | 23.87 | 24.07 | $[23.74, 24.24]$ |
| **Coordinated Adaptive** | Corridor Travel Time (s) | **48.88** | 0.89 | 48.84 | 48.01 | 49.79 | $[46.67, 51.09]$ |
| | Corridor Speed (km/h) | **38.20** | 0.13 | 38.16 | 38.10 | 38.35 | $[37.88, 38.53]$ |
| | Cumulative Delay (veh$\cdot$s) | **5736.33** | 100.90 | 5726.00 | 5641.00 | 5842.00 | $[5485.69, 5986.98]$ |
| | Mean Corridor Queue (veh) | **6.37** | 0.11 | 6.36 | 6.27 | 6.49 | $[6.10, 6.64]$ |
| | Max Corridor Queue (veh) | **26.00** | 1.73 | 27.00 | 24 | 27 | $[21.70, 30.30]$ |
| | $\text{CO}_2$ Emissions (kg) | **42.65** | 0.24 | 42.58 | 42.46 | 42.92 | $[42.07, 43.24]$ |
| | Fuel Consumption (L) | **18.41** | 0.10 | 18.38 | 18.33 | 18.52 | $[18.16, 18.66]$ |
| **MARL PPO** | Corridor Travel Time (s) | 88.68 | 1.31 | 88.73 | 87.35 | 89.97 | $[85.43, 91.94]$ |
| | Corridor Speed (km/h) | 24.96 | 0.20 | 24.95 | 24.77 | 25.17 | $[24.47, 25.46]$ |
| | Cumulative Delay (veh$\cdot$s) | 12826.67 | 260.68 | 12773.00 | 12597.00 | 13110.00 | $[12179.10, 13474.23]$ |
| | Mean Corridor Queue (veh) | 14.25 | 0.29 | 14.19 | 14.00 | 14.57 | $[13.53, 14.97]$ |
| | Max Corridor Queue (veh) | 45.33 | 2.52 | 45.00 | 43 | 48 | $[39.07, 51.59]$ |
| | $\text{CO}_2$ Emissions (kg) | 56.27 | 0.41 | 56.43 | 55.81 | 56.58 | $[55.26, 57.28]$ |
| | Fuel Consumption (L) | 24.29 | 0.18 | 24.36 | 24.09 | 24.43 | $[23.86, 24.73]$ |
| **MARL DQN** | Corridor Travel Time (s) | **58.57** | 0.91 | 58.33 | 57.81 | 59.58 | $[56.31, 60.83]$ |
| | Corridor Speed (km/h) | **31.31** | 0.07 | 31.30 | 31.24 | 31.38 | $[31.13, 31.48]$ |
| | Cumulative Delay (veh$\cdot$s) | **8169.33** | 211.26 | 8212.00 | 7940.00 | 8356.00 | $[7644.54, 8694.13]$ |
| | Mean Corridor Queue (veh) | **9.07** | 0.23 | 9.12 | 8.82 | 9.28 | $[8.50, 9.64]$ |
| | Max Corridor Queue (veh) | **40.00** | 3.61 | 41.00 | 36 | 43 | $[31.03, 48.97]$ |
| | $\text{CO}_2$ Emissions (kg) | **47.55** | 0.62 | 47.79 | 46.85 | 48.00 | $[46.02, 49.08]$ |
| | Fuel Consumption (L) | **20.53** | 0.27 | 20.63 | 20.22 | 20.72 | $[19.87, 21.19]$ |

---

## 3. Paired Statistical Significance Testing

### 3.1 Justification for Paired Comparison
In traditional randomized trials, independent two-sample t-tests are used when subjects receive different treatments independently. In this simulation experiment, however:
- **Each controller was tested on the exact same three random seeds (`1, 2, 3`).**
- **Traffic departure schedules and driver imperfection sequences were identical across controllers for any given seed.**
- Therefore, variance across seeds is a matched blocking factor, requiring a **paired Student's t-test ($N=3, df=2$)** on the paired difference $D_i = X_{i, \text{controller}} - X_{i, \text{baseline}}$:
  $$t = \frac{\bar{D}}{s_D / \sqrt{N}}$$

### 3.2 Paired t-Test Results Against Baseline

| Comparison vs. Baseline | Metric | Mean Difference | % Improvement | $s_D$ | Paired $t$ | Exact $p$-Value | Statistical Significance |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Coordinated Adaptive** | Corridor Travel Time | $-40.99\text{ s}$ | **+45.61%** | 0.6673 | $-106.41$ | **0.00009** | **Statistically Significant ($p < 0.001$)** |
| | Corridor Speed | $+9.93\text{ km/h}$ | **+35.12%** | 0.2974 | $+57.82$ | **0.00030** | **Statistically Significant ($p < 0.001$)** |
| | Cumulative Delay | $-6621.33\text{ veh}\cdot\text{s}$ | **+53.58%** | 148.38 | $-77.29$ | **0.00017** | **Statistically Significant ($p < 0.001$)** |
| | $\text{CO}_2$ Emissions | $-12.91\text{ kg}$ | **+23.24%** | 0.2312 | $-96.73$ | **0.00011** | **Statistically Significant ($p < 0.001$)** |
| | Fuel Consumption | $-5.58\text{ L}$ | **+23.25%** | 0.1003 | $-96.32$ | **0.00011** | **Statistically Significant ($p < 0.001$)** |
| **MARL DQN** | Corridor Travel Time | $-31.30\text{ s}$ | **+34.82%** | 0.9639 | $-56.24$ | **0.00032** | **Statistically Significant ($p < 0.001$)** |
| | Corridor Speed | $+3.03\text{ km/h}$ | **+10.73%** | 0.3568 | $+14.71$ | **0.00459** | **Statistically Significant ($p < 0.01$)** |
| | Cumulative Delay | $-4188.33\text{ veh}\cdot\text{s}$ | **+33.88%** | 332.50 | $-21.82$ | **0.00209** | **Statistically Significant ($p < 0.01$)** |
| | $\text{CO}_2$ Emissions | $-8.01\text{ kg}$ | **+14.42%** | 0.7717 | $-17.99$ | **0.00308** | **Statistically Significant ($p < 0.01$)** |
| | Fuel Consumption | $-3.46\text{ L}$ | **+14.42%** | 0.3334 | $-17.98$ | **0.00308** | **Statistically Significant ($p < 0.01$)** |
| **MARL PPO** | Corridor Travel Time | $-1.19\text{ s}$ | **+1.31%** | 1.9432 | $-1.061$ | **0.39998** | **NOT Statistically Significant ($p = 0.40$)** |
| | Corridor Speed | $-3.31\text{ km/h}$ | **-11.71%** | 0.2829 | $-20.29$ | **0.00242** | **Statistically Significant Speed Reduction** |
| | Cumulative Delay | $+469.00\text{ veh}\cdot\text{s}$ | **-3.81%** | 349.96 | $+2.321$ | **0.14602** | **NOT Statistically Significant** |
| | $\text{CO}_2$ Emissions | $+0.71\text{ kg}$ | **-1.28%** | 0.5690 | $+2.159$ | **0.16345** | **NOT Statistically Significant** |
| | Fuel Consumption | $+0.31\text{ L}$ | **-1.28%** | 0.2463 | $+2.164$ | **0.16296** | **NOT Statistically Significant** |

---

## 4. Analysis Across Demand Regimes

```
   Regime 1: Peak (0-300s)           Regime 2: Shoulder (300-600s)      Regime 3: Off-Peak (600-900s)
   Heavy Inflow Loading             BMTC Clusters & Ambulance           Network Clearance & Dissipation
   (208 departed, 82 unfin)         (170 departed, 31 unfin)            (0 departed, all clear)
```

| Metric | Demand Regime | Baseline | Coordinated Adaptive | MARL PPO | MARL DQN | Operational Interpretation |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Corridor Travel Time (s)** | Peak ($0-300\text{s}$) | 102.42 | **42.32** | 89.04 | 53.94 | Coordinated cuts peak corridor traversal time by 58.7%. |
| | Shoulder ($300-600\text{s}$) | 86.87 | **54.78** | 87.23 | 67.00 | Coordinated handles bus clusters with 36.9% lower travel time. |
| | Off-Peak ($600-900\text{s}$) | 67.91 | **34.47** | 95.14 | 36.17 | Coordinated and DQN rapidly drain residual queues. |
| **Cumulative Delay (veh$\cdot$s)**| Peak ($0-300\text{s}$) | 5182.7 | **1763.7** | 4733.0 | 1951.0 | Coordinated avoids gridlock during initial inflow loading. |
| | Shoulder ($300-600\text{s}$) | 6861.0 | **3919.3** | 7462.7 | 5990.0 | PPO delay rises as anti-starvation preemption cycles green. |
| | Off-Peak ($600-900\text{s}$) | 314.0 | **53.3** | 631.0 | 228.3 | Coordinated achieves near-zero delay during network drain. |
| **Max Queue Length (veh)** | Peak ($0-300\text{s}$) | 47.0 | **19.3** | 37.0 | 28.7 | Baseline queue builds up to 47 vehicles at Silk Board. |
| | Shoulder ($300-600\text{s}$) | 58.7 | **26.0** | 45.3 | 40.0 | Baseline reaches peak corridor congestion (59 veh queue). |
| | Off-Peak ($600-900\text{s}$) | 13.0 | **5.3** | 16.0 | 9.0 | All queues fully empty by $t = 900\text{ s}$. |

---

## 5. Methodological & Scientific Limitations

1. **Small Sample Size ($N=3$ Seeds):**
   - Evaluating three random seeds is sufficient for initial proof-of-concept and demonstrates clear performance separation between Coordinated Adaptive and Baseline under the paired t-test.
   - However, $N=3$ ($df=2$) is **not sufficient to claim universal generalization** across arbitrary real-world traffic variations or unmodeled weather/incident conditions.
   - Non-parametric tests (such as the Wilcoxon signed-rank test) cannot achieve statistical significance at $N=3$ because the minimum possible two-tailed p-value for 3 pairs is $p = 0.25$ ($1 / 2^3 = 0.125$ one-tailed).
2. **Synthetic Traffic Flow Assumption:**
   - The road network topology is extracted directly from OpenStreetMap (`silk_board.net.xml`), providing real physical road coordinates and lane counts.
   - However, vehicle routes (`silk_board.rou.xml`) are **synthetic flow schedules** calibrated to represent characteristic Silk Board traffic patterns, rather than real-time camera or loop detector telemetry from the Bengaluru Traffic Police.
3. **PPO Optimization Trade-off:**
   - MARL PPO exhibits lower average speed ($24.96\text{ km/h}$) and higher delay ($12{,}826\text{ veh}\cdot\text{s}$) than Baseline. This occurs because the safety shield's anti-starvation mechanism frequently preempts the arterial green phase to relieve Madiwala side-street queues. This behavior represents safe and starvation-free operation, but does not optimize arterial throughput.
4. **Scope of 3D Visualization:**
   - The Three.js 3D viewport provides architectural digital twin rendering (road ribbons, elevations, support piers, and HTML markers). Live vehicle entities and traffic signal heads are rendered exclusively on the 2D live canvas and signal status panels.
