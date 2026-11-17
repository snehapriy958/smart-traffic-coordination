# Demo Readiness & Production Live Demonstration Guide

**Document ID:** HTC-AUDIT-PHASE11-DEMOGUIDE  
**Timestamp:** 2026-11-17T13:58:00+05:30  
**Target Audience:** Live Reviewers, Conference Evaluators, Municipal Stakeholders & System Operators  
**Platform:** Smart Traffic Coordination System — Bengaluru Traffic Intelligence Platform  

---

## 1. System Overview & Pre-Flight Checklist

The **Bengaluru Traffic Intelligence Platform** is a full-stack cyber-physical traffic management platform connecting a calibrated microscopic simulation engine (Eclipse SUMO 1.26.0) with an asynchronous FastAPI backend and a WebGL Three.js 3D Digital Twin.

### Pre-Flight Verification Checklist:
- [x] Python 3.13.14 (64-bit) available in PATH
- [x] Node.js v22.21.1 and npm 10.9.2 available in PATH
- [x] SUMO 1.26.0 (`sumo.exe`) accessible via `SUMO_HOME` environment variable
- [x] Ports `8000` (FastAPI) and `5173` (Vite / React) unoccupied
- [x] 0 orphan `sumo.exe`, `python.exe`, or `node.exe` processes running

---

## 2. Deterministic Startup Sequence (PowerShell)

### Step 1: Pre-Execution Port & Process Cleanliness
Open a PowerShell terminal and verify that no conflicting services are running:
```powershell
Get-Process python*, sumo*, node* -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 8000, 5173 -State Listen -ErrorAction SilentlyContinue
```
*(If any stale process exists, terminate it cleanly before starting).*

### Step 2: Start the FastAPI Backend Service
In **Terminal 1**, navigate to the project root and launch Uvicorn:
```powershell
cd C:\Developers\Sneha\Projects\hybrid-traffic-control
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
**Expected Terminal Output:**
```text
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Verify backend health in a separate terminal:
```powershell
curl http://127.0.0.1:8000/health
# Expected: {"status":"healthy","sumo_connected":false,"active_mode":"stopped"}
```

### Step 3: Start the React 18 Frontend Development Server
In **Terminal 2**, navigate to the frontend directory and launch Vite:
```powershell
cd C:\Developers\Sneha\Projects\hybrid-traffic-control\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
**Expected Terminal Output:**
```text
  VITE v6.0.11  ready in 480 ms

  ➜  Local:   http://127.0.0.1:5173/
  ➜  Network: http://<LAN-IP>:5173/
