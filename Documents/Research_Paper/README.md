# Smart Traffic Coordination System — Research Paper Documentation Workspace
**Corridor**: Central Silk Board Arterial Corridor (Hosur Road J1 -> J2 -> J3), Bengaluru, India  
**Target Paper**: *Smart Traffic Coordination System: A Cyber-Physical Simulation Twin and Benchmarking Study with Runtime Safety Shielding on a Heterogeneous Urban Corridor*  
**Status**: **Supervisor Review Ready (Audit Composite Score: 9.69 / 10)**  
**Workspace Root**: `Documents/Research_Paper/`

---

## 1. Directory Structure & Navigation Guide

```text
Documents/Research_Paper/
├── 00_Project_Overview/              # Project vision, objectives, hypotheses, contributions, architecture
├── 01_Literature_Review/             # 16-paper survey, related work matrix, research gap, verified bib
├── 02_Methodology/                   # System model, network specs, controller designs, math formulas, safety
├── 03_Experimental_Data/             # Dataset specs, master manifest, raw data catalog, fleet split
├── 04_Results_and_Analysis/          # Master benchmark tables, statistical tests, speed & fuel analyses
├── 05_Validation_and_Testing/        # Evidence register, test matrices, controller validation, reproducibility
├── 06_Research_Paper/                # Master manuscript draft and modular section drafts
├── 07_Figures_and_Tables/            # Directory tree for publication vector figures and tables
├── 08_References_and_Citations/      # Verified REFERENCES.bib, citation audit, DOI verification
├── 09_Formatting_and_Submission/     # Target venues (TR-C / IEEE T-ITS), submission checklist, CRediT roles
├── 10_Audit_Reports/                 # Independent audit reports, correction logs, unresolved issues
└── README.md                         # This source-to-destination index and navigation guide
```

---

## 2. Source-to-Destination Index & Authoritative Mapping

