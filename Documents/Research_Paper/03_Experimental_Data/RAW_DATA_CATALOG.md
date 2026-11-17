# Raw Data Catalog & JSON Field Specifications

All 40 master run records are stored in `outputs/validation/10seeds/runs/run_{controller}_seed{seed}.json`.

Each file contains the following primary top-level dictionary structures:

1. `mode`: Controller name (`baseline`, `coordinated`, `marl_dqn`, `marl_ppo`).
2. `seed`: Random generator seed integer ($1 \dots 10$).
3. `duration_s`: 900 seconds.
4. `wall_time_s`: Real-world execution duration (typically 35-45 seconds per run).
5. `status`: `COMPLETED`.
6. `phase_switches`: Number of phase transitions per junction (`J1`, `J2`, `J3`).
7. `action_counts`: Decisions made per junction (`KEEP`, `SWITCH`, `EXTEND`).
8. `starvation_events_count`: Number of safety-shield anti-starvation preemption interventions.
9. `regimes`: Temporal interval breakdown (`peak`: [0, 300], `shoulder`: [300, 600], `off_peak`: [600, 900]).
10. `full_900s`: Complete aggregate metrics over the entire 900-second horizon:
    - `departed`: Total vehicles entered (378).
    - `arrived`: Total vehicles arrived (378).
    - `corridor_trips`: Vehicles traversing J1 -> J2 -> J3 (109).
    - `unfinished`: Vehicles remaining on network at step 900 (0).
    - `avg_corridor_travel_time_s`: Mean corridor traversal duration (s).
    - `avg_speed_kmh`: Mean corridor speed (km/h).
    - `avg_waiting_time_s`: Mean vehicle waiting time (s).
    - `cumulative_delay_veh_s`: Total Riemann sum of queue delay ($D_{\text{cum}}$, $\text{veh}\cdot\text{s}$).
    - `co2_kg`: Cumulative carbon dioxide mass ($10^{-6} \sum \text{mg}$).
    - `fuel_liters`: Petrol-equivalent volumetric consumption index ($\text{mg} / 750{,}000$).
