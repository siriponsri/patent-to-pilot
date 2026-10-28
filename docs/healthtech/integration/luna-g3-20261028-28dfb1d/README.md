# Luna G3 backend integration handoff

Run: `luna-g3-20261028-28dfb1d`  
Date: 2026-10-28  
Tested code HEAD: `28dfb1dcaf0f4794d74ba80c2fea09b0108f3f86`  
Status: `BACKEND_COMPLETE_UI_PENDING`

## Purpose and boundary

This handoff records the current backend contract and capability delta for a future Claude-owned local frontend. It covers HealthTech dossier contracts, source inspection, file-backed history, selected-version export, and the three public facts-only dossier walkthroughs. It does not implement or merge frontend code, create a service, call a provider, fetch a source, or change the Claude worktree.

The Claude UX snapshot remains at `96c63b14a1a2df8e8f8b816edee0dff7feddc3d3` in `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-claude-ux-20261028`. That worktree is paused and untouched. Treat the JSON in `adapter-contract.json` as the Luna-side delta to inspect before frontend integration; the older UX prose may describe pre-repair limitations.

## Actual backend surface

The current Python surface is local and synchronous:

- `DossierInput.model_validate_json(...)` validates the closed input envelope. Public cases reject synthetic sources, evaluator-only sources, newer-than-cutoff sources, duplicate canonical patent documents, and evidence outside permitted inputs.
- `run_dossier(data, run_id, code_commit)` returns `(DossierVersion, AcquisitionEvent[], RunManifest)` for the declared offline policy. It is not an HTTP job service and does not dispatch a provider.
- `save_version(history_dir, dossier)` creates `version-####.json` with exclusive creation, flush/fsync, and cleanup after an interrupted write.
- `append_user_edits(history_dir, edits, expected_parent_version=...)` creates the next contiguous version and rejects a stale parent. A caller must preserve the rejected writer's text as a recoverable conflict; the backend does not merge conflicts or provide idempotency keys.
- `select_version(...)`, `load_versions(...)`, and `history_manifest(...)` read a contiguous local chain. `source_view(...)` returns the pinned source identity, revision, jurisdiction, date, hash, synthetic flag, and requested top-level field when available.
- `manage_dossier_history.py export ... --version N` writes selected-version JSON plus English and Thai Markdown. `export_markdown(...)` keeps source evidence, unresolved items, next requests, version context, and a separate `User edits` section.

Exact signatures, capability states, and file hashes are in [`adapter-contract.json`](adapter-contract.json). The proposed frontend adapter names in that JSON are integration seams, not current Python exports or HTTP endpoints.

## Safe frontend expectations

The frontend may import a validated dossier, render source-backed facts, show unresolved/unknown items, preserve user overlays in a separate local namespace, and export a labelled recovery package. It must not:

- turn `retrieved_candidate` into `disclosed_link` without independent disclosure evidence;
- interpret an empty patent input pool as evidence that no patents exist;
- expose evaluator relations, provider payloads, private paths, credentials, or arbitrary fetch controls;
- claim a server, background job, cancellation, collaboration, PDF/DOCX export, monetary savings, clinical suitability, FTO, investment merit, or publication readiness;
- treat the Python dossier version as a browser-local snapshot version.

The current public cases are `K121849`, `K163345`, and `K190167`. Each has one public regulatory source, seven evidence items, zero candidates, three unresolved items, and three next information requests. They are facts-only walkthroughs with empty patent input pools, not device–patent coverage evidence.

## Verification evidence

- Backend repair tests: `tests/test_healthtech_repairs.py::test_history_rejects_stale_parent_and_export_includes_user_edits` and `tests/test_healthtech_repairs.py::test_history_two_simultaneous_writers_have_one_commit_and_one_conflict`.
- Current-head revalidation: [`LUNA_G1_G3_CURRENT_HEAD_20261028-210230.md`](../../LUNA_G1_G3_CURRENT_HEAD_20261028-210230.md) and [`current-head-210230.json`](../../evidence/luna-g1-g3-20261028/current-head-210230.json).
- The current offline suite is recorded at 281 tests with zero failures, errors, and skips; network attempts, credential reads, provider calls, and paid cost are all zero. This is engineering evidence only.
- The actual no-code UI walkthrough remains `NOT_RUN / PENDING_CLAUDE_PAUSED`; do not promote this handoff to full HT-G3 completion.

## Next actor

Claude may implement a local frontend on its own branch after rechecking the current base and path ownership. The next integration review must compare the frontend adapter to this handoff, run its own import/source/edit/conflict/export checks, and keep UI capability status separate from backend evidence. Bridge rights/cohort/split evidence remains a separate `BLOCKED_LOCAL` research dependency.
