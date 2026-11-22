# G02 dataset contracts (registry, inspection, adapters)

Program PTP-2026-11-21, goal G02, 22 Nov 2026. Stdlib only. **No dataset rows were fetched, downloaded or opened;
no gated terms were accepted; no setup script was run; dr-train was not touched.**

Code: `src/patent_to_pilot/workbench/datasets/` (`registry.json`, `registry.py`, `policy.py`, `inspect.py`,
`loaders.py`, `adapters.py`, `evaluator.py`). Tests: `tests/test_ptp_g02_datasets.py`. Synthetic fixtures:
`tests/fixtures/ptp_g02/datasets/` (fictional rows, CC0, see `FIXTURES.json`).

## Registered datasets

| dataset_id | Revision | License | Role | Access | Exposure |
|---|---|---|---|---|---|
| `ptp_g01_fixture` | (bundled) | CC0-1.0 | G01 runtime/engineering checks | bundled | PTP-authored synthetic |
| `datalyes/DAPFAM_patent` | `780f4011…afea2d` | CC-BY-NC-SA-4.0 (no product bundle) | principal patent benchmark | public | **previously exposed**: B53 Stage 1 evaluated ALL 1,247 / OUT 905 / IN 1,217 |
| `VISAI-AI/thai-gazette-evidence-retrieval` | `87e695ee…1ec374` | CC-BY-4.0 | public frozen transfer | public | not exposed (metadata only); `test` is evaluation-only |
| `VISAI-AI/nitibench-plus` | `41286bcb…7f7b7` | CC-BY-4.0 | optional temporal companion | **auto-gated, acceptance NOT performed** | not exposed |

Every dataset has `development_use: false` except the G01 fixture. Each fact carries a `sources` entry (owner note section,
repo file or URL). Counts come only from the owner note, the dataset cards, or datasets-server `/info`.

`availability(dataset_id, search_roots)` reports `not_downloaded`, `gated_acceptance_required` or `local_copy_found`
from directory/marker-file existence plus an optional `PTP_DATASET_MANIFEST.json` sidecar or the HF cache snapshot name
(revision). It never opens a row. NitiBench+ is always `gated_acceptance_required` until the registry records an
acceptance (`acceptance_performed` + `acceptance_record`), even if files exist locally.

## What each adapter maps (runtime)

- **DAPFAM** `corpus` row → `SourceRecord(source_id=relevant_id, version_id=revision, title=title_en, text=view)`;
  `queries` row → `RequestRecord(request_id=query_id, as_of=None)`. Views: TA (title, abstract), TAC (+claims, default),
  FULL (+description), joined like B53 `tac()` (non-empty fields, newline). Components are not altered.
- **Gazette** `corpus` row → `SourceRecord(source_id=_id, text=text verbatim, title="" kept as-is, language th)`;
  `queries` row → `RequestRecord(request_id=_id, text)`. `Span` slices half-open **code-point** offsets and can report
  the UTF-8 byte range separately.
- **NitiBench+** case → one `RequestRecord` per sub-question (`as_of` = decision date verbatim, `context` = fact pattern).
  Without a native sub-question id the request id is a declared positional locator (`<case>/sub_questions[i]`), marked
  `request_id_kind=positional_locator`; a missing case id raises. Gold sections become versioned `SourceRecord`s
  (`version_id=version_uri`, `source_id=current_uri` or `None`, `valid_from`/`valid_to` verbatim) **only** under the named
  oracle setting `gold_cited_in_force_public_validation`.

Rows are projected onto the registry `runtime_fields` allowlist before mapping. Asking for an evaluator, withheld or
dropped field of any config raises `EvaluatorFieldRequested`. Text is never normalized (tested with Thai SARA AM, a
non-canonical tone-mark/vowel order, double spaces and trailing newline).

## Evaluator-only (held by `evaluator.py`, never by runtime adapters)

- DAPFAM: the whole `relations` config (`query_id`, `relevant_id`, `relevance_score`, `domain_rel`).
- Gazette: the whole `default`/`test` config (`query-id`, `corpus-id`, `score`, `evidence_start_char`,
  `evidence_end_char`, `evidence_text`, `passage_text`); query `author_model`, `judge_model`.
  `question_type` is **withheld** by default; release requires an explicit, predeclared `release_withheld`.
- NitiBench+: `source_id` (decision number), `title`, `drift_band`, `verdict`, `reasoning`, `citations` and their
  `law`/`section`/`version_uri`/`valid_from`/`valid_to`/`current_uri`; `question_type` withheld; `canary` dropped;
  `gold_sections` evaluator-only except the named oracle setting. Missing citation ids stay `None` (`resolved=False`).

Inspection (`inspect_schema`) returns column names, inferred types and a row count, never values. Paths whose name (or
components below `root`) contain `test`, `qrel`, `sealed`, `private`, `secret`, `credential` or `.env` are refused before
opening; `gold`/`relations`/`label`/`answer`/`evidence` paths, or `role="evaluator"`, are reduced to column names only.

## URLs fetched (metadata only)

1. `https://datasets-server.huggingface.co/info?dataset=datalyes/DAPFAM_patent`
2. `https://datasets-server.huggingface.co/info?dataset=VISAI-AI/thai-gazette-evidence-retrieval`
3. `https://datasets-server.huggingface.co/info?dataset=VISAI-AI/nitibench-plus` (HTTP 401, gated; nothing returned)
4. `https://huggingface.co/datasets/datalyes/DAPFAM_patent/resolve/780f4011d60297fc6e97a4119b0c516d13afea2d/README.md`
5. `https://huggingface.co/datasets/VISAI-AI/thai-gazette-evidence-retrieval/resolve/87e695ee4951ff34932804431433ac55991ec374/README.md`
6. `https://huggingface.co/datasets/VISAI-AI/nitibench-plus/resolve/41286bcb1eeba6721c03d581d4ca3095a1b7f7b7/README.md`

No `/rows`, `/first-rows`, `/search` or parquet URL was requested; no card example row was copied.

## Field names: verified vs assumed

- **DAPFAM: all verified** (datasets-server `/info`; also used by `scripts/healthtech/b53_first_stage.py`). The source
  spells `earliest_claim_jusrisdiction`. TA/TAC are PTP view definitions, not card definitions.
- **Gazette: all verified** (`/info` and pinned card).
- **NitiBench+: partly assumed.** Verified on the card: `canary`, `source_id`, `fact_pattern`, `question_type`, `law`,
  `version_uri`, `valid_from`, `valid_to`, `current_uri`. Assumed: `id`, `court`, `decision_date`, `domain`, `drift_band`,
  `title`, `sub_questions`, `question`, `verdict`, `reasoning`, `citations`, `section`, gold-section `text`. Adapters read
  these via the registry `field_map`, so they can be corrected after authorized access without code changes. Date formats
  are unspecified and kept as strings.

## Left for later goals

- Owner acceptance of NitiBench+ terms (owner account flow) and recording it in the registry; then verify assumed names.
- Per-item owner approval before any dataset download; write `PTP_DATASET_MANIFEST.json` (revision, file hashes) at download.
- Parquet reading (pyarrow is not installed); current loaders read JSONL only.
- Resolve the owner registry's `existing_non_dapfam_dev` entry (not registered here).
- Wire the adapters into the engine ingestion path and the Workbench UI (another G02 part).
- Evaluators (native metrics, span scorer, ALL/IN/OUT denominators) are not implemented; only label readers exist.
