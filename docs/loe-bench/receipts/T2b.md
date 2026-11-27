# T2b | Orange Book availability and matched age signal

## Result

**PASS for the development rerun.** The [summary](../../../loe-bench/data/T2b_dev_summary.json) records the same split dates, cohort counts and event-cluster counts as T2. Validation has 2,231 rows, 628 drug clusters and 89 event clusters at 12 months, and 1,118 rows, 579 drug clusters and 66 event clusters at 24 months. The 36-month horizon is `NOT_RUN` under the strict embargo.

| Horizon | OPEN | BLOCKED | CONTESTED | M3 OPEN no-entry calls | Package ensemble OPEN no-entry calls |
| --- | ---: | ---: | ---: | ---: | ---: |
| 12 months | 2 | 506 | 1,723 | 2/2 | 2/2 |
| 24 months | 10 | 181 | 927 | 0/10 | 10/10 |

| Horizon | Arm | AURC₈₀ | Brier | ECE | Coverage |
| --- | --- | ---: | ---: | ---: | ---: |
| 12 months | B1 | 0.017482 | 0.037536 | 0.005143 | 100.00% |
| 12 months | M1 | 0.012989 | 0.036837 | 0.004444 | 99.82% |
| 12 months | M2 | 0.040814 | 0.038358 | 0.001634 | 99.91% |
| 12 months | M3 | 0.012672 | 0.036828 | 0.005114 | 99.87% |
| 24 months | B1 | 0.028828 | 0.070273 | 0.004038 | 100.00% |
| 24 months | M1 | 0.021563 | 0.067790 | 0.006742 | 95.17% |
| 24 months | M2 | 0.077582 | 0.074929 | 0.006340 | 99.46% |
| 24 months | M3 | 0.025605 | 0.071296 | 0.032500 | 99.37% |

| Horizon | M3 − M1 ΔAURC₈₀ (95% CI) | M3 − B1 ΔAURC₈₀ (95% CI) | M1 − B1 ΔAURC₈₀ (95% CI) |
| --- | ---: | ---: | ---: |
| 12 months | −0.00032 [−0.00092, +0.00027] | −0.00481 [−0.01015, +0.00018] | −0.00449 [−0.01009, +0.00062] |
| 24 months | +0.00404 [−0.00010, +0.00990] | −0.00322 [−0.01195, +0.00542] | −0.00727 [−0.01531, −0.00004] |

Lower AURC₈₀ is better. All six comparisons had 2,000 valid paired draws. The M3–M1 intervals include zero at both horizons and neither point estimate reaches the declared useful improvement. Both M1 and M3 tried three configurations and selected L2 = 100 at both horizons.

| Cutoff | Chosen edition | Staleness in days | Availability proof, Wayback timestamp UTC | Split use |
| --- | --- | ---: | --- | --- |
| 2010-01-01 | 2009-10-16 | 77 | `20091104091455` | TRAIN at 12 and 24 months |
| 2011-01-01 | None | — | Fresh edition unavailable | Coverage inventory |
| 2012-01-01 | 2011-12-14 | 18 | `20111229223919` | Validation at 12 months |
| 2013-01-01 | 2012-09-17 | 106 | `20120921215526` | Validation at 12 and 24 months |
| 2014-01-01 | 2013-08-30 | 124 | `20130906105914` | Validation at 12 and 24 months |
| 2015-01-01 | 2014-09-10 | 113 | `20140915104404` | Validation at 12 months |
| 2016-01-01 | 2015-09-18 | 105 | `20151006063349` | Coverage inventory |

The December 2009 ZIP's capture postdates the 2010 cutoff. The October 2009 ZIP supplies timely evidence for TRAIN. The latest proven ZIP at the 2011 cutoff is 375 days old. [E2b archive evidence](E2b.md#coverage)

## Design choices

