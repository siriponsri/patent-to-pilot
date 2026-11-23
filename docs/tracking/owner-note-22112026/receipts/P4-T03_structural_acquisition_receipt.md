# P4-T03 receipt: useful expansion without an annex keyword

**Task:** P4-T03, "Useful expansion without an annex keyword", section 5 of the owner fix plan of 23 Nov 2026
(`PTP_Thai_Search_Structure_Requirements_Fix_Plan_20261123.md`). It builds on P4-T01a (Thai search, `bd37ea09`) and
P4-T01b (requirement Remove/Undo, `ff35de32`).
**Date:** 23 Nov 2026. **Cost:** USD 0. No paid call, model or download was used to build or test this. The tests use
only loopback connections.
**Status fields:**
- `product_readiness`: the structural acquisition step now runs inside the real assessment path, with tests (below).
- `method_evidence`: none. This is engineering acceptance only. Synthetic or authored fixtures prove the mechanism.
  They measure no retrieval effectiveness. The matched comparison of plan section 8 has **not** been run.
- `publication_readiness`: not affected.

## What the owner sees

- **Compare** works as before. When the first search leaves a visible gap, the engine takes at most one extra step
  inside that candidate's own documents before it records the result. Each result card then shows the step under
  "Extra step before the result was recorded". The card lists the gap, the action, the exact query, the scope, the new
  passages (marked *Same document* or *New document*), and a link to inspect each passage. A visible gap is one of:
  - no match;
  - a reference such as `ข้อ ๔(๒)` to another part;
  - a missing bounded field;
  - an item marked as missing.
- **Baseline only (no extra step, for comparison)** reruns Compare without the step. The card then says "baseline mode"
  and still lists the gaps it saw.
- **Inspect** now lists the document structure around the span. For each part it shows the section path, the
  extraction rule and the confidence.
- The sample and synthetic projects are unchanged. They never take the extra step.

## Design

**One interface, a new policy version.** `relation_search.py` keeps `ptp-relsel-first-unresolved/1.0.0` byte-identical.
Its pin `e4ea084c…5629c` is unchanged, and its functions now refuse policies of another family. The file adds
**`ptp-structural-acquisition/2.0.0`**, pinned at SHA-256 `124909017ac6a77daa253585399a202540f2dc01756fc41d28ae6bd4815fdd89`.
It also adds a pure selector (`select_structural_action`) and a pure operator (`structural_action_step`). These reuse
the existing `ActionBudget`, `EligibilityMask` and `RerankRequest`. Policy v2 declares the following:

| Part | Rule (summary; full text is in the policy and its fingerprint) |
|---|---|
| Gap signals (G1) | `no_hit`, `unresolved_reference` (an explicit reference or a parser-exposed binding whose target is not in the pool), `absent_bounded_field`, `user_declared_missing`. A free-text lexical match stays **Evidence found (not judged)**; it never opens or closes a gap. |
| Actions (S1) | `resolve_reference`, `recover_context`, `search_within_source`, `search_eligible_corpus` |
| Resolution (S2) | Qualified key `(source_id, version_id, section_path)`. A section reference resolves only inside its own version: the same annex container first, then the exact key, then the enclosing unit. An annex reference resolves inside its version, or else to exactly one other source of the same candidate that holds that annex unit. An external instrument resolves only when exactly one eligible source of the candidate is identified by title. Ambiguous and unidentified references stay visible as non-actionable states. |
| Order (S3) | Action priority, then pool rank, then span start, then target key. There are no scores, labels, randomness or model calls. |
| Budget (S4) | At most **one** action per obligation after the seed search; an optional run cap (`max_structural_actions`). |
| Query (Q1–Q3) | Resolve and recover actions use a structural lookup with no text search. The two search actions use the product Thai index with the OR of the original requirement's analyzer terms, plus the field label for a bounded requirement. They are scoped to the anchor source version or to the candidate's eligible versions, with a bounded substring fallback. |
| Rerank / assess (R1–R3) | Only the original requirement is used: the score is the number of distinct requirement terms in the unit. Seed units are read first, then new units. A free-text requirement cites a new unit only when the seed found nothing. |

