# G01 decisions

All rows are dated 2026-11-21 and none needed owner input.

| # | Question | Choice | Reason |
|---|---|---|---|
| D1 | Where does the core live? | New package `src/patent_to_pilot/workbench/`: `core.py` holds `EvidenceCore`; `parser.py`, `store.py`, `guard.py` and `server.py` sit beside it | The existing modules are domain-specific (see `REPO_AUDIT.md`). One service is called by the CLI and the HTTP app. |
| D2 | New dependencies? | None. Standard library only (sqlite3/FTS5, http.server) | Smallest change. No license impact. |
| D3 | Runtime fixtures | Copied byte-exact to `workbench/sample/`; `.gitattributes` sets `-text` | The manifest SHA-256 pins LF bytes, and Git `core.autocrlf=true` would otherwise rewrite them. |
| D4 | Test oracle | Copied to `tests/fixtures/ptp_g01/` and read only by `tests/test_ptp_g01_workbench.py` | A test asserts that the runtime package never references it. The static server serves only 3 named files. |
| D5 | Passage boundary | From just after the `## <ID>` heading's newline to the line break before the next blank line (or the next heading, or EOF), with that line break excluded | Matches the fixture README. The quote carries no trailing newline. Offsets are code points on the unmodified decoded text. |
| D6 | Current scope | `passage_fts` holds only current versions. The revision deletes the old rows and inserts the new ones in the same transaction that moves `current_sources` | A current search cannot return a stale version. History stays in `source_versions` and `passages`. |
| D7 | Search rule | FTS5 phrase of the requirement query, filtered by `candidate_id` (from the source metadata), top 3, ordered by bm25, then source, version, passage | Deterministic. No mapping from requirement to source. |
| D8 | Outcome vocabulary | `meets`, `does_not_meet`, `unknown`; UI adds `needs_review` | Same as the fixture oracle. No existing enum was renamed. |
| D9 | Malformed evidence | Unknown, plus a validation issue that names the problem | The spec forbids guessing. |
| D10 | Change handling | Citation dependents → `needs_review` (persisted) → re-acquired. Search-scope dependents → search re-executed; the assessment is reused only if the hit identities are unchanged. Other candidates → not re-run. Strategy recorded as `selective_by_dependency` | The trace shows real work: 3 searches and 1 read for the change run, not a full recompute. |
| D11 | Idempotency | The event is stored with its hash. A repeat returns `already_applied` with the recorded result. Bytes that do not match the pinned hash raise `hash_mismatch` | Spec G01-A11. |
| D12 | Port | 8765, else the next free port (up to +19). **Exclusive bind** (`SO_EXCLUSIVEADDRUSE`, `allow_reuse_address=False`) | Windows QA showed that Python's default `SO_REUSEADDR` let a second server take a port already in use. Fixed, with a regression test. |
| D13 | Data dir | `--data-dir`, else `%PTP_DATA_DIR%`, else `%LOCALAPPDATA%\PatentToPilot\workbench\workbench.sqlite3` | Kept outside the repo and outside the static mount. Backups use the SQLite backup API (`--backup`). |
| D14 | Browser auto-open | `Start-PTP.cmd` passes `--open`. `PTP_NO_BROWSER=1` suppresses it (used for automated QA) | The owner gets the page opened automatically; tests do not open a browser. |
