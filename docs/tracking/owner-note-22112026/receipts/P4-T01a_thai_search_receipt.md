# P4-T01a receipt: normal Thai search works by default

**Task:** P4-T01a, goal 1 of the owner plan `PTP_Thai_Search_Structure_Requirements_Fix_Plan_20261123.md` (sections 1-4,
8 and 10), written against commit `7cf8339a`. It is an additive subtask of P4. It does not renumber any phase.
**Date:** 23 Nov 2026. **Cost:** USD 0. No network, model, download or paid call was used. PyThaiNLP 5.4.0 was already
installed in the project venv with owner approval.

**Status fields:**
- `product_readiness`: a user can type Thai normally in the default Search box and get the right canonical quote. The
  focused tests and the repository gate pass (see Tests).
- `method_evidence`: none. All checks use authored engineering fixtures. They are not benchmark results and claim no
  retrieval gain. The plan's section 8 comparison (raw FTS5 vs segmented vs fallback vs strong control) has not run.
- `publication_readiness`: not affected.

**Out of scope here:** requirement Remove/Undo (a parallel worktree does it) and structural acquisition (plan section 5).
`Workflow.relation_action`, the explicit-reference detector, `trace_slice._terms` / `_or_match` and the frozen P0-T06 /
P2 routes are unchanged and still read the legacy index.

## What changed

1. **Versioned Thai analyzer:** `src/patent_to_pilot/workbench/thai_analyzer.py` (new).
   - Segmentation uses PyThaiNLP `newmm-safe` through the top-level `word_tokenize`, with `keep_whitespace=True` and
     `join_broken_num=False`.
   - The dictionary is built once per process and never mutated afterwards. It is the immutable base list
     `thai_words()` (a frozenset) plus 8 declared domain terms.
   - Alignment is checked exactly: the tokens must join back to the input. A text that fails the check is never
     indexed with misaligned tokens. It uses the declared fallback (runs of indexable characters), and that use is
     counted per passage (`segmentation = 'fallback_runs'`).
   - Offsets are half-open Python code points into the canonical text. They are not UTF-16 offsets.
   - Index terms split each word into the character runs that SQLite keeps under
     `unicode61 categories 'L* N* Co M*' remove_diacritics 0`. Each Python term therefore equals one FTS5 token.
   - The normalization `fold-v1` turns Thai digits into ASCII digits and lower-cases each character. It keeps code
     points one-to-one, so offsets do not move.
   - No Thai word is dropped. `ไม่`, `ห้าม`, `ต้อง` and `เว้นแต่` stay searchable. Only the existing English stopword
     list is dropped from the any-word expression.
   - Section identifiers (`มาตรา`, `ข้อ`, `วรรค`, `หมวด`, `ส่วน`, `ภาคผนวก`, `บัญชีท้าย`, and section / clause /
     article / annex ...) get a lookup key with normalized digits, such as `ข้อ ๕(๒)` and `ข้อ 5(2)` → `ข้อ:5(2)`. The
     original spelling and its span are kept. `ข้อ 5` matches `ข้อ ๕(๒)` but never `ข้อ 52`.
2. **New derived FTS5 table:** `passage_fts_th_v1`, in `src/patent_to_pilot/workbench/product_lexical.py` (new).
   - Tokenizer: `unicode61 categories 'L* N* Co M*' remove_diacritics 0`. Its `body` column holds the segmented,
     folded derivative of the passage.
   - The canonical quote stays in `passages` / `source_versions`. Quotes, citations and highlight offsets always come
     from it.
   - `lexical_index_state` records, per project, the active index, generation, analyzer identity (name, version,
     PyThaiNLP version, dictionary hash, normalization), corpus revision, passage count and alignment fallbacks.
   - `lexical_index_generations` keeps one history row per generation, of kind `full_rebuild` or `incremental`.
   - Indexing runs inside `EvidenceCore._make_current`'s own transaction: a version never becomes current without its
     derivative rows. The path is an incremental replace of the source, checked against the current scope, or else a
     full project rebuild.
   - A full rebuild is a single transaction, and the active pointer switches only when it commits.
   - A derivative that is missing, stale or built by another analyzer identity is rebuilt **on demand** before it is
     searched.
   - Existing stores migrate additively: only `CREATE ... IF NOT EXISTS` of the three new tables. No existing table
     changed and `schema_version` is unchanged.
