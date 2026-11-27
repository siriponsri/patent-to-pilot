# DEVX | Fixed-order development trials

## Protocol recorded before scoring

Replay merged E7b at `c4281994` on its NME cohort using the same B1, M2, evidence, thresholds, five SHA-256 drug folds, and AURC80 tied-prefix rule. Carry forward the E7b-selected L2 of 100 for each trained arm and horizon. Compare the recreated baseline with the tracked E7b metrics before proceeding. Preserve the test seal. Decode approval outcomes only through 2016-01-01 and keep all development label windows strictly before 2017-01-01, with TRAIN windows ending strictly before validation starts. Use pinned local inputs only.

Run one fixed candidate at a time in order K07, K09, K10, K08, K06. Each comparison has two configurations per M1 and M3, current and candidate. Count ten comparison entries, five new configurations and one initial baseline per arm per horizon. Reuse the current configuration's predictions. Report B1 and M2 as unchanged reference arms. Robustness refits are accounted for separately.

| ID | Candidate |
| --- | --- |
| K07 | Use the FIX2c NDA links from the same fresh, availability-proven historical edition. Add distinct count of strength within form and route and distinct count of form and route pairs, with separate missing/partial flags. Collapse duplicates, normalize whitespace, case and decimal notation, and preserve component order and unit labels. Count only timely dated approvals or the explicit pre-1982 approval marker. Exclude conflicting presentations for the same product identifier and flag their missingness. Keep prior NDA count and oral/injectable indicators. |
| K09 | Use pooled logistic hazards with one interval intercept and fixed covariates at the landmark, including the 12-month graph indicators for M3 and TRAIN 12-month B1 logit for both. Use one unit of likelihood weight per observed at-risk landmark interval. Retain a completed event-free interval before censoring and an observed event inside an otherwise incomplete interval. Enter interval two only if still at risk. Respect the strict training maturity boundary even if this leaves only interval one observable, as it does on the primary 12-month split. Compute 24-month raw risk as one minus the product of conditional survival probabilities. Calibrate each evaluated horizon separately and use its original action policy. |
| K10 | Replace the sigmoid with one monotone beta calibration map, logit risk = intercept + a log(p) − b log(1−p), a,b ≥ 0. Use E7b folds, clipping, standardized inputs, L2 = 1 and the same 300-epoch, 0.3-step logistic loss optimizer with slope projection. Use the identity map for single-class or empty calibration sets. |
| K08 | Fit logistic error risk on the emitted-class confidence and absolute disagreement with the TRAIN age probability for that same action, using defaults L2 = 1, 300 epochs and step 0.3. Within each outer drug fold, form selector training examples with another held-drug fold. Inner training excludes both held folds from the age/model fits and the calibration fit. Restrict calibration and selector inputs to development labels. Fit only on answered actions. Apply the selector to the previous pipeline's fixed actions and probabilities, using an outer-held-drug TRAIN age table for scoring disagreement. Use original ranking for empty or single-class selector training. |
| K06 | Compare a zero score discount with 0.05 once per answered row, applied after any earlier adopted selector. For M3, enumerate binary completions of UNKNOWN leaves and flag a leaf when flipping only that leaf can alter the root. For M1, apply the same discount if either raw expiration clock or the challenge is missing, using the same snapshot and challenge assignment. Retain probabilities and actions, and do not clip ranking scores. |

Adopt only if the candidate's M3−B1 AURC80 contrast at 24 months decreases by at least 0.0010 relative to current, its 12-month contrast increases by at most 0.0010, and the M1−B1 contrast at 24 months increases by at most 0.0010. Apply the M1 guard to every trial, including the matched K06 change. Missing AURC80 rejects adoption. Report each arm's AURC80, Brier, 10-bin ECE and achieved coverage. Report the three contrasts M3−B1, M3−M1 and M1−B1 for both configurations, plus each contrast's candidate-minus-current change and the within-M3 and within-M1 changes. Use the same 2,000 paired whole-drug draws, seed 20261127, 95% percentile endpoints and coverage rules throughout. Report invalid draws. These comparisons condition on fitted predictions and development selection. The criteria v2 practical effect threshold is −0.010 against B1 and is distinct from the DEVX adoption gate.

