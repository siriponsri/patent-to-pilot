# POWER-SIM | Prospective expansion feasibility

CPU-only simulation of the registered single-origin Track A design and prospective alternatives for the incremental graph comparison. Each reported probability is model-based. The eventual prospective effect, event rate and operational reliability remain unknown. [Locked simulation protocol](POWER-SIM-PROTOCOL.md) · [Power plan](../POWER-PLAN.md) · [Machine results](../../../loe-bench/data/POWER_SIM.json)

## Decision and reporting conventions

**Owner input.** Carry annual C and biennial D into planner review for a +5 pp decision. C retained 97.90% power under low incidence and 95.50% under weaker M1–M3 score correlation. D had the highest central completion-adjusted power, with 7 required freezes, but its low-incidence power was 87.10%. At .99 per freeze, the low-incidence joint probability of a complete panel and H2 rejection was about 86.8% for C and 81.2% for D. The quarterly plan gives greater conditional power for a +2 pp gain at the cost of 43 freezes. At +1.36 pp, no tested central design reached 80% power. Consider the four-year quarterly schedule separately if an earlier readout matters. Its central +5 pp result needs stress verification before any design decision.

The complete machine result gives rejection counts, denominators, Monte Carlo standard errors and Wilson 95% intervals for every cell. Track A's H2 success is the unconditional probability of passing both H1 and H2. Its H2 result also includes the marginal and reached-step conditional probabilities, plus H3 at 12 months. The expansions have one primary H2 test at final maturity. Their H1 columns give the positive-lower-bound frequency at the same nominal level as a descriptive comparison. No intermediate efficacy tests enter the results. A positive lower bound against zero does not establish a lower bound above the proposed five-point practical effect. Both probabilities are in the JSON.

An event row is a forecast at one origin whose horizon contains the first approval. An approval can contribute several event rows. The study resamples the active-moiety key across all of its rows. Canada uses a separate queue and approval clock and shares the active-moiety cluster across countries. Readout dates assume the first eligible outcome archive covers maturity. The scheduling simulation does not establish when that archive will be available.

### Decision table

Central incidence and score dependence, H1 +10 pp and H2 +5 pp. Power entries show the percent and Monte Carlo standard error in percentage points. The annual burden columns show the average across the forecast years, including zero-freeze years. Each prediction run is local CPU. Maturity scoring and review are counted separately in the machine results.

| Design | H1 power ± MC SE | H2 power ± MC SE | Expected approvals / event rows | Final year | Freezes | Annual freezes / CPU runs / owner actions | Complete at .95 / .99 per freeze |
|---|---:|---:|---:|---:|---:|---:|---:|
| A · Existing Track A | 28.85 ± 1.01% | 5.30 ± 0.50% | 51 / 51 | 2028 | 1 | 1.00 / 1.00 / 2.00 | 95.0% / 99.0% |
| B · Quarterly US | 99.75 ± 0.11% | 100.00 ± 0.00% | 319 / 2,176 | 2039 | 43 | 3.91 / 3.91 / 4.91 | 11.0% / 64.9% |
| C · Annual US | 99.20 ± 0.20% | 99.80 ± 0.10% | 318 / 608 | 2039 | 12 | 1.09 / 1.09 / 2.09 | 54.0% / 88.6% |
| D · Biennial US | 94.80 ± 0.50% | 98.15 ± 0.30% | 317 / 355 | 2039 | 7 | 0.64 / 0.64 / 1.18 | 69.8% / 93.2% |
| E · Quarterly US, 36 months | 100.00 ± 0.00% | 100.00 ± 0.00% | 344 / 3,251 | 2040 | 43 | 3.91 / 3.91 / 4.91 | 11.0% / 64.9% |
| F · Annual US + assumed Canada | 100.00 ± 0.00% | 100.00 ± 0.00% | 537 / 1,027 | 2039 | 24 | 2.18 / 2.18 / 3.18 | 29.2% / 78.6% |

