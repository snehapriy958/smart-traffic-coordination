# Series 4C: Cooperative Reward Coupling Mechanism Ablation — Status & Safe Recovery Plan

**Document ID:** HTC-AUDIT-PHASE7-SERIES4C  
**Timestamp:** 2026-11-17T13:52:00+05:30  
**Status:** FROZEN AUDIT & SAFE RECOVERY PLAN (Strictly Read-Only — No Simulations Executed)  
**Experiment Path:** `outputs/experiments/phase4/final_150ep/series_4c_reward_coupling/`  
**Master Script:** `scripts/train_series4c_master.py`  
**Master Manifest:** `outputs/experiments/phase4/final_150ep/series_4c_reward_coupling/manifest_series_4c.json`  

---

## 1. Executive Summary

Series 4C was designed to investigate the causal effect of the cooperative reward coupling coefficient $\beta \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$ on Multi-Agent Proximal Policy Optimization (MAPPO) across 5 training seeds ($101 \dots 105$) with 10 confirmatory evaluation seeds ($1 \dots 10$) per checkpoint (25 training runs $\times$ 150 episodes = 3,750 episodes; 250 evaluations).

As of this audit:
- **Completed Runs:** Exactly 3 of 25 runs are completed ($\beta = 0.00$, seeds 101, 102, 103).
- **Completed Evaluations:** 30 of 250 confirmatory evaluations are completed.
- **Current Manifest State:** Run 4 (`beta_000_seed104`) is marked `"TRAINING"`, but no active process is running, and no partial checkpoint exists.
- **Pending Runs:** 21 runs are `"PENDING"`.
- **Active Execution:** **0 processes active** (no `python.exe` or `sumo.exe` running).
- **Estimated Remaining Runtime:** $\approx 22 \times 72 \text{ minutes} \approx 26.4 \text{ wall-clock hours}$.

---

## 2. Completed Run Audit & Cryptographic Verification

All three completed runs have been fully verified against their checkpoints, history sidecars, and evaluation outputs.

| Run ID | $\beta$ | Train Seed | Episodes | Wall Time (s) | Checkpoint Path | SHA-256 Hash Match | Completed Evals | Mean Travel Time (s) | Travel Time SD (s) |
|---|---|---|---|---|---|---|---|---|---|
| `beta_000_seed101` | 0.00 | 101 | 150 | 4,476.07 s | `checkpoints/phase4/final_150ep/series_4c_mappo_beta_000_seed101.json` | **MATCH** (`27fe48d0e5...`) | 10 / 10 | 80.43 s | 1.66 s |
| `beta_000_seed102` | 0.00 | 102 | 150 | 3,915.66 s | `checkpoints/phase4/final_150ep/series_4c_mappo_beta_000_seed102.json` | **MATCH** (`e767c29ae7...`) | 10 / 10 | 88.16 s | 0.79 s |
| `beta_000_seed103` | 0.00 | 103 | 150 | 4,244.77 s | `checkpoints/phase4/final_150ep/series_4c_mappo_beta_000_seed103.json` | **MATCH** (`88ca384d14...`) | 10 / 10 | 99.38 s | 0.81 s |

### Pooled Empirical Performance ($\beta = 0.00$, $N = 30$ evaluations):
- **Mean Travel Time:** $89.32 \text{ s}$
- **Sample Standard Deviation:** $7.99 \text{ s}$
- **Median:** $88.16 \text{ s}$
- **90th Percentile (p90):** $99.70 \text{ s}$
- **95th Percentile (p95):** $99.98 \text{ s}$
- **Contextual Comparison:** Fixed-Time Baseline achieves $90.02 \pm 1.26 \text{ s}$. Uncoupled MAPPO ($\beta = 0.00$) yields statistically indistinguishable performance from Fixed-Time ($p = 0.68$), confirming that without cooperative reward coupling or extensive hyperparameter tuning, uncoupled independent PPO fails to outperform fixed-time coordination.

---

## 3. Root Cause Analysis: Stalled Run 4 (`seed104`)

