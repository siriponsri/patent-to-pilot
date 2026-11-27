# T4b | Development-validated power simulation

## Result

**PASS for variance calibration against the seal-preserving development replay.** All six independent simulated SDs are within 25% of the recalculated empirical bootstrap SDs. The exact reference null gives H1 type-I of 2.81% [2.53%, 3.12%] at α = 0.025. The prespecified H1 α = 0.020 gives 2.24% [1.99%, 2.52%]. The simulation favors α = 0.020 for main-planner review before preregistration. Its interval still includes rates above 2.5%.

### Validation

Empirical SDs use 2,000 valid paired bootstrap draws. Fitted SDs use 2,500 independent simulated datasets per horizon at the fixed validation structure. The before column uses the E7b-derived residual correlation fit before T4b's noise recalibration.

| Horizon | Contrast | Empirical SD | Simulated SD | SD ratio before calibration | Fitted SD ratio |
| --- | --- | ---: | ---: | ---: | ---: |
| 24 months | M3 − B1 | 0.005096 | 0.004619 | 0.716 | 0.906 |
| 24 months | M3 − M1 | 0.001820 | 0.001862 | 0.676 | 1.023 |
| 24 months | M1 − B1 | 0.004340 | 0.004500 | 0.784 | 1.037 |
| 12 months | M3 − B1 | 0.002810 | 0.002813 | 0.834 | 1.001 |
| 12 months | M3 − M1 | 0.000623 | 0.000647 | 1.089 | 1.039 |
| 12 months | M1 − B1 | 0.002892 | 0.002870 | 0.831 | 0.992 |

| Horizon | Latent B1 correlation with each regulatory arm | Latent M1–M3 correlation | Within-drug correlation | Error score scale |
| --- | ---: | ---: | ---: | ---: |
| 24 months | 0.15 | 0.85 | 0.3364 | 1.00 |
| 12 months | 0.15 | 0.96 | 0.3261 | 1.00 |

### Power

All mains used 5,000 synthetic datasets. At an imposed ΔAURC80 of −0.010 for each step, every run rejected H1, H2 and H3 at both H1 alpha settings. All power entries of 100% correspond to 5,000/5,000 and a 95% Wilson interval of [99.92%, 100%]. H1 conditional and overall power are identical because H1 opens the sequence. The MDE values are absolute ΔAURC80 magnitudes from the location-shift estimate.

| Scenario | 24-month event clusters | 24-month event-row prevalence | H1 power | H2 conditional / overall | H3 conditional / overall | Unevaluable H1 / H2 / H3 | H1 MDE at α 0.025 / 0.020 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sparse | 30 | 0.56% | 100% | 100% / 100% | 100% / 100% | 0% / 0% / 0% | 0.00456 / 0.00473 |
| Event grid | 50 | 0.93% | 100% | 100% / 100% | 100% / 100% | 0% / 0% / 0% | 0.00420 / 0.00434 |
| Reference | 75 | 1.42% | 100% | 100% / 100% | 100% / 100% | 0% / 0% / 0% | 0.00394 / 0.00407 |
| Event grid | 100 | 1.90% | 100% | 100% / 100% | 100% / 100% | 0% / 0% / 0% | 0.00375 / 0.00388 |
| Event grid | 150 | 2.92% | 100% | 100% / 100% | 100% / 100% | 0% / 0% / 0% | 0.00377 / 0.00390 |
| Downward drift | 53 | 1.00% | 100% | 100% / 100% | 100% / 100% | 0% / 0% / 0% | 0.00431 / 0.00444 |
| Upward drift | 97 | 1.84% | 100% | 100% / 100% | 100% / 100% | 0% / 0% / 0% | 0.00377 / 0.00392 |
| Young histories | 75 | 1.44% | 100% | 100% / 100% | 100% / 100% | 0% / 0% / 0% | 0.00396 / 0.00409 |
| Latent B1 correlation 0.25 | 75 | 1.42% | 100% | 100% / 100% | 100% / 100% | 0% / 0% / 0% | 0.00394 / 0.00407 |
| Latent B1 correlation 0.90 | 75 | 1.41% | 100% | 100% / 100% | 100% / 100% | 0% / 0% / 0% | 0.00356 / 0.00369 |

H1 clears 80% power at 30 event clusters, the lowest count examined. This is a bound on the simulated grid. C′ still requires at least 50 actual event clusters and fresh, availability-proven Orange Book editions. The candidate inventory counts 10,004 rows and 1,362 clusters at 24 months and 11,398 rows and 1,394 clusters at 12 months, before unknown generic-entry exclusions. Independent large-population checks met the 0.0006 tolerance in every null and useful-effect scenario. At 30 and 75 clusters, 800 matched runs per scenario gave identical decisions with 199 and 2,000 draws at both H1 alpha settings. This comparison covers the useful effect, where all runs rejected.

