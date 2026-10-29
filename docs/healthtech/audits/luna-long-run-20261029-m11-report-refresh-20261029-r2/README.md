# HT-M11 consolidated long-run report refresh

Status: `PASS_REPORT_GENERATED_WITH_DEV_AND_HOLDOUT_B4`

## Objective

Refresh the reproducible long-run report so it includes both the frozen development HT-B4 provider-shaped mock and the successful final-holdout HT-B4 mock alongside the HT-B0a/B0b/B1/B2/B3 controls.

## Outcome

The report contains 12 frontier rows: 5 development controls, 5 final-holdout controls, one development B4 mock row, and one final-holdout B4 mock row. The development B4 mock records macro known-link recall@20 of `1.0000` across 12 provider-shaped calls, while the untouched holdout B4 mock records `0.8857` across 8 calls. On holdout, B4 matches HT-B3 and remains below HT-B0b, HT-B1, and HT-B2.

Both B4 rows are provider-shaped mock evidence only. Paid cost is `$0.00`; simulated debits are `$0.0012` for development and `$0.0008` for holdout; unknown/pending billing items remain zero. No live provider request, semantic relevance judgment, or paid canary was run.

## Verification

- `tests/test_healthtech_long_run_report.py` passes with optional holdout-B4 coverage.
- Compile checks pass for the report builder and regression test.
- The real generator writes `REPORT.md`, `summary_tables.json`, `frontier_table.csv`, and `receipt.json` in this directory.
- The initial generation attempt with a mistyped development receipt path failed before reading inputs and wrote no report rows; it is not used as evidence. The successful `-r2` run is the canonical output.

Exact commands, input hashes, output paths, and limits are recorded in [`verification.json`](verification.json). Continuation conditions are in [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md).

## Boundaries

- Known-link metrics remain descriptive recovery of product-level disclosed relationships; unjudged pairs are not negatives.
- Provider-shaped calls exercise the action schema and accounting path; they are not live-provider evidence.
- The small company-level holdout is not a generalization proof, statistical significance result, exhaustive-recall estimate, clinical/FTO assessment, patent-validity opinion, investment conclusion, or publication-readiness decision.
- Live HT-B4 remains `BLOCKED_LOCAL` pending explicit transfer rights, current credential/credit readiness, exact bounds, and reconciliation gates.