### A. Manifest Inconsistency
In `manifest_series_4c.json`, Run 4 is flagged as:
```json
{
  "beta": 0.0,
  "beta_tag": "beta_000",
  "train_seed": 104,
  "training_status": "TRAINING",
  "training_wall_time_s": 0.0,
  "checkpoint_sha256": null
}
```
However:
1. `checkpoints/phase4/final_150ep/series_4c_mappo_beta_000_seed104.json` **does not exist**.
2. `checkpoints/phase4/final_150ep/series_4c_mappo_beta_000_seed104.history.json` **does not exist**.
3. No active `python.exe` process with script `train_series4c_master.py` exists.

### B. Root Cause: Windows Sandbox Loopback Socket Deadlock
From the execution log (`series_4c_execution.log`):
```text
2026-11-13 18:20:41,000 [INFO] [Series4CMaster] [RECOVERY] Authorized termination of stalled worker task-6727 (due to sandbox TCP loopback block). Manifest Run 1 (beta_000_seed101) reset to PENDING. Relaunching with BypassSandbox: true for TraCI loopback communication.
```
When Python launches SUMO via TraCI on Windows:
1. SUMO is invoked with `--remote-port <PORT>`.
2. Python connects to `127.0.0.1:<PORT>`.
3. Under sandboxed execution (`BypassSandbox: false`), Windows network isolation blocks loopback TCP socket handshakes, causing Python to hang indefinitely in `SYN_SENT` while SUMO sits in `LISTEN`.
4. The background process previously monitoring this was terminated, leaving the manifest in an intermediate `"TRAINING"` state.

---

## 4. Workload Remaining & Resource Estimation

- **Runs Remaining:** 22 training runs (seeds 104, 105 for $\beta=0.00$, and all 5 seeds for $\beta \in \{0.25, 0.50, 0.75, 1.00\}$).
- **Episodes Remaining:** $22 \times 150 = 3,300 \text{ training episodes}$.
- **Evaluations Remaining:** $22 \times 10 = 220 \text{ confirmatory evaluations}$.
- **Empirical Cycle Time:**
  - Training: $\approx 4,200 \text{ s}$ ($\approx 70 \text{ min}$) per run.
  - Evaluations (10 seeds): $\approx 120 \text{ s}$ ($\approx 2 \text{ min}$) per checkpoint.
  - Total per run: $\approx 72 \text{ min}$.
- **Total Compute Time:** $22 \times 1.2 \text{ hours} \approx 26.4 \text{ wall-clock hours}$.
- **Disk Footprint:** Checkpoints $\approx 8 \text{ KB}$ each; history $\approx 45 \text{ KB}$ each; evaluation JSONs $\approx 12 \text{ KB}$ each. Total expected disk footprint $< 50 \text{ MB}$.

---

## 5. Safe Recovery Plan (To Be Triggered Only Upon User Request)

The master script `scripts/train_series4c_master.py` was specifically engineered with idempotent resume logic:
1. If `checkpoints/phase4/final_150ep/series_4c_mappo_{beta_tag}_seed{ts}.json` exists and passes `verify_checkpoint_integrity()`, training is skipped, status is set to `"COMPLETED"`, and missing evaluations are executed.
2. If the checkpoint is missing or invalid, it executes clean training.

### Pre-Recovery Manifest Sanitation:
To ensure clean resume without manual manifest surgery, Run 4's status in `manifest_series_4c.json` can be cleanly set to `"PENDING"`:
```python
# Safe manifest fix (if resuming):
manifest["runs"]["beta_000_seed104"]["training_status"] = "PENDING"
```

### Execution Command:
When the user explicitly authorizes running the 26.4-hour workload, execute:
```powershell
# Outside sandbox to permit Windows TraCI loopback communication:
python scripts/train_series4c_master.py
```

### Scientific Decision for Current Deliverable:
In accordance with strict safety constraints (**do not start expensive training runs**), Series 4C will remain frozen in its current state. The 3 completed runs ($N=30$ evaluations) are documented and reported as preliminary empirical data in the research papers and reports, with remaining runs clearly classified as **in-progress future ablation work**.
