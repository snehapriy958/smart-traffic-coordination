# Mathematical Equations, Formal Formulations & Methodology

**Document ID:** HTC-RESEARCH-METHODOLOGY  
**Target Publication Venues:** IEEE Transactions on Intelligent Transportation Systems (T-ITS) / Transportation Research Part C  
**Classification:** Formal Problem Formulation, Algorithmic Specifications & Mathematical Derivations  

---

## 1. Problem Formulation: Urban Arterial Traffic Signal Control

We formulate the traffic signal control problem along an $M$-intersection arterial corridor as a discrete-time Multi-Agent Markov Decision Process (MAMDP) or Decentralized Partially Observable Markov Decision Process (Dec-POMDP) augmented with deterministic safety constraints:
$$\mathcal{M} = \langle \mathcal{N}, \mathcal{S}, \{\mathcal{A}_i\}_{i \in \mathcal{N}}, \{\mathcal{O}_i\}_{i \in \mathcal{N}}, \mathcal{P}, \{\mathcal{R}_i\}_{i \in \mathcal{N}}, \gamma, \mathcal{C} \rangle$$
where:
- $\mathcal{N} = \{J_1, J_2, J_3\}$ is the set of signalized intersections (agents).
- $\mathcal{S}$ is the global environmental state.
- $\mathcal{A}_i = \{0, 1, 2\}$ is the discrete action set for agent $i$ (`KEEP`, `SWITCH`, `EXTEND`).
- $\mathcal{O}_i$ is the local observation space for agent $i$.
- $\mathcal{P}: \mathcal{S} \times \mathcal{A} \times \mathcal{S} \to [0, 1]$ is the state transition probability function governed by microscopic SUMO kinematics.
- $\mathcal{R}_i$ is the local reward function for agent $i$.
- $\gamma \in [0, 1)$ is the temporal discount factor ($\gamma = 0.99$).
- $\mathcal{C}$ is the deterministic safety constraint set (safety shield).

---

## 2. State & Observation Space Formulations

State extraction occurs at controller decision intervals $T_{\text{decision}} = 5.0\text{ s}$ across the 4 approaches of each intersection: Northbound (NB), Southbound (SB), Eastbound (EB), and Westbound (WB).

### 2.1 Baseline 8-Dimensional Observation Space ($\mathcal{O}_{8\text{D}}$)
For intersection $i \in \mathcal{N}$, the 8D feature vector $\mathbf{o}^{(8)}_i \in \mathbb{R}^8$ captures local approach queues, elapsed phase time, active phase, and total waiting time:
$$\mathbf{o}^{(8)}_i = \left[ \tilde{q}_{\text{NB}}, \tilde{q}_{\text{SB}}, \tilde{q}_{\text{EB}}, \tilde{q}_{\text{WB}}, \tilde{g}_{\text{elapsed}}, p_i, \tilde{w}_{\text{tot}}, \tilde{v}_{\text{avg}} \right]^T$$
where:
- $\tilde{q}_k = \frac{\min(q_k, 50.0)}{50.0} \in [0, 1]$ is the normalized queue length on approach $k$.
- $\tilde{g}_{\text{elapsed}} = \frac{\min(g_{\text{elapsed}}, 60.0)}{60.0} \in [0, 1]$ is the normalized green duration of the active phase.
- $p_i \in \{0, 1\}$ is the binary active green phase index ($0$: cross-street green, $1$: arterial Hosur Road green).
- $\tilde{w}_{\text{tot}} = \frac{\min(w_{\text{tot}}, 500.0)}{500.0} \in [0, 1]$ is normalized cumulative vehicle wait time.
- $\tilde{v}_{\text{avg}} = \frac{\min(v_{\text{avg}}, 16.67)}{16.67} \in [0, 1]$ is normalized mean approach speed ($16.67\text{ m/s} = 60\text{ km/h}$).

