# G01 acceptance status (PTP-2026-11-21 / G01)

**Overall: COMPLETE for the G01 contract.** One check remains for the owner to observe: double-clicking the launcher in Explorer and the automatic opening of the default browser. Both were not observed (see A14).

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| A01 | Repository audit | PASS | `REPO_AUDIT.md` |
| A02 | CLI and HTTP use the same core | PASS | `test_http_and_cli_reach_the_same_core`: same `core_identity` and `config_sha256`, with `invoked_via` set to `http` or `cli`. The smoke command runs a CLI run and then an HTTP change. |
| A03 | Initial index = 4 versions, no v2, no oracle | PASS | `test_initial_import_excludes_revision`, `test_runtime_never_references_test_oracle`, smoke check 1 |
| A04 | Real search/read/check gives the fixture matrix | PASS | `test_initial_comparison_matches_oracle_and_citations_are_literal`. The run has 6 search actions and 5 passage reads. |
| A05 | Every non-unknown decision has an exact citation | PASS | The literal equality `text[start:end] == quote` and the hash are checked at commit and again on resolve. Same test, plus smoke check 4. |
| A06 | Thai text and °C survive storage, JSON, display and export | PASS | Exact string checked in the core, in a new process, in HTTP JSON, and in the browser drawer (`<mark>` text identical). Screenshot `01`. |
| A07 | Revision creates v2, keeps v1 and reopens affected work | PASS | `test_source_revision_flow_matches_oracle`. Assessment events read `committed`, `needs_review`, `superseded`. |
| A08 | Range criterion changes after v2 | PASS | A/R2 goes from meets (40–70 °C) to does_not_meet (40–60 °C). The 69/70/71 variations follow the parsed numbers. |
| A09 | Current search uses v2; v1 citation still valid | PASS | `_search` returns only `DEMO-S2@v2`. The v1 citation resolves with status `historical` (browser label: "Superseded (current: v2)"). |
| A10 | Restart preserves everything | PASS | `test_restart_from_a_new_process` (a separate Python process). Browser: server stopped and restarted, page shows a "Recorded run" with the v2 state (screenshot `04`). |
| A11 | Duplicate change safe; malformed evidence explicit | PASS | `test_duplicate_and_conflicting_change` (already_applied, hash_mismatch, not-found), `test_malformed_range_is_a_validation_issue_not_a_guess`, `test_missing_citation_errors_are_specific` |
| A12 | No remote model call or download | PASS | Socket guard `loopback_only` around runs (smoke and tests): 0 remote attempts. Capabilities: local and API models disabled. The core imports no provider module. |
| A13 | One local server, working UI, truthful labels | PASS | Browser QA at 1280 px and 360 px. Steps: open sample (no fabricated result), run, citation drawer (focus returns to the citation button on close), revision, change diff, run trace, providers, restart. No console errors and no horizontal scroll at 360 px. |
| A14 | Launcher, doctor, smoke, instructions | PASS (partly owner-observed) | `Start-PTP.cmd` was run through `cmd.exe` from another working directory with port 8765 busy. It chose 8766, the health check passed and an HTTP run completed. Doctor OK. Smoke 15/15. **NOT_RUN:** Explorer double-click and the automatic opening of the default browser (suppressed with `PTP_NO_BROWSER` during QA). |
| A15 | Research TEST and labels stay isolated | PASS | Own store `workbench.sqlite3` and project `sample-thermal-module-demo-01`. No research store, TEST data or historical goal record was read or written. |

## Test runs

| Command | Result |
|---|---|
| `python -m pytest tests/test_ptp_g01_workbench.py` | 16 passed |
| `.venv\Scripts\python.exe scripts\ptp_run.py --smoke` | 15/15 PASS, 1.6–3.5 s |
| `.venv\Scripts\python.exe scripts\ptp_run.py --doctor` | OK |
| Full suite `python -m pytest` | Only the 8 known pre-existing failures (`test_sacr_r2/r3_smoke_supervisor` budget cases); no new failures |
