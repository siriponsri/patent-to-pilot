# G03 DEV decision memo, protocol v1 (22 Nov 2026)

**Protocol:** [G03-DEV-PROTOCOL.md](G03-DEV-PROTOCOL.md), frozen at ec720914 before any G03 number.
**Results:** [g03-dev-results.json](g03-dev-results.json), [g03-dev-tables.md](g03-dev-tables.md) (all 75 arms per block),
[g03-dev-gate.json](g03-dev-gate.json).
**Code:** `scripts/research/g03_route_acquisition.py`, `g03_decide.py`, `g03_queue.sh`, `g03_render.py`.
**Cost:** USD 0; dr-train CPU, about 35 minutes. No TEST block was read, and DAPFAM was not used.

## 1. Exact method compared

- **Routes:** precomputed depth-1,000 rankings on the 1M-unit Challenge-1M corpus:
  - L = BM25;
  - Q = Qwen3-Embedding-0.6B;
  - P = PatEmbed-large;
  - A = Arctic-embed-m-v2.0;
  - all zero-shot.
- **Actions:** windows of 200 per route. **Budget:** B = 4 (sweep 2–4). **Final scorer:** RRF over acquired windows, common
  to every arm.
- **support_frontier_v0:**
  - lexical + dense anchor (L1, then P1; P was the best dense route on P1-DEV);
  - then the per-query observable score yield × (1 − dup) (novelty) or yield × dup (consensus).
  - Consensus won on P1-DEV, so SF\* = SF-v0c.

## 2. Results

- **E01 reproduction gate:** 24/24 cells equal the existing single-route summaries (P1-DEV and VAL; ALL/IN/OUT R@200).
- **Best fixed allocation on P1-DEV:** F\* = Q×2 + P×2, i.e. Qwen3 and PatEmbed to depth 400 each, with no BM25 and no
  Arctic. ALL R@200 = 0.4230 (P1-DEV), 0.4523 (VAL).

**Principal contrast on VAL (SF\* − F\*, B = 4, cluster bootstrap by art unit, 10,000 replicates):**

| R@200 | Δ [95% CI] | wins / losses |
|---|---|---|
| ALL | −0.0199 [−0.0254, −0.0141] | 112 / 245 |
| IN | −0.0208 [−0.0301, −0.0111] | 64 / 141 |
| OUT | −0.0157 [−0.0241, −0.0076] | 58 / 115 |

**Decision (frozen rule): PARK the adaptive allocation v0.** F\* stays the static default.

**Descriptive (P1-DEV / VAL):**

| Contrast | P1-DEV | VAL |
|---|---|---|
| SF\* − round robin | +0.004 | +0.006 |
| SF\* − deeper PatEmbed (P×4) | −0.012 | −0.009 |
| SF\* − its own anchor (L1 + P1) | +0.017 | +0.017 |

The adaptive part does add recall on top of its own anchor. The anchor is the problem: at B = 2 the best fixed pair
(Q1 + P1) reaches 0.418 on P1-DEV against 0.388 for the forced L1 + P1.

## 3. Observed failures and what they mean

1. **The forced lexical anchor (POLICY_V0 §2.3) costs one of four actions on the weakest route.**
   - BM25 is 0.217 ALL R@200, against 0.418 for PatEmbed.
   - No DEV-best allocation at any budget uses BM25.
2. **Observable overlap is a weak allocation signal.**
   - Consensus beats novelty (+0.014 on P1-DEV at B = 4), but neither beats a well-chosen fixed allocation.
   - In the novelty variant, the first anchor route always shows zero duplication, which biases it toward going deeper on
     BM25. This is a defect of the v0 rule as written; it is recorded, not patched.
3. **Headroom exists but is label-dependent.**
   - Choosing the best of the 35 fixed allocations per query with labels (post-hoc, descriptive only) would give ALL R@200
     0.502 vs 0.423 on P1-DEV (+0.079), and 0.529 vs 0.452 on VAL.
   - This repeats the Paper 2 pre-check: per-query oracle headroom without an observable predictor (router NO_GO).
4. **More actions of the same kind give little.** The best fixed allocation goes from 0.418 (B = 2) to 0.423 (B = 4) on
   P1-DEV. Extra depth on the same routes adds little; new kinds of candidates are needed.

## 4. Next version (mechanism-level, pre-declared)

- **[G03-DEV-AMENDMENT-1-20261122.md](G03-DEV-AMENDMENT-1-20261122.md):** field obligations (title+abstract, first
  independent claim) as new PatEmbed routes. This tests M1 (structured obligations) rather than re-tuning v0.
- **A learned route selector** (METHOD_SPEC §6 allows it after the rule and controls expose a limitation) is a candidate for
  amendment 2. It needs the TRAIN-block runs of every route; the PatEmbed TRAIN run does not exist yet.
- **For the paper (STATISTICAL_PLAN §8):** if acquisition stays null, the headline can rest on the maintenance contribution
  (C2/M3). The experiment history is not rewritten.

## 4a. Amendment 1 result: field obligations (M1), decided 22 Nov

**Results:** [g03-dev-results-a1.json](g03-dev-results-a1.json). **Integrity:** F\* evaluated in both namespaces gives
identical per-query values on P1-DEV and VAL.

**Setup:**
- New routes: T (PatEmbed on title+abstract) and C (PatEmbed on the first independent claim).
- 70 fixed allocations over L, Q, P, T, C at B = 4.

**Findings:**
- The best on P1-DEV is **F1\* = Q1 + P1 + C2**, so it does use an obligation route. ALL R@200 = 0.4248, against 0.4230
  for F\*.
- On P1-DEV, F1\* − F\* = **+0.0018 [+0.0003, +0.0032]**: real but tiny.
- **Principal on VAL, F1\* − F\*:**
  - ALL **−0.0054 [−0.0107, +0.0000]**;
  - IN −0.0078 [−0.0169, +0.0016];
  - OUT −0.0051 [−0.0123, +0.0016].
- **Decision (frozen rule): PARK obligation routes.** The IN and OUT lower bounds fall below −δ, so non-inferiority is not
  shown. The DEV gain does not carry to VAL.

**Descriptive:**
- Field routes alone are weaker than the whole query: T×4 0.393 and C×4 0.381, against P×4 0.418 on P1-DEV.
- SF-v1c (PatEmbed anchor, consensus over 5 routes) is below F1\* on both blocks: −0.011 on P1-DEV, −0.007 on VAL.

**Reading:** with these encoders and a fixed RRF scorer, re-slicing the same request into field queries adds very few new
relevant families. Effects of ±0.005 sit at the resolution limit of VAL (2,000 tasks).

## 5. Product consequence

The static default for product retrieval is a fixed dense allocation fused by RRF. The DEV winner uses PatEmbed, whose
assets are research-only (CC BY-NC-SA), so the product default must use licence-compatible routes such as Qwen3 (Apache 2.0)
plus BM25. That choice is a separate product decision, not this DEV result.
