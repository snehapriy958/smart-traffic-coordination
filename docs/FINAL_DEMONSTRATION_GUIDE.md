# Smart Traffic Coordination System — Final Demonstration Guide

**Project:** Smart Traffic Coordination System – Bengaluru Silk Board Corridor  
**Target Audience:** Final-Year Engineering Project Evaluators, Reviewers, and Demonstration Team  
**Evaluation Baseline:** Phase 5 Verified Findings and Protocol  
**Date:** 2026-11-09  

---

## 1. System Requirements & Environment Setup

### 1.1 Prerequisites
- **Operating System:** Windows 10/11 x64 (or Linux Ubuntu 22.04+)
- **Python:** Python 3.11, 3.12, or 3.13 (`torch>=2.0.0`, `fastapi>=0.100.0`, `uvicorn>=0.22.0`, `traci>=1.18.0`)
- **SUMO:** Eclipse SUMO $\ge 1.18.0$ (verified on version 1.26.0)
- **Node.js:** Node.js v18+, v20+, or v22+ (`npm>=9.0.0`)

### 1.2 Environment Configuration
Ensure Eclipse SUMO is installed and added to the system environment path:
```powershell
# In PowerShell:
$env:SUMO_HOME = "C:\Program Files (x86)\Eclipse\Sumo"
sumo --version
# Expected: Eclipse SUMO sumo Version 1.26.0 (or higher)
```

---

## 2. Step-by-Step Application Startup

### 2.1 Backend Service Startup
Open a terminal in the project root directory and start the FastAPI asynchronous server:
```powershell
# From repository root
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*Expected Terminal Output:*
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
[Database] Schema initialized and pre-seeded.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 2.2 Frontend Application Startup
Open a second terminal in the project root directory and start the Vite development server:
```powershell
# From repository root
npm --prefix frontend run dev
```
*Expected Terminal Output:*
```
  VITE v5.4.21  ready in 480 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 2.3 Verification of Connectivity
Open Google Chrome or Microsoft Edge and navigate to:
```
http://localhost:5173/
```
Verify that:
1. The top header shows **Silk Board Corridor — Live Traffic Twin**.
2. The WebSocket connection indicator shows a green **LIVE** badge.
3. The KPI ribbons and 2D corridor diagram load with initialized zeroed state.

---

## 3. Recommended Project Demonstration Sequence

```
+----------------------------------------------------------------------------------------------------+
|                                    DEMONSTRATION WALKTHROUGH                                       |
|                                                                                                    |
|  [Step 1: 3D Twin] ──► [Step 2: Baseline] ──► [Step 3: Coordinated] ──► [Step 4: MARL DQN]        |
|   Inspect Road          Observe Standing       Show Green-Wave          Show Learned Q-Policy      |
|   Elevations &          Queues at J2           Progression &            & 15s Safety Shield        |
|   Support Piers         (59 veh peak)          45.61% TT Drop           Enforcement                |
|                                                                                                    |
|                                └──► [Step 5: Emergency Wave] ──► [Step 6: Defense Q&A]            |
|                                      Ambulance Corridor          Scientific Disclosures &          |
|                                      Preemption Clearance        Paired Statistical Bounds         |
+----------------------------------------------------------------------------------------------------+
```

### Step 1: 3D Corridor Digital Twin Inspection
1. On the dashboard, click the **"Switch to 3D Corridor Digital Twin"** button.
2. Demonstrate the camera navigation presets on the top toolbar:
   - **Corridor Overview:** Explains the continuous arterial spine from Madiwala ($J_1$) across Central Silk Board ($J_2$) to Bommanahalli ($J_3$).
   - **J1 Madiwala Checkpost:** Zooms to the depressed Madiwala Underpass modeled at $-4.5\text{ m}$ relative elevation.
   - **J2 Central Silk Board:** Highlights the +8.0m elevated Silk Board Flyover supported by cylindrical concrete piers.
   - **J3 Rupena Agrahara:** Demonstrates the southern exit signal discharging into Electronic City.
3. Open the **Layers Menu** and toggle off/on the elevated flyover and concrete support pillars to show procedural mesh construction.
4. **Evaluator Talking Point:**
   > *"The 3D view is an architectural digital twin extruded from SUMO network coordinates to model true spatial elevations. Live vehicle counts and dynamic signal phase aspects are rendered on the 2D live canvas at 10 Hz over WebSockets."*

### Step 2: Baseline Fixed-Time Controller Demonstration
1. Return to the 2D Dashboard.
2. Select **Fixed-Time Baseline** in the controller dropdown.
3. Set duration to `300` seconds and click **Start Simulation**.
4. Observe the traffic dynamics:
   - During peak loading ($0–300\text{ s}$), fixed phase allocations fail to adapt to heavy Hosur Road arrivals.
   - Standing queues build up rapidly at $J_2$ (Central Silk Board), reaching peak queues of 47–59 vehicles.
   - Corridor speed drops below $28\text{ km/h}$, with average travel time reaching $89.87\text{ s}$.
5. Click **Stop Simulation** or allow it to complete, and point out the resulting cumulative delay ($12{,}357\text{ veh}\cdot\text{s}$) and emissions ($55.56\text{ kg CO}_2$).

