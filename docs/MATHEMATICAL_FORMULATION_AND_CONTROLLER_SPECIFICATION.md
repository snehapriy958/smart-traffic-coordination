# Mathematical Formulations and Controller Technical Specification

**Project:** Smart Traffic Coordination System — Bengaluru Silk Board Corridor  
**Document:** Mathematical Modeling, Traffic Flow Theory, Emission Conversions, and Reinforcement Learning  
**Audience:** Software Engineers, Traffic Engineers, Academic Examiners

---

## 1. Traffic Metric Formulations

### 1.1 Fundamental Traffic Flow Relationship
In traffic flow theory, traffic state across a corridor segment is governed by Lighthill-Whitham-Richards (LWR) macroscopic continuum principles:
$$q = k \cdot v_s$$
where:
- $q$: Traffic flow rate ($\text{vehicles/hour}$ or $\text{veh/s}$).
- $k$: Traffic density ($\text{vehicles/km}$).
- $v_s$: Space-mean speed ($\text{km/h}$).

### 1.2 Instantaneous Approach Queue Length
In the implementation ([`traffic_service/state_extractor.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/state_extractor.py)), queue length on approach lane $l$ is measured microscopically:
$$Q_l(t) = \sum_{v \in \mathcal{V}_l(t)} \mathbf{1}_{\{u_v(t) \le u_{\text{queue}}\}}$$
where:
- $\mathcal{V}_l(t)$: Set of active vehicle IDs present on lane $l$ at simulation step $t$.
- $u_v(t)$: Instantaneous speed of vehicle $v$ ($\text{m/s}$).
- $u_{\text{queue}} = 1.39\text{ m/s} = 5.0\text{ km/h}$: Standard queue velocity threshold.
- Total approach queue for junction $j$:
  $$Q_j(t) = \sum_{l \in \mathcal{L}_j} Q_l(t)$$

### 1.3 Approach Waiting Time
Waiting time tracks vehicles halted or crawling at an intersection approach:
$$W_l(t) = \sum_{v \in \mathcal{V}_l(t)} w_v(t)$$
where $w_v(t)$ is TraCI's accumulated waiting time ($\text{s}$) accrued while vehicle speed $u_v(t) \le 0.1\text{ m/s}$.

### 1.4 Network Average Speed (Time-Mean Speed)
At simulation second $t$, approach speed is averaged across all active intersection approach lanes:
$$\bar{u}_j(t) = \begin{cases} \frac{1}{|\mathcal{V}_j(t)|}\sum_{v \in \mathcal{V}_j(t)} u_v(t) \cdot 3.6 & \text{if } |\mathcal{V}_j(t)| > 0 \\ 0.0 & \text{otherwise} \end{cases}$$
The network-wide average speed reported across the 900-second horizon is the time-mean of approach speeds across active seconds:
$$\bar{v}_{\text{network}} = \frac{1}{T_{\text{active}}}\sum_{t=1}^{T} \left( \frac{1}{|J_{\text{active}}(t)|}\sum_{j \in J_{\text{active}}(t)} \bar{u}_j(t) \right)$$
> [!NOTE] Methodological Disclosure  
> This metric represents the **network-wide time-mean of instantaneous approach speeds**, which differs from the harmonic space-mean speed derived from corridor travel time ($v_s = L / \bar{T}_{\text{corridor}}$).

### 1.5 Corridor Travel Time
Corridor travel time is evaluated exclusively over the cohort of $M = 109$ vehicles executing the continuous route `corridor_j1_j2_j3` ($J_1 \to J_2 \to J_3$):
$$\bar{T}_{\text{corridor}} = \frac{1}{M}\sum_{i=1}^M \left( t_{\text{exit}, i} - t_{\text{entry}, i} \right)$$
where:
- $t_{\text{entry}, i}$: Simulation second when vehicle $i$ registers on entry detector edge `172853382#2`.
- $t_{\text{exit}, i}$: Simulation second when vehicle $i$ registers on exit detector edge `40696223#1`.

---

## 2. Emission and Fuel Calculations (HBEFA4 Standards)

Microscopic vehicle emissions in SUMO are simulated via the **Handbook Emission Factors for Road Transport (HBEFA v4.2)** model.

### 2.1 Instantaneous Mass Emission Rate
At each discrete time step $\Delta t = 1.0\text{ s}$, TraCI samples mass flow rates ($\text{mg/s}$) for all edges $e$ in the arterial corridor:
$$\dot{m}_{\text{CO}_2}(t) = \sum_{e \in \mathcal{E}} \text{traci.edge.getCO2Emission}(e) \quad [\text{mg/s}]$$
$$\dot{m}_{\text{NO}_x}(t) = \sum_{e \in \mathcal{E}} \text{traci.edge.getNOxEmission}(e) \quad [\text{mg/s}]$$
$$\dot{m}_{\text{fuel}}(t) = \sum_{e \in \mathcal{E}} \text{traci.edge.getFuelConsumption}(e) \quad [\text{mg/s}]$$

### 2.2 Accumulated Mass and Volume Conversions
To translate instantaneous milligrams per second into standard environmental engineering units:

1. **Carbon Dioxide ($\text{CO}_2$) Mass:**
   $$M_{\text{CO}_2} = \frac{1}{10^6}\sum_{t=1}^T \dot{m}_{\text{CO}_2}(t) \cdot \Delta t \quad [\text{kg}]$$
   *(Divisor $10^6\text{ mg/kg}$ converts milligrams to kilograms).*

2. **Nitrogen Oxides ($\text{NO}_x$) Mass:**
   $$M_{\text{NO}_x} = \frac{1}{10^3}\sum_{t=1}^T \dot{m}_{\text{NO}_x}(t) \cdot \Delta t \quad [\text{g}]$$
   *(Divisor $10^3\text{ mg/g}$ converts milligrams to grams).*

3. **Fuel Volume Consumption:**
   $$V_{\text{fuel}} = \frac{\sum_{t=1}^T \dot{m}_{\text{fuel}}(t) \cdot \Delta t}{\rho_{\text{fuel}}} \quad [\text{liters}]$$
   where the fuel density constant is:
   $$\rho_{\text{fuel}} = 0.750\text{ kg/L} = 750{,}000\text{ mg/L}$$
   > [!NOTE] Fuel Density Assumption  
   > The factor $750{,}000\text{ mg/L}$ represents standard calibrated density for blended commercial urban fuels (gasoline $\approx 0.740\text{ kg/L}$, diesel $\approx 0.830\text{ kg/L}$).

---

## 3. Signal Controller Mathematical Formulations

### 3.1 Fixed-Time Baseline Controller
The Fixed-Time controller executes static pre-timed cyclic programs without sensor feedback:
- Fixed cycle length: $C = 90.0\text{ s}$.
- Green splits: Arterial Hosur green $g_1 = 45.0\text{ s}$, Cross-street green $g_2 = 39.0\text{ s}$.
- Yellow clearance: $y = 3.0\text{ s}$ per transition ($2 \times 3.0\text{ s} = 6.0\text{ s}$ total yellow).
- Cycle invariant: $\sum g_i + \sum y_i = C$.

### 3.2 Coordinated Adaptive Green-Wave Controller
The Coordinated Adaptive algorithm dynamically adjusts green splits based on approach queue pressure and enforces arterial progression offsets:
1. **Dynamic Green Extension:**
   If queue pressure on active green approach $Q_{\text{active}}(t) > Q_{\text{cross}}(t)$ and elapsed green $g_{\text{elapsed}} < \text{max\_green}$:
   $$g_{\text{target}} = \min\left(g_{\text{elapsed}} + \Delta g_{\text{ext}}, \; \text{max\_green}\right)$$
   where $\Delta g_{\text{ext}} = 5.0\text{ s}$ and $\text{max\_green} = 60.0\text{ s}$.
2. **Inter-Junction Green-Wave Coordination Offset:**
   To establish a progression green wave along $J_1 \to J_2 \to J_3$:
   $$\Delta t_{\text{offset}}(j, j+1) = \frac{d_{j, j+1}}{\bar{v}_{\text{progression}}}$$
   where $d_{j, j+1}$ is inter-intersection distance ($\text{m}$) and $\bar{v}_{\text{progression}} \approx 11.1\text{ m/s}$ ($40\text{ km/h}$).

---

## 4. Multi-Agent Reinforcement Learning (MARL) Formulations

### 4.1 14-Dimensional Normalized State Vector ($s_j \in \mathbb{R}^{14}$)
At each decision interval ($5.0\text{ s}$), each agent $j \in \{J_1, J_2, J_3\}$ extracts a normalized observation vector:

| Index | Feature | Raw Source | Normalization Constant | Normalized Range |
|:---:|:---|:---|:---:|:---:|
| 0 | `phase` | Active TLS phase index | $/ 3.0$ | $[0.0, 1.0]$ |
| 1 | `phase_elapsed` | Seconds active in phase | $/ 60.0$ | $[0.0, 1.0]$ |
| 2 | `time_to_switch` | Next switch countdown | $/ 60.0$ | $[0.0, 1.0]$ |
| 3 | `app_q0` | Approach 0 queue | $/ 50.0$ | $[0.0, 1.0]$ |
| 4 | `app_q1` | Approach 1 queue | $/ 50.0$ | $[0.0, 1.0]$ |
| 5 | `total_q` | Total junction queue | $/ 100.0$ | $[0.0, 1.0]$ |
| 6 | `avg_speed` | Instantaneous approach speed | $/ 60.0\text{ km/h}$ | $[0.0, 1.0]$ |
| 7 | `total_wait` | Total waiting time | $/ 300.0\text{ s}$ | $[0.0, 1.0]$ |
| 8 | `vehicle_count` | Total approach vehicles | $/ 50.0$ | $[0.0, 1.0]$ |
| 9 | `upstream_inflow` | Hub predicted arrival flow | $/ 50.0$ | $[0.0, 1.0]$ |
| 10 | `platoons_count` | Approaching vehicle platoons | $/ 5.0$ | $[0.0, 1.0]$ |
| 11 | `co2_rate` | Approach $\text{CO}_2$ emissions | $/ 10{,}000\text{ mg/s}$ | $[0.0, 1.0]$ |
| 12 | `emergency_approaching` | Binary emergency flag | $\{0.0, 1.0\}$ | $\{0.0, 1.0\}$ |
| 13 | `padding` | Geometric alignment scalar | $0.0$ | $0.0$ |

### 4.2 Discrete Action Space ($\mathcal{A}$)
$$\mathcal{A} = \{0: \text{KEEP}, \; 1: \text{SWITCH}, \; 2: \text{EXTEND}\}$$
- `KEEP` ($0$): Maintain current phase duration without modification.
- `SWITCH` ($1$): Initiate safe transition to conflicting phase through mandatory 3.0-second yellow.
- `EXTEND` ($2$): Extend active green by $+5.0\text{ s}$ up to $\text{max\_green} = 60.0\text{ s}$.

### 4.3 Multi-Objective Composite Reward Function
The reward for agent $j$ at time step $t$ balances delay, queues, emissions, and throughput:
$$R_j(t) = - w_q \frac{Q_j(t)}{50} - w_w \frac{W_j(t)}{300} - w_e \frac{E_j(t)}{10000} + w_{\text{thru}} M_{\text{thru}, j}(t) - w_{\text{switch}} \mathbf{1}_{\{a_j = \text{SWITCH}\}}$$
where weights are calibrated as:
$$w_q = 0.35, \quad w_w = 0.30, \quad w_e = 0.15, \quad w_{\text{thru}} = 0.20, \quad w_{\text{switch}} = 0.05$$

### 4.4 MARL Double-DQN Algorithm
The value-based Q-network updates parameters $\theta$ using the Double-DQN Bellman target:
$$Y_t^{\text{Double-DQN}} = R_{t+1} + \gamma Q\left(s_{t+1}, \; \arg\max_{a'} Q(s_{t+1}, a'; \theta_t); \; \theta_t^{-}\right)$$
$$\mathcal{L}(\theta) = \mathbb{E}\left[ \left( Y_t^{\text{Double-DQN}} - Q(s_t, a_t; \theta) \right)^2 \right]$$
where $\theta_t^{-}$ are periodic frozen target network parameters and $\gamma = 0.99$.

### 4.5 MARL Actor-Critic PPO Algorithm
The policy network $\pi_\theta(a|s)$ and value network $V_\phi(s)$ are optimized via clipped surrogate gradients:
$$\mathcal{L}^{\text{CLIP}}(\theta) = \hat{\mathbb{E}}_t \left[ \min\left( r_t(\theta)\hat{A}_t, \; \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon)\hat{A}_t \right) \right]$$
where:
- Probability ratio: $r_t(\theta) = \frac{\pi_\theta(a_t | s_t)}{\pi_{\theta_{\text{old}}}(a_t | s_t)}$.
- Clipping bound: $\epsilon = 0.20$.
- Generalized Advantage Estimation (GAE):
  $$\hat{A}_t = \sum_{l=0}^{\infty} (\gamma \lambda)^l \delta_{t+l}^V, \quad \delta_t^V = R_{t+1} + \gamma V_\phi(s_{t+1}) - V_\phi(s_t)$$
  with $\gamma = 0.99, \lambda = 0.95$.

---

## 5. Deterministic Safety Shielding Mathematics

Regardless of reinforcement learning policy output, safety guardrails operate as a hard deterministic shield via boolean action masks $\mathcal{M} = [m_{\text{keep}}, m_{\text{switch}}, m_{\text{extend}}] \in \{0.0, 1.0\}^3$:

### 5.1 Minimum Green Time Constraint
To prevent dangerous high-frequency signal flicker, no phase can switch before $15.0\text{ s}$ elapsed green:
$$\text{If } g_{\text{elapsed}} < \text{min\_green} \; (15.0\text{ s}): \quad \mathcal{M} = [1.0, \; 0.0, \; 0.0]$$
*(Action `SWITCH` is strictly masked to $0.0$).*

### 5.2 Anti-Starvation Preemption Constraint
To guarantee cross-streets are never indefinitely starved, red duration is monitored per approach:
$$\text{If } t_{\text{red}, a} \ge \text{max\_red} \; (60.0\text{ s}) \quad \text{and} \quad Q_a \ge 1: \quad \mathcal{M} = [0.0, \; 1.0, \; 0.0]$$
*(When the approach has waited $\ge 60\text{s}$ with vehicles in queue, `SWITCH` is enforced with probability $1.0$).*

### 5.3 Emergency Vehicle Preemption Priority
When an approaching emergency vehicle ($v_{\text{type}} = \text{ambulance}$) is detected within distance $d_{\text{stopline}} \le 200\text{ m}$:
1. Normal policy inference is bypassed.
2. If conflicting phase is active: immediate 3.0s yellow transition to arterial green phase ($P = 2$ for $J_1/J_3$, $P = 0$ for $J_2$).
3. Phase is locked on arterial green until emergency vehicle clears exit detector:
   $$\mathcal{M} = [1.0, \; 0.0, \; 0.0] \quad \text{(Emergency Priority Lock)}$$

---
**Formulation Approved by:** Antigravity Senior Engineering & Verification Auditor
