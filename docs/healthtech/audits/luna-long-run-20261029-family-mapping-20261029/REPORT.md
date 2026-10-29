# HT-M2 family-mapping sensitivity report

## Objective and scope

This package tests whether explicit family metadata from locally cached Google Patents pages changes evaluator group structure for the current Boston Scientific WATCHMAN, Stryker Neurovascular, and Cook Medical Zenith device-patent cohorts.

Included:

- a parser for the explicit `section itemprop=family` / `h2 ID=...` fields in cached pages;
- manifest and source-registry size/hash validation before parsing;
- evaluator-only family-aware group construction through the existing `shared_reference_groups` helper;
- focused regression coverage for parser behavior, mutation rejection, source separation, and group merging.

Excluded:

- runtime retrieval inputs, controller observations, rankings, or candidate universes;
- evaluator relation files or gold-derived labels in runtime code;
- semantic relevance judgments, patent-family legal opinions, FTO, clinical review, or public release;
- provider calls, paid inference, Bridge acquisition, and external outreach.

## Deliverable

The build script writes a versioned mapping with per-patent source ID, source URL/revision, raw-page hash, and an explicit family-section locator. The analysis script compares exact-patent groups with groups derived from those sourced family IDs. Both scripts fail closed on malformed manifests, missing raw pages, raw hash/size mutations, conflicting mappings, or unsupported source policy IDs.

The local mapping artifact is ignored evidence at `results/healthtech/ht-google-family-mapping-20261029-r1/family-mapping.json`. The analysis artifacts are ignored evidence at `results/healthtech/ht-family-group-analysis-20261029-r1/development.json` and `results/healthtech/ht-family-group-analysis-20261029-r1/final_holdout.json`.

## Evidence

| Acceptance criterion | Status | Evidence |
| --- | --- | --- |
| Recover only explicit family IDs from permitted local source pages | PASS | `build_google_family_mapping.py`; mapping status `SOURCED_LOCAL_EVALUATOR_MAPPING`; 24/24 mapped |
| Preserve source identity and raw-file integrity | PASS | manifest size/hash checks plus source-registry raw hash checks; mutation regression passes |
| Keep evaluator metadata out of runtime inputs | PASS | `analyze_family_groups.py` consumes a separate mapping and existing reference/group inputs; regression asserts no evaluator fields are emitted by the mapping builder |
| Compare development and final-holdout group structure | PASS | development: 5 queries, 3 exact groups, 3 family-aware groups; holdout: 3 queries, 3 exact groups, 3 family-aware groups |
| Avoid unsupported scientific or legal claims | PASS | report records family metadata as uncertainty structure only; unlisted pairs remain unjudged |
| Keep paid/provider boundary unchanged | PASS | 0 provider calls, 0 network acquisitions, 0 neural calls, `$0.00` paid cost |
| Full repository suite, controlled subprocess environment | PASS | explicit `PYTHONPATH=src` propagation -> `350 passed`, one existing `fitz` deprecation warning |
| Default full-suite invocation | SETUP DISTINCTION | two pre-existing child-process import failures in `tests/test_release_budget_process.py`; controlled rerun passes |

## Source and artifact matrix

| Item | Source or path | Result |
| --- | --- | --- |
| Boston cohort | `results/healthtech/ht-boston-watchman-20261028-r4` | 7 patents, 5 families |
| Stryker cohort | `results/healthtech/ht-stryker-neurovascular-20261029-r1` | 13 patents, 10 families |
| Cook cohort | `results/healthtech/ht-cook-zenith-20261029-r1` | 4 patents, 4 families |
| Combined mapping | `results/healthtech/ht-google-family-mapping-20261029-r1/family-mapping.json` | 24 patents, 19 families, 0 unmapped |
| Development analysis | `results/healthtech/ht-family-group-analysis-20261029-r1/development.json` | 5 queries, 3 exact / 3 family-aware groups, 0 merges |
| Final-holdout analysis | `results/healthtech/ht-family-group-analysis-20261029-r1/final_holdout.json` | 3 queries, 3 exact / 3 family-aware groups, 0 merges |

## Synthesis

The sourced mapping is useful as evaluator-side provenance and uncertainty metadata. In this slice, it does not alter the observed group partition: no two exact-patent groups share a sourced family ID. That is a descriptive result for this cohort, not evidence that family-aware grouping is unnecessary in general. The cohort still uses product-level disclosure links and does not provide independent semantic relevance gold.

## Risks and limitations

- Google family-section IDs are source metadata, not a legal or semantic family adjudication.
- The three cohorts are local research inputs under recorded rights policies; the audit does not grant redistribution rights.
- The mapping is not added to runtime JSON, retrieval inputs, controller observations, or production exports.
- Current results do not support pooled scientific generalization, exhaustive recall, FTO, clinical suitability, patent validity, investment merit, or publication readiness.
- In this uninstalled checkout, the default full-suite command does not propagate the pytest source path to child processes. The explicit `PYTHONPATH=src` process-level rerun passes and is the accepted full-suite verification.
- A licensed relevance-judgment cohort with multiple independent groups and an untouched final holdout remains unimplemented.

## Handoff

Status is `READY_FOR_REVIEW` for the offline family-mapping package. The next actor should source or authorize a rights-cleared relevance-judgment cohort, freeze its universe and holdout rules before scoring, and retain all failed queries and unjudged pairs. No additional paid authorization is requested by this package.
