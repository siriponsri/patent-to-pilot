# Documentation map

Where each kind of document lives. The repository overview is the [root README](../README.md); the plan and evidence index
is [INDEX-PLAN.md](../INDEX-PLAN.md), and the current state is [HANDOFF.md](../HANDOFF.md). This page only points to
locations: when a location changes, update it here and in INDEX-PLAN.md.

## Start here

| Need | Location |
|---|---|
| Project overview, quick start, testing | [README.md](../README.md) |
| Current state, blockers, running jobs, next steps | [HANDOFF.md](../HANDOFF.md) |
| Plans, goals and evidence locations | [INDEX-PLAN.md](../INDEX-PLAN.md) |
| Rules for every contributor and agent | [AGENTS.md](../AGENTS.md), [CLAUDE.md](../CLAUDE.md) |
| Starting on a new account | [maintenance/NEXT-ACCOUNT-HANDOFF-20261122b.md](maintenance/NEXT-ACCOUNT-HANDOFF-20261122b.md), [maintenance/AGENT-LESSONS.md](maintenance/AGENT-LESSONS.md) |

## Plans and tracking

| What | Location | Notes |
|---|---|---|
| Live phase board (P0–P5) | [tracking/owner-note-22112026/PHASE_BOARD.md](tracking/owner-note-22112026/PHASE_BOARD.md) | Rendered from the registry; status and research outcome are separate fields |
| Goal and task registry | [tracking/owner-note-22112026/goal_registry.json](tracking/owner-note-22112026/goal_registry.json), [phase_tasks.csv](tracking/owner-note-22112026/phase_tasks.csv) | Machine-readable source of the board |
| Task receipts | [tracking/owner-note-22112026/receipts/](tracking/owner-note-22112026/receipts/) | Small receipts; large or restricted outputs stay in `../_private_artifacts/` |
| AFFiNE page sources | [tracking/owner-note-22112026/affine/](tracking/owner-note-22112026/affine/) | Projection of the registry for the AFFiNE workspace; AFFiNE is never a research dependency |
| Earlier goal tracker (G01–G08) | [tracking/PTP-PHASE-TRACKER.md](tracking/PTP-PHASE-TRACKER.md) | Superseded by the P0–P5 board; kept as history |
| Owner decisions | [maintenance/OWNER-DECISIONS-20261122.md](maintenance/OWNER-DECISIONS-20261122.md) | D1–D10 |
| Spending proposals and records | [maintenance/API-BUDGET-PROPOSAL-20261122.md](maintenance/API-BUDGET-PROPOSAL-20261122.md), [healthtech/research/g03-dev/g03-dev-a3-spend.json](healthtech/research/g03-dev/g03-dev-a3-spend.json) | No paid call without a recorded owner envelope |

The owner's program packages (`docs/owner/`) are owner-local, untracked and read-only. They are not part of the published
repository; tracked documents summarise or reference them but never copy them.

## Architecture and product

| What | Location |
|---|---|
| Design record for the bounded core and local search | [architecture/ADR-0001-bounded-core-and-local-search.md](architecture/ADR-0001-bounded-core-and-local-search.md) |
| Logo and the foundation-slice architecture figure | [assets/](assets/) |
| Foundation acceptance receipts (local slice; provider, ingestion and dataset contracts) | [G01/STATUS.md](../artifacts/owner-program/PTP-2026-11-21/G01/STATUS.md), [G02/STATUS.md](../artifacts/owner-program/PTP-2026-11-21/G02/STATUS.md) |
| Owner walkthroughs | [G01/OWNER_START.md](../artifacts/owner-program/PTP-2026-11-21/G01/OWNER_START.md), [G02/OWNER_START.md](../artifacts/owner-program/PTP-2026-11-21/G02/OWNER_START.md) |
| Dataset contracts | [G02/DATASETS.md](../artifacts/owner-program/PTP-2026-11-21/G02/DATASETS.md) |

## Research evidence

Frozen protocols, results and audits. Every item keeps its original scope; none is a result of the proposed structural
method.

| Topic | Location |
|---|---|
| Baselines and candidate policy on allowed DEV data (protocol, amendments 1–3, decision memo) | [healthtech/research/g03-dev/](healthtech/research/g03-dev/) |
| B53.0 and the PatenTEB/DAPFAM overlap audit | [healthtech/research/b53-0/](healthtech/research/b53-0/) |
| Pre-declarations and comparability audits (B53, DAPFAM, Paper 53) | [healthtech/research/plans/](healthtech/research/plans/) |
| P1-BridgeRet manifests, DEV baselines, fine-tuning grid, AM-7 | [healthtech/research/paper1-bridgeret/](healthtech/research/paper1-bridgeret/) |
| P1-DAPFAM (closed) | [healthtech/research/paper1-report/](healthtech/research/paper1-report/) |
| DAPFAM acquisition pre-checks (all NO_GO; do not repeat) | [healthtech/research/paper2-precheck/README.md](healthtech/research/paper2-precheck/README.md) |
| Audit convention and run receipts | [healthtech/audits/README.md](healthtech/audits/README.md) |
| Related work | [../literature-review/README.md](../literature-review/README.md) |

## Maintenance and runbooks

| What | Location |
|---|---|
| dr-train artifact pull and prune procedure (after every phase) | [maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md](maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md) |
| Pull/prune summaries | [../artifacts/maintenance/](../artifacts/maintenance/) |
| Agent lessons | [maintenance/AGENT-LESSONS.md](maintenance/AGENT-LESSONS.md) |
| Documentation consistency audit (22 Nov 2026) | [maintenance/DOCS-CONSISTENCY-AUDIT-20261122.md](maintenance/DOCS-CONSISTENCY-AUDIT-20261122.md) |
| Repository housekeeping record (21 Nov 2026) | [HOUSEKEEPING-20261121.md](HOUSEKEEPING-20261121.md) |

## Writing

| Track | Location | Rule |
|---|---|---|
| Track overview | [writing/README.md](writing/README.md) | Never mix text, numbers or claims between tracks without noting the source |
| The research paper | [writing/journal/](writing/journal/README.md) | Paper 86 is banned (enforced by `tests/test_org_adaptive_terminology.py`); arXiv:2605.24297 is not used |
| Independent Study 2 | [writing/is2/](writing/is2/README.md) | Paper 86 allowed here only; B53 results in [writing/is2/results/](writing/is2/results/) |

## History

| What | Location |
|---|---|
| Handoff history before 21 Nov 2026 | [../archives/HANDOFF-HISTORY-TO-20261121.md](../archives/HANDOFF-HISTORY-TO-20261121.md) |
| HealthTech-era history and recovery links | [healthtech/HISTORY.md](healthtech/HISTORY.md) |

Historical identifiers (earlier G-numbers, HT-\*, Paper 1–3 plans) keep their original meanings in these records; the
current plan is the P0–P5 board above.
