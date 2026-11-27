# FIX2c | Historical Orange Book linkage and development rerun

## Result

**PASS for development execution and historical linkage.** The FIX2b key produced 2,445 entities. T2b's edition selection and availability proofs reproduced exactly. The 2011 cutoff still has no fresh proven edition and the strict embargo leaves the 36-month horizon `NOT_RUN`. The 12- and 24-month runs each used 547 training rows.

| Horizon | Validation rows | Drug clusters | Event clusters | OPEN | BLOCKED | CONTESTED | M3 OPEN no-entry | Package ensemble OPEN no-entry |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 12 months | 2,161 | 609 | 90 | 3 | 500 | 1,658 | 3/3 | 3/3 |
| 24 months | 1,083 | 561 | 67 | 10 | 181 | 892 | 0/10 | 9/10 |

| Horizon | Arm | AURC80 | Brier | ECE | Coverage |
| --- | --- | ---: | ---: | ---: | ---: |
| 12 months | B1 | 0.018575 | 0.039073 | 0.005471 | 100.00% |
| 12 months | M1 | 0.014621 | 0.038387 | 0.004525 | 99.91% |
| 12 months | M2 | 0.040666 | 0.040019 | 0.002011 | 99.91% |
| 12 months | M3 | 0.014236 | 0.038370 | 0.004542 | 99.95% |
| 24 months | B1 | 0.029330 | 0.073047 | 0.007294 | 100.00% |
| 24 months | M1 | 0.022234 | 0.069822 | 0.016749 | 94.46% |
| 24 months | M2 | 0.073570 | 0.077207 | 0.006354 | 99.26% |
| 24 months | M3 | 0.022100 | 0.071162 | 0.021058 | 97.51% |

| Horizon | M3 − M1 ΔAURC80 (95% CI) | M3 − B1 ΔAURC80 (95% CI) | M1 − B1 ΔAURC80 (95% CI) |
| --- | ---: | ---: | ---: |
| 12 months | −0.000386 [−0.001096, +0.000444] | −0.004339 [−0.009966, +0.001001] | −0.003953 [−0.009845, +0.001630] |
| 24 months | −0.000135 [−0.001453, +0.001101] | −0.007230 [−0.016242, +0.001034] | −0.007096 [−0.016259, +0.001424] |

All six intervals include zero and each uses 2,000 valid paired draws. The 24-month M1 versus B1 interval now crosses zero. Both M1 and M3 selected L2 = 100 at both horizons.

| Edition | NDA rows linked / total | Link rate |
| --- | ---: | ---: |
| 2009-06-09 | 7,409 / 7,441 | 99.57% |
| 2009-10-16 | 7,484 / 7,517 | 99.56% |
| 2009-12-22 | 7,522 / 7,846 | 95.87% |
| 2011-03-18 | 7,741 / 8,060 | 96.04% |
| 2011-12-14 | 7,867 / 8,186 | 96.10% |
| 2012-01-17 | 7,888 / 8,205 | 96.14% |
| 2012-09-17 | 8,010 / 8,338 | 96.07% |
| 2013-01-18 | 8,071 / 8,406 | 96.01% |
| 2013-08-30 | 8,172 / 8,508 | 96.05% |
| 2014-09-10 | 8,353 / 8,692 | 96.10% |
| 2015-01-16 | 8,420 / 8,760 | 96.12% |
| 2015-09-18 | 8,547 / 8,894 | 96.10% |
| 2016-03-18 | 8,659 / 9,011 | 96.09% |
| 2016-12-16 | 8,785 / 9,133 | 96.19% |

In the 2011-12-14 ZIP, product `022371/001` (ASTEPRO, data row 2806) produced conflicting product identity evidence and `017835/001` (CHROMALBIN, data row 693) had no entity match. In the 2014-09-10 ZIP, `020725/002` (CREON, data row 242) had no entity match. Ingredient linkage supplied all observed successful joins. The exact-product fallback recovered a synthetic blank ingredient row and supplied zero incremental matches in the historical inventory.

## Conflict resolution

