# Figure Catalog & Visualization Plan

| Figure ID | Title | Description | Source Data / Script | Artifact Status |
| :---: | :--- | :--- | :--- | :---: |
| **Fig. 1** | System Architecture | Cyber-physical twin pipeline (SUMO, TraCI, Shield, FastAPI, WS) | `SYSTEM_ARCHITECTURE.md` | **ASCII Rendered (Vector PDF Planned)** |
| **Fig. 2** | Corridor Network Topology | OSM microscopic road network (J1, J2, J3, 306 edges) | `sumo/silk_board/network/silk_board.net.xml` | **Source Data Verified (GIS Render Planned)** |
| **Fig. 3** | Travel Time Boxplots | 10-seed distributions across Fixed-Time, Adaptive, DQN, PPO | `outputs/validation/10seeds/runs/*.json` | **Reproducible Data Ready (Plot Script Planned)** |
| **Fig. 4** | Cumulative Delay Progression | Riemann sum curves over 900s horizon across 3 regimes | `outputs/validation/10seeds/runs/*.json` | **Reproducible Data Ready (Plot Script Planned)** |
| **Fig. 5** | Mean Corridor Speed | Velocity trajectory curves across peak, shoulder, off-peak | `outputs/validation/10seeds/runs/*.json` | **Reproducible Data Ready (Plot Script Planned)** |
| **Fig. 6** | Emissions & Fuel Tradeoffs | CO2 mass vs. petrol-equivalent fuel volume scatter | `outputs/validation/10seeds/runs/*.json` | **Reproducible Data Ready (Plot Script Planned)** |
| **Fig. 7** | Safety Shield State Machine | Decision tree enforcing min/max green, clearance, preemption | `SAFETY_CONSTRAINTS.md` | **Flowchart Rendered (Vector PDF Planned)** |
| **Fig. 8** | Fleet Composition Donut | Departed vehicle modal split (68% 2W, 27% Car, 3% Bus, 1% HGV)| `VEHICLE_COMPOSITION.md` | **Reproducible Data Ready (Plot Script Planned)** |

*Note: All numerical data for Figures 3–6 and 8 reside in unedited JSON execution records. Plot scripts will generate publication-ready EPS/PDF graphics during IEEE/Elsevier LaTeX typesetting.*