For each adopted change only, compare its previous and candidate pipelines on the forward development split. At 12 months, use TRAIN 2010–2011 and validation 2013–2014. At 24 months, use TRAIN 2010–2011 and validation 2014. The 2011 window matures in 2013, so 2014 is the first eligible validation cutoff and the last with a 24-month window ending before the seal. Both checks overlap the primary validation cohort. Report the sign of the 24- and 12-month M3−B1 changes and keep the primary adoption decision.

## Result

**PASS for development execution. Adopt K07 only.** The [machine results](../../../loe-bench/data/DEVX_results.json) contain each current and candidate arm, paired contrasts and changes, selector fold diagnostics, the robustness comparison, configuration counts and source digests. Each interval below is the 95% percentile interval from 2,000 paired whole-drug draws. All reported point estimates and draws reached the required coverage.

| Trial | Change in M3−B1 at 24 months | Change in M3−B1 at 12 months | Change in M1−B1 at 24 months | Decision |
| --- | ---: | ---: | ---: | --- |
| K07 | −0.003205 [−0.008333, −0.000292] | −0.000895 [−0.001691, −0.000216] | −0.001933 [−0.003848, −0.000242] | Adopt |
| K09 | +0.003623 [+0.000221, +0.007718] | −0.000966 [−0.002034, −0.000043] | +0.002208 [−0.000066, +0.005055] | Reject. Missed the 24-month target and M1 guard. |
| K10 | +0.000422 [+0.000001, +0.001160] | +0.000175 [+0.000000, +0.000422] | +0.000870 [+0.000083, +0.002267] | Reject. Missed the 24-month target. |
| K08 | +0.003146 [−0.002528, +0.009110] | +0.004435 [+0.001609, +0.007993] | +0.002056 [−0.002388, +0.006708] | Reject. Missed all three gates. |
| K06 | +0.003302 [−0.000736, +0.010225] | +0.001261 [−0.001649, +0.004668] | −0.000075 [−0.000210, −0.000010] | Reject. Missed both M3 gates. |

The final flags are K07 enabled and K09, K10, K08 and K06 disabled. Each trained arm had ten comparison entries per horizon, covering six distinct configurations including E7b. Those are 20 entries and 12 distinct horizon-specific evaluations across both horizons. K07 used two additional refits per horizon on the forward split. B1 and M2 retained their reference definitions.

| Horizon | Arm | AURC80 | Brier | ECE | Coverage |
| --- | --- | ---: | ---: | ---: | ---: |
| 12 | B1 | 0.018575 | 0.039073 | 0.005471 | 100.00% |
| 12 | M1 | 0.011847 | 0.036743 | 0.007145 | 98.70% |
| 12 | M2 | 0.034704 | 0.039982 | 0.003845 | 100.00% |
| 12 | M3 | 0.010917 | 0.036985 | 0.007901 | 98.75% |
| 24 | B1 | 0.029330 | 0.073047 | 0.007294 | 100.00% |
| 24 | M1 | 0.017761 | 0.067031 | 0.025929 | 93.07% |
| 24 | M2 | 0.067111 | 0.075511 | 0.009583 | 97.14% |
| 24 | M3 | 0.017438 | 0.066504 | 0.023820 | 93.54% |

| Retained pipeline | M3−B1 | M3−M1 | M1−B1 |
| --- | ---: | ---: | ---: |
| 12 months | −0.007657 [−0.013473, −0.002347] | −0.000929 [−0.001902, +0.000157] | −0.006728 [−0.012684, −0.001042] |
| 24 months | −0.011892 [−0.021583, −0.003535] | −0.000323 [−0.001330, +0.000791] | −0.011570 [−0.020856, −0.003500] |

