# G03 DEV amendment 1 (22 Nov 2026): obligation routes (M1). FROZEN before any amendment-1 number

**Why (v0 result, `G03-DEV-DECISION-MEMO.md`):**
- support_frontier_v0 was PARKED: on VAL, SF\* − F\* gave ALL R@200 −0.020 [−0.025, −0.014].
- The forced lexical anchor costs one action on the weakest route; every best fixed allocation used no BM25.
- Observable route-overlap signals did not capture the post-hoc per-query headroom (+0.079 ALL R@200).

Following doc 02 ("do not continue costly retries without a new mechanism-level hypothesis"), amendment 1 tests a
**different mechanism**. It does not tune v0.

**H-M1:** splitting the request into field obligations adds relevant families that whole-query routes miss, at the same
budget and with the same final scorer.
- **O1:** title + abstract (the problem context).
- **O2:** the first independent claim (the claimed elements).

## 1. New routes (runtime side, no labels)

- **T:** PatEmbed-large on O1, i.e. `title + "\n" + abstract`.
- **C:** PatEmbed-large on O2, the first independent claim (`claim`).
- Both use exactly the z-patembed settings: mean pooling, prompt `encode query for mixed document retrieval: `,
  512 tokens, fp16, L2-normalised.
- Retrieval: exact inner product against the existing `runs/z-patembed/passages.f16.npy` (1M units), top 1,000.
  Ties: score desc, then unit order, as in `dense_bridgeret_v3.py`.
- Blocks: P1-DEV and VAL only.
- Hardware: encoding runs on the approved V100 under the shared GPU lock with memory fraction 0.12; retrieval on CPU.

## 2. Arms (same action model, budget and final scorer as protocol v1 §3)

- **Routes:** L, Q, P (v1 protocol) plus T and C.
- **Fixed allocations:** all 70 allocations with B = 4 over (L, Q, P, T, C).
- **F1\*:** the best of these on P1-DEV by ALL R@200. Ties within 0.0005: fewer routes, then route order P, Q, T, C, L.
- **SF-v1c (descriptive):** anchor = P window 1 (no forced lexical anchor), then the v0 consensus score over all five
  routes, with the same tie rule (route order L, Q, P, T, C).

## 3. Principal contrast and decision

- **Principal: F1\* − F\* on VAL at B = 4,** where F\* = `alloc-L0-Q2-P2-A0` (the protocol v1 best fixed allocation). This
  isolates the value of adding obligation routes.
- Same endpoint (ALL R@200), same IN/OUT non-inferiority margin δ = 0.005, same cluster bootstrap, same continue / revise /
  park rule.
- If F1\* contains no T or C window, H-M1 is "not supported on DEV" and nothing on VAL is needed beyond descriptive
  reporting.

**Disclosed second look:** VAL was used once for the protocol v1 decision. This is its second use. Both are DEV-phase
decisions, and neither is a confirmatory claim for the paper.

**Descriptive:** SF-v1c − F1\*, the full 70-allocation table, and the overlap of T and C with Q and P (shared units in the
top 200).
