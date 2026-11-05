# Protocol draft: organization-adaptive agentic acquisition for cross-domain patent prior-art exposure (DAPFAM)

- Protocol ID: `ptp-org-adaptive-xdomain-protocol-v0-draft`
- Written: 2026-11-05 (UTC+7). **Status: DRAFT, NOT FROZEN.** No acquisition policy or LLM action has been scored. The frozen version (`v1`) is committed with the Stage 2 freeze file before any test-split scoring.
- Study type: solo, reproducible computational study. There are no human assessors, no recruited users and no paid inference. "Organization" means a simulated organization defined from public patent metadata (Section 6). It is never a customer, a user study or a business validation.
- Companion documents:
  - [PoC plan](ORG_ADAPTIVE_POC_PLAN_20261105_EN.md)
  - [manuscript writing plan](ORG_ADAPTIVE_MANUSCRIPT_PLAN_20261105_EN.md)
- Terminology: this study uses only the neutral terms defined here. See the manuscript plan, §4.

## 0. Owner decisions (2026-11-05)

| ID | Decision |
|---|---|
| D1 | This study is written as a new, self-contained manuscript. The owner's earlier unpublished analyses on DAPFAM are superseded and are not cited or named. Only one WPI manuscript goes forward. |
| D2 | Simulated organizations are IPC sections A–H (Section 6). |
| D3 | The fixed baseline is the strongest dense passage retriever available: PatEmbed-large passages (Section 5). |
| D4 | Where Stage 0 shows that the conventional single-window setup can be improved, the improvement is adopted immediately as an additional **fixed** candidate. This happens before any method is scored, and the dev split then picks the fixed baseline F\*. |

## 1. Motivation

| Evidence | Finding used here | Status |
|---|---|---|
| Srihangpiboon & Ploysuwan (IEEE, published; cited as prior work) | Reranking instructions had near-zero mean effects on DAPFAM cross-domain nDCG@100. Only a minority of frozen top-100 pools contained any known cross-domain relevant family. | Published aggregates |
| Patent-to-Pilot Track A (this repository, frozen tests) | The best fixed ranking policy depends on task granularity. On PAR4PC, dense beat BM25 and fusion hurt; on PI4PC, dense did not beat BM25 and fusion helped. | `docs/healthtech/audits/ptp-wpi-research-package-20261104/` |
| This repository, BM25 diagnostic | BM25 over title+abstract reaches strict-OUT macro Recall@100 of 0.0834 over 905 queries. | `results/healthtech/ht-dapfam-bm25-20261030-r3/summary.json` |
| This study, Stage 0/1 (to be measured) | How many judged cross-domain relevant families never enter a strong dense Top-200 pool, and how much reordering alone could recover | `docs/healthtech/audits/ptp-org-adaptive-stage0-20261105/` |

Working hypothesis: in cross-domain prior-art search, most remaining error comes from relevant families that never enter the candidate pool, and no single fixed retriever is best everywhere. The study therefore targets **candidate acquisition**, not reranking.

## 2. Related work and novelty boundary

This is a quick scan (2026-11-05), not a systematic review. Rerun it before the manuscript and record it in `RELATED_PAPERS.md`.

| Work | What it already covers | What this study must not claim |
|---|---|---|
| DeepRetrieval (arXiv 2503.00223) | RL-trained query rewriting with a retrieval-metric reward | That RL query rewriting is new |
| arXiv 2510.17139 | On-policy RL for direct query rewriting often gives limited gains | RL rewriting as the main contribution. RL is optional (Stage 4). |
| PatEx-Gym (arXiv 2610.33503) | Agentic prior-art search over 1M+ patents with an SFT-trained 4B agent | That agentic patent search is new |
| PatentAgentBench (arXiv 2610.35031) | Agent evaluation on eight patent tasks | — |
| MBA-RAG, Adaptive-RAG, Retriever Portfolios, RAGRouter-Bench baselines | Per-query routing and bandit selection among retrieval strategies | That bandit or router selection is new in general |
| CPC-aware LLM query expansion (Springer 2026) | LLM paraphrase expansion for patents; Recall@50 rose from 0.47 to 0.48 | That LLM expansion for patents is new |
| DAPFAM (Ayaou et al.) | IN/OUT partition by IPC3; BM25, dense and RRF baselines | — |

**Claimed gap, to be re-verified:** no work found that evaluates adaptive, cost-accounted candidate acquisition aimed at **cross-domain (IPC3-disjoint) exposure** at an equal candidate budget, with policies adapted to an organization's technology profile.

## 3. Data and rights

