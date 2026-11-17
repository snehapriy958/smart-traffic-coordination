# Section III: Problem Formulation & Corridor Modeling

## A. Corridor Network Topology
The corridor network $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ represents the Hosur Road arterial in Bengaluru, comprising three consecutive signalized junctions:
- J1: Madiwala (TLS: `1617743335`)
- J2: Central Silk Board (TLS: `GS_cluster_10282769895_10775075568_11964440742_11964440743`)
- J3: Rupena Agrahara (TLS: `6970466614`)
The microscopic network comprises 306 directed edges, 213 junctions, and 490 lanes compiled in UTM Zone 43N (EPSG:32643).

## B. Fleet Heterogeneity & Demand Profile
Configured dynamic travel demand inserts 378 vehicles over 600s dynamic insertion. All 378 vehicles complete their trips by $T = 900.0\text{ s}$.
- Network Departures ($N=378$): 257 motorcycles (67.99%), 103 passenger cars (27.25%), 12 BMTC buses (3.17%), 5 heavy trucks (1.32%), 1 emergency ambulance (0.26%).
- Corridor Traversal Trips ($N=109$): 73 motorcycles (66.97%), 31 cars (28.44%), 2 buses (1.83%), 2 trucks (1.83%), 1 ambulance (0.92%).
