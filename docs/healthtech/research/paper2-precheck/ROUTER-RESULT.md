# Paper 2 pre-check: label-free per-query router on DAPFAM dev — NO_GO

Status: `NO_GO`, run once on 2026-11-16, dev only.

- Spec: [ROUTER-PREDECLARATION.md](ROUTER-PREDECLARATION.md), committed in `d8f4354` before any router number was computed.
- Script: [router/run_router_dev.py](router/run_router_dev.py).
- Aggregates: [router-dev-result.json](router-dev-result.json).
- Per-query rows stay in the private folder `ptp-paper2-router-dev-20261116-v1`.
- CPU: 11.7 s (wall 13.4 s; [router/cpu-receipts.jsonl](router/cpu-receipts.jsonl)). 0 model calls, no downloads, no paid API. The test split was not read.

## Sanity

Reproduced Stage 1 exactly from hash-pinned inputs: F\* (R2 dense) = 0.16184 and the one-action oracle = 0.25572 strict-OUT R@200 (n = 349). Oracle headroom = 0.0939.

## Results (cross-fitted strict-OUT R@200, Stage 1 Amendment 1 folds)

| Router | OUT R@200 | Δ vs F\* (query-macro) | Component Δ [95% CI] | 98.33% CI | IN R@200 (Δ) | Switch rate | W / L / T | Oracle headroom captured |
|---|---|---|---|---|---|---|---|---|
| F\* = R2 | 0.1618 | — | — | — | 0.5182 | — | — | — |
| A consensus | 0.1397 | −0.0222 | −0.0001 [−0.023, +0.030] | [−0.027, +0.037] | 0.4734 (−0.045) | 98% (R3 for 339 queries) | 13 / 52 / 284 | −24% |
| **B threshold switch (best)** | **0.1618** | **0.0000** | 0.0000 [0, 0] | [0, 0] | 0.5182 (0.000) | 0% | 0 / 0 / 349 | 0% |
| C ridge gain model | 0.1615 | −0.0003 | −0.0331 [−0.098, +0.027] | [−0.115, +0.038] | 0.4947 (−0.023) | 46% (Q3 for 107 queries) | 13 / 27 / 309 | −0.4% |

Query bootstrap (descriptive): A −0.022 [−0.039, −0.006]; C −0.0003 [−0.013, +0.012].

**Verdict:**
- Best router = B, Δ = 0.000 (needs ≥ 0.010).
- 98.33% CI lower bound = 0.000 (needs > 0).
- IN Δ = 0.000 (needs ≥ −0.020).
- Result: **NO_GO**.

## Reading

- **Router B never switches.** In all five training folds (and on all 349 queries), the best τ on training data was "never switch". No threshold on the consensus gap raised training recall above R2, so B collapses to F\*. It is the "best" router only because it equals the baseline.
- **Router A (pick the most consensual list)** almost always picks R3. R3 is the RRF of R1 and R2, so it overlaps both by construction. This loses OUT recall (52 losses vs 13 wins) and IN recall.
- **Router C (ridge gain model)** switches on 46% of queries, mostly to Q3, but wins and losses cancel on OUT (13 vs 27; query-macro −0.0003). It costs 0.023 IN R@200 (component Δ −0.058, CI below 0).
- **Conclusion.** List-agreement features from the six Top-200 lists carry no usable signal about which action holds a query's cross-domain prior art. The +0.094 one-action oracle headroom remains label-dependent on this dev set. Together with the failed fixed-mix, per-section-mix and class-prior checks, no label-free selection rule tested so far beats dense R2.

## Implementation note (verdict unaffected)

The "component Δ" column is the mean of component means, the convention of `paired_cluster_bootstrap`. The GO script compared that value with the 0.010 threshold, while the pre-declaration states the query-macro difference.

For the selected router B both are exactly 0, so the verdict is the same under either reading. For A and C the two differ (one large component of 269 OUT queries, 30 OUT components). Both are shown above.

## Limitations

- Dev is exposed: Stage 1 and later checks used it. This is a feasibility screen, not a confirmatory test.
- Component dependence: 30 OUT components, the largest with 269 of 349 queries, so component intervals are wide.
- Citation-derived qrels are incomplete: unjudged ≠ negative. Some "losses" may be unjudged relevant families.
- The routers need all six action lists (2 LLM calls per query), so even a positive result would have carried that compute cost.
- Only three pre-declared routers with ranking-overlap features were tested. Score-based, text-based or query-difficulty features were not, and this result does not rule them out.
