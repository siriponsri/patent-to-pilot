# HT-M3 family-aware frontier audit

- Run ID: `luna-long-run-20261029-family-frontier-20261029`
- Date: `2026-10-29`
- Tested source commit: `4f4ed62a2649d720d3840aea2e1a8132b11617f2`
- Committed package revision: `0db213fe46d591bb5c3f83a7d3d188256fe14f0c`
- Status: `PASS_OFFLINE_FAMILY_FRONTIER_ANALYSIS`
- Scope: evaluator-side re-projection of the frozen Boston Scientific/Cook development frontier and Stryker company holdout frontier onto the sourced Google family mapping.

## Result

The new analyzer adds family-aware group rows and frontier-prefix diagnostics without changing rankings, runtime inputs, exact-patent metrics, or evaluator relations.

- Development: `5` queries, `3` exact groups, `3` family-aware groups, `0` merges, `9` frontier rows.
- Final holdout: `3` queries, `3` exact groups, `3` family-aware groups, `0` merges, `9` frontier rows.
- Every method/cutoff group result and every frontier row matches the existing exact-group result after normalizing group identity by query set.
- Family-aware uncertainty remains `NOT_ESTIMABLE`; the analysis does not create a new independent sample or semantic gold.

## Verification

- `tests/test_healthtech_family_mapping.py`: `5` passed.
- The controlled full repository suite with `PYTHONPATH=src` propagated passes `351` tests with one existing `fitz` deprecation warning.
- `rtk proxy python -m compileall -q scripts/healthtech/analyze_family_frontier.py tests/test_healthtech_family_mapping.py`: exit `0`.
- Real development and holdout reprojections both exit `0` with `PASS_OFFLINE_FAMILY_FRONTIER_ANALYSIS`.
- Provider calls, network acquisition, neural inference, and paid cost are `0` / `$0.00`.

Machine-readable details are in [`verification.json`](verification.json), [`experiment-ledger.json`](experiment-ledger.json), and [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md).

## Limits

This package is a sensitivity/provenance analysis over already frozen local baselines. Family IDs are explicit Google Patents metadata under the recorded local-research policy; they are not legal family adjudication, semantic relevance, patent validity, FTO, clinical suitability, investment merit, or publication evidence. Unlisted device-patent pairs remain unjudged.

The development and holdout outputs remain descriptive. No new licensed relevance-judgment cohort was acquired, and no paid branch was opened.

## Handoff

The next information-gaining package is a rights-cleared relevance-judgment cohort with multiple independent company/family groups and a predeclared untouched final holdout. Keep Bridge acquisition and live/provider HT-B4 gated on their existing rights, identity, pricing, transfer, and ledger conditions.
