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

## Phase 1b: corrected re-run of V1–V3 (DRAFT, written 8 Nov 2026, not run; needs owner go-ahead)

These entries repeat V1–V3 with one change: the PatEmbed instruction prefix (`DENSE_QUERY_PREFIX`) is removed from the query text before BM25 tokenisation and before the reranker. The dense encoder still gets the prefix. Every other setting stays exactly as declared above.

- **Code change:**
  - one shared helper strips `DENSE_QUERY_PREFIX` when present;
  - a unit test asserts that no BM25 or reranker query starts with it.
- **Receipts:** record the stripped-query hash.
- **V1b BM25:** V1 on the stripped query.
- **V2b hybrid:** the V1b BM25 scores and the unchanged dense scores. Same λ grid, CV and tie rule as V2.
- **V3b cross-encoder:** V3 on the stripped query.
  - Its raw scores are also written to a private file (one row per query–candidate pair), so that V5 needs no second GPU pass.
  - The ranking rule is unchanged.
- **Scope and measures:** as in phase 1.
- **Estimated time:** about 1 h on the V100. Hybrid takes about 8 min per query view, the reranker about 20 min per view.

## Phase 2 (DRAFT, written 8 Nov 2026, not run; needs owner go-ahead; runs after phase 1b)

Shared settings are as in phase 1: lane X, dev only, the same measures and bootstrap.

- **Primary cell:** query view P, corpus view main.
- **Score fusion:** "fusion" means fused = λ·z_dense + (1 − λ)·z_method.
  - z is per-query over the scored candidates.
  - λ ∈ {0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0}. λ = 1 must reproduce X; λ = 0 is the method alone.
  - λ is chosen by the V2 4-fold CV (same fold hash, ties to the larger λ). The out-of-fold score is the honest estimate.

### V4 — Qwen3-8B pointwise reranker on the X top 30

- **Model:** the local Qwen3-8B already used for briefs (same revision and weights as the P-brief receipts), fp16 on the V100, thinking disabled.
- **Input:**
  - the query is brief P without the prefix;
  - the candidate is its title plus the first 200 words of the abstract.
- **Prompts (frozen now, 2 variants):**
  - **R-neutral:** "Here is a technical problem and a patent. Is this patent relevant prior art for the problem? Answer yes or no."
  - **R-cross:** "Here is a technical problem and a patent, which may come from a different technical field. Does the patent disclose a mechanism or technique that could solve this problem, even if it was made for another field? Answer yes or no."
  - Both use the same system message as the brief prompts.
- **Score:** logsumexp of the "yes"/"Yes" token logits minus logsumexp of the "no"/"No" token logits, at the first answer token. It needs a single forward pass and no generation.
- **Depth:** the top 30 of X, which gives 59,550 pairs per prompt. Ranks 31–200 stay unchanged.
- **Fusion:** z-scores are taken over the top 30. λ and the prompt are chosen jointly by the 4-fold CV over 2 prompts × 7 λ.
- **Run-time rule (fixed now):**
  - First, a smoke test of 300 pairs measures throughput.
  - If both prompts together are projected to take more than 8 h, only R-cross runs, and this is recorded.
  - Rankings are not inspected before that decision.
- **Why:**
  - V3 tests a general topical reranker. V4 tests whether stating the cross-field goal in the prompt changes the ranking.
  - This links to the owner's published reranking paper on prompt sensitivity.

### V5 — V3b reranker scores fused with dense

- Uses the V3b scores saved over the X top 100 and needs no new GPU pass.
- Fusion as defined above, with z-scores over the top 100.
- **Why:** V3 alone replaces the dense order. V5 tests whether the reranker adds a complementary signal instead.

### V6 — function-channel fusion

- **Generation:** the existing frozen prompt `FUNCTION` (`ptp-solution-scout-v1`, in `run_qwen_scout_actions.py`), with brief P as input, greedy decoding.
  - It produces one function text per dev query. A failed or short output scores as X for that query, with no retries.
- **Retrieval:** the function text is encoded by PatEmbed with the prefix and searched in lane X.
- **Fusion:** with the P dense scores over the union of both top-1000 lists, as defined above.
- **Prior evidence:** on DAPFAM dev, function texts alone retrieved less than the plain brief (OUT R@200 about 0.19 vs 0.29 in the lane; [scout feasibility audit](../audits/ptp-solution-scout-feasibility-20261105/README.md)). That is why only the fusion is tested here.
- **Estimated time:** about 3.5 h of generation (about 6.3 s per call) plus about 10 min of search.
- **Lowest priority:** V6 is dropped if the owner limits GPU time.

### Approval and implementation notes (8 Nov 2026, written before any phase-1b or phase-2 run)

- **Approval:** the owner approved phase 1b and phase 2 on 8 Nov 2026 ("Approve 1b + phase 2"). The DRAFT labels above now read as approved entries.
- **Phase 1b code:** fixed at `14263c9`. The guard refuses to run if any stripped query still starts with `encode query`.
- **CV and λ:**
  - As in V2, λ = 1.0 is a sanity row only and is excluded from the CV choice.
  - Each CV group is one entry: `llm` (both prompts jointly), `cef` (V5) and `fch` (V6).
  - A tie goes to the larger λ, then to the variant listed first, R-neutral before R-cross.