- DAPFAM, `datalyes/DAPFAM_patent`, revision `a59a74ce31384165065af1823a83c6f94ccafd48`. License CC BY-NC-SA 4.0: non-commercial research only.
- 1,247 query families, 45,336 target families and 49,869 relation rows. Positive rows: 19,736 IN and 5,193 OUT. 905 queries have at least one strict-OUT positive.
- Local copies (git-ignored): `methodology/datasets/research-only-nc/`. Stage 0 checked their SHA-256 values.
- Share-alike applies to derived data. Generated query texts and per-query outputs stay in `_private_artifacts/`. Git holds only aggregates, hashes and code.
- Unlisted query–target pairs are **unjudged, not negative**.
- Models (pinned):
  - PatEmbed-large `2d5c0f92…` (CC BY-NC-SA 4.0);
  - Qwen3-8B `b968826d…` (Apache-2.0);
  - multilingual-e5-base.
- **Prior exposure, declared:** baseline retrievers have previously been run on all 1,247 queries, by this repository's BM25 diagnostic and by the owner's earlier unpublished work. No acquisition policy or LLM action in Section 5 has been scored on any query.

## 4. Split (Stage 0, done)

1. Build connected components of queries that share any positive target family (IN or OUT).
2. Every component with ≥ 50 queries goes to dev, because one large cluster in test would dominate the component bootstrap. Stage 0 found 526 components; the largest has 374 queries spanning all eight sections, and the next has 51. This rule was added after component sizes were seen and before any method was scored.
3. Shuffle the remaining components with seed `20261105`, within the majority first-IPC section of their queries. Move components to dev until each section's dev query count (large components included) reaches one third.
4. Result: dev 474 queries (349 OUT-eligible) and test 773 queries (556 OUT-eligible). The split file is private; its SHA-256 is in `docs/healthtech/audits/ptp-org-adaptive-stage0-20261105/stage0-split-inputs.json`.

## 5. Actions, policies and budget

Each action returns a ranked list of target families. A policy chooses actions per query and merges their lists into one pool of **B = 200 unique families**. The merge interleaves the chosen lists round-robin by rank and drops duplicates. Every policy gets the same B.

| ID | Action | LLM calls |
|---|---|---:|
| R1 | BM25 over title + abstract + claims | 0 |
| R2 | Dense passage retrieval. PatEmbed-large with its `retrieval_OUT` prompt pair; 384/64-term title+abstract+claims passages; MaxP family score. The query is encoded as **one 512-token window**. | 0 |
| R2w | Same as R2, but the query is cut into 384/64-term windows. The passage score is the maximum over windows, then MaxP over passages. Added under D4: Stage 0 found that 1,187 of 1,247 queries exceed 512 tokens (median 1,309), so R2 drops 71% of query tokens. | 0 |
| R3 | RRF(R1, best of R2/R2w on dev), k = 60 | 0 |
| Q1 | **Functional abstraction.** Qwen3-8B rewrites the problem and mechanism without field-specific vocabulary; the text is retrieved with the dense retriever and BM25 and fused. | 1 |
| Q2 | **IPC-shift.** Qwen3-8B proposes up to 3 IPC3 classes outside the query's own codes; retrieval with the Q1 text is restricted to corpus families carrying those codes. | shared with Q1 |
| Q3 | Pseudo-document: Qwen3-8B writes a hypothetical earlier abstract from another field, retrieved with the dense retriever | 1 |

Prompt version `ptp-org-adaptive-qwen-actions-v1` is in `scripts/healthtech/run_qwen_query_actions.py`. v1 replaced v0 after the Stage 0 canary: under v0, IPC-shift returned unusable codes for 19 of 20 queries. Prompts are frozen in Stage 2. Decoding is greedy. Every generation records its input and output hashes, tokens, latency and failures; a failed generation contributes an empty list, and there are no retries.

**Policies compared:**

| ID | Policy |
|---|---|
| F\* | Best single fixed action among R1, R2, R2w and R3 on dev (the fixed baseline) |
| M\* | Best fixed mix of actions on dev; it may include Q actions |
| π-global | Contextual-bandit policy trained on all dev queries |
| π-org | Same policy class, trained only on one simulated organization's dev queries |
| Oracle | Per-query best action set using test labels. An upper bound only, never a method. |

Policy features are label-free:
- query length in tokens and windows;
- number and sections of IPC3 codes;
- BM25 top-1/top-2 margin;
- R1/R2 overlap@50;
- the share of dense top-50 candidates whose IPC3 set is disjoint from the query's.

Reward on dev = new strict-OUT positives added to the pool − λ × Qwen calls, with λ chosen by the rule in Section 8.

