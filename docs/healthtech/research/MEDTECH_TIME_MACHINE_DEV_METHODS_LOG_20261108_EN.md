# MTM dev methods log (rules §8: every variant tried on dev is logged)

- **Status:** OPEN (dev only). Test is sealed.
- **Rules:** [MEDTECH_TIME_MACHINE_BENCHMARK_RULES_DRAFT_20261107_EN.md](MEDTECH_TIME_MACHINE_BENCHMARK_RULES_DRAFT_20261107_EN.md), frozen at `7d317e7`.
- **Baseline:** the frozen dense X lane. See the [dev audit](../audits/ptp-medtech-tm-dev-20261107/README.md). Main view, query view P: hit@20 0.180, hit@100 0.313.
- **Carry-forward limit:** at most 4 methods go to the single test read. A method claim needs method − X on hit@20 with a lower bound > 0 after Holm correction across the carried methods (rules §9).

Each entry below is written **before** its dev run. Settings are not changed after its results are seen; a change becomes a new entry.

## Phase 1 (owner approved 8 Nov 2026, after a Deep Research review of candidate methods)

These settings are shared by every phase-1 entry.

- **Lane and queries:** all candidates in lane X use the same rules as the baseline: the publication-date time filter, the own family removed, and families sharing a CPC3 with the query removed (`keep_mask` from `run_mtm_dense_pool.py`).
- **Views reported:** query views P (primary) and T; all 4 corpus views (main is primary).
- **Measures:** hit@20 (primary), hit@100 and MRR@100.
- **new-gold@100:** the share of queries whose baseline X top 100 had no target but the method's top 100 does. **lost-gold@100** is the reverse.
- **Contrast:** method − X on hit@20, paired query bootstrap, 5,000 resamples, seed `20261107`.
- **Code:**
  - `scripts/healthtech/run_mtm_hybrid.py` (V1, V2);
  - `scripts/healthtech/run_mtm_rerank_ce.py` (V3);
  - `scripts/healthtech/analyze_mtm_methods.py` (refuses `--split test`).
- **Labels:** none of the run scripts read labels.

### V1 — BM25 in lane X

- **Text and tokens:** title + abstract + claims per family. Tokens are lowercase `[a-z0-9]+` of length ≥ 2, minus the Lucene English stopword list (33 words). There is no stemming and no patent-specific stopwords.
- **Scoring:**
  - BM25 with k1 = 0.9 and b = 0.4 (Pyserini defaults).
  - idf = ln(1 + (N − df + 0.5)/(df + 0.5)).
  - Each query term counts once.
  - Ties are broken by family ID, as in the baseline.
- **Question:** does lexical matching reach targets the dense lane misses (new-gold@100)?

### V2 — score-calibrated BM25 + PatEmbed hybrid in lane X

- **Candidates:** the union of the dense X top 1,000 and the BM25 X top 1,000.
- **Scoring:**
  - Each score is z-normalised over that union for each query.
  - fused = λ·z_dense + (1 − λ)·z_bm25, for λ ∈ {0.5, 0.6, 0.7, 0.8, 0.9}.
  - λ = 1.0 is also written as a sanity check: it must reproduce the baseline X order.
- **λ selection:**
  - Use 4-fold cross-validation on dev. A query's fold is the first 8 hex digits of sha256(query id), mod 4.
  - In each fold, pick the λ with the best mean hit@20 on the other 3 folds. On a tie, take the larger λ, the one closer to the baseline.
  - The honest dev estimate is the out-of-fold hit@20.
  - The λ for a possible test freeze is the full-dev argmax under the same tie rule.
- **Why not RRF:** fixed RRF fusion was negative in the earlier preregistered Track A test.

### V3 — zero-shot cross-encoder rerank of the baseline X top 100

- **Model:** `BAAI/bge-reranker-v2-m3` (Apache-2.0), revision `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, downloaded to dr-train on 8 Nov 2026. The weight sha256 goes in the receipt.
- **Input:**
  - the query text paired with the candidate's `title. abstract`;
  - max length 512 tokens;
  - fp16 on the V100;
  - the score is the single logit.
- **Ranking:**
  - The top 100 are reordered by score; ties keep the baseline order.
  - Ranks 101–200 stay unchanged, so hit@100 equals the baseline by construction.
- **Scope:** corpus view main only, query views P and T. The sensitivity views follow only if V3 helps on main.

### Not yet run (later phases, each needs its own entry before running)

- a Qwen3-8B reranker with a small frozen prompt family (the Paper 53 prompt-sensitivity link);
- a function/mechanism query channel;
- ColBERTv2 late interaction;
- dev-supervised PatEmbed adaptation. This one needs a dev/test target-overlap check first.

## Results

Each result is appended here with its audit link once its run ends.
