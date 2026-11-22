# G02 progress: provider, ingestion and dataset contracts (resumable)

**Spec:** `docs/owner/owner-note-21112026/02_GOALS_AND_PHASES.md` §G02, `03_MODELS_AND_PROVIDERS.md`,
`04_DATASETS_AND_TRANSFER.md`, `08_ARCHITECTURE_FLOW.md`, `product/LOCAL_ARCHITECTURE.md` §8.
**Spend:** USD 0. **Base:** `6742ce7b` (G01 at `40780c97`).

## Status: COMPLETE (22 Nov 2026)

- [x] Read specs; audit G01 core, store, server and guard
- [x] `workbench/providers.py` + `profiles.py`: chat/embedding/rerank ports, three adapters, connection checks,
      env-var credential references, remote and spend policy, request ledger
- [x] `workbench/generations.py`: embedding-space and generation identity, build beside the old one, validation,
      activation, stale detection, vector reuse
- [x] `workbench/ingest.py` + core: owner projects, text/MD ingestion, source_addition and source_revision events
- [x] `workbench/datasets/`: registry, availability, schema inspection, adapters (background agent; 27 tests)
- [x] Core wiring: hybrid retrieval, index-generation dependencies, retrieval-mode and generation-switch events
- [x] HTTP routes, CLI flags, Providers view, Add-document UI, project switcher
- [x] Tests (15 + 27 + 16), smoke, real embedding route (Qwen3-Embedding-0.6B), browser QA at 1280/360 with restart
- [x] STATUS, DECISIONS, OWNER_START, RUN_RECEIPT, handoff, memory, AGENT-LESSONS

## Next action

G03 (baselines and candidate policy on allowed DEV). Separately: B53 Stage 2 evaluation, because its scores finished
on 22 Nov.
