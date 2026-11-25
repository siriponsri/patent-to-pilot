# Index: plan and evidence

Start with the [master plan and live S0–S5 board](docs/evidence-scope/MASTER-PLAN.md), the [prospective freeze](docs/evidence-scope/FREEZE.md) and [HANDOFF](HANDOFF.md). The phase sheets contain tasks and dependencies for GPT 6.2 high. The earlier [P0–P5 board](docs/tracking/owner-note-22112026/PHASE_BOARD.md) retains historical task state and is rendered by `scripts/tracking/ptp_tracker.py`.

S1 delivered the [controlled data and scorer](docs/evidence-scope/receipts/S1-20261125.md). S2 delivered the [local alpha](docs/evidence-scope/receipts/S2-workbench.md) and [public-source inventory](docs/evidence-scope/receipts/S2-sources.md). S3 closed NEGATIVE on controlled Thai DEV with uninformative English transfer. See the [preregistration](docs/healthtech/audits/S3-20261125/PREREGISTRATION.md), [machine lock](docs/healthtech/audits/S3-20261125/freeze.json), [execution receipt](docs/healthtech/audits/S3-20261125/RESULTS.md), [machine result](docs/healthtech/audits/S3-20261125/results.json) and [continuity matrix](docs/healthtech/audits/S3-20261125/BRIDGE.md).

Option A closed NULL in the Thai controlled comparison, with diagnostic-only evidence for the architecture. See the [research protocol](docs/evidence-scope/alternative-evidence/PROTOCOL.md), [prospective v2 lock](docs/evidence-scope/alternative-evidence/freeze.json), [closest-work audit](docs/evidence-scope/05-alternative-evidence-literature.md), [fresh packet manifest](docs/evidence-scope/alternative-evidence/packet/manifest.json), [development fixture traces](docs/evidence-scope/alternative-evidence/fixture-checks.json), and [sealed original results and audit](docs/evidence-scope/alternative-evidence/RESULTS.md). [S4 product validation](docs/evidence-scope/04-product-release.md) separately closed for the Windows alpha, with [integrated verification](docs/evidence-scope/receipts/S4-integrated-verification.md).

## 1. Owner inputs (owner-local, untracked, read-only)

| Package | Use |
|---|---|
| `docs/owner/owner-note-22112026/` (**P0–P5 baseline**) | `00_START_HERE.md`; `01_OWNER_DIRECTION_AND_DECISIONS.md` (N01–N12); `02_GOALS_AND_PHASES.md` (P0–P5, 35 tasks); `03_BUDGET_AND_AUTONOMY.md` (E1 in force, E1R pending); `04_ARCHITECTURE.md`; `research/` (A3 amendment, method, score contract, datasets, paper/IS2 blueprint); `product/` (UX, engine integration, AFFiNE tracking); `spec/` (document IR, evidence trace schema) |
| `docs/owner/owner-note-21112026/` (earlier) | Program PTP-2026-11-21, G01–G08; still the source of the G01/G02 acceptance criteria |

## 2. Inherited phases and their evidence

| Phase | Goal | Live status | Key evidence |
|---|---|---|---|
| P0 | Control, setup and execution readiness | See board | `docs/tracking/owner-note-22112026/receipts/P0-*` |
| P1 | Reproducible model-panel and A3 experiment | See board | [A3r0 protocol](docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3-20261122.md), [A3r1 proposed](docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3R1-PROPOSED.md) |
| P2 | Constructive structural candidate acquisition | P2-T04 COMPLETE, NO_GAIN | [Complete-content controls](docs/tracking/owner-note-22112026/receipts/P2-T02_coverage_control_results.md), [D19 results](docs/tracking/owner-note-22112026/receipts/P2-T02_D19_followup_results.md), [frozen matched screen](docs/tracking/owner-note-22112026/receipts/P2-T04_frozen_protocol.md), [matched results](docs/tracking/owner-note-22112026/receipts/P2-T04_results.md) |
| P3 | Thai transfer and structural scope evaluation | See board | — |
| P4 | Integrated product usability and explainability | See board | Workbench (G01/G02 foundations) |
| P5 | Manuscript, artifact release and IS2 readiness | See board | [MANUSCRIPT-DRAFT-v1.md](docs/writing/journal/MANUSCRIPT-DRAFT-v1.md), [IS2 outline v3](docs/writing/is2/IS2-OUTLINE-v3-20261122.md) |