The 24-month M3−B1 point estimate reaches the criteria v2 practical threshold on primary development. Both M3−M1 intervals include zero. At 24 months K07 increased M3 Brier from 0.065436 to 0.066504 and ECE from 0.015272 to 0.023820. [E7b baseline](E7b.md) · [Criteria v2](../PLAN.md#confirmatory-criteria-v2-main-planner-proposal-owner-approved-27-november-2026)

| K07 forward split | Validation rows | Drug / event clusters | Change in M3−B1 | Direction held |
| --- | ---: | ---: | ---: | --- |
| 12 months, 2013–2014 | 1,083 | 561 / 41 | +0.000060 [−0.000183, +0.000330] | No |
| 24 months, 2014 | 544 | 544 / 50 | −0.002433 [−0.006082, −0.000488] | Yes |

## Evidence and verification

From `loe-bench/` on Python 3.12.10 and NumPy 2.5.4:

```powershell
python -B scripts/devx_run.py
python -B -m unittest discover -s loe_bench/tests -t .
```

Both commands exited 0. The unittest suite passed 130 tests, with existing Purple Book file-handle warnings. The replay matched E7b row, cluster and verdict counts, and matched all arm metrics and paired bootstrap intervals within 1e-12 before comparing any candidate. The primary validation cohorts contain 2,161 rows and 90 event clusters at 12 months, and 1,083 rows and 67 event clusters at 24 months. The result audit verified the protocol hash, cumulative flags, contrasts, draw counts and the unchanged Brier, ECE and coverage for the two ranking-only trials. The seal lock and environment variable were absent. All runs used local CPU.

From the repository root, `python -B -m pytest --tb=short --basetemp C:/Users/User/AppData/Local/Temp/ptp-devx-a5c7-01 -p no:cacheprovider` exited 1. It reported 2,760 passed, 50 skipped, one xfailed and the eight accepted SACR r2/r3 supervisor budget failures. [Repository test policy](../../../AGENTS.md)

The result SHA-256 is `20976edcb567a8961e26a9b8da3b967f53c947b62b9727d7c4ed367e8e1196e8`. The input digests identify the pinned S0 and GSRS releases and the historical Orange Book, PIV and court manifests. K07 inherits the FIX2c NDA product match and the E7b archive freshness proof. Its source columns in `products.txt` are `DF;Route`, `Strength` and `Approval_Date`, with application and product numbers identifying rows. [FIX2c linkage and locators](FIX2c.md#evidence) · [Technique definitions](../TECHNIQUE-SCAN.md)

## Failures and limitations

- Two initial baseline checks stopped before candidate scoring. Limiting the Orange Book identity source to NDA rows left four primary 12-month validation verdicts different from E7b. Adding early ANDA Orange Book rows restored historical product evidence but left a verdict discrepancy at each primary 12-month cutoff, including TRAIN. The successful replay also preserved undated ANDA product ingredients for identity resolution after stripping submission objects. Its outcome reader admits development final original approvals through 2016-01-01. Later ANDA product approval dates are masked before decoding, and the historical application-type index reads ANDA application identifiers only.
- In K09, the first interval supplies 547 primary 12-month training observations. The second interval cannot supply a completed event-free observation because its end meets the validation boundary. It supplies 21 observed events before that boundary under the declared censoring rule. This clarifies the protocol wording about the observable interval and may distort pooled slopes in this fold. The primary 24-month fit supplies 522 second-year observations.
- Both forward checks overlap primary validation. Calibration and selection use grouped development data and intervals condition on the fitted predictions. K08 uses nested drug exclusions for selector training and a held-drug age table for application. The emitted actions and probabilities remain the inherited cross-calibrated pipeline outputs, which can use earlier records for the same drug during primary TRAIN fitting.
- K07 counts archived presentations with observable strength, form and route at the cutoff. Partial or missing strength is flagged on 94 primary 12-month rows and 55 primary 24-month rows, including unavailable or unlinked evidence. Documentary strength strings retain unit labels and combination order. Equivalent expressions can therefore count separately. The FDA approval outcome is distinct from commercial entry.

## Next action

The main planner can review K07 and record the five dispositions in the technique ledger. Carry the 12-month forward result and the 24-month calibration trade-off into any preregistration review. The protected test remains sealed.
