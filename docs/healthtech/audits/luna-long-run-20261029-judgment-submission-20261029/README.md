# HT-T4 relevance-submission adapter audit

## Objective

Make the frozen semantic-review packet executable as a fail-closed intake
boundary: an authorized reviewer submission must bind to an existing packet
row, an explicit label, a registered source revision/SHA-256, and a locator
before it can enter `ht-relevance-judgment-cohort-v1`.

## Deliverable

Added:

- `src/patent_to_pilot/evaluation/healthtech/judgment_submission.py`
- `scripts/healthtech/ingest_relevance_judgments.py`
- `tests/test_healthtech_judgment_submission.py`

The adapter accepts partial submissions and leaves all omitted packet rows
unjudged. It rejects unknown packet rows, duplicate pairs, missing expert
roles, source drift, unsupported bases, and product-disclosure source classes.
It preserves the runtime's numeric source token as
`patent_id_runtime_raw` while the judgment contract uses the verified
canonicalizable ID in `patent_id_raw`/`patent_id_canonical`.

## Verification

- Focused submission, packet, and contract tests pass `20/20`.
- Controlled full suite passes `373/373` with one existing warning.
- `compileall` passes with exit `0`.
- Temporary end-to-end CLI smoke passes with one synthetic fixture label:
  `1` judged pair, `191` unjudged pairs, and `NOT_ESTIMABLE` generalization.
- No real semantic labels were created, persisted, or claimed.
- Provider calls, network acquisition, neural inference, and paid cost remain
  `0`; the smoke used only a temporary synthetic source.

## Boundaries

This package does not authorize adjudication, acquire expert labels, or turn
the local product-disclosure sources into semantic gold. The 192-pair packet,
company split, and Stryker holdout remain unchanged. A future real submission
must provide a separately rights-cleared source manifest with an explicit
semantic intended use and allowed local decision.

## Next action

Obtain or authorize the real rights-cleared semantic source, run this adapter
against the frozen packet, inspect the validation report, and only then rerun
HT-B0a/B0b/B1/B2/B3. Keep missing labels as unjudged and keep family-aware
generalization `NOT_ESTIMABLE` until family mapping is bound to the judgment
split.
