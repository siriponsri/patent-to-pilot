# P5 — Manuscript, artifact release and IS2 readiness

Phase status: **IN_PROGRESS**

**Entry rule:** Start each task only when its listed task dependencies and execution authority hold. Entry requirements describe the first available work; AFFiNE and full P0 completion do not gate research.

**Exit rule:** Required tasks have verified evidence or an explicit permitted skip; material blocked work prevents COMPLETE. Research outcome is reported separately.

| Task | Title | Status | Outcome | Next |
|---|---|---|---|---|
| P5-T01 | Draft the single manuscript and three linked contribution tests | ✅ COMPLETE | NOT_RUN | P5-T02 when results exist |
| P5-T02 | Synthesize actual scoreboards, ablations and limits | ⏳ NOT_STARTED | NOT_RUN | P5-T03; P5-T04 if claims are supported |
| P5-T03 | Package the shared engine and reproducible licensed artifacts | ⏳ NOT_STARTED | NOT_RUN | P5-T04; P5-T05 |
| P5-T04 | Verify IS2 narrative, demonstration and claim boundaries | ⏳ NOT_STARTED | NOT_RUN | P5-T05 |
| P5-T05 | Close deliverables and record actual release/submission state | ⏳ NOT_STARTED | NOT_RUN | Complete if all declared evidence holds; otherwise named unresolved task |

## P5-T01 — Draft the single manuscript and three linked contribution tests

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T01; P0-T04
- **Acceptance evidence:** Write background/method/design now; preserve Paper 53 identity/DOI uncertainty, Paper 86 IS2-only boundary and direct prior art; result cells remain NOT_RUN.
- **Evidence:** docs/writing/journal/MANUSCRIPT-DRAFT-v1.md; docs/tracking/owner-note-22112026/receipts/P5-T01_manuscript_draft.md; docs/tracking/owner-note-22112026/receipts/P5-T01_claim_evidence_map.csv
- **Check:** guard test tests/test_org_adaptive_terminology.py PASS; all new result cells NOT_RUN
- **Next:** P5-T02 when results exist
- **Blocker:** —
- **Notes:** [2026-11-22] writing agent started (background/method; results NOT_RUN) | [2026-11-22] writing corrections W1-W6 applied (docs/maintenance/WRITING-CORRECTIONS-20261122.md); IS2 generated docx/py still print 37.1% until next rebuild

## P5-T02 — Synthesize actual scoreboards, ablations and limits

- **Status:** see the table above (single place to update)
- **Depends on:** P5-T01
- **Acceptance evidence:** Populate versioned actual results only; separate P1, DAPFAM and Thai; require acquisition evidence for the positive method claim and real evidence for each contribution.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P5-T03; P5-T04 if claims are supported
- **Blocker:** —

## P5-T03 — Package the shared engine and reproducible licensed artifacts

- **Status:** see the table above (single place to update)
- **Depends on:** P4-T05; P5-T01
- **Acceptance evidence:** Bundle verified code/config/demo with exact versions and tests; keep restricted corpora/weights/keys outside release; label research status independently from product readiness.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P5-T04; P5-T05
- **Blocker:** —

## P5-T04 — Verify IS2 narrative, demonstration and claim boundaries

- **Status:** see the table above (single place to update)
- **Depends on:** P5-T01; P4-T05
- **Acceptance evidence:** Demonstrate actual evidence discovery or clearly labeled synthetic workflow, source inspection and revision; show aggregate scores beside examples; distinguish submission/acceptance/adoption states.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P5-T05
- **Blocker:** —

## P5-T05 — Close deliverables and record actual release/submission state

- **Status:** see the table above (single place to update)
- **Depends on:** P5-T02; P5-T03; P5-T04
- **Acceptance evidence:** Record research, product and publication readiness separately; attach artifact URIs and actual release/submission evidence; close only fulfilled goals.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** Complete if all declared evidence holds; otherwise named unresolved task
- **Blocker:** —
