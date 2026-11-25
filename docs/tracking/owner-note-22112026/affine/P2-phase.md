# P2 — Constructive structural candidate acquisition

Phase status: **IN_PROGRESS**

**Entry rule:** Start each task only when its listed task dependencies and execution authority hold. Entry requirements describe the first available work; AFFiNE and full P0 completion do not gate research.

**Exit rule:** Required tasks have verified evidence or an explicit permitted skip; material blocked work prevents COMPLETE. Research outcome is reported separately.

| Task | Title | Status | Outcome | Next |
|---|---|---|---|---|
| P2-T01 | Audit eligible content and available structural evidence | ✅ COMPLETE | ENGINEERING_VERIFIED | P2-T02 (claims-complete rebuild vs equal-content control; Arctic/BM25 pilot first) |
| P2-T02 | Establish complete-content and stronger simple controls | ✅ COMPLETE | ENGINEERING_VERIFIED | Use both D19 C1 routes in frozen P2-T04 |
| P2-T03 | Implement one bounded source-relation search action | ✅ COMPLETE | ENGINEERING_VERIFIED | P2-T04 (after P2-T02 controls); P4-T03 |
| P2-T04 | Screen the bounded mechanism against close matched controls | 🔄 IN_PROGRESS | NOT_RUN | Monitor the frozen cutoff-tie gate, matched runtime and separate evaluator on dr-train |
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
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P2-T02_coverage_control_results.md; docs/tracking/owner-note-22112026/receipts/P2-T02_D19_followup_results.md
- **Check:** 2026-11-25
- **Next:** Use both D19 C1 routes in frozen P2-T04
- **Blocker:** —
- **Notes:** [2026-11-22] protocol frozen at docs/healthtech/research/p2-coverage/P2-T02-COVERAGE-CONTROL-PROTOCOL.md; implementation next | [2026-11-23] C0 gate passed exactly on full P1-DEV before the OOM; no result numbers | [2026-11-23] Amendment A1: running on RunPod pod 0adflwvktmsvuu (A40, USD 0.59/h, no volume); C0 rebuilt and gated before C1/C2; envelope R1 USD 20, stop at 15 | [2026-11-23] A1 run live on RunPod pod jd41r4cvv171q6 (US-KS-2, USD 0.72/h) since 13:25 UTC; inputs sha256-verified; stop at USD 15 | [2026-11-24] Coverage control done on RunPod: Arctic C1-C0 +0.0165 [0.0144,0.0186], BM25-full-C0 +0.0223 [0.0200,0.0247] -> new representation baselines; structure C2-C1 -0.0087 (no credit). C0 reproduction exact. Fusion/deeper-control descriptives deferred to dr-train | [2026-11-24] D19 uses frozen Qwen3 and PatEmbed C1 arms. Local tests found and corrected the declared Qwen3 window guard and cosine computation before any C1 score. | [2026-11-24] D26 authority received before any pod creation or new evidence. | [2026-11-24] Private p2t02-d19-stage-20261124 verification.json pins both rebuilt manifest digests. PatEmbed relay sidecar unavailable; preserved C0 gate and computed local archive digest. | [2026-11-24] A100 price USD 2.19/h compute with up to USD 0.03/h ephemeral disk; reserve USD 9.50, four-hour operating deadline. P1-DEV only. | [2026-11-24] D26 first pod US-MD-1, USD 2.19/h compute plus disk, started 13:47:49 UTC on 24 Nov | [2026-11-24] Qwen3 selected Secure US-MO-1 L40S at USD 1.09/h compute plus ephemeral disk; 7h15m operating deadline. | [2026-11-24] Attempt 1 weight transfer failed before hashes. Retry with HF_HUB_ENABLE_HF_TRANSFER=0, same pins and deadline. L40S stock fell to NONE before creation. | [2026-11-24] P2-T04 complete lexical corpus kept locally from same paid run. No additional network volume. Qwen3 stock still pending. | [2026-11-24] P2-T04 lexical data hash matches archived Arctic artifact. | [2026-11-24] RTX quote USD 0.72/h compute plus disk. Direct create returned unavailable. Queue cmwustzcf0083geoxv18etk77 expires after eight minutes. | [2026-11-24] Qwen3 RTX direct create returned unavailable. Queue expired 14:45:36 UTC, podId null; only PatEmbed running. Reprice within D26 after lower-cost stock or PatEmbed settlement. | [2026-11-24] Qwen3 10813cm5sej2s2 at USD 0.72/h compute plus disk. 14:58:21 UTC create, deadline 25 Nov 01:46:21 UTC. | [2026-11-24] Collectors terminate only after pull SHA-256 verification. Provider termination and billing verification remain required. | [2026-11-24] Qwen3 selected window 511 under the declared tokenizer rule. | [2026-11-24] Qwen3 first two shard timings and token-length resource estimate recorded; research scores NOT_RUN. | [2026-11-24] PatEmbed all 13 shards merged. C1 scores still NOT_RUN at this checkpoint. | [2026-11-24] PatEmbed exact invoice pending; USD 6 provisional, USD 8.50 Qwen3 reservation, USD 5.50 conservative uncommitted within D26. | [2026-11-24] Qwen3 442–480 minutes estimated remaining encode from 16:53 UTC, plus retrieval, gates and pull. | [2026-11-25] PatEmbed post-teardown billing reconciled USD 5.98138593; Qwen3 USD 8.50 reservation remains. D26 cap USD 20. | [2026-11-25] Qwen3 scoped CLI self-lookup unverified. Monitor management API teardown explicitly. | [2026-11-25] Two SSH watcher reads briefly disconnected, then recovered on the same run; no additional pod. | [2026-11-25] All 14 Qwen3 shards merged; keep provider delete ready after verified pull. | [2026-11-25] [2026-11-25] Both D19 archives verified and both pods deleted; PatEmbed billing reconciled, Qwen3 final day bucket pending. Spend includes conservative USD 7.20 for Qwen3. | [2026-11-25] RunPod billing reconciled after the closing bucket. PatEmbed USD 5.98138593 and Qwen3 USD 7.07228578. Pod list empty including cluster members.

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
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P2-T04_frozen_protocol.md; docs/tracking/owner-note-22112026/receipts/P2-T04_execution.md
- **Check:** 2026-11-25
- **Next:** Monitor the frozen cutoff-tie gate, matched runtime and separate evaluator on dr-train
- **Blocker:** —
- **Notes:** [2026-11-24] D26 authorizes parallel synthetic runtime preparation; no research scoring before freeze. | [2026-11-24] Arctic C1 and BM25-full retrieval run fingerprints recorded. P2-T04 adapters await full suite and frozen manifest; no DEV metrics computed. | [2026-11-24] Offline runner requires a pinned P1-DEV manifest, exact original-query BM25 parity, shared G03 seed and an isolated evaluator. | [2026-11-24] Source adapters and frozen-manifest entry point verified on authored fixtures. dr-train has sklearn 1.9.1; require exact archival BM25 parity. | [2026-11-24] Staged P1-DEV Arctic-serialised original queries under the dr-train memory watchdog and recovered the exact historical A3r1 comparator from the verified archive. | [2026-11-24] One bounded stream with 30 GiB MemAvailable guard. No new retrieval calls. | [2026-11-24] Evaluator keeps an exact P1-DEV cohort, includes empty rankings and reads judgments outside runtime. | [2026-11-24] Separate evaluator ready. Runtime manifest awaits D19 decisions and exact archive BM25 reproduction. | [2026-11-24] Code archive ff9c2048. Complete frozen route decisions after D19. No research job has run on dr-train. | [2026-11-24] The Windows sklearn skip was exercised with actual dr-train backend dependencies using one CPU process and the 30 GiB guard. | [2026-11-25] [2026-11-25] D19 C1 controls and frozen runtime/evaluator manifests verified on dr-train. No matched rankings or scores yet. | [2026-11-25] [2026-11-25] The frozen CPU launcher started at 00:40:48 UTC. One guarded process group; no RunPod spend. | [2026-11-25] [2026-11-25] First frozen app differs. Zero matched scores; no memory abort or paid spend. | [2026-11-25] [2026-11-25] Attempt logs pulled and hash-verified. Scoped diagnostic v2 started 01:00:12 UTC; per-item approval requested for the original scikit-learn wheel. | [2026-11-25] [2026-11-25] Same top 999 and identical cutoff displayed score for app 13200810. Synthetic tie confirmed AVX2-dependent selection. Pinned a scalar CPU replay before scoring. | [2026-11-25] [2026-11-25] Scalar replay ended at 01:26:02 UTC at the same cutoff. Logs pulled, no scores or spend, no active job. | [2026-11-25] Owner chose A and approved one pinned PyPI wheel for a CPU-only replay. Approval does not cover a changed gate or paid compute. | [2026-11-25] Approved wheel and launcher match both pins. Isolated 1.7.2, NumPy 2.2.6, SciPy 1.18.1, AVX2 active; existing 1.9.1 verified. Guarded replay started 10:09:21 UTC. | [2026-11-25] Exact replay failed at 10:22:12 UTC and logs were verified locally. A bounded diagnostic will count cutoff-only and other mismatches across the 2,000 frozen apps; it does not read judgments or score a screen. | [2026-11-25] Census completed 10:37:49 UTC. 1,996 exact top-1000, 4 cutoff-only, zero others, 2,000 exact top-200. Logs verified locally; evaluator NOT_RUN; no paid compute. | [2026-11-25] Owner approved A. Freeze a verified raw-score tie exception solely at rank 1,000, with exact ordered top-200 and the original progression rule. | [2026-11-25] Amendment b4e0f903 was published before the 10:53:36 UTC guarded launch; five hashes verified, one CPU process group, no paid compute.

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
