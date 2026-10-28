# Handoff receipt

Result: `READY_FOR_REVIEW`, not goal complete.

The local history race is fixed with same-filesystem staging and atomic hard-link publication. A reader paused while a writer owns an unpublished staging file sees the last committed chain only; a concurrent same-version writer cannot overwrite the winner. Abandoned hidden staging files can be recovered by age without modifying committed versions.

The new Abbott adapter reads `runtime.json`, `source_registry.json`, the PMA snapshots, the raw Abbott product disclosure page, and the raw patent pages. It does not read `evaluator/references.json`. Each case starts with the BM25/SQLite FTS5 local lexical baseline, retains ordinary `retrieved_candidate` entries, and annotates or appends independently disclosed `disclosed_link` entries with source-backed evidence.

Generated local outputs cover MitraClip, Tendyne, and TriClip. Each includes the dossier, acquisition events, sanitized case manifest, source viewer result, history versions 1 and 2, a user edit, and JSON/English/Thai exports. Counts are recorded in `verification.json` and the case manifests.

The development freeze is deliberately narrow: one company, three devices, 41 patent documents, 61 independently parsed product-level disclosed pairs, and 62 unjudged distractor pairs. Shared exact-document overlap is recorded; family identity remains unknown. No holdout, exhaustive recall, semantic relevance, clinical suitability, FTO, patent validity, investment merit, or public-release claim is made.

Package C now also has a fresh query-matched fixed-prefix frontier at `results/healthtech/ht-real-baselines-20261028-r7/`. At K=20, the terminal macro known-link recall is `0.442739` for HT-B0a, `0.662242` for HT-B0b, `0.498802` for HT-B1, `0.568912` for HT-B2, and `0.498802` for HT-B3. The artifact records actual query calls, rerank pairs, embedding/rerank tokens, CPU/wall time, per-prefix reached/not-realized queries, and descriptive exact-patent group rows. The first query hash matches across HT-B1/B2/B3. Confidence intervals are `NOT_ESTIMABLE` because the slice has three queries, two exact-patent groups, one company group, unknown family mapping, and no final holdout; see `frontier_summary.json`.

Rights are mixed. The openFDA terms support public-domain treatment of openFDA material unless an exception applies, with requested attribution. The Abbott page is a product-level legal notice, not a claim-level or redistribution license. Google Patents page rights were not resolved to a source-specific redistribution grant. The generated dossier text therefore remains local-only and product display/redistribution is `BLOCKED_LOCAL` for the third-party disclosure/patent material.

Next work is listed in `NEXT_ACTIONS.md`.
