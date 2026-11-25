# Documentation map

Use the [root README](../README.md) to run the local reader and the [Planner handoff](../HANDOFF.md) to resume work. The [evidence index](../INDEX-PLAN.md) keeps measured outcomes and original source locations accessible across program changes.

## Start here

| Need | Location |
|---|---|
| Active program and branch ownership | [RA Pharma master plan](ra-pharma/MASTER-PLAN.md) · [Common evidence contract](ra-pharma/EVIDENCE-CONTRACT.md) |
| Research executor | [Research brief](ra-pharma/research/BRIEF.md) · [Research handoff](ra-pharma/research/HANDOFF.md) |
| Product executor | [Product brief](ra-pharma/product/BRIEF.md) · [Product handoff](ra-pharma/product/HANDOFF.md) |
| Earlier program | [S0–S5 board](evidence-scope/MASTER-PLAN.md) · [Historical research freeze](evidence-scope/FREEZE.md) · [S4 integrated validation](evidence-scope/receipts/S4-integrated-verification.md) |
| Project overview, quick start, testing | [README.md](../README.md) |
| Current state, blockers, running jobs, next steps | [HANDOFF.md](../HANDOFF.md) |
| Plans, goals and evidence locations | [INDEX-PLAN.md](../INDEX-PLAN.md) |
| Rules for every contributor and agent | [AGENTS.md](../AGENTS.md), [CLAUDE.md](../CLAUDE.md) |
| Starting on a new account | [current handoff](../HANDOFF.md), [maintenance/AGENT-LESSONS.md](maintenance/AGENT-LESSONS.md) |

## Plans and tracking

| What | Location | Notes |
|---|---|---|
| Inherited P0–P5 board | [tracking/owner-note-22112026/PHASE_BOARD.md](tracking/owner-note-22112026/PHASE_BOARD.md) | Rendered from the registry; status and research outcome are separate fields |
| Goal and task registry | [tracking/owner-note-22112026/goal_registry.json](tracking/owner-note-22112026/goal_registry.json), [phase_tasks.csv](tracking/owner-note-22112026/phase_tasks.csv) | Machine-readable source of the board |
| Task receipts | [tracking/owner-note-22112026/receipts/](tracking/owner-note-22112026/receipts/) | Small receipts; large or restricted outputs stay in `../_private_artifacts/` |
| AFFiNE page sources | [tracking/owner-note-22112026/affine/](tracking/owner-note-22112026/affine/) | Projection of the registry for the AFFiNE workspace; AFFiNE is never a research dependency |
| Earlier goal tracker (G01–G08) | [tracking/PTP-PHASE-TRACKER.md](tracking/PTP-PHASE-TRACKER.md) | Superseded by the P0–P5 board; kept as history |
| Owner decisions | [maintenance/OWNER-DECISIONS-20261122.md](maintenance/OWNER-DECISIONS-20261122.md) | Dated approvals and scope changes |
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

The following receipts retain their original cohorts, comparators and release scope. The new three-specialist research comparison starts from its own prospective record.

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

Historical G-numbers, HT identifiers and Paper 1–3 plans keep their original meanings. New work follows the [RA Pharma dispatch board](ra-pharma/MASTER-PLAN.md).
