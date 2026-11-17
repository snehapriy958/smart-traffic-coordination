# Research Objectives
**Project**: Smart Traffic Coordination System  
**Target Corridor**: Central Silk Board Arterial Corridor, Bengaluru  

---

## 1. Primary Research Objectives (RO)

- **RO-1: Cyber-Physical Simulation Twin Formulation**  
  Construct an open, reproducible, microscopic simulation testbed of a major heterogeneous urban corridor (Hosur Road J1 Madiwala -> J2 Central Silk Board -> J3 Rupena Agrahara) modeling realistic vehicle kinematics, multi-class modal splits (two-wheelers, cars, buses, trucks, ambulances), and HBEFA4 emissions.

- **RO-2: Rigorous Multi-Controller Benchmarking**  
  Perform an empirical and statistically sound comparative evaluation of four distinct control paradigms:
  1. Classical Fixed-Time Coordination (pre-timed baseline)
  2. Coordinated Adaptive Queue-Balancing Heuristic
  3. Value-based Deep Reinforcement Learning (Dueling Double-DQN)
  4. Policy-gradient Multi-Agent Reinforcement Learning (Decentralized PPO)

- **RO-3: Runtime Safety Shielding & Deadlock Prevention**  
  Formulate and validate a formal safety shield wrapper operating between RL policy inference and hardware actuators to enforce 100% compliance with traffic safety standards (minimum green, maximum green, yellow clearance, all-red clearance, and anti-starvation preemption).

- **RO-4: Environmental Externality & Stoichiometric Auditing**  
  Quantify the direct linkage between corridor flow smoothing, cumulative queuing delay reduction, greenhouse gas emissions (CO2), and volumetric fuel consumption (L_petrol-eq), demonstrating physical mass conservation.

- **RO-5: Multi-Agent Credit Assignment Analysis**  
  Investigate the structural challenges of decentralized policy optimization across adjacent intersections, identifying why decentralized PPO exhibits non-stationary learning bottlenecks compared to heuristic coordination.