- Merged `origin/loe/FIX2b` into `loe/FIX2c` from `ac2a2ca8`. In `ob_history.py` retained the T2b availability proofs, identity-aware sources and cache, and restored the FIX2b data-directory context for GSRS. In `t2_features.py` indexed the exact proven edition selected by T2b and retained the moiety and legacy key modes. The inclusive six-calendar-month floor and as-of product and patent date filters still apply.
- The model runner builds FIX2b entity identities once, using the pinned GSRS release and its existing alias union. A historical NDA product can join through its full ingredient composition and canonical alias. A matching NDA and product number can recover an absent ingredient field or a low-confidence historical name with the same normalized full name set. Conflicting product identities stay unlinked. The edition contributes only its own patents and exclusivities. The historical book cannot add a new entity link to the FIX2b union.
- For the two headerless 2009 editions, the Drugs@FDA and typed S0 Orange Book snapshots provide application types by application number. Untyped records without a unique supported type are counted separately. The denominator counts explicit or uniquely inferred NDA product rows, including records ineligible because their approval dates postdate the edition.
- The model protocol retains the shared training-only age table, split and strict embargo, calibration folds, tuning grid, verdict and action rules, and paired drug-cluster bootstrap from T2b. The legacy runner invocation keeps the original normalization for reproducing T2b. [T2b protocol](T2b.md#design-choices)

## Evidence

From `loe-bench/` with Python 3.12.10:

```powershell
python -m unittest discover -s loe_bench/tests -t .
python scripts/t2_dev_run.py --raw C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/raw-20261127 --key-mode moiety
```

The machine summary records source URLs, capture times, SHA-256 values and unmatched examples with application and product numbers and one-based nonblank data row numbers in the `products.txt` member. The runner verifies both Drugs@FDA files, five S0 Orange Book snapshot files, the GSRS export and the historical ZIPs it reads. [Machine summary](../../../loe-bench/data/FIX2c_dev_summary.json) · [S0 manifest](../../../loe-bench/data/S0_INPUT_MANIFEST.json) · [GSRS release and rights](FIX2.md#sources) · [FDA archival inventory](E2b.md)

- Both commands exited 0. All 93 LOE-Bench tests passed, with the existing Purple Book file-handle warnings. The fixture merges two actual legacy keys, retains both historical patents under the canonical key and its aliases, and refuses a future edition and a late capture.
- Root `python -m pytest --tb=short --basetemp C:/Users/User/AppData/Local/Temp/ptp-fix2c-merge` exited 1 with 2,760 passed, 50 skipped, one xfailed and the eight accepted SACR r2/r3 supervisor-budget failures.
- The summary audit checked split and edition parity with T2b, validation windows, verdict and ECE counts, paired deltas, draw counts and archive denominators. Summary SHA-256 is `13cfe83d34bbac707c95391fb832e7bb07101c4a029f7a9e3bca2c4873470bd4`. The test seal source matches the branch base. The preregistration lock and its environment variable were absent.

## Failures and limitations

- Historical identity matching uses the 2026 GSRS release and the S0 FDA snapshots. The edition hashes and capture evidence establish the temporal availability of the patent and exclusivity records. Historical availability of the identity crosswalk itself is unverified. Product-level linkage coverage is an engineering measure and does not independently adjudicate semantic correctness. [FIX2b audit](FIX2b.md#failures-and-limitations)
- Linkage counts cover ZIPs with edition dates before 2017-01-01. The descriptive inventory includes dated ZIPs with later capture dates. The model only uses fresh editions with availability proven by its cutoff. Purple Book is outside this NDA/ANDA protocol. The separate BLA/biosimilar pipeline was left out of the rerun. [Purple Book scope](E3.md)
- The first two editions have 626 and 620 unclassified product rows, respectively. Those rows are omitted from the reported NDA denominators. The higher link rates in those editions reflect a denominator based on application-type recovery and are sensitive to that recovery.
- The validation data inform tuning and calibration. Bootstrap intervals condition on the selected model predictions. Entity changes also affect cohort membership and event linkage, so the FIX2c versus T2b comparison cannot isolate the effect of historical patent linkage.

## Next action

The main planner reviews unmatched products, the retrospective identity crosswalk and the development rerun, then updates the lane handoff and memory at integration. Keep confirmatory evaluation behind the preregistration gate.
