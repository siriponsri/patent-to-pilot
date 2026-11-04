# Business-value scenario package - 2026-11-03

Status: `PASS_SCENARIO_ONLY_NOT_OBSERVED_BUSINESS_VALIDATION`.

This package separates measured machine-side workflow evidence from
illustrative labor and infrastructure assumptions. It is intended to make the
practical-cost discussion reproducible in the manuscript; it is not user
validation, revenue, willingness-to-pay, ROI, or a production cost claim.

## Observed inputs

- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Named real-device cases: `3`
- Mean local-vector HTTP time: `33.023` seconds per case
- Mean guided local Qwen generation time: `38.960` seconds per case
- Combined observed machine time: `71.983` seconds per case
- Combined observed machine time in hours: `0.0199952778`
- Human review time: not measured
- GPU price: not observed
- Paid API cost: not observed because the paid branch did not dispatch

The three cases passed the recorded engineering workflow checks for source
inspection, history, and JSON export. That is a developer-side operational
proxy only; it is not an independent user study or customer result.

## Scenario formula

Illustrative unit cost is calculated as:

`human_hours * labor_rate_usd_per_hour + observed_machine_hours * gpu_rate_usd_per_hour`

The scenario excludes support, storage, API charges, review rework, and any
commercial overhead. Those omissions are intentional because they were not
measured in this solo computational round.

The lower, central, and upper rows are sensitivity assumptions, not observed
workflow outcomes. Their purpose is to show how a decision-maker can replace
the assumptions with measured review time and an approved infrastructure rate.

## Interpretation boundary

The package supports a potential-value discussion about citation/locator
integrity, evidence coverage, machine time, and cost-quality trade-offs. It
does not establish that the system saves human time, reduces total dossier
cost, generates revenue, or earns a positive ROI. No external participant,
buyer, or customer was involved.

Machine-readable inputs and calculations are in `scenario.json` and
`scenario.csv`; source hashes are recorded in `verification.json`.