The F mean of 537 approvals consists of 318 US and 219 Canadian events across 433 distinct active-moiety clusters. At +5 pp, applying the .99 freeze assumption gives 64.9% operational power for B, 88.5% for C and 91.5% for D. At .95, the corresponding probabilities are 11.0%, 53.9% and 68.5%. The median calendar gap is 12 months for C and 24 for D, with the supplemental October 2037 origin in both. The peak annual freezes and owner actions are four and five for B, two and three for C and D, and four and five for F. Track A's one scheduled freeze is already verified.

An extra 3% irreversible custody-loss risk in each active forecast year, combined with .99 per freeze, lowers completion to 46.4% for B, 63.4% for C and 77.6% for D under the stated independence assumptions.

### Central effect grid

All cells used 2,000 panels. Each entry is percent ± Monte Carlo SE in percentage points. H2 at zero is the simulated type I error under the broad exchangeable-rank null with the stated nonzero H1 alternative. The expected event counts and burden are shared across the eight effect cells within each design because the same histories enter each target. When every panel rejects or none rejects, the plug-in SE is zero and the Wilson interval still has positive width.

| Design | H1 target (pp) | H1 power | H2 0 pp | H2 +1.36 pp | H2 +2 pp | H2 +5 pp |
|---|---:|---:|---:|---:|---:|---:|
| A | +10 | 28.85 ± 1.01 | 0.00 ± 0.00 | 0.20 ± 0.10 | 0.45 ± 0.15 | 5.30 ± 0.50 |
| A | +20.37 | 83.30 ± 0.83 | 0.10 ± 0.07 | 0.45 ± 0.15 | 1.10 ± 0.23 | 11.75 ± 0.72 |
| B | +10 | 99.75 ± 0.11 | 1.95 ± 0.31 | 49.35 ± 1.12 | 83.80 ± 0.82 | 100.00 ± 0.00 |
| B | +20.37 | 100.00 ± 0.00 | 1.50 ± 0.27 | 48.35 ± 1.12 | 83.50 ± 0.83 | 100.00 ± 0.00 |
| C | +10 | 99.20 ± 0.20 | 2.20 ± 0.33 | 25.80 ± 0.98 | 49.10 ± 1.12 | 99.80 ± 0.10 |
| C | +20.37 | 100.00 ± 0.00 | 1.90 ± 0.31 | 26.95 ± 0.99 | 51.95 ± 1.12 | 99.90 ± 0.07 |
| D | +10 | 94.80 ± 0.50 | 0.20 ± 0.10 | 7.55 ± 0.59 | 21.05 ± 0.91 | 98.15 ± 0.30 |
| D | +20.37 | 100.00 ± 0.00 | 0.50 ± 0.16 | 6.95 ± 0.57 | 20.75 ± 0.91 | 97.40 ± 0.36 |
| E | +10 | 100.00 ± 0.00 | 2.30 ± 0.34 | 65.15 ± 1.07 | 94.00 ± 0.53 | 100.00 ± 0.00 |
| E | +20.37 | 100.00 ± 0.00 | 2.05 ± 0.32 | 64.15 ± 1.07 | 92.15 ± 0.60 | 100.00 ± 0.00 |
| F | +10 | 100.00 ± 0.00 | 1.85 ± 0.30 | 37.75 ± 1.08 | 69.75 ± 1.03 | 100.00 ± 0.00 |
| F | +20.37 | 100.00 ± 0.00 | 1.70 ± 0.29 | 39.05 ± 1.09 | 70.50 ± 1.02 | 100.00 ± 0.00 |

For A at +10/+5 pp, H2 marginal power was 11.60% ± 0.72 pp and sequence power was 5.30% ± 0.50 pp. Under the +20.37/+1.36 pp scenario, the H2 marginal and sequence rates both rounded to 0.45% ± 0.15 pp. At H1 +20.37 pp and H2 zero, two panels out of 2,000 falsely passed H2, both after H1. The independent calibrated A H1 effects were +10.03 and +20.74 pp. The initial projection from TRAIN was 51 events, and the simulation averaged 51.33. For C, annual roster retention averaged 96.28%, close to the observed development value of 96.85%.

### Cadence and shorter spans

