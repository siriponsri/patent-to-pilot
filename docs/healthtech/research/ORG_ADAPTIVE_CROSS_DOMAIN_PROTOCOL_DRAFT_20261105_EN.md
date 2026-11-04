# Protocol draft: organization-adaptive agentic acquisition for cross-domain patent prior-art exposure (DAPFAM)

- Protocol ID: `ptp-org-adaptive-xdomain-protocol-v0-draft`
- Written: 2026-11-05 (UTC+7). **Status: DRAFT, NOT FROZEN.** Nothing in this document has been run. The frozen version (`v1`) is committed together with the Stage 2 freeze file before any new method is scored on the test split.
- Study type: solo, reproducible computational study. There are no human assessors, no recruited users and no paid inference. "Organization" means a simulated organization defined from public patent metadata (Section 6). It is never a customer, a user study or a business validation.
- Companion plan: [ORG_ADAPTIVE_POC_PLAN_20261105_EN.md](ORG_ADAPTIVE_POC_PLAN_20261105_EN.md).

## 0. Owner decisions

| ID | Decision | Why it matters |
|---|---|---|
| D1 | **Answered by the owner, 2026-11-05.** `myIS/docs/journal/journal_08` (commit `1f9b89e`, 2026-09-03; a WPI extension of Paper 86) is an older, unsubmitted plan. If this study turns out stronger, it is submitted to WPI **instead of** journal_08. Only one WPI manuscript will go forward. | Prevents two WPI submissions resting on the same DAPFAM exposure findings. Whichever manuscript goes forward must credit the Paper 86 analyses as the authors' own prior work. |
| D2 | **Answered by the owner, 2026-11-05:** Paper 86 was not presented and is confirmed not to be published. Under clause 4 of the signed IEEE form, the copyright transfer is void. Paper 86 analyses may be folded into this work and described as the authors' earlier unpublished analysis. | File the confirmation (e.g. the organizer email) beside the Paper 86 records in `myDegree/IS/IS_2/` before submission. |
| D3 | **Answered by the owner, 2026-11-05:** simulated organizations = IPC sections A–H (Section 6). | Population for RQ3. |
| D4 | **Answered by the owner, 2026-11-05:** R2 reproduces ARM-03, the PatEmbed-large passage pipeline from myIS, as the strongest fixed baseline. | A harder, fairer comparison. Stage 0 must show the reproduction matches Paper 86's strict-OUT Recall@200 of 0.260; any gap is reported. |

## 1. Motivation and lineage

| Prior own work | Finding used here | Evidence status |
|---|---|---|
| Paper 53 (IEEE, published) | Reranking instructions had near-zero mean effects on DAPFAM strict-OUT nDCG@100; only 257 of 692 frozen top-100 pools exposed a known OUT-relevant family. | Reported aggregates; original-run records not recovered. |
| Paper 86 (iSAI-NLP 2026 submission 86; not presented; confirmed unpublished, D2) | For PatEmbed-large passage retrieval (ARM-03), 78.3% of the 5,193 judged strict-OUT pairs are absent from the Top-200 pool. Strict-OUT macro Recall@100 is 0.188, and Recall@200 (equal to the ideal-reordering bound) is 0.260. | 2026 execution receipts; aggregates in `myIS/docs/figures/15_a6_depth_curve.csv` and `19_a7_within_pool_bound.csv`. Not re-run in this repository. |
| Patent-to-Pilot Track A (this repository, frozen tests) | The best fixed ranking policy depends on task granularity. On PAR4PC, dense beat BM25 and fusion hurt; on PI4PC, dense did not beat BM25 and fusion helped. | `docs/healthtech/audits/ptp-wpi-research-package-20261104/` |
| This repository, BM25 diagnostic | BM25 title+abstract strict-OUT macro Recall@100 is 0.0834 over 905 queries. | `results/healthtech/ht-dapfam-bm25-20261030-r3/summary.json` |

The common thread: in cross-domain prior-art search, most of the remaining error comes from relevant families that never enter the candidate pool, and no single fixed retriever is best everywhere. This study therefore targets **candidate acquisition**, not reranking.

## 2. Related work and novelty boundary

This is a quick scan (2026-11-05), not a systematic review. Before the manuscript, rerun the search and record it in `RELATED_PAPERS.md`.

| Work | What it already covers | What this study must not claim |
|---|---|---|
| DeepRetrieval (arXiv 2503.00223) | RL-trained query rewriting with a retrieval-metric reward (PubMed, ClinicalTrials.gov) | That RL query rewriting is new |
| arXiv 2510.17139 | On-policy RL for direct query rewriting often gives limited gains and loses to prompting | RL rewriting as the main contribution. RL is optional (Stage 4) and always compared with prompting. |
| PatEx-Gym (arXiv 2610.33503) | Agentic prior-art search over 1M+ patents, with a 4B agent trained by SFT | That agentic patent prior-art search is new |
| PatentAgentBench (arXiv 2610.35031) | Evaluation of LLM agents on eight patent tasks | — |
| MBA-RAG (COLING 2025), Adaptive-RAG, Retriever Portfolios (2026), RAGRouter-Bench baselines | Per-query routing and bandit selection among retrieval strategies | That bandit or router selection is new in general |
| CPC-aware LLM query expansion (Springer 2026) | LLM paraphrase expansion for patents; Recall@50 rose from 0.47 to 0.48 | That LLM expansion for patents is new |
| DAPFAM (Ayaou et al.) | IN/OUT partition by IPC3; BM25, dense and RRF baselines | — |

