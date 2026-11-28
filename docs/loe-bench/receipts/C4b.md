# C4b | Medicaid reimbursement forecasts

## Decision and freeze

The main planner promoted C4's mapped-package target and added two reimbursement endpoints for D41 pain point P2. The seven Medicaid origins end in December 2016. C4 found unverified historical vintages for all seven and unresolved package identities in every origin window. The full national ingredient totals remain `NOT_ESTIMABLE`. [C4 predecessor](C4.md) · [D41 plan](../PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026).

The v2 protocol freezes the endpoints, candidate rules, two baselines, queue linkage, fixed factor, missing-data rules and ingredient-cluster bootstrap before the Medicaid run. The C3b 12-month export is present and pinned by byte hash. The executor uses the exported native M3 and B1 scores. The December 2016 Medicaid baseline can use 2017 SDUD outcomes. A queue at the 1 January 2017 cutoff is reserved. [C4 v2 specification](../../../loe-bench/data/C4_SPEC.json) · [Spec digest](../../../loe-bench/data/C4_SPEC.sha256).

The pre-score commit is `6efd728ef08deae646e09f3c5d279b2446ccd982`. Spec LF SHA-256 is `c0644bb4c1ed9d6050e256191c85bb34dd120a73b6da78850a1faf80e2c400f0`. C3b's exact FREEZE replay manifest independently confirms the input file `FREEZE_dev_scores_12m.json` and SHA-256 `e9f7d9af0033207488adf1bb582e24a12982d5d72039ce8c8c611b1792227db7`. Each arm has 430 slots over 2,161 eligible cutoff rows. [C3b export and replay receipt](https://github.com/siriponsri/patent-to-pilot/blob/e8d3658da06ebe18bf973419a42fed62a333f9b6/docs/loe-bench/receipts/C3b.md) · [Published FREEZE development roster](../../../loe-bench/data/FREEZE_dev_report.json).

## Frozen comparison