3. **Workbench Search default = `auto`:** `workflow.py`, `static/index.html`, `static/app.js`.
   - There is one box with automatic Thai handling. `terms`, `phrase` and `literal` stay as labelled **Advanced**
     options on the legacy index (the historical raw-FTS5 control).
   - Declared ranking rule: route order identifier > all words > any word > substring. Within a route, results sort by
     BM25 ascending, or by source order for substring. A passage keeps its best route.
   - **Bounded fallback:** a substring check of the whole query, using `fold-v1`, over at most 20,000 current passages.
     It runs when one of these holds:
     - `short_query`: fewer than 3 non-space characters;
     - `no_index_terms`;
     - `no_word_hits`;
     - `thai_partial_coverage`: a Thai query with fewer word-index results than the limit, because a typed word can sit
       inside a longer dictionary word, such as `ธุรกิจ` inside `ผู้ประกอบธุรกิจ`;
     - `analyzer_unavailable`.

     The reasons, the scan count, the cap and the count found are returned in `lexical_trace.fallback` and shown in the
     UI.
   - Every MATCH term holds only letters, numbers, marks or private-use characters, and every term is double-quoted.
     User quotes and operators (`AND`, `OR`, `NOT`, `NEAR`, `*`, `^`, `:`) are therefore inert, and all SQL values
     are bound.
4. **Owner requirement matching:** `core.py`.
   - `EvidenceCore._search` now calls `_req_lexical`. For `owner_files` projects with the analyzer available, a
     requirement's `terms` form maps to `auto` and its `phrase` form to `phrase`, on `passage_fts_th_v1`.
   - Each hit records `lexical: {index, analyzer, route}`. The search action records `detail.lexical`: the index,
     generation, corpus revision, mode, query terms, issued expressions and fallback.
   - The G01 sample, the synthetic projects and any explicit custom expression keep the legacy `_lexical`. Old run
     records have no `lexical` key, which means they used the legacy `passage_fts`.
5. **Highlighting:** the marks come from the same analyzer terms as the index, the identifier spans with the same key,
   and literal folded occurrences of the query. Offsets are relative to the canonical quote.
6. **Packaging:** `pyproject.toml` gains the optional extra `thai = ["pythainlp>=5.4,<6"]`. Without PyThaiNLP, every
   product route falls back to the legacy index plus the bounded substring check, and it says so in the response notes
   and in `capabilities().lexical.product_thai`.

Note on item 4: because requirement matching uses `auto`, a recognized section identifier in the requirement text
is also searched, on the identifier route first.

Edits to shared hot spots, kept small for the later merge:
- `core.py`: one import; the `product_lexical` attribute; one call at the end of `_make_current`; `_req_lexical` plus
  three call sites inside `_search`; one `detail["lexical"]` line in `_acquire_and_commit`; the capability key; the
  code-hash file list.
- `workflow.py`: `SEARCH_MODES`, the default mode, and a two-line `auto` dispatch.
- `store.py` and `server.py` are untouched.

## Versions and hashes (measured)

| Item | Value |
|---|---|
| Analyzer identity | `ptp-thai-lexical/1.0.0;newmm-safe;pythainlp=5.4.0;dict=37875115d95d;fold-v1` |
| Combined dictionary SHA-256 (62,108 words) | `37875115d95dc54ff62c1fa059b071667d7312fe9a6bd4892af4957108613e18` |
| Base `thai_words()` SHA-256 (62,106 words) | `0df520c0672c4069af3e1e06a6621eae4e4abcc5a85c2ba712d3a368618b9336` |
| Domain terms SHA-256 (8 terms; `อนุสิทธิบัตร` and `บัญชีท้าย` are new to the base list) | `3a63b4ea501d453cf8cd62240c473acb0605b6f36be0acc15f4f13dd7513d8f6` |
| Index / profile | `passage_fts_th_v1` / `product-thai-lexical-v1` |
| Runtime used for measurement | Python 3.12.10, SQLite 3.49.1, PyThaiNLP 5.4.0 (project venv site-packages) |

## Measured local latency and index size

The runs were on this Windows PC, in a fresh temporary store. Inputs were the G01 sample (4 sources, 6 passages) and the
authored Thai fixture of `tests/test_thai_search.py` (2 sources, 6 passages). Latency is the median of 30 calls to
`Workflow.search`, which includes analysis, FTS5, canonical-quote verification and highlighting. These are
small-fixture engineering numbers, not throughput claims.

| Measurement | Value |
|---|---|
| Analyzer first build (import + trie), once per process | 0.56 s |
| Full derivative rebuild, sample (6 passages) / Thai fixture (6 passages) | 7.0 ms / 8.6 ms |
| Ingest of the Thai fixture, including the derivative inside the transaction | 21.7 ms |
| `auto` search, median (max) across 8 queries: Thai, English, mixed, identifier, fallback | 7.0-9.1 ms (max 13.8 ms) |
| Legacy `terms` search on the same queries, median | 4.0-5.2 ms |
| Index size, 12 passages: FTS5 data blocks, legacy / Thai derivative | 2,055 B / 5,462 B |
| Body text stored: legacy (raw quote) / derivative (segmented) | 851 B / 867 B |

