# P4 — Integrated product usability and explainability

Phase status: **IN_PROGRESS**

**Entry rule:** Start each task only when its listed task dependencies and execution authority hold. Entry requirements describe the first available work; AFFiNE and full P0 completion do not gate research.

**Exit rule:** Required tasks have verified evidence or an explicit permitted skip; material blocked work prevents COMPLETE. Research outcome is reported separately.

| Task | Title | Status | Outcome | Next |
|---|---|---|---|---|
| P4-T01 | Extend the existing Search, Compare and Inspect workflow | 🔄 IN_PROGRESS | NOT_RUN | P4-T02; P4-T03 |
| P4-T02 | Make local, API and self-hosted modes clear and usable | ⏳ NOT_STARTED | NOT_RUN | P4-T05 |
| P4-T03 | Make source, structural scope and search provenance inspectable | ⏳ NOT_STARTED | NOT_RUN | P4-T04; P4-T05 |
| P4-T04 | Verify selective revision against full recomputation | ⏳ NOT_STARTED | NOT_RUN | P4-T05 |
| P4-T05 | Observe clean-install and user-task success | ⏳ NOT_STARTED | NOT_RUN | P5-T03; P5-T04 |

## P4-T01 — Extend the existing Search, Compare and Inspect workflow

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T06
- **Acceptance evidence:** Reuse existing Workbench/store; accept explicit arbitrary requirements; actual local search and baseline comparison work without paid inference.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P4-T02; P4-T03
- **Blocker:** —
- **Notes:** [2026-11-22] agent started

## P4-T02 — Make local, API and self-hosted modes clear and usable

- **Status:** see the table above (single place to update)
- **Depends on:** P4-T01; P0-T04
- **Acceptance evidence:** Show active execution mode, exact model and missing capability; configure credentials securely once; missing optional endpoint does not block local search.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P4-T05
- **Blocker:** —

## P4-T03 — Make source, structural scope and search provenance inspectable

- **Status:** see the table above (single place to update)
- **Depends on:** P4-T01; P2-T03
- **Acceptance evidence:** Resolve original page/text, scope qualifiers and actual new-candidate action; reject hypothesis-as-evidence; show source-region absence honestly.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P4-T04; P4-T05
- **Blocker:** —

## P4-T04 — Verify selective revision against full recomputation

- **Status:** see the table above (single place to update)
- **Depends on:** P4-T03
- **Acceptance evidence:** Change source text, scope edges and corpus membership; compare affected evidence with a full rerun; measure work/cost before claiming savings.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P4-T05
- **Blocker:** —

## P4-T05 — Observe clean-install and user-task success

- **Status:** see the table above (single place to update)
- **Depends on:** P4-T01; P4-T02; P4-T03; P4-T04
- **Acceptance evidence:** Verify supported Windows flow, restart persistence, actual source inspection and revision errors; observe predefined tasks/time/corrections; identify untested environments clearly.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P5-T03; P5-T04
- **Blocker:** —
