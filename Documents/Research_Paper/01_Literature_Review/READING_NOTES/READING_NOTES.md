# Annotated Reading Notes on 16 Core Literature References

### 1. Webster (1958) - Traffic Signal Settings
- **Core Contribution**: Introduced the classical cycle-length formula $C_0 = (1.5L + 5) / (1 - Y)$ minimizing steady-state vehicle delay for fixed-time controllers.
- **Relevance**: Represents the baseline against which all modern adaptive and RL algorithms are benchmarked.
- **Limitation**: Assumes uniform arrival distributions and lane-disciplined passenger cars, failing under peak oversaturation and high two-wheeler flows.

### 2. Hunt et al. (1981) - SCOOT
- **Core Contribution**: Developed Split, Cycle, and Offset Optimization Technique using cyclic flow profiles from upstream inductive loop detectors.
- **Relevance**: Foundation of coordinated arterial progression.
- **Limitation**: Centralized architecture creates single points of failure and requires extensive manual calibration.

### 3. Lowrie (1990) - SCATS
- **Core Contribution**: Sydney Co-ordinated Adaptive Traffic System; dynamically selects signal plans based on degree of saturation (DS) at stop-lines.
- **Relevance**: Benchmark for industry-standard closed-loop adaptive control.
- **Limitation**: Relies on rigid predefined phase stages and discrete step adjustments.

### 4. Koonce & Rodegerdts (2008) - Traffic Signal Timing Manual (FHWA)
- **Core Contribution**: Comprehensive US Federal guidelines for minimum green, yellow change, and all-red clearance intervals.
- **Relevance**: Defines the mathematical safety constraints for our runtime safety shield ($g_{\min} \ge 15	ext{s}, y = 4	ext{s}, r = 2	ext{s}$).

### 5. Genders & Razavi (2016) - Deep Q-Learning for Traffic Signal Control
- **Core Contribution**: First modern demonstration of DQN applied to single-intersection signal state.
- **Relevance**: Proven feasibility of deep Q-learning with discrete action spaces.

### 6. Wei et al. (2018) - IntelliLight
- **Core Contribution**: Phase-gate Deep Q-Network utilizing rich state inputs (queues, waiting times, images).
- **Relevance**: Informed our reward function structure balancing queue changes and delay.

### 7. Wei et al. (2019) - CoLight
- **Core Contribution**: Multi-intersection coordination via graph attention networks (GAT) to model spatial dependencies between neighbors.
- **Relevance**: High-performing multi-agent architecture; highlights credit-assignment complexity in multi-hop corridors.

### 8. Zheng et al. (2019) - PressLight
- **Core Contribution**: Integrates Max-Pressure control theory into RL reward functions, proving that minimizing pressure between upstream and downstream queues guarantees network stability.
- **Relevance**: Directly inspired our Coordinated Adaptive queue-pressure heuristic.

### 9. Alshiekh et al. (2018) - Safe Reinforcement Learning via Shielding
- **Core Contribution**: Introduced runtime shielding where an external safety monitor intercepts and corrects unsafe exploratory RL actions based on temporal logic.
- **Relevance**: Theoretical foundation for our deterministic safety shield state machine.

### 10. Al-Dabbagh et al. (2021) - Multi-Objective RL for Traffic Signal Control
- **Core Contribution**: Analyzed Pareto tradeoffs between vehicle delay, vehicular emissions, and pedestrian wait times.
- **Relevance**: Justifies our multi-objective evaluation across travel time, cumulative delay, and HBEFA4 emissions.

### 11. Notter et al. (2019) - HBEFA 4.1 Development Report
- **Core Contribution**: Handbook of Emission Factors for Road Transport v4.1; provides microscopic emission factors (mg/s) for European vehicle fleets.
- **Relevance**: Basis for SUMO's internal emissions engine (Euro-4 petrol cars, Euro-VI diesel buses/trucks).

### 12. Lopez et al. (2018) - Microscopic Traffic Simulation using SUMO
- **Core Contribution**: Standard reference for Eclipse SUMO architecture, car-following models, and TraCI.
- **Relevance**: The simulation core of this entire research work.

### 13. Krajzewicz et al. (2012) - Traffic Control Interface (TraCI)
- **Core Contribution**: Real-time socket protocol coupling simulation engines to external Python control scripts.
- **Relevance**: The fundamental communication bridge enabling our sub-second controller execution.

### 14. Le et al. (2017) - Decentralized Signal Control with Max-Pressure
- **Core Contribution**: Rigorous mathematical proof that decentralized max-pressure control maximizes corridor throughput without global coordination.
- **Relevance**: Explains why decentralized queue heuristics match or exceed complex MARL agents in linear arterial corridors.

### 15. Chen et al. (2019) - MetaLight
- **Core Contribution**: Meta-reinforcement learning enabling rapid adaptation of traffic agents across multiple intersections and demand shifts.
- **Relevance**: Demonstrates transferability challenges across diverse urban geometries.

### 16. Zhang et al. (2019) - CityFlow
- **Core Contribution**: Massively parallel traffic simulator designed for large-scale multi-agent RL benchmarking.
- **Relevance**: Establishes standard benchmarking protocols for multi-intersection comparative research.