The quarterly fit uses eight consecutive quarters through Q2 of the origin year. Carry-forward repeats the last observation. Drift extrapolates the first-to-last slope and floors each predicted quarter at zero. The ratio endpoint uses the fourth quarter after December 31, which is six steps after the fit anchor. Its observed value divides the mapped sum of total reimbursement by the mapped sum of prescriptions in that quarter, requiring a positive denominator. The annual endpoints sum the next four calendar quarters. Both reimbursement endpoints use nominal US dollars. [C4 benchmark paper](https://doi.org/10.1016/j.ijforecast.2015.08.001) · [CMS field definitions](https://www.medicaid.gov/medicaid/prescription-drugs/downloads/cms-r-144-state-invoice-data-definitions-2019.pdf).

The entry-adjusted policy multiplies the carry-forward reimbursement forecast by **0.465** for every queued ingredient, with two generic producers assumed in the forecast year. The factor is the FDA median generic-to-brand average manufacturer price ratio for two producers, page 9. It is frozen independently of the Medicaid outcomes. The policy applies it to the target year as a scenario. The M3 and B1 arms rank their complete cutoff rosters by native score, take `floor(N/5)` and use a shared fixed hash ordering for boundary ties. They then compare with unadjusted carry-forward and drift on the same exact-cutoff, active-moiety-linked rows. Unqueued keys on that roster retain carry-forward. [FDA December 2019 report](https://www.fda.gov/media/133509/download) · [Published FREEZE development roster](../../../loe-bench/data/FREEZE_dev_report.json).

## Development results

**`DEVELOPMENT_ONLY`, retrospective, vintage-uncontrolled.** Both queue adjustments increased MAE relative to unadjusted carry-forward on the paired Medicaid rows for both reimbursement endpoints. M3 had higher annual-dollar MAE than B1. The M3–B1 per-prescription MAE difference was inconclusive. Drift had lower annual-dollar MAE than carry-forward in the pooled analysis of seven origins. For annual prescription counts, carry-forward reproduced C4's lower MAE. The full national target is `NOT_ESTIMABLE` for all three endpoints. The `AS_OF_PROVEN` arm has zero admitted origins and is `NOT_RUN`.

The tables give point estimates and 95% percentile intervals from 2,000 ingredient-cluster bootstrap draws. Each paired row is an ingredient-origin. Bias is forecast minus observed. Positive MAE differences favor the comparator named second.

| All mapped origins | Pairs / ingredients / origins | Arm | MAE [95% interval] | Signed bias [95% interval] |
|---|---:|---|---:|---:|
| Annual prescriptions (claims) | 1,270 / 403 / 7 | Carry-forward | 25,002 [19,479, 31,219] | −7,542 [−13,045, −2,362] |
| | | Drift | 31,114 [23,418, 39,010] | +12,998 [+6,455, +19,760] |
| Q4 reimbursement (USD per prescription) | 1,356 / 429 / 7 | Carry-forward | 253.70 [184.72, 329.28] | −211.31 [−284.89, −144.00] |
| | | Drift | 239.62 [173.40, 315.84] | −45.39 [−101.25, −0.21] |
| Annual reimbursement (USD millions) | 1,270 / 403 / 7 | Carry-forward | 11.02 [7.50, 14.96] | −6.86 [−10.44, −3.46] |
| | | Drift | 8.27 [5.39, 12.55] | +2.48 [−0.33, +6.46] |

On all mapped origins, the paired drift minus carry-forward MAE difference for counts was **+6,112** claims [2,382, 10,207]. For Q4 reimbursement per prescription the difference was **−14.08** USD [−50.03, 20.47]. For annual reimbursement it was **−2.75 million** USD [−5.30, −0.12].

| Queue-linked origins | Pairs / ingredients / origins | Arm | MAE [95% interval] | Signed bias [95% interval] |
|---|---:|---|---:|---:|
| Q4 reimbursement (USD per prescription) | 160 / 68 / 4 | Carry-forward | 462.59 [263.58, 700.64] | −453.78 [−693.43, −253.43] |
| | | Drift | 290.45 [151.00, 493.07] | −181.59 [−382.48, −43.36] |
| | | B1-adjusted | 834.64 [504.85, 1,226.92] | −825.84 [−1,216.67, −494.99] |
| | | M3-adjusted | 843.82 [519.34, 1,237.00] | −840.50 [−1,233.84, −516.86] |
| Annual reimbursement (USD millions) | 150 / 64 / 4 | Carry-forward | 13.22 [6.45, 22.92] | −12.13 [−21.86, −5.46] |
| | | Drift | 9.53 [4.81, 16.01] | −2.62 [−6.76, +0.88] |
| | | B1-adjusted | 18.21 [10.34, 28.30] | −17.54 [−27.81, −9.64] |
| | | M3-adjusted | 34.65 [11.68, 75.76] | −33.99 [−75.10, −11.01] |

| Paired MAE difference | Q4 USD per prescription [95% interval] | Annual USD millions [95% interval] |
|---|---:|---:|
| Drift minus carry-forward | −172.13 [−292.12, −66.37] | −3.69 [−8.41, −0.20] |
| B1-adjusted minus carry-forward | +372.05 [193.27, 587.26] | +4.98 [2.24, 8.29] |
| M3-adjusted minus carry-forward | +381.24 [203.61, 606.77] | +21.43 [4.07, 53.21] |
| M3-adjusted minus B1-adjusted | +9.19 [−136.98, 140.29] | +16.44 [0.45, 48.14] |

### Coverage and linkage

Identity coverage is the share of observed NDC-quarter records that map to a date-eligible FDA ingredient identity. Per-ingredient coverage uses its own mapped NDC-quarters as the denominator and reports the fractions with complete national counts, complete national amounts and both. The machine report includes those fractions, denominators, and suppression and missingness counts by origin and window. Unresolved identities make each ingredient's share of its full national frame unknown.

| Medicaid origin | Fit identity coverage | Annual outcome identity coverage | Q4 identity coverage | Annual count / amount pairs (each) | Q4 ratio pairs | Queue-linked amount / ratio pairs |
|---|---:|---:|---:|---:|---:|---:|
| 2010-12-31 | 14.3% | 18.3% | 19.2% | 53 | 55 | No frozen cutoff |
| 2011-12-31 | 16.1% | 20.3% | 21.1% | 57 | 59 | 9 / 9 |
| 2012-12-31 | 18.2% | 22.3% | 23.1% | 172 | 180 | 42 / 45 |
| 2013-12-31 | 20.4% | 25.1% | 26.0% | 220 | 234 | 49 / 53 |
| 2014-12-31 | 22.4% | 28.1% | 28.9% | 235 | 259 | 50 / 53 |
| 2015-12-31 | 25.1% | 31.4% | 32.7% | 262 | 275 | No frozen cutoff |
| 2016-12-31 | 28.2% | 34.7% | 35.7% | 271 | 294 | Reserved cutoff |

GSRS resolved 378/403 (93.8%) of scored count and annual reimbursement ingredients and 403/429 (93.9%) of scored Q4 ratio ingredients. At the four exported cutoffs, the annual amount joined 150/684 baseline rows, with 45 unresolved moiety links and 489 resolved keys outside the roster. The ratio joined 160/732, with 47 unresolved links and 525 outside the roster. The B1 and M3 policies triggered on 43 and 59 of the 150 annual amount rows and on 47 and 63 of the 160 ratio rows, respectively.

## Limits and planner handoff

The target covers date-eligible, mapped US Medicaid SDUD national `XX` records. Total Amount Reimbursed is a gross, pre-rebate provider payment measure and includes both Medicaid and non-Medicaid amounts in the SDUD records. Net drug price and Thai demand are outside this endpoint. Combination NDCs contribute to all listed ingredients, so ingredient totals can overlap. The current NDC directory omits historical products, and the FDA factor was published after the origins. The entry queues forecast approval risk, while actual market entry, realized producer counts and payer terms remain unobserved. The evaluation describes the specified scenario on the observed subset. [CMS rebate treatment](https://www.medicaid.gov/faq/2020-04-09/92001) · [C4 vintage audit](C4.md#distribution-and-vintage-audit).

For integration, retain carry-forward as the frozen primary baseline and drift as the secondary. Record the higher MAE of both queue adjustments and keep the FDA multiplier as a D41 scenario. Review historical SDUD releases and package identity coverage before attempting any as-of analysis. This receipt is the executor handoff and memory entry. The main planner owns lane-level updates.

## Reproduce

Run from `loe-bench/` with Python 3.12 and the LOE-Bench dependencies. The output name must be new. Confirm that the canonical preregistration lock and its environment variable are absent before starting. The runner rejects both if present.

```powershell
$loePrivate = 'C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench'
$c4Raw = "$loePrivate/medicaid_sdud"
$c4Replay = "$c4Raw/c4b-dev-replay-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
$env:OPENBLAS_NUM_THREADS = '1'
rtk proxy python -m loe_bench.c4b --spec data/C4_SPEC.json --inputs data/C4_INPUTS.json `
  --raw-dir "$c4Raw" --gsrs "$loePrivate/moiety/dump-public-2026-08-06.gsrs" `
  --scores "$loePrivate/FREEZE_dev_scores_12m.json" --out "$c4Replay"
rtk proxy python -m unittest discover -s loe_bench/tests -t .
```

Omit `--scores` to use the same directory's default C3b paths. If the exact 12-month export is absent, baseline results are still produced and the adjusted arms are `PENDING_SCORE_EXPORT`. Supply the pinned 12-month file and a new output path to rerun. To reproduce C4 v1, use revision `e1239c29` and its receipt command with the v1 spec and runner from that revision.

## Verification

- **PASS** for the pinned development run on CPU with Python 3.12.10 and NumPy 2.5.4. The private report is `medicaid_sdud/c4b-dev-summary.json` under the directory above, with SHA-256 `cb7369160e39924c3e39f6b77fb4ffd7807169b2c8f9f25fc2eaae013ab1224b`. The report retains per-ingredient coverage and pooled intervals for all paired MAE contrasts. Original inputs and the FDA PDF stay outside Git.
- **PASS** for report validation. Annual prescription pair count, ingredient count, both MAEs and both biases match the C4 mapped diagnostic. Seven Medicaid origins were evaluated. Four pre-2017 benchmark cutoffs supplied queues. The seal file matches the parent revision and the preregistration lock was absent. No paid services or GPU were used.
- **PASS** for `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/`. All 212 tests passed, including 7 new hand-checkable C4b tests. Existing Purple Book resource warnings appeared.
- **FAIL** for root `python -m pytest --tb=short` with the eight standing SACR r2/r3 supervisor budget failures only. 2,760 passed, 50 skipped and one xfailed.
