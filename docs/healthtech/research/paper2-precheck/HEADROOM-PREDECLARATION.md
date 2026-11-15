# Paper 2 pre-check: BM25 exposure headroom on DAPFAM dev (PRE-DECLARATION)

Status: written and committed BEFORE any BM25 index, ranking or metric was computed (2026-11-16).
Scope: CPU only, local machine, DAPFAM **dev** only. The protected test folder is not read. No model calls, no paid API,
no downloads. Exposed dev: B0 dev scores are already known from Paper 1 S5 (OUT Recall@200 0.14772); this check is
descriptive and is not a confirmatory test.

## Question
Does adding a lexical BM25 retriever to the frozen dense baseline B0 increase cross-domain (OUT) exposure at a fixed
pool size of 200?

## Inputs (private, outside the repo; SHA-256 checked before use)
- corpus `ptp-dapfam-native-dev-20261110-v3/runtime-dev/corpus.jsonl` 42f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d (45,336 families)
- queries `.../runtime-dev/queries-ta.jsonl` 6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a (474 dev TA queries)
- qrels `.../dev-evaluation/qrels-dev.jsonl` ca693dc8a1d5c5bf10249c8e9438be5198346349dcd1b6a6194e0eeb96923473
- B0 top-200 `ptp-paper1-a2-dev-20261115-v1/reference-top200-private.jsonl` 1f0f738ff649a111f16292edb5c63bd27cb6b204f6bc6205dbef6e89323c61c9
  (S5 re-encoded anchors; must reproduce S5 B0 Recall@200 ALL/IN/OUT 0.34262/0.51370/0.14772, else stop).

## BM25 (own numpy/scipy implementation)
- Tokenizer: lowercase, tokens = regex `[a-z0-9]+`, then remove this fixed stopword list:
  a an and are as at be by for from has have in into is it its of on or that the this to was were which with
  wherein said such being comprising thereof
- Document = title + abstract + claims (joined with spaces). Query = the TA `text` field.
- Parameters k1 = 0.9, b = 0.4. idf(t) = ln(1 + (N - df + 0.5)/(df + 0.5)), N = 45,336.
  score(q,d) = sum over DISTINCT query terms t present in d of idf(t) * tf(t,d) * (k1+1) / (tf(t,d) + k1*(1 - b + b*dl/avgdl)),
  dl = token count after stopword removal. Query terms not in the corpus vocabulary contribute nothing.
- Ranking: documents with score > 0, sorted by score descending, ties by family id ascending; the query's own family
  id is excluded; keep top 200 (shorter list only if fewer than 200 documents score > 0).
- B0 is used unchanged (its frozen list; it contains the query's own family for the 43 dev queries whose family is in
  the corpus). Self-exclusion applies to BM25 only.

## Systems
- B0 (frozen dense top-200)
- BM25 (top-200, above)
- RRF(B0, BM25): `paper1_analysis.rrf_fuse` (read only), k = 60, depth 200, ties -> better B0 rank, then family id.
- U400: union of B0 top-200 and BM25 top-200 (B0 order, then BM25 families not already present). Descriptive
  exposure upper bound only (pool 400, not a fixed-200 system); reported as Recall@400 and exposure only.

## Metrics
- Frozen native evaluator: `native_dev_task` + `evaluate_paper1_dev` (ALL/IN/OUT Recall@200, Recall@100, NDCG@10);
  U400 via `evaluate_native_dev(cutoffs=(400,))`.
- Paired per-query deltas vs B0 (BM25, RRF) for each metric and partition: mean delta, wins/losses/ties (|d| <= 1e-12 tie).
- OUT exposure strata vs B0 (`paper1_analysis.exposure_strata`, exposed = Recall@cutoff > 0): BM25@200, RRF@200, U400@400.
- No bootstrap, no significance claim.

## Go / no-go (fixed now)
GO if RRF OUT Recall@200 - B0 OUT Recall@200 >= 0.010 AND RRF IN Recall@200 - B0 IN Recall@200 >= -0.020.
Otherwise NO_GO. Reported as-is; no variants (no other k1/b, tokenizer, fusion k, field weighting or query view).

## Outputs
- Per-query values (contain dev IDs): `../_private_artifacts/healthtech/ptp-paper2-headroom-dev-20261116-v1/` only.
- Public aggregates: `headroom-dev-result.json`, `HEADROOM-RESULT.md` (this folder). CPU metered with
  `scripts/healthtech/meter_local_cpu.py`; receipt `cpu-receipts.jsonl`.
