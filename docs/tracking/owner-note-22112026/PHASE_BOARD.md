# Phase board (live)

Rendered from `goal_registry.json` at 2026-11-23T06:01:09+07:00. Do not edit by hand; use `python scripts/tracking/ptp_tracker.py set ...`. Status and research outcome are separate fields.

## Readiness

| Field | Value |
|---|---|
| method_evidence | NOT_YET_DEMONSTRATED |
| product_readiness | CORE_VERIFIED_PLUS_SYNTHETIC_TRACE_SLICE |
| publication_readiness | DRAFT_WITH_NOT_RUN_RESULTS |

## Milestones

| Milestone | Status | Evidence |
|---|---|---|
| OFFLINE_READY | COMPLETE | docs/tracking/owner-note-22112026/receipts/P0-T07_readiness.json |
| AFFINE_READY | BLOCKED | docs/tracking/owner-note-22112026/receipts/P0-T02_affine_setup.md |
| PAID_RESEARCH_READY | COMPLETE | docs/tracking/owner-note-22112026/receipts/P1-T03_freeze_receipt.json |
| METHOD_WIN_SUPPORTED | NOT_STARTED |  |
| PRODUCT_RELEASE_READY | NOT_STARTED |  |
| PUBLICATION_READY | NOT_STARTED |  |

## P0 — Control, setup and execution readiness

Phase status: **IN_PROGRESS**

| Task | Title | Status | Outcome | Evidence | Next | Blocker | AFFiNE |
|---|---|---|---|---|---|---|---|
| P0-T01 | Reconcile checkout, historical results and active authority | ✅ COMPLETE | ENGINEERING_VERIFIED | docs/tracking/owner-note-22112026/receipts/P0-T01_state_reconciliation.md; docs/tracking/owner-note-22112026/receipts/P0-T01_authority_snapshot.json | P0-T02; P0-T04; P0-T05; P0-T06 | — | NOT_SYNCED |
| P0-T02 | Install or update AFFiNE from the verified repository path | 🟡 PARTIAL | NOT_RUN | docs/tracking/owner-note-22112026/receipts/P0-T02_affine_setup.md | P0-T03 | Owner must complete first-run admin setup at http://127.0.0.1:3010 (agent does not create accounts or enter passwords) | NOT_SYNCED |
| P0-T03 | Create live tracking copies and mirror phases into AFFiNE | 🟡 PARTIAL | NOT_RUN | docs/tracking/owner-note-22112026/goal_registry.json; docs/tracking/owner-note-22112026/PHASE_BOARD.md | P0-T07 | No supported automated write path to AFFiNE (web sync broken, MCP read-only); repo PHASE_BOARD.md is tracker of record | NOT_SYNCED |
| P0-T04 | Prepare prospective A3r1 protocol and no-call provider plan | ✅ COMPLETE | NOT_RUN | docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3R1-PROPOSED.md; docs/tracking/owner-note-22112026/receipts/P0-T04_proposed_protocol.md; docs/tracking/owner-note-22112026/receipts/P0-T04_provider_readiness.json | P0-T07; P1-T01 | — | NOT_SYNCED |
| P0-T05 | Implement and verify shared budget reservation accounting | ✅ COMPLETE | ENGINEERING_VERIFIED | docs/tracking/owner-note-22112026/receipts/P0-T05_ledger_verification.md; docs/tracking/owner-note-22112026/receipts/P0-T05_budget_forecast.json; src/patent_to_pilot/budget/ledger.py; tests/test_budget_ledger.py; tests/test_g03_a3_caller_budget.py | P0-T07; P1-T01 | — | NOT_SYNCED |
| P0-T06 | Implement a source-bound synthetic search-and-trace slice | ✅ COMPLETE | ENGINEERING_VERIFIED | docs/tracking/owner-note-22112026/receipts/P0-T06_synthetic_trace.json; docs/tracking/owner-note-22112026/receipts/P0-T06_trace_verification.md; src/patent_to_pilot/workbench/trace_slice.py; tests/test_p0_t06_trace_slice.py | P0-T07; P2-T01; P2-T03; P3-T01; P4-T01; P4-T03 | — | NOT_SYNCED |
| P0-T07 | Close free preparation and publish separate readiness milestones | ✅ COMPLETE | ENGINEERING_VERIFIED | docs/tracking/owner-note-22112026/receipts/P0-T07_readiness.json | P2-T01; P2-T03; P4-T01; P1-T01 after E1R+keys | — | NOT_SYNCED |

