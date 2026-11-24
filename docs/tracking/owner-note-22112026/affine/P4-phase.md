# P4 — Integrated product usability and explainability

Phase status: **IN_PROGRESS**

**Entry rule:** Start each task only when its listed task dependencies and execution authority hold. Entry requirements describe the first available work; AFFiNE and full P0 completion do not gate research.

**Exit rule:** Required tasks have verified evidence or an explicit permitted skip; material blocked work prevents COMPLETE. Research outcome is reported separately.

| Task | Title | Status | Outcome | Next |
|---|---|---|---|---|
| P4-T01 | Extend the existing Search, Compare and Inspect workflow | ✅ COMPLETE | ENGINEERING_VERIFIED | P4-T02; P4-T03 |
| P4-T02 | Make local, API and self-hosted modes clear and usable | ✅ COMPLETE | NOT_RUN | P4-T05 |
| P4-T03 | Make source, structural scope and search provenance inspectable | ✅ COMPLETE | ENGINEERING_VERIFIED | P4-T04; plan section 8 matched comparison |
| P4-T04 | Verify selective revision against full recomputation | 🟡 PARTIAL | ENGINEERING_VERIFIED | Implement corpus source removal (D3), then verify removal against full recomputation |
| P4-T05 | Observe clean-install and user-task success | ⏳ NOT_STARTED | NOT_RUN | P5-T03; P5-T04 |

## P4-T01 — Extend the existing Search, Compare and Inspect workflow

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T06
- **Acceptance evidence:** Reuse existing Workbench/store; accept explicit arbitrary requirements; actual local search and baseline comparison work without paid inference.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P4-T01_workflow_receipt.md; docs/tracking/owner-note-22112026/receipts/P4-T01a_thai_search_receipt.md; docs/tracking/owner-note-22112026/receipts/P4-T01b_requirement_lifecycle_receipt.md
- **Check:** 9 new tests; workbench suites 119 pass; smoke 15/15; browser check, no console errors
- **Next:** P4-T02; P4-T03
- **Blocker:** —
- **Notes:** [2026-11-22] agent started | [2026-11-23] Search (terms/phrase/literal), arbitrary requirements, Compare baseline vs bounded relation action (labelled ENGINEERING DEMO), Inspect spans + original file + honest page mapping; Thai FTS5 not segmented | [2026-11-23] follow-ups merged: P4-T01a Thai search (PyThaiNLP 5.4.0 newmm-safe, passage_fts_th_v1, auto mode) + P4-T01b Remove/Undo; combined gate = only 8 known SACR failures; smoke 15/15

## P4-T02 — Make local, API and self-hosted modes clear and usable

- **Status:** see the table above (single place to update)
- **Depends on:** P4-T01; P0-T04
- **Acceptance evidence:** Show active execution mode, exact model and missing capability; configure credentials securely once; missing optional endpoint does not block local search.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P4-T02_provider_ux_receipt.md
- **Check:** NOT_CHECKED
- **Next:** P4-T05
- **Blocker:** —
- **Notes:** [2026-11-23] Mode indicator (local/API/self-hosted) with exact model; missing-capability list; name-only credential setup (Windows user env var); local search/compare/inspect verified with all optional endpoints missing; gate 8 SACR only, smoke 15/15

## P4-T03 — Make source, structural scope and search provenance inspectable

- **Status:** see the table above (single place to update)
- **Depends on:** P4-T01; P2-T03
- **Acceptance evidence:** Resolve original page/text, scope qualifiers and actual new-candidate action; reject hypothesis-as-evidence; show source-region absence honestly.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P4-T03_structural_acquisition_receipt.md; src/patent_to_pilot/workbench/acquisition.py; src/patent_to_pilot/workbench/structure.py; tests/test_structural_acquisition.py
- **Check:** 15 new tests; full gate only 8 known SACR failures; smoke 15/15; browser Compare renders, no console errors
- **Next:** P4-T04; plan section 8 matched comparison
- **Blocker:** —
- **Notes:** [2026-11-23] policy ptp-structural-acquisition/2.0.0 (sha 12490901...), acquisition inside assessment path with persisted receipts + scope dependencies; V1 side-by-side now opt-in; no effectiveness measured

## P4-T04 — Verify selective revision against full recomputation

- **Status:** see the table above (single place to update)
- **Depends on:** P4-T03
- **Acceptance evidence:** Change source text, scope edges and corpus membership; compare affected evidence with a full rerun; measure work/cost before claiming savings.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P4-T04_revision_comparison.md
- **Check:** D25 merge 98d6c37a: full suite accepted with exact eight SACR exceptions; smoke 15/15; 11/11 supported fixture matches
- **Next:** Implement corpus source removal (D3), then verify removal against full recomputation
- **Blocker:** —
- **Notes:** [2026-11-23] P4-T01b requirement Remove/Undo lifecycle merged ff35de32 (retire/restore obligations+assessments, stale in-flight commits rejected); revision-vs-full-rerun comparison still to do | [2026-11-23] Selective = full-from-scratch in 10/11 runnable scenarios after fix D1 (scope-dependent reuse); D2 sibling-anchor order dependence open (policy decision); D3 no source-removal operation; work 23 vs 64 obligations re-assessed on small fixtures (not a benchmark) | [2026-11-24] D25 verified and merged. Selective and in-place results match scratch in all 11 supported authored fixtures, including d1.

## P4-T05 — Observe clean-install and user-task success

- **Status:** see the table above (single place to update)
- **Depends on:** P4-T01; P4-T02; P4-T03; P4-T04
- **Acceptance evidence:** Verify supported Windows flow, restart persistence, actual source inspection and revision errors; observe predefined tasks/time/corrections; identify untested environments clearly.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P5-T03; P5-T04
- **Blocker:** —
