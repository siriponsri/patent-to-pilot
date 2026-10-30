# Luna main merge verification

Run ID: `luna-main-merge-20261030`

Date: `2026-10-30` (Asia/Bangkok)

Status: `PASS_LUNA_ANCESTOR_VERIFIED`

This record verifies the Luna publication work is already included in the
current `origin/main` candidate. The Luna publication commit is an ancestor
of the remote main tip, so no duplicate merge commit is required.

## Revisions

- Luna publication: `bf416e9ab6b6d2d031e885d4b6bb0a2d08bf9ebc`
- Remote-embedding implementation: `fd32ef8`, `b30ddff`, `68c4fdf`
- Runtime export and SSH canary tip: `a34a228891332d27ec34112a68a02666507f3ddb`
- Audit scope: verification and publication of the existing main candidate

## Checks

- `git merge-base --is-ancestor bf416e9 origin/main`: PASS
- Clean detached verification worktree: PASS
- `git diff --check origin/main^ origin/main`: PASS
- Targeted remote/vector/DAPFAM/integration tests: `21 passed`
- Full suite via `python -m pytest`: `451 passed, 1 skipped, 2 warnings`
- DuckDB CLI: `v2.0.0`

The direct `pytest` executable was not used as the final result because its
wrapper omitted the repository root from `sys.path` during collection. The
canonical `python -m pytest` invocation passed the full suite.

## Boundaries

Remote GPU encoding, vector transfer, dense evaluation, and vector-backed
dossier execution remain `NOT_RUN`. The allocation facts required by that
branch are still absent. This merge verification does not change that status,
does not read credentials, and does not publish runtime bundles or model files.

The user's existing dirty main checkout was preserved. No reset, stash, broad
cleanup, or unrelated file staging was performed.

Machine-readable details are in `verification.json`; the continuation note is
in `NEXT_ACTIONS.md`.
