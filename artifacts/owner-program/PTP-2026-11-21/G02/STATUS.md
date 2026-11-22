# G02 acceptance status (PTP-2026-11-21 / G02)

**Overall: COMPLETE for the G02 contract, at USD 0.** Paid API routes are implemented and policy-tested. They have not
been called against a real paid service, because no owner spending envelope exists.

G02 acceptance (`02_GOALS_AND_PHASES.md` §G02):

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Lexical-only operation remains usable | PASS | Lexical is the default mode. The G01 suite (16 tests) and smoke (15/15) are unchanged. `test_lexical_mode_is_the_default_and_unchanged`. A failing provider falls back to lexical with the reason recorded (`test_provider_failure_falls_back_to_lexical_with_a_recorded_reason`). |
| 2 | A configured local or API model can be used when access and budget already exist | PASS (local) / PASS-by-contract (API) | **Real local model:** Qwen3-Embedding-0.6B through the `openai_compatible` adapter (dr-train CPU, SSH tunnel to loopback). Connection check ready, index built, hybrid run, revision under hybrid: [REAL_EMBEDDING_ROUTE.json](REAL_EMBEDDING_ROUTE.json). **API:** the `anthropic_native` adapter is checked against a loopback contract double. It is blocked without an envelope and, with one, passes chat, structured output and usage. The request cap is enforced, and the key appears in no stored file (`test_paid_route_needs_an_envelope_and_the_key_never_reaches_the_store`). |
| 3 | An embedding change creates a new index generation | PASS | A new model digest gives a new embedding space and generation. The old one is retired and its files are kept. Dependent searches are re-executed (`test_embedding_change_creates_a_new_generation_and_never_mixes_spaces`). With the real model, a corpus revision rebuilt the generation and embedded only the 2 changed passages, reusing 5. |
| 4 | Missing optional capabilities produce a clear state and a working fallback | PASS | The capabilities cover chat, embedding, rerank, paid API and PDF. Their states are `not_configured`, `configured_not_ready`, `ready`, `blocked_without_envelope` and `unavailable`. Profile checks distinguish reachability, model availability, role capability, structured output and usage. Streaming and context limit are marked `not_checked`, not assumed. PDF upload is refused with an explanation. |
| 5 | Independent chat, embedding and reranking ports; Ollama, OpenAI-compatible, native Anthropic | PASS | [providers.py](../../../../src/patent_to_pilot/workbench/providers.py). Each role and adapter is checked in `test_each_role_and_adapter_is_checked_honestly`. |
| 6 | Plain text/Markdown ingestion; optional PDF | PASS (text/MD); PDF parked | [ingest.py](../../../../src/patent_to_pilot/workbench/ingest.py). Bytes are stored exactly (Thai included) with code-point offsets. Re-ingesting identical bytes is a no-op. The same name creates a new version. PDF needs a parser package and therefore a per-item owner approval (see DECISIONS D7). |
| 7 | Dataset metadata registries, read-only schema inspection, loaders without gated/private assets | PASS | [DATASETS.md](DATASETS.md) and `workbench/datasets/` (27 tests). NitiBench+ always reports `gated_acceptance_required`. Evaluator fields cannot reach runtime records. Inspection refuses TEST/qrels paths without opening them. |
| 8 | Source language, canonical IDs, locators and version context preserved | PASS | Ingestion and dataset adapters keep the text unnormalised and the IDs as given; missing IDs stay missing. NitiBench+ `valid_from`/`valid_to` and `as_of` are carried through. |

Additional behaviour delivered beyond the minimum, needed so that ingestion stays correct:

- **New-source events.** A new uncited document joins the candidate's search scope. It re-checks every result for that
  candidate and can overturn an earlier "nothing found": A/R2 went from Unknown to Meets in the browser and in
  `test_a_new_uncited_document_can_overturn_nothing_found`.
- **Index-generation dependencies.** Dense search receipts are bound to the generation and embedding space. Switching
  generation re-executes those searches, and results are reused only when the evidence is identical.

## Test and check runs

| Command | Result |
|---|---|
| `python -m pytest tests/test_ptp_g02_providers.py` | 15 passed |
| `python -m pytest tests/test_ptp_g02_datasets.py` | 27 passed |
| `python -m pytest tests/test_ptp_g01_workbench.py` | 16 passed. One assertion was updated because the capability states are now G02 states. |
| `.venv\Scripts\python.exe scripts\ptp_run.py --smoke` / `--doctor` | 15/15 PASS / OK |
| CLI walkthrough (`--providers`, `--create-project`, `--ingest`, `--run --project`, `--retrieval-mode`) | Works. Hybrid without an index is refused with a clear message (exit 2). |
| `scripts/research/g02_real_route_check.py` (real Qwen3-Embedding-0.6B) | PASS: 1024 dimensions; hybrid run; revision under hybrid; Thai query top hit = the Thai passage (cosine 0.63) |
| Browser QA, 1280 and 360 px, real embedding route | Owner project created; 3 documents added (Thai included); run; profile saved, checked and ready; index built; hybrid on; new-source event overturned Unknown; server restart then recorded hybrid state. 0 console errors, no horizontal scroll at 360 px. Screenshots in `screenshots/`. |
| Full suite `python -m pytest` | See RUN_RECEIPT.json `tests.full_suite`. |

## Defect found and fixed during G02

A retained (identical) assessment kept the search receipt of the run that first committed it. A later recheck therefore
compared against stale hits and re-did work that could have been reused. With the real model, Concept B was reacquired
instead of revalidated after an unrelated revision. The retained assessment now records its latest supporting search.
A regression assertion is in `test_source_revision_refreshes_the_generation_and_reuses_unchanged_vectors`.

## Not done / not verified

- No real paid API call (no envelope). No real Ollama route: Ollama is not installed on the owner PC and installing it
  needs approval. Ollama is covered by contract tests only.
- No real reranker route. Qwen3-Reranker is not a sentence-transformers cross-encoder, so the `/rerank` route is
  contract-tested only.
- Chat models are configurable and checkable but are not yet used by the evidence core. The bounded fixture parser still
  decides outcomes; model-based extraction belongs to G03.
- Explorer double-click and default-browser auto-open (from G01) are still owner-observed items.
