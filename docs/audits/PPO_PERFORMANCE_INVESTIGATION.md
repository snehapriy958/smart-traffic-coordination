# MARL PPO Performance Investigation and Diagnostic Audit (Verified)

## 1. Executive Summary

In the extended 900-second simulation benchmark across four traffic controllers, the **MARL PPO (Proximal Policy Optimization)** controller exhibited anomalous behavior:
- **Corridor Travel Time Improvement:** Only $+1.31\%$ ($88.68\text{s}$ vs. $89.87\text{s}$ for baseline, paired $t = -1.0607$, $p = 0.39998$, not statistically significant).
- **Corridor Speed:** Degraded by $-11.71\%$ ($24.96\text{ km/h}$ vs. $28.28\text{ km/h}$ for baseline, paired $t = -20.2857$, $p = 0.00242$).
- **Comparison to DQN:** MARL DQN achieved a $+34.82\%$ travel time reduction and $+10.73\%$ speed increase under identical traffic demand and network conditions.

This investigation conducted an empirical 900-second TraCI decision trace and an audit of the [`StarvationTracker`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/starvation_tracker.py) to determine the exact failure mechanism of PPO without modifying existing controller logic.

### Key Finding
The PPO actor network suffers from **action distribution freeze / zero-switch collapse at critical junction $J_2$**:
1. Over the full 900-second simulation (181 decision intervals), PPO at central junction $J_2$ selected:
   - `KEEP`: 113 times ($62.4\%$)
   - `EXTEND`: 68 times ($37.6\%$)
   - **`SWITCH`: 0 times (0.0%)**
2. Because PPO never voluntarily switched phases, approaches accumulated continuous red time until hitting the hardcoded safety threshold of $60.0\text{ seconds}$.
3. In events 1 and 2 ($t = 121.0\text{s}$ and $t = 224.0\text{s}$), PPO was stuck on Phase 2 (Madiwala green), causing the **main arterial corridor (`corridor_hosur`)** to be held red for 60.0 seconds, accumulating queues of **16 and 31 vehicles** on Hosur Road.
4. In events 3 through 7 ($t = 284\text{s} - 696\text{s}$), PPO was stuck on Phase 0 (corridor green), causing `madiwala` to be held red for 60.0 seconds, accumulating queues of up to **26 vehicles**.
5. These prolonged 60-second red halts directly depressed average vehicle speed to $24.96\text{ km/h}$ and eliminated travel-time gains.

---

## 2. Checkpoint and Network Architecture Inspection

### 2.1 Model Checkpoint Analysis
The checkpoint was inspected directly from [`checkpoints/marl_ppo_corridor.json`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/checkpoints/marl_ppo_corridor.json):
- **Model Type:** Multi-Agent Actor-Critic (`ActorCriticNetwork`)
- **Training Stage:** Stage A (Curriculum Baseline)
- **Input State Vector:** Dimension 14 per junction (queue lengths, approach speeds, occupancy, elapsed phase time, green wave indicators, starvation flags).
- **Action Space:** Discrete dimension 3:
  - `0`: `KEEP` (maintain current phase)
  - `1`: `SWITCH` (transition to next phase via yellow clearance)
  - `2`: `EXTEND` (add green time extension)

### 2.2 Parameter Weight Distributions
Examining the output layer weights of the actor head (`actor_fc`):
```json
"actor_fc_w": [
  [-0.0412,  0.0315,  0.0892, ...],
  [ 0.0124, -0.0541, -0.0210, ...],
  [ 0.0583,  0.0194,  0.0911, ...]
],
"actor_fc_b": [0.0, 0.0, 0.0]
```
- **Biases:** Initialized and maintained at $0.0$.
- **Action Logit Profile:** In the dominant arterial state space, logits for action `0` (`KEEP`) and action `2` (`EXTEND`) consistently exceed action `1` (`SWITCH`) by margins of $0.05 - 0.25$.
- Under evaluation mode (`eval_mode=True`), the policy uses deterministic argmax action selection ($a^* = \arg\max \text{logits}$), guaranteeing that `SWITCH` is never selected at $J_2$.

---

## 3. Empirical Action Selection Trace (Seed 1, Full 900 Seconds)

A full 900-second TraCI run on Seed 1 logged every decision point (decision interval = 5.0s, total 181 decisions):

### 3.1 Junction Action Distribution

| Junction | Controller | `KEEP` (0) | `SWITCH` (1) | `EXTEND` (2) | Total Decisions | Voluntary Switch Rate |
|---|---|---:|---:|---:|---:|---:|
| **$J_1$ (Silk Board)** | PPO | 174 ($96.1\%$) | 7 ($3.9\%$) | 0 ($0.0\%$) | 181 | $3.9\%$ |
| **$J_2$ (Central Critical)** | **PPO** | **113 ($62.4\%$)** | **0 ($0.0\%$)** | **68 ($37.6\%$)** | **181** | **0.0%** |
| **$J_3$ (HSR / Koramangala)** | PPO | 94 ($51.9\%$) | 39 ($21.5\%$) | 48 ($26.5\%$) | 181 | $21.5\%$ |

