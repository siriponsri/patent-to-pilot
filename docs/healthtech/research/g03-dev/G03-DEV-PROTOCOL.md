# G03 DEV protocol v1: budgeted route acquisition on P1-DEV (FROZEN before any G03 number)

**Program:** PTP-2026-11-21 / G03 (E01–E03 of `research/EXPERIMENT_REGISTRY.md`; method from `research/METHOD_SPEC.md` and
`POLICY_V0.md`).

**Frozen:** 22 Nov 2026. The commit that adds this file is the freeze; no G03 number existed before it. This file is not edited
after freezing; any change goes into a dated amendment file.

**Known beforehand, disclosed:**
- The single-route P1-DEV/VAL summaries (BridgeRet E0/zero-shot evaluations, Nov 2026). For example, OUT R@200: BM25 0.1727,
  Arctic 0.2248, Qwen3 0.2741, PatEmbed 0.3282.
- The AM-7 stage 2a lessons: OUT-only endpoints are gameable (N4), and co-citation adds about +0.01.

**Spend:** USD 0, CPU only on dr-train. **Data:** allowed non-DAPFAM DEV only.
- No TEST block is read; the evaluator refuses TEST.
- DAPFAM and Gazette are not used and select nothing.

## 1. Question

Under the same action budget and the same final scorer, does an adaptive per-query allocation of search actions
(support_frontier_v0, single whole-query obligation) retrieve more known relevant families than the best fixed allocation?
It must also do so without losing IN or OUT recall.

## 2. Data and evaluator

- **Blocks:**
  - **P1-DEV** (selection; 26,575 tasks, 25,626 with runs);
  - **VAL** (decision block; 2,000 tasks; viewed descriptively in AM-7, never used for selection here).
- **Labels:** developer-visible `challenge1m/out-v1/pairs-dev.tsv`, `corpus-units.tsv` and `splits/private/tasks.tsv`
  (filing dates only), read **only** by the existing evaluator `eval_bridgeret_dev.py`, unchanged:
  - positives = cited units first published before the filing date, own unit excluded;
  - IN/OUT by `dom_ipc3`;
  - query-macro over queries with a non-empty relevant set;
  - a query missing from the run scores 0.
  The runtime (arms and policy) never reads labels.
- **Routes:** precomputed depth-1000 rankings over the 1M-unit Challenge-1M corpus:
  - **L** = BM25 (`runs/bm25`);
  - **Q** = Qwen3-Embedding-0.6B zero-shot (`runs/z-qwen3`);
  - **P** = PatEmbed zero-shot (`runs/z-patembed`; research-only licence);
  - **A** = Arctic-embed-m-v2.0 zero-shot (`runs/z-arctic`).

## 3. Action model (shared by every arm)

- **search(route, window w)** returns ranks (w−1)·200+1 … w·200 of that route. A route's windows are taken in order, so a
  deeper search is a distinct, counted action. The same signature is never repeated.
- **Budget B** = number of search actions per query. Primary: **B = 4** (POLICY_V0: 4 search actions, depth 200,
  candidate cap 800). Sweep: B ∈ {2, 3, 4}, the same for every arm.
- **Common final scorer:**
  - s(c) = Σ over routes r whose *acquired* windows contain c of 1 / (60 + rank_r(c));
  - ties: best acquired rank, then unit id;
  - final ranked depth 200 (written to the run file evaluated at R@200).
- No reranker, LLM, graph expansion or co-citation in this protocol.

## 4. Arms

| Arm | Definition |
|---|---|
| **E01 single routes** | L, Q, P, A with B = 1. Reproduction gate: their ALL/IN/OUT R@200 must equal the existing summaries to 4 decimals before any other arm is read. |
| **Fixed allocations** | Every allocation (nL, nQ, nP, nA) with Σ = B (35 at B = 4; 20 at B = 3; 10 at B = 2), with windows taken in order. |
| **F\*** (best fixed) | Allocation with the highest P1-DEV ALL R@200 at B = 4. Ties within 0.0005: fewer routes, then route order Q, P, A, L. |
| **RR** (round robin) | (1, 1, 1, 1) at B = 4. |
| **D** (deeper) | The single route with the best P1-DEV ALL R@200 at B = 1, taking all B windows. |
| **SF-v0n** (novelty) | Policy, §5, score = yield × (1 − dup). |
| **SF-v0c** (consensus) | Same as SF-v0n except score = yield × dup. This tests the opposite observable hypothesis: agreement concentrates relevance. |

