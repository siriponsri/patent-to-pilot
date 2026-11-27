# FREEZE | Criteria v3 development freeze

## Protocol recorded before scoring

Use the merged FIX2c, E7b and K07 development replay, REG PIV semantics and graph v1.
Use the T1v3 guarded source readers, split, native models and train-only calibration.
Reconcile H2 on the same development roster. Replay pre-REG by restoring fresh-list
non-observation for matched undated PIV rows without a dated witness. Swap REG on
TRAIN, then on validation. Compare both queue scorers, matching seeds and draws.
Check native scores and common calibrators against the K22 entrypoints. Historical
policy differences belong to secondary actions. [T1v3](T1v3.md) · [REG](REG.md) · [K22](K22.md)

Freeze the native triage queue and keep the T1v3 asymmetric policy for safety and
illustrative loss. Report grouped native-score AP. For continuity report policy
AURC80 and full-coverage E-AURC on the legacy TRAIN-selected 90% confidence operating
point where defined. Also report the common probability-only ranking diagnostic
using calibrated probabilities, a 0.5 classification threshold, and max(p, 1−p)
confidence. The latter supplies a defined ranking diagnostic independent of
realized policy coverage. Brier and ten-bin ECE use calibrated probabilities.
Use missed-clear cost 10, false-flag cost 1 and referral cost 0.5, with perfect
referral resolution assumed. Use the same 2,000 paired whole-drug draws per horizon
and seed 20261127 for endpoints and contrasts. Keep the original safety interval
conditional on the observed clear roster. The acceptance checks are exact annual
queue capacity and defined endpoints. Report conditional auto-clear safety and
legacy coverage separately. [Criteria v3](../PLAN.md#confirmatory-criteria-v3-owner-approved-27-november-2026-supersedes-v2-endpoints)

The sealed schedule is set using annual Jan 1 cutoffs from 2017 and complete
follow-up by the pinned S0 observation end. Candidate cutoffs require an FDA
Orange Book edition within six calendar months with availability proven by the
cutoff. An independent data custodian supplies the blinded event history
projection to the eligibility gate. The gate only emits PASS or FAIL. The
FREEZE executor runs development only.

## H2 reconciliation

**PASS.** The merged-code crossover reproduced the two published H2 estimates
and both 95% interval endpoints within 1e-12. T1v3 used the pre-REG pipeline
based on `3f648223`. K22 used the post-REG pipeline based on `58f4f9ed`.
The sole pipeline difference between those bases was the REG challenge fix.
The same source manifests and pinned raw-file digests appear in both published
receipts. [Machine comparison](../../../loe-bench/data/FREEZE_reconciliation.json)

| REG application | M1 hits / 91 | M3 v1 hits / 91 | H2, pp [95% CI] | Change from pre-REG, pp |
| --- | ---: | ---: | ---: | ---: |
| Neither partition, T1v3 replay | 59 | 58 | −1.10 [−4.67, +3.33] | 0.00 |
| TRAIN only | 40 | 45 | +5.49 [−2.00, +11.25] | +6.59 |
| Validation only | 59 | 58 | −1.10 [−4.67, +3.33] | 0.00 |
| Both partitions, K22 v1 replay | 40 | 45 | +5.49 [−2.00, +11.25] | +6.59 |

At the 2010 training cutoff REG changed the challenge-missing feature on 11 of
547 rows and the v1 verdict on seven. It changed neither feature nor verdict on
the 1,083 validation rows. M1 lost 19 captured events and M3 v1 lost 13, which
increased the between-arm difference by six event rows. Roster, labels, dates,
base features and K07 breadth matched exactly across crossover partitions.
Both entrypoints used the same fitted M1 and M3 v1 native scores and the same
five-fold OOF sigmoid parameters. The two queue implementations agreed on
capacity and expected hits at the point and on all 2,000 matched PCG64 draws
in every stage. Both used seed 20261127 and fractional boundary ties.

Criteria v3 use the post-REG native-risk queue with graph v1. K22's fixed
0.05/0.5 thresholds affect its secondary decision loss. The freeze uses the
T1v3 inner-TRAIN asymmetric threshold selection. No additional model or queue
bug surfaced. The merged REG fix has a regression fixture for undated PIV
records. [REG test](../../../loe-bench/loe_bench/tests/test_e7_challenge.py)

## Frozen configuration

**FROZEN_FOR_PREREG.** Exact annual queue capacity and defined endpoints both
passed. This is a development freeze. It leaves test authorization to the owner.
The implementation pin is `f683017c4fb73aadd91bb97f3381f5dd9308c9ca`.
The configuration pins the S0, Orange Book, PIV and Rai manifests, raw input
digests and GSRS identity release. The NBER manifest is recorded as excluded
after K20 rejection. Tracked manifest hashes use LF bytes for reproducibility
across Git checkouts. [Frozen configuration](../../../loe-bench/data/FROZEN_CONFIG.json)

Both horizons train at 2010-01-01. Validation uses annual cutoffs in 2012–2015
for 12 months and 2013–2014 for 24 months. The sealed schedule admits annual
cutoffs in 2017–2025 and 2017–2024, respectively, from the pinned coverage
metadata and complete follow-up through 2026-11-27. Admission requires a fresh
availability-proven FDA ZIP for each cutoff and at least 50 distinct eligible
event drugs at 24 months. The independent gate verifies edition digests and
accepts a custodian's blinded deduplicated NME/ANDA history projection. It emits
one PASS or FAIL result. The executor did not create, receive or run that
projection. Synthetic checks exercised the threshold, time-window boundary
and binary output. [Gate script](../../../loe-bench/scripts/freeze_gate.py)

## Development results

**DEVELOPMENT_ONLY.** The 12-month panel had 2,161 rows, 90 event rows from 90
drugs and 430 queue slots. The 24-month panel had 1,083 rows, 91 events from
67 drugs and 215 slots. All 2,000 paired draws were defined at each horizon.
The JSON reports point estimates, paired 95% intervals, annual capacity
and tie audits, and policy actions. [Development report](../../../loe-bench/data/FREEZE_dev_report.json)

| Months | Arm | Recall | Queue precision | Distinct event-drug capture | AP | Loss per row | AURC80 | E-AURC | Brier | ECE |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 12 | B1 | 48.11% | 10.07% | 48.11% | .09189 | .65178 | .07772 | .07046 | .04025 | .00584 |
| 12 | M1 | 61.11% | 12.79% | 61.11% | .20050 | .51920 | .01162 | .01381 | .03829 | .01398 |
| 12 | M3 v1 | 61.11% | 12.79% | 61.11% | .18860 | .54998 | .01068 | .01306 | .03822 | .01709 |
| 24 | B1 | 39.65% | 16.78% | 46.39% | .17288 | .53786 | .02933 | .03432 | .07507 | .01797 |
| 24 | M1 | 43.96% | 18.60% | 47.76% | .21580 | .76223 | .02297 | .02832 | .07793 | .07562 |
| 24 | M3 v1 | 49.45% | 20.93% | 52.24% | .22189 | .80979 | .02272 | .02784 | .07782 | .08001 |

| Development contrast | Recall difference, pp [95% CI] | Point meets +10 pp |
| --- | ---: | --- |
| H1, 24m M3 v1 − B1 | +9.80 [+0.14, +19.65] | No |
| H2, 24m M3 v1 − M1 | +5.49 [−2.00, +11.25] | No |
| H3, 12m M3 v1 − B1 | +13.00 [+3.27, +23.17] | Yes |

Auto-clear safety failed for all five estimable arm-horizons. B1 at 24 months
cleared zero cases and was unevaluable. The missed/cleared counts for B1, M1
and M3 were 10/67, 3/293 and 3/397 at 12 months and 0/0, 0/25 and 1/38 at
24 months. The queue is the recommended workflow. All other cases stay with
the evaluator's normal process.

## Reproduction

Run from `loe-bench/` using Python 3.12.10, NumPy 2.5.4 and the pinned local
inputs. The canonical run hashes LF JSON bytes.

```powershell
rtk proxy python -B scripts/freeze_reconcile.py
rtk proxy python -B scripts/freeze_run.py
rtk proxy python -B -m unittest discover -s loe_bench/tests -t .
```

**PASS:** LOE-Bench unittest ran 166 tests with exit 0. The aggregate audit
checked the code pin, source manifest digests, queue and policy arithmetic,
H2 parity and the closed seal. Root pytest ran with `--tb=short -p
no:cacheprovider` and a fresh external temporary directory. It exited 1 with
2,760 passed, 50 skipped, one xfailed and the eight accepted pre-existing
SACR r2/r3 supervisor budget failures. [Repository test policy](../../../AGENTS.md)

**PASS:** Two independent canonical runs emitted identical LF SHA-256 digests.
An independent read of the final bytes matched both runs.

| Artifact | SHA-256 |
| --- | --- |
| Development report | `da0532932654e316ce4276498c49279214c31822aaa38fdcd8a30d0a930acefa` |
| Frozen configuration | `d40119189b9e3b3b319f16449ac672766d46de2272dd9579eadaa8d23eb27c39` |
| Reconciliation | `d268f3616586207e0d2bd3be41e2733803ae55769fa61609692af62317d9c01c` |

## Failures and limitations

- The PowerShell SHA wrapper could not resolve `Get-FileHash`. The runners
  emitted their own SHA-256 digests, and Python `hashlib` computed a separate
  digest over the output bytes.
- The LOE-Bench suite emitted existing Purple Book unclosed-file warnings.
- The legacy 90%-target policy did not reach 80% coverage for M1 or M3 at 24
  months. No legacy arm reached the full coverage required for full E-AURC.
  The table uses the complete probability-only diagnostic specified above.
- The intervals hold the development fits fixed. The operational loss assumes
  illustrative costs and perfect referral adjudication. The frozen development
  training roster is a single cutoff. The H2 sign change reflects sensitivity
  to the challenge input and does not establish incremental performance.
- The post-2023 sensitivity cohort and Track B were outside this development
  run. The C′ gate and confirmatory tests remain NOT_RUN, and T4c alpha
  disposition is pending. The preregistration lock and authorization variable
  were absent throughout the development runs.

## Next action

Main planner reviews this receipt and the machine artifacts, then adopts the
freeze or records requested corrections. Before preregistration, settle the T4c
alpha rule and arrange the independent C′ gate through the data custodian.
The owner controls preregistration and the subsequent seal release.
