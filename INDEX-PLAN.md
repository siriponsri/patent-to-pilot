# Index: plans, goals and evidence

Program **PTP-2026-11-21**. This is a map, not a diary: update a row when a goal, plan or evidence location changes. The
current narrative state lives in [HANDOFF.md](HANDOFF.md). Pre-21-Nov index rows are archived in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md).

## 1. Program sources (owner-local, untracked, read-only)

`docs/owner/owner-note-21112026/`:

| File | Use |
|---|---|
| `00_START_HERE.md` | Program decision and package map |
| `01_PROGRAM_CHARTER.md` | Research question, three proposed contributions, scope |
| `02_GOALS_AND_PHASES.md` | Goal registry G01–G08 and acceptance |
| `06_RESEARCH_PROTOCOL.md`, `07_PAPER_BLUEPRINT.md` | Method, evaluation and paper plan |
| `08_ARCHITECTURE_FLOW.md`, `product/LOCAL_ARCHITECTURE.md` | Engine and local application architecture |
| `10_PAPER53_BRIDGE.md` | How the new work relates to Paper 53 |
| `12_EVIDENCE_STATUS_AND_SOURCES.md` | What was checked, what remains unmeasured |
| `13_ACCEPTANCE_AND_REPORTING.md`, `14_BUDGET_AND_RELEASE.md` | Reporting rules, budget and release limits |

## 2. Goals

| Goal | Phase | Status | Receipts |
|---|---|---|---|
| G01 Shared core and local vertical slice | Foundation | COMPLETE (21 Nov 2026) | [artifacts/owner-program/PTP-2026-11-21/G01/](artifacts/owner-program/PTP-2026-11-21/G01/) |
| G02 Provider, ingestion and dataset contracts | Foundation | NEXT | — |
| G03 Baselines and candidate policy on allowed DEV | Method development | Not started | — |
| G04 Matched patent benchmark | Evidence | Not started | — |
| G05 Transfer and evidence maintenance | Evidence | Not started | — |
| G06 English-first product beta | Product and paper | Not started | — |
| G07 Unified paper and evidence audit | Product and paper | Not started | — |
| G08 IS2 demonstration and release rehearsal | IS2 delivery | Not started | — |

Receipts for each goal go in `artifacts/owner-program/PTP-2026-11-21/<goal>/` (STATUS, RUN_RECEIPT, DECISIONS, PROGRESS).

## 3. Historical evidence the new paper may use

All rows keep their original scope; none is a result of the new engine.

| Topic | Location | Status |
|---|---|---|
| Paper 53 / DAPFAM comparability | [plans/DAPFAM-PAPER-COMPARABILITY.md](docs/healthtech/research/plans/DAPFAM-PAPER-COMPARABILITY.md), [plans/RELATED-WORK-AUDIT.md](docs/healthtech/research/plans/RELATED-WORK-AUDIT.md) | Audit; exact Paper 53 replication not established |
| B53 first-stage substitution (IS2) | [plans/B53-PREDECLARATION.md](docs/healthtech/research/plans/B53-PREDECLARATION.md), [B53-STAGE1-RESULTS.md](docs/writing/is2/results/B53-STAGE1-RESULTS.md) | Stage 1 measured; Stage 2 incomplete |
| P1-DAPFAM (old Paper 1) | [paper1-report/TEST-RESULT-TABLES.md](docs/healthtech/research/paper1-report/TEST-RESULT-TABLES.md), [PAPER1-MANUSCRIPT-DRAFT.md](docs/healthtech/research/PAPER1-MANUSCRIPT-DRAFT.md) | Closed, H1 inconclusive; test exposed |
| P1-BridgeRet manifests and DEV baselines | [paper1-bridgeret/](docs/healthtech/research/paper1-bridgeret/) (`manifest-v2/`, `dev-results/`, `MORNING-REPORT-20261119.md`) | Frozen manifest; DEV descriptive |
| P1 fine-tuning grid | [ft-grid30k/sstar-grid30k.md](docs/healthtech/research/paper1-bridgeret/ft-grid30k/sstar-grid30k.md), [P1-RETHINK-20261120.md](docs/healthtech/research/paper1-bridgeret/P1-RETHINK-20261120.md) | All configs below zero-shot; parked |
| AM-7 missing-reference study | [am7/AM-7-MISSING-REFERENCE.md](docs/healthtech/research/paper1-bridgeret/am7/AM-7-MISSING-REFERENCE.md), [am7/AM-7.1.md](docs/healthtech/research/paper1-bridgeret/am7/AM-7.1.md), [am7/stage2a/](docs/healthtech/research/paper1-bridgeret/am7/stage2a/) | Stage 2a done; owner gate failed; parked |
| DAPFAM acquisition pre-checks | [paper2-precheck/README.md](docs/healthtech/research/paper2-precheck/README.md) | All NO_GO; do not repeat |
| Audit convention and run records | [docs/healthtech/audits/README.md](docs/healthtech/audits/README.md) | Historical receipts; tests read some of them |
| Literature | [literature-review/](literature-review/README.md) | Curated, not a systematic review |

## 4. Writing

| Track | Location | Rule |
|---|---|---|
| The one paper (G07) | `docs/writing/journal/` | Paper 86 banned; arXiv:2605.24297 not used |
| IS2 | [docs/writing/is2/](docs/writing/is2/) | Paper 86 allowed here only |
