# State, Action & Reward Formulation

## 1. Observation Spaces

### Local State Vector (8D - Used by DQN):
For intersection $i$, the 8-dimensional state vector $\mathbf{s}_i^{\text{local}} \in [0, 1]^8$ consists of:
- $[s_0, s_1, s_2, s_3]$: Normalized queue lengths on approaches (North, South, East, West): $s_k = \min(1.0, Q_k / 30.0)$.
- $[s_4, s_5, s_6, s_7]$: Normalized mean approach velocities: $s_{4+k} = \min(1.0, \bar{v}_k / v_{\text{free}})$.

### Augmented State Vector (14D - Used by Decentralized PPO):
- $[s_0 \dots s_7]$: 8 local approach features as above.
- $[s_8, s_9]$: Current active phase index (one-hot encoded) and normalized green elapsed time $t_{\text{green}} / g_{\max}$.
- $[s_{10} \dots s_{13}]$: 4 neighbor coordination features (upstream queue counts and downstream residual capacities).

## 2. Action Space
At each decision step ($\Delta t_{\text{dec}} = 5.0\text{ s}$), each agent selects an action from a discrete 3-action space $\mathcal{A} = \{0, 1, 2\}$:
- **Action 0 (`ACTION_KEEP`)**: Hold the currently active green phase stage.
- **Action 1 (`ACTION_SWITCH`)**: Initiate a transition to the next conflicting phase stage (subject to 4s yellow + 2s all-red clearance).
- **Action 2 (`ACTION_EXTEND`)**: Request a green extension by $\Delta t_{\text{dec}}$ seconds up to the maximum green limit ($g_{\max} = 60.0\text{ s}$).

No fourth action exists; all agents across DQN, PPO, and MAPPO are parametrized with `num_actions = 3` in `traffic_service/ai/env.py` and `traffic_service/ai/marl_controller.py`. Phase stage mapping is executed deterministically by the dual-ring signal manager.

## 3. Reward Formulation
The local transition reward at step $t$ is formulated as a multi-component penalty:
$$r_t = - \left( w_q \Delta Q_t + w_d D_t + w_s S_t \right)$$
where:
- $\Delta Q_t = \sum_k (Q_k(t) - Q_k(t-1))$: Change in total halted queue length ($w_q = 0.5$).
- $D_t = \sum_k d_k(t)$: Total delay accumulated over the decision step ($w_d = 0.3$).
- $S_t \in \{0, 1\}$: Phase switch penalty discouraging unnecessary cycling ($w_s = 0.2$).
- The raw reward is clipped to $[-50.0, +50.0]$ to stabilize gradient updates.