| Absolute H1 effect target at 75 clusters | H1 power at α 0.025 | H1 power at α 0.020 |
| ---: | ---: | ---: |
| 0.00294 | 69.00% | 65.80% |
| 0.00307 | 72.52% | 68.96% |
| 0.00494 | 99.30% | 98.70% |
| 0.00507 | 99.14% | 98.86% |

The direct intervention brackets 80% power between target magnitudes 0.00307 and 0.00494 at both alpha settings. It uses 5,000 datasets per target and 199 draws. This supports the order of magnitude of the reference location-shift estimate.

### Type-I error

| H1 one-sided alpha | Global-null rejections at 75 event clusters | Type-I rate | 95% Monte Carlo CI |
| ---: | ---: | ---: | ---: |
| 0.025 | 337 / 12,000 | 2.81% | 2.53% to 3.12% |
| 0.020 | 269 / 12,000 | 2.24% | 1.99% to 2.52% |

Both alpha settings use the same null datasets and 2,000 paired whole-drug resamples per dataset. The nominal interval is above 2.5% and its upper bound exceeds the 3.0% target. With α = 0.020, the upper bound is below 3.0% and H1 retains full measured power at the −0.010 alternative. H2 and H3 keep α = 0.025. This check measures H1 and global-null family-wise error at the reference setting. It leaves mixed-null behavior and other scenario nulls unmeasured.

## Protocol

Compare the three simulated AURC80 contrast SDs at each of the two E7b validation structures with 2,000 exact paired cluster bootstrap draws from the development predictions. Keep the cutoff, cluster IDs, labels and prevalence fixed in the validation simulation. Use an independent stream for verification and accept ratios from 0.75 to 1.25. Fit the error-ranking tilts to the observed arm AURC80 values. Select score-correlation, error-dispersion and within-drug parameters by minimizing the largest absolute log SD ratio on a separate development simulation stream. Record failed calibration or replay checks.

For test-sized simulations, use annual NDA-only roster entry counts and synthetic event timing. Evaluate the event-cluster grid 30, 50, 75, 100 and 150, the T4 prevalence-drift counts 53 and 97, young histories, and low and high latent B1–regulatory-arm correlations. The simultaneous useful-effect target is −0.010 for H1, H2 and H3. The fixed sequence and AURC80 coverage gate follow criteria v2. The ordinary power grid uses 5,000 replicates per scenario and 199 paired whole-drug draws. Compare matched decisions against 2,000 draws at the reference design and at 30 event clusters. Estimate H1 type-I under the reference global null with 12,000 replicates at 2,000 draws. Prespecify one-sided α = 0.020 for H1 as a sensitivity, leaving H2 and H3 at α = 0.025. Use Wilson 95% intervals over simulation replicates.