**Real-import structure adapter** (`structure.py`, ruleset `ptp-owner-structure/1.0.0`). At import, inside the same
transaction as the version, the adapter stores `structure_nodes` and `structure_edges`. Each one records its rule and a
declared confidence. Older stores build the structure once, on demand. The adapter produces:

- **Numbered units** from line-start identifiers in Thai and English: `มาตรา ข้อ หมวด ส่วน/ส่วนที่ ภาคผนวก บัญชีท้าย`,
  and Section, Clause, Article, Chapter, Part, Annex, Appendix, Schedule, Attachment, Exhibit. Labels can use Thai or
  ASCII digits.
- **Nested numbering:** `(๒)`, `(ก)` and decimal `4.2`.
- **Paragraph ordinals** (`วรรค`).
- **Markdown headings, footnotes and pipe tables**, for Markdown only.
- **Reference edges** with their resolution state.

Identifier keys fold Thai digits, so `ข้อ ๕(๒)` and `ข้อ 5(2)` both become `ข้อ:5(2)`, while the original spelling and
the exact span are kept. A PDF text layer and plain text get numbering only. The adapter builds no footnote, table or
geometry binding from flat text.

**In the assessment path** (`acquisition.py`, called from `EvidenceCore._acquire_and_commit`): the order is seed search,
then gap detection, then at most one action, then merge and rerank, then read and assess against the original
requirement, then commit. Before the assessment is read, the step:
- persists the receipt (`acquisition_receipts`, plus the run action `structural_acquisition`);
- links the receipt to the committed (or rejected) assessment;
- records `acquisition_scope` dependencies, so a later source change re-runs the action instead of reusing the result.

The receipt follows the plan's sketch: requirement id and version, lifecycle revision, policy, action, reason,
anchors, scope, query, index generation, pool before, new unit/document ids, same-document ids, final ids and outcome.

**Scope** on every route: project, candidate, current source version and an optional declared date rule. The date rule
takes `effective` or `publication` dates; these are distinct, caller-supplied fields, because the store has no dates.
The mask is re-checked after merging. `_commit` now refuses a citation from another candidate's source
(`citation_candidate_scope`).

**Counters:** the Compare response now takes `paid_model_calls` and `remote_calls` from the run's own counters instead
of constants. It adds `run.provider_dispatch`, measured directly from the `provider_usage` rows written during the run.
Same-document context gain and new-document gain are counted separately, both in each receipt and in the run counters.

**Unchanged:**
- the legacy `passage_fts` index;
- the `trace_slice` helpers;
- the frozen P0-T06 and P2 routes;
- `RelationSearchSlice`;
- the G01 sample path, so the smoke test still passes 15/15.

The P4-T01 read-only V1 side-by-side (`Workflow.relation_action`) is still available, but only with
`legacy_side_by_side: true`, and it remains labelled ENGINEERING DEMO.

## Tests

`tests/test_structural_acquisition.py` has 15 tests. All use authored fixtures imported through the real owner path:
Markdown, plain text, and the P0-T06 synthetic PDFs through pypdf.

