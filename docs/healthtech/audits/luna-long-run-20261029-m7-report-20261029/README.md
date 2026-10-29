# HealthTech long-run report audit

- Run ID: `luna-long-run-20261029-m7-report-20261029`
- Date: `2026-10-29` (Asia/Bangkok)
- Status: `PASS_REPORT_GENERATED_PARTIAL_LONG_RUN`
- Scope: build one reproducible report from frozen HT-B0a/B0b/B1/B2/B3 development and holdout artifacts plus the HT-B4 provider-shaped mock; prepare the next G5/G6 handoff materials; refresh the budget draft with the exact current endpoint snapshot.
- Implementation commit used by the report builder: `237fc669a4b7829be420c48547f36a69e28f64f0`
- Tree state: unrelated owner artifacts were preserved; no Claude UX/UI worktree was touched.

## Outcome

The report builder read only local frozen artifacts and wrote `REPORT.md`, `summary_tables.json`, `frontier_table.csv`, and `receipt.json`. The report contains 10 offline baseline rows plus one B4 mock row. The development view contains 5 queries/devices and 24 patents; the untouched Stryker holdout contains 3 queries over the same 24-patent universe. The B4 mock contains 12 structured provider-shaped calls, 12 schema-valid responses, simulated debit `USD0.0012`, paid cost `USD0.00`, and zero unknown or pending ledger items.

The package remains partial. Product-level disclosed links are not semantic relevance gold. Live/provider execution, paid canary/pilot, semantic judgment intake, statistical significance, user validation, commercial validation, and publication readiness remain `NOT_RUN`, `BLOCKED_LOCAL`, or `NOT_VALIDATED` as stated in the report.

## Included artifacts

- [`REPORT.md`](REPORT.md) — generated human-readable report.
- [`summary_tables.json`](summary_tables.json) — source-bound structured summary and input hashes.
- [`frontier_table.csv`](frontier_table.csv) — compact development/holdout/B4 frontier table.
- [`receipt.json`](receipt.json) — report-generation receipt and limitations.
- [`verification.json`](verification.json) — commands, outcomes, hashes, and boundaries.
- [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md) — continuation conditions.

Related prepared materials:

- [`../../business/PILOT_TASK_PACKET_20261029.md`](../../business/PILOT_TASK_PACKET_20261029.md)
- [`../../research/G6_MANUSCRIPT_METHODS_SKELETON_20261029.md`](../../research/G6_MANUSCRIPT_METHODS_SKELETON_20261029.md)
- [`../../goals/luna-long-run-20261028-889958e/BUDGET_EXPANSION_REQUEST_TH.md`](../../goals/luna-long-run-20261028-889958e/BUDGET_EXPANSION_REQUEST_TH.md)