- **V4:**
  - SDPA attention, fp16, batch 16, left padding, one forward pass per pair.
  - The answer words must each be a single token; the run stops otherwise.
  - The smoke test (300 pairs) runs on dev pairs. Its scores are not analysed.
- **V5:** also runs on query view T, because the V3b scores exist for T. P/main stays primary.
- **V6:** the λ grid includes 0, the function channel alone. A query whose function text fails scores as X.
- **Code:**
  - `run_mtm_rerank_llm.py` (V4 scores);
  - `run_mtm_fusion.py` (V4/V5 fusion);
  - `run_mtm_hybrid.py --channel-queries` (V6);
  - `run_qwen_scout_actions.py generate --actions F` (V6 text);
  - `analyze_mtm_methods.py --cv-prefix llm,cef,fch`.
- **Job script:** `docs/healthtech/audits/ptp-medtech-tm-dev-phase2-20261108/run_dev2.sh`.

### Carry-forward rule for phases 1b and 2 (fixed now)

- A method is eligible if its CV out-of-fold Δ hit@20 on P/main has a 95% lower bound > 0.
- If more than 4 are eligible, the 4 with the largest out-of-fold Δ are carried.
- The test read happens once, after the owner freezes the list (rules §14). Each test method uses its full-dev λ and prompt choice.

### Not yet run (later phases, each needs its own entry before running)

- dev-supervised PatEmbed adaptation. It needs a dev/test target-overlap check first, which reads test target IDs, so it needs separate owner approval;
- ColBERTv2 late interaction (no library installed on dr-train);
- per-grant-year and CPC-section breakdowns (descriptive, dev).

## Results

Each result is appended here with its audit link once its run ends.

### Phase 1 (V1–V3), run 8 Nov 2026 04:35Z–05:35Z, code `2feec03`

[Audit](../audits/ptp-medtech-tm-dev-phase1-20261108/README.md). Every step exit=0, with no retries. λ = 1.0 reproduced the baseline exactly. Settings were as declared above.

The table shows query view P, corpus view main, hit@20, as method − X with a 95% bootstrap CI. X = 0.180.

| Entry | Δ hit@20 | new@100 / lost@100 | Outcome |
|---|---|---|---|
| V1 BM25 | −0.143 [−0.160, −0.126] | 0.013 / 0.255 | negative |
| V2 hybrid, CV out of fold (λ 0.9 in all 4 folds) | +0.005 [−0.004, +0.014] | 0.021 / 0.011 | null |
| V3 bge-reranker-v2-m3, top 100 | −0.036 [−0.052, −0.021] | 0 / 0 by design | negative |

Other views:

- **T/main:** V2 CV +0.006 [−0.004, +0.016]; V3 −0.005 [−0.017, +0.008].
- **V2 CV on T in the small, matched and uniform views:** the lower bound is above 0. These are not primary.

No phase-1 entry meets the §9 bar on the primary view. Carrying any of them to test needs an owner decision.

**Correction (8 Nov 2026, after the results above were pushed):** V1–V3 are **defective**.

- **The defect:** the stored query text begins with the PatEmbed instruction `encode query for different document retrieval: `. BM25 tokenised that prefix, and the reranker read it. For example, the title query "Intravenous stand" became 7 BM25 tokens, 5 of them from the prefix.
- **Status:** the results stay on record, but they are not valid tests of the declared methods and are **not eligible for carry-forward**.
- **Owner decision:** the owner chose not to carry phase 1 to test (8 Nov 2026), before this defect was found.
- See the phase-1b entries below.

### Phase 1b (V1b–V3b, query prefix stripped), run 8 Nov 2026 05:51Z–06:51Z, code `14263c9`

[Audit](../audits/ptp-medtech-tm-dev-phase1b-20261108/README.md). Every step exit=0, with no retries. λ = 1.0 reproduced the baseline exactly.

The table shows query view P, corpus view main, hit@20, as method − X with a 95% bootstrap CI. X = 0.180.

| Entry | Δ hit@20 | new@100 / lost@100 | Outcome |
|---|---|---|---|
| V1b BM25 | −0.136 [−0.153, −0.119] | 0.016 / 0.246 | negative |
| V2b hybrid, CV out of fold (λ 0.8, 0.9, 0.9, 0.9) | +0.002 [−0.008, +0.011] | 0.025 / 0.016 | null |
| V3b bge-reranker-v2-m3, top 100 | −0.027 [−0.043, −0.013] | 0 / 0 by design | negative |

Secondary result, query view T: V2b CV gives +0.014 [+0.008, +0.021] on main. Its lower bound is above 0 in all 4 corpus views. T is not the primary view.

Under the fixed rule, no phase-1b entry is eligible for carry-forward.