| Plan 5.4 requirement | Test |
|---|---|
| A newly acquired passage changes the committed assessment, its quote is stored exactly, and the trace survives reload | `test_acquired_passage_changes_the_committed_assessment_quote_is_exact_and_trace_survives_reload`: baseline `unknown`, structural `meets` via `ข้อ ๔(๒)`; the receipt is linked; a fresh `EvidenceCore` reads the same receipt SHA-256 |
| Real-import fixtures with and without explicit references | the above, plus `..._without_references_takes_no_structural_action` and the PDF test |
| Missing requirement without any reference | `..._searched_within_the_same_instrument_without_any_reference` (the fee example of section 5.1) |
| Source/version disambiguation, Thai digits | `test_source_and_version_disambiguation_with_thai_digits`; `test_structure_thai_digits_...` |
| Table/footnote binding where supported | structure tests (built for Markdown; not built for plain text or the PDF text layer) |
| Ambiguity visible; external instrument unresolved unless identified | `test_structure_ambiguity_...`; `test_external_instrument_stays_unresolved_until_...` |
| One-action bound; unchanged original requirements | pure operator test; integration test (budget 1/1, mission and requirement hashes unchanged) |
| Scope isolation | `test_scope_isolation_...`: another candidate's document is never in the pool, and the commit refuses it |
| Annex in another source and its revision | `test_pdf_text_layer_import_...` (Annex B → `annex-b@v1`, then re-acquired at `@v2`) |
| Archive/restore and stale-commit rules with acquisition in the path | `test_archive_restore_and_stale_commit_rules_hold_...` |
| Counters propagated; dispatch verified directly | `test_provider_dispatch_is_measured_...`: lexical profile with provider dispatch patched to fail; local embedding double in hybrid mode |
| The UI reads the persisted trace | `test_compare_over_http_returns_the_persisted_trace_...` |

`tests/test_p4_t01_workflow.py` changed in one place: the V1 side-by-side assertions now request
`legacy_side_by_side: true`, and the test also checks that the default Compare returns the persisted trace.

**Gate (23 Nov 2026).** The full suite was run with pypdf and PyThaiNLP available
(`python -c "...sys.path.append(r'.venv/Lib/site-packages')...pytest.main(['-q','-p','no:cacheprovider'])"`):
- 2655 passed, 6 skipped and 1 xfailed;
- 8 failed, which are only the 8 known SACR r2/r3 supervisor budget tests
  (`test_budget_cannot_use_nonfinite_inflated_or_erased_cost[nan|inflated|erased|insufficient]` in r2 and r3);
- `python scripts/ptp_run.py --smoke`: 15/15 PASS, and the G01 sample is unchanged.

## Owner walkthrough

1. Start the Workbench (`Start-PTP.cmd`). Create a project with one candidate.
2. Add a Thai notice in which one clause points to another clause, for example
   `ข้อ ๒ … ต้องเป็นไปตามข้อ ๔(๒)`, where `ข้อ ๔ (๒)` holds `Supported temperature range: 5 to 60 °C.`
3. Add a bounded requirement for the temperature range, for example 10–50 °C, with search words that appear only in
   `ข้อ ๒`.
4. Tick **Baseline only** and press **Run compare**: the result is *Unknown*.
5. Untick it and run again: the result is *Meets*. The cited passage is `ข้อ ๔`. The card says one *resolve reference*
   step brought in one *Same document* passage, and **Inspect source** opens the exact quote.
6. Close and restart the Workbench. The same card is still there: it is read from the stored run.

## Limitations

- **No effectiveness claim.** No judged data was used. The plan section 8 arms (raw FTS5, Thai FTS5, plus fallback, a
  strong control, plus one action) still need a frozen protocol and matched budgets.
- **Text actions stay lexical.** For a free-text requirement in the default `terms` mode, the seed already searches
  every word in the candidate's scope. So the two search actions mainly help `phrase` requirements, deeper bounded-field
  reads and declared-missing items. Synonyms and semantics are out of scope.
- **Parent headings.** `recover_context` uses numbered parents, footnotes and table headers. Plain Markdown headings
  are stored but not used as context targets.
- **Unsupported reference forms.** Roman-numeral labels and forms such as `วรรคสองของข้อ ๓` are not parsed; a
  standalone `วรรค` resolves against the enclosing unit.
- **External instruments** are identified only by source title, within the same candidate. A shared law must be
  imported under each candidate that relies on it.
- **Version identity and dates.** Documents are identified by `source_id`; families are not defined for owner
  documents. Date eligibility needs caller-supplied dates, and the seed route itself is not date-filtered.
- **Re-checks.** Any result that rests on an action is re-acquired after a change in its scope; it is not reused. This
  is conservative and costs extra local searches.
- **Recorded steps.** Structural steps are counted in their own run counter, not in `max_acquisition_actions`. The
  passages they read do count in `max_source_reads`.
