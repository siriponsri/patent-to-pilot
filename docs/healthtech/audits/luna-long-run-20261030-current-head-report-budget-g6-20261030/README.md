# HT current-head report, budget, and G6 refresh

- Run ID: `luna-long-run-20261030-current-head-report-budget-g6-20261030`
- Date: `2026-10-30`
- Status: `PASS_CURRENT_HEAD_REPORT_BUDGET_G6_REFRESH`
- Parent evidence: `docs/healthtech/audits/luna-long-run-20261030-current-head-baseline-b4-20261030/`
- Source head before documentation: `1c468994ad603287007bde761ab15fbd37ffeffa`

## Scope

This package refreshes the canonical G6 manuscript skeleton and the non-submitted budget/data expansion request from the M30 current-head report. It does not create a new retrieval run, semantic label, source acquisition, provider request, external transfer, or paid reservation.

The refreshed surfaces now bind to the current 8-device/31-patent development view, the untouched 3-device Stryker holdout, the M30 HT-B0a/B0b/B1/B2/B3 rows, the same-cohort HT-B4 mock, and the current protocol/cohort hashes. Historical M3/M10/M11 figures remain in the budget request or manuscript only where explicitly labeled as historical.

## Refreshed artifacts

- `docs/healthtech/research/G6_MANUSCRIPT_METHODS_SKELETON_20261029.md` now reports M30 baseline rows, current B4 mock holdout comparisons, current paired-group diagnostics, current report/analysis links, and the correct development/holdout frontier interpretation.
- `docs/healthtech/goals/luna-long-run-20261028-889958e/BUDGET_EXPANSION_REQUEST_TH.md` now records M30 evidence and preserves the recommendation of `$0.00` incremental authorization with no paid dispatch.
- `tests/test_healthtech_g6_skeleton.py` binds both documents to the current-head report and rejects stale or missing M30 facts.

## Verification

- G6/current-head documentation regression: `3 passed`.
- Long-run report and analysis regressions: `4 passed`.
- `rtk proxy python -m compileall -q src scripts tests`: exit `0`.
- `git diff --check`: exit `0`.
- Provider calls: `0`.
- Network acquisition: `0`.
- Paid cost: `USD 0.00`.
- New semantic labels: `0`.
- Incremental budget authorization requested: `USD 0.00`.

Machine-readable hashes, commands, and source bindings are in [`verification.json`](verification.json).

## Boundaries

This is evidence integration and decision preparation, not a new scientific run. The M30 results remain descriptive product-level known-link recovery, not semantic relevance gold, exhaustive recall, generalization, clinical/FTO, patent-validity, investment, or publication evidence. Live/provider HT-B4 remains `BLOCKED_LOCAL`; Bridge remains `BLOCKED_LOCAL`; Zenodo record `21101400` remains restricted; Claude UX/UI remains paused.

## Next action

Obtain owner authorization and exact schema/rights terms for an admissible semantic device-patent judgment source. Run M23, M25, and M24 in sequence, then rerun the frozen controls without changing denominators, holdout membership, or the `UNJUDGED` policy.
