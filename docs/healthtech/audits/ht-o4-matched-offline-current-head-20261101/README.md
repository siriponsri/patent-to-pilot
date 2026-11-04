# O4 matched offline current-head frontier — 2026-11-01

Status: `PASS_DESCRIPTIVE_MATCHED_OFFLINE_FRONTIER_O3_BLOCKED`

This package continues the existing Patent-to-Pilot O1-O4 goal. It reruns the
fixed controls `HT-B0a` through `HT-B3` and the deterministic offline
`HT-B4` controller on the same frozen Abbott development cohort, current
candidate `891f3b3`, and shared local MiniLM encoder/reranker bundle. It does
not open the paid branch, change the frozen cohort, or combine results from a
different candidate.

## Frozen inputs

- Cohort: `ht-public-cohort-20261029-frozen-r1`
- Devices: `MitraClip`, `Tendyne`, `TriClip` (`3` devices)
- Patent universe: `41` documents; `61` source-disclosed reference pairs
- Exact-patent groups: `2`; company groups: `1` (`ABBOTT MEDICAL`)
- Candidate depth / rerank depth: `41 / 41`
- Primary endpoint: macro known-link Recall@20
- Protocol hash: `a87acaa448f97eabccae0f1fecc5378720ecf1178869336f68b42174eb828b0f`
- Runtime / references / groups hashes: `3abd5cc3...`, `4024eb9c...`, `bfb1d828...`
- Cohort manifest hash: `b92b50716599ad6ea3cdeb5b6a692990a52ae8dd113bfc0bb5cad2cdd2148715`

The runtime wrote predictions before evaluator references were loaded. Unlisted
links remain unjudged and are not treated as negative labels.

## Matched frontier

| Method | Macro Recall@20 | Query calls | Rerank pairs | Failed devices |
|---|---:|---:|---:|---:|
| HT-B0a company/metadata control | 0.442739 | 3 | 0 | 0 |
| HT-B0b lexical control | 0.662242 | 3 | 0 | 0 |
| HT-B1 fixed hybrid | 0.498802 | 3 | 123 | 0 |
| HT-B2 fixed multi-query | 0.568912 | 9 | 369 | 0 |
| HT-B3 simple adaptive heuristic | 0.498802 | 5 | 205 | 0 |
| HT-B4 deterministic offline controller | 0.498802 | 5 | 205 | 0 |

HT-B4 micro Recall@20 was `0.475410` and controller steps were `8`. Every
attempt in both runs completed; the baseline error count was `0`. Provider
calls, paid cost, GPU jobs, ledger mutations, and retries that could change
the frozen condition were all `0`.

## Interpretation boundary

This is a reproducible matched development frontier, not a confirmatory study.
The current Abbott slice has no final holdout, only two exact-patent groups and
one company group, so uncertainty and company-held-out generalization are not
estimable. The observed result favors the lexical control in this cohort and
does not establish that adaptive acquisition is generally worse or better.
Product-level source-disclosed links are not semantic relevance gold, legal
validity, FTO, clinical suitability, exhaustive recall, or investment evidence.

## Private artifacts

Raw rankings, runtime predictions, evaluator outputs, and model files remain
outside Git at
`C:/Users/User/Documents/Codex/2026-10-31/task/ptp-o4-matched-20261101/`.
The tracked checkpoint stores sanitized hashes and summary values only.

## Next action

Use this frontier in the manuscript and keep the main adaptive claim
`NOT_ESTABLISHED`. The live `qwen/qwen3-32b` comparison remains gated on the
canonical R1 journal, current credit, route/pricing, outbound prompt rights,
and writer-quiescence evidence.
