# P4-T01b receipt: requirement Remove and Undo in the Workbench

**Task:** P4-T01b, "Remove and Undo work safely and simply", section 6 of the owner fix plan of 23 Nov 2026
(`PTP_Thai_Search_Structure_Requirements_Fix_Plan_20261123.md`, written against commit `7cf8339a`, the base of this work).
**Date:** 23 Nov 2026. **Cost:** USD 0. No network, model or paid call was used to build or test this.
**Status fields:** `product_readiness`: requirements can be removed and restored, with tests (below).
`method_evidence`: none (a product repair, not a retrieval result). `publication_readiness`: not affected.
**Out of scope here:** Thai search (section 4, a parallel branch) and structural acquisition (section 5, later).

## What the owner sees

- On the Compare tab, each requirement of an owner project has a **Remove** button.
- After a removal, a short **Undo** notice appears for 10 seconds. Undo brings the requirement back with the same ID,
  the same text and the same place in the list.
- **Show removed (n)** lists removed requirements, each with a **Restore** button.
- Removed requirements disappear from the overview matrix and from Compare. Their earlier results stay readable in
  history, and the Changes tab lists "Requirement removed" and "Requirement restored" events.
- With no active requirements the overview says so; Compare and runs still work and plan nothing.
- The sample and synthetic projects stay fixed (HTTP 409 `project_is_fixed`).

## How it works

**Storage (additive; no existing table changed).** `projects.mission_json` keeps only the **active** requirements, so
planning, comparison, Compare and revision processing see active requirements without further changes. Two new
tables hold the lifecycle:

| Table | Holds |
|---|---|
| `requirement_lifecycle` | Per requirement: stable ID, state (`active`/`removed`), monotonic `lifecycle_revision`, content SHA-256, full snapshot, list position, last event |
| `mission_lifecycle` | Per project: monotonic mission revision |

A requirement with no row is active at revision 0. The revision advances on every add, edit, removal and restoration,
including a restoration of identical text.

**Remove (`POST /api/projects/{pid}/requirements/{id}/archive`)** runs in one `BEGIN IMMEDIATE` transaction:
1. Refuse fixed projects. Check that the requirement is active; if the body carries `expected_revision`, check that it
   matches (409 `revision_conflict` otherwise).
2. Take the requirement out of the active mission and save its snapshot and hash.
3. Set its obligations to `retired`. Set its `current` assessments to `retired` and append a `retired` assessment
   event. Citations, dependencies and earlier events are kept.
4. Advance the requirement and mission revisions, and append one `requirement_removed` change event with the snapshot,
   the retired obligations and the retired assessments.

**Restore (`.../restore`)** runs in one transaction. It puts the recorded snapshot back at its old position after
checking the snapshot hash. Obligations are reopened by an UPSERT on the existing key `(project_id, candidate_id,
requirement_id)`, not a blind INSERT. Retired assessments stay historical; the next run assesses the requirement
against the current sources. Both revisions advance and one `requirement_restored` event is appended.

**Idempotence.** Removing a removed requirement answers `already_removed`; restoring an active one answers
`already_active`. Neither writes anything. The UI also disables the button after the first click.

**No ID reuse.** Saving a requirement with a removed ID is refused (409 `requirement_removed`); Undo/Restore is the
only way back. Automatic IDs (`U1`, `U2`, ...) skip removed IDs.

**In-flight results.** Each `plan_obligation` action now records `requirement_lifecycle_revision` and
`requirement_sha256`. Inside the commit transaction, `_commit` rechecks three things: the requirement is still
active, its content hash is unchanged, and its lifecycle revision equals the planned one. A result that fails any
check is not committed. It is recorded as `rejected_stale` with the reason, and counted in the run counters. A
removal followed by a restore of identical text is caught by the revision check. An obligation planned after a
removal is skipped (`skip_stale_obligation`).

**No resurrection.**
- `_process_revision` skips retired obligations and requirements that are not active.
- The obligation updates for source revisions and additions, and the recheck-reuse update, exclude `state='retired'`.
- The index-generation switch and the retrieval-mode switch only touch `done` obligations.
- `comparison()` returns cells for active requirements only.

## Files

- `src/patent_to_pilot/workbench/store.py`: `SCHEMA_P4T01B` (two tables, created in place on existing stores).
- `src/patent_to_pilot/workbench/core.py`:
  - lifecycle section (`archive_requirement`, `restore_requirement`, `requirement_lifecycle`, `_stale_requirement`);
  - commit recheck, plan record and skip;
  - active-only filters in revision processing, source-import invalidation and current cells.
- `src/patent_to_pilot/workbench/workflow.py`:
  - `requirements()` lists revisions and removed requirements;
  - `save_requirement` refuses removed IDs and advances revisions;
  - thin archive/restore wrappers.
- `src/patent_to_pilot/workbench/server.py`: the two POST routes, under the existing POST guards and the server lock.
- `src/patent_to_pilot/workbench/static/app.js`, `app.css`: Remove, Undo notice, Show removed, and the labels for
  the new events and action.
- `tests/test_requirement_lifecycle.py`: 15 tests.

Shared hot spots for the Thai-search merge: core.py's search functions (`fts_*`, `_lexical`, `_search`,
`_make_current`) and the store's FTS table are untouched. The only core edits outside the new section are short,
marked `P4-T01b` lines in `_acquire_and_commit` (counter), `_commit` (recheck), `_execute` (plan record),
`_import_source` and `_process_revision` (retired filter) and `comparison()` (active filter). A future FTS reindex
must not write `obligations`. If it reopens work, it must exclude `state='retired'`, as the existing paths now do.

## Acceptance (section 6) and evidence

| Case | Test |
|---|---|
| Remove before assessment | `test_remove_before_assessment` |
| Remove after assessment, readable history | `test_remove_after_assessment_keeps_readable_history` |
| Undo (same ID/text/position, upsert, history kept) | `test_undo_restores_same_id_and_content_and_reopens_obligations` |
| Repeated clicks, stale revision, unknown ID | `test_repeated_remove_and_restore_are_idempotent` |
| Source update and source addition | `test_source_update_and_addition_do_not_resurrect_removed_obligations` |
| Reindex (index generation) and retrieval switch | `test_reindex_and_retrieval_switch_do_not_resurrect_removed_obligations` |
| App restart | `test_removal_and_restore_survive_restart` |
| In-flight stale commit: removal / remove+restore identical / edit | `test_in_flight_result_is_rejected_after_*` (3 tests) |
| Zero requirements | `test_zero_active_requirements_is_a_valid_empty_state` |
| No ID reuse | `test_removed_ids_are_never_reused` |
| HTTP routes and POST guards | `test_http_archive_restore_routes_and_guards` |
| Read-only sample/synthetic projects | `test_sample_and_synthetic_projects_stay_read_only` |
| UI controls served | `test_ui_offers_remove_undo_and_show_removed` |

**Results (worktree branch, with pypdf):**
- New file: 15 passed.
- With the P4-T01, G01 and G02 Workbench suites: 63 passed.
- Full suite: the only failures are the 8 known SACR r2/r3 supervisor budget tests; there were no errors.
  - In a first run, `test_healthtech_vector_http::test_server_owned_vector_config_binds_http_job_to_exact_input` also
    failed. A background job was still `running` while a smoke run and a browser server were active on the same
    machine. That test is outside the Workbench.
  - It passed on its own, and in a clean full rerun.
- `python scripts/ptp_run.py --smoke`: 15/15 PASS.
- Manual check in the browser on a temporary store: Remove, then the Undo notice, then Undo; and Show removed, then
  Restore. Both restored the requirement in its original position.
