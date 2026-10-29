# HT-T1 relevance-judgment intake contract audit

- Run ID: `luna-long-run-20261029-relevance-contract-20261029`
- Date: `2026-10-29`
- Tested source commit: `2af198af8635f28c0d0b8ad8ed9be852b6e7bd98`
- Candidate package commit: `a194045d316d60951b914dd2d1ac61a481b7b043`
- Status: `PASS_ENGINEERING_OFFLINE`
- Scope: fail-closed intake and validation for a future rights-cleared semantic relevance-judgment cohort.

## Result

Added the `ht-relevance-judgment-cohort-v1` contract and CLI validator. The contract requires:

- Explicit `relevant` or `not_relevant` labels with source revision, source hash, rights policy, intended use, and locator.
- Separate semantic-judgment provenance; product-disclosure sources cannot be promoted to semantic gold.
- Runtime query/patent membership checks, raw/canonical patent identity checks, duplicate/conflicting-pair rejection, and source-hash binding.
- Required runtime exclusions for semantic judgments, split answers, gold-derived query variants, and family labels.
- Company/family split-overlap rejection before a final holdout is accepted.
- Open-world accounting where every absent query-patent pair remains `unjudged` and is never recoded as a negative.

No real semantic labels were created. Tests use only explicitly marked `authored_fixture` rows, and the CLI smoke test produced a structural report with `2` judged pairs and `118` unjudged pairs.

## Verification

- Focused judgment/evaluator tests: `35 passed`.
- Controlled full repository suite with `PYTHONPATH=src` propagated: `361 passed, 1 warning`.
- Compile checks: exit `0`.
- CLI smoke: `PASS`; explicit unjudged count preserved as `118`.
- Provider calls, network acquisition, neural provider calls, and paid cost: `0` / `0` / `0` / `$0.00`.

Machine-readable details are in [`REPORT.md`](REPORT.md), [`verification.json`](verification.json), [`experiment-ledger.json`](experiment-ledger.json), and [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md).

## Limits

This package validates judgment provenance and split integrity; it does not supply expert labels, adjudicate medical suitability, establish patent validity/FTO, or resolve the Bridge rights/cohort blocker. Authored fixtures are engineering inputs only. A future real cohort still needs a rights review, independent company/family groups, frozen denominators, an untouched holdout, and actual source-backed judgments.

## Handoff

Use the validator when a licensed or otherwise rights-cleared judgment source is available. Keep the paid/provider branch, public raw-data release, deployment, outreach, clinical/FTO analysis, and Claude UX/UI paused or blocked on their existing gates.
