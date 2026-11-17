# Security, Governance & Municipal Field Deployment Gap Analysis

**Document ID:** HTC-AUDIT-PHASE12-SECURITY  
**Timestamp:** 2026-11-17T13:58:30+05:30  
**Classification:** Enterprise Security Audit, Cyber-Physical Risk Assessment & Deployment Roadmap  
**Target Audience:** Chief Information Security Officers (CISO), Municipal Traffic Engineers & Deployment Architects  

---

## 1. Executive Summary

The **Bengaluru Traffic Intelligence Platform** currently operates as a high-fidelity research and evaluation digital twin. To transition this cyber-physical system (CPS) from an offline simulation environment into live municipal road infrastructure (e.g., Bengaluru Traffic Police ITMS / SCATS field cabinets), strict cybersecurity controls, fail-safe watchdogs, and industrial communications protocols must be deployed.

This report establishes:
1. A rigorous security audit of the existing software stack.
2. An analysis of the cyber-physical attack surface.
3. A formal architectural gap analysis between simulation and field deployment.
4. An actionable deployment roadmap with concrete engineering remediation steps.

---

## 2. Software & Network Security Audit

### 2.1 API Security & Access Control
- **Current Research State:** 
  - FastAPI web services configured with permissive Cross-Origin Resource Sharing (`allow_origins=["*"]`) for local frontend development.
  - REST endpoints (`/api/traffic/control/mode`, `/api/traffic/emergency`) and WebSocket broadcast streams (`/ws/traffic`) operate without authentication tokens.
- **Identified Cyber Risk:** 
  - Unauthorized clients on the local network could inject false emergency preemption commands or alter signal timing modes without administrative authorization.
- **Production Remediation Specification:**
  1. **OAuth2 / JWT Authentication:** Require cryptographically signed JSON Web Tokens (RS256) on all state-mutating endpoints (`POST /api/traffic/*`).
  2. **Role-Based Access Control (RBAC):**
     - `Viewer` (Traffic monitor): Read-only WebSocket telemetry and historical metric export.
     - `Operator` (Traffic engineer): Controller mode switching and plan scheduling.
     - `EmergencyServices` (Police / Fire / Ambulance): Emergency wave preemption trigger with mandatory audit logging.
  3. **Strict CORS Policy:** Restrict allowed origins to whitelisted municipal domain names (e.g., `https://traffic.bengaluru.gov.in`).

### 2.2 Input Validation & Denial-of-Service (DoS) Protection
- **Current State:** 
  - Pydantic v2 schemas (`backend/schemas.py`) strictly validate payload data types and enum constraints (`SimulationMode`, `EmergencyPriorityRequest`).
- **Production Remediation Specification:**
  1. **Rate Limiting:** Implement token-bucket rate limiting via Redis (`slowapi` middleware) restricting clients to $10\text{ requests/second}$ for control endpoints.
  2. **Input Bounding:** Enforce explicit numeric bounds on simulation duration ($10 \le T \le 3600\text{ s}$) and detector polling frequencies.

### 2.3 TraCI Loopback Isolation
- **Current State:** 
  - Eclipse SUMO communicates with Python via an unencrypted loopback TCP socket (`127.0.0.1:<PORT>`).
- **Production Remediation Specification:**
  - In containerized deployments (Docker / Kubernetes), enforce Unix Domain Sockets or isolated network namespaces to prevent port collision and host sniffing.

---

## 3. Cyber-Physical Attack Surface & Hardware Fail-Safes

In municipal intelligent transportation systems, software faults or network intrusions must never cause physical collision hazards.

```
+-----------------------------------------------------------------------------------------+
|                                CYBER-PHYSICAL SAFETY HIERARCHY                          |
+-----------------------------------------------------------------------------------------+
| LEVEL 3: Edge AI & Cloud Orchestration (FastAPI, PyTorch, MAPPO, Double-DQN)           |
|          * Optimization & offset synchronization (Non-safety critical)                  |
+-----------------------------------------------------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
| LEVEL 2: Runtime Deterministic Safety Shield (SignalController Python Module)           |
|          * Enforces min-green (15s), max-green (60s), yellow clearance (4s/6s)          |
|          * Overrides unsafe AI commands deterministically                               |
+-----------------------------------------------------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
| LEVEL 1: Hardware Conflict Monitor Unit (CMU) / Malfunction Management Unit (MMU)       |
|          * Physical electrical interlocking inside NEMA TS2 / ATC 2070 Traffic Cabinet   |
|          * Hard-wired green-conflict interlocks (Simultaneous conflicting green IMPOSSIBLE)|
|          * Hardware Watchdog: Reverts to Flashing Red / Yellow on IPC heartbeat loss   |
+-----------------------------------------------------------------------------------------+
```

