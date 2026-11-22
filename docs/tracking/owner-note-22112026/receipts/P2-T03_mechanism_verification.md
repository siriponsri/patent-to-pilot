# P2-T03 — One bounded source-relation search action: verification

**Status:** implemented and verified on SYNTHETIC packets only (22 Nov 2026). **Evidence class:** engineering mechanism.
No research data was read, no benchmark or DEV split was touched, and no number below is a retrieval result.
**Spend:** USD 0 (no network, no model call, no download, no paid call). Specification:
[P2-T03_mechanism_spec.md](P2-T03_mechanism_spec.md).

## Files

| File | Change |
|---|---|
| `src/patent_to_pilot/workbench/relation_search.py` | New: the operator (pure `relation_search_step`), policy `ptp-relsel-first-unresolved/1.0.0` (pinned SHA-256 `e4ea084c…5629c`), eligibility mask, action budget, typed query material, evidence registry, reference in-memory BM25 backend/reranker, pure trace emitter, Workbench adapter `RelationSearchSlice` |
| `src/patent_to_pilot/workbench/trace_slice.py` | Additive: `TraceSlice._event` accepts `eligibility_profile_id` and `result_limit` keyword arguments whose defaults are the previous constants (P0-T06 output unchanged) |
| `tests/test_p2_t03_relation_search.py` | New: 19 tests on authored synthetic packets |

No store schema, fixture, provider, profile, budget-ledger or script file was changed.

## Synthetic packets used

* **Pure form:** an authored in-memory packet (every text starts with "SYNTHETIC"): a query with two exact requirement
  spans ("the sensor closes the valve", "the temperature exceeds the threshold"), eight one-paragraph documents with
  families and dates (the query document, an own-family member, a post-cutoff document, an undated document, a decoy
  that matches only the generated hypothesis "shutoff", and a document that matches the original requirements), a seed
  pool of two documents and five authored relation states (two unresolved actionable, one supported, one contradicted,
  one unresolved but not search-actionable). The coverage assessor is an authored test function.
* **Workbench form:** the existing P0-T06 synthetic letter / Annex A (decoy) / Annex B packet, unchanged, in fresh
  temporary stores, with real SQLite FTS5 BM25 searches.

## Required behaviour and the tests that check it

| Requirement | Test(s) | What is asserted |
|---|---|---|
| Preserve exact query requirements | `test_requirements_are_exact_spans_and_preserved_unchanged` | spans equal `query[start:end]`; wrong or ambiguous span refused; object frozen; record requirements and fingerprint equal the input; trace `original_query` and assessment spans resolve to the exact requirement |
| Named, versioned, pinned rule | `test_policy_is_named_versioned_and_pinned` | name/version, fingerprint equals the pin; record carries name and SHA-256; an edited policy with the same name is refused (`policy_unknown`) |
| Deterministic selection | `test_selection_is_deterministic_and_independent_of_input_order`, `test_selection_rule_order_keys_and_skips` | all 120 permutations of the five relation states give a byte-identical record; each sort key (requirement position, pool rank, reference offset, key) and each skip reason is exercised |
| Exactly one eligible global search within a budget | `test_exactly_one_expansion_search_within_the_action_budget`, `test_no_unresolved_relation_means_no_search`, `test_workbench_budget_of_one_runs_the_seed_only`, `test_workbench_operator_reproduces_the_p0_t06_action_and_records_it` | the backend is called exactly once even with two unresolved relations; a spent budget gives `budget_exhausted` with no search and no hypothesis generation; spending past the limit raises `BudgetExhausted`; no unresolved relation gives no search; Workbench: 2 FTS searches with the default budget, 1 with a budget of 1 |
| Eligibility masks | `test_eligibility_mask_filters_the_expansion_route_and_is_recorded`, `test_workbench_eligibility_mask_applies_to_both_routes`, `test_workbench_date_mask_keeps_a_late_annex_out_and_the_relation_unresolved` | exclusions recorded with exact reasons (`excluded_id`, `excluded_group:FAM-Q`, `date_not_before_cutoff`, `missing_date`) for candidates the backend really returned; none enters the pool; declared `include` admits the undated document; an ineligible pool before the action is refused; Workbench: excluding Annex A removes the decoy; a post-cutoff Annex B keeps the relation unresolved; a missing-date mask also empties the seed |
| Merge and new-candidate accounting | `test_merge_records_real_before_after_membership_and_new_candidates`, `test_workbench_operator_reproduces_the_p0_t06_action_and_records_it` | `after = before + (returned − before)`, `new = returned − before`; a re-found seed document is not new; backend duplicates are de-duplicated; record and trace agree; Workbench pools equal the P0-T06 slice's pools exactly |
| Coverage re-check | `test_coverage_is_rechecked_once_on_the_merged_pool` | assessor called once with the merged pool; selected relation unresolved → supported; requirement status stays unresolved because another relation of it is still open |
| Rerank against the original query only | `test_rerank_uses_only_the_original_query_so_expansion_cannot_win_by_self_matching`, `test_workbench_rerank_is_against_the_original_requirement_only` | the reranker receives exactly `RerankRequest(query_id, original text, requirement texts)` and no source-copied or hypothesis term; the hypothesis-only decoy is first by the expansion search and last after rerank; the new document matching the original requirements is first; out-of-pool scores refused; Workbench rerank expression equals the seed (requirement) expression and contains neither "coastal" nor "annex" |
| Hypothesis never cited | `test_a_generated_hypothesis_can_never_be_cited`, `test_workbench_hypothesis_is_typed_and_never_cited` | hypothesis appears only as `generated_search_hypothesis` and as a query artifact, never in evidence; an assessor citing it, a relation reference pointing at it, registry resolution, an id collision and the type gate all raise `HypothesisNotEvidence`; an edited event is caught by the semantic check |
| Schema-valid trace | `test_pure_form_emits_a_schema_valid_trace_and_tampering_is_caught`, `test_workbench_operator_reproduces_the_p0_t06_action_and_records_it` | pure and Workbench events have no schema or semantic errors; tampered pool sets / quotes are caught; an emitter that misreports the submitted query is refused (`trace_mismatch`) |
| P0-T06 unchanged | `test_p0_t06_events_keep_their_original_profile_and_limit`, the whole `tests/test_p0_t06_trace_slice.py` | P0-T06 events keep `eligibility_profile_id = synthetic-packet-current-versions-only` and `result_limit = 5`; all 22 P0-T06 tests pass |

