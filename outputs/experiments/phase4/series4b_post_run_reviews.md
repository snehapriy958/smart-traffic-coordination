# Series 4B Post-Run Audit Log

Generated automatically after every completed 150-episode training run.

---

## Series 4B Post-Run Audit: Run 17 / 30

**Audit Timestamp:** 2026-11-12 19:31:48 IST  
**Completed Run:** Run 17 / 30  
**Algorithm:** MAPPO | **Observation Space:** 4-Dimensional | **Training Seed:** 104  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 3888.4s (~64.8 min) | **Throughput:** 2.31 ep/min (~25.92s/ep)  
**Total Verified Completed Runs:** 17 / 30  
**Total Verified Completed Episodes:** 2550 / 4500 (56.67%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_mappo_4dim_seed104.json`
  - **SHA-256:** `635a4147a90cb547f4844f6c1a0851319b84d1d7bad6e168dc0211b8d9ccbd7e`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_mappo_4dim_seed104.history.json`
  - **SHA-256:** `678c79a0d388efa22ec8a83d23b7a20700c625790079c2da398dc6fa71b7fa93`
- **Metadata Check:** Algorithm=`mappo`, ObservationDim=4, TrainSeed=104, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Actor & Critic Weights:** All junction actor networks (`J1`, `J2`, `J3`) and centralized critic parameters intact.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 17`, `episodes_completed: 2550` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -22.5092 +/- 3.6626 (range: [-31.76, -13.55])
- **First 25 Episodes Mean Reward:** -20.9475
- **Last 25 Episodes Mean Reward:** -23.5897 (Delta from First 25: -2.6423)
- **Last 10 Episodes Stability:** -23.8686 +/- 2.3187
- **Corridor Travel Time:** Overall Mean = 78.78s | Last 25 Episodes = 86.45s
- **Cumulative Delay:** Overall Mean = 12391.9 veh-s | Last 25 Episodes = 12778.5 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 3.82 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (75% load)
- **Free Disk Space:** 72.74 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 13172, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs (currently PID active). Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings detected in task logs.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 18 / 30** — MAPPO, 4-Dimensional Observation Space, Training Seed 105.
- **Next Run Status:** **`RUNNING`** (currently at Episode 51 / 150).
- **Estimated Remaining Training Time (Series 4B):** ~13.7 hours across remaining 13 runs (1899 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5343` through completion of Run 18 and subsequent runs.

---

## Series 4B Post-Run Audit: Run 18 / 30

**Audit Timestamp:** 2026-11-12 20:19:44 IST  
**Completed Run:** Run 18 / 30  
**Algorithm:** MAPPO | **Observation Space:** 4-Dimensional | **Training Seed:** 105  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 4146.1s (~69.1 min) | **Throughput:** 2.17 ep/min (~27.64s/ep)  
**Total Verified Completed Runs:** 18 / 30  
**Total Verified Completed Episodes:** 2700 / 4500 (60.00%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_mappo_4dim_seed105.json`
  - **SHA-256:** `5aff69bacd5ee8fe5b44dd9bb9c76a042a1acd77de7a83a7095e35aca9190ef1`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_mappo_4dim_seed105.history.json`
  - **SHA-256:** `7f9438196d249f6d3380aa45b9c3088605d5ee36e618ccd4ee88460aced040aa`
- **Metadata Check:** Algorithm=`mappo`, ObservationDim=4, TrainSeed=105, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Actor & Critic Weights:** All junction actor networks (`J1`, `J2`, `J3`) and centralized critic parameters intact.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 18`, `episodes_completed: 2700` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -25.2659 +/- 4.4431 (range: [-38.17, -15.69])
- **First 25 Episodes Mean Reward:** -23.7595
- **Last 25 Episodes Mean Reward:** -26.2811 (Delta from First 25: -2.5216)
- **Last 10 Episodes Stability:** -25.5732 +/- 4.5074
- **Corridor Travel Time:** Overall Mean = 88.51s | Last 25 Episodes = 88.24s
- **Cumulative Delay:** Overall Mean = 14200.9 veh-s | Last 25 Episodes = 14221.8 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 4.30 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (72% load)
- **Free Disk Space:** 72.67 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 28896, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings detected in task logs.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 19 / 30** — DQN, 14-Dimensional Observation Space, Training Seed 104.
- **Next Run Status:** **`RUNNING`** (currently at Episode 3 / 150 of dqn_14d_seed104).
- **Estimated Remaining Training Time (Series 4B):** ~13.8 hours across remaining 12 runs (1800 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5343` through completion of Run 19 and subsequent runs.

---

## Series 4B Post-Run Audit: Run 19 / 30

**Audit Timestamp:** 2026-11-12 21:38:26 IST  
**Completed Run:** Run 19 / 30  
**Algorithm:** DQN | **Observation Space:** 14-Dimensional | **Training Seed:** 104  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 4723.9s (~78.7 min) | **Throughput:** 1.91 ep/min (~31.49s/ep)  
**Total Verified Completed Runs:** 19 / 30  
**Total Verified Completed Episodes:** 2850 / 4500 (63.33%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_14dim_seed104.json`
  - **SHA-256:** `4464cf64c183aa7b2a275a849efdd6f383d92cf8ffd477a7bebfb5b98c87bbc6`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_14dim_seed104.history.json`
  - **SHA-256:** `38e56003bbf0bf3ac314177d392c93472825007f8d8b4b593b18fe65c362cf41`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=14, TrainSeed=104, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Actor & Critic Weights:** All junction Q-networks (`J1`, `J2`, `J3`) parameters intact.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 19`, `episodes_completed: 2850` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -26.5008 +/- 2.2565 (range: [-33.19, -19.90])
- **First 25 Episodes Mean Reward:** -27.6584
- **Last 25 Episodes Mean Reward:** -26.1985 (Delta from First 25: +1.4600)
- **Last 10 Episodes Stability:** -25.6805 +/- 2.2292
- **Corridor Travel Time:** Overall Mean = 92.43s | Last 25 Episodes = 91.38s
- **Cumulative Delay:** Overall Mean = 14367.1 veh-s | Last 25 Episodes = 14119.8 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 4.43 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (71% load)
- **Free Disk Space:** 74.21 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 37248, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings detected in task logs.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 20 / 30** — DQN, 14-Dimensional Observation Space, Training Seed 105.
- **Next Run Status:** **`RUNNING`** (currently at Episode 2 / 150 of dqn_14d_seed105).
- **Estimated Remaining Training Time (Series 4B):** ~14.4 hours across remaining 11 runs (1650 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5343` through completion of Run 20 and subsequent runs.

---

## Series 4B Post-Run Audit: Run 20 / 30

**Audit Timestamp:** 2026-11-12 23:03:47 IST  
**Completed Run:** Run 20 / 30  
**Algorithm:** DQN | **Observation Space:** 14-Dimensional | **Training Seed:** 105  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 4981.0s (~83.0 min) | **Throughput:** 1.81 ep/min (~33.21s/ep)  
**Total Verified Completed Runs:** 20 / 30  
**Total Verified Completed Episodes:** 3000 / 4500 (66.67%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_14dim_seed105.json`
  - **SHA-256:** `6bb740d4dddc8f2ba9956a9a49e67ffd6ca0e310747f515a94876ebf5002cf7c`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_14dim_seed105.history.json`
  - **SHA-256:** `1d85dce88a42f434737f9cb1c8d57988f59de47055d0cc64cc1a361031adaac2`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=14, TrainSeed=105, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Q-Network Weights:** All junction Q-networks (`J1`, `J2`, `J3`) parameters intact.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 20`, `episodes_completed: 3000` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -28.0738 +/- 3.1245 (range: [-35.03, -18.02])
- **First 25 Episodes Mean Reward:** -28.3182
- **Last 25 Episodes Mean Reward:** -28.0508 (Delta from First 25: +0.2675)
- **Last 10 Episodes Stability:** -26.2267 +/- 3.0606
- **Corridor Travel Time:** Overall Mean = 100.27s | Last 25 Episodes = 100.47s
- **Cumulative Delay:** Overall Mean = 14816.8 veh-s | Last 25 Episodes = 14672.6 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 4.27 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **Free Disk Space:** 73.71 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Finished Run 20 cleanly.
- **Training Exceptions:** 0 errors or warnings during Run 20.

### 5. Transition to Run 21
- **Next Scheduled Run:** Run 21 / 30 — DQN, 8-Dimensional Observation Space, Training Seed 101.

---

## Series 4B Post-Run Audit: Run 21 / 30

**Audit Timestamp:** 2026-11-13 00:38:14 IST  
**Completed Run:** Run 21 / 30  
**Algorithm:** DQN | **Observation Space:** 8-Dimensional | **Training Seed:** 101  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 5195.6s (~86.6 min) | **Throughput:** 1.73 ep/min (~34.64s/ep)  
**Total Verified Completed Runs:** 21 / 30  
**Total Verified Completed Episodes:** 3150 / 4500 (70.00%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_8dim_seed101.json`
  - **SHA-256:** `3b3a93462af0dbd006ba9160925fb56ad1e435daee21e23b19af602d22029095`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_8dim_seed101.history.json`
  - **SHA-256:** `5cf5fda91d04ada434eef3b62f0e4de2d677b96c5f153a63ae7787b745874e2e`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=8, TrainSeed=101, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Q-Network Weights:** All junction Q-networks (`J1`, `J2`, `J3`) weights intact with verified 8-dimensional input architecture.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 21`, `episodes_completed: 3150` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -25.8297 +/- 3.3299 (range: [-34.74, -19.24])
- **First 25 Episodes Mean Reward:** -29.5390
- **Last 25 Episodes Mean Reward:** -24.8437 (Delta from First 25: +4.6953)
- **Last 10 Episodes Stability:** -24.6660 +/- 3.0936
- **Corridor Travel Time:** Overall Mean = 104.44s | Last 25 Episodes = 100.09s
- **Cumulative Delay:** Overall Mean = 15215.7 veh-s | Last 25 Episodes = 14392.2 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 3.58 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (77% load)
- **Free Disk Space:** 70.57 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 8224, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings during Run 21.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 22 / 30** — DQN, 8-Dimensional Observation Space, Training Seed 102.
- **Next Run Status:** **`RUNNING`** (currently at Episode 2 / 150 of dqn_8d_seed102).
- **Estimated Remaining Training Time (Series 4B):** ~13.0 hours across remaining 9 runs (1350 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5920` through completion of Run 22 and subsequent runs.

---

## Series 4B Post-Run Audit: Run 22 / 30

**Audit Timestamp:** 2026-11-13 02:04:47 IST  
**Completed Run:** Run 22 / 30  
**Algorithm:** DQN | **Observation Space:** 8-Dimensional | **Training Seed:** 102  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 5173.9s (~86.2 min) | **Throughput:** 1.74 ep/min (~34.49s/ep)  
**Total Verified Completed Runs:** 22 / 30  
**Total Verified Completed Episodes:** 3300 / 4500 (73.33%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_8dim_seed102.json`
  - **SHA-256:** `97086d3dc244b0be4748d3ba2926a9c8a1a1cd51c5684c7bbe7b4ad89b6c5315`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_8dim_seed102.history.json`
  - **SHA-256:** `d9921791d259d3def11a89b323b6798da44a4b093b7a3f065004e775762dc594`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=8, TrainSeed=102, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Q-Network Weights:** All junction Q-networks (`J1`, `J2`, `J3`) weights intact with verified 8-dimensional input architecture.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 22`, `episodes_completed: 3300` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -23.3802 +/- 2.1589 (range: [-29.77, -18.61])
- **First 25 Episodes Mean Reward:** -22.6637
- **Last 25 Episodes Mean Reward:** -23.3086 (Delta from First 25: -0.6448)
- **Last 10 Episodes Stability:** -23.2730 +/- 1.3900
- **Corridor Travel Time:** Overall Mean = 80.08s | Last 25 Episodes = 80.38s
- **Cumulative Delay:** Overall Mean = 12202.0 veh-s | Last 25 Episodes = 12191.5 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 5.00 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (68% load)
- **Free Disk Space:** 70.07 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 28852, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings during Run 22.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 23 / 30** — DQN, 8-Dimensional Observation Space, Training Seed 103.
- **Next Run Status:** **`RUNNING`** (currently at Episode 3 / 150 of dqn_8d_seed103).
- **Estimated Remaining Training Time (Series 4B):** ~11.5 hours across remaining 8 runs (1200 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5920` through completion of Run 23 and subsequent runs.

---

## Series 4B Post-Run Audit: Run 23 / 30

**Audit Timestamp:** 2026-11-13 03:29:10 IST  
**Completed Run:** Run 23 / 30  
**Algorithm:** DQN | **Observation Space:** 8-Dimensional | **Training Seed:** 103  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 4590.8s (~76.5 min) | **Throughput:** 1.96 ep/min (~30.61s/ep)  
**Total Verified Completed Runs:** 23 / 30  
**Total Verified Completed Episodes:** 3450 / 4500 (76.67%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_8dim_seed103.json`
  - **SHA-256:** `cdbfb74b939f22bf41cd8d50682a1f74fb058e7131d1bced7546a4a0ece98e5d`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_8dim_seed103.history.json`
  - **SHA-256:** `e130e0482ebea21f28bb50dd0d4abfeb7f7d25b2c1267dc52b39e7b9b178273e`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=8, TrainSeed=103, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Q-Network Weights:** All junction Q-networks (`J1`, `J2`, `J3`) weights intact with verified 8-dimensional input architecture.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 23`, `episodes_completed: 3450` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -19.2039 +/- 3.0264 (range: [-31.33, -14.59])
- **First 25 Episodes Mean Reward:** -19.2788
- **Last 25 Episodes Mean Reward:** -18.4057 (Delta from First 25: +0.8731)
- **Last 10 Episodes Stability:** -18.6032 +/- 2.8256
- **Corridor Travel Time:** Overall Mean = 73.52s | Last 25 Episodes = 71.51s
- **Cumulative Delay:** Overall Mean = 10988.6 veh-s | Last 25 Episodes = 10907.7 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 3.48 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (78% load)
- **Free Disk Space:** 69.88 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 7048, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings during Run 23.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 24 / 30** — DQN, 8-Dimensional Observation Space, Training Seed 104.
- **Next Run Status:** **`RUNNING`** (currently at Episode 19 / 150 of dqn_8d_seed104).
- **Estimated Remaining Training Time (Series 4B):** ~8.8 hours across remaining 7 runs (1031 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5920` through completion of Run 24 and subsequent runs.

---

## Series 4B Post-Run Audit: Run 24 / 30

**Audit Timestamp:** 2026-11-13 04:35:59 IST  
**Completed Run:** Run 24 / 30  
**Algorithm:** DQN | **Observation Space:** 8-Dimensional | **Training Seed:** 104  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 4442.8s (~74.0 min) | **Throughput:** 2.03 ep/min (~29.62s/ep)  
**Total Verified Completed Runs:** 24 / 30  
**Total Verified Completed Episodes:** 3600 / 4500 (80.00%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_8dim_seed104.json`
  - **SHA-256:** `2cbf3a8e8552d17e9c3a163148afbe67df14317d0358bc93273a1ed5c123282e`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_8dim_seed104.history.json`
  - **SHA-256:** `36d5155490e1ac770b2287242fc38b8923841b2d4e3a24d2e82af94e3cabfeaa`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=8, TrainSeed=104, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Q-Network Weights:** All junction Q-networks (`J1`, `J2`, `J3`) weights intact with verified 8-dimensional input architecture.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 24`, `episodes_completed: 3600` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -22.2024 +/- 1.9250 (range: [-26.97, -16.72])
- **First 25 Episodes Mean Reward:** -21.7147
- **Last 25 Episodes Mean Reward:** -22.5883 (Delta from First 25: -0.8736)
- **Last 10 Episodes Stability:** -21.9385 +/- 2.4001
- **Corridor Travel Time:** Overall Mean = 77.07s | Last 25 Episodes = 77.91s
- **Cumulative Delay:** Overall Mean = 11328.4 veh-s | Last 25 Episodes = 11415.6 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 3.54 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (77% load)
- **Free Disk Space:** 69.65 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 21156, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings during Run 24.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 25 / 30** — DQN, 8-Dimensional Observation Space, Training Seed 105.
- **Next Run Status:** **`RUNNING`** (currently active).
- **Estimated Remaining Training Time (Series 4B):** ~7.4 hours across remaining 6 runs (900 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5920` through completion of Run 25 and subsequent runs.

---

## Series 4B Post-Run Audit: Run 25 / 30

**Audit Timestamp:** 2026-11-13 05:49:54 IST  
**Completed Run:** Run 25 / 30  
**Algorithm:** DQN | **Observation Space:** 8-Dimensional | **Training Seed:** 105  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 4502.9s (~75.0 min) | **Throughput:** 2.00 ep/min (~30.02s/ep)  
**Total Verified Completed Runs:** 25 / 30  
**Total Verified Completed Episodes:** 3750 / 4500 (83.33%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_8dim_seed105.json`
  - **SHA-256:** `247f3484ce9636cf3c840322ec9849cfa707b684e25f5b7557223b675c606b63`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_8dim_seed105.history.json`
  - **SHA-256:** `4c6d636566c9c2c0195c57d79b7c4b945f289e3c0606e21e1430f8ee53a92572`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=8, TrainSeed=105, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Q-Network Weights:** All junction Q-networks (`J1`, `J2`, `J3`) weights intact with verified 8-dimensional input architecture.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 25`, `episodes_completed: 3750` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -22.7911 +/- 2.4817 (range: [-29.54, -16.42])
- **First 25 Episodes Mean Reward:** -22.1209
- **Last 25 Episodes Mean Reward:** -22.7099 (Delta from First 25: -0.5890)
- **Last 10 Episodes Stability:** -23.2311 +/- 2.7453
- **Corridor Travel Time:** Overall Mean = 77.54s | Last 25 Episodes = 77.53s
- **Cumulative Delay:** Overall Mean = 12600.7 veh-s | Last 25 Episodes = 12531.0 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 3.16 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (80% load)
- **Free Disk Space:** 69.35 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 32088, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings during Run 25.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 26 / 30** — DQN, 4-Dimensional Observation Space, Training Seed 101.
- **Next Run Status:** **`RUNNING`** (currently active).
- **Estimated Remaining Training Time (Series 4B):** ~6.3 hours across remaining 5 runs (750 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5920` through completion of Run 26 and subsequent runs.

---

## Series 4B Post-Run Audit: Run 26 / 30

**Audit Timestamp:** 2026-11-13 07:12:58 IST  
**Completed Run:** Run 26 / 30  
**Algorithm:** DQN | **Observation Space:** 4-Dimensional | **Training Seed:** 101  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 4947.5s (~82.5 min) | **Throughput:** 1.82 ep/min (~32.98s/ep)  
**Total Verified Completed Runs:** 26 / 30  
**Total Verified Completed Episodes:** 3900 / 4500 (86.67%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_4dim_seed101.json`
  - **SHA-256:** `b4bc607f4818b8f23228afa5058623d8e2c6a0326e6aa24a8b86727539d8b5ff`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_4dim_seed101.history.json`
  - **SHA-256:** `1dbc1174593aef524522bfc4a70559836125664e3fed78607e46c9aae812cf72`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=4, TrainSeed=101, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Q-Network Weights:** All junction Q-networks (`J1`, `J2`, `J3`) weights intact with verified 4-dimensional input architecture.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 26`, `episodes_completed: 3900` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -33.8801 +/- 6.7323 (range: [-50.95, -19.11])
- **First 25 Episodes Mean Reward:** -29.8209
- **Last 25 Episodes Mean Reward:** -35.5395 (Delta from First 25: -5.7186)
- **Last 10 Episodes Stability:** -33.3503 +/- 6.0203
- **Corridor Travel Time:** Overall Mean = 118.80s | Last 25 Episodes = 122.07s
- **Cumulative Delay:** Overall Mean = 18745.3 veh-s | Last 25 Episodes = 19143.2 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 3.01 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (81% load)
- **Free Disk Space:** 69.27 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 17164, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings during Run 26.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 27 / 30** — DQN, 4-Dimensional Observation Space, Training Seed 102.
- **Next Run Status:** **`RUNNING`** (currently active).
- **Estimated Remaining Training Time (Series 4B):** ~5.5 hours across remaining 4 runs (600 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5920` through completion of Run 27 and subsequent runs.

---

## Series 4B Post-Run Audit: Run 27 / 30

**Audit Timestamp:** 2026-11-13 08:37:56 IST  
**Completed Run:** Run 27 / 30  
**Algorithm:** DQN | **Observation Space:** 4-Dimensional | **Training Seed:** 102  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 5141.1s (~85.7 min) | **Throughput:** 1.75 ep/min (~34.27s/ep)  
**Total Verified Completed Runs:** 27 / 30  
**Total Verified Completed Episodes:** 4050 / 4500 (90.00%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_4dim_seed102.json`
  - **SHA-256:** `3d879a1383cbb7f2daf05d2adbd0794622d091757022bd8561190f991904402d`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_4dim_seed102.history.json`
  - **SHA-256:** `d5c5ce16f7c401d76a916c1f813dd930bfcb488fc933ae9cf0cea60b86ebf9c8`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=4, TrainSeed=102, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Q-Network Weights:** All junction Q-networks (`J1`, `J2`, `J3`) weights intact with verified 4-dimensional input architecture.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 27`, `episodes_completed: 4050` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -40.5020 +/- 3.1683 (range: [-49.87, -23.36])
- **First 25 Episodes Mean Reward:** -40.5060
- **Last 25 Episodes Mean Reward:** -39.2801 (Delta from First 25: +1.2259)
- **Last 10 Episodes Stability:** -39.5259 +/- 2.4221
- **Corridor Travel Time:** Overall Mean = 75.62s | Last 25 Episodes = 77.14s
- **Cumulative Delay:** Overall Mean = 21996.3 veh-s | Last 25 Episodes = 21076.3 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 3.08 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (80% load)
- **Free Disk Space:** 70.20 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 26104, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings during Run 27.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 28 / 30** — DQN, 4-Dimensional Observation Space, Training Seed 103.
- **Next Run Status:** **`RUNNING`** (currently active).
- **Estimated Remaining Training Time (Series 4B):** ~4.3 hours across remaining 3 runs (450 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5920` through completion of Run 28 and subsequent runs.

---

## Series 4B Post-Run Audit: Run 28 / 30

**Audit Timestamp:** 2026-11-13 10:04:47 IST  
**Completed Run:** Run 28 / 30  
**Algorithm:** DQN | **Observation Space:** 4-Dimensional | **Training Seed:** 103  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 5200.1s (~86.7 min) | **Throughput:** 1.73 ep/min (~34.67s/ep)  
**Total Verified Completed Runs:** 28 / 30  
**Total Verified Completed Episodes:** 4200 / 4500 (93.33%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_4dim_seed103.json`
  - **SHA-256:** `504bbf2c6d550a3aff2cbbb7a585fb4627cb1195c66cd7f0113affd62a0b5c37`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_4dim_seed103.history.json`
  - **SHA-256:** `dc648d941745f9093877100fa58ca72de8f8a1543a99701b7a2cee7359f80ca6`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=4, TrainSeed=103, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Q-Network Weights:** All junction Q-networks (`J1`, `J2`, `J3`) weights intact with verified 4-dimensional input architecture.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 28`, `episodes_completed: 4200` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -22.9484 +/- 2.6654 (range: [-31.91, -16.44])
- **First 25 Episodes Mean Reward:** -22.2206
- **Last 25 Episodes Mean Reward:** -23.7230 (Delta from First 25: -1.5024)
- **Last 10 Episodes Stability:** -24.2507 +/- 2.3652
- **Corridor Travel Time:** Overall Mean = 96.78s | Last 25 Episodes = 93.85s
- **Cumulative Delay:** Overall Mean = 13250.3 veh-s | Last 25 Episodes = 13146.4 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 2.85 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (82% load)
- **Free Disk Space:** 69.96 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 19228, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings during Run 28.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 29 / 30** — DQN, 4-Dimensional Observation Space, Training Seed 104.
- **Next Run Status:** **`RUNNING`** (currently active).
- **Estimated Remaining Training Time (Series 4B):** ~2.9 hours across remaining 2 runs (300 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5920` through completion of Run 29 and subsequent runs.

---

## Series 4B Post-Run Audit: Run 29 / 30

**Audit Timestamp:** 2026-11-13 11:31:41 IST  
**Completed Run:** Run 29 / 30  
**Algorithm:** DQN | **Observation Space:** 4-Dimensional | **Training Seed:** 104  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 5157.4s (~86.0 min) | **Throughput:** 1.75 ep/min (~34.38s/ep)  
**Total Verified Completed Runs:** 29 / 30  
**Total Verified Completed Episodes:** 4350 / 4500 (96.67%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_4dim_seed104.json`
  - **SHA-256:** `9a911bf3ac6ba051496b5eac6e105055d2cc899a8a39a82ab2b33e9a5455567d`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_4dim_seed104.history.json`
  - **SHA-256:** `9f8a71e65febda07fa559a4ff39b483136938954b5879e60492ef448aaede15e`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=4, TrainSeed=104, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Q-Network Weights:** All junction Q-networks (`J1`, `J2`, `J3`) weights intact with verified 4-dimensional input architecture.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 29`, `episodes_completed: 4350` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -23.4488 +/- 2.4537 (range: [-30.60, -18.35])
- **First 25 Episodes Mean Reward:** -23.5165
- **Last 25 Episodes Mean Reward:** -22.0432 (Delta from First 25: +1.4733)
- **Last 10 Episodes Stability:** -22.3364 +/- 0.9639
- **Corridor Travel Time:** Overall Mean = 85.18s | Last 25 Episodes = 84.51s
- **Cumulative Delay:** Overall Mean = 13515.4 veh-s | Last 25 Episodes = 12750.0 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 2.11 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (86% load)
- **Free Disk Space:** 69.78 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 19332, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings during Run 29.

### 5. Next Run Status & Schedule
- **Next Expected Run:** **Run 30 / 30 (FINAL TRAINING RUN)** — DQN, 4-Dimensional Observation Space, Training Seed 105.
- **Next Run Status:** **`RUNNING`** (currently active).
- **Estimated Remaining Training Time (Series 4B):** ~1.4 hours across remaining 1 run (150 episodes).
- **Recommended Action:** Continue uninterrupted execution in `task-5920` through completion of Run 30, followed immediately by the 300 confirmatory evaluation runs.

---

## Series 4B Post-Run Audit: Run 30 / 30 (FINAL TRAINING RUN COMPLETE)

**Audit Timestamp:** 2026-11-13 13:03:07 IST  
**Completed Run:** Run 30 / 30  
**Algorithm:** DQN | **Observation Space:** 4-Dimensional | **Training Seed:** 105  
**Completed Episodes:** 150 / 150  
**Run Wall-Clock Time:** 5454.2s (~90.9 min) | **Throughput:** 1.65 ep/min (~36.36s/ep)  
**Total Verified Completed Runs:** 30 / 30 (100.00% TRAINING COMPLETED)  
**Total Verified Completed Episodes:** 4500 / 4500 (100.00%)  

### 1. Checkpoint & Artifact Verification
- **Checkpoint File:** `checkpoints/phase4/final_150ep/series_4b_dqn_4dim_seed105.json`
  - **SHA-256:** `35a66d34570dbc37bac505257bcf5325a36a7c8c77ba8fb36605f9b4c9fd0d5d`
- **History File:** `checkpoints/phase4/final_150ep/series_4b_dqn_4dim_seed105.history.json`
  - **SHA-256:** `681d4d86e04566725a1f84ddc0ff7aa27e6b3fb1697046c1ed9bdff6b76d4770`
- **Metadata Check:** Algorithm=`dqn`, ObservationDim=4, TrainSeed=105, Episodes=150
- **Verified 150ep Flag:** `True` (PASS)
- **Q-Network Weights:** All junction Q-networks (`J1`, `J2`, `J3`) weights intact with verified 4-dimensional input architecture.
- **Numerical Stability:** 0 NaN, 0 Infinity values across all 150 episodes (PASS).
- **Simulation Duration Compliance:** 150 / 150 episodes terminated at exactly `1200.00` simulation seconds (PASS).

### 2. Manifest Consistency
- **Manifest Status:** `training_runs_completed: 30`, `episodes_completed: 4500` (PASS).
- **Recorded Path & Integrity:** File paths match disk locations with zero duplication across all 30/30 runs.

### 3. Training Performance & Trajectory
- **Overall Mean Reward:** -34.8634 +/- 3.0766 (range: [-41.95, -23.45])
- **First 25 Episodes Mean Reward:** -31.7473
- **Last 25 Episodes Mean Reward:** -35.2686 (Delta from First 25: -3.5213)
- **Last 10 Episodes Stability:** -34.8435 +/- 2.4019
- **Corridor Travel Time:** Overall Mean = 72.76s | Last 25 Episodes = 72.22s
- **Cumulative Delay:** Overall Mean = 19160.5 veh-s | Last 25 Episodes = 19372.0 veh-s
- **Throughput:** 109.0 vehicles completed per episode across all evaluations.

### 4. System Health & Safeguards
- **Physical RAM Available:** 2.66 GB (Safeguard >= 1.2 GB: **HEALTHY**)
- **RAM Total & Load:** 15.82 GB (83% load)
- **Free Disk Space:** 69.20 GB (Safeguard >= 5.0 GB: **HEALTHY**)
- **Active Worker Process:** Single Python process (PID 37464, 0 duplicates)
- **SUMO / TraCI Status:** Actively cycling clean PIDs. Zero orphaned processes.
- **Training Exceptions:** 0 errors or warnings during Run 30.

### 5. Final Evaluation Phase Status
- **Training Complete:** 30 / 30 runs, 4,500 / 4,500 episodes (100.00%)
- **Next Phase:** **Confirmatory Evaluations (300 runs)** — 30 configurations x 10 evaluation seeds (seeds 1–10), 900.0s simulation duration.
- **Recommended Action:** Continue execution through all 300 evaluations, compute final statistical analysis, update research paper records, and produce final audit.
