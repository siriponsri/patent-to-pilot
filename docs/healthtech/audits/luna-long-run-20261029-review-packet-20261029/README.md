# HT-T3 relevance review packet audit

## Objective

Freeze a provenance-bound semantic-review denominator over the current
Boston Scientific, Stryker Neurovascular, and Cook Medical runtime cohort
without creating semantic relevance gold or promoting product-disclosure
relations into labels.

## Deliverable

The implementation adds:

- `src/patent_to_pilot/evaluation/healthtech/review_packet.py`
- `scripts/healthtech/prepare_relevance_review_packet.py`
- `tests/test_healthtech_review_packet.py`

The real local packet is written at
`results/healthtech/ht-relevance-review-20261029-r1/packet.json` and is kept
outside the staged audit because it is a local metadata artifact bound to
restricted local research inputs.

The packet freezes `8` queries, `24` runtime patents, and `192` query-patent
pairs. All `192` pairs remain `UNJUDGED`; the packet contains `0` semantic
labels, no `label`/`gold`/`known_link` fields, no disclosure evidence rows, and
no copied patent text. It preserves the existing `3` company groups and the
predeclared `3`-query Stryker final holdout. Sourced Google family metadata is
recorded as evaluator-side provenance only.

## Verification

- Focused review-packet and relevance-contract tests pass `15/15`.
- Controlled full suite passes `368/368` with one existing warning.
- `compileall` passes with exit `0`.
- The real CLI build passes with `8` queries, `24` patents, `192` pairs, and
  `0` semantic labels.
- The generated packet is metadata-only and preserves the open-world policy:
  absent pairs remain unjudged, not negative.
- Provider calls, network acquisition, neural inference, and paid cost are
  all `0`; the cohort was reused from existing local snapshots.

Machine-readable evidence is in `verification.json` and
`experiment-ledger.json`.

## Boundaries

This package does not acquire expert labels, claim semantic relevance, verify
clinical suitability, determine patent validity/FTO, or authorize external
sharing. The source registry still records local-research rights and the
packet marks semantic-judgment clearance as unresolved. Bridge remains
`BLOCKED_LOCAL`; live/provider HT-B4 remains blocked; Claude UX/UI remains
paused.

## Next action

Supply or authorize a rights-cleared semantic judgment source with explicit
labels, source revision/hash, adjudicator role, and locators. Apply the
existing `ht-relevance-judgment-cohort-v1` contract to those labels, keep the
192-pair denominator and company/family split fixed, then rerun HT-B0a/B0b/B1/
B2/B3 before making any pooled scientific claim.