| Organized File in `Documents/Research_Paper/` | Source File in Repository | Nature of Content | Authority Level |
| :--- | :--- | :--- | :---: |
| `00_Project_Overview/PROJECT_OVERVIEW.md` | Primary Synthesis | System overview and scope | Level 4 |
| `00_Project_Overview/RESEARCH_OBJECTIVES.md` | Primary Synthesis | 5 core research objectives | Level 4 |
| `00_Project_Overview/RESEARCH_QUESTIONS_AND_HYPOTHESES.md` | Primary Synthesis | 4 RQs and 4 verified Hypotheses | Level 4 |
| `00_Project_Overview/RESEARCH_CONTRIBUTIONS.md` | Primary Synthesis | 5 major scientific contributions | Level 4 |
| `00_Project_Overview/SYSTEM_ARCHITECTURE.md` | Primary Synthesis | Cyber-physical ASCII pipeline | Level 4 |
| `01_Literature_Review/LITERATURE_REVIEW.md` | `research/LITERATURE_REVIEW.md` | 16-paper literature survey | Level 7 |
| `01_Literature_Review/RELATED_WORK_COMPARISON.md` | `research/RELATED_WORK_COMPARISON.csv` | Comparative taxonomical matrix | Level 7 |
| `01_Literature_Review/RESEARCH_GAP_AND_NOVELTY.md` | `research/RESEARCH_GAP_AND_NOVELTY.md` | Explicit research gap statement | Level 7 |
| `01_Literature_Review/REFERENCE_VERIFICATION.md` | CrossRef / DBLP Audit | DOI and metadata verification | Level 5 |
| `01_Literature_Review/REFERENCES.bib` | `research/REFERENCES.bib` | 16 verified BibTeX entries | Level 5 |
| `01_Literature_Review/READING_NOTES/READING_NOTES.md` | Primary Synthesis | Detailed notes on 16 core papers | Level 7 |
| `02_Methodology/RESEARCH_METHODOLOGY.md` | Primary Synthesis | End-to-end experimental workflow | Level 4 |
| `02_Methodology/SYSTEM_MODEL.md` | Primary Synthesis | Graph network & Krauss kinematics | Level 4 |
| `02_Methodology/TRAFFIC_NETWORK_AND_DATASET.md` | Primary Synthesis | 306 edges, 213 junctions, demand | Level 2 |
| `02_Methodology/CONTROLLER_ARCHITECTURE.md` | `traffic_service/` code | 4 controller specifications | Level 4 |
| `02_Methodology/STATE_ACTION_REWARD_FORMULATION.md` | `traffic_service/ai/env.py` | 8D/14D states, 4 actions, reward | Level 4 |
| `02_Methodology/MATHEMATICAL_EQUATIONS.md` | `research/EQUATIONS_AND_METHODOLOGY.md` | Complete mathematical formulations | Level 7 |
| `02_Methodology/EMISSION_AND_FUEL_METHODOLOGY.md` | Primary Synthesis | HBEFA4 integration & stoichiometry | Level 3 |
| `02_Methodology/SAFETY_CONSTRAINTS.md` | `traffic_service/signal_controller.py` | Min/max green, clearance, shield | Level 4 |
| `02_Methodology/EXPERIMENTAL_PROTOCOL.md` | `scripts/run_10seed_validation.py` | 40-run benchmarking protocol | Level 2 |
| `03_Experimental_Data/DATASET_DESCRIPTION.md` | `sumo/silk_board/` | SUMO network and route files | Level 2 |
| `03_Experimental_Data/EXPERIMENT_MANIFEST.md` | `outputs/validation/10seeds/` | Manifest of all 40 master runs | Level 1 |
| `03_Experimental_Data/RAW_DATA_CATALOG.md` | Primary Synthesis | JSON dictionary schema and fields | Level 1 |
| `03_Experimental_Data/BENCHMARK_CONFIGURATION.md` | `scripts/run_10seed_validation.py` | Simulation parameters & edges | Level 2 |
| `03_Experimental_Data/VEHICLE_COMPOSITION.md` | `scratch/analyze_departed_fleet.py` | Exact fleet counts (N=378, N=109) | Level 1 |
| `03_Experimental_Data/DATA_PROVENANCE.md` | Primary Synthesis | Audit trail from raw JSON to paper | Level 1 |
| `04_Results_and_Analysis/RESULTS_AND_TABLES.md` | `research/RESULTS_AND_TABLES.md` | Table 1 (Benchmark), Table 1b | Level 7 |
| `04_Results_and_Analysis/STATISTICAL_ANALYSIS.md` | `statistical_analysis.json` | Complete descriptive & paired stats | Level 6 |
| `04_Results_and_Analysis/CONTROLLER_COMPARISON.md` | Primary Synthesis | Multi-controller behavioral analysis | Level 7 |
| `04_Results_and_Analysis/TRAVEL_TIME_ANALYSIS.md` | Primary Synthesis | Travel time metrics & p-values | Level 6 |
| `04_Results_and_Analysis/CUMULATIVE_DELAY_ANALYSIS.md` | `outputs/validation/10seeds/` | Cumulative delay (12,373.2 veh*s) | Level 1 |
| `04_Results_and_Analysis/SPEED_ANALYSIS.md` | `outputs/validation/10seeds/` | Velocity analysis (28.21 km/h) | Level 1 |
| `04_Results_and_Analysis/EMISSIONS_ANALYSIS.md` | Primary Synthesis | HBEFA4 CO2 emission reductions | Level 6 |
| `04_Results_and_Analysis/FUEL_CONSUMPTION_ANALYSIS.md` | Primary Synthesis | Petrol-equivalent fuel & stoichiometry | Level 3 |
| `04_Results_and_Analysis/ROBUSTNESS_AND_ABLATION_ANALYSIS.md`| `outputs/experiments/phase4/` | Series 4B ablations & 4C status | Level 6 |
| `04_Results_and_Analysis/FIGURE_CATALOG.md` | Primary Synthesis | Publication figure & table plan | Level 7 |
| `05_Validation_and_Testing/FINAL_SOURCE_EVIDENCE_REGISTER.md`| `reports/final/SCIENTIFIC_CLAIM_...` | Verification register | Level 5 |
| `05_Validation_and_Testing/FINAL_METRIC_VERIFICATION_MATRIX.md`| `reports/final/METRIC_FORMULA_...` | Metric formula validation | Level 5 |
| `05_Validation_and_Testing/FINAL_TEST_EVIDENCE_MATRIX.md` | `reports/final/FINAL_ACCEPTANCE_...`| Automated test suite evidence | Level 5 |
| `05_Validation_and_Testing/CONTROLLER_VERIFICATION.md` | `reports/final/CONTROLLER_IMPLEM...` | Controller code verification | Level 4 |
| `05_Validation_and_Testing/INTEGRATION_TEST_EVIDENCE.md` | `reports/final/END_TO_END_DATA_...` | TraCI/FastAPI/WS integration | Level 5 |
| `05_Validation_and_Testing/REPRODUCIBILITY_VALIDATION.md` | Primary Synthesis | Step-by-step reproduction guide | Level 2 |
| `05_Validation_and_Testing/SCIENTIFIC_CLAIM_VERIFICATION.md`| Primary Synthesis | Claim-by-claim verification table | Level 5 |
| `06_Research_Paper/RESEARCH_PAPER_MASTER_DRAFT.md` | `research/RESEARCH_PAPER_MASTER_DRAFT.md`| Complete master manuscript | Level 7 |
| `06_Research_Paper/ABSTRACT.md` | Extracted from Master Draft | Standalone Abstract | Level 7 |
| `06_Research_Paper/INTRODUCTION.md` | Extracted from Master Draft | Section I Draft | Level 7 |
| `06_Research_Paper/RELATED_WORK.md` | Extracted from Master Draft | Section II Draft | Level 7 |
| `06_Research_Paper/PROBLEM_FORMULATION.md` | Extracted from Master Draft | Section III Draft | Level 7 |
| `06_Research_Paper/PROPOSED_METHODOLOGY.md` | Extracted from Master Draft | Section IV Draft | Level 7 |
| `06_Research_Paper/EXPERIMENTAL_SETUP.md` | Extracted from Master Draft | Section V Draft | Level 7 |
| `06_Research_Paper/RESULTS_AND_DISCUSSION.md` | Extracted from Master Draft | Section VI Draft | Level 7 |
| `06_Research_Paper/LIMITATIONS.md` | Extracted from Master Draft | Section VII Draft | Level 7 |
| `06_Research_Paper/CONCLUSION_AND_FUTURE_WORK.md` | Extracted from Master Draft | Section VIII Draft | Level 7 |
| `06_Research_Paper/KEYWORDS.md` | Primary Synthesis | Standard IEEE/ACM Keywords | Level 7 |
| `07_Figures_and_Tables/tables/TABLES_SUMMARY.md` | Primary Synthesis | Tables summary for LaTeX conversion | Level 7 |
| `08_References_and_Citations/REFERENCES.bib` | `research/REFERENCES.bib` | 16 verified BibTeX entries | Level 5 |
| `08_References_and_Citations/CITATION_AUDIT.md` | CrossRef / DBLP Audit | Formal citation audit | Level 5 |
| `08_References_and_Citations/DOI_VERIFICATION.md` | CrossRef / DBLP Audit | 15 active DOIs verified | Level 5 |
| `08_References_and_Citations/REFERENCE_NOTES.md` | Primary Synthesis | In-depth literature reading notes | Level 7 |
| `09_Formatting_and_Submission/TARGET_VENUE_COMPARISON.md` | Primary Synthesis | TR-C vs IEEE T-ITS vs IEEE TCST | Level 8 |
| `09_Formatting_and_Submission/PAPER_FORMATTING_GUIDE.md` | Primary Synthesis | LaTeX IEEEtran / elsarticle specs | Level 8 |
| `09_Formatting_and_Submission/SUBMISSION_CHECKLIST.md` | Primary Synthesis | Pre-submission verification list | Level 8 |
| `09_Formatting_and_Submission/AUTHOR_CONTRIBUTIONS.md` | Primary Synthesis | CRediT taxonomy roles | Level 8 |
| `09_Formatting_and_Submission/ACKNOWLEDGEMENTS_AND_FUNDING.md`| Primary Synthesis | Grant and institutional text | Level 8 |
| `10_Audit_Reports/FINAL_MANUSCRIPT_CORRECTION_LOG.md` | `reports/final/RESEARCH_PAPER_CORR...`| Complete itemized correction log | Level 5 |
| `10_Audit_Reports/FINAL_UNRESOLVED_SCIENTIFIC_ISSUES.md` | `reports/final/RESEARCH_PAPER_UNRE...`| Transparent limitation register | Level 5 |
| `10_Audit_Reports/CROSS_DOCUMENT_CONSISTENCY_MATRIX.md` | `reports/final/RESEARCH_PAPER_CROSS...`| 100% cross-file alignment matrix | Level 5 |
| `10_Audit_Reports/FINAL_RESEARCH_PAPER_READINESS_REPORT.md`| `reports/final/RESEARCH_PAPER_FINAL...`| 9.69/10 readiness certification | Level 5 |

---

## 3. Order of Authority & Evidence Hierarchy

1. **Level 1: Raw Simulation Execution Records** (`outputs/validation/10seeds/runs/*.json`) — Immutable ground truth.
2. **Level 2: Experiment Scripts & Network Files** (`scripts/run_10seed_validation.py`, `sumo/silk_board/`) — Operational parameters.
3. **Level 3: Metric Calculation Code** (`backend/simulation_service.py`, `traffic_service/state_extractor.py`) — Exact formulas.
4. **Level 4: Controller & Safety Shield Source Code** (`traffic_service/signal_controller.py`, `traffic_service/ai/env.py`).
5. **Level 5: Reproducible Test & Verification Reports** (`reports/final/`).
6. **Level 6: Derived Statistical Aggregates** (`outputs/validation/10seeds/statistical_analysis.json`).
7. **Level 7: Research Manuscript Drafts & Tables** (`06_Research_Paper/`, `04_Results_and_Analysis/`).
8. **Level 8: Formatting, Submission & Administrative Planning** (`09_Formatting_and_Submission/`).