- Start from `be2fce13` and retain [T2's strict split, cohort, labels and scoring policies](T2.md#design-choices). For each annual cutoff the T2b feature builder selects the latest Orange Book edition dated no later than that cutoff and at or after the inclusive six-calendar-month floor. Require exact-edition availability by the UTC cutoff date. Accept the primary Wayback capture, an additional capture keyed by edition SHA-256, or an exact FDA publication record. The latter uses `e2b.fda_publication_records` with `edition_sha256`, `publication_date`, `source_url`, `html_sha256` and `locator`. The current manifest's FDA listing notes do not identify a qualifying ZIP by hash. Keep rows with unavailable evidence and mark the Orange Book features missing. Verify the selected ZIPs used in the splits.
- Fit one B1 age table on TRAIN per horizon. For M1 and M3, append the logit of that table's prediction, clipped at probabilities of `1e-8` and `1 - 1e-8`, to the shared feature vector. Both arms use that TRAIN table for TRAIN and validation features. M3 adds three verdict indicators and uses the existing graph decision policy. Both arms use the existing logistic optimizer at 300 epochs and learning rate 0.3 with the same three L2 settings, `1, 10, 100`. Use the fixed T2 sigmoid recalibration with five drug-key validation folds for each candidate. Select independently by lowest pooled cross-calibrated validation Brier score, breaking exact ties by smaller L2. B1 and M2 retain their T2 definitions.
- Use the T2 thresholds, Brier, 10-bin ECE, coverage and normalized AURC over 0–80% coverage. Compute M3−M1, M3−B1 and M1−B1 on identical validation rows. Use 2,000 paired bootstrap draws by drug key with seed `20261127` and a 95% percentile interval for each pair reaching 80% coverage. The declared useful effect is Δ ≤ −0.010. Cutoffs from 2017-01-01 are outside the development runner.

## Evidence

```powershell
cd loe-bench
python -m unittest discover -s loe_bench/tests -t .
python scripts/t2_dev_run.py --raw C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/raw-20261127
```

Both commands exited 0 on Python 3.12.10. All 68 LOE-Bench unit tests passed with existing Purple Book file-handle warnings. The new tests cover late-only captures, timely alternatives, same-date ZIP identity, and explicit publication records linked by hash. The runner verified the SHA-256 of both Drugs@FDA inputs and all five ZIPs used for model rows. The [summary](../../../loe-bench/data/T2b_dev_summary.json) records input and manifest hashes, source URLs, capture timestamps, and per-cutoff row and verdict counts. Exact edition row locators follow the [T2 evidence section](T2.md#evidence). A summary audit checked cohort parity with T2, edition eligibility, verdict and ECE totals, tuning selections, pair deltas and draw counts. The seal file matches the starting revision and the lock file is absent.

The final repository run used `python -m pytest --tb=short --basetemp C:/Users/User/AppData/Local/Temp/ptp-t2b-97a3-02` with the development runner idle. Raw exit 1. It reproduced 2,760 passed, 50 skipped, one xfailed and the eight accepted SACR r2/r3 budget failures, with two warnings. The Workbench loopback case passed in the final run. [Repository test policy](../../../AGENTS.md)

## Failures and limitations

- The first repository pytest run, using `--tb=short --basetemp C:/Users/User/AppData/Local/Temp/ptp-t2b-97a3-01`, exited 1 with 2,759 passed, 50 skipped, one xfailed, eight known SACR budget failures and one Workbench loopback failure. `tests/test_ptp_g01_workbench.py::test_http_and_cli_reach_the_same_core` raised `WinError 10053` and passed in isolation with a fresh temporary directory.
- Validation supplies both calibration folds and model selection. The bootstrap conditions on the selected fits and predictions, so the intervals describe this development analysis. T2b changes edition coverage, adds the age signal and introduces matched tuning in the same run. Their individual effects remain unmeasured.
- The OPEN subset remains sparse. Its no-entry counts measure emitted actions. The 24-month counts alone cannot establish decision quality.
- At 36 months the first TRAIN window ends on 2013-01-01, which is the latest admissible validation start. The embargo requires strict separation.

## Next action

The main planner reviews the edition and model changes before integrating T2b. Use the development results to inform the separately assigned threshold and power cards under their declared rules. Keep confirmatory scoring behind the preregistration gate.