## P1 — Reproducible model-panel and A3 experiment

Phase status: **IN_PROGRESS**

| Task | Title | Status | Outcome | Evidence | Next | Blocker | AFFiNE |
|---|---|---|---|---|---|---|---|
| P1-T01 | Resolve paid execution prerequisites and exact scope | ✅ COMPLETE | ENGINEERING_VERIFIED | docs/tracking/owner-note-22112026/receipts/P1-T03_freeze_receipt.json | P1-T02 | — | NOT_SYNCED |
| P1-T02 | Calibrate the complete output contract on TRAIN only | ✅ COMPLETE | ENGINEERING_VERIFIED | docs/tracking/owner-note-22112026/receipts/P1-T02_format_cost_receipt.md; docs/tracking/owner-note-22112026/receipts/P1-T02_calibration_manifest.json | P1-T03 | — | NOT_SYNCED |
| P1-T03 | Freeze A3r1 eligibility, configuration and pilot manifest | ✅ COMPLETE | ENGINEERING_VERIFIED | docs/tracking/owner-note-22112026/receipts/P1-T03_freeze_receipt.json; docs/healthtech/research/g03-dev/a3r1/a3r1-caller-config.json | P1-T04 | — | NOT_SYNCED |
| P1-T04 | Execute the declared four-model DEV pilot and spending decision | ⏳ NOT_STARTED | NOT_RUN | — | P1-T05 on GO; P1-T06 on STOP | — | NOT_SYNCED |
| P1-T05 | Run one selected Stage B only after GO | ⏳ NOT_STARTED | NOT_RUN | — | P1-T06 | — | NOT_SYNCED |
| P1-T06 | Close A3 evidence and hand off the constructive ladder | ⏳ NOT_STARTED | NOT_RUN | — | P2-T02; P2-T04; P5-T02 when evidence exists | — | NOT_SYNCED |

## P2 — Constructive structural candidate acquisition

Phase status: **IN_PROGRESS**

| Task | Title | Status | Outcome | Evidence | Next | Blocker | AFFiNE |
|---|---|---|---|---|---|---|---|
| P2-T01 | Audit eligible content and available structural evidence | ✅ COMPLETE | ENGINEERING_VERIFIED | docs/tracking/owner-note-22112026/receipts/P2-T01_content_coverage_audit.md | P2-T02 (claims-complete rebuild vs equal-content control; Arctic/BM25 pilot first) | — | NOT_SYNCED |
| P2-T02 | Establish complete-content and stronger simple controls | 🔄 IN_PROGRESS | NOT_RUN | — | P2-T04 | — | NOT_SYNCED |
| P2-T03 | Implement one bounded source-relation search action | ✅ COMPLETE | ENGINEERING_VERIFIED | docs/tracking/owner-note-22112026/receipts/P2-T03_mechanism_spec.md; docs/tracking/owner-note-22112026/receipts/P2-T03_mechanism_verification.md; src/patent_to_pilot/workbench/relation_search.py; tests/test_p2_t03_relation_search.py | P2-T04 (after P2-T02 controls); P4-T03 | — | NOT_SYNCED |
| P2-T04 | Screen the bounded mechanism against close matched controls | ⏳ NOT_STARTED | NOT_RUN | — | P2-T05 if viable | — | NOT_SYNCED |
| P2-T05 | Freeze the selected method, primary endpoint and next evaluation | ⏳ NOT_STARTED | NOT_RUN | — | P2-T06 | — | NOT_SYNCED |
| P2-T06 | Measure the primary matched retrieval comparison | ⏳ NOT_STARTED | NOT_RUN | — | P2-T07; P3-T03 | — | NOT_SYNCED |
| P2-T07 | Attribute candidate acquisition and decide research readiness | ⏳ NOT_STARTED | NOT_RUN | — | P3-T03; P4 integration; P5-T02 | — | NOT_SYNCED |

