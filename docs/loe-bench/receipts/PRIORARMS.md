# PRIORARMS | Open survival arms

**P1-RSF-OPEN ADMITTED. P2-COX-OPEN ADMITTED.** Both arms met the locked technical criteria and have private t0 predictions at 12 and 24 months. The forecast run at `892be4ef1627c9aaf389883a30ade9182edd0ff5` exited 0. The C′ supplement is `NOT_RUN`. The freeze card takes the predictions and manifest forward.

## Protocol and input boundary

The [locked specification](../PRIOR-ARMS-SPEC.md) defines two exploratory Track A arms outside H1–H3. The branch starts at `7196a9245132ff2719d9f335352fb9cdb3238964`, after the specification lock `369c232a3e0297ed73871d0cd7b9d4cf07f4d370`. The Track A core branch and planner checkout had no changes to the assigned paths at startup. The endpoint is first final original FDA ANDA approval in `(cutoff, cutoff + horizon]` for an eligible active-moiety history. Fits separate the horizons. The event clock divides elapsed days by the full calendar-window days and sets administrative censoring to 1. Every survival score is `1 − Ŝ(1 | X)`.

The runner reuses [TRACKA-CORE](TRACKA-CORE.md) for S0 and dated cutoff evidence, eligibility, t0 identity order and native queue allocation. Before modeling it verifies all 12 original package hashes from `SHA256SUMS`, the private core manifest, tagged S0 bytes and source pins, and the cutoff editions selected for TRAIN and t0. The private core checksum file started at SHA-256 `d4021b0a7c5562ce22124a551bc559fa863db842e1c863be68b91cd1ebb129b1`. The first-NDA calendar year is a single linear term. P2 centers and scales age and year with the population standard deviation of TRAIN, drops only exact zero-variance TRAIN columns and uses one CPU thread per numerical library. P1 uses the frozen zero fill and missingness bits supplied by the as-of builder. The isolated process receives the two feature matrices and TRAIN survival targets. Forecast input matrices carry features alone.

The [FREEZE](FREEZE.md) replay supplies the 2010 TRAIN and both development validation rosters. B1, M1 and M3 use native scores for the queue, AUC and C-index. Use their frozen TRAIN sigmoid probabilities for accuracy and Brier. The B3 development rule reads the linked, availability-proven Orange Book edition at each cutoff, compares all its recorded expiry dates to the horizon end and preserves the registered positive call on an empty list. The stricter time interpretation for the C-index compares an observed event only with a strictly later observed time from the same cutoff, including administrative censoring. Event times tied with one another or with administrative censoring contribute zero comparable pairs. Tied native risk on a comparable pair earns half credit. All development contrasts are descriptive and use 2,000 common whole-drug PCG64 draws per horizon, seed `20261127`, with yearly queues rebuilt on every draw and linear 95% percentile bounds.

The modeling run used local pre-t0 sources. No outcome-source fetch, paid API, GPU job or protected C′ data read occurred. Prospective outcomes remain pending. P1 and P2 never ran on the protected C′ projection or its score exports. Mature Track A TRAIN is independently reconstructed from S0 under the Track A protocol.

## Development validation (descriptive)

| Months | TRAIN cutoff | TRAIN rows / events | Validation cutoffs | Rows | Drugs | Event rows / drugs | Prevalence | Slots per arm |
| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 12 | 2010-01-01 | 547 / 25 | 2012–2015 | 2,161 | 609 | 90 / 90 | 4.16% | 430 |
| 24 | 2010-01-01 | 547 / 46 | 2013–2014 | 1,083 | 561 | 91 / 67 | 8.40% | 215 |

The B1, M1 and M3 replay matched the frozen TRAIN calibrators, roster counts, native recall and Brier scores. The paired intervals condition on the fitted arms. Confusion counts use the inclusive 0.5 cutoff for positive calls.