| US schedule | H1 +10 pp power | H2 +5 pp power | H2 null rejection | Approvals / event rows | Final year | Freezes | Complete at .95 / .99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Monthly to October 2037 | 99.80% | 100.00% | 2.90% | 319 / 6,426 | 2039 | 127 | 0.15% / 27.90% |
| Quarterly for four forecast years | 89.00% | 99.40% | 2.25% | 153 / 859 | 2033 | 17 | 41.81% / 84.29% |
| Quarterly for eight forecast years | 99.15% | 100.00% | 2.30% | 256 / 1,680 | 2037 | 33 | 18.40% / 71.77% |

The monthly, quarterly, annual and biennial 24-month schedules over the full span saw about 317–319 distinct first approvals. They differed mainly in observations per approval. B had 6.82, C had 1.91 and D had 1.12. B's separate forecasts can add precision through repeated score measurements under the assumed dependence structure. Denser origins provide little additional enrollment in this simulation. The four-year comparison has only a central incidence and score-dependence check. Its strong +5 pp result is sensitive to whether the low synthetic variance transfers. The power plan used a more conservative 0.10 variance per independent-event equivalent for sizing. [Planning variance and alternatives](../POWER-PLAN.md#information-and-calendar-time)

### Inference checks

A used the exact 2,000-draw percentile bootstrap, with H1 and H2 at 24 months and H3 at 12 months. B, C, E, F and the three cadence sensitivities passed the matched local-linear check against 2,000 draws. D's H2 null showed a 3.75 pp rejection difference, beyond the 3.5 pp limit. D used the prespecified 400-draw bootstrap fallback. Its matched decision disagreement was at most 0.625% across the checked contrasts and cells, and evaluability agreed. The checked settings were H1 +10 pp and H2 zero or +5 pp at central nuisance values. These matched checks qualify estimates against the exact method on the simulated panels. The broader stress rates quantify model uncertainty and do not establish type I control across real cohorts.

The central A +20.37/+1.36 pp cell reached H2 in 1,666 of 2,000 panels. Nine passed H2 and two passed H3. H3 marginal power was 12.50% and full-sequence power was 0.10%. Its reached-step estimate uses only nine panels. In the low-incidence A sensitivity, H3 independently calibrated at +10.67 pp and missed the 0.50 pp tolerance in both effect cells. Read its H3 and full-sequence rates as provisional. Both 24-month contrasts met the effect tolerance there. The A gated H2 +5 pp rate ranged from 0.95% at low incidence to 11.60% at high incidence. Weaker cross-arm dependence gave 4.50% with central incidence.

### Sensitivity of the quarterly and annual options

These are one-factor screens with 2,000 panels per estimate and H1 set to +10 pp. The error columns give H2 null rejection percentages. They describe the tested nuisance settings only. The lower-persistence and higher-persistence settings are 0.50 and 0.95, respectively. Full estimates, including Monte Carlo SE and Wilson intervals, are in the machine results.

| Scenario | B approvals | B H2 +5 pp | B H2 error | C approvals | C H2 +5 pp | C H2 error |
|---|---:|---:|---:|---:|---:|---:|
| Central | 319 | 100.00% | 1.95% | 318 | 99.80% | 2.20% |
| Low incidence | 220 | 99.95% | 2.35% | 219 | 97.90% | 2.20% |
| High incidence | 402 | 100.00% | 2.05% | 401 | 100.00% | 2.05% |
| Lower score persistence | 319 | 100.00% | 2.60% | 319 | 99.90% | 2.50% |
| Higher score persistence | 319 | 100.00% | 2.80% | 318 | 99.90% | 1.90% |
| Shared annual incidence shocks | 318 | 100.00% | 1.90% | 317 | 99.85% | 2.00% |
| M1–M3 score correlation 0.90 | 319 | 99.80% | 2.10% | 318 | 95.50% | 2.30% |
| Younger roster and faster arrivals | 394 | 100.00% | 1.75% | 393 | 99.95% | 2.25% |
| Within-bin exchangeable null | 319 | N/A | 2.00% | 318 | N/A | 1.80% |

B's null upper Wilson limits reached 3.39% and 3.62% in the lower- and higher-persistence screens. At +5 pp the central H2 point-variance product per unique event drug was 0.016 for B and 0.035 for C. With score correlation 0.90 those products increased to 0.035 and 0.063. The original planning stress used 0.10 per independent-event equivalent. The simulation's variance results depend on how much the two arms disagree and how often that disagreement persists over overlapping windows. Both B and C reached 100% rejection in the +10 pp H2 stress.