**Guard against gaming the label definition.** OUT means IPC3-disjoint, and Q2 deliberately searches disjoint classes. All-positive (IN + OUT) Recall@200 is therefore a mandatory non-inferiority check (H-G), and IN and OUT exposure are always reported side by side.

## 6. Simulated organizations

- An organization is the set of queries whose first-listed IPC3 code falls in one IPC section, A–H (up to 8 organizations).
- A demonstration organization, "cardiovascular-device", is defined as queries whose first-listed IPC3 is A61. It supports the PoC and is reported descriptively.
- The profile is the organization's IPC3 frequency vector, computed from its dev queries only.
- An organization with fewer than 30 OUT-eligible test queries is reported descriptively, not inferentially.

## 7. Research questions and hypotheses

- **RQ0 (exposure diagnosis, descriptive).** For the fixed baseline F\*, what share of judged strict-OUT pairs is absent from the Top-200 pool, and how much macro Recall@100 could ideal reordering of that pool recover?
- **RQ1 (acquisition).** Do LLM cross-domain actions increase strict-OUT exposure at an equal candidate budget?
  - H1: M\* − F\* on macro strict-OUT Recall@200 > 0.
- **RQ2 (adaptivity).**
  - H2: π-global − F\* > 0, with Qwen call rate < 1.
  - H2b (tolerance check, not equivalence): lower 95% bound of π-global − M\* ≥ −0.01.
- **RQ3 (organization context).**
  - H3: pooled over test queries, π-org − π-global > 0.
- **Guard H-G.** For π-global and M\* vs F\*, the lower 95% bound of the all-positive Recall@200 difference is ≥ −0.02.
- **RQ4 (cost, descriptive).** Qwen calls, tokens, GPU-seconds and latency per query; the exposure–cost frontier.

**Primary endpoint:** macro strict-OUT Recall@200 over OUT-eligible test queries.

**Secondary endpoints:** strict-OUT Recall@100 and hit-rate@200; all-positive and IN Recall@200; nDCG@100 of the merged pool; per-organization results.

## 8. Staged plan with stop rules

| Stage | Work | Gate to continue |
|---|---|---|
| 0 (**done, PASS**; [audit](../audits/ptp-org-adaptive-stage0-20261105/README.md)) | Hash check; split; model and license records; pooling equivalence check against SentenceTransformer; dense Top-200 pools for R2 and R2w; internal consistency check of R2 against the owner's earlier run (not reported); 20-query Qwen canary on dev | Hashes match; pooling equivalent; canary failure rate ≤ 5%. R2w (max and mean) was lower than R2 on every dev endpoint, so R2 stays the dense candidate. Prompt v1 replaced v0 after v0's IPC-shift failed. |
| 1 | Run every action on dev. Compute F\*, M\* and the dev oracle. | **Headroom gate:** dev oracle − F\* ≥ 0.03 strict-OUT Recall@200, **and** Q actions contribute ≥ 10% of the unique OUT positives found by any action. If either fails, stop, report it as a diagnostic finding and do not open test. |
| 2 | Train π-global and π-org on dev with 5-fold cross-fitting by component. Choose λ as the smallest grid value whose cross-fitted π-global stays within 0.01 of M\*. Freeze prompts, code hashes, selections and λ, and commit **before** test. | Freeze committed |
| 3 | Score all policies on test once. Paired component bootstrap (10,000 resamples, seed `20261105`); Holm adjustment over H1, H2 and H3; H2b and H-G are tolerance checks. | — |
| 4 (optional, separate amendment) | GRPO-LoRA on Qwen3-1.7B or 4B for Q1, rewarded by dev OUT exposure gain; compared with the prompted Q1 under its own freeze | Only if H1 is positive and the owner approves the extra compute |

Non-significant differences are reported as such and never called equivalence. Every policy and action is reported on test, not only the selected ones.

## 9. Compute and cost

- No paid API calls; the E2 ledger is not touched.
- Qwen3-8B runs fp16 on the approved dr-train V100 under the existing cooperative lock.
- Dense passage encoding is one fp32 pass over 188,944 passages; query-window variants reuse those vectors.

## 10. Known limitations, declared before any policy run

- Citation-based qrels are incomplete, and the IPC3-based OUT label is an operational proxy for "cross-domain".
- Simulated organizations are IPC sections, not companies.
- Every DAPFAM query has been seen by earlier baseline runs (Section 3), and a single benchmark limits external validity.
- LLM-generated queries may encode Qwen's pretraining knowledge of the cited patents; contamination cannot be ruled out.
- Exposure is necessary but not sufficient: an exposed family still has to be ranked and read.
- 10.1% of dense passages exceed 512 tokens, which drops 4% of passage tokens; passage-side truncation is kept as is and reported.