| Months | Arm | Recall at 20% | ROC AUC | Accuracy | TP / FP / TN / FN | Always-negative accuracy | Brier | Hard-rule Brier | C-index | Comparable pairs |
| ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 12 | B1 | 48.11% | 0.6836 | 95.84% | 0 / 0 / 2071 / 90 | 95.84% | 0.04025 | NA | 0.6835 | 47,560 |
| 12 | M1 | 61.11% | 0.7880 | 95.84% | 0 / 0 / 2071 / 90 | 95.84% | 0.03829 | NA | 0.7834 | 47,560 |
| 12 | M3 | 61.11% | 0.7932 | 95.84% | 0 / 0 / 2071 / 90 | 95.84% | 0.03822 | NA | 0.7887 | 47,560 |
| 12 | B3 | 10.70% | 0.3750 | 46.41% | 25 / 1093 / 978 / 65 | 95.84% | NA | 0.53586 | 0.3767 | 47,560 |
| 12 | P1-RSF-OPEN | 44.44% | 0.7070 | 95.84% | 0 / 0 / 2071 / 90 | 95.84% | 0.03925 | NA | 0.7029 | 47,560 |
| 12 | P2-COX-OPEN | 53.33% | 0.7046 | 95.84% | 0 / 0 / 2071 / 90 | 95.84% | 0.03805 | NA | 0.6851 | 47,560 |
| 24 | B1 | 39.65% | 0.7199 | 91.60% | 0 / 0 / 992 / 91 | 91.60% | 0.07507 | NA | 0.7128 | 47,158 |
| 24 | M1 | 43.96% | 0.7575 | 91.41% | 0 / 2 / 990 / 91 | 91.60% | 0.07793 | NA | 0.7495 | 47,158 |
| 24 | M3 | 49.45% | 0.7659 | 91.51% | 1 / 2 / 990 / 90 | 91.60% | 0.07782 | NA | 0.7589 | 47,158 |
| 24 | B3 | 11.38% | 0.3705 | 41.37% | 29 / 573 / 419 / 62 | 91.60% | NA | 0.58633 | 0.3764 | 47,158 |
| 24 | P1-RSF-OPEN | 48.35% | 0.7708 | 91.60% | 0 / 0 / 992 / 91 | 91.60% | 0.07107 | NA | 0.7615 | 47,158 |
| 24 | P2-COX-OPEN | 36.26% | 0.5600 | 91.60% | 0 / 0 / 992 / 91 | 91.60% | 0.09786 | NA | 0.5555 | 47,158 |

| Months | Paired recall contrast | Difference, pp | 95% CI, pp | Undefined / draws |
| ---: | --- | ---: | --- | ---: |
| 12 | P1 − M3 | −16.67 | [−28.09, −5.49] | 0 / 2,000 |
| 12 | P2 − M3 | −7.78 | [−17.50, +2.38] | 0 / 2,000 |
| 24 | P1 − M3 | −1.10 | [−12.33, +11.00] | 0 / 2,000 |
| 24 | P2 − M3 | −13.19 | [−29.89, +3.33] | 0 / 2,000 |

## Track A t0 preparation and admission

| Months | Mature TRAIN rows / events / drugs | TRAIN cutoffs | t0 roster | Ordered core join |
| ---: | ---: | --- | ---: | --- |
| 12 | 8,513 / 332 / 954 | 2010 and 2012–2025 | 651 | PASS |
| 24 | 7,893 / 618 / 922 | 2010 and 2012–2024 | 651 | PASS |

| Arm | Repeat fits across development and t0 | Fit and convergence | Finite t0 forecasts | Decision |
| --- | --- | --- | --- | --- |
| P1-RSF-OPEN | PASS, exact score vectors and model summaries in all four repeat pairs | PASS, 500 trees fitted per model. The forest has no iterative convergence test. | PASS, 651 per horizon | ADMITTED |
| P2-COX-OPEN | PASS, exact score vectors and model summaries in all four repeat pairs | PASS, finite coefficients and baseline survival, with no convergence or numerical warnings | PASS, 651 per horizon | ADMITTED |

Admission used the fixture results, fit checks, repeatability and complete finite scores. P2 dropped `oral` and `injectable` in every fit under the zero-variance TRAIN rule. The dated core features, fixed model settings and isolated runtime constrain both adaptations. The development results describe reused cutoffs and do not establish prospective performance.

| Months | Arm | Capacity | Native boundary score | Above / tied | Slots at boundary | Boundary inclusion |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 12 | P1-RSF-OPEN | 130 | 0.07924949784890756 | 129 / 1 | 1 | 1.0 |
| 12 | P2-COX-OPEN | 130 | 0.02340580396156522 | 129 / 1 | 1 | 1.0 |
| 24 | P1-RSF-OPEN | 130 | 0.16541829550462628 | 129 / 1 | 1 | 1.0 |
| 24 | P2-COX-OPEN | 130 | 0.044009484545998845 | 129 / 1 | 1 | 1.0 |

| Artifact | SHA-256 |
| --- | --- |
| Private `trackA/priorarms_predictions_12m.jsonl` | `8b8610f5f317cfcf8b2dab7b2c0a5cb92da14e80269845fe826a5d45aee7ca65` |
| Private `trackA/priorarms_predictions_24m.jsonl` | `d5be5a65209dbe71cebcdda0fb74373b5d17d20dfc4c188af126f2d318bc356a` |
| Private `trackA/SHA256SUMS` after append | `f2d4e2b5a627f4ec5ff0f2df4a993ff21ecda2f6108e4fc18296f67748b13e8e` |
| [PRIORARMS manifest](../../../loe-bench/data/PRIORARMS_MANIFEST.json), canonical LF | `6fa51cea9298d11f70ddf1ba2d0d680971df3a01172b3b10ea4203250d2be524` |