D ranged from 87.10% to 99.65% power at +5 pp across its noncentral settings, with H2 null rejection of 0.30–0.60%. E reached 100% power at +5 pp under the tested incidence and shock settings. Its low-incidence null rejection reached 3.10%. F reached 99.70% power at +5 pp under weaker cross-arm dependence and 100% in the other reported alternatives. The two Canada rate sensitivities imply 119–318 Canadian approvals and 437–636 total approvals over the fixed span. Their H2 null rejection was 2.50% in each. The simulated Canadian rates do not resolve eligibility or archive feasibility.

### Filing gate

**Filing verification `NOT_RUN`.** B cleared the central screening thresholds at 100% H2 power and 1.95% H2 null rejection. The second timed pilot took 0.618 seconds per exact 2,000-draw B panel, including local run overhead. Extrapolation to 38 independent verification cells of 10,000 panels each was roughly 65 worker-hours, or over eight wall hours even with ideal eight-worker scaling. The executor used a one-hour local verification window for this feasibility card. The exact filing grid and independent T4c raw-history replication therefore remain unmeasured. The custody conditions also need owner review. No OSF filing or branch integration occurred on this card.

## Inputs, assumptions and limitations

- **US rate and roster.** The generator starts at 651 and targets 51 events in the first 24 months, with 32 and 70 as sensitivity anchors. Central arrival intensity uses the 22 entrants between the two annual T4c validation rosters of 539 and 544, which retained 522 histories. Starting ages are synthetic, and first approval is the only exit. Counts at later origins can change with aging, arrivals and prior approvals. Distinct approvals and effective information consequently differ from the planning arithmetic that assumes constant incidence.
- **Score dependence.** The input supplies DEV B1 age-clock levels and joint rank summaries for M1/M3. Scores have real B1 ties, correlated regulatory residuals and a shared drug component. Range checks vary the persistent score fraction and cross-arm dependence. Score shifts impose target queue-recall differences on synthetic data. The independent effect check and realized panel differences are recorded per cell. Using a 24-month rank footprint at 36 months assumes transport to a different prediction task. The simulation neither fits new core predictors nor estimates Track A's queue overlap.
- **Events.** Each jurisdiction draws one absorbing first-event date per drug. All overlapping windows use that date. A shared frailty creates within-drug dependence, and the annual shock sensitivity creates cross-drug dependence in incidence. It does not test calendar-wide changes in relative graph skill. The extension inference conditions on the named dates. The fixed schedules do not adapt to accrued events.
- **Canada.** The endpoint, denominator, available archives, cross-country linkage and prospective event dependence have no empirical calibration here. F assumes 32 approvals in 24 months per 651 at-risk Canadian histories, with 16 and 51 as sensitivity values. Same-cohort enrollment, full synthetic moiety matching and shared frailty are assumptions. No extract was downloaded. A Canadian NOC is a separate regulatory event. [Health Canada NOC database](https://www.canada.ca/en/health-canada/services/drugs-health-products/drug-products/notice-compliance/database.html)
- **Maintenance.** The model assigns one prediction run, one attestation and one freeze to each enrolled country-origin, plus one restore check in each forecast year with an origin. Yearly averages include intervening zero-freeze years. The maturity analysis is a separate run and owner review. Track A's 2027 descriptive readout and 2028 final analysis are separate entries. Completion assumes a fixed probability for each freeze and independence across freezes, with separate 1% and 3% annual custody-loss sensitivities during active forecast years. Track A's original freeze already happened. The tabulated one-freeze probabilities are illustrative. The scenario does not measure operator effort, data latency or loss after the last origin. [Track A freeze evidence](TRACKA-FREEZE.md) · [Forecast Hub, external precedent for rolling timestamped submissions](https://doi.org/10.1038/s41597-022-01517-w)

## Reproduction and integrity

Use Windows Python 3.12 and NumPy. The source checks the normalized Git blob of the T4c aggregate before parsing it. The optional Numba path accelerates exact queue rebuilding with the same whole-drug weights and fractional tie arithmetic, and the NumPy implementation supplies the reference fallback. The test fixtures compare both paths to the registered scorer and a hand-checkable boundary tie. [Registered inference](../PREREGISTRATION.md#effect-size-and-statistical-power) · [Field and Welsh, clustered bootstrap](https://doi.org/10.1111/j.1467-9868.2007.00593.x)

The CPU run used the existing CPython 3.12.10 and NumPy 2.5.4. The executor downloaded the following CPython 3.12 Windows x64 wheels from PyPI on 28 November 2026 and installed only Numba and llvmlite into an isolated temporary package directory. The matching NumPy wheel was downloaded as a dependency check. Neither the global installation nor project dependencies changed.

| Wheel | Package metadata licence | Downloaded wheel SHA-256 |
|---|---|---|
| [Numba 0.68.1](https://pypi.org/project/numba/0.68.1/) | BSD | `6d115039768cc2eb3cc99b32355ca507e1bbc653eca5492c83ab6399f218df27` |
| [llvmlite 0.50.0](https://pypi.org/project/llvmlite/0.50.0/) | BSD-2-Clause and Apache-2.0 with LLVM exception | `c20595cc3a76e3c85140fdafbf9246c732ddf8e0e646ba2f4e4881f87567300d` |
| [NumPy 2.5.4](https://pypi.org/project/numpy/2.5.4/) | BSD-3-Clause core with bundled third-party notices | `a7b1b6353e36a7e50de2973a38d705c88ee93adcf120673cee7f45a4a3fa223a` |

```powershell
$powerSimPackages = Join-Path $env:TEMP 'ptp-power-sim-packages'
rtk proxy py -3.12 -m pip install --only-binary=:all: --no-deps --target $powerSimPackages numba==0.68.1 llvmlite==0.50.0
$env:PYTHONPATH = $powerSimPackages
$env:NUMBA_CACHE_DIR = Join-Path $env:TEMP 'ptp-power-sim-numba-cache'
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
rtk proxy py -3.12 -B loe-bench/sim/power_sim.py --pilot
rtk proxy py -3.12 -B loe-bench/sim/power_sim.py --workers 8 --pilot-exact-seconds 0.6182223333356281
rtk proxy py -3.12 -m pytest tests/test_org_adaptive_terminology.py -q
rtk proxy py -3.12 -m pytest loe-bench/sim/test_power_sim.py -q
```

The first pilot stopped at an incorrect key path in the aggregate reader. After correcting the path, the historical count tabulation matched the 50, 75 and 150 event-grid rows for H1/H2 sequence rejection (36.76%/2.04%, 49.96%/3.94% and 80.58%/13.60%). Independent simulation of those original pools is `NOT_RUN`. Their exact synthetic history templates are unavailable in the admitted aggregate. The original builder depends on mixed historical sources and was outside the allowed inputs.

**Run and tests.** The CPU screen completed in 1,571.37 wall seconds with eight workers and exit 0. It produced 124 effect cells across 47 design and setting combinations, with 2,000 replicate panels per combination. The output audit confirmed all 124 H1/H2 target checks, two provisional H3 checks in the same A low-incidence setting, the matched inference choices, the reported probability arithmetic and the protocol digest. The normalized result SHA-256 is `ddea868eedd611846c52b47659431b4778a6c3ab9bbad43b6bf6ec1439b4151b`.

The requested terminology test passed 2 cases. The simulation suite passed 9 cases with both the accelerated and NumPy implementations, including registered single-origin parity and weighted queue parity across overlapping origins. The root `py -3.12 -m pytest -q --tb=short --basetemp <short-local-path>` run returned exit 1 with the eight standing SACR r2/r3 supervisor-budget failures. No additional failures were reported.

The only measured input was the public repository's T4c aggregate at `31bb509f`. Committed aggregate contrasts supplied the two named C′ scenario values through the power plan. The card used zero remote workers, paid APIs and GPU jobs. C′ rows, protected exports, private prospective predictions, Track A outcomes and credential files were never opened. The planner owns integration of this receipt into the shared HANDOFF and MEMORY and reviews the evidence before the next owner decision.
