# G01 repository audit (PTP-2026-11-21 / G01)

- **Repository:** `C:\Users\User\Desktop\myProject\patent-to-pilot`
- **Branch:** `main`
- **Base commit:** `99a5be1a` (= origin/main at start)

**Pre-existing untracked items** (all preserved, none modified):

- `.claude/`
- `docs/owner/`
- `uv.lock`
- `docs/healthtech/research/PATENT_TO_PILOT_RESEARCH_AND_CLAUDE_HANDOFF_2026-11-09.md`

**Exception:** one entry, `ptp-workbench`, was appended to the owner-local `.claude/launch.json` for the browser preview. The original was backed up before the edit.

## Inspected modules and reuse decisions

| Component | Actual code | Observed | Decision |
|---|---|---|---|
| Python runtime | `.venv\Scripts\python.exe` | 3.12.14; SQLite 3.53.1 with FTS5; pydantic 2.14 | Reused as the owner runtime. G01 needs only the standard library. |
| FTS5 lexical search | `src/patent_to_pilot/retrieval/fts.py` (`FTSIndex`) | The patent-document schema (title/abstract/claims) allows one source identity/version per index file (it raises `ValueError` on a second one) and has no current-version pointer | Pattern reused: FTS5 `unicode61` tokenizer, bm25 ordering. A new multi-source, current-scope passage table lives in `workbench/store.py`. Extending `FTSIndex` would have broken its single-source invariant. |
| Append-only SQLite | `src/patent_to_pilot/core/repository.py` (`SQLiteRecordRepository`) | Typed-record JSON history for HealthTech records | Concept reused (append-only, explicit current pointers). Separate schema so the sample never joins research stores. |
| Literal spans | `src/patent_to_pilot/extraction/interfaces.py::_original_span` | Finds a query in text and returns offsets | Not needed. G01 spans come from the fixture heading grammar, with code-point offsets on the unmodified text. |
| Loopback HTTP | `src/patent_to_pilot/healthtech/http.py` (`ThreadingHTTPServer`, `JobStore`) | HealthTech dossier jobs with domain contracts | Pattern reused (stdlib server, loopback only, JSON errors). A new small app is in `workbench/server.py`. |
| Frontend | `frontend/healthtech-web` | TH/EN dossier UI served by Node (`serve.mjs`), not by Python | Not reused. The spec requires one Python process and no Node at runtime. A small static UI is in `workbench/static/`. |
| Providers | `src/patent_to_pilot/core/providers.py`, `healthtech/generation.py` | Local Qwen and API providers exist | Deliberately not imported. Capabilities report lexical active and local/API disabled; a socket guard proves no remote call. |

Historical G01–G22 records were not changed. New records use the compound identity `PTP-2026-11-21/G01`.
