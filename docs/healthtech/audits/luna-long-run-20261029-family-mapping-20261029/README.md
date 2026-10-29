# HT-M2 family-mapping sensitivity audit

- Run ID: `luna-long-run-20261029-family-mapping-20261029`
- Date: `2026-10-29`
- Tested source commit: `c0610110bfd8962948445cd525713f9d58e219fd`
- Status: `PASS_OFFLINE_FAMILY_SENSITIVITY`
- Scope: local, evaluator-side family metadata recovery and group-structure sensitivity for the Boston Scientific, Stryker Neurovascular, and Cook Medical cohorts.
- Parent context: current offline device-patent development package; live/provider HT-B4 and Bridge acquisition remain `BLOCKED_LOCAL`.

## Result

The new parser recovered explicit Google Patents family-section identifiers from the cached local patent pages without reading evaluator relations or changing runtime inputs.

- `24/24` patents mapped.
- `19` Google family IDs observed.
- `0` unmapped patents.
- Development grouping stayed at `3` exact groups and `3` family-aware groups across `5` reference queries.
- Final-holdout grouping stayed at `3` exact groups and `3` family-aware groups across `3` reference queries.
- `0` family merges crossed existing exact-patent groups in either analysis.

The result improves provenance and uncertainty visibility, but it does not change the current group structure or create semantic relevance labels.

## Verification

- Family parser, source/hash validation, evaluator/runtime separation, mutation rejection, and family-group merging regressions pass.
- The focused HealthTech selection passes `80` tests.
- The full repository suite with `PYTHONPATH=src` propagated into subprocesses passes `350` tests with one existing `fitz` deprecation warning.
- The unqualified full-suite invocation has a setup-only failure in two pre-existing subprocess tests because this checkout is not installed; the controlled `PYTHONPATH=src` rerun is the valid process-level verification.
- `rtk proxy python -m compileall -q src scripts tests` exits `0`.
- Provider calls, network acquisition, neural inference, and paid cost are all `0` / `$0.00`.

Machine-readable details are in [`verification.json`](verification.json), [`experiment-ledger.json`](experiment-ledger.json), and [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md).

## Limits

The family ID is sourced metadata from an explicit Google Patents family section and is retained under the `google-patents-pages` local-research policy. It is not semantic relevance evidence, exhaustive recall, patent validity, FTO, clinical suitability, investment merit, or public redistribution permission. Unlisted pairs remain unjudged; no negative labels or final-holdout claims were created.

No raw HTML, evaluator-only relations, credentials, private local paths, or third-party restricted payloads are staged in this audit folder.

## Handoff

The next information-gaining package is a rights-cleared relevance-judgment cohort with multiple independent company/family groups and a predeclared untouched final holdout. Keep paid provider work gated on current identity, pricing, transfer-rights, payload, and ledger-reconciliation evidence.