### 2.2 Extended 14-Dimensional Observation Space ($\mathcal{O}_{14\text{D}}$)
To provide the agent with upstream coordination awareness, transit priority signals, and density differentials, the 14D observation vector $\mathbf{o}^{(14)}_i \in \mathbb{R}^{14}$ augments $\mathbf{o}^{(8)}_i$ with 6 additional features:
$$\mathbf{o}^{(14)}_i = \left[ \mathbf{o}^{(8)}_i, \tilde{q}_{\text{upstream}}, \tilde{d}_{\text{arterial}}, \tilde{d}_{\text{cross}}, \rho_{\text{inflow}}, \mathbb{I}_{\text{TSP}}, \tilde{t}_{\text{starve}} \right]^T$$
where:
- $\tilde{q}_{\text{upstream}} = \frac{\min(q_{\text{upstream}}, 50.0)}{50.0}$ is the upstream platoon queue released by the adjacent upstream intersection.
- $\tilde{d}_{\text{arterial}} = \frac{\min(d_{\text{arterial}}, 300.0)}{300.0}$ is mean arterial vehicle delay.
- $\tilde{d}_{\text{cross}} = \frac{\min(d_{\text{cross}}, 300.0)}{300.0}$ is mean cross-street vehicle delay.
- $\rho_{\text{inflow}} = \frac{\min(\text{inflow rate}, 2.0)}{2.0}$ is normalized vehicle entry rate ($\text{veh/s}$).
- $\mathbb{I}_{\text{TSP}} \in \{0, 1\}$ is the binary Transit Signal Priority request flag (active when a high-occupancy bus is within $150\text{ m}$ of the stop-line).
- $\tilde{t}_{\text{starve}} = \frac{\min(t_{\text{red}}, 120.0)}{120.0} \in [0, 1]$ is normalized elapsed red time on the non-active phase.

---

## 3. Reward Function & Cooperative Coupling

The local reward function $r_i(t)$ balances delay reduction, queue equalization, phase stability, and transit priority:
$$r_i(t) = - \left( w_q \sum_{k \in \text{approaches}} q_{i,k}(t) + w_d \bar{d}_i(t) + w_s \cdot \mathbb{I}_{\text{switch}}(t) + w_{\text{starve}} \cdot \max(0, t_{\text{red}} - 90.0) \right) + w_p \cdot P_i(t)$$
where default hyperparameters are:
- $w_q = 0.5$ (queue length penalty)
- $w_d = 0.3$ (delay penalty)
- $w_s = 2.0$ (phase switching penalty to suppress chattering)
- $w_{\text{starve}} = 1.0$ (starvation penalty for red time exceeding 90s)
- $w_p = 1.0$ (throughput reward for completed vehicles $P_i$)

### 3.1 Multi-Objective Passenger Weighting (Series 4E)
Under passenger-weighted reward, delay and queue terms are scaled by dynamic vehicle occupancy $O_v$:
$$r_{i,\text{passenger}}(t) = - \sum_{v \in \mathcal{V}_i} O_v \cdot \left( w_q \cdot \mathbb{I}_{v \text{ queued}} + w_d \cdot d_v(t) \right)$$
where $O_v = 1.5$ for passenger cars/two-wheelers, and $O_v = 35.0$ for public transit buses (BMTC).

### 3.2 Cooperative Reward Coupling Formulation (Series 4C)
To encourage inter-agent arterial coordination without centralized communication, local rewards are mixed with neighbor rewards via coupling coefficient $\beta \in [0.0, 1.0]$:
$$\tilde{r}_i(t) = (1 - \beta) \cdot r_i(t) + \beta \cdot \frac{1}{|\mathcal{N}_i|} \sum_{j \in \mathcal{N}_i} r_j(t)$$
where $\mathcal{N}_i$ is the set of topological neighbors of intersection $i$ along the corridor:
- $\mathcal{N}_{J_1} = \{J_2\}$
- $\mathcal{N}_{J_2} = \{J_1, J_3\}$
- $\mathcal{N}_{J_3} = \{J_2\}$

---

## 4. Deterministic Safety Shield Invariants

The safety shield acts as a formal runtime filter $\mathcal{S}_{\text{shield}}: \mathcal{S} \times \mathcal{A}_{\text{AI}} \to \mathcal{A}_{\text{safe}}$:
```
AI Action Proposal a_proposed in {KEEP, SWITCH, EXTEND}
                         |
                         v
        +----------------------------------+
        | In Yellow Clearance Transition?  |-- YES --> Force KEEP (Wait for Yellow completion)
        +----------------------------------+
                         | NO
                         v
        +----------------------------------+
        | Elapsed Green g_elapsed < 15.0s? |-- YES --> Force KEEP (Reject early SWITCH)
        +----------------------------------+
                         | NO
                         v
        +----------------------------------+
        | Elapsed Green g_elapsed >= 60.0s?|-- YES --> Force SWITCH (Prevent arterial holdout)
        +----------------------------------+
                         | NO
                         v
        +----------------------------------+
        | Cross Red t_red >= 120.0s?       |-- YES --> Force SWITCH (Anti-starvation override)
        +----------------------------------+
                         | NO
                         v
             Grant a_safe = a_proposed
```

