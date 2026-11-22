# P4-T01 receipt: Search, Compare and Inspect in the existing Workbench

**Task:** P4-T01, "Extend the existing Search, Compare and Inspect workflow" (owner note 22 Nov 2026).
**Date:** 23 Nov 2026. **Cost:** USD 0. No network, model or paid call was used to build or test this.
**Status fields:** `product_readiness`: the local workflow works and has tests (see below). `method_evidence`: none.
The relation-search panel is an engineering demonstration and does not measure retrieval quality.
`publication_readiness`: not affected.

## What was built

The work reuses the existing Workbench: the same `EvidenceCore`, the same SQLite store, the same loopback server and
the same bundled UI. No table was added and no G01 or G02 table changed.

1. **Search** (new Search tab). A free-text query runs over the current-scope passage index of the open project.
   - **Terms** (the default) and **Exact phrase** are SQLite FTS5 BM25 queries. The tokenizer is `unicode61`, the
     same index the run engine uses.
   - **Literal** is a separate, labelled route for Thai text inside longer unsegmented runs. It is a case-sensitive
     substring scan of the same current passages. It does not use FTS5 and does not rank results.
   - Each result carries:
     - the exact stored passage quote;
     - its code-point offsets in the canonical text of that source version;
     - the offsets of the highlighted matches;
     - a snippet window with its own offsets;
     - the BM25 score;
     - the FTS5 expression that was actually issued.
   - The response says when a Thai query meets the tokenizer's limit, and when a project has nothing searchable yet.
2. **Explicit, arbitrary requirements** (Compare tab, requirement form).
   - Users type requirements in their own words. Each one is validated (`core.normalize_requirement`) and stored in
     the project's mission.
   - A new requirement opens one obligation per candidate. An edited requirement reopens its obligations.
   - Every save is recorded as a `requirement_change` change event. History is kept.
   - **Free-text requirements** (`kind: text`) are searched with `terms` by default, or `phrase`. The engine cites the
     best-ranked passage per candidate with outcome **"Evidence found (not judged)"**. It never decides whether the
     passage satisfies the requirement (rule 12).
   - **Bounded-field requirements** (the G01 grammar) are still accepted through the API and still use the G01
     parser and predicates.
   - The sample project and the synthetic project are **fixed** (HTTP 409 `project_is_fixed`), so G01 sample results
     stay reproducible.
   - `create_project` accepts both kinds of requirement.
3. **Compare** (Compare tab).
   - The project's requirement set runs through the **existing assessment path** (`EvidenceCore.run_comparison`,
     PLAN → ACQUIRE → COMMIT). It shows per-requirement, per-candidate results with the cited quote and an Inspect
     button.
   - Each requirement also shows a **side-by-side** of:
     - **Baseline:** the seed search, i.e. the OR of the requirement's own terms, top 5 over the project's current
       passages;
     - **With one relation search:** exactly one bounded action under the pinned default policy
       `ptp-relsel-first-unresolved/1.0.0` (`POLICY_V1`, fingerprint checked), with a budget of 2 searches (seed plus
       one).
   - The panel shows the issued query, its typed terms (`source_copy` or `original_requirement`), the before, after
     and new candidates (new ones are badged), the runtime coverage status before and after (labelled "not gold"),
     and the budget.
   - It is labelled **"ENGINEERING DEMO … not a research result"**.
   - Two forms of the same operator are used:
     - **Owner projects:** a project adapter of `relation_search.relation_search_step` over the project's FTS5 index.
       Its coverage signal is a deterministic explicit cross-reference detector (`Annex|Appendix|Schedule|Exhibit|
       Attachment <label>` or `ภาคผนวก <label>`). A reference counts as bound only when a pool passage has a heading
       line for it. No generated hypotheses are used. This form is read-only and is not written to the run history.
     - **The synthetic P2-T03 packet:** `RelationSearchSlice` itself, i.e. the Workbench form with the default policy.
       It is recorded as a `relation_search` run. The welcome page has an opt-in button, **Load synthetic
       relation-search example**, that creates this labelled project in the current store.
4. **Inspect** (drawer, opened from Search, Compare or any citation).
   - Opens any span `[start, end)` of a stored source version. It re-verifies the stored bytes against their hash
     and shows the exact text with the span highlighted. It also lists the overlapping passages.
   - It reports the original artifact: media type, hash, size, integrity check, and an **Open the original file** link
     (served inline with `Content-Security-Policy: sandbox`).
   - It reports the page mapping honestly:
     - `regions`: P0-T06/P2-T03 `doc_nodes`, i.e. page plus normalized bbox. These are authored line bands.
     - `page_only`: PDFs ingested via `pdf_text_layer_v1`, using the `[page N]` markers. No region geometry exists.
     - `none`: plain text or Markdown, or no layout recorded. A plain reason is given.
   - When no separate original file was kept (for example, the G01 sample imported from fixture files), it says
     `not_kept` and does not invent one.

## Endpoints (all loopback, JSON unless noted)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/projects/{pid}/search` | `{query, mode: terms\|phrase\|literal, limit 1-50, candidate_id?}` → results with offsets |
| GET | `/api/projects/{pid}/requirements` | requirement list with kind, match mode, issued FTS5 expression, `editable` |
| POST | `/api/projects/{pid}/requirements` | create/update `{requirement_id?, label, query?, match?}` (or a bounded `field` + `predicate`) |
| POST | `/api/projects/{pid}/compare` | `{run?: true, requirement_ids?}` → assessment run + per-requirement side-by-side |
| GET | `/api/projects/{pid}/sources/{sid}/versions/{vid}/spans/{start}/{end}` | Inspect a span |
| GET | `/api/projects/{pid}/sources/{sid}/versions/{vid}/original` | stored original bytes (PDF or text/plain), 404 if not kept |
| POST | `/api/synthetic/relation-search` | opt-in: create (once) and run the labelled synthetic P2-T03 project |

