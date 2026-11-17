# Benchmark Configuration

- **Simulation Platform**: Eclipse SUMO v1.26.0 / TraCI Python Client
- **Random Seeds**: 10 seeds ($S = \{1, 2, 3, 4, 5, 6, 7, 8, 9, 10\}$)
- **Corridor Edges**: `172853382#2`, `172853382#3`, `464465165#0`, `92196679#0`, `1148717038#0`, `40696223#1`, `-148697299`, `-744783934`
- **Entry Edge**: `172853382#2` (J1 Madiwala approach)
- **Exit Edge**: `40696223#1` (J3 Rupena Agrahara departure)
- **Time Horizon**: 900.0 seconds
- **Traffic Regimes**:
  - Peak: $0 \le t < 300\text{ s}$
  - Shoulder: $300 \le t < 600\text{ s}$
  - Off-Peak: $600 \le t \le 900\text{ s}$
