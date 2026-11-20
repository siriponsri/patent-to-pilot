# Housekeeping record — 21 November 2026

Owner request (21 Nov 2026): align the repository with program PTP-2026-11-21, delete unrelated docs, unused branches and
old goal documents, and make the documentation current. Everything removed here can be recovered from Git history; the base
commit before this cleanup is `40780c97`.

## 1. Branches and worktrees

Every tip was recorded before deletion. Recover a branch with `git branch <name> <sha>`.

| Branch | Tip SHA | Merged into main | Where it existed |
|---|---|---|---|
| `claude/paper2-harness-0d504a` | `120f523f8e888360b0c74fcc915014e06080c41f` | yes | local (remote already gone) |
| `claude/prod-p0-evidence-bedc49` | `0f6e78938d560eb8a93b3be25c34876ce921f61e` | yes | local (remote already gone) |
| `codex/patent-to-pilot-long-run-20261031` | `0cf41e0d37cac75bc9475c8604ab3dabb5c5fd66` | no (1 commit) | local + worktree |
| `codex/pepo-paused-audit-20261101` | `a0809b4b124a6e19b8aea58c4258397aa60715df` | no (2 commits) | local + remote + worktree |
| `codex/research-product-o1-o4-20261031` | `b4bc13ccf8a9a71a8f50d16346ae1c6557bc69d0` | yes | local + remote + worktree |
| `codex/pepo-ui-integration-20261031` | `0d049802d36bc2eebe60331ec444d62469fd767f` | yes | remote only |

The two unmerged Codex branches hold HealthTech HTTP-job and queued-resume work from 1 Nov 2026 that the program no longer
uses. Only `main` remains, locally and on `origin`.

Worktrees removed: `../_worktrees/patent-to-pilot-long-run-20261031` (134 uncommitted paths),
`../_worktrees/patent-to-pilot-research-product-20261031` (26 uncommitted paths), the clean Codex worktree
`Documents/Codex/2026-11-01/task-3/publish-http`, and an empty orphan folder `../_worktrees/patent-to-pilot-long-run-20261102`.
None was locked. Before removal, the uncommitted files, a binary patch and `git status` of each dirty worktree were copied
to `../_private_artifacts/worktree-salvage/<name>/` (about 17 MB, outside Git), with the branch manifest in
`branch-manifest-20261121.txt`. `git worktree prune` left only the main checkout.

Kept: two stashes from 30 Oct 2026 (`ba92cf3a`, `5e95e5c2`); drop them only on the owner's request.

## 2. Documents removed (72 files, about 2.44 MB)

| Group | Files | Why |
|---|---|---|
| Root goal and plan docs: `GOAL.md`, `PLAN.md`, `MASTER-PLAN.md`, `HANDOFF_PROMPT.md` | 4 | Superseded by program PTP-2026-11-21; no longer updated |
| `docs/GOAL.md`, `docs/PLAN.md`, `docs/CODEX_CLI_HANDOFF.md`, `docs/G03_DATA_ACQUISITION.md`, `docs/RESEARCH_GAP_MATRIX.md`, `docs/TOOLING_REGISTRY.md` | 6 | Oct 2026 goal-era documents |
| `docs/handoff/` | 18 | Oct 2026 Luna/Pepo agent handoffs |
| `docs/provider-pilot/`, `docs/research/`, `docs/product/` | 16 | Oct 2026 provider pilot, G02/G13 readiness and product contracts, replaced by the owner's `product/` specification |
| `docs/architecture/G04-G07-G08-interfaces.md` | 1 | Old goal namespace that collides with the new G04–G08 |
| `docs/healthtech/` root handoffs (five `LUNA_*` notes, `PRELIVE_OFFLINE_RECEIPT_2026-10-27.md`, `G1_G2_RECEIPT.md`) | 7 | Oct 2026 status notes; the audit records they summarise remain. Three others (`G3_NO_CODE_JOURNEY_TH_EN.md`, `LUNA_G1_G3_RECEIPT_20261028-200041.md`, `LUNA_G1_G3_REVALIDATION_20261028-203003.md`) were kept because `docs/healthtech/integration/*/adapter-contract.json` binds their hashes and `tests/test_healthtech_integration_contract.py` reads them |
| `memory/` and `archives/INDEX.md` | 7 | Shared-memory index of 10 Nov, replaced by HANDOFF/INDEX-PLAN |
| `docs/writing/RESEARCH-ROADMAP.md`, `docs/writing/LANE-WORK-ORDERS.md` | 2 | 19 Nov three-paper roadmap and lane plan, superseded by the one-paper program |
| `assets/` (old logo, architecture and goal-map images) and `docs/assets/patent-to-pilot/` | 11 | Replaced by `docs/assets/logo.svg` and `docs/assets/architecture.svg` |

Moved: `RELATED_PAPERS.md` → `literature-review/healthtech/RELATED_PAPERS.md` (links repaired).

Deliberately kept as evidence the new paper may need: `docs/healthtech/research/` (frozen pre-declarations, P1-DAPFAM,
P1-BridgeRet, AM-7 and B53 records, Paper 53/DAPFAM audits), `docs/healthtech/audits/` (tests read several receipts),
`docs/writing/` (IS2 and journal drafts), `literature-review/`, and `docs/architecture/ADR-0001` (still describes the FTS5
basis of G01; annotated). Historical documents may still contain links to removed files.

## 3. Handoff files rewritten

`CLAUDE.md`, `HANDOFF.md` and `INDEX-PLAN.md` (together about 1.14 MB of dated history) were rewritten as short current-state
documents for PTP-2026-11-21. Their previous content is preserved verbatim in
[archives/HANDOFF-HISTORY-TO-20261121.md](../archives/HANDOFF-HISTORY-TO-20261121.md). `AGENTS.md` and `README.md` were
rewritten; `docs/writing/README.md` now records the one-paper decision. All standing rules were carried over, plus the new
rule to pull dr-train artifacts to local after every phase and delete remote copies that are no longer needed.

## 4. Not touched

`docs/owner/` (owner-local, untracked), `src/patent_to_pilot/workbench/`, `scripts/ptp_run.py`, `Start-PTP.cmd`, `tests/`,
`artifacts/owner-program/`, and the paths owned by the parallel dr-train cleanup session (`artifacts/maintenance/`,
`scripts/maintenance/`, `docs/maintenance/`, `../_private_artifacts/` apart from the new `worktree-salvage/` folder).
