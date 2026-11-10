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

### Phase 2 (V4–V6), run 8 Nov 2026 06:55Z–11:53Z, code `2691931`, PROMPTS=N,C

[Audit](../audits/ptp-medtech-tm-dev-phase2-20261108/README.md). Every step exit=0, with no retries. λ = 1 reproduced the baseline head for 1,985/1,985 queries in every fusion. V6 generation failed for 4 of 1,985 queries, which were scored as X.

The table shows query view P, corpus view main, hit@20, as method − X with a 95% bootstrap CI. X = 0.180.

| Entry | CV choice | Δ hit@20, out of fold | Outcome |
|---|---|---|---|
| V4 Qwen3-8B yes/no, top 30, fused | R-neutral λ 0.5 in all 4 folds | **+0.017 [+0.010, +0.025]** | **eligible** |
| V5 bge reranker fused with dense | λ 0.7, 0.6, 0.7, 0.6 (full dev 0.6) | +0.007 [−0.001, +0.015] | not eligible |
| V6 function channel fused with P | λ 0.9 in all 4 folds | −0.003 [−0.007, +0.002] | not eligible |

Results without fusion:

- V4 R-neutral alone: +0.012 [+0.003, +0.020].
- V4 R-cross alone: +0.003 [−0.007, +0.013].
- V6 function channel alone: −0.081.

Secondary result: V5 on T/main gives +0.015 [+0.008, +0.023].

