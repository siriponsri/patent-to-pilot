# M12 paired group uncertainty diagnostic

Status: `PASS_DESCRIPTIVE_ANALYSIS_NOT_ESTIMABLE`

This audit records the paired group diagnostic added after the M11 report and budget refresh. It preserves the frozen family-aware development and final-holdout artifacts, aligns methods by `group_id` at `K=20`, and reports descriptive deltas against the fixed `HT-B0b` baseline.

## Scope

- Base code revision: `fa507ec44fd40ee216b5d92c39ef2c86054cfe9b`
- Implementation revision: `d4f4881c6192a0107fac6702909d6970920e3067`
- Endpoint: macro known-link recall at `K=20`
- Baseline: `HT-B0b`
- Minimum effective group threshold: `5`
- Development effective groups: `3`
- Final-holdout effective groups: `3`
- Paid provider calls: `0`
- Paid cost: `$0.00`

The threshold is not met in either split. The diagnostic therefore reports mean deltas, population standard deviation, and min/max deltas with status `NOT_ESTIMABLE`; it does not report significance, confidence intervals, or a confirmatory superiority claim.

## Observed paired deltas

| Split | Comparison | Mean delta | Population SD | Min | Max | Status |
|---|---|---:|---:|---:|---:|---|
| development | HT-B0a - HT-B0b | -0.0516 | 0.0730 | -0.1548 | 0.0000 | NOT_ESTIMABLE |
| development | HT-B1 - HT-B0b | 0.0000 | 0.0000 | 0.0000 | 0.0000 | NOT_ESTIMABLE |
| development | HT-B2 - HT-B0b | 0.0000 | 0.0000 | 0.0000 | 0.0000 | NOT_ESTIMABLE |
| development | HT-B3 - HT-B0b | 0.0000 | 0.0000 | 0.0000 | 0.0000 | NOT_ESTIMABLE |
| final_holdout | HT-B0a - HT-B0b | -0.1333 | 0.1886 | -0.4000 | 0.0000 | NOT_ESTIMABLE |
| final_holdout | HT-B1 - HT-B0b | -0.0190 | 0.1406 | -0.2000 | 0.1429 | NOT_ESTIMABLE |
| final_holdout | HT-B2 - HT-B0b | -0.0190 | 0.1406 | -0.2000 | 0.1429 | NOT_ESTIMABLE |
| final_holdout | HT-B3 - HT-B0b | -0.0667 | 0.0943 | -0.2000 | 0.0000 | NOT_ESTIMABLE |

The observed wall-time/recall frontier remains `HT-B0a` and `HT-B0b` in both frozen views. The HT-B4 row remains provider-shaped mock evidence only; its development recall matches `HT-B0b` and `HT-B2`, with simulated debit `$0.0012` and paid cost `$0.00`.

## Reproduction

Run from the repository root:

```text
rtk proxy python -B scripts/healthtech/analyze_long_run.py --summary docs/healthtech/audits/luna-long-run-20261029-m11-report-refresh-20261029-r2/summary_tables.json --dev-frontier results/healthtech/ht-multicompany-baselines-20261029-family-r1-dev/frontier_diagnostics.json --holdout-frontier results/healthtech/ht-multicompany-baselines-20261029-family-r1-holdout/frontier_diagnostics.json --output docs/healthtech/audits/luna-long-run-20261029-m12-group-uncertainty-20261029 --code-commit d4f4881c6192a0107fac6702909d6970920e3067
```

Focused verification already completed:

```text
rtk proxy python -m pytest -q tests/test_healthtech_long_run_analysis.py tests/test_healthtech_long_run_report.py
4 passed

rtk proxy python -m compileall -q scripts/healthtech/analyze_long_run.py tests/test_healthtech_long_run_analysis.py
exit 0
```

The real generation completed with `PASS_DESCRIPTIVE_ANALYSIS_NOT_ESTIMABLE` and wrote the six output artifacts listed in `verification.json`.

## Files

- Machine-readable analysis: [`analysis.json`](analysis.json)
- Human-readable analysis: [`ANALYSIS.md`](ANALYSIS.md)
- Machine-readable verification: [`verification.json`](verification.json)
- Continuation note: [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md)
- Frontier table: [`quality_cost_frontier.csv`](quality_cost_frontier.csv)
- Development figure: [`quality_cost_development.svg`](quality_cost_development.svg)
- Holdout figure: [`quality_cost_holdout.svg`](quality_cost_holdout.svg)
- Recall comparison figure: [`recall_comparison.svg`](recall_comparison.svg)

## Boundaries

- Semantic relevance gold and expert adjudication: `NOT_RUN`.
- Statistical significance, power, confidence intervals, and confirmatory superiority testing: `NOT_RUN` / `NOT_ESTIMABLE`.
- Generalization beyond the frozen groups: `NOT_ESTIMABLE`.
- Live/provider HT-B4: `BLOCKED_LOCAL`; provider calls in this package: `0`.
- User, commercial, clinical, FTO, patent-validity, investment, and publication claims: `NOT_VALIDATED`, `NOT_RUN`, or out of scope.
- Product-level disclosed links remain a documented-link benchmark proxy. Unjudged pairs remain unjudged and are not negatives.

## Next action

Obtain or authorize a rights-cleared semantic judgment source with explicit `relevant` / `not_relevant` labels, source revision and SHA-256, rights policy, adjudicator role, exact locators, multiple independent company/family groups, and a predeclared untouched final holdout. Apply the existing relevance-judgment contract without changing the frozen denominator or holdout, then rerun `HT-B0a`, `HT-B0b`, `HT-B1`, `HT-B2`, and `HT-B3`.
