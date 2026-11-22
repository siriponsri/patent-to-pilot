# P0-T06 — Source-bound synthetic search-and-trace slice: verification

**Status:** implemented and verified on a SYNTHETIC packet (22 Nov 2026). **Evidence class:** engineering plumbing only.
Everything in the packet is authored and fictional; no result here says anything about retrieval quality.
**Spend:** USD 0 (no network, no model, no download, no OCR, no paid call).

## What was built

| Piece | Where |
|---|---|
| Authored synthetic packet (letter with Clause 4/5/6 and footnote [1], separately filed Annex A (decoy) and Annex B, controlled revision Annex B v1 → v2 changing 60 C to 55 C) | `src/patent_to_pilot/workbench/fixtures/p0_t06_synthetic/packet.json` |
| Generated fixture artifacts per version: original PDF bytes, canonical UTF-8 text, layout (pages + node spans + regions), plus `MANIFEST.json` with SHA-256 of every file | same folder (`*.pdf`, `*.canonical.txt`, `*.layout.json`) |
| Slice engine, typed records, schema + semantic checks, CLI | `src/patent_to_pilot/workbench/trace_slice.py` |
| Verbatim copy of the owner event schema (SHA-256 `4ec5e368…40a3`) | `src/patent_to_pilot/workbench/schemas/evidence_trace.schema.json` |
| Additive store tables (`original_artifacts`, `source_pages`, `doc_nodes`, `doc_relations`, `source_evidence`, `search_hypotheses`, `bound_requirements`, `runtime_assessments`, `trace_events`) and two triggers that stop an id from being both source evidence and a hypothesis | `src/patent_to_pilot/workbench/store.py` (`SCHEMA_P0T06`, `CREATE … IF NOT EXISTS`) |
| Core extensions (no behaviour change for G01/G02 callers): optional explicit FTS5 `match` in `_lexical`; `extra(con)` hook inside the `_import_source` transaction; owner uploads now also keep their original bytes; `source_version()` reports `original_artifact`; synthetic projects refuse owner uploads | `src/patent_to_pilot/workbench/core.py` |
| Read-only API `GET /api/synthetic/trace-slice` (runs in a fresh temporary store) and one link on the Welcome page | `server.py`, `static/index.html` |
| Tests | `tests/test_p0_t06_trace_slice.py` (22 tests) |
| Emitted trace (this receipt's companion) | `docs/tracking/owner-note-22112026/receipts/P0-T06_synthetic_trace.json` |

## What the emitted trace shows (all executed; nothing in these sets is authored)

The receipt JSON is a wrapper (`ptp-p0-t06-trace-bundle/1`). Each element of `events` is one evidence-trace event that
validates against the owner schema; the wrapper itself is not an event.

1. **Source-bound requirement.** `syn-req-1` is the exact span `[5, 88)` of the question
   "What maximum operating temperature applies to enclosure units installed at seaside sites?".
2. **Seed search** (`seed_search`, real SQLite FTS5 BM25 over the current index, limit 5):
   `"maximum" OR "operating" OR "temperature" OR "enclosure" OR "units" OR "installed" OR "seaside" OR "sites"` →
   returned `syn-letter@v1#clause-5`, `syn-letter@v1#clause-4`. The Annex B rule is *not* in the pool
   (vocabulary mismatch is built into the synthetic text). The footnote binds to Clause 4 by closure inside the same
   immutable version (`qualifies`, scope = Clause 4 only). The runtime assessment is `unresolved`: Clause 5 references
   "Annex B" and no Annex B heading has been acquired.
3. **One structural expansion** (`structural_expansion`, selected assessment `asm-001`):
   `"annex b" OR "installed" OR "seaside" OR "sites" OR "coastal"`. Term provenance is recorded:
   `"Annex B"` is copied from source evidence `ev:syn-letter@v1#clause-5[274:281]`; `installed/seaside/sites` are
   original requirement terms specific to Clause 5; `coastal` is a **generated search hypothesis** (authored synonym
   table, no model call). Before = 2 nodes; returned = 4; new = Annex B heading, Annex B rule, **and the Annex A decoy**.
4. **Annex binding.** "Annex B" binds to exactly one acquired annex heading (`syn-annex-b@v1#annex-heading`,
   "Annex B. Coastal exception"); `incorporates` scope = the Annex B rule ("… may run up to 60 C."). The Annex A decoy
   entered the pool but is bound to nothing and is not cited (new membership ≠ relevance). The assessment after the
   action is `supported` (a structural coverage signal, `basis = runtime_not_gold`).
5. **Controlled revision** `SYN-REV-ANNEX-B-V2` through the same import transaction. Node IDs are per immutable version;
   v2 nodes carry `alignment` to their v1 anchors. Predicted before re-running:
   * changed node: `syn-annex-b@v1#annex-b-1` only;
   * re-check: the Annex B rule evidence (`cited_node_changed`), the Clause 5 evidence and its "Annex B" span
     (`governed_scope_changed` — unchanged text, but the scope it incorporates changed), the Annex B heading
     (`reanchor`: same text, new version), both Annex B relations (rebind), the assessment, and both searches
     (their search scope contained the superseded version);
   * retained without re-check: Clause 4, its footnote marker, the footnote, and the footnote `qualifies` relation.
   Executed re-check (two `replay_search` events): pool equivalent under alignment; observed replaced evidence ⊆
   predicted re-check set; every evidence/relation predicted "retained" was retained
   (`prediction_covers_every_observed_change = true`); the new assessment cites "… may run up to 55 C."; v1 text still
   resolves from the store but is no longer searchable (FTS for `"60"` returns nothing).

## Verified by tests (`tests/test_p0_t06_trace_slice.py`)

| Required check | Test(s) |
|---|---|
| Synthetic label present (packet, manifest, every document's first line and PDF, layout files, project `data_origin = synthetic_demo`, event `mode = synthetic_demo`, bundle label); synthetic project refuses owner uploads | `test_fixture_is_labelled_synthetic_and_regenerates_byte_identically`, `test_every_emitted_event_validates…`, `test_the_synthetic_project_refuses_owner_uploads` |
| Fixtures are exactly what the authoring code produces; tampering refused | `…regenerates_byte_identically`, `test_tampered_fixture_is_refused` |
| Original bytes, canonical text and page/region mapping are distinct artifacts with distinct hashes, and resolve after reopening the store | `test_original_bytes_canonical_text_and_regions_are_distinct_and_survive_restart` |
| Canonical text equals the PDF text layer (pypdf) and every node quote is on its page | `test_canonical_text_is_the_text_layer_of_the_original_pdf` |
| Spans resolve exactly (trace JSON and, independently, the store); requirement span resolves in the question | `test_every_cited_span_resolves_exactly_to_stored_text_and_original_bytes` |
| Before/after membership is real: each event's `returned_ids` equals an independent raw-SQLite FTS5 query; after = dedup(before ∪ returned); new = returned − before; baseline misses the annex rule; decoy not cited; run/actions recorded in the existing tables | `test_candidate_pools_are_real_fts5_membership_before_and_after_the_action`, `test_seed_assessment_is_unresolved_and_names_the_missing_annex` |
| Annex binding resolves to the referenced annex and its scope; an ambiguous label (two "Annex B" headings) is not bound | `test_annex_binding_resolves_to_the_referenced_annex_and_its_scope`, `test_an_ambiguous_annex_label_is_not_bound` |
| Hypothesis-as-evidence rejected: type gate, assessment, relation provenance, SQLite trigger, semantic check, schema | `test_generated_hypothesis_can_never_be_cited`, `test_trace_checks_reject_a_hypothesis_used_as_evidence` |
| Trace validates against the owner schema (jsonschema Draft 2020-12) and the semantic checks; tampering (quote, pool sets, original bytes, index manifest, relation scope, missing field, invoiced synthetic cost) is caught; the validator also accepts the owner's own synthetic example | `test_bundled_schema_is_the_owner_specification`, `test_every_emitted_event_validates…`, `test_checks_catch_tampering`, `test_validator_accepts_the_owner_synthetic_example` |
| Revision re-check scope correct (Annex B revision); an uncited-qualifier change re-opens the qualified clause (footnote-only revision); selective re-check equals a full rerun on the revised corpus | `test_annex_revision_rechecks_exactly_the_dependent_evidence`, `test_footnote_revision_reopens_the_qualified_clause_even_though_its_text_is_unchanged`, `test_selective_recheck_equals_a_full_rerun_on_the_revised_corpus` |
| Read-only API works and does not touch the served store; owner uploads keep original bytes; old G02 stores gain the new tables additively | `test_read_only_api_serves_the_synthetic_trace_without_touching_the_store`, `test_owner_ingestion_now_keeps_the_original_bytes`, `test_existing_g02_store_gains_the_new_tables_additively` |

## Exact test results (22 Nov 2026, Windows, Python 3.12.10, SQLite 3.49.1, jsonschema 4.26.0, pypdf 6.21.4 via `.venv`)

Command form: `python -c "import sys; sys.path.append(r'.venv/Lib/site-packages'); import pytest; sys.exit(pytest.main([...]))"`

* `tests/test_p0_t06_trace_slice.py`: **22 passed**, 0 skipped (the pypdf and owner-example tests ran).
* G01/G02 regression (`test_ptp_g01_workbench.py`, `test_ptp_g02_datasets.py`, `test_ptp_g02_openrouter_profiles.py`,
  `test_ptp_g02_pdf_ingest.py`, `test_ptp_g02_providers.py`): **69 passed**.
* Full suite (`pytest -rfEs`, whole `tests/`): **8 failed, 2534 passed, 6 skipped, 1 xfailed** in 153 s. The 8 failures
  are exactly the accepted pre-existing SACR supervisor budget tests
  (`test_sacr_r2_smoke_supervisor.py` and `test_sacr_r3_smoke_supervisor.py`,
  `test_budget_cannot_use_nonfinite_inflated_or_erased_cost[nan|inflated|erased|insufficient]`). Skips are unrelated
  (sklearn missing, DuckDB opt-in, native-supervisor guards). Other agents were editing other files in the same
  checkout during this run; the counts are those of the working tree at that time.

## How to run

```
python -m patent_to_pilot.workbench.trace_slice --out trace.json            # fresh temporary store
python -m patent_to_pilot.workbench.trace_slice --out trace.json --data-dir DIR
python -m patent_to_pilot.workbench.trace_slice --regenerate-fixtures       # rebuild generated fixture files
```
(with `src` on `PYTHONPATH`, or the package installed). In the Workbench: Welcome page → "Open the synthetic trace
(JSON)", or `GET /api/synthetic/trace-slice`. Both run in a temporary store; the owner's store is not modified.

## Limitations (stated, not hidden)

* **Synthetic only.** The packet, its wording, the synonym table and the line layout are authored. Success shows the
  data contract and engine plumbing work end to end; it is not evidence of retrieval effectiveness and must not be
  presented as a research result. Arbitrary-document support is not claimed.
* **No OCR, no real geometry.** The PDFs are generated by the slice's own minimal writer (Helvetica, one text layer).
  Regions are authored line bands (full column width × one line height), not glyph-tight boxes and not parser output;
  rotation is always 0 and CropBox = MediaBox. Real-document geometry, rotated pages and scanned pages are untested.
* **Structure extraction is a fixture grammar.** Footnote markers `[n]`, `Annex X` references and `Annex X.` headings are
  matched by regular expressions written for this packet. Relations from markers/labels are recorded as
  `explicit_source`; `parent_of` as `parser_inferred` with confidence 1.0 meaning "the rule fired", not verified truth.
* **The assessor is structural.** `supported` means every reference from the seed evidence is bound to acquired
  context; it is not a semantic judgement and never `contradicted`. It is a fallible runtime signal, not gold.
* **Lexical route only.** FTS5 `unicode61` without stemming (the vocabulary mismatch in the packet relies on that).
  Dense/hybrid routes, family aggregation and Thai tokenisation are not exercised.
* **Re-check is not a speed claim.** In a three-document packet both searches depend on the revised corpus, so both are
  replayed; the selective part is the dependency prediction for evidence, relations and the assessment, which is checked
  against the executed replay and against a full rerun. No speedup is claimed.
* **Action-effect causality** (fixed-pipeline action-removal replay) is not implemented; the trace says what search
  found a source, not that the action caused a better answer.
* The receipt's event timestamps and run IDs come from the actual run and change on every regeneration; the fixture
  hashes do not.
