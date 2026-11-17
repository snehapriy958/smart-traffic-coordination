# Traffic Network & Demand Dataset Specification

## 1. Network Topology
- **Source**: OpenStreetMap (OSM) extraction of Hosur Road corridor, Bengaluru.
- **Coordinate Reference System**: EPSG:32643 (UTM Zone 43N).
- **Directed Edges**: 306
- **Junction Nodes**: 213 (3 signalized corridor intersections, 210 unsignalized merges/turnarounds)
- **Lanes**: 490 (including dedicated turning pockets and bus lanes)
- **Netconvert File**: `sumo/silk_board/network/silk_board.net.xml`

## 2. Configured Dynamic Travel Demand
Demand is dynamically inserted over $T_{\text{insert}} = 600.0\text{ s}$ across three traffic regimes:
1. **Peak Congestion ($0 \le t < 300\text{ s}$)**: High inflow rate ($\sim 2{,}500\text{ veh/h}$ equivalent), heavy directional tidal flow J1 -> J2 -> J3.
2. **Shoulder Decline ($300 \le t < 600\text{ s}$)**: Moderate inflow rate ($\sim 1{,}500\text{ veh/h}$ equivalent), balanced cross-street traffic.
3. **Off-Peak Dissipation ($600 \le t \le 900\text{ s}$)**: Inflow ceases ($0\text{ veh/h}$), allowing residual queue clearance.

- **Total Vehicles Departed**: Exactly 378 vehicles.
- **Corridor Throughput Trips**: Exactly 109 vehicles complete the entire J1 -> J2 -> J3 traversal.
- **Completion Rate**: 100% of departed vehicles arrive by $T = 900.0\text{ s}$.