**Carry-forward candidate (needs the owner's freeze):** V4 with R-neutral, X top 30 and λ 0.5. It is the only eligible method, so Holm needs no adjustment.

## Phase 3 (owner approved 9 Nov 2026, after the [phase-3 audit](../audits/ptp-medtech-tm-phase3-audit-20261109/README.md))

Each entry below is written before its run. Later phase-3 entries (cited-distractor view, 3c, 3d, DAPFAM) get their own detailed entries before they run.

**Shared settings:** as in phase 2 (dev only; lane X; P primary, T secondary; 4 corpus views). There are two new measures:

- **hit@200**;
- **new-gold@200 / lost-gold@200** against X's top 200.

A first-stage method counts as changing exposure only if hit@100 or hit@200 changes, not just hit@20.

### 3a — dense vector PRF (Rocchio) in lane X

- **Base:** the frozen dense X retrieval: PatEmbed-large MaxP, the reused passage vectors, and the same `keep_mask`.
- **Feedback:**
  - For each query, take the first k families of its own X ranking in each corpus view.
  - The feedback vector of a family is its best-matching passage vector for the query (the MaxP winner).
  - c_k is the mean of those k vectors.
- **New query:** q' = normalise(w·q + (1 − w)·normalise(c_k)), where q is the normalised query vector.
- **Second pass:** a full MaxP lane-X retrieval with q' under the same `keep_mask`, depth 200.
- **Grid:** k ∈ {3, 5, 10} and query weight w ∈ {0.7, 0.8, 0.9}, so α = 1 − w ∈ {0.3, 0.2, 0.1}.
  - Variant names are `prfK<k>-<w>`.
  - w = 1.0 (`prfK0-1.0`) is the sanity row: it must reproduce X exactly and is excluded from the CV.
- **CV:** the 4-fold CV jointly over all 9 variants (prefix `prf`). A tie goes to the larger w, the one closer to X, then to the smaller k (listed first).
- **Eligibility:** the usual CV out-of-fold lower bound > 0 on P/main hit@20, **and** hit@100 or hit@200 must differ from X.
- **Code:** `scripts/healthtech/run_mtm_prf.py`.
- **Evidence:**
  - vector PRF is training-free (Li et al., TOIS 2023);
  - it is sensitive to feedback quality (Li et al., SIGIR 2022);
  - no patent study exists.

### 3b — citation-reuse gating probe (BigQuery; dev labels only; no method claim)

- **SQL:** `scripts/healthtech/sql/tm06_device_sea_citation_edges.sql`.
  - **Citing grants:** US B1/B2 grants, granted 2001-01-01 to 2016-12-31, with a device CPC subclass (A61B/F/G/H/J/L/M/N).
  - **Edges:** their examiner (SEA) citations to US publications, mapped to cited family IDs. Each edge is (citing family, citing grant date, cited family), deduplicated.
  - **Spend:** dry-run first; the owner's per-query cap applies.
- **Analysis:** `scripts/healthtech/analyze_mtm_citation_probe.py` (CPU, dev only).
  - **Visible edges:** an edge counts for query q only if the citing grant date ≤ T(q), the query's priority date.
  - **Excluded citers:** the query's own family, and all benchmark query families (dev and test). This is the conservative rule planned for 3c.
- **Measures:**
  - (i) **Reach:** the share of dev queries with at least one target cited by a visible device citer. This is an upper bound for unlimited-neighbour citation chasing.
  - (ii) **Co-citation inter-connection:** among queries with two or more targets, the share whose targets include a pair co-cited by one visible device citer. This variant can be computed from these edges; Gobeill et al. used direct target–target citation.
  - (iii) **Popularity null:** rank lane-X corpus families (same `keep_mask`, main view) by the number of visible device-citer citations, with ties by family ID and no query text. Report hit@20/100/200.
  - (iv) **Outside-corpus share:** of the distinct families cited by device grants from 2001–2016, the share that is not in the MTM corpus.
- **Go/no-go for 3c (fixed now):**
  - **Go** only if reach ≥ 48.8% (X hit@200 38.8% + 10 points) **and** popularity-null hit@200 < reach/2.
  - Otherwise 3c is not built, and the probe is reported as a negative feasibility result.

### Decisions recorded on 9 Nov 2026

- **The owner's published reranking paper** will be presented at its conference on 19–21 Nov 2026. It has no DOI yet; cite it as accepted/to appear until one is issued.
- **Data licence:** the owner confirmed it from the repository's dataset table.
  - Google Patents Public Data (`patents-public-data.patents.publications`) is provided by IFI CLAIMS Patent Services and Google under CC BY 4.0. Source: <https://github.com/google/patents-public-data/blob/master/tables/dataset_Google%20Patents%20Public%20Datasets.md#patents-public-datapatentspublications>.
  - Any release must give the attribution, the licence link, the table, the retrieval dates and the modifications.
  - The data licence grants no rights to patented inventions.

### Phase 3b gating probe, run 9 Nov 2026 (BigQuery tm06 plus dr-train CPU analysis at `50eec39`)

[Audit](../audits/ptp-medtech-tm-dev-phase3b-20261109/README.md).

| Measure | Value |
|---|---|
| Reach | 30.3% |
| Co-citation inter-connection | 3.1% |
| Popularity null (hit@20 / @100 / @200) | 0.6 / 2.1 / 3.7% |
| Outside-corpus share | 87.1% |

**Gate: NO_GO.** Reach 30.3% is below 48.8%, so 3c (citation chasing) is not built.

The popularity null is far below X, so the corpus enrichment is not trivially exploitable.

### Phase 3a PRF, run 8–9 Nov 2026 23:49Z–00:22Z, code `a29610b`

[Audit](../audits/ptp-medtech-tm-dev-phase3a-20261109/README.md). Every step exit=0, with no retries. prfK0-1.0 reproduced X exactly.

- **P/main, CV out of fold** (k10, w 0.9 in all 4 folds): Δ hit@20 −0.003 [−0.008, +0.003]; hit@200 0.383 vs 0.388.
- **Every variant** lowers hit@20 and hit@200, and loses more targets at depth 200 than it gains. **Negative; not eligible.**
- **T/main, CV:** +0.005 [−0.001, +0.011] (secondary).

## R1-PARITY-P-MAIN-v1 — 10 Nov 2026

Status: DECLARED_PENDING_ISOLATION_AND_INPUT_PINS; NOT_RUN. Integrity comparison only, not a new candidate method. See [fixed declaration](MTM_DEV_BASELINE_PARITY_DECLARATION_20261110_EN.md). Exact original P-dev bytes, full cohort, main/X and main/U, depth 200, batch 64, original MaxP/prefix/topk and bound vector reuse. Require exact ordered equality for every available query; preserve predeclared missing ledger, failures and all attempts. No test, re-encoding, tuning or automatic retry. Actual source/input/environment pins and isolated curator handoff required before launch.

## SYN-SACR-001 — 10 Nov 2026

DECLARED_NOT_RUN: synthetic engineering smoke only, not R3/dev research. Fixed authored liquid-flow input, at most profile/generic/selective calls (selective contingent on structurally usable profile), no retries, local fp16/eager Qwen, 8192/4096 input/output token caps, 900s soft / 1200s supervisor deadline. [Full declaration](../audits/ptp-method-first-r2-smoke-20261110/README.md). No benchmark or protected data; actual R1 gates remain open.

### SYN-SACR-001 observed outcome
Completed 10 Nov, 01:09:47Z–01:11:37Z, code c9c37d01f6f3472ad614aead719cb81b07cb7a37. Two calls; profile EOS complete but invalid source spans (seven mismatches); generic response structurally valid; selective skipped. Zero retries or output repair. Peak allocated16.67GB/reserved17.79GB, total108.552s. Engineering loading works for this short synthetic input; profile contract fails. No benchmark/retrieval outcome or semantic validation. See smoke audit result.json. Any changed profile protocol must have a new version/declaration before a new attempt.

## SYN-SACR-002 — quote-profile-v1 engineering regression

DECLARED_NOT_RUN. Same authored fixture as known regression, not independent validation; new quote-profile prompt/adapter, max two calls (profile_quotes, conditional selective), no generic rerun or output repair. All model/decode/resource limits fixed as SYN-SACR-001. [Declaration](../audits/ptp-method-first-r2-quote-smoke-20261110/README.md). Prior failure remains. No benchmark/label access, R3 pilot or implicit further tuning.

### SYN-SACR-002 observed outcome
10 Nov01:18:52Z–01:20:05Z, code47958726a80c715eda52f76031d368b9e1fdb05c. One call681/344 tokens, EOS complete but JSON syntax error (comma delimiter character898); quote alignment not reached, selective skipped. No salvage/retry. Runtime71.66s, peak allocated16.65GB/reserved17.73GB. This is a second preserved engineering failure, not retrieval evidence. Assess structured-output feasibility before any further declared model attempt.


### 2026-11-10 08:28:17 Bangkok — CPU JSON grammar feasibility (not a retrieval experiment)

Five authored token-sequence expectations matched with installed Qwen tokenizer and
lm-format-enforcer0.11.3; small quote schema only. Invented quote accepted, confirming
format constraints do not ensure grounding. No model calls/weights or benchmark data.
See ../audits/ptp-method-first-r2-json-grammar-20261110/README.md and
SACR_STRUCTURED_OUTPUT_PLAN_20261110_EN.md for the bounded next engineering gate.
No third model attempt declared or launched. Earlier failures remain unchanged.


### 2026-11-10 08:32:30 Bangkok — Full-schema CPU gate FAILED

Full quote-profile grammar and46 local tests passed. Independent JSON Schema8/8
expected cases; actual Qwen token filter7/8. Unicode fixture rejected at first Thai
character260; token filter permits EOS at token109 despite incomplete JSON. Original
receipt preserved; character diagnostic localizes failure. No model calls/weights
or benchmark data. See ../audits/ptp-method-first-r2-full-schema-20261110/README.md.
No SYN-SACR-003 declaration or launch. Inspect alphabet/dead-end and fail-closed
configuration before a separately versioned CPU check. Prior failures unchanged.


### 2026-11-10 08:36:07 Bangkok — Grammar dead-end diagnosis and prospective guard

Installed source confirms92-character default alphabet and ForceStopParser/EOS
fallback paths. Added complete-JSON/schema EOS guard and finite vocabulary/source
alphabet builder;39 targeted local tests and lint pass. Actual configured integration
NOT_RUN; no model calls. Next separately versioned CPU integration before any third
model declaration. See ../audits/ptp-method-first-r2-grammar-guard-20261110/README.md.
Prior failed receipts unchanged; actual-data and semantic gates remain.


### 2026-11-10 08:39:38 Bangkok — Configured full-schema CPU v2 FAILED

Explicit alphabet/config and EOS guard, committed module base11d7a164f6c2a7217ddea2e13565c4c6121a1caf.
Tokenizer8/10 vs independent JSON Schema10/10. Two combined escape-token failures;
character parser accepts both full strings. No premature EOS observed; null-only
passes. No model calls. Freetext optimization is a candidate cause, not established.
See ../audits/ptp-method-first-r2-full-schema-v2-20261110/README.md.
Next bounded identical-prefix diagnostic; no generation integration or third smoke.


### 2026-11-10 08:43:55 Bangkok — Bounded shortcut diagnostic timeout

Identical character-state default/no-shortcut comparison exceeded120s without
completed output. RemotePID2966698 terminated after identity verification, then
/proc absence verified. No retry or model call. Cause not proven; no viable
generation decoder established. Preserve v2 failure and timeout receipt. Stop
automatic grammar/model attempts; continue independent semantic/R6 preparation.
Audit ../audits/ptp-method-first-r2-full-schema-v2-20261110/README.md.


### 2026-11-10 08:47:30 Bangkok — Fidelity policy proposal and manuscript material

Proposed source-first batch fidelity gate; no observations/adoption. Human review
must not silently filter automatic retrieval outputs. Working method-first manuscript
material leaves results/novelty/reference verification and R6 incomplete. Nine links
resolve and claims trace to current audits. No experiment or protocol amendment.
See ../audits/ptp-method-first-r2-fidelity-r6-draft-20261110/README.md.
Next independent synthetic acquisition/controls contract; actual R1/generation gates remain.


### 2026-11-10 08:50:45 Bangkok — Synthetic full-index acquisition package

CPU chunked float32 MaxP, common eligibility, globally stable tie cutoff, union
and anchor scores implemented;33 acquisition/selector tests and lint pass.
Historical GPU baseline unchanged. Real index binding/parity and resource feasibility
NOT_RUN; no benchmark/model/GPU access. See ../audits/ptp-method-first-r2-acquisition-20261110/README.md.
Next component-passage binding and matched controls; no R3 declaration implied.


### 2026-11-10 08:54:15 Bangkok — Pre-embedded factorial integration

G/G,G/L,I/G,I/L share anchor/index/mask/component profile with separate acquisition
unions and same ordered passages per family. Order/owner digest fails before search.
44 synthetic tests and lint pass. Vector/text provenance, embedding/generation,
fallback/full cost and actual parity remain open. No experiment or protected access.
Audit ../audits/ptp-method-first-r2-factorial-20261110/README.md.


### 2026-11-10 08:57:16 Bangkok — Source-bound component compiler/receipt package

Validated source/profile rows, explicit-condition-only conjunction and exact
plan/row/encoder/vector-byte binding implemented.43 targeted tests/lint pass;
actual encoder execution and semantic fidelity not established. No model/data
run. Failed/review plans remain explicit, not silently removed.
Audit ../audits/ptp-method-first-r2-components-20261110/README.md.
Next per-query failure/fallback and complete accounting; real R1/generation gates remain.


### 2026-11-10 09:00:34 Bangkok — Outcome/cohort and cost utilities

Missing/fallback denominator preservation, stop-on-review/retrieval-failure and
unknown-preserving actual-operation cost summaries implemented.36 tests/lint pass.
External durable attempt/event reconciliation and complete controller remain open;
no real cost or relevance measurement. No data/model run.
Audit ../audits/ptp-method-first-r2-outcomes-20261110/README.md.
Next reconciliation and full R0–R6 evidence audit; no completion claim.


### 2026-11-10 09:04:16 Bangkok — Full readiness audit and conditional freeze proposal

31 checklist +6 package requirements mapped; overall INCOMPLETE, not ready R3/R5.
SACR has no R3/R4 outcome and is not eligible for nomination; this is not a
negative scientific result. Conditional four-total-system panel proposal is not
freeze/approval. No test or model execution.
Audit ../audits/ptp-method-first-readiness-20261110/README.md.
Next expected-run/reservation/event reconciliation and offline controller.


### 2026-11-10 09:07:05 Bangkok — Dev run-record reconciliation

Expected dev manifest/slot, terminal attempt, cost-event and cohort reconciliation
implemented;27 tests/lint pass. No automatic nonterminal-to-interrupted conversion,
no retry slots, no skipped costs. Actual receipt byte loading/controller remain open.
No model/data run. Audit ../audits/ptp-method-first-r2-reconcile-20261110/README.md.
Next durable synthetic controller; actual R1/generation/fidelity gates unchanged.


### 2026-11-10 09:12:05 Bangkok — Durable stage journal and offline integration

Exclusive reserved stages, sealed output/receipt/event files and byte-checked
reconciliation implemented.36 focused and181 full SACR tests pass;9 journal tests
rechecked after fixture-ID alignment. Authored profile/views and injected embeddings,
actual CPU kernels only;0 model calls. Not production controller or actual resource
proof. Audit ../audits/ptp-method-first-r2-journal-20261110/README.md.
Next primary prior-art boundary and actual input/controller gates; no new model attempt.
