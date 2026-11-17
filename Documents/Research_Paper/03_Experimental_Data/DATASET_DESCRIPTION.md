# Dataset Description: Bengaluru Arterial Corridor

## 1. Network Data Files
- **SUMO Network File**: `sumo/silk_board/network/silk_board.net.xml` (306 edges, 213 junctions, 490 lanes).
- **Vehicle Types Definition**: `sumo/silk_board/demand/vehicle_types.add.xml`.
- **Route & Flow Generation**: `sumo/silk_board/demand/silk_board.rou.xml`.
- **SUMO Configuration**: `sumo/silk_board/simulation.sumocfg`.

## 2. Simulation Step Parameters
- Simulation step length: $\Delta t = 1.0\text{ s}$.
- Controller decision interval: $\Delta t_{\text{dec}} = 5.0\text{ s}$.
- Inflow duration: $600.0\text{ s}$.
- Total evaluation duration: $900.0\text{ s}$.
