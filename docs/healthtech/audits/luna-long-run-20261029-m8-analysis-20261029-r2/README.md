# HealthTech long-run descriptive analysis audit

- Run ID: `luna-long-run-20261029-m8-analysis-20261029-r2`
- Date: `2026-10-29` (Asia/Bangkok)
- Status: `PASS_DESCRIPTIVE_ANALYSIS_NOT_ESTIMABLE`
- Scope: compute reproducible quality-resource frontiers, group spread, holdout-minus-development deltas, and deterministic SVG plots from the frozen M7 report and baseline frontiers.
- Analysis implementation commit: `862e74c0267d27f5d90c92a4d8d198d5d4b6682f`
- Tree state: unrelated owner artifacts were preserved; Claude UX/UI worktree was not touched.

## Outcome

The analysis reads only local frozen artifacts. HT-B0a and HT-B0b are on the observed Pareto frontier in both development and final holdout when the coordinates are macro known-link recall at `K=20` and realized wall time. HT-B1, HT-B2, and HT-B3 are dominated by HT-B0b on those observed coordinates. Holdout-minus-development deltas are reported descriptively by method. The B4 mock matches HT-B0b and HT-B2 on development recall, with simulated debit `USD0.0012` and paid cost `USD0.00`; it remains mock-only and is not provider evidence.

These findings do not establish method superiority, semantic relevance, exhaustive recall, clinical suitability, FTO, patent validity, investment merit, or generalization. The labels remain product-level disclosed links, unlisted pairs remain unjudged, and the effective group count is small.

## Included artifacts

- [`ANALYSIS.md`](ANALYSIS.md) — generated interpretation and tables.
- [`analysis.json`](analysis.json) — structured analysis, input hashes, frontier flags, and deltas.
- [`quality_cost_frontier.csv`](quality_cost_frontier.csv) — all development/holdout method rows with resources and Pareto flags.
- [`quality_cost_development.svg`](quality_cost_development.svg) — deterministic development scatter plot.
- [`quality_cost_holdout.svg`](quality_cost_holdout.svg) — deterministic holdout scatter plot.
- [`recall_comparison.svg`](recall_comparison.svg) — deterministic development/holdout bar comparison.
- [`verification.json`](verification.json) — commands, hashes, and boundaries.
- [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md) — continuation conditions.
