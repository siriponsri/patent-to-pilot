# PTP-2026-11-21 / G01 progress (resumable)

Continue from here after a context compaction: re-read `docs/owner/owner-note-21112026/11_CLAUDE_G01_PROMPT.md`, `product/G01_VERTICAL_SLICE.md`, then this file.

## Decisions so far

- The new package is `src/patent_to_pilot/workbench/`.
  - Existing `healthtech/http.py` (dossier jobs), `retrieval/fts.py` (one source identity/version per index, patent schema) and `frontend/healthtech-web` (Node server) are domain-specific.
  - Their patterns are reused: stdlib `ThreadingHTTPServer` on loopback, FTS5 `unicode61`, append-only SQLite.
  - See `REPO_AUDIT.md`.
- Runtime fixtures were copied byte-exact into `src/patent_to_pilot/workbench/sample/`. All 5 SHA-256 values match the manifest. `.gitattributes` `-text` pins the LF bytes.
- The test oracle copy is in `tests/fixtures/ptp_g01/expected_assertions.json`. It is read by tests only.
- Interpreters:
  - runtime: `.venv\Scripts\python.exe` (3.12.14, FTS5 3.53.1, pydantic 2.14);
  - tests: system `python` 3.12.10 with pytest.

## Status

- [x] Read package docs, inspect repo, copy fixtures
- [x] core: `workbench/{core,parser,store,guard}.py`
- [x] HTTP server `workbench/server.py` + static Workbench `workbench/static/`
- [x] CLI `scripts/ptp_run.py` + `Start-PTP.cmd` (CRLF). Doctor OK; smoke 15/15 PASS (3.5 s)
- [x] tests `tests/test_ptp_g01_workbench.py`: 15 PASS (system python 3.12.10 + pytest)
- [x] browser QA (1280/360, restart), Windows cmd launcher QA (busy-port bug found + fixed), reports written
- [x] commit/push + handoff

## Current task

G01 complete. Next goal per 02_GOALS_AND_PHASES.md; owner observation of Explorer double-click pending.