### Step 3: Coordinated Adaptive Controller Demonstration
1. Click **Reset Simulation** to clear the session.
2. Select **Coordinated Adaptive** in the controller dropdown and click **Start Simulation**.
3. Observe the marked difference in traffic flow:
   - Dynamic cycle length adjustments synchronize green intervals across $J_1$, $J_2$, and $J_3$.
   - Platoons arriving from Madiwala receive green waves through Silk Board, preventing congestion bottlenecks.
   - Mean corridor queue remains under $6.4\text{ vehicles}$ (compared to $13.7\text{ vehicles}$ under Baseline).
   - Average corridor speed increases by **+35.12%** ($38.20\text{ km/h}$ vs. $28.28\text{ km/h}$).
   - Corridor travel time drops by **-45.61%** ($48.88\text{ s}$ vs. $89.87\text{ s}$).
   - Fuel consumption is reduced by **-23.25%** ($18.41\text{ L}$ vs. $23.99\text{ L}$).
4. **Evaluator Talking Point:**
   > *"Coordinated Adaptive control achieves the highest overall corridor efficiency by anticipating platoon arrival times and establishing green-wave progression offsets across the three intersections."*

### Step 4: MARL Double-DQN Controller & Safety Shield Demonstration
1. Click **Reset Simulation**.
2. Select **MARL DQN (Trained Double-DQN Checkpoint)** and click **Start Simulation**.
3. Point out the real-time AI decision-making:
   - Independent Dueling Double-DQN agents at $J_1, J_2, J_3$ observe 14-dimensional local state vectors (queue lengths, approach speeds, waiting times, downstream pressure).
   - The learned policy switches phases to relieve high-density lanes, cutting corridor travel time by **-34.82%** ($58.57\text{ s}$) and cumulative delay by **-33.88%** ($8{,}169\text{ veh}\cdot\text{s}$) relative to Baseline.
4. **Demonstrating Safety Shield Enforcement:**
   - On the Signal Status panel, attempt to force a manual phase change immediately after a switch has occurred.
   - Point out that the system rejects the request: the deterministic safety shield strictly enforces a $15.0\text{-second}$ minimum green duration (`min_green = 15.0`), preventing hazardous rapid signal cycling.
   - If side-street red time reaches 60 seconds, point out that the anti-starvation preemption mechanism automatically triggers to prevent cross-street starvation.

### Step 5: Emergency Vehicle Green Wave Preemption
1. While any simulation mode is active, trigger an emergency preemption event via the Emergency Panel (or observe the scheduled `ambulance_0` insertion at $t=420\text{ s}$).
2. Observe the coordinated emergency wave:
   - Upstream and downstream signals immediately transition through safety yellow and lock green for the emergency corridor route.
   - The 2D corridor displays the pulsing **Emergency Green Wave Active** banner.
   - The ambulance clears the 1.25 km corridor with zero queue stoppages.
   - Once the emergency vehicle exits edge `40696223#1`, signals unlock and return safely to normal coordinated control.

---

## 4. Scientific Defense Talking Points & Q&A Preparation

| Potential Reviewer Question | Rigorous Engineering Defense |
| :--- | :--- |
| **"Why does Coordinated Adaptive outperform the Reinforcement Learning agents?"** | *"Coordinated Adaptive uses analytical green-wave progression equations specifically engineered for linear arterial corridors with predictable platoon arrival times. MARL DQN achieves significant improvements over Baseline (-34.82% travel time), but RL agents explore decentralized actions that occasionally disrupt continuous green waves to prevent side-street starvation."* |
| **"Why did MARL PPO not show travel-time superiority over Baseline?"** | *"MARL PPO learned a highly risk-averse policy. In our multi-objective reward formulation, queue penalties and anti-starvation preemption frequently force phase switches to clear Madiwala side-street queues. This prevents local deadlocks but reduces arterial progression speed (-11.71%). We truthfully report that PPO's 1.31% travel time improvement was not statistically significant (p = 0.40)."* |
| **"How many vehicles were simulated?"** | *"Exactly 378 vehicles are generated per 900-second simulation run (362 from 31 continuous flows and 1 discrete ambulance, which SUMO discretizes into 378 vehicles). Across our 12-run multi-seed evaluation, this totals 4,536 vehicle-run instances. 109 vehicles traverse the complete arterial corridor, and 269 execute feeder-turn movements."* |
| **"Are the statistical findings significant with only 3 seeds?"** | *"Because each controller was tested on the identical random seeds (1, 2, 3) under identical demand schedules, we conducted paired Student's t-tests (df=2). Coordinated Adaptive (t = -106.41, p = 0.00009) and MARL DQN (t = -56.24, p = 0.00032) are statistically significant at alpha = 0.001. However, we explicitly disclose that 3 seeds represent preliminary proof-of-concept evidence, not universal generalization across all real-world conditions."* |
| **"Does the system use live Bangalore Traffic Police camera feeds?"** | *"No. The network road geometry and lane widths are derived directly from OpenStreetMap data for Silk Board, but the traffic flows are calibrated synthetic schedules modeling realistic Bengaluru traffic heterogeneity across five vehicle classes."* |

---

## 5. Teardown and Cleanup Instructions

When the demonstration is concluded:
1. In the backend terminal, press `CTRL + C` to initiate graceful shutdown.
   - The lifespan shutdown handler terminates active TraCI connections and closes SUMO cleanly.
2. In the frontend terminal, press `CTRL + C` to stop Vite.
3. Confirm that no orphaned SUMO processes remain:
   ```powershell
   Get-Process -Name "*sumo*" -ErrorAction SilentlyContinue
   ```
   *(No output indicates 100% clean process teardown).*
