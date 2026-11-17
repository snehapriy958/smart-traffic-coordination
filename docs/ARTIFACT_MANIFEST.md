# Experiment Artifact Manifest and Storage Policy

**Project:** Smart Traffic Coordination System — Bengaluru Silk Board Corridor  
**Date:** 2026-11-09T15:53:00+05:30  
**Repository Branch:** `marl-p6-2-curriculum-training` (Commit: `0fa845e`)

---

## 1. Artifact Classification & Storage Policy

Every artifact generated or utilized in the project is classified into one of five categories:

| Category | Description | Storage Strategy | Version Control Recommendation |
|:---|:---|:---|:---|
| **Category A: Source Code** | Executable scripts, backend routes, AI models, simulator orchestration | Direct Git Tracking | Commit directly to repository |
| **Category B: Small Summaries** | Aggregated benchmark datasets, statistical test outputs, summary JSONs | Direct Git Tracking | Commit directly to repository |
| **Category C: Raw Datasets** | 40 per-run microscopic execution logs ($< 3\text{ KB}$ each) | Local Archive / Git Tracking | Commit to repository (Total size $< 270\text{ KB}$) |
| **Category D: Checkpoints** | Trained PyTorch neural network weight dictionaries (~$1\text{ MB}$ each) | Direct Git / Git LFS | Tracked in Git repository (`checkpoints/`) |
| **Category E: Temporary Files** | Browser profiles, pytest caches, compile artifacts | Exclude via `.gitignore` | Strictly excluded from version control |

---

## 2. Definitive Inventory of Experimental Artifacts

### Category A: Source Code & Validation Scripts
| Artifact Path | Size | SHA-256 Checksum | Purpose / Description | Storage Status |
|:---|---:|:---|:---|:---:|
| `scripts/run_10seed_validation.py` | 20,340 B | `d1e50f10f94af2da90e96de381cf13eca724f994b0745349a55ceeb90a75e3b9` | Autonomous 40-run 10-seed simulation runner with TraCI process isolation and statistical test engine | **Track in Git** |
| `traffic_service/ai/marl_controller.py` | 18,720 B | `ceba80a563914a27546859846b86e08beff9179d67568102d1d4ca6b86375037` | Multi-agent coordination controller for DQN and PPO signal actuation | **Track in Git** |
| `traffic_service/ai/starvation_tracker.py` | 9,845 B | `11181216b23d9b4b0e879a957816c27771ec8e3e4a2d8544c8024a1b026601ea` | Deterministic anti-starvation safety tracker enforcing 60s max-red threshold | **Track in Git** |

### Category B: Small Experimental Summaries & Statistics
| Artifact Path | Size | SHA-256 Checksum | Purpose / Description | Storage Status |
|:---|---:|:---|:---|:---:|
| `outputs/validation/historical_3seeds/extended_eval_results.json` | 27,086 B | `e5881662d2370122b5cfd42bb80e1a9a4eb53d6dc5f9de680bb1437708fd8ad8` | Preserved Phase 5/6 historical 3-seed benchmark results (12 runs total) | **Track in Git** |
| `outputs/validation/10seeds/eval_10seeds_summary.json` | 142,225 B | `80b6828528bb807fbfa106bc5f6bed5bb7e453db62068b435d2293192e71e5b2` | Comprehensive 10-seed master dataset covering 40 runs across Peak, Shoulder, Off-Peak | **Track in Git** |
| `outputs/validation/10seeds/statistical_analysis.json` | 21,312 B | `dfad814689ce9955618941506423d9f9daa2518c3ea8205c55d522388f9cc168` | Full inferential statistics: paired t-tests, $p$-values, 95% CIs, Wilcoxon $W$, Cohen's $d_z$ | **Track in Git** |

### Category C: Raw 10-Seed Simulation Run Records (`outputs/validation/10seeds/runs/`)
Total Files: **40 JSON files** | Total Size: **$102,488\text{ bytes}$ ($\approx 100.1\text{ KB}$)** | Storage: **Track in Git** (All 40 files are lightweight structured JSON summaries of each 900s run):

- `run_baseline_seed1.json` through `run_baseline_seed10.json` (10 runs, ~2.5 KB each)
- `run_coordinated_seed1.json` through `run_coordinated_seed10.json` (10 runs, ~2.5 KB each)
- `run_marl_dqn_seed1.json` through `run_marl_dqn_seed10.json` (10 runs, ~2.5 KB each)
- `run_marl_ppo_seed1.json` through `run_marl_ppo_seed10.json` (10 runs, ~2.5 KB each)

### Category D: Primary Model Checkpoints (`checkpoints/`)
All model checkpoints are already tracked in the repository. The primary production models are:

| Checkpoint Path | Size | SHA-256 Checksum | Controller | Architecture |
|:---|---:|:---|:---|:---|
| `checkpoints/marl_dqn_corridor.json` | 982,917 B | `befe2767162bec95bce97a6859a52b85a79d4d850c9c34f956f1cf83684922b1` | MARL Double-DQN | Dueling Double-DQN ($J_1, J_2, J_3$) |
| `checkpoints/marl_ppo_corridor.json` | 982,905 B | `3f60909e5fb9a434112f3cb0a5540a4db7ec22a67bdba98ae5ff1c4a0733e0ef` | MARL Actor-Critic PPO | Discrete Actor-Critic ($J_1, J_2, J_3$) |

### Category E: Temporary and Generated Files (Excluded via `.gitignore`)
- `outputs/temp_chrome_profile/` (Generated during headless browser screenshots)
- `frontend/dist/` (Production Vite build output)
- `frontend/node_modules/` (Node package dependencies)
- `__pycache__/`, `*.pyc`, `.pytest_cache/` (Python compilation and test caches)
- `*.db`, `*.sqlite3` (SQLite local run databases)

---

## 3. Git LFS Evaluation

- **Git LFS Availability:** Git LFS version `git-lfs/3.7.1` is installed on the host operating system.
- **Assessment:**  
  The newly generated validation artifacts (`outputs/validation/10seeds/` and `outputs/validation/historical_3seeds/`) total **$293\text{ KB}$ combined across all 43 files**.  
  Because the total storage footprint is well under 1 MB, configuring Git LFS for these JSON files is unnecessary and would introduce redundant third-party pointer dependencies. Standard Git tracking provides full cryptographic tracking and zero-overhead portability.

---
**Manifest Approved by:** Antigravity Senior Engineering & Verification Auditor
