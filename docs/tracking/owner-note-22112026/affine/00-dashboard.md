# Patent-to-Pilot — Program dashboard

Tracker projection of the live registry in the repository (`docs/tracking/owner-note-22112026/goal_registry.json`). Phases advance by verified outcomes, not dates.

## Readiness

- **method_evidence**: NOT_YET_DEMONSTRATED
- **product_readiness**: CORE_VERIFIED_PLUS_SYNTHETIC_TRACE_SLICE
- **publication_readiness**: DRAFT_WITH_NOT_RUN_RESULTS

## Milestones

- **OFFLINE_READY**: COMPLETE
- **AFFINE_READY**: BLOCKED
- **PAID_RESEARCH_READY**: COMPLETE
- **METHOD_WIN_SUPPORTED**: NOT_STARTED
- **PRODUCT_RELEASE_READY**: NOT_STARTED
- **PUBLICATION_READY**: NOT_STARTED

## Task counts

- ⛔ BLOCKED: 2
- ✅ COMPLETE: 14
- 🔄 IN_PROGRESS: 1
- ⏳ NOT_STARTED: 16
- 🟡 PARTIAL: 2

## Phases

| Phase | Name | Status | Tasks done |
|---|---|---|---|
| P0 | Control, setup and execution readiness | IN_PROGRESS | 5/7 |
| P1 | Reproducible model-panel and A3 experiment | IN_PROGRESS | 3/6 |
| P2 | Constructive structural candidate acquisition | IN_PROGRESS | 2/7 |
| P3 | Thai transfer and structural scope evaluation | IN_PROGRESS | 1/5 |
| P4 | Integrated product usability and explainability | IN_PROGRESS | 2/5 |
| P5 | Manuscript, artifact release and IS2 readiness | IN_PROGRESS | 1/5 |

## Needs attention

- **P0-T02** Install or update AFFiNE from the verified repository path: Owner must complete first-run admin setup at http://127.0.0.1:3010 (agent does not create accounts or enter passwords)
- **P0-T03** Create live tracking copies and mirror phases into AFFiNE: No supported automated write path to AFFiNE (web sync broken, MCP read-only); repo PHASE_BOARD.md is tracker of record
- **P0-T04** Prepare prospective A3r1 protocol and no-call provider plan: E1R approval; Typhoon key/quota (TYPHOON_API_KEY) or declare deferred
- **P1-T04** Execute the declared four-model DEV pilot and spending decision: dr-train unreachable: pilot routes/evaluation/decision pending (generation complete, USD 0.785 committed)
- **P2-T02** Establish complete-content and stronger simple controls: First full launch OOM'd dr-train (125 GB used; our 32 forked tokenizer workers); host unreachable since ~07:00. Fix is local (workers get own chunks, gc.freeze, 16 workers, 24 GiB watchdog, serialized CPU stages). On recovery: kill our PIDs 1536690/1546555 + workers first; relaunch only after owner OK