**Claimed gap, to be re-verified:** no work found that evaluates adaptive, cost-accounted candidate acquisition aimed at **cross-domain (IPC3-disjoint) exposure** at an equal candidate budget, with policies adapted to an organization's technology profile.

## 3. Data and rights

- DAPFAM, `datalyes/DAPFAM_patent`, revision `a59a74ce31384165065af1823a83c6f94ccafd48`. License CC BY-NC-SA 4.0: non-commercial research only.
- 1,247 query families, 45,336 target families and 49,869 relation rows. Positive rows: 19,736 IN and 5,193 OUT. 905 queries have at least one strict-OUT positive.
- Local copies (git-ignored): `methodology/datasets/research-only-nc/{corpus,queries,qrels_all}.parquet`. SHA-256 values are recorded in `results/healthtech/ht-dapfam-bm25-20261030-r3/manifest.json` and must match in Stage 0.
- Share-alike applies to derived datasets. Qwen-generated query texts derived from DAPFAM text stay private (`_private_artifacts/`). Git holds only aggregates, hashes and code.
- Unlisted query–target pairs are **unjudged, not negative**. Citation-based qrels are incomplete proxies.
- Models:
  - Qwen3-8B, pinned copy on dr-train. The license (expected Apache-2.0) is recorded in Stage 0 from the pinned model card.
  - PatEmbed: CC BY-NC-SA 4.0.
  - multilingual-e5-base.

**Prior exposure, declared:**
- All 1,247 queries have been scored by BM25 (this repository), by ARM-03 (Paper 86) and, for 692 of them, by Paper 53's arms.
- No method defined in Section 5 has been scored on any query.
- Baseline scores seen earlier are not used for selection beyond what Section 8 allows on the dev split.

## 4. Split (Stage 0, label-structure only)

1. Build connected components of queries that share any positive target family (relevance > 0, IN or OUT). This blocks target-family leakage across splits.
2. Stratify components by the section letter of each query's first-listed IPC3 code.
3. Assign components to **dev (≈ 1/3)** and **test (≈ 2/3)** with seed `20261105`.
4. Write the split file, its SHA-256 and component counts to the audit folder before any method runs.

## 5. Actions, policies and budget

Each action returns a ranked list of target families. A policy chooses actions per query and merges their lists into one pool of **B = 200 unique families**. The merge interleaves the chosen lists round-robin by rank and drops duplicates. Every policy gets the same B.

| ID | Action | LLM calls |
|---|---|---:|
| R1 | BM25 over title + abstract + claims | 0 |
| R2 | ARM-03 reproduction (owner decision D4): PatEmbed-large, recipe SP (384/64-term passages, max-p family aggregation), pinned revision from Paper 86. If Stage 0 cannot reproduce it within 0.005 strict-OUT Recall@200, stop and report the gap before choosing a fallback. | 0 |
| R3 | RRF(R1, R2), k = 60 | 0 |
| Q1 | **Functional abstraction.** Qwen3-8B rewrites the query family's problem and mechanism without field-specific vocabulary. The text is retrieved with R2 and R1 and fused. | 1 |
| Q2 | **IPC-shift.** Qwen3-8B proposes up to 3 IPC3 classes outside the query's own codes where the same mechanism may appear. Retrieval with the Q1 text is restricted to corpus families carrying those codes. | 1 (shared with Q1 if batched) |
| Q3 | Pseudo-document (HyDE-style) in patent-abstract style, retrieved with R2 | 1 |

Prompts, decoding (greedy, temperature 0), max tokens and the output schema are written into the freeze file. Each generation records its input hash, output hash, tokens, latency and failures. A failed generation contributes an empty list; there are no retries.

**Policies compared:**

| ID | Policy |
|---|---|
| F\* | Best single fixed action among R1–R3 on dev (the fixed baseline) |
| M\* | Best fixed mix of actions on dev; it may include Q actions |
| π-global | Contextual-bandit policy trained on all dev queries |
| π-org | The same policy class, trained only on dev queries of one simulated organization (Section 6) |
| Oracle | Per-query best action set, using test labels. Reported only as an upper bound, never as a method. |

Policy features are label-free:
- query length;
- number and sections of IPC3 codes;
- BM25 top-1/top-2 margin;
- R1/R2 overlap@50;
- the share of R2 top-50 candidates whose IPC3 set is disjoint from the query's;
- a Qwen-free cost estimate.

Reward on dev is the number of new strict-OUT positives added to the pool minus λ × Qwen calls. λ is chosen on dev by the rule in Section 8.