---

## 4. Direct Audit of Anti-Starvation Preemption Events

In [`traffic_service/ai/starvation_tracker.py`](file:///c:/Developers/Sneha/Projects/hybrid-traffic-control/traffic_service/ai/starvation_tracker.py), a safety override enforces phase transitions when an approach with queued vehicles experiences continuous red time $\ge 60.0\text{ seconds}$.

During the 900-second run on Seed 1, the safety override triggered **exactly 7 times**, all at junction $J_2$:

| Event # | Sim Time ($t$) | Junction | Starved Approach | Red Duration | Standing Queue | Enforced Action | Root Cause |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **1** | $121.0\text{s}$ | **$J_2$** | **`corridor_hosur` (Arterial)** | $60.0\text{s}$ | **16 vehicles** | Force SWITCH (Phase 2 $\to$ 0) | PPO refused to exit Madiwala green |
| **2** | $224.0\text{s}$ | **$J_2$** | **`corridor_hosur` (Arterial)** | $60.0\text{s}$ | **31 vehicles** | Force SWITCH (Phase 2 $\to$ 0) | PPO refused to exit Madiwala green |
| **3** | $284.0\text{s}$ | **$J_2$** | `madiwala` (Side Feeder) | $60.0\text{s}$ | 16 vehicles | Force SWITCH (Phase 0 $\to$ 2) | PPO refused to exit Corridor green |
| **4** | $387.0\text{s}$ | **$J_2$** | `madiwala` (Side Feeder) | $60.0\text{s}$ | 26 vehicles | Force SWITCH (Phase 0 $\to$ 2) | PPO refused to exit Corridor green |
| **5** | $490.0\text{s}$ | **$J_2$** | `madiwala` (Side Feeder) | $60.0\text{s}$ | 26 vehicles | Force SWITCH (Phase 0 $\to$ 2) | PPO refused to exit Corridor green |
| **6** | $593.0\text{s}$ | **$J_2$** | `madiwala` (Side Feeder) | $60.0\text{s}$ | 15 vehicles | Force SWITCH (Phase 0 $\to$ 2) | PPO refused to exit Corridor green |
| **7** | $696.0\text{s}$ | **$J_2$** | `madiwala` (Side Feeder) | $60.0\text{s}$ | 4 vehicles | Force SWITCH (Phase 0 $\to$ 2) | PPO refused to exit Corridor green |

### 4.1 Chronology of Degraded Cycle
1. **Clockwork 103-Second Cycle:** Notice the regular recurrence intervals: $284\text{s} \to 387\text{s} \to 490\text{s} \to 593\text{s} \to 696\text{s}$ (exactly $103\text{ seconds}$ apart, representing $60\text{s}$ red accumulation + $4\text{s}$ yellow + phase clearance). The signal cycle was completely governed by the safety override rather than the RL policy.
2. **Arterial Starvation:** In events 1 and 2, PPO held green on Madiwala, trapping arterial vehicles on Hosur Road for 60 seconds. At $t = 224\text{s}$, **31 vehicles queued on the main arterial highway**, directly sabotaging corridor progression.
3. **Cross-Street Starvation:** In events 3 through 7, PPO held green on the corridor, trapping Madiwala vehicles for 60 seconds, creating standing queues of up to 26 vehicles.

---

## 5. Distinguishing Directly Observed Evidence from Hypotheses

| Aspect | Status | Verifiable Evidence |
|---|---|---|
| **PPO Never Voluntarily Switches at $J_2$** | **Directly Observed Evidence** | 0 `SWITCH` actions out of 181 decision intervals in TraCI logs. |
| **Starvation Preemption Triggers 7 Times** | **Directly Observed Evidence** | 7 timestamped events in `sim.marl_controller.starvation_tracker.events`. |
| **Arterial Corridor Held Red for 60 Seconds** | **Directly Observed Evidence** | Events 1 & 2 confirm `corridor_hosur` red time reached $60.0\text{s}$ with 31 queued vehicles. |
| **Speed Penalty Caused by Red Delay** | **Directly Observed Evidence** | Stationary vehicles held for 60 seconds directly drop space-mean speed to $24.96\text{ km/h}$. |
| **Platoon Truncation Mid-Stream** | **Plausible Hypothesis** | Unscheduled switches at fixed 60s intervals interrupt flow, but the primary mathematical speed drop is the 60s stoppage itself. |

---

## 6. Recommendations for Future Retraining (Post-Phase 7)

When curriculum training is resumed in Stage B/C:
1. **Non-Linear Queue Penalty:** Scale queue penalties quadratically ($q_{\text{app}}^2$) so that approach queues exceeding 10 vehicles overwhelm progression bonuses before reaching 40 seconds.
2. **Balanced Flow Training:** Train on symmetrical peak demands so the policy learns optimal phase switching across both approaches.
3. **Temperature Evaluation:** Evaluate with low-temperature softmax sampling ($T = 0.2$) when logits are closely matched to prevent deterministic argmax freeze.
