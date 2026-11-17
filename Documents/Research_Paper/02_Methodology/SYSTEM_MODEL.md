# System Model & Problem Formulation

## 1. Corridor Network Model
The arterial corridor is modeled as a directed graph $\mathcal{G} = (\mathcal{V}, \mathcal{E})$, where $\mathcal{V}$ is the set of junctions and $\mathcal{E}$ is the set of directed road edges. The active signalized corridor comprises three consecutive intersections:
- **J1 (Madiwala)**: Northern entry intersection (TLS ID: `1617743335`), 4-phase dual-ring control.
- **J2 (Central Silk Board)**: Central nexus intersection (TLS ID: `GS_cluster_10282769895_10775075568_11964440742_11964440743`), high-capacity rotary-arterial junction.
- **J3 (Rupena Agrahara)**: Southern arterial exit intersection (TLS ID: `6970466614`), 4-phase arterial control.

Corridor arterial progression runs along directed edges connecting J1 -> J2 -> J3 with entry edge `172853382#2` and exit edge `40696223#1`.

## 2. Microscopic Vehicle Kinematics
Vehicle following behavior is governed by the Krauss model:
$$v_{\text{safe}}(t) = v_l(t) + \frac{g(t) - v_l(t)\tau}{\frac{v_l(t) + v(t)}{2b} + \tau}$$
$$v(t + \Delta t) = \max\left(0, \min\left(v(t) + a\Delta t, v_{\text{safe}}(t), v_{\max}\right) - \eta\right)$$
where $g(t)$ is the bumper-to-bumper gap to the leading vehicle, $\tau$ is driver reaction time, $a$ is maximum acceleration, $b$ is comfortable deceleration, and $\eta \sim \mathcal{U}(0, \sigma a)$ represents driver imperfection / stochasticity.