**Guard against gaming the label definition.** OUT is defined by IPC3 disjointness, and Q2 deliberately searches IPC3-disjoint classes. A policy could therefore raise OUT exposure by retrieving any disjoint-IPC family, relevant or not. All-positive (IN + OUT) Recall@200 is therefore a mandatory non-inferiority check (H-G), and every report gives IN and OUT exposure side by side.

## 6. Simulated organizations

- An organization is the set of queries whose first-listed IPC3 code falls in one IPC section, A–H. This gives up to 8 organizations, and every query belongs to exactly one.
- A demonstration organization, "cardiovascular-device", is defined as queries whose first-listed IPC3 is A61. Of all 1,247 queries, 203 carry A61 anywhere in their codes. This organization supports the PoC and the Track B link and is reported descriptively.
- The profile is the organization's IPC3 frequency vector, computed from its dev queries only.
- An organization with fewer than 30 OUT-eligible test queries is reported descriptively, not inferentially.

## 7. Research questions and hypotheses

- **RQ1 (acquisition).** Do LLM cross-domain actions increase strict-OUT exposure at an equal candidate budget?
  - H1: M\* − F\* on macro strict-OUT Recall@200 > 0.
- **RQ2 (adaptivity).** Does a learned per-query policy beat the fixed baseline while calling the LLM on only part of the queries?
  - H2: π-global − F\* > 0, with Qwen call rate < 1.
  - H2b (tolerance check, not equivalence): lower 95% bound of π-global − M\* ≥ −0.01.
- **RQ3 (organization context).** Does a policy adapted to an organization's profile beat the global policy on that organization's held-out queries?
  - H3: pooled over test queries, π-org − π-global > 0.
- **Guard H-G.** For π-global and M\* vs F\*, the lower 95% bound of the all-positive Recall@200 difference is ≥ −0.02.
- **RQ4 (cost).** Report Qwen calls, tokens, GPU-seconds and latency per query for every policy, plus the exposure–cost frontier. This is descriptive.

**Primary endpoint:** macro strict-OUT Recall@200 over OUT-eligible test queries, which is pool exposure.

**Secondary endpoints:**
- strict-OUT Recall@100 and hit-rate@200 (at least one OUT positive in the pool);
- all-positive and IN Recall@200;
- nDCG@100 of the merged pool in its merge order;
- per-organization results.

## 8. Staged plan with stop rules

| Stage | Work | Compute | Gate to continue |
|---|---|---|---|
| 0 | Hash check; split; model and license records; reproduce ARM-03 (R2) on dr-train; 20-query Qwen canary on dev for throughput, failure rate and prompt sanity | CPU + corpus encoding + less than 1 GPU-hour of Qwen | Hashes match; ARM-03 reproduced within 0.005; canary failure rate ≤ 5% |
| 1 | Run every action on dev. Compute F\*, M\* and the dev oracle. | GPU: Qwen ≈ 2 calls × dev queries; encode the corpus once per dense model | **Headroom gate:** dev oracle − F\* ≥ 0.03 strict-OUT Recall@200, **and** Q actions contribute ≥ 10% of the unique OUT positives found by any action. If either fails, stop. Report the headroom result as a diagnostic finding and do not open test. |
| 2 | Train π-global and π-org on dev with 5-fold cross-fitting by component. Choose λ as the smallest grid value whose cross-fitted π-global stays within 0.01 of M\*. Write the freeze file (prompts, code hashes, selections, λ) and commit **before** test. | CPU | Freeze committed |
| 3 | Score all policies on test once. Use a paired component bootstrap (10,000 resamples, seed `20261105`) with Holm adjustment over H1, H2 and H3. H2b and H-G are tolerance checks. | GPU for Qwen on test queries | — |
| 4 (optional, separate amendment) | GRPO-LoRA on Qwen3-1.7B or 4B for the Q1 generator on dev, rewarded by OUT exposure gain. It is compared against the prompted Q1 as a new arm under its own freeze. | Hours to days on one V100 | Only if Stage 3 shows a positive H1 and the owner approves the extra compute |

Non-significant differences are reported as such and are never called equivalence. Every policy and action is reported on test, not only the selected ones.

## 9. Compute and cost

- No paid API calls. The E2 ledger is not touched.
- Qwen3-8B runs fp16 on the approved dr-train V100 slot with the existing cooperative lock, using the established `run_qwen_generation_evidence_pack.py` pattern. Throughput comes from the Stage 0 canary, not from estimates.
- Corpus encoding: one pass per dense model over 45,336 families.

## 10. Known limitations, declared before any run

- Citation-based qrels are incomplete, and the IPC3-based OUT label is an operational proxy for "cross-domain".
- Simulated organizations are IPC sections, not companies. Results do not show value for any real organization.
- Every DAPFAM query has been seen by earlier baselines (Section 3), and a single benchmark limits external validity. A second open-pool benchmark is future work and needs its own rights check.
- LLM-generated queries may encode Qwen's pretraining knowledge of the cited patents. Contamination cannot be ruled out and must be discussed.
- Exposure is necessary but not sufficient: an exposed family still has to be ranked and read by a searcher.
