# G03 DEV amendment 2 (22 Nov 2026): learned per-query allocation selector. FROZEN before any amendment-2 number

**Why:**
- Under protocol v1, the per-query oracle over the 35 fixed allocations (B = 4) would reach ALL R@200 0.502 against 0.423
  for F\* on P1-DEV (+0.079), and 0.529 against 0.452 on VAL.
- The rule-based observable signals of support_frontier_v0 did not capture this headroom.
- METHOD_SPEC §6 allows a learned selector once the rule and the controls expose a concrete limitation, using "action yield
  and cost learned on allowed DEV".

The labels come from the **TRAIN** block (developer-visible). The selector sees only runtime features.

**Independence:** this amendment uses the protocol-v1 route set (L, Q, P, A) and does not depend on amendment 1's outcome.
Amendment 1 was frozen and started before this file; none of its numbers were known when this was written.

## 1. Data

- **TRAIN sample:** 30,000 TRAIN tasks, those with the smallest sha256(`g03-a2-train-v1` + app_id). Eligible tasks have
  ≥ 1 ALL positive under the evaluator rules and output from all four routes.
- **TRAIN route runs:**
  - L, Q and A already exist;
  - P (PatEmbed-large, whole query) is built now with exactly the z-patembed settings, from `ser-patembed-v1/queries.jsonl`:
    mean pooling, prompt `encode query for mixed document retrieval: `, 512 tokens, exact inner product over the same
    passages, top 1,000.
- **Targets:** per-query ALL, IN and OUT R@200 for each of the 35 B = 4 allocations, computed on the TRAIN sample by the
  unchanged evaluator, with the same action model and final scorer as protocol v1.

## 2. Features (runtime-observable only; no labels, no text)

- **Per route** r ∈ {L, Q, P, A}:
  - the scores at ranks 1, 10, 50 and 200;
  - s1 − s200;
  - an output-present flag.
- **Per route pair:** the overlap of their top-200 sets, |∩| / 200 (6 pairs).
- Total: 30 features.

## 3. Selectors

Each candidate predicts, for every allocation, a query's ALL R@200 from the features. Per query it then picks the
allocation with the highest prediction. Ties: F\* first, then the protocol-v1 F\* tie order.

| ID | Model per allocation |
|---|---|
| LS-ridge | Standardised features; ridge α = 1.0 |
| LS-hgb | `HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=31, random_state=0)` |

The realised R@200 of a selected allocation for a P1-DEV or VAL query is read from the protocol-v1 evaluation of that
allocation (per-query values from the unchanged evaluator). No new P1-DEV or VAL runs are needed.

## 4. Selection, principal contrast and decision

- **Selection on P1-DEV:** LS\* = the selector with the higher ALL R@200. Ties within 0.0005 → LS-ridge.
- **Principal on VAL: LS\* − F\*** (F\* = `alloc-L0-Q2-P2-A0`). Same cluster bootstrap, same δ = 0.005 IN/OUT
  non-inferiority, same continue / revise / park rule as protocol v1 §7.
- **Disclosed:** this is the third look at VAL in G03 (v1 decision, amendment 1, amendment 2). DEV-phase only. The paper's
  confirmatory comparison is a later frozen G04 run.
- **Descriptive:**
  - the share of oracle headroom captured: (LS\* − F\*) / (oracle − F\*);
  - the distribution of chosen allocations;
  - both selectors on both blocks.
