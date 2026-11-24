# P2 — Constructive structural candidate acquisition

Phase status: **IN_PROGRESS**

**Entry rule:** Start each task only when its listed task dependencies and execution authority hold. Entry requirements describe the first available work; AFFiNE and full P0 completion do not gate research.

**Exit rule:** Required tasks have verified evidence or an explicit permitted skip; material blocked work prevents COMPLETE. Research outcome is reported separately.

| Task | Title | Status | Outcome | Next |
|---|---|---|---|---|
| P2-T01 | Audit eligible content and available structural evidence | ✅ COMPLETE | ENGINEERING_VERIFIED | P2-T02 (claims-complete rebuild vs equal-content control; Arctic/BM25 pilot first) |
| P2-T02 | Establish complete-content and stronger simple controls | ✅ COMPLETE | ENGINEERING_VERIFIED | Monitor PatEmbed; recheck low-cost Qwen3 capacity and preserve the budget guard |
| P2-T03 | Implement one bounded source-relation search action | ✅ COMPLETE | ENGINEERING_VERIFIED | P2-T04 (after P2-T02 controls); P4-T03 |
| P2-T04 | Screen the bounded mechanism against close matched controls | 🟡 PARTIAL | NOT_RUN | Finish D19 and freeze the executable matched P1-DEV screen before computing metrics |
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
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P2-T02_coverage_control_results.md
- **Check:** PatEmbed remote SHA PASS; same-pod transfer retry started after optional hf_transfer setup error. Qwen3 create HTTP 400; no pod
- **Next:** Monitor PatEmbed; recheck low-cost Qwen3 capacity and preserve the budget guard
- **Blocker:** —
- **Notes:** [2026-11-22] protocol frozen at docs/healthtech/research/p2-coverage/P2-T02-COVERAGE-CONTROL-PROTOCOL.md; implementation next | [2026-11-23] C0 gate passed exactly on full P1-DEV before the OOM; no result numbers | [2026-11-23] Amendment A1: running on RunPod pod 0adflwvktmsvuu (A40, USD 0.59/h, no volume); C0 rebuilt and gated before C1/C2; envelope R1 USD 20, stop at 15 | [2026-11-23] A1 run live on RunPod pod jd41r4cvv171q6 (US-KS-2, USD 0.72/h) since 13:25 UTC; inputs sha256-verified; stop at USD 15 | [2026-11-24] Coverage control done on RunPod: Arctic C1-C0 +0.0165 [0.0144,0.0186], BM25-full-C0 +0.0223 [0.0200,0.0247] -> new representation baselines; structure C2-C1 -0.0087 (no credit). C0 reproduction exact. Fusion/deeper-control descriptives deferred to dr-train | [2026-11-24] D19 uses frozen Qwen3 and PatEmbed C1 arms. Local tests found and corrected the declared Qwen3 window guard and cosine computation before any C1 score. | [2026-11-24] D26 authority received before any pod creation or new evidence. | [2026-11-24] Private p2t02-d19-stage-20261124 verification.json pins both rebuilt manifest digests. PatEmbed relay sidecar unavailable; preserved C0 gate and computed local archive digest. | [2026-11-24] A100 price USD 2.19/h compute with up to USD 0.03/h ephemeral disk; reserve USD 9.50, four-hour operating deadline. P1-DEV only. | [2026-11-24] D26 first pod US-MD-1, USD 2.19/h compute plus disk, started 13:47:49 UTC on 24 Nov | [2026-11-24] Qwen3 selected Secure US-MO-1 L40S at USD 1.09/h compute plus ephemeral disk; 7h15m operating deadline. | [2026-11-24] Attempt 1 weight transfer failed before hashes. Retry with HF_HUB_ENABLE_HF_TRANSFER=0, same pins and deadline. L40S stock fell to NONE before creation.

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
- **Evidence:** docs/healthtech/research/p2-coverage/P2-T04-SCREEN-PREPARATION.md
- **Check:** Frozen-manifest integration fixtures PASS; combined full suite running. Live BM25 parity and screen NOT_RUN
- **Next:** Finish D19 and freeze the executable matched P1-DEV screen before computing metrics
- **Blocker:** Comparator decisions pending D19 execution; offline runtime prep can proceed
- **Notes:** [2026-11-24] D26 authorizes parallel synthetic runtime preparation; no research scoring before freeze. | [2026-11-24] Arctic C1 and BM25-full retrieval run fingerprints recorded. P2-T04 adapters await full suite and frozen manifest; no DEV metrics computed. | [2026-11-24] Offline runner requires a pinned P1-DEV manifest, exact original-query BM25 parity, shared G03 seed and an isolated evaluator.

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
