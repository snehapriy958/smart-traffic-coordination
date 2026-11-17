# Summary of Manuscript Tables & Verification Status

| Table ID | Title & Description | Source Evidence | Generation Status |
| :---: | :--- | :--- | :---: |
| **Table I** | **Master Corridor Benchmark Performance Matrix ($N = 10$ Seeds)**<br>Travel Time, Relative Change, Paired $t$, $p$-values, Bonferroni, Cohen's $d_z$, Cumulative Delay, Speed, CO2, Fuel | 40 raw JSON runs in `outputs/validation/10seeds/runs/*.json` | **ACTUALLY GENERATED & VERIFIED** |
| **Table 1b** | **Empirical Vehicle Fleet Composition & Microscopic Modal Split**<br>Network Departures ($N=378$) & Corridor Trips ($N=109$) across 5 vehicle classes | Departure logs parsed via `scratch/analyze_departed_fleet.py` | **ACTUALLY GENERATED & VERIFIED** |
| **Table II** | **Primary Research Hypothesis Testing & Statistical Sign-Off**<br>Decisions on H1, H2, H3, H4 with parametric & non-parametric tests | `statistical_analysis.json` ($df=9$) | **ACTUALLY GENERATED & VERIFIED** |
| **Table III** | **Safety Shield Constraint Boundaries & Clearance Parameters**<br>Min/max green ($15\text{s}/60\text{s}$), yellow/all-red ($4\text{s}/2\text{s}$), anti-starvation ($120\text{s}$) | `traffic_service/signal_controller.py` | **ACTUALLY GENERATED & VERIFIED** |
| **Table IV** | **Chemical Stoichiometric Combustion & Mass Conservation Matrix**<br>Theoretical octane chemistry vs. empirical HBEFA4 simulation mass balance | HBEFA4 integration ($0.208\%$ deviation) | **ACTUALLY GENERATED & VERIFIED** |
