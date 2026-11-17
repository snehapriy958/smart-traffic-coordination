# Data Provenance & Reproducibility Traceability

All experimental claims originate from primary, unedited execution artifacts:
1. **Raw Log Location**: `outputs/validation/10seeds/runs/*.json`
2. **Master Summary File**: `outputs/validation/10seeds/eval_10seeds_summary.json`
3. **Statistical Database**: `outputs/validation/10seeds/statistical_analysis.json`
4. **Independent Python Verification Script**: `scratch/analyze_raw_runs_all.py`
5. **Checksum & Immutability**: All 40 raw runs were generated during Phase 4 validation and preserved without alteration. Zero runs have been deleted or overwritten.