## Files

New:
- `src/patent_to_pilot/workbench/workflow.py`: Search, requirements, Compare, Inspect and the relation-search adapter.
- `tests/test_p4_t01_workflow.py`: 9 API-level tests through the live loopback server, under `loopback_only()`.

Changed:
- `src/patent_to_pilot/workbench/core.py`:
  - `fts_terms`, `requirement_match`, `requirement_kind` and `normalize_requirement`;
  - the `evidence_found` outcome;
  - `_search` and `_acquire_and_commit` now use the requirement's match expression and handle free-text requirements.
  - G01 requirements have no `match` key, so they still search with the identical phrase expression.
- `src/patent_to_pilot/workbench/server.py`: seven routes and a non-JSON `Raw` response for original files.
- `src/patent_to_pilot/workbench/static/index.html`, `app.js`, `app.css`:
  - Search and Compare tabs;
  - requirement form;
  - side-by-side panel;
  - Inspect drawer;
  - the synthetic-example button.

## How to try it

1. Run `Start-PTP.cmd` (or `python scripts/ptp_run.py --serve`) and open the Workbench.
2. **Search:** open the sample project, then the **Search** tab. Type `temperature range` (Terms), or `กักเก็บ` with
   **Literal text (for Thai)**. Select **Inspect source** on a result.
3. **Arbitrary requirements:** on the welcome page, **Create project**. Add a `.md`, `.txt` or `.pdf` file on Evidence.
   Open **Compare**, type a requirement, select **Save requirement**, then **Run compare**.
4. **Relation-search demo:** on the welcome page, **Load synthetic relation-search example**. The Compare tab shows the
   baseline (2 candidates) beside the action (issued `"annex b" OR "installed" OR "seaside" OR "sites" OR "coastal"`,
   3 new candidates). **Inspect source** on a new candidate shows page 1, its region box and the original PDF.

## Verification (23 Nov 2026, local Windows, Python 3.12.10, pypdf from `.venv`)

- `tests/test_p4_t01_workflow.py`: **9 passed**. The tests check:
  - search offsets, snippets and matches resolve in the stored text;
  - phrase/terms/literal modes, the candidate filter, the Thai note and validation errors;
  - requirement create, update, unchanged, Thai, bounded-field and eight rejection codes;
  - the sample stays fixed and still produces 6 G01 assessments with the phrase expression;
  - Compare commits an `evidence_found` assessment with a literal citation;
  - the side-by-side uses `POLICY_V1`, 2 searches, the exact issued query and typed terms, a baseline equal to the
    FTS5 seed result, the new candidate `letter@v1#annex-b`, `after = before + new`, and `unresolved → supported`;
  - requirements without references issue no extra search;
  - the synthetic example uses `RelationSearchSlice` and is recorded as a run, and its PDF original is served with a
    matching hash;
  - Inspect covers spans, Thai spans, `none` and `not_kept` honesty, 404/422 errors and the PDF `page_only` mapping;
  - the UI is served.
- Workbench test files (G01, G02 ×4, P0-T06, P2-T03, P4-T01): **119 passed**.
- Full suite: see the result line below.
- `python scripts/ptp_run.py --smoke`: **15/15 PASS**. The smoke was not modified.
- Browser check (preview of a temporary QA store):
  - a free-text requirement was saved and assessed;
  - Compare rendered the panel, which said plainly that no extra search was issued;
  - a Thai literal search found `ปั๊ม` inside an unsegmented run, and Inspect reported "no page or region mapping";
  - the synthetic example rendered the baseline (2) beside the action (5, 3 new) with "New" badges;
  - no console errors.

Full suite result (`.venv` site-packages, 23 Nov 2026): **2599 passed, 10 failed, 6 skipped, 1 xfailed**.
- 8 of the failures are the known SACR r2/r3 supervisor budget tests.
- The other 2 are in `tests/test_g03_a3_caller_budget.py`:
  - `test_tracked_a3r1_config_loads_800_tokens_and_stays_disabled`;
  - `test_typhoon_without_a_verified_price_is_never_dispatched`.
- These 2 come from the concurrent P1-T03 freeze commit `8c4c23f1`, which enabled the tracked A3r1 caller config
  (`execution_enabled` is now true). They do not touch the Workbench and are not caused by this task. They are
  reported for the P1 owner of that config.

## Limitations (stated, not hidden)

- **No semantic judgement for free-text requirements.** "Evidence found" means "best lexical match". A person must
  read the quote. Literal source match is source integrity, not support.
- **Thai lexical search:** `unicode61` does not segment Thai. FTS5 modes match only whole space-delimited runs, and
  the Literal route is an unranked substring scan. A declared Thai segmentation is P3 work.
- **The owner-project relation action** only acts on explicit cross-references with a matching heading line. On the
  G01 sample and on most documents it truthfully reports "no unresolved relation; no extra search". It has no
  hypothesis generator. It is read-only, so it is not in the run history; the synthetic form is recorded. Its
  candidate pool is project-wide (all candidates), while the assessment path searches per candidate.
- **Page/region mapping** exists only for the synthetic packet (authored line bands, not glyph boxes) and as page
  numbers for text-layer PDFs. No other layout extraction or OCR exists.
- **Requirements cannot be deleted** (only added or edited), so committed history stays consistent. The UI edits
  free-text requirements; bounded-field requirements are API-only.
- **Compare re-runs** the full comparison each time (the existing run engine's behaviour). For the synthetic project,
  each Compare re-runs the relation search and records a new run.
- **No usability observation** was done (P4-T05). Nothing here claims a UX advantage over another product.