Estimate the minimum event count on the measured grid. Compute the 80%-power effect by shifting the bootstrap limit distribution from the −0.010 run and check the reference estimate against a direct, separately seeded rank intervention. Record whether the target can be attained under the fitted score generator. [Criteria v2](../PLAN.md#confirmatory-criteria-v2-main-planner-proposal-owner-approved-27-november-2026) · [Morris, White and Crowther, 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/)

## Development replay and source boundary

Use merged `t2.evaluate` with challenge features enabled and the E7 and E7b development witness inventories. Replay the witnessed challenge state as of each cutoff. Recompute the three empirical paired SDs and percentile intervals with the same `random.Random` whole-drug draw stream and exact confidence ties. The binned count evaluator agrees with the reference bootstrap on the fixture at both reported percentiles, including invalid draws.

| Horizon | Validation cutoffs | Rows | Drug clusters | Event clusters | Event rows | Row prevalence |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 24 months | 2013 and 2014 | 1,083 | 561 | 67 | 91 | 8.40% |
| 12 months | 2012 through 2015 | 2,161 | 609 | 90 | 90 | 4.16% |

The projected replay and E7b agree on cutoff row counts, total drug and event cluster counts, and B1 AURC80. The restricted composition and evidence replay changes a few graph verdicts and the M1 and M3 predictions. At 24 months, the projected M3−B1 estimate is −0.009158 with bootstrap CI [−0.019634, +0.000885]. E7b reports −0.008688 [−0.019380, +0.001702]. At 12 months, the projected result is −0.007157 [−0.012726, −0.001915]. E7b reports −0.006762 [−0.012407, −0.001366]. The machine output records the corresponding comparison for all six contrasts. Exact reproduction of the original E7b prediction vectors and their empirical SD is **NOT ESTABLISHED**. The variance gate applies to the seal-preserving projected replay. [E7b](E7b.md) · [E7b development summary](../../../loe-bench/data/E7b_dev_summary.json)

The Drugs@FDA reader selects the earliest original final ANDA approval through 2016-01-01 from byte slices before invoking the JSON decoder. A record without an eligible approval never reaches the decoder. It also excludes dated product rows later than the admitted original approval and selects only resolution fields from admitted rows. The Orange Book reader filters grouped products by application type and dates before decoding. It uses the prior-to-1982 flag as evidence for otherwise undated early products and excludes the 2020-plus ANDA file entirely. The mixed input digests cover their pinned bytes. NDA-only candidate counts run through a separate reader that cannot open ANDA inputs. The replay uses only development Orange Book editions and challenge witnesses. The fixtures place a decoder guard around mixed records and a future-only application.

## Generator and inference

T4 used its earlier matched arm fit and 120 bootstrap draws. It checked population effects and left sampling variance against development unmeasured. T4b fits confidence age effects, marginal referral, and a common conditional call process from the projected E7b predictions. It recalibrates correlated arm ranks, within-drug rank dependence and error-specific score dispersion. Gaussian cluster and row draws share noise across the two synthetic horizons. A non-reference correlation setting changes B1's correlations with M1 and M3. It preserves the M1–M3 correlation where positive definiteness permits.

The test scenarios randomly assign development-derived age and event-lag templates to the counted NDA-only entry cohorts. The synthetic first event stops later at-risk rows and gives nested horizon labels. These candidate cohort sizes include drugs that could be ineligible because of earlier ANDA approval. Both drift scenarios change event-cluster counts and consequently row prevalence. For each scenario, the null uses identical latent risk-ranking margins for all three arms. The alternative changes the confidence ranking of M3 errors while keeping its referral rule fixed. If needed, the fit raises the synthetic comparator AURC80 to 0.013 so there is sufficient risk headroom to express a 0.010 improvement. These are imposed alternatives with scope defined by the simulation.

## Reproduction

Run the command from the repository root with the pinned local inputs, Python 3.12 and NumPy installed.

```powershell
python -B loe-bench/scripts/t4_power.py --workers 8
```

`--prepare-only` prints the development replay audit. The full command writes [T4b_power.json](../../../loe-bench/data/T4b_power.json). From `loe-bench/`, `python -B -m unittest discover -s loe_bench/tests -t .` passed 128 tests with the existing Purple Book file-handle warnings. T4b fixtures cover the pre-decode filter, reference bootstrap agreement, a one-contrast variance failure, fixed development structure, generator determinism, roster entry and matched 2,000-draw limits.

The repository suite ran with `python -B -m pytest --tb=short --basetemp C:/Users/User/AppData/Local/Temp/ptp-t4b-97c1f0a8 -p no:cacheprovider`. It returned 2,760 passed, 50 skipped, one xfailed and the eight accepted SACR r2/r3 supervisor budget failures, exit 1. [Repository test policy](../../../AGENTS.md)

The simulation exited 0 in 1,474.3 seconds with Python 3.12.10, NumPy 2.5.4 and eight local workers. Its JSON SHA-256 is `24b3798cfeedbd36d0c7535014b8fc07dc363403c342a11db9f47340d7604f21`. The seal guard file was unchanged. The preregistration lock and authorization variable were absent. [Simulation output](../../../loe-bench/data/T4b_power.json)

## Failures and limitations

- The first two guarded attempts to replay E7b's original raw challenge linkage stopped on its inherited equality check at the 2011 cutoff. The projected cohort had the same total of 534 rows. One leaf was FALSE where the original aggregate counted TRUE. The finalized replay uses the published dated E7b witness inventory and E7's per-cutoff challenge witnesses. Both initial runs stopped during development assembly. The seal and input boundary remained in place.
- Exact original E7b arm vectors are unavailable from its summary and the finalized projection makes small changes to M1 and M3. The reported empirical SDs come from 2,000 draws on the current, projected development replay. They have a similar scale to the published E7b intervals. The fit conditions on a fixed observed outcome panel and targets an unstratified cluster bootstrap SD. The calibrated noise can absorb uncertainty from that difference in conditioning.
- The generator uses a common conditional call process and 20 confidence bins. It calibrates contrast SDs on two development structures. It simplifies the actual model actions, model selection, ranking, tie distributions and transport to later eras. The 12-month and 24-month validation calibrations are marginal checks for each horizon. The generator shares event histories and latent draws across horizons for the simulated fixed sequence.
- Scenario power, event-count bounds and MDE condition on the NDA-only roster, synthetic event prevalence and imposed rankings. The simulation supplies no C′ eligibility measurement. A joint −0.010 improvement across all three steps exceeds the small graph increment seen in E7b. Exact null coverage is measured for the reference scenario only.

## Next action

The main planner can review the projected E7b variance evidence and consider H1 α = 0.020 for preregistration. Keep the 50-event and fresh-edition gates. Treat the reported power as conditional on the synthetic comparator's risk headroom and the imposed effect. If exact agreement with the original E7b vectors is required, obtain a development-only prediction export with approved provenance before rerunning the empirical SD calculation.