### Mathematical Invariants:
1. **Minimum Green Bound:**
   $$\forall t, \quad g_{\text{phase}}(t) < 15.0\text{ s} \implies a_{\text{safe}}(t) = \text{ACTION\_KEEP}$$
2. **Maximum Green Bound:**
   $$\forall t, \quad g_{\text{phase}}(t) \ge 60.0\text{ s} \implies a_{\text{safe}}(t) = \text{ACTION\_SWITCH}$$
3. **Mandatory Clearance Bound:**
   $$\forall \text{transitions } p_A \to p_B, \quad \Delta t_{\text{yellow}} = \begin{cases} 4.0\text{ s} & \text{for } J_1, J_3 \\ 6.0\text{ s} & \text{for } J_2 \text{ (Rotary)} \end{cases}$$
4. **Anti-Starvation Bound:**
   $$\forall k \in \text{approaches}, \quad t_{\text{red}, k} \le 120.0\text{ s}$$

---

## 5. Control Algorithms Formulations

### 5.1 Coordinated Adaptive Controller
Implemented with upstream platoon anticipation:
At central junction $J_2$, effective demand accounts for incoming platoons released by upstream junction $J_1$:
$$Q_{\text{eff,hosur}}(t) = Q_{\text{hosur}}(t) + \left\lfloor 5.0 \times \text{hub.get\_expected\_inflow}("J2") \right\rfloor$$
- **Phase 0 (Hosur Green) Decision:**
  $$\text{Action} = \begin{cases} \text{SWITCH to Phase 2} & \text{if } g_{\text{elapsed}} \ge 15.0\text{s} \land Q_{\text{madiwala}} > Q_{\text{eff,hosur}} + 2 \\ \text{EXTEND Phase 0} & \text{if } Q_{\text{eff,hosur}} > 0 \land Q_{\text{eff,hosur}} \ge Q_{\text{madiwala}} \land g_{\text{elapsed}} < 60.0\text{s} \\ \text{KEEP} & \text{otherwise} \end{cases}$$

### 5.2 Dueling Double-DQN Architecture
To prevent overestimation bias in action-value estimation, we implement Double Deep Q-Networks with Dueling heads:
$$Q(s, a; \theta, \alpha, \beta) = V(s; \theta, \beta) + \left( A(s, a; \theta, \alpha) - \frac{1}{|\mathcal{A}|} \sum_{a' \in \mathcal{A}} A(s, a'; \theta, \alpha) \right)$$
where $\theta$ represents shared convolutional/dense trunk parameters, $\beta$ represents value stream weights, and $\alpha$ represents advantage stream weights.

