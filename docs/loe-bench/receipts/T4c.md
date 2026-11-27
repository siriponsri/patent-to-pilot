# T4c | Review-queue recall power

**PASS for the development variance gate.** All six ratios were 0.754–1.229. **H1 power at +10 points was 49.96% at the 75-cluster reference.** The lowest tested size with a point estimate of at least 80% was 150 event clusters, with 80.58% H1 power and a 95% Monte Carlo interval of [79.46%, 81.65%]. The reference H1 MDE was approximately 14.26 recall points. `RULE_SELECTED_ALPHA = 0.025` under the predeclared, within-B1-tie H1 null. All results use development or synthetic inputs. The test seal stayed closed.

## Protocol before simulation

Apply the [owner-approved criteria v3](../PLAN.md#confirmatory-criteria-v3-owner-approved-27-november-2026-supersedes-v2-endpoints) and [CP4 rerun specification](../CP4-METRIC-REDESIGN.md#t4-rerun-and-t5-decision). Base revision `3f6482237fbc03d3a174bf0c09d1d33b0208dccb`.

Replay the native B1, M1 and M3 K07 predictors on the embargoed primary development split. Use the T4b byte-level ANDA and Orange Book projections for all outcome readers. Count the retrospective candidate frame from dated NDA/NME features using the separate T4b reader. Fit annual first-approval hazards on TRAIN for the B1 native scores and tie levels. Resample 2,000 paired whole-drug draws at each development horizon. Compare all six empirical contrast SDs with 2,500 independently seeded simulations conditional on the original development panel. Accept ratios in [0.75, 1.25]. Fit conditional age, relative year and outcome rank distributions, and residual cross-arm and within-drug dependence. Search the declared correlation grid if necessary, keeping the variance fit and verification streams separate. Publish annual capture, precision, boundary ties and paired event-capture discordance.

Reuse T4b's synthetic timing, horizons, at-risk histories, first-event stopping and NDA-only arrival counts. Draw shared drug and row effects across horizons. The B1 TRAIN age-clock values remain fixed. Fit score shifts using exact queue inclusion breakpoints across 2,500 synthetic panels per scenario. Verify targets independently on 5,000 panels with an absolute tolerance of 0.005 recall. Use exchangeable M1 and M3 rank margins for a zero H2 contrast. An exact H1 or H3 null uses event-independent random order within the B1 score blocks. The M3 queue can therefore differ within boundary ties while its expected capture conditional on the history equals B1's fractional capture. Verify realized null differences independently as a check on this implementation.

The main scenarios target H1/H2/H3 of +0.10/+0.02/+0.10. The 75-cluster reference also varies H1 over +0.05, +0.075, +0.10, +0.15, +0.20, +0.25 and +0.30, and H2 over 0, +0.02 and +0.05 at H1 = +0.10. Each power cell uses 5,000 datasets. Report the first 80% crossing as the bracketing measured effects and a linear interpolation. Report the lowest grid event count with at least 80% H1 power at the useful effect. The sample-size grid gives a conditional scenario decision.

At each cutoff reapply `floor(N/5)` to the bootstrap row count and fractionally allocate the boundary tie. Pool event captures and event denominators across cutoffs. The fixed sequence is M3−B1 at 24 months, M3−M1 at 24 months and M3−B1 at 12 months. Use the empirical lower order statistic at zero-based index `floor(alpha × draws)`. Stop on a bound at or below zero or any undefined replicate. Report marginal, reached-step conditional and sequence rejection, with Wilson 95% Monte Carlo intervals. A 400-draw power approximation requires a matched comparison with 2,000 draws on 400 datasets each at 30 clusters with +0.10 and at 75 clusters with +0.075 and +0.20. The absolute marginal rejection difference must be at most 3.5 points and decision disagreement at most 10%, with identical evaluability at each step and both alpha values. Use 2,000 draws if any check fails.

At the 75-cluster reference, use 12,000 datasets and 2,000 paired draws to check H1 at one-sided α = 0.025. Select 0.025 if its Wilson 95% upper limit is at most 2.5%. Otherwise select 0.020 and independently rerun with the same counts. Apply the selected alpha at every reached step. Estimate familywise error under the global null and under separate mixed nulls for H2 and H3.

## Development variance gate

**PASS, DEVELOPMENT_ONLY.** The 24-month panel has 1,083 rows, 91 event rows and 67 event drugs among 561 drugs. The 12-month panel has 2,161 rows and 90 event drugs among 609 drugs. The bootstrap produced 2,000 valid replicates at each horizon. All six verification ratios are in the declared interval.

| Horizon | Contrast | Empirical SD | Simulated SD | Ratio |
| --- | --- | ---: | ---: | ---: |
| 24 months | M3−B1 | 0.055497 | 0.043296 | 0.780 |
| 24 months | M3−M1 | 0.019976 | 0.024545 | 1.229 |
| 24 months | M1−B1 | 0.056692 | 0.043517 | 0.768 |
| 12 months | M3−B1 | 0.052063 | 0.039351 | 0.756 |
| 12 months | M3−M1 | 0.019263 | 0.022179 | 1.151 |
| 12 months | M1−B1 | 0.051494 | 0.038805 | 0.754 |

The selected M1–M3 Gaussian residual correlations were 0.96697 at 24 months and 0.97301 at 12 months. Within-drug correlations were 0.8 for both horizons. The machine output records the candidate grid and failed independent attempts, per-arm conditional rank parameters, native age-clock values and per-cutoff checks. On the 12-month panel the B1 boundary split a 27-row tie in 2013 and a 30-row tie in 2015. M3's empirical versus simulated precision at the 2013 cutoff was 9.35% versus 11.60%. Both results retain 107 slots and 17 event rows at that cutoff. The replication checks pooled variance and shows visible differences in some annual captures.

## Power at the selected alpha

Each row below uses 5,000 datasets. The main cells target H1/H2/H3 recall gains of +10/+2/+10 points. Independent population checks met the 0.005 recall tolerance throughout. In three matched checks with 400 datasets each, 400 inner draws differed from 2,000 draws by at most 1.75 percentage points in marginal rejection and 5.5% in paired decisions. Evaluability agreed in each comparison. All 18 power cells had zero unevaluable datasets at all steps. The [machine output](../../../loe-bench/data/T4c_power.json) includes Wilson intervals, counts, denominators, marginal and reached-step rates for both alpha values.

| Scenario | Event drugs | H1 power [95% MC CI] | H2 conditional / sequence | H3 conditional / full sequence |
| --- | ---: | ---: | ---: | ---: |
| Event grid | 30 | 24.62% [23.45%, 25.83%] | 2.44% / 0.60% | 50.00% / 0.30% |
| Event grid | 50 | 36.76% [35.43%, 38.11%] | 5.55% / 2.04% | 54.90% / 1.12% |
| Reference | 75 | 49.96% [48.57%, 51.35%] | 7.89% / 3.94% | 60.91% / 2.40% |
| Event grid | 100 | 64.32% [62.98%, 65.64%] | 10.32% / 6.64% | 65.06% / 4.32% |
| Event grid | 150 | 80.58% [79.46%, 81.65%] | 16.88% / 13.60% | 79.56% / 10.82% |
| Downward drift | 53 | 36.38% [35.06%, 37.72%] | 7.04% / 2.56% | 53.91% / 1.38% |
| Upward drift | 97 | 62.44% [61.09%, 63.77%] | 10.35% / 6.46% | 65.33% / 4.22% |
| Adverse age mix | 75 | 66.16% [64.84%, 67.46%] | 10.16% / 6.72% | 68.75% / 4.62% |
| Weaker cross-arm correlation | 75 | 38.12% [36.78%, 39.47%] | 9.18% / 3.50% | 66.86% / 2.34% |
| Stronger cross-arm correlation | 75 | 72.12% [70.86%, 73.35%] | 5.99% / 4.32% | 78.24% / 3.38% |

The adverse age mix restricts starting ages to five years or less and keeps event histories that can reach age five at entry. In this generator it increases H1 power. For the weaker and stronger scenarios, the M1–M3 residual correlation is 0.25 and 0.995, with B1 rank-loading adjustments of −1.5 and +2.5 respectively. The resulting mean 24-month B1–M3 score correlations are 0.439, 0.694 and 0.822 in the weaker, reference and stronger scenarios.

| H1 target at 75 event drugs | Verified H1 gain | H1 power [95% MC CI] | H2 sequence | Full sequence |
| ---: | ---: | ---: | ---: | ---: |
| +5.0 pp | +4.95 pp | 15.58% [14.60%, 16.61%] | 1.48% | 1.18% |
| +7.5 pp | +7.46 pp | 31.28% [30.01%, 32.58%] | 2.70% | 1.96% |
| +10.0 pp | +9.95 pp | 49.96% [48.57%, 51.35%] | 3.94% | 2.40% |
| +15.0 pp | +14.91 pp | 84.52% [83.49%, 85.50%] | 5.86% | 2.58% |
| +20.0 pp | +19.95 pp | 98.48% [98.10%, 98.78%] | 7.18% | 3.10% |
| +25.0 pp | +24.99 pp | 100.00% [99.92%, 100.00%] | 8.52% | 3.42% |
| +30.0 pp | +29.99 pp | 100.00% [99.92%, 100.00%] | 8.66% | 3.34% |

The 80% crossing lies between verified H1 effects of +9.95 and +14.91 points. Linear interpolation gives +14.26 points at 75 event drugs. At the +10-point H1 target, H2 gains of 0, +2 and +5 points give H2 sequence rates of 0.36%, 3.94% and 27.26%. The corresponding full-sequence rates are 0.22%, 2.40% and 16.84%. The 150-event minimum is the smallest point estimate crossing on this grid. Its interval includes values below 80%, and the full-sequence power is 10.82% at the main effect targets.

The dated NDA/NME candidate counts are 10,004 rows and 1,362 drugs at 24 months and 11,398 rows and 1,394 drugs at 12 months. The published frame gives the actual annual availability counts before first-entry exclusions. Both the event counts and the at-risk row counts used to simulate power depend on the synthetic first-approval process.

## Type-I error and alpha

Each null cell uses 12,000 datasets and 2,000 draws per dataset at α = 0.025. There were zero unevaluable datasets. Under the global null, the independently verified H1 population difference was close to zero and its expectation is exactly zero conditional on each generated history by the tie lottery. The upper Wilson limit of 0.032% is below 2.5%, giving `RULE_SELECTED_ALPHA = 0.025`. The 0.020 type-I rerun was not triggered.

| Null configuration at 75 event drugs | True-null marginal rejection | Familywise false rejection | 95% MC CI for familywise error |
| --- | ---: | ---: | ---: |
| H1, H2 and H3 null | H1 0/12,000 | 0/12,000 (0.000%) | [0.000%, 0.032%] |
| H2 null, H1 +10 pp and H3 +10 pp | H2 55/12,000 | 37/12,000 (0.308%) | [0.224%, 0.425%] |
| H3 null, H1 +10 pp and H2 +5 pp | H3 1/12,000 | 0/12,000 (0.000%) | [0.000%, 0.032%] |

## Changes from T4b

T4b used confidence and AURC80 under common coverage. T4c ranks native entry risk on the full eligible cohort and measures pooled event recall at annual capacity. B1's one-year hazard table supplies its exact score levels. M1 and M3 use a Gaussian rank fit with age, relative cutoff year, native B1 risk and outcome as synthetic score predictors. A paired draw resamples drug weights, recomputes cutoff capacity and uses exact fractional tie membership. The queue implementation encodes weighted prefixes near the capacity boundary and falls back to the full ordered cutoff whenever the prefixes cannot certify the resampled queue. The historical v2 effects and alpha estimates stay with [T4b](T4b.md).

## Reproduction

From the repository root with the pinned local source paths and NumPy available, run the following command. Use `--validate-only` for the development SD fit. The [machine output](../../../loe-bench/data/T4c_power.json) records the exact input digests and edition locators from the replay manifest. The development observation ends on 2016-01-01.

```powershell
rtk proxy python -B loe-bench/scripts/t4c_power.py --workers 8
```

The focused T4b and T4c pytest files passed all 20 tests. All 154 LOE-Bench unittest tests passed with the existing Purple Book resource warnings. The v3 fixtures check fractional ties against explicit duplicated rows, cutoff capacity recomputation, the exact fallback, rank-shift breakpoints, deterministic draws, undefined-step handling, the variance gate, and decoder guards for every CP4 outcome reader. The T4b pre-parse and dated feature fixtures run unchanged.

`rtk proxy python -B -m pytest --tb=short --basetemp C:/Users/User/AppData/Local/Temp/ptp-t4c-2567e74a -p no:cacheprovider` finished in 503.75 seconds. It returned exit 1 with 2,760 passed, 50 skipped, one xfailed and the eight accepted SACR r2/r3 supervisor-budget failures.

The simulation completed with exit 0 in 3,596.3 seconds using Python 3.12.10, NumPy 2.5.4 and eight local CPU workers. It used zero remote or paid compute. The machine output SHA-256 is `ace3fa342145c63febc29387cb9180ac8e79e4c8335f7446f29687b9f987ece5`. The final serialization names the v3 correlation overrides explicitly and retains every measured value. The focused tests passed again after the reporting adjustment. The seal guard SHA-256 is `eb1c41c81fc4c77120a1fecc00ae0053cc18f11cd3fb466ee6ea774704cafddb`. The preregistration lock and authorization variable were absent at entry and exit.

## Failures and limitations

- The 12-month B1 contrast ratios are near the lower boundary of the variance gate. The fit selects on a fixed development outcome panel and evaluates new score draws using the first candidate with a passing independent check. Annual capture and paired discordance still differ from the empirical panel.
- The candidate roster counts NDA/NME availability. Prior generic entry and the exact C′ evaluation eligibility remain unknown. Histories impose synthetic first approvals and approximate age progression from development. The scenario effects are imposed rank interventions.
- The exact H1 and H3 nulls preserve the ordering of different B1 score blocks. They create discordant queues within the boundary blocks and verify equality of expected recall. The type-I estimate therefore addresses this null design. A null with broad cross-block disagreement or different temporal drift remains unmeasured.
- The adverse age cell emitted a diagnostic divide warning for a cutoff with zero event rows. Its annual recall was serialized as `null`. Pooled power had defined denominators in all 5,000 datasets. The reporting guard now emits the same annual `null` directly.

## Next action

The main planner should keep T5 on hold for the 75-cluster reference. Review whether 150 or more eligible event drugs are feasible under the fresh-edition C′ rules, and whether an additional null with cross-block disagreement is needed to establish error calibration for the planned comparison. The simulation leaves the prospective Track A path and the test seal in force.
