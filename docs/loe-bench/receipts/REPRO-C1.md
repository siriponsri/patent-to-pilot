# REPRO-C1 | Independent recomputation of C′

**28 November 2026 · REPRODUCED WITH EXPLAINED DIFFERENCES.** H1 passed, H2 failed and stopped the fixed sequence, and H3 remained descriptive. All requested results agree at the precision reported in SCORE. The largest absolute difference in an unrounded bootstrap endpoint was `2.22e-16` in recall units, about `2.22e-14` percentage points. Changing only the floating-point reduction reproduced the original JSON values exactly.

## Inputs and independence

The executor started from clean checkout `bc4dc19e74c97a6b5c9ca2692e27574916947cd3` and created `loe/REPRO-C1`. The executor was independent of SCORE. The governing recipe came from the [registered queue and inference rules](../PREREGISTRATION.md#inference-criteria-and-analysis-failures) and the OSF update sheets [1](../OSF-UPDATE-SHEET.md), [2](../OSF-UPDATE-2-SHEET.md), [3](../OSF-UPDATE-3-SHEET.md) and [4](../OSF-UPDATE-4-SHEET.md). The canonical registered record SHA-256 is `3f91145251465b0ed9c89233337748e1b9fd84db8c4c2a6158860374670e1c77`.

1. Read the registered methods and the relevant OSF update text. Consulted the file-and-digest entries under [SCORE private outputs](SCORE.md#private-outputs-and-verification) to identify the two inputs. Verified both raw SHA-256 values before decoding either export. Inspected only field names, types and record counts in the preliminary schema probe.
2. Implemented and ran [the independent verifier](../../../loe-bench/verify/repro_c1.py) using Python 3.12.10 and NumPy 2.5.4 on CPU. Captured the aggregate-only output before opening the comparison results or scorer source. The source SHA-256 was `e4a056ce9fb4cb7ce7fbf31c6530c9c23df4971a688be38afc19e423294e6732`. The pre-comparison aggregate SHA-256 was `3185891a338cfd5db1a0b2c0d41cbe83d046d3569dc49380cb19334d8ad7aed5` (UTF-8, CRLF, trailing newline).
3. Compared the frozen output with [SCORE](SCORE.md#primary-family) and the [aggregate JSON](../../../loe-bench/data/SCORE_CPRIME_RESULTS.json), whose canonical LF SHA-256 was `38f65240b57a4662349d3bdc89fd026908d888bdb2cfcb1ed63f430ed845d932`. After comparing, inspected the original scorer and queue code and tested the numerical explanation below.

| Input under the private `loe-bench/score` directory | Rows | Expected and observed raw SHA-256 |
| --- | ---: | --- |
| `C1_scores_12m.json` | 5,259 | `a644f1d40271c9a59a5405b840724906332ce975854d2afedd3d22c4ded80891` |
| `C1_scores_24m.json` | 4,639 | `c3b9e51891fd8f577dfce9f7fbbfb466f25f29ae50ed4edd9d8b2d0fcbcc84e7` |

Both exports were read-only. The private bootstrap archive, export manifest, raw protected labels and other private inputs were unopened. The verifier reads only the two named exports and emits only aggregates. This audit starts at exported scores and event indicators. Model fitting, historical cohort construction and source-label reconstruction were outside its scope. No GPU or paid API was used.

## Reproduction procedure

From the repository root, run `py -3.12 loe-bench/verify/repro_c1.py <score-directory>` with Python 3.12.10 and NumPy 2.5.4. At each cutoff, the verifier finds the slot boundary by partitioning the native scores of the sampled copies. Each score above the boundary earns one slot per copy. Each score at the boundary earns the remaining slots divided by the number of tied copies. The verifier sums expected event hits over cutoffs and divides by all event rows for recall and all review slots for precision. M3 distinct event-drug capture at 24 months averages each event drug's chance of appearing at least once on a positive row, using independent cutoff lotteries.

For each horizon, sort unique string drug keys with `np.unique`, reset PCG64 to 20261127 and call `rng.integers(n, size=n)` once for each of 2,000 draws. Use the resulting vector of whole-drug multiplicities for all arms, rebuild each cutoff's queue and subtract paired recalls. Both the 95% interval's lower endpoint and the one-sided 97.5% lower bound use the 0.025 linear percentile. A lower bound must exceed zero for a reached hypothesis to pass. The +10 pp criterion evaluates the point estimate separately.

## Comparison with the unrounded SCORE JSON

The arm estimates use `horizons.<months>.arms.<arm>.expected_queued_events`, `horizons.<months>.slots` and the matching arm estimates in `horizons.<months>.levels`. Each arm uses 202 event rows at 12 months and 368 at 24 months. These denominators also match exactly.

| Horizon | Arm | Measure | Independent | SCORE JSON | Absolute difference |
| ---: | --- | --- | ---: | ---: | ---: |
| 12m | B1 | Expected hits | 102.28938217367079 | 102.28938217367079 | 0 |
| 12m | B1 | Slots | 1048 | 1048 | 0 |
| 12m | B1 | Recall | 0.5063830800676772 | 0.5063830800676772 | 0 |
| 12m | B1 | Precision | 0.09760437230312098 | 0.09760437230312098 | 0 |
| 12m | M1 | Expected hits | 137 | 137 | 0 |
| 12m | M1 | Slots | 1048 | 1048 | 0 |
| 12m | M1 | Recall | 0.6782178217821783 | 0.6782178217821783 | 0 |
| 12m | M1 | Precision | 0.13072519083969467 | 0.13072519083969467 | 0 |
| 12m | M3 | Expected hits | 136 | 136 | 0 |
| 12m | M3 | Slots | 1048 | 1048 | 0 |
| 12m | M3 | Recall | 0.6732673267326733 | 0.6732673267326733 | 0 |
| 12m | M3 | Precision | 0.1297709923664122 | 0.1297709923664122 | 0 |
| 24m | B1 | Expected hits | 171.04234654234656 | 171.04234654234654 | 2.842170943040401e-14 |
| 24m | B1 | Slots | 924 | 924 | 0 |
| 24m | B1 | Recall | 0.46478898516942 | 0.4647889851694199 | 1.110223024625157e-16 |
| 24m | B1 | Precision | 0.18511076465621923 | 0.1851107646562192 | 2.775557561562891e-17 |
| 24m | M1 | Expected hits | 241 | 241 | 0 |
| 24m | M1 | Slots | 924 | 924 | 0 |
| 24m | M1 | Recall | 0.654891304347826 | 0.654891304347826 | 0 |
| 24m | M1 | Precision | 0.26082251082251084 | 0.26082251082251084 | 0 |
| 24m | M3 | Expected hits | 246 | 246 | 0 |
| 24m | M3 | Slots | 924 | 924 | 0 |
| 24m | M3 | Recall | 0.6684782608695652 | 0.6684782608695652 | 0 |
| 24m | M3 | Precision | 0.2662337662337662 | 0.2662337662337662 | 0 |

M3 distinct event-drug capture at 24 months uses `horizons.24.event_drugs`, `horizons.24.arms.M3.expected_captured_event_drugs` and `horizons.24.levels.M3.distinct_event_drug_capture`.

| 24m M3 distinct capture measure | Independent | SCORE JSON | Absolute difference |
| --- | ---: | ---: | ---: |
| Event drugs | 202 | 202 | 0 |
| Expected captured event drugs | 143 | 143 | 0 |
| Capture proportion | 0.7079207920792079 | 0.7079207920792079 | 0 |
| 95% lower endpoint | 0.6511597625968992 | 0.6511597625968992 | 0 |
| 95% upper endpoint | 0.7668431510639367 | 0.7668431510639367 | 0 |
| Undefined draws | 0 | 0 | 0 |

Contrast values below are proportions. H1–H3 refer to the JSON `primary` fields. The 24-month M1−B1 secondary contrast uses `horizons.24.contrasts.M1-B1.recall`. The reference gives the same 0.025 quantile as its 95% interval's lower endpoint for this contrast.

| Contrast | Measure | Independent | SCORE JSON | Absolute difference |
| --- | --- | ---: | ---: | ---: |
| H1 | Point | 0.20368927570014517 | 0.20368927570014528 | 1.110223024625157e-16 |
| H1 | 95% lower endpoint | 0.14369109147667547 | 0.14369109147667547 | 0 |
| H1 | 95% upper endpoint | 0.2616295354199167 | 0.2616295354199167 | 0 |
| H1 | One-sided lower bound | 0.14369109147667547 | 0.14369109147667547 | 0 |
| H1 | Undefined draws | 0 | 0 | 0 |
| H2 | Point | 0.013586956521739135 | 0.013586956521739135 | 0 |
| H2 | 95% lower endpoint | -0.02200895491827964 | -0.02200895491827964 | 0 |
| H2 | 95% upper endpoint | 0.030138848652899144 | 0.030138848652899144 | 0 |
| H2 | One-sided lower bound | -0.02200895491827964 | -0.02200895491827964 | 0 |
| H2 | Undefined draws | 0 | 0 | 0 |
| H3 | Point | 0.16688424666499613 | 0.16688424666499613 | 0 |
| H3 | 95% lower endpoint | 0.09975633310676586 | 0.09975633310676608 | 2.220446049250313e-16 |
| H3 | 95% upper endpoint | 0.24214724916185112 | 0.24214724916185107 | 5.551115123125783e-17 |
| H3 | One-sided lower bound | 0.09975633310676586 | 0.09975633310676608 | 2.220446049250313e-16 |
| H3 | Undefined draws | 0 | 0 | 0 |
| M1−B1, 24m | Point | 0.19010231917840603 | 0.19010231917840614 | 1.110223024625157e-16 |
| M1−B1, 24m | 95% lower endpoint | 0.13335263056064942 | 0.13335263056064942 | 0 |
| M1−B1, 24m | 95% upper endpoint | 0.2561777777568839 | 0.2561777777568839 | 0 |
| M1−B1, 24m | One-sided lower bound | 0.13335263056064942 | 0.13335263056064942 | 0 |
| M1−B1, 24m | Undefined draws | 0 | 0 | 0 |

| Contrast | Horizon and arms | Independent and SCORE point, pp | Independent and SCORE 95% CI, pp | Independent and SCORE one-sided lower, pp | Independent and SCORE decision | ≥+10 pp |
| --- | --- | ---: | --- | ---: | --- | --- |
| H1 | 24m M3−B1 | +20.37 | [+14.37, +26.16] | +14.37 | PASS | Yes |
| H2 | 24m M3−M1 | +1.36 | [−2.20, +3.01] | −2.20 | FAIL | No |
| H3 | 12m M3−B1 | +16.69 | [+9.98, +24.21] | +9.98 | NOT_REACHED_DESCRIPTIVE | Yes |
| Secondary | 24m M1−B1 | +19.01 | [+13.34, +25.62] | +13.34 | Descriptive | Yes |

The absolute difference for every numeric entry in the rounded comparison table is zero at the shown precision. All six recall and precision pairs and the M3 distinct capture proportion also match the [four-decimal SCORE table](SCORE.md#secondary-analyses).

## Discrepancy diagnosis

The independent verifier sums the fractional event weights within each cutoff and adds those subtotals. The [original adapter](../../../loe-bench/scripts/score_cprime.py#L303), published in SCORE commit `a7464a7a` with LF SHA-256 `6b6f37e09d0ca209a4c83f65fdffd1a29cc295dd941fe64acde6e2eb2214450b`, takes one full-panel dot product of shares with multiplicity-weighted event indicators. The [original queue](../../../loe-bench/loe_bench/review_metrics.py#L13) allocates slots by cumulative counts of grouped native scores. Both use the same tie fractions and the same registered PCG64 procedure. The choice of floating-point reduction changes the order of additions.

A diagnostic rerun reused the independently computed shares in export row order and changed only the pooled hit reduction to `float(shares @ (row_copies * positive))`. All 47 tested JSON numeric fields matched exactly after that change, including all four contrast intervals. No production scorer was executed. The committed verifier retains its pre-comparison reduction and source hash.

## Verification and handoff

- PASS · `py -3.12 -m pytest loe-bench/verify/test_repro_c1.py tests/test_org_adaptive_terminology.py -q` · Six tests passed. The fixtures cover a three-way tie at the boundary, a changing slot count and duplicate copies, a repeated event drug across cutoffs, and an undefined bootstrap draw.
- PASS · `py -3.12 -m pytest tests/test_org_adaptive_terminology.py -q` · Two tests passed.
- PASS · Checked all 50 numeric comparison rows and absolute differences against the pre-comparison aggregate and SCORE JSON.
- FAIL (accepted baseline) · `py -3.12 -m pytest -o addopts= -q` · Exit 1. 2,760 passed, 50 skipped, one xfailed and eight failed in 813.84 seconds. All failures were the four `nan`, `inflated`, `erased` and `insufficient` cases of `test_budget_cannot_use_nonfinite_inflated_or_erased_cost` in each of `test_sacr_r2_smoke_supervisor.py` and `test_sacr_r3_smoke_supervisor.py`. The existing ledger fails the cumulative budget check before the fixture mutations.

The main planner owns review and integration, including the lane handoff and memory updates. The reusable result for those records is that the registered RNG and cutoff queues can be independently rerun from the two authenticated exports, with the reduction order accounting for the last-bit differences. Use the displayed SCORE precision for publication and document the reduction order if exact JSON equality is required. The branch for review is `origin/loe/REPRO-C1`.
