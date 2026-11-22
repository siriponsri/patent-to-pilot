# P0 — Control, setup and execution readiness

Phase status: **IN_PROGRESS**

**Entry rule:** Start each task only when its listed task dependencies and execution authority hold. Entry requirements describe the first available work; AFFiNE and full P0 completion do not gate research.

**Exit rule:** Required tasks have verified evidence or an explicit permitted skip; material blocked work prevents COMPLETE. Research outcome is reported separately.

| Task | Title | Status | Outcome | Next |
|---|---|---|---|---|
| P0-T01 | Reconcile checkout, historical results and active authority | ✅ COMPLETE | ENGINEERING_VERIFIED | P0-T02; P0-T04; P0-T05; P0-T06 |
| P0-T02 | Install or update AFFiNE from the verified repository path | 🟡 PARTIAL | NOT_RUN | P0-T03 |
| P0-T03 | Create live tracking copies and mirror phases into AFFiNE | 🟡 PARTIAL | NOT_RUN | P0-T07 |
| P0-T04 | Prepare prospective A3r1 protocol and no-call provider plan | ✅ COMPLETE | NOT_RUN | P0-T07; P1-T01 |
| P0-T05 | Implement and verify shared budget reservation accounting | 🔄 IN_PROGRESS | NOT_RUN | P0-T07; P1-T01 |
| P0-T06 | Implement a source-bound synthetic search-and-trace slice | 🔄 IN_PROGRESS | NOT_RUN | P0-T07; P2-T01; P2-T03; P3-T01; P4-T01; P4-T03 |
| P0-T07 | Close free preparation and publish separate readiness milestones | ⏳ NOT_STARTED | NOT_RUN | P1-T01 if eligible; free P2/P4/P5 tasks by dependency |

## P0-T01 — Reconcile checkout, historical results and active authority

- **Status:** see the table above (single place to update)
- **Depends on:** —
- **Acceptance evidence:** Record actual HEAD, current instructions, legacy G01/G02 evidence, A3 effectiveness exposure and exact budget/resource scope; preserve history.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P0-T01_state_reconciliation.md; docs/tracking/owner-note-22112026/receipts/P0-T01_authority_snapshot.json
- **Check:** PASS
- **Next:** P0-T02; P0-T04; P0-T05; P0-T06
- **Blocker:** —
- **Notes:** [2026-11-22] HEAD ad7982d2 = pin + 1 tracker commit; no A3 effectiveness exposure; E1 active, E1R pending

## P0-T02 — Install or update AFFiNE from the verified repository path

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T01
- **Acceptance evidence:** Follow product/AFFINE_PHASE_TRACKING.md; preserve existing data; record version, health, access and backup/restore evidence; no pretend installation.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P0-T02_affine_setup.md
- **Check:** server healthy; admin setup pending
- **Next:** P0-T03
- **Blocker:** Owner must complete first-run admin setup at http://127.0.0.1:3010 (agent does not create accounts or enter passwords)
- **Notes:** [2026-11-22] desktop 0.27.4 installed earlier; evaluating self-host route | [2026-11-22] upstream 0.27.4 self-host pinned by digest; fork aisle9@36bc78bf is source reference only

## P0-T03 — Create live tracking copies and mirror phases into AFFiNE

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T01
- **Acceptance evidence:** Copy seeds into docs/tracking/owner-note-22112026; preserve task IDs; each AFFiNE item links evidence and next action. If AFFiNE is unavailable, local tracking is ready but synchronization remains BLOCKED.
- **Evidence:** docs/tracking/owner-note-22112026/goal_registry.json; docs/tracking/owner-note-22112026/PHASE_BOARD.md
- **Check:** local tracker live (35 tasks); AFFiNE mirror pending
- **Next:** P0-T07
- **Blocker:** Workspace 15d6fa22 created on server, but the in-app browser client does not push docs (server snapshots=0, updates=0; websocket and SharedWorker work in probes). Need owner check in own browser/desktop or permission to drive Claude in Chrome
- **Notes:** [2026-11-22] live registry initialised from seed (hashes recorded); scripts/tracking/ptp_tracker.py renders CSV, board and affine/*.md | [2026-11-22] server workspace created via UI; local test doc not synced

## P0-T04 — Prepare prospective A3r1 protocol and no-call provider plan

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T01
- **Acceptance evidence:** Preserve A3r0; name exact four-model/three-lineage panel, common proposed 800-token cap and same 32 TRAIN cases per model; record prices/identity/access without model calls.
- **Evidence:** docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3R1-PROPOSED.md; docs/tracking/owner-note-22112026/receipts/P0-T04_proposed_protocol.md; docs/tracking/owner-note-22112026/receipts/P0-T04_provider_readiness.json
- **Check:** PASS (no-call catalogue reads only; USD 0)
- **Next:** P0-T07; P1-T01
- **Blocker:** —
- **Notes:** [2026-11-22] parallel agent started | [2026-11-22] A3r1 not affordable under E1 (no model Stage-B-eligible at USD 6 stop); fits E1R; OpenRouter balance ~8.365 needs top-up before Stage B; Typhoon not on OpenRouter, price unpublished

## P0-T05 — Implement and verify shared budget reservation accounting

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T01
- **Acceptance evidence:** Use fake provider responses to verify atomic reservations, retries, request caps, restart persistence and unknown-cost pauses; reconcile historical smoke and Workbench spend.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P0-T07; P1-T01
- **Blocker:** —
- **Notes:** [2026-11-22] parallel agent started

## P0-T06 — Implement a source-bound synthetic search-and-trace slice

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T01
- **Acceptance evidence:** Run actual local lexical search on an authored synthetic packet; resolve original bytes, spans and annex binding; record real before/after candidate membership; label synthetic data.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P0-T07; P2-T01; P2-T03; P3-T01; P4-T01; P4-T03
- **Blocker:** —
- **Notes:** [2026-11-22] parallel agent started

## P0-T07 — Close free preparation and publish separate readiness milestones

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T01; P0-T04; P0-T05; P0-T06
- **Acceptance evidence:** Run focused checks and required repository gate; report known SACR/PDF-test limitations; set OFFLINE_READY, AFFINE_READY and PAID_RESEARCH_READY separately from evidence. Unfinished material tasks stay BLOCKED/PARTIAL. Completing this readiness receipt does not complete blocked P0 tasks or authorize paid execution.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P1-T01 if eligible; free P2/P4/P5 tasks by dependency
- **Blocker:** —
