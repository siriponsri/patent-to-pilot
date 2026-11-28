# C4b | Medicaid reimbursement forecasts

## Executor checkpoint

The main planner promoted C4's mapped-package target and added two reimbursement endpoints for D41 pain point P2. The seven Medicaid origins end in December 2016. C4 found unverified historical vintages for all seven and unresolved package identities in every origin window. The full national ingredient totals remain `NOT_ESTIMABLE`. [C4 predecessor](C4.md) · [D41 plan](../PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026).

The v2 protocol freezes the endpoints, candidate rules, two baselines, queue linkage, fixed factor, missing-data rules and ingredient-cluster bootstrap before the Medicaid run. The C3b 12-month export is present and pinned by byte hash. The executor uses the exported native M3 and B1 scores. The December 2016 Medicaid baseline can use 2017 SDUD outcomes. A queue at the 1 January 2017 cutoff is reserved. [C4 v2 specification](../../../loe-bench/data/C4_SPEC.json) · [Spec digest](../../../loe-bench/data/C4_SPEC.sha256).

Development scoring is `NOT_RUN` at this checkpoint. LOE-Bench unittest discovery passed 212 tests. Root pytest reported the eight standing SACR r2/r3 supervisor budget failures, 2,760 passed, 50 skipped and one xfailed. The next action is to commit the pre-score freeze on `loe/C4b` and run the pinned CPU scorer. This receipt carries the executor handoff and the memory entry for main-planner integration.

## Frozen comparison

The quarterly fit uses eight consecutive quarters through Q2 of the origin year. Carry-forward repeats the last observation. Drift extrapolates the first-to-last slope and floors each predicted quarter at zero. The ratio endpoint uses the fourth quarter after December 31, which is six steps after the fit anchor. Its observed value divides the mapped sum of total reimbursement by the mapped sum of prescriptions in that quarter, requiring a positive denominator. The annual endpoints sum the next four calendar quarters. Both reimbursement endpoints use nominal US dollars. [C4 benchmark paper](https://doi.org/10.1016/j.ijforecast.2015.08.001) · [CMS field definitions](https://www.medicaid.gov/medicaid/prescription-drugs/downloads/cms-r-144-state-invoice-data-definitions-2019.pdf).

The entry-adjusted policy multiplies the carry-forward reimbursement forecast by **0.465** for every queued ingredient, with two generic producers assumed in the forecast year. The factor is the FDA median generic-to-brand average manufacturer price ratio for two producers, page 9. It is frozen independently of the Medicaid outcomes. The policy applies it to the target year as a scenario. The M3 and B1 arms rank their complete cutoff rosters by native score, take `floor(N/5)` and use a shared fixed hash ordering for boundary ties. They then compare with unadjusted carry-forward and drift on the same exact-cutoff, active-moiety-linked rows. Unqueued keys on that roster retain carry-forward. [FDA December 2019 report](https://www.fda.gov/media/133509/download) · [Published FREEZE development roster](../../../loe-bench/data/FREEZE_dev_report.json).

The forecast target remains specific to the date-eligible, mapped packages in the US Medicaid SDUD national `XX` records. Total Amount Reimbursed is a gross, pre-rebate provider payment measure and includes both Medicaid and non-Medicaid amounts in the SDUD records. It measures neither net price nor Thai demand. Combination NDCs contribute to all listed ingredients, so ingredient totals can overlap. The crosswalk uses a current export with limited historical coverage, and the FDA factor was published after the origins. Neither input supports an as-of or causal result. [CMS rebate treatment](https://www.medicaid.gov/faq/2020-04-09/92001) · [C4 vintage audit](C4.md#distribution-and-vintage-audit).

## Reproduce

Run from `loe-bench/` with Python 3.12 and the LOE-Bench dependencies. The output name must be new. Confirm that the canonical preregistration lock and its environment variable are absent before starting. The runner rejects both if present.

```powershell
$loePrivate = 'C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench'
$c4Raw = "$loePrivate/medicaid_sdud"
$c4Replay = "$c4Raw/c4b-dev-replay-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
rtk proxy python -m loe_bench.c4b --spec data/C4_SPEC.json --inputs data/C4_INPUTS.json `
  --raw-dir "$c4Raw" --gsrs "$loePrivate/moiety/dump-public-2026-08-06.gsrs" `
  --scores "$loePrivate/FREEZE_dev_scores_12m.json" --out "$c4Replay"
rtk proxy python -m unittest discover -s loe_bench/tests -t .
```

Omit `--scores` to use the same directory's default C3b paths. If the exact 12-month export is absent, baseline results are still produced and the adjusted arms are `PENDING_SCORE_EXPORT`. Supply the pinned 12-month file and a new output path to rerun. To reproduce C4 v1, use revision `e1239c29` and its receipt command with the v1 spec and runner from that revision.
