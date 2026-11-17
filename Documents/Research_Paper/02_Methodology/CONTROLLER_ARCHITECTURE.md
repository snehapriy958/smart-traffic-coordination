# Signal Controller Architectures

This platform implements four distinct control paradigms evaluated in the master benchmark:

### 1. Fixed-Time Coordination (Pre-timed Baseline)
- Operates a deterministic 120-second background cycle length.
- Pre-allocated green splits based on historical peak saturation ratios.
- Fixed 4-second yellow change and 2-second all-red clearance intervals.

### 2. Coordinated Adaptive (Queue-Balancing Heuristic)
- Evaluates approach queue imbalances every decision interval ($\Delta t_{\text{dec}} = 5.0\text{ s}$).
- Computes pressure difference between active green phases and waiting red phases:
  $$\Delta P = \sum_{l \in \text{Active}} Q_l - \sum_{m \in \text{Waiting}} Q_m$$
- Extends the current green phase if $\Delta P > \theta_{\text{extend}}$ and $g_{\text{elapsed}} < g_{\max}$. Switches to the highest-pressure conflicting phase otherwise.

### 3. Dueling Double-DQN (Value-Based Deep RL)
- State space: 8-dimensional normalized local observation vector.
- Action space: Discrete 3-action transition set $\mathcal{A} = \{0: \text{KEEP}, 1: \text{SWITCH}, 2: \text{EXTEND}\}$ governing phase holding, yellow/all-red transition initiation, and green extension up to $g_{\max} = 60\text{ s}$.
- Architecture: 2 hidden layers (64, 64 neurons, ReLU) branching into separate Value $V(s)$ and Advantage $A(s, a)$ streams:
  $$Q(s, a) = V(s) + \left(A(s, a) - \frac{1}{|\mathcal{A}|}\sum_{a'} A(s, a')\right)$$
- Double Q-learning target: $y = r + \gamma Q(s', \arg\max_a Q(s', a; \theta); \theta^{-})$.

### 4. Multi-Agent PPO (Policy-Gradient MARL)
- State space: 14-dimensional vector (8 local approach features + 6 neighbor summary features).
- Architecture: Decentralized actor-critic networks with separate actor $\pi_\theta(a|s)$ and critic $V_\phi(s)$ heads.
- Clipped surrogate loss:
  $$L^{\text{CLIP}}(\theta) = \hat{\mathbb{E}}_t \left[\min(r_t(\theta)\hat{A}_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon)\hat{A}_t)\right]$$
