# O4 matched offline frontier report

## Result

The current candidate `891f3b3` was evaluated on the same frozen Abbott
development cohort with the same local encoder/reranker revisions and
candidate/rerank depth `41`. The primary metric was macro known-link Recall@20.

| Method | Recall@20 | Calls | Rerank pairs | Status |
|---|---:|---:|---:|---|
| HT-B0a | 0.442739 | 3 | 0 | offline control |
| HT-B0b | 0.662242 | 3 | 0 | offline control |
| HT-B1 | 0.498802 | 3 | 123 | offline control |
| HT-B2 | 0.568912 | 9 | 369 | offline control |
| HT-B3 | 0.498802 | 5 | 205 | offline heuristic |
| HT-B4 offline | 0.498802 | 5 | 205 | deterministic controller |

HT-B4 also recorded micro Recall@20 `0.475410`, `8` controller steps and zero
failed devices. The fixed lexical method was the strongest observed condition
on this cohort. HT-B4 tied B1 and B3 at the reported macro endpoint while using
the same realized call and rerank counts as B3.

## Failure and uncertainty

No baseline or controller attempt failed and no provider/network call occurred.
The cohort remains development-only. It has two exact-patent groups, one
company group, no final holdout, and product-level disclosure labels. The
result therefore supports reproducibility and a descriptive quality-resource
frontier only. It does not support a superiority claim, a powered test,
semantic patent relevance, or generalization.

## Cost boundary

Paid cost was `USD0.00`; local compute is reported as realized query calls,
rerank pairs, tokens and CPU/wall time rather than being treated as free.
The API branch was not attempted and the existing cumulative USD8 scope and
ledger history were unchanged.

## Reproduction

The exact commands and artifact hashes are recorded in `verification.json` and
`CHECKPOINT.json`. Raw output roots are private and are not committed.
