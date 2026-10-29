# HT-M11 budget refresh

Status: `PASS_REPORT_AND_BUDGET_REFRESH_NO_EXTRA_SPEND`

## Objective

Record the decision impact of the M11 consolidated report refresh and update the non-submitted budget/data expansion request without opening a paid/provider branch.

## Outcome

The M11 report contains 12 rows: five development controls, five final-holdout controls, one development HT-B4 provider-shaped mock row, and one final-holdout HT-B4 provider-shaped mock row. The untouched 3-device/24-patent holdout records B4 macro/micro known-link Recall@20 of `0.8857142857142857/0.8461538461538461` across 8 provider-shaped calls and 120 rerank pairs. B4 matches HT-B3 and remains below HT-B0b, HT-B1, and HT-B2 on macro recall.

Simulated holdout debit is `$0.0008`; paid cost is `$0.00`; unknown/pending billing items are `0`; and no ledger breach is recorded. The budget request now records the holdout result and retains the recommendation of `$0.00` incremental authorization with no paid round opened.

## Verification

- The parent M11 report receipt was corrected so the `frontier_table.csv` SHA-256 is the exact 64-character digest.
- The budget request remains a draft and was not submitted; no provider request, credential/credit check, reservation, or paid spend occurred.
- Exact commands and outcomes are recorded in [`verification.json`](verification.json).

## Boundaries

- This is a documentation and evidence-index refresh; the underlying model outputs and source hashes were not rerun or changed.
- HT-B4 evidence remains provider-shaped mock evidence, not live-provider evidence.
- Known-link metrics remain descriptive product-disclosure recovery; unjudged pairs are not negatives.
- Semantic relevance gold, generalization, statistical significance, exhaustive recall, clinical/FTO, patent validity, investment, user validation, commercial validation, and publication readiness remain `NOT_RUN`, `NOT_ESTIMABLE`, or `NOT_VALIDATED` as applicable.
- Live HT-B4 remains `BLOCKED_LOCAL`; the budget request is `PENDING / NO EXTRA SPEND AUTHORIZED`.