## P3 — Thai transfer and structural scope evaluation

Phase status: **IN_PROGRESS**

| Task | Title | Status | Outcome | Evidence | Next | Blocker | AFFiNE |
|---|---|---|---|---|---|---|---|
| P3-T01 | Prepare Thai dataset/profile rights and exposure adapters | ✅ COMPLETE | ENGINEERING_VERIFIED | docs/tracking/owner-note-22112026/receipts/P3-T01_thai_data_contract.md; src/patent_to_pilot/workbench/datasets/thai_contract.py; tests/test_p3_t01_thai_contract.py | P3-T02 (needs per-item download approvals / packet rights) | — | NOT_SYNCED |
| P3-T02 | Build grouped source packets and independent judgments | ⏳ NOT_STARTED | NOT_RUN | — | P3-T04 | — | NOT_SYNCED |
| P3-T03 | Run separate Thai text-transfer comparisons | ⏳ NOT_STARTED | NOT_RUN | — | P3-T05 | — | NOT_SYNCED |
| P3-T04 | Evaluate structural scope and OCR end to end | ⏳ NOT_STARTED | NOT_RUN | — | P3-T05; P4-T03 | — | NOT_SYNCED |
| P3-T05 | Freeze supported Thai scope and transfer claims | ⏳ NOT_STARTED | NOT_RUN | — | P4-T05; P5-T02 | — | NOT_SYNCED |

## P4 — Integrated product usability and explainability

Phase status: **IN_PROGRESS**

| Task | Title | Status | Outcome | Evidence | Next | Blocker | AFFiNE |
|---|---|---|---|---|---|---|---|
| P4-T01 | Extend the existing Search, Compare and Inspect workflow | 🔄 IN_PROGRESS | NOT_RUN | — | P4-T02; P4-T03 | — | NOT_SYNCED |
| P4-T02 | Make local, API and self-hosted modes clear and usable | ⏳ NOT_STARTED | NOT_RUN | — | P4-T05 | — | NOT_SYNCED |
| P4-T03 | Make source, structural scope and search provenance inspectable | ⏳ NOT_STARTED | NOT_RUN | — | P4-T04; P4-T05 | — | NOT_SYNCED |
| P4-T04 | Verify selective revision against full recomputation | ⏳ NOT_STARTED | NOT_RUN | — | P4-T05 | — | NOT_SYNCED |
| P4-T05 | Observe clean-install and user-task success | ⏳ NOT_STARTED | NOT_RUN | — | P5-T03; P5-T04 | — | NOT_SYNCED |

## P5 — Manuscript, artifact release and IS2 readiness

Phase status: **IN_PROGRESS**

| Task | Title | Status | Outcome | Evidence | Next | Blocker | AFFiNE |
|---|---|---|---|---|---|---|---|
| P5-T01 | Draft the single manuscript and three linked contribution tests | ✅ COMPLETE | NOT_RUN | docs/writing/journal/MANUSCRIPT-DRAFT-v1.md; docs/tracking/owner-note-22112026/receipts/P5-T01_manuscript_draft.md; docs/tracking/owner-note-22112026/receipts/P5-T01_claim_evidence_map.csv | P5-T02 when results exist | — | NOT_SYNCED |
| P5-T02 | Synthesize actual scoreboards, ablations and limits | ⏳ NOT_STARTED | NOT_RUN | — | P5-T03; P5-T04 if claims are supported | — | NOT_SYNCED |
| P5-T03 | Package the shared engine and reproducible licensed artifacts | ⏳ NOT_STARTED | NOT_RUN | — | P5-T04; P5-T05 | — | NOT_SYNCED |
| P5-T04 | Verify IS2 narrative, demonstration and claim boundaries | ⏳ NOT_STARTED | NOT_RUN | — | P5-T05 | — | NOT_SYNCED |
| P5-T05 | Close deliverables and record actual release/submission state | ⏳ NOT_STARTED | NOT_RUN | — | Complete if all declared evidence holds; otherwise named unresolved task | — | NOT_SYNCED |