An independent read verified all 14 file digests, the exact ordered `(key, t0, horizon_months)` joins to the core roster and predictions, the per-arm float64 score digests, and every expected queue inclusion from tied risks. All four arms-by-horizon queues total 130 slots. The predictions remain under `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/trackA/`. The manifest records model settings, score distributions, Cox coefficients and TRAIN transforms, survival grids and the research input digests.

## C′ supplement

**NOT_RUN.** The [dated analysis note](PRIORARMS-CPRIME-NOTE.md) was committed at `4ee32b11` before any supplement work. The authorized [`score_cprime.py`](../../../loe-bench/scripts/score_cprime.py) runner is bound to `loe/SCORE`; its preflight reads and verifies development inputs, while its scoring path opens protected outcome sources. It exposes no export-only command. The exports documented by SCORE contain native risk and binary labels. They omit exact event times and calibrated probabilities. The frozen sigmoid could reconstruct probabilities if the export-only execution path were authorized. No C′ per-row file was opened.

| Months | Arm | ROC AUC | Accuracy at p ≥ 0.5 | Brier from SCORE | C-index |
| ---: | --- | --- | --- | ---: | --- |
| 12 | B1 | NOT_RUN | NOT_RUN | 0.0373 | NOT_ESTIMABLE |
| 12 | M1 | NOT_RUN | NOT_RUN | 0.0354 | NOT_ESTIMABLE |
| 12 | M3 | NOT_RUN | NOT_RUN | 0.0352 | NOT_ESTIMABLE |
| 24 | B1 | NOT_RUN | NOT_RUN | 0.0713 | NOT_ESTIMABLE |
| 24 | M1 | NOT_RUN | NOT_RUN | 0.0654 | NOT_ESTIMABLE |
| 24 | M3 | NOT_RUN | NOT_RUN | 0.0647 | NOT_ESTIMABLE |

