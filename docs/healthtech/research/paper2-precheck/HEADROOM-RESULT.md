# Paper 2 pre-check result: BM25 exposure headroom on DAPFAM dev

**Verdict: NO_GO** (pre-declared rule in `HEADROOM-PREDECLARATION.md`, committed 35016fe before any computation).
RRF(B0, BM25) − B0: OUT Recall@200 **−0.0197** (needed ≥ +0.010); IN Recall@200 **−0.0555** (needed ≥ −0.020). Both
conditions fail. Reported as-is; no variants were run.

Run once, CPU only, local: 96.2 s process CPU (metered, `cpu-receipts.jsonl`), 107.4 s wall, 0 model calls,
no protected test access. Inputs hash-verified; B0 reproduces Paper 1 S5 (ALL/IN/OUT Recall@200 0.34262/0.51370/0.14772).
BM25 index: 45,336 families, 183,862 terms, avg length 748 tokens; every query returned 200 BM25 results.
Full aggregates: `headroom-dev-result.json`. Per-query values stay in the private folder.

## Main table (dev, macro over eligible queries)

| Partition (n) | Metric | B0 | BM25 | RRF | RRF − B0 (W/L/T) | U400 Recall@400 |
|---|---|---|---|---|---|---|
| OUT (349) | Recall@200 | 0.1477 | 0.0690 | 0.1280 | −0.0197 (10/50/289) | 0.1679 |
| OUT | Recall@100 | 0.0973 | 0.0498 | 0.0897 | −0.0076 (17/32/300) | |
| OUT | NDCG@10 | 0.0233 | 0.0109 | 0.0204 | −0.0029 (19/21/309) | |
| IN (450) | Recall@200 | 0.5137 | 0.2829 | 0.4582 | −0.0555 (45/212/193) | 0.5489 |
| IN | Recall@100 | 0.3941 | 0.2104 | 0.3643 | −0.0298 (62/182/206) | |
| IN | NDCG@10 | 0.2069 | 0.1102 | 0.1733 | −0.0336 (122/186/142) | |
| ALL (474) | Recall@200 | 0.3426 | 0.1764 | 0.2994 | −0.0433 (45/237/192) | 0.3686 |

## OUT exposure (query has ≥ 1 OUT positive in the pool), vs B0 top-200

| System | both | system only | B0 only | neither |
|---|---|---|---|---|
| BM25 @200 | 70 | 12 | 66 | 201 |
| RRF @200 | 117 | 8 | 19 | 205 |
| U400 @400 (union) | 136 | 12 | 0 | 201 |

## Reading
- BM25 alone is much weaker than dense B0 on every partition (OUT Recall@200 0.069 vs 0.148).
- Fusing it at a fixed pool of 200 pushes B0 positives out: RRF loses OUT exposure on 19 queries and gains it on 8.
- Even the descriptive 400-family union (an exposure upper bound, not a fixed-200 system) adds OUT exposure on only
  12 of 349 queries (+0.020 OUT recall at twice the pool); 201 OUT queries have no OUT positive in either pool.
- So lexical BM25 does not supply the missing cross-domain candidates; the OUT exposure gap is not a "dense misses
  lexical matches" problem at this depth.

## Limitations
- Dev only and exposed: B0 dev scores were already known (Paper 1 S5). Descriptive; no bootstrap or significance.
- One BM25 configuration only (k1 0.9, b 0.4, fixed tokenizer/stopwords, TA query, TAC document), fixed in advance.
  A different lexical setup could behave differently; this check does not test that.
- B0 is the frozen list and includes the query's own family for 43 queries (10 self-positive); BM25 excludes it.
  This asymmetry slightly favours B0 on ALL/IN; it cannot explain the size of the losses.
- Recall is measured against known DAPFAM positives only; unjudged families are not negatives.