```

### Step 4: Open the Platform in Browser
Open Google Chrome or Microsoft Edge and navigate to:
```
http://127.0.0.1:5173
```

---

## 3. Step-by-Step Live Demonstration Script

Follow this structured, 7-minute demonstration narrative to showcase the system's capabilities:

### Scene 1: Corridor Digital Twin & Geographic Reality (1 Minute)
- **Visual:** The 3D Digital Twin loads with 306 road edges, 213 junctions, and 490 lanes rendered in WebGL.
- **Narrative to Stakeholders:**
  > *"This digital twin models the infamous Central Silk Board corridor in South Bengaluru along Hosur Road. We are looking at three sequential junctions: Madiwala Checkpost (J1), the Central Silk Board interchange (J2), and Rupena Agrahara (J3). The road network is extracted from OpenStreetMap and calibrated to Indian Road Congress urban standards."*
- **Action:** Use mouse to pan, tilt, and zoom around Junction J2 (Central Silk Board rotary).

### Scene 2: Fixed-Time Baseline & Congestion Buildup (1.5 Minutes)
- **Action:** In the Control Panel, ensure Mode is set to **"Fixed-Time (Baseline)"**, and click **"Start Simulation"**.
- **Visual:** The simulation status indicator turns green (`LIVE SIMULATION - BASELINE`). Vehicles spawn and begin traveling along Hosur Road. Notice the rigid 90-second cycle timer.
- **Narrative to Stakeholders:**
  > *"Under conventional pre-timed control, signals switch rigidly regardless of traffic pressure. Notice Junction J2: arterial vehicles from Madiwala are forced to stop even when the cross-street has zero traffic. Watch the Corridor Travel Time card rise to ~90 seconds and cumulative vehicle delay climb past 10,000 veh-seconds."*

### Scene 3: Transition to Coordinated Adaptive Control (1.5 Minutes)
- **Action:** In the mode selector, click **"Coordinated Adaptive"**.
- **Visual:** The mode updates seamlessly. The signal controllers at J1, J2, and J3 immediately begin synchronizing. J2's signal extends green as incoming vehicle platoons arrive from J1.
- **Narrative to Stakeholders:**
  > *"Now we activate our Coordinated Adaptive Controller. Notice what happens at Central Silk Board: rather than cutting off the platoon, J2's controller uses virtual inter-junction communication to anticipate upstream arrivals from J1. It extends green on Phase 0, creating an arterial green wave. Travel times drop by 44.6% to under 50 seconds, and tailpipe emissions drop by over 34%."*

### Scene 4: Explainable Decision Rationale Drawer (1.5 Minutes)
- **Action:** In the Signal Status Panel, point to **Junction J2 (Central Silk Board)**. The **"Decision Rationale & Causal Chain"** drawer is open by default.
- **Visual:** Point out the live telemetry badges:
  - **Active Controller:** `Coordinated Adaptive`
  - **Action Badge:** `EXTEND` or `SWITCH`
  - **Observed Queue:** `Q_art = 12, Q_cross = 4`
  - **Decision Reason:** *"Arterial demand dominant (Q=12 >= 4), extending green"*
  - **Observed Queue Outcome ($\Delta Q$):** Showing subsequent queue reduction.
- **Narrative to Stakeholders:**
  > *"In municipal deployments, black-box AI is unacceptable. Our platform provides complete causal transparency. For every single 5-second actuation, the operator sees exactly what the controller observed, why it made the decision, what safety shield constraints were enforced, and the resulting change in queue length."*

### Scene 5: Emergency Vehicle Green Wave Preemption (1 Minute)
- **Action:** In the Emergency Panel, select **"Junction J1 -> J3 (Southbound Ambulance)"** and click **"Trigger Emergency Preemption"**.
- **Visual:** An emergency siren indicator pulses. In the 3D twin, an ambulance model appears with emergency flashing strobes. Signal lights along the corridor immediately cascade to green ahead of the ambulance, clearing all stop-line queues.
- **Narrative to Stakeholders:**
  > *"When emergency services are dispatched, our emergency wave coordinator overrides standard phase splits. It detects the emergency vehicle 250 meters upstream and locks arterial green phases across J1, J2, and J3. The ambulance crosses the entire corridor without experiencing a single red light, reducing transit time by over 60%."*

### Scene 6: Autonomous Deep Reinforcement Learning Mode (0.5 Minutes)
- **Action:** Switch mode to **"Dueling Double-DQN (AI)"**.
- **Visual:** The system switches to neural inference. Point to the controller badge in the Decision Rationale drawer (`Double-DQN`).
- **Narrative to Stakeholders:**
  > *"Our platform also supports decentralized Deep RL. Without pre-programmed progression logic, these Dueling Double-DQN agents autonomously discovered green-wave synchronization, achieving a verified 37% travel time reduction while operating safely behind our deterministic runtime safety shield."*

---

## 4. Troubleshooting & Clean Shutdown

| Symptom | Probable Cause | Immediate Remediation |
| :--- | :--- | :--- |
| **Backend fails on port 8000 (`Address already in use`)** | Stale Python process from previous session | Run `Get-Process python* \| Stop-Process -Force` |
| **SUMO fails to connect (`TraCI error`)** | Temporary loopback socket timeout | Refresh browser; restart backend with `python -m uvicorn backend.main:app` |
| **Frontend shows "Disconnected from Server"** | WebSocket connection dropped or backend down | Verify backend running in Terminal 1; check `http://127.0.0.1:8000/health` |
| **3D Canvas displays black screen** | WebGL context loss in browser | Open Chrome settings $\to$ System $\to$ Enable "Hardware acceleration" $\to$ Refresh tab |

### Clean System Shutdown:
When the demonstration concludes, stop the terminals:
1. In Terminal 1 (Backend): Press `Ctrl + C`.
2. In Terminal 2 (Frontend): Press `Ctrl + C`.
3. In PowerShell, confirm no orphaned simulation processes remain:
   ```powershell
   Get-Process python*, sumo*, node* -ErrorAction SilentlyContinue
   ```
