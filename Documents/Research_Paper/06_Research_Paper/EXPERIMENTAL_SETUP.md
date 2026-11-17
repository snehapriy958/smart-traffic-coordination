# Section V: Experimental Setup & Benchmarking Design

- **Execution Protocol**: 40 isolated runs ($4\text{ controllers} \times 10\text{ seeds}$) executed via `scripts/run_10seed_validation.py`.
- **Duration**: 900.0s per run (Peak 0-300s, Shoulder 300-600s, Off-Peak 600-900s).
- **Statistical Design**: Paired Student's t-test ($df=9$), Holm-Bonferroni correction ($m=3$), Cohen's $d_z$, Wilcoxon signed-rank test.