**Foundations (complete, preserved):**
- G01 local vertical slice: [artifacts/owner-program/PTP-2026-11-21/G01/](artifacts/owner-program/PTP-2026-11-21/G01/).
- G02 providers, ingestion and datasets: [G02/](artifacts/owner-program/PTP-2026-11-21/G02/).
- The 22 Nov add-ons (PDF text layer, OpenRouter templates) are recorded in HANDOFF.

## 3. Evidence the paper may use (each row keeps its original scope)

| Topic | Location | Status |
|---|---|---|
| G03 DEV (P1 Challenge-1M) | [g03-dev/](docs/healthtech/research/g03-dev/): protocol v1, amendments 1–3, decision memo, results JSON | v1, A1, A2 PARKED; A3r0 frozen, format smoke only ([spend](docs/healthtech/research/g03-dev/g03-dev-a3-spend.json)); A3r1 closed, exploratory CONTINUE |
| B53 first-stage substitution (IS2) | [B53-STAGE1-RESULTS.md](docs/writing/is2/results/B53-STAGE1-RESULTS.md), [B53-STAGE2-RESULTS.md](docs/writing/is2/results/B53-STAGE2-RESULTS.md) | Stage 1 and 2 measured; no instruction contrast significant |
| B53.0 DAPFAM pipeline check | [b53-0/B53-0-RESULTS.md](docs/healthtech/research/b53-0/B53-0-RESULTS.md) | 11 of 12 cells match the DAPFAM paper |
| PatEmbed–DAPFAM overlap (D3) | [PATENTEB-OVERLAP-AUDIT-20261122.md](docs/healthtech/research/b53-0/PATENTEB-OVERLAP-AUDIT-20261122.md) | Train split unreleased; shared family pool; training overlap unmeasured |
| Paper 53 / DAPFAM comparability | [plans/DAPFAM-PAPER-COMPARABILITY.md](docs/healthtech/research/plans/DAPFAM-PAPER-COMPARABILITY.md), [plans/RELATED-WORK-AUDIT.md](docs/healthtech/research/plans/RELATED-WORK-AUDIT.md) | Audit; exact replication not established; [original-source denominator verified](docs/evidence-scope/00-organization.md#original-source-corrections) |
| P1-DAPFAM (old Paper 1) | [paper1-report/TEST-RESULT-TABLES.md](docs/healthtech/research/paper1-report/TEST-RESULT-TABLES.md) | Closed, H1 inconclusive; test exposed |
| P1-BridgeRet manifests, DEV baselines, FT grid | [paper1-bridgeret/](docs/healthtech/research/paper1-bridgeret/) | Frozen manifest; FT below zero-shot; parked |
| AM-7 missing-reference study | [am7/](docs/healthtech/research/paper1-bridgeret/am7/) | Stage 2a done; owner gate failed; parked |
| DAPFAM acquisition pre-checks | [paper2-precheck/README.md](docs/healthtech/research/paper2-precheck/README.md) | All NO_GO; do not repeat |
| Writing corrections | [WRITING-CORRECTIONS-20261122.md](docs/maintenance/WRITING-CORRECTIONS-20261122.md) | W1–W6 applied 22 Nov |
| dr-train pull/prune | [20261121 cleanup](artifacts/maintenance/20261121-dr-train-cleanup/SUMMARY.md), [20261122 B53](artifacts/maintenance/20261122-b53-pull/SUMMARY.md), [20261122 G03](artifacts/maintenance/20261122-g03-pull/SUMMARY.md); [runbook](docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md) | Done; large derived files compressed, not deleted |
| Audit convention and run records | [docs/healthtech/audits/README.md](docs/healthtech/audits/README.md) | Historical receipts |
| Literature | [literature-review/](literature-review/README.md) | Curated, not a systematic review |

## 4. Writing

| Track | Location | Rule |
|---|---|---|
| The one paper (P5) | `docs/writing/journal/` | Paper 86 banned; arXiv:2605.24297 not used |
| IS2 | [docs/writing/is2/](docs/writing/is2/) | Paper 86 allowed here only (D10) |