#### Loss Function & Target:
$$Y_t^{\text{DoubleQ}} = R_{t+1} + \gamma Q\left(S_{t+1}, \arg\max_a Q(S_{t+1}, a; \theta_t); \theta_t^-\right)$$
$$\mathcal{L}(\theta) = \mathbb{E}_{(s, a, r, s') \sim \mathcal{D}} \left[ \left( Y_t^{\text{DoubleQ}} - Q(s, a; \theta) \right)^2 \right]$$
Target network parameters $\theta^-$ are updated via Polyak averaging:
$$\theta^- \leftarrow \tau \theta + (1 - \tau) \theta^-, \quad \tau = 0.005$$

### 5.3 Multi-Agent PPO (MAPPO) Formulation
MAPPO employs Centralized Training with Decentralized Execution (CTDE).
- **Actor (Policy $\pi_\theta$):** Conditions on local observation $\mathbf{o}_i \in \mathbb{R}^{14}$.
- **Critic (Value Function $V_\phi$):** Conditions on concatenated global corridor state $\mathbf{s} = [\mathbf{o}_{J_1}, \mathbf{o}_{J_2}, \mathbf{o}_{J_3}] \in \mathbb{R}^{42}$.

#### Clipped Surrogate Objective:
$$L^{\text{CLIP}}(\theta) = \hat{\mathbb{E}}_t \left[ \min\left( \rho_t(\theta) \hat{A}_t, \, \text{clip}\left(\rho_t(\theta), 1 - \epsilon, 1 + \epsilon\right) \hat{A}_t \right) \right]$$
where $\rho_t(\theta) = \frac{\pi_\theta(a_t | \mathbf{o}_t)}{\pi_{\theta_{\text{old}}}(a_t | \mathbf{o}_t)}$ is the probability ratio, and $\epsilon = 0.2$.

#### Generalized Advantage Estimation (GAE):
$$\hat{A}_t^{\text{GAE}(\gamma, \lambda)} = \sum_{l=0}^\infty (\gamma \lambda)^l \delta_{t+l}^V$$
where $\delta_t^V = r_t + \gamma V_\phi(\mathbf{s}_{t+1}) - V_\phi(\mathbf{s}_t)$, with $\gamma = 0.99, \lambda = 0.95$.

---

## 6. Environmental Emissions & Chemical Stoichiometry

Microscopic instantaneous tailpipe emissions are sampled using the European HBEFA v4.2 model implemented in SUMO 1.26.0:
$$\text{CO}_2\,(\text{kg}) = \frac{1}{10^6} \sum_{t=1}^T \sum_{v \in \mathcal{V}(t)} e_{v, \text{CO}_2}(t) \cdot \Delta t$$
$$\text{NO}_x\,(\text{g}) = \frac{1}{10^3} \sum_{t=1}^T \sum_{v \in \mathcal{V}(t)} e_{v, \text{NO}_x}(t) \cdot \Delta t$$
$$\text{Fuel}\,(\text{L}) = \frac{1}{\rho_{\text{fuel}} \cdot 10^6} \sum_{t=1}^T \sum_{v \in \mathcal{V}(t)} e_{v, \text{fuel}}(t) \cdot \Delta t$$
where $\rho_{\text{fuel}} = 0.750\text{ kg/L}$ is standard automotive petrol density (DIN EN 228).

### Stoichiometric Validation:
Combustion of standard octane petrol ($\text{C}_8\text{H}_{18}$):
$$\text{C}_8\text{H}_{18} + 12.5 \, \text{O}_2 \to 8 \, \text{CO}_2 + 9 \, \text{H}_2\text{O}$$
- Molecular weight of octane: $M_{\text{fuel}} = 114.23\text{ g/mol}$
- Molecular weight of carbon dioxide: $M_{\text{CO}_2} = 44.01\text{ g/mol}$
- Theoretical stoichiometric yield:
  $$Y_{\text{theoretical}} = \frac{8 \times 44.01}{114.23} \times 0.750\text{ kg/L} = 2.3116\text{ kg CO}_2 / \text{L petrol}$$
- Measured simulation output:
  $$Y_{\text{measured}} = \frac{49.95\text{ kg CO}_2}{21.57\text{ L fuel}} = 2.3157\text{ kg CO}_2 / \text{L petrol}$$
- Relative error:
  $$\delta = \frac{|2.3157 - 2.3116|}{2.3116} = 0.177\% < 0.20\%$$
Confirming rigorous physical and dimensional validity.

---

## 7. Statistical Inference & Hierarchical Variance Decomposition

### 7.1 Paired Comparisons & Multiple Testing Correction
For $N=10$ paired evaluation seeds, we compute the paired difference $D_i = X_{A, i} - X_{B, i}$:
$$t = \frac{\bar{D}}{s_D / \sqrt{N}}, \quad df = N - 1 = 9$$
Cohen's effect size for paired samples:
$$d_z = \frac{\bar{D}}{s_D}$$
To guard against family-wise Type I error inflation across $K=3$ pairwise comparisons against baseline, Bonferroni adjusted significance threshold is:
$$\alpha_{\text{adjusted}} = \frac{\alpha}{K} = \frac{0.05}{3} = 0.0167$$

### 7.2 Linear Mixed-Effects Model (LMM) for Multi-Seed Ablations
To properly account for non-independence in hierarchical multi-seed experiments ($M=5$ models, $E=10$ evaluations per model, $N=50$ total runs):
$$Y_{ijk} = \mu + \alpha_i + u_{j(i)} + \epsilon_{ijk}$$
where:
- $\alpha_i$ is the fixed effect of configuration $i \in \{8\text{D}, 14\text{D}\}$.
- $u_{j(i)} \sim \mathcal{N}(0, \sigma^2_{\text{model}})$ is the random effect of training seed $j$ nested in configuration $i$.
- $\epsilon_{ijk} \sim \mathcal{N}(0, \sigma^2_{\text{eval}})$ is the residual evaluation seed variance.
- Total variance: $\sigma^2_{\text{total}} = \sigma^2_{\text{model}} + \sigma^2_{\text{eval}}$.
- Intraclass Correlation Coefficient (ICC):
  $$\text{ICC} = \frac{\sigma^2_{\text{model}}}{\sigma^2_{\text{model}} + \sigma^2_{\text{eval}}}$$
This formulation formally separates model training instability from traffic evaluation noise.