## Observed on the P0-T06 packet (Workbench form, default mask and budget)

Seed (FTS5, requirement terms): `syn-letter@v1#clause-5`, `syn-letter@v1#clause-4`. Selected relation:
`annex-reference:ev:syn-letter@v1#clause-5[274:281]` (sort key `[0, 0, 274, …]`; the footnote binding was skipped as
`status_supported`). Submitted query: `"annex b" OR "installed" OR "seaside" OR "sites" OR "coastal"`, identical to P0-T06.
New candidates: Annex B heading, Annex A decoy, Annex B rule. Coverage: unresolved → supported. Original-query rerank:
the two seed clauses keep scores; all three new candidates are unscored and follow them. This is plumbing behaviour on
an authored packet, not evidence for or against the mechanism.

## Exact test results

Environment: Windows 11, Python 3.12.10, SQLite 3.49.1, jsonschema 4.26.0, pytest 8.4.2 (via `.venv` site-packages).
Command form: `python -c "import sys; sys.path.append(r'.venv/Lib/site-packages'); import pytest; sys.exit(pytest.main(['-q','-p','no:cacheprovider', <files>]))"`.

* `tests/test_p2_t03_relation_search.py`: **19 passed**.
* `tests/test_p2_t03_relation_search.py` + `tests/test_p0_t06_trace_slice.py` + G01/G02 regression
  (`test_ptp_g01_workbench.py`, `test_ptp_g02_datasets.py`, `test_ptp_g02_openrouter_profiles.py`,
  `test_ptp_g02_pdf_ingest.py`, `test_ptp_g02_providers.py`): **110 passed** (19 + 22 + 69).
* Full suite (`tests/`, `-rfEs`, run on the final code): **8 failed, 2553 passed, 6 skipped, 1 xfailed** in 327 s.
  The 8 failures are exactly the accepted pre-existing SACR supervisor budget tests
  (`test_sacr_r2_smoke_supervisor.py` and `test_sacr_r3_smoke_supervisor.py`,
  `test_budget_cannot_use_nonfinite_inflated_or_erased_cost[nan|inflated|erased|insufficient]`). The skips are the
  pre-existing ones (no `sklearn`, `PTP_TEST_DUCKDB` unset, 4 native-supervisor guards). The passed count is the P0-T06
  baseline 2534 plus the 19 new tests.

## Not done here

No P2-T04 screening, no DEV run, no protocol freeze, no commit. The policy must be frozen by name, version and
fingerprint in the P2-T04 protocol before any research number is computed with it.
