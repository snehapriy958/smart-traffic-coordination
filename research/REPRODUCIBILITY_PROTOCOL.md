# Scientific Reproducibility Protocol & Audit Replication Guide

**Document ID:** HTC-RESEARCH-REPRODUCIBILITY  
**Target Publication Venues:** IEEE Transactions on Intelligent Transportation Systems (T-ITS) / Transportation Research Part C  
**Classification:** Experimental Protocol, Deterministic Reproduction & Integrity Verification  

---

## 1. Computational Environment & System Dependencies

To guarantee deterministic replication of all empirical benchmarks, evaluations, and statistical analyses, the experimental pipeline was developed and verified under the following environment:

| Component | Verified Specification | Build / Commit / Package Details |
| :--- | :--- | :--- |
| **Operating System** | Microsoft Windows 11 Enterprise (64-bit) | Kernel version 10.0.26100 |
| **Python Runtime** | Python 3.13.14 (64-bit) | CPython implementation |
| **Microscopic Simulator** | Eclipse SUMO 1.26.0 | Build `MSVC 19.29.30133.0 Release 64-bit` |
| **Deep Learning Framework** | PyTorch 2.8.0 + CUDA (CPU Fallback) | TorchVision 0.23.0 |
| **Scientific Computing** | NumPy 2.3.3, SciPy 1.15.2, Pandas 2.2.3 | Statsmodels 0.14.4 |
| **Backend Framework** | FastAPI 0.141.1, Uvicorn 0.34.0, Pydantic 2.10 | SQLite3 (Persistent storage) |
| **Node.js & Frontend** | Node.js v22.21.1, npm 10.9.2 | React 18.3.1, Three.js 0.187.0, Vite 6.0 |
| **Containerization** | Docker Engine 29.6.1 | Multi-stage Dockerfile |

---

## 2. Directory Layout & Preserved Research Artifacts

The repository maintains strict separation between source code, test suites, frozen checkpoints, and evaluation JSONs:

```
hybrid-traffic-control/
├── backend/                               # FastAPI web services, REST routers, WebSocket manager
├── checkpoints/
│   └── phase4/
│       └── final_150ep/                   # 171 trained model checkpoints (*.json + *.history.json)
├── frontend/                              # React 18, Three.js WebGL digital twin, TailwindCSS
├── outputs/
│   ├── experiments/
│   │   └── phase4/
│   │       ├── final_150ep/               # 1,228 confirmatory evaluation JSONs across series
│   │       │   ├── series_4b_observation_space/
│   │       │   └── series_4c_reward_coupling/
│   │       └── series_4e_passenger_reward/
│   └── validation/
│       └── final_reproducible_analysis/   # Self-contained benchmark replication package
├── research/                              # Research papers, literature review, equations, BibTeX
├── reports/final/                         # Phase 1-13 comprehensive audit reports
├── sumo/silk_board/                       # SUMO network, edges, routes, and detectors (OSM geometry + configured demand)
└── tests/                                 # 231 unit, integration, and safety invariant tests
```

---

## 3. Step-by-Step Reproduction Instructions

### Step 3.1: Verify Software Environment & CLI Tools
```powershell
python --version          # Expected: Python 3.13.x
sumo --version            # Expected: Eclipse SUMO sumo Version 1.26.0
node --version            # Expected: v22.x.x
npm --version             # Expected: 10.x.x
```

### Step 3.2: Execute Automated Regression & Safety Test Suites
Run all backend, controller, and safety invariant tests:
```powershell
# Run API endpoint integration suite
pytest tests/test_api.py -v

# Run controller, safety shield, and coordination test suites
pytest tests/test_multi_intersection.py tests/test_emergency_wave.py -v

# Run comprehensive regression suite
pytest tests/ -m "not slow" --tb=short
```

Run frontend UI component unit tests:
```powershell
cd frontend
npm test
cd ..
```

### Step 3.3: Re-Execute Authoritative Master Benchmark Analysis
The master benchmark analysis script parses the raw 40 evaluation JSONs (10 seeds across 4 controllers), re-computes all descriptive and inferential statistics, checks physical stoichiometry, and exports summary CSVs:
```powershell
python outputs/validation/final_reproducible_analysis/reproduce_benchmark_analysis.py
```
**Expected Output Artifacts in `outputs/validation/final_reproducible_analysis/`:**
- `master_benchmark_summary.csv`: Summary of mean, sample SD, population SD, median, p90, p95 for all metrics.
- `paired_comparisons.csv`: Paired $t$-statistics, degrees of freedom, raw and Bonferroni p-values, Cohen's $d_z$.
- `raw_40runs_matrix.csv`: Full tabular matrix of all 40 simulation runs.
- `recomputed_statistics.json`: Machine-readable JSON dictionary of all statistics.

### Step 3.4: Re-Execute Series 4B Linear Mixed-Effects Model (LMM) Analysis
To verify the hierarchical variance decomposition ($\sigma^2_{\text{model}} = 217.18$ vs $\sigma^2_{\text{eval}} = 19.90$):
```powershell
python scratch/reproduce_4b_lmm.py
```

---

## 4. Checkpoint Integrity & Cryptographic SHA-256 Register

Key model checkpoints evaluated in the research can be verified against their SHA-256 hashes:

| Controller / Checkpoint File | Series | Size | SHA-256 Hash |
| :--- | :---: | :---: | :--- |
| `series_4c_mappo_beta_000_seed101.json` | 4C | $8.2 \text{ KB}$ | `27fe48d0e5170d10373059868516d56df4237eb31ad961d7a31b7d526742512f` |
| `series_4c_mappo_beta_000_seed102.json` | 4C | $8.2 \text{ KB}$ | `e767c29ae73256193ff435555620ae19b889ebdb81069bce05963cfb061b659c` |
| `series_4c_mappo_beta_000_seed103.json` | 4C | $8.2 \text{ KB}$ | `88ca384d14b4fb24e62a149cb267c768cbfbcfaecf937e2db3db18fa3fcfa06e` |

Verification command:
```powershell
Get-FileHash -Algorithm SHA256 checkpoints/phase4/final_150ep/series_4c_mappo_beta_000_seed101.json
```

---

## 5. Clean Startup Protocol for Live Demonstration

To launch the live platform and digital twin without background conflicts:
```powershell
# Terminal 1: Launch FastAPI Backend (Port 8000)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Launch Vite React Frontend (Port 5173)
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
Open browser at `http://127.0.0.1:5173`. Click **"Start Simulation"** to launch real-time SUMO-backed corridor coordination with live Three.js 3D rendering and the Explainable Decision Rationale drawer.