### 3.1 Hardware Conflict Monitor Unit (CMU / MMU) Interlock
In physical traffic signal cabinets (NEMA TS2 Type 1 or Advanced Transportation Controller ATC 2070), physical green-green conflicts are prevented by hardware relays. If the AI software issues a conflicting phase command, the physical MMU immediately disconnects controller outputs and drops the intersection into fail-safe **Flashing Red / Yellow** mode.

### 3.2 Heartbeat Failover Watchdog
To guard against software crashes, operating system freezes, or network dropouts:
- The edge AI industrial PC must transmit a cryptographic heartbeat pulse (every $500\text{ ms}$) to the local signal cabinet controller.
- If the heartbeat lapses for $> 2.0\text{ s}$, the signal cabinet automatically falls back to local pre-timed coordination (Fixed-Time baseline).

---

## 4. Physical Field Deployment Gap Analysis

Transitioning from the calibrated SUMO microscopic simulation to physical municipal intersections requires bridging five engineering gaps:

| Functional Domain | Simulation Environment (Current) | Physical Municipal Deployment (Target) | Required Engineering Transition |
| :--- | :--- | :--- | :--- |
| **Traffic Sensing** | Perfect SUMO simulated induction loops & edge detectors | Thermal cameras, Radar detectors, CCTV AI computer vision (YOLOv8/v10) | Deploy edge vision inferencing on road gantries; map bounding box vehicle counts to edge approach queues. |
| **Actuation Protocol** | Python TraCI loopback TCP API (`traci.trafficlight.setPhase`) | NTCIP 1202 / NEMA TS2 standard over RS-485 / Ethernet | Implement an NTCIP 1202 protocol bridge translating high-level phase actions (`KEEP`, `SWITCH`, `EXTEND`) to ASC/3 or Econolite signal controller commands. |
| **Compute Hardware** | Local workstation / server running Python 3.13 | Ruggedized Industrial IPC (e.g., NVIDIA Jetson AGX Orin / Advantech fanless PC) | Package AI inference engine into lightweight TensorRT / ONNX models rated for $-40^\circ\text{C}$ to $+75^\circ\text{C}$ operation. |
| **Transit / Emergency** | Injected simulated SUMO vehicle tags (`vType="emergency"`) | DSRC / C-V2X (Cellular Vehicle-to-Everything) or GPS/4G AVL transponders | Integrate municipal Computer-Aided Dispatch (CAD) and BMTC bus AVL feeds via standard GTFS-Realtime protocol. |
| **Environmental Telemetry** | European HBEFA 4.2 emission factor lookup tables | IoT air quality sensors (PM2.5, PM10, $\text{NO}_2, \text{CO}$) | Calibrate simulated emissions against real-time roadside environmental sensor arrays. |

---

## 5. Municipal Deployment Phasing Roadmap

```
+----------------------------------------------------------------------------------------------------+
|                                    4-PHASE MUNICIPAL DEPLOYMENT                                    |
+----------------------------------+----------------------------------+------------------------------+
| PHASE A: Shadow Mode (Months 1-3)| PHASE B: Off-Peak Actuation (M4)| PHASE C: Corridor Closed Loop|
| - Install camera/radar detectors | - Active control during off-peak| - Full daytime corridor coord|
| - Ingest real-world traffic data | - Human operator on standby      | - Emergency wave preemption  |
| - Run AI in shadow mode (no act) | - Fail-safe watchdog active      | - Real-time digital twin UI  |
+----------------------------------+----------------------------------+------------------------------+
                                   | PHASE D: City-Scale Expansion    |
                                   | - Scale to Outer Ring Road (ORR) |
                                   | - Integrate with BMTC transit TSP|
                                   | - Enterprise cloud telemetry     |
                                   +----------------------------------+
```

### Phase A: Shadow Deployment & Perception Calibration (Months 1–3)
- Deploy AI inference computers in traffic cabinets along Hosur Road in **Shadow Mode**.
- Ingest real camera and radar vehicle feeds without driving physical signal lamps.
- Compare AI proposed decisions against existing field controllers to validate queue estimation accuracy and response latency.

### Phase B: Supervised Off-Peak Testing (Month 4)
- Enable active actuation during off-peak hours (e.g., 22:00–05:00).
- Station traffic police engineers at each cabinet with manual override switches.
- Verify that physical transitions, yellow clearance, and pedestrian crossing intervals match legal mandates.

### Phase C: Full Daytime Corridor Coordination (Months 5–6)
- Activate Coordinated Adaptive and Dueling Double-DQN control during morning and evening peak hours along Madiwala, Silk Board, and Rupena Agrahara.
- Connect emergency vehicle CAD dispatch to enable live ambulance green-wave preemption.
- Stream corridor telemetry to the Traffic Management Centre (TMC) 3D digital twin.

### Phase D: Basin-Wide Scaling (Months 7+)
- Expand the network from 3 corridor junctions to the entire 213-junction South Bengaluru basin.
- Integrate active BMTC bus fleet priority via GTFS-Realtime feeds.
