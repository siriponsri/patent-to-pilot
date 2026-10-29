# M20 report

## Decision

Run the existing offline controls across all four company-held-out views. The
experiment passes as descriptive development sensitivity evidence and should
replace the prior single-company transfer summary in the next-action ledger.
It does not unlock a pooled scientific claim or paid HT-B4.

## Inputs and method

- Reused hashed local snapshots for Boston Scientific WATCHMAN, Stryker Neurovascular, Cook Medical Zenith, and Philips cardiovascular devices.
- Bound the existing sourced evaluator-only family mapping without changing runtime inputs.
- Composed one frozen view per held-out company using `compose_multicompany_cohort.py`.
- Ran the unchanged HT-B0a/B0b/B1/B2/B3 runner at `K=20`, candidate depth 31, and rerank depth 31 on development and final-holdout views.
- Loaded evaluator references only after raw rankings were written, preserving runtime/evaluator separation.

## Findings

All eight splits completed with zero failed devices and no provider/network
activity. Holdout macro Recall@20 was lowest on the Stryker transfer case for
B0a, B0b, B1, and B3; B2 was lowest on Cook. The observed holdout means across
the four company views were B0a `0.847024`, B0b `0.952381`, B1 `0.938690`, B2
`0.908929`, and B3 `0.938690`.

These are known-link recovery measurements against product-level disclosure
relations. They are not semantic claim relevance, clinical truth, patent
validity, FTO, exhaustive recall, investment evidence, or proof that one method
is better. The small per-company holdouts and repeated shared corpus keep
generalization uncertainty descriptive.

## Boundaries

Implemented: reusable orchestration, per-company frozen views, baseline reruns,
hash-bound receipts, command logging, and focused regression coverage.

Not run: rights-cleared expert semantic judgments, final pooled inference,
live/provider HT-B4, participant studies, commercial validation, deployment,
outreach, public raw-data release, clinical/FTO analysis, patent validity, or
publication acceptance.

## Next action

Obtain or authorize the semantic judgment source, preserve the 341-pair
unjudged policy and current holdout contract, ingest only explicit labeled rows,
then rerun the frozen controls before any pooled claim. Keep the paid branch
`BLOCKED_LOCAL` until exact pricing, provider identity, transfer rights, and
ledger reconciliation are evidenced.