## Tests

- New file `tests/test_thai_search.py`: **27 passed** with PyThaiNLP. It covers:
  - analyzer alignment, offsets, negation words, identity and identifier keys;
  - a misaligned tokenizer that is never indexed;
  - mark categories against default `unicode61`, checked with fts5vocab;
  - an unspaced Thai query with the exact canonical quote;
  - combining marks (Thai, and Latin `é`) and mixed Thai/English;
  - Thai vs Arabic digits in section ids, including the `52` boundary;
  - 13 quote/operator/injection inputs;
  - short-input and hidden-word fallback with recorded reasons and a bounded scan;
  - repeated words and supplementary-plane characters (`😀𠀀`) in spans, checked through Inspect;
  - project / candidate / version isolation and the generation history;
  - on-demand rebuild, restart, analyzer-identity change and migration of a pre-P4-T01a store;
  - legacy `passage_fts` rows and DDL unchanged, and the G01 sample run still on the legacy route;
  - owner Thai requirement matched through the analyzer, with the trace recorded;
  - degradation without PyThaiNLP;
  - the owner acceptance flow over loopback HTTP (import → type unspaced Thai → open the result → see the quote).
- Under the system Python, which has no PyThaiNLP: 26 skipped, 1 passed (the degradation test).
- Existing test updated: `tests/test_p4_t01_workflow.py`. Two legacy assertions now pass `"mode": "terms"` explicitly,
  because the default mode is now `auto`.
- Full gate, with venv site-packages, so pypdf and PyThaiNLP are active: **2623 passed, 8 failed, 8 skipped,
  1 xfailed**. The 8 failures are exactly the known SACR r2/r3 supervisor budget tests
  (`test_budget_cannot_use_nonfinite_inflated_or_erased_cost[nan|inflated|erased|insufficient]` in
  `test_sacr_r2_smoke_supervisor.py` and `test_sacr_r3_smoke_supervisor.py`). No other failure occurred.
  - This gate ran before one later edit: the code-point fix to `app.js` `marked()`, plus receipt wording.
  - `tests/test_thai_search.py`, `tests/test_p4_t01_workflow.py` and `tests/test_ptp_g01_workbench.py` were rerun after
    that edit: 52 passed.
- `python -m pytest` with the system Python, which has no PyThaiNLP or pypdf, so every product route takes the
  legacy fallback: **2587 passed, 8 failed, 36 skipped, 1 xfailed**. The run was after all edits, and the 8 failures
  are the same known SACR r2/r3 supervisor budget tests.
- `python scripts/ptp_run.py --smoke`: 15/15 PASS with the system Python (no PyThaiNLP) and 15/15 PASS with the venv
  Python (PyThaiNLP active). The G01 sample results are unchanged: its assessments still use `passage_fts`.

## Limitations (honest)

- PyThaiNLP's base dictionary contains compounds such as `ผู้ประกอบธุรกิจ`, `ไม่ต้อง` and `ได้รับอนุญาต`. A word typed
  alone that sits inside such a compound is not in the word index. Only the bounded substring check finds it, and only
  when the whole typed query occurs literally. No sub-word index is built.
- `thai_partial_coverage` fires for most Thai queries on small corpora, because results are usually fewer than the
  limit. The fallback is bounded (20,000 passages, one linear scan) and labelled, but it is not a trigram index.
- Requirement matching uses the derivative only for `owner_files` projects with PyThaiNLP installed. Without it, owner
  projects silently keep the legacy route (recorded: hits carry no `lexical` key).
- Switching an existing owner project to the derivative does not reopen its obligations. The next comparison run
  re-searches every obligation with the new route, and the action detail records it.
- The structural relation action (section 5) still uses the legacy index and `trace_slice` helpers by design.
- Python's `unicodedata` and SQLite's `unicode61` category tables may differ for rare code points across versions. This
  affects highlighting only, never citations.
- Highlight offsets are Python code points, not UTF-16 units. The bundled UI's `marked()` now slices an array of code
  points; before this change it sliced UTF-16 strings, which misplaced marks after a supplementary-plane character. The
  tests verify the offsets on the server side only; the UI was not exercised in a browser.
- HANDOFF.md, INDEX-PLAN.md and the tracker registry were not updated in this worktree, to avoid merge conflicts with
  the parallel lifecycle branch. The integrating agent should record P4-T01a through `scripts/tracking/ptp_tracker.py`.
