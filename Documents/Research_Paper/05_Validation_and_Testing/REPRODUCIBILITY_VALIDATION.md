# Reproducibility Validation Protocol

### Protocol to Reproduce Main Benchmark:
1. Ensure Python 3.11+ and Eclipse SUMO v1.26.0 are installed.
2. Run validation script:
   ```bash
   python scripts/run_10seed_validation.py --duration 900
   ```
3. Recompute statistical tests:
   ```bash
   python scratch/analyze_raw_runs_all.py
   ```
4. Check output consistency against `outputs/validation/10seeds/statistical_analysis.json`.
