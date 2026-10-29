# HT-M3 family-aware cohort freeze audit

- Run ID: `luna-long-run-20261029-family-freeze-20261029`
- Date: `2026-10-29`
- Tested source commit: `1e1c463787bf1a494c6d9c99367cebda5a2bfea5`
- Candidate package commit: `PENDING_FIRST_COMMIT`
- Status: `PASS_OFFLINE_ANALYSIS`
- Scope: deterministic family-aware freeze of the Boston Scientific, Stryker Neurovascular, and Cook Medical composite cohort.
- Parent context: sourced family mapping and family-aware frontier re-projection remain evaluator-side sensitivity packages; Bridge acquisition and live/provider HT-B4 remain `BLOCKED_LOCAL`.

## Result

The composite builder now accepts an optional sourced family mapping, records evaluator-only family groups and mapping metadata, and rejects any family group that crosses the development/final-holdout split. The new derived local composite contains:

- `8` devices, `24` patents, `31` disclosed product-level pairs, and `161` unjudged distractor pairs.
- `6` full-cohort family groups, `3` development family groups, and `3` final-holdout family groups.
- `0` family split overlaps and `0` newly acquired bytes.
- A typed-rights provenance receipt covering `31/31` disclosed pairs with `0` unresolved rights policies.

The family-aware composite is frozen for future evaluator-side work. Existing HT-B0a/B0b/B1/B2/B3 baselines remain bound to the earlier composite manifest; this package does not claim a new baseline run under the family-aware manifest.

## Verification

- Focused family/cohort regressions pass `10/10`.
- The controlled full repository suite passes `353` tests with one existing warning when `PYTHONPATH=src` is propagated to child processes.
- Compile checks pass with exit `0`.
- The family-aware composition command exits `0` and records cohort SHA-256 `0f35a29ccc08ce5980f22dc0a3de9b1ce834a67165efa66796c157da0927d52b`.
- The reviewed typed-rights provenance verification exits `PASS` with manifest hash `a961c551d094f70720420e53023e806b7fa248c6b30da248ff9332a1d319a5e5`.
- Provider calls, network acquisition, neural inference, and paid cost are `0` / `0` / `0` / `$0.00`.

Machine-readable details are in [`REPORT.md`](REPORT.md), [`verification.json`](verification.json), [`experiment-ledger.json`](experiment-ledger.json), and [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md).

## Limits

Family IDs are sourced Google Patents metadata retained under the recorded local-research policy. They are not semantic relevance judgments, legal family adjudication, exhaustive recall, patent validity, FTO, clinical suitability, investment merit, or publication evidence. Product-level disclosure links remain structural source-backed references rather than independent expert gold. Unlisted pairs remain unjudged and are not recoded as negatives.

No raw restricted payloads, credentials, evaluator-only relations, or private local files are staged in this audit folder. The derived cohort continues to follow the parent rights matrix and does not grant redistribution permission.

## Handoff

The next information-gaining package is a rights-cleared relevance-judgment cohort with multiple independent company/family groups and a predeclared untouched final holdout. Keep the paid provider branch, Bridge branch, public raw-data release, clinical/FTO work, deployment, outreach, and Claude UX/UI paused or blocked on their existing gates.