## 5. Policy support_frontier_v0 (deterministic, per query, labels never read)

1. **Anchor:** lexical + best dense:
   - L window 1;
   - then the dense route with the best P1-DEV ALL R@200 at B = 1, window 1 (POLICY_V0 §2.3).
   - These are 2 actions.
2. **For each remaining action, score every route's next window:**
   - yield(r) = (1 + useful_r) / (2 + attempts_r), where useful = the window added ≥ 1 new unit (POLICY_V0 §5);
   - dup(r) = the fraction of r's last acquired window that was already in the pool when acquired;
   - a never-used route gets the declared neutral dup = 0.5;
   - planning cost = 1 for every route (no calibrated costs; POLICY_V0 §6).
3. **Ties:** fewer attempts on that route, then order L, Q, P, A (lexical before dense; POLICY_V0 §7).
4. **Stop:** when B actions are used, or when every route is at depth 1000.
   - stop reason "budget used" ≠ "no relevant document exists".

## 6. Endpoints

- **Primary:** ALL R@200 (query-macro, evaluator definition).
- **Joint constraint, declared because of AM-7:** IN R@200 and OUT R@200 are each non-inferior to the comparator, with margin
  **δ = 0.005 absolute**. That is half of the smallest gain AM-7 treated as practically relevant (0.010), and roughly one
  extra relevant family in 200 queries with one positive each.
- **Secondary (descriptive):**
  - pool recall of all acquired units (ALL/IN/OUT; candidate availability, not ranking quality);
  - R@1000 is not applicable (pool ≤ 800);
  - OUT MRR, OUT nDCG@10, actions used, unique candidates, CPU seconds.

## 7. Selection (P1-DEV only) and decision (VAL)

- **On P1-DEV:**
  - choose F\* (§4);
  - choose **SF\*** = the SF variant with higher ALL R@200 at B = 4 (tie within 0.0005 → SF-v0n, the POLICY_V0 default).
  - No other parameter is tuned.
- **Principal contrast on VAL: SF\* − F\*** at B = 4, paired per query.
  - Cluster bootstrap by examiner art unit (am7_lib `cluster_bootstrap`, B = 10,000, seed 20261119).
  - If the art unit is unavailable for a query, its own cluster is used.
  - 95% CIs for ALL, IN and OUT R@200.
- **Decision rule (doc 02 continue / revise / park):**
  - **Continue** (adaptive helps): the ALL lower CI > 0, and the IN and OUT lower CIs > −δ.
  - **Revise:** the ALL CI includes 0 and IN/OUT hold. Record a mechanism-level hypothesis before any v1.
  - **Park the adaptive allocation:** the ALL upper CI < 0, or IN or OUT is inferior. F\* stays the Product static default.
- **Mechanism contrasts, descriptive** with the same bootstrap and no multiplicity claim:
  - SF\* − RR;
  - SF\* − D;
  - the anchor-only (2 actions) increment;
  - the B = 2/3/4 sweep for SF\*, F\*(B) and RR.
- **Reported regardless of outcome:**
  - every executed arm, including failures and the full 35-allocation table on P1-DEV;
  - the same arms on VAL.

## 8. What this protocol can and cannot show

- **Can show:** whether observable-overlap allocation beats a DEV-selected fixed allocation of the same actions, at matched
  budget, with the final scorer held fixed.
- **Cannot show:**
  - true recall;
  - user benefit;
  - transfer to DAPFAM or Gazette;
  - anything about obligations beyond a single whole-query obligation (decomposition is a later variant, M1).
- **N4 (IPC demotion)** is a final-ordering manipulation, not an acquisition arm. It is deferred to E05 on DAPFAM native, where
  ALL/IN/OUT are reported jointly.

## 9. Code and receipts

- **Code:** `scripts/research/g03_route_acquisition.py` builds the arm run files. Evaluation uses the unchanged
  `eval_bridgeret_dev.py`, and `scripts/research/g03_decide.py` computes the selection, bootstrap and decision.
- **Outputs on dr-train:** `/data/ptp-paper2/g03-dev/`. Aggregates go to `docs/healthtech/research/g03-dev/`.
- **Per-query rows** stay on dr-train and in the local private archive.
