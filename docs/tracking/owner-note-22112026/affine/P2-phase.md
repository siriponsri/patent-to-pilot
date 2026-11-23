# P2 — Constructive structural candidate acquisition

Phase status: **IN_PROGRESS**

**Entry rule:** Start each task only when its listed task dependencies and execution authority hold. Entry requirements describe the first available work; AFFiNE and full P0 completion do not gate research.

**Exit rule:** Required tasks have verified evidence or an explicit permitted skip; material blocked work prevents COMPLETE. Research outcome is reported separately.

| Task | Title | Status | Outcome | Next |
|---|---|---|---|---|
| P2-T01 | Audit eligible content and available structural evidence | ✅ COMPLETE | ENGINEERING_VERIFIED | P2-T02 (claims-complete rebuild vs equal-content control; Arctic/BM25 pilot first) |
| P2-T02 | Establish complete-content and stronger simple controls | ⛔ BLOCKED | NOT_RUN | P2-T04 |
| P2-T03 | Implement one bounded source-relation search action | ✅ COMPLETE | ENGINEERING_VERIFIED | P2-T04 (after P2-T02 controls); P4-T03 |
| P2-T04 | Screen the bounded mechanism against close matched controls | ⏳ NOT_STARTED | NOT_RUN | P2-T05 if viable |
| P2-T05 | Freeze the selected method, primary endpoint and next evaluation | ⏳ NOT_STARTED | NOT_RUN | P2-T06 |
| P2-T06 | Measure the primary matched retrieval comparison | ⏳ NOT_STARTED | NOT_RUN | P2-T07; P3-T03 |
| P2-T07 | Attribute candidate acquisition and decide research readiness | ⏳ NOT_STARTED | NOT_RUN | P3-T03; P4 integration; P5-T02 |

## P2-T01 — Audit eligible content and available structural evidence

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T06
- **Acceptance evidence:** Inspect permitted manifests/index configuration for truncation, omitted sections and family aggregation; do not open protected TEST or download a new corpus.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P2-T01_content_coverage_audit.md
- **Check:** read-only audit; no TEST opened; USD 0
- **Next:** P2-T02 (claims-complete rebuild vs equal-content control; Arctic/BM25 pilot first)
- **Blocker:** —
- **Notes:** [2026-11-22] read-only content coverage audit agent started | [2026-11-22] content gap found: index holds title+abstract+first claim only (~12% of claim tokens); 512 cap cuts 7-17% of units; claim dependency 97.8% available; no description/CPC; outputs pulled to _private_artifacts/dr-train-archive/20261122-p2t01

## P2-T02 — Establish complete-content and stronger simple controls

- **Status:** see the table above (single place to update)
- **Depends on:** P2-T01; P0-T05
- **Acceptance evidence:** Compare equal-content flat/structural units and deeper original-query retrieval under shared masks/budgets; record actual results and resource costs.
- **Evidence:** docs/healthtech/research/p2-coverage/P2-T02-RUN-NOTES.md
- **Check:** NOT_CHECKED
- **Next:** P2-T04
- **Blocker:** First full launch OOM'd dr-train (125 GB used; our 32 forked tokenizer workers); host unreachable since ~07:00. Fix is local (workers get own chunks, gc.freeze, 16 workers, 24 GiB watchdog, serialized CPU stages). On recovery: kill our PIDs 1536690/1546555 + workers first; relaunch only after owner OK
- **Notes:** [2026-11-22] protocol frozen at docs/healthtech/research/p2-coverage/P2-T02-COVERAGE-CONTROL-PROTOCOL.md; implementation next | [2026-11-23] C0 gate passed exactly on full P1-DEV before the OOM; no result numbers

## P2-T03 — Implement one bounded source-relation search action

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T06
- **Acceptance evidence:** Preserve exact query requirements; select one unresolved relation; issue one eligible global search; merge and recheck coverage; rerank against original query. Synthetic tests are clearly marked.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P2-T03_mechanism_spec.md; docs/tracking/owner-note-22112026/receipts/P2-T03_mechanism_verification.md; src/patent_to_pilot/workbench/relation_search.py; tests/test_p2_t03_relation_search.py
- **Check:** 19 synthetic tests; P0-T06+G01/G02 regression 110 pass; full suite only 8 known SACR failures
- **Next:** P2-T04 (after P2-T02 controls); P4-T03
- **Blocker:** —
- **Notes:** [2026-11-22] relation-search operator agent started (engineering only) | [2026-11-22] policy ptp-relsel-first-unresolved/1.0.0 (sha256 e4ea084c...) to be frozen in P2-T04 protocol; reranks against original query only; synthetic packet shows plumbing only, new candidates rank below seeds

## P2-T04 — Screen the bounded mechanism against close matched controls

- **Status:** see the table above (single place to update)
- **Depends on:** P2-T02; P2-T03
- **Acceptance evidence:** Use permitted DEV only; compare static queries, generic feedback, extractive feedback and shuffled bindings as needed; count new families and net final score, all attempted variants and costs.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P2-T05 if viable
- **Blocker:** —

## P2-T05 — Freeze the selected method, primary endpoint and next evaluation

- **Status:** see the table above (single place to update)
- **Depends on:** P2-T04
- **Acceptance evidence:** Declare strongest eligible comparator, primary metric/population, +0.010 proposed practical target or justified prospective margin, uncertainty/guards and exact protected-access gate before results.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P2-T06
- **Blocker:** —

## P2-T06 — Measure the primary matched retrieval comparison

- **Status:** see the table above (single place to update)
- **Depends on:** P2-T05
- **Acceptance evidence:** Run only after the declared access gate; retain paired scores, intervals, subgroup counts, failures and costs; keep DAPFAM exposed comparison separate from protected evaluation.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P2-T07; P3-T03
- **Blocker:** —

## P2-T07 — Attribute candidate acquisition and decide research readiness

- **Status:** see the table above (single place to update)
- **Depends on:** P2-T06
- **Acceptance evidence:** Require evidence of newly recovered judged-positive families, net primary-score gain and relevant ablations for an acquisition claim; distinguish ranking-only gains; freeze claims to actual evidence.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P3-T03; P4 integration; P5-T02
- **Blocker:** —
