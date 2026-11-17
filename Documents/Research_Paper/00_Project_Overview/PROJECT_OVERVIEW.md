# Project Overview: Bengaluru Traffic Intelligence Platform
**System**: Smart Traffic Coordination System — Cyber-Physical Corridor Simulation Twin  
**Target Corridor**: Hosur Road Arterial Corridor, Bengaluru (J1 Madiwala -> J2 Central Silk Board -> J3 Rupena Agrahara)  
**Corridor Geometry**: 306 directed edges, 213 junctions, 490 lanes compiled in UTM Zone 43N (EPSG:32643)  
**Primary Research Goal**: Comparative benchmarking and cyber-physical validation of classical, rule-based adaptive, and multi-agent reinforcement learning traffic signal controllers under heterogeneous traffic dynamics with runtime safety shielding.

---

## 1. System Vision & Cyber-Physical Twin Architecture
Urban traffic congestion across high-density developing metropolitan corridors—such as Bengaluru's Central Silk Board nexus—presents severe challenges: non-lane-based traffic flows, extreme modal heterogeneity, high two-wheeler saturation (>67%), and recurrent intersection spillback. 

This platform implements an end-to-end cyber-physical simulation twin integrating:
1. **SUMO Microscopic Engine**: High-fidelity vehicle kinematic and emission simulation (HBEFA4/2.0).
2. **TraCI Real-Time Telemetry Pipeline**: Sub-second extraction of approach queue lengths, instantaneous velocities, and vehicle modal states.
3. **Multi-Agent Coordination & Safety Shield Layer**: Real-time signal phase optimization subject to strict NEMA/IRC clearance constraints (15s min green, 60s max green, 4s yellow, 2s all-red).
4. **FastAPI & WebSocket Observability Backend**: Sub-10ms state broadcast to interactive visualizers.

---

## 2. Experimental Scope & Boundary Qualifications
- **Simulation Environment**: High-fidelity microscopic digital twin constructed from OpenStreetMap road geometry and configured dynamic travel demand.
- **Empirical Field Status**: Synthetic demand configuration reflecting heterogeneous vehicle classes. Empirical calibration against live field inductive loop / radar sensors is scoped as future municipal work.
- **Master Benchmark Horizon**: 900.0s (15 minutes), comprising Peak (0-300s), Shoulder (300-600s), and Off-Peak (600-900s) traffic regimes across 10 matched random seeds (Seeds 1-10, df=9).