[SCORE's Brier values and export schema](SCORE.md).

## External reference, not head-to-head

LOE-Bench estimates in this table use first final original ANDA approval on the development validation rosters. Published values use the study-specific endpoint and cohorts shown. These designs do not estimate cross-study performance differences.

| Study | Endpoint and cohort | Published metric and value | LOE-Bench development, 12m / 24m | Source |
| --- | --- | --- | --- | --- |
| Hu 2021 presentation | Time from the earliest lawful submission date to first ANDA submission referencing a new chemical entity | RSF leave-one-out C-index 0.767 | P1 C-index 0.7029 / 0.7615 · M3 C-index 0.7887 / 0.7589 | [FDA presentation, slide 13](https://www.complexgenerics.org/wp-content/uploads/crcg/prsnt-Hu20210921-SBIA.pdf#page=13) |
| Hopefl et al. 2025 | First ANDA submission for orphan drug products, 140 NCEs and 97 non-NCEs, with separate time origins | RSF C-index, NCE / non-NCE. Leave-one-product-out 0.769 / 0.736. Repeated five-fold CV 0.675 ± 0.026 / 0.754 ± 0.044. | P1 C-index 0.7029 / 0.7615 · M3 C-index 0.7887 / 0.7589 | [Primary paper, §4.2](https://pmc.ncbi.nlm.nih.gov/articles/PMC12497357/) |
| Kerr & Glos 2020 | Time from NME approval to first generic approval for FDA small-molecule NMEs approved in 2001–2012 | Cox association HR 0.464 for NMEs with both orphan and non-orphan indications versus single-indication non-orphan NMEs | P2 C-index 0.6851 / 0.5555. The fitted model uses a dated orphan flag, so an equivalent indication hazard ratio is unavailable. | [Publisher abstract, Results](https://doi.org/10.1007/s40290-019-00317-9) |
| Beall et al. 2018 | First appearance of a generic in Medicaid prescriptions for 170 top-selling small molecules that lost exclusivity in 2000–2012 | 42% of entry dates within one quarter of their estimates | B3 horizon accuracy 46.41% / 41.37%. The binary all-listed-expiry rule supplies no quarter-error estimate. | [Primary paper, Table 1](https://www.valueinhealthjournal.com/article/S1098-3015%2818%2932154-5/fulltext) |
| Memedovich et al. 2025 | Paragraph IV challenge within one year of eligibility for 210 FDA-approved patented small molecules from 2007–2018 | ROC AUC 0.807 for random forest and 0.770 for elastic net | P1 AUC 0.7070 / 0.7708 · P2 AUC 0.7046 / 0.5600 · M3 AUC 0.7932 / 0.7659 | [Primary paper, Table 2](https://doi.org/10.1371/journal.pmed.1004540) |

The references use the locked specification and [lane memory](../MEMORY.md#28-nov-2026-evening-prior-method-comparison-locked). The lane memory identifies Kerr and Glos's association HRs without a numerical value, so the table transcribes the one HR in the publisher's abstract. The Hu 2019 full article and supplement remain unverified. Its 2021 presentation supplies the C-index cited here.

## Reproduction and licenses

The base interpreter is `C:/Users/User/AppData/Local/Programs/Python/Python312/python.exe`, CPython 3.12.10 with registered NumPy 2.5.4. Its executable SHA-256 is `4d6f5f81a4bca11191c4c7c6b43632694d0a4ce74e068619d8fdc161d469859a`. The isolated interpreter is `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/venv-priorarms/Scripts/python.exe`, made from that base. All three specified package pins installed on Windows. The [Windows x86-64 wheel lock](../../../loe-bench/requirements-priorarms.lock) has LF SHA-256 `f34cd0791d5e1e0832bdf7614dbb74794a3c9497ee37fe0ab1238b4c97002d83` and records each of the 14 wheel hashes. PyPI wheels reside in `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/priorarms-wheels/`. Offline `pip install --no-index --require-hashes` and `pip check` both exited 0. The GPL wheels remain in that private research environment and wheelhouse. The repository carries the install lock and the experimental adapter.

| Dependency | Version | License from wheel metadata or included license |
| --- | --- | --- |
| CPython | 3.12.10 | PSF license |
| NumPy, SciPy | 2.2.6, 1.18.1 | BSD-3-Clause with bundled license notices |
| scikit-learn, joblib, threadpoolctl, cloudpickle | 1.7.2, 1.6.0, 3.8.0, 3.1.3 | BSD-3-Clause |
| scikit-survival | 0.25.0 | GPL-3.0-or-later |
| ECOS | 2.0.14 | GPLv3 |
| numexpr | 2.14.2 | MIT with bundled license notices |
| OSQP, QDLDL, tzdata | 0.6.7.post3, 0.1.9.post1, 2026.6 | Apache-2.0 |
| pandas, python-dateutil | 3.1.1, 4.0.0 | BSD-3-Clause with included license notices |

Run from `loe-bench/` on the committed code with the untouched core package and the isolated venv in the paths above.

```powershell
rtk proxy python -B scripts/priorarms_run.py
```

## Verification

| Interpreter | Command and working directory | Result | Exit |
| --- | --- | --- | ---: |
| CPython 3.12.10, registered NumPy 2.5.4 | `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` | PASS, 253 run, 243 passed, 10 skipped, including the five survival-runtime fixtures | 0 |
| Isolated CPython 3.12.10, NumPy 2.2.6 | `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` | PASS, 253 run, 248 passed, 5 skipped, all ten PRIORARMS fixtures passed | 0 |
| Isolated CPython 3.12.10, NumPy 2.2.6 | `python -B -m unittest loe_bench.tests.test_priorarms` from `loe-bench/` | PASS, ten passed on the forecast implementation | 0 |
| CPython 3.12.10, pytest 8.4.2, registered NumPy 2.5.4 | `python -m pytest --tb=short -p no:cacheprovider --basetemp <fresh-local-temp>` from the repository root | 2,760 passed, 50 skipped, one xfailed, eight standing SACR budget failures and two warnings | 1 |

The accepted pytest failures were `test_budget_cannot_use_nonfinite_inflated_or_erased_cost` in `test_sacr_r2_smoke_supervisor.py` and `test_sacr_r3_smoke_supervisor.py`, each for `nan`, `inflated`, `erased` and `insufficient`. The LOE-Bench suites emitted the existing Purple Book resource warnings. The survival fixtures cover an event on a leap-year window boundary, administrative censoring, exact missing bits, fractional ties under replicated row counts, within-cutoff comparable pairs, the inclusive probability threshold, TRAIN-only Cox transforms, analytic Breslow survival, surfaced convergence warnings and exact repeat fits for both methods.

The first modeling invocation at `51780b45` exited 1 before the first fit because the Python socket guard blocked SciPy's Windows hostname lookup during import. `892be4ef` allows that local OS lookup and retains the socket restrictions on network operations. The isolated CLI fixture reproduces the import and fit path. The failed invocation wrote no scores or private package changes.

## Handoff

The freeze card should carry both admitted columns from the two private prediction files into the Track A freeze. Verify the expanded `SHA256SUMS` and preserve the ordered core join and code, source and model pins in the freeze manifest. The planner controls the tag, external timestamp and OSF update 4. The two prospective windows mature on 27 November 2027 and 27 November 2028, respectively.
