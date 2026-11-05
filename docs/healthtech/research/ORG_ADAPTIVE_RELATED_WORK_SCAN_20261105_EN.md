# Related-work scan after Stage 1 (5 Nov 2026)

Purpose: decide the next direction after Stage 1. On dev, LLM query actions reached 23% of the union of strict-OUT positives that no conventional action reached, but no fixed or per-IPC-section mix beat dense retrieval at a 200-family budget ([Stage 1 audit](../audits/ptp-org-adaptive-stage1-20261105/README.md)).

Sources:
- the 35 local PDFs in `literature-review/pdfs/`;
- 10 open-access arXiv papers added to `literature-review/pdfs/05-cross-domain-followup/` (git-ignored);
- a web and GitHub search.

This is not a systematic review. Page numbers refer to the PDFs.

## What the literature says about our Stage 1 result

| Finding | Source | Consequence for us |
|---|---|---|
| Generative query or document expansion helps weak retrievers and usually hurts strong ones | Weller et al., EACL Findings 2024 (arXiv 2309.08541) | Our Q actions losing to dense alone is the expected outcome, not an anomaly |
| Prompt-only rewriting helps or hurts depending on the domain. Feature-based gating has AUC 0.593 and does not beat never-rewriting; the oracle ceiling is +3 pp | Kotte, arXiv 2603.13301 (2026) | Per-query "when to rewrite" gating is likely to give a null result. Treat it as a risky direction |
| Query-performance prediction and an SVM could not predict which patent topics expansion helps; pseudo-relevance feedback halved recall on CLEF-IP | Magdy & Jones, PaIR 2011, p.3 and p.5 | Historical precedent for negative routing results in patents |
| Across 22 embedding models (22M–12B, including Qwen3-Embedding 0.6/4/8B), the IN→OUT gap on DAPFAM is 55–65%; BM25+dense fusion does not close it; fine-tuning on one landscape hurts cross-domain retrieval in 5 of 8 cases | Yousefiramandi & Cooney (Clarivate), arXiv 2605.24297 (2026) | Better encoders or fusion alone will not solve OUT. Characterising the OUT gap is no longer novel by itself |
| Fixed-K truncation removes the recall gains from fusion | RAG-Fusion industry study, arXiv 2603.02153 | The same equal-budget effect we observed |
| Reformulation weights adapted by a bandit under a fixed reranking budget give up to +33% Recall@50 on MS MARCO/TREC DL. Equal-weight RRF degrades as reformulations are added | ReformIR, arXiv 2605.00560, pp.4–8 | Closest prior work for adaptive acquisition under a budget. Its judge is anchored to the original query, which carries the in-domain bias |
| Adaptive retrieval decisions: Adaptive-RAG, MBA-RAG (bandit), cost-aware evidence selection | HealthTech pack P14–P19 | A bandit over retrieval actions is not novel in itself |

## DAPFAM baselines and protocol

- DAPFAM (Ayaou, Cavallucci, Chibane) is published in *Array* 29:100720 (2026).
  - OUT is evaluated on "candidates with no shared IPC3 codes" (p.17), which reads as ranking within the OUT candidate subset.
  - Best OUT results: dense-passage R@100 0.155, RRF R@100 0.165 (Tables 15, 18).
  - There is no official split, and the RRF K was tuned on the evaluation set (p.18).
- Our strict-OUT protocol ranks the whole corpus, so IN families compete for the same slots. Our R2 strict-OUT R@100 is 0.112. Before comparing numbers, we must reproduce DAPFAM's subset protocol at R@100.
- PatenTEB (arXiv 2510.22264) trains patembed with a retrieval_OUT task built from Lens with the DAPFAM method (pp.5–7).
  - The paper states no exclusion of DAPFAM families.
  - Leakage check pending: the HF dataset `datalyes/retrieval_OUT` is gated, and its file list shows only a test split.

## Open space

- No published method targets the IPC-disjoint (OUT) setting itself.
- No RL- or retrieval-reward-trained patent query rewriter exists. The nearest are PatEx-Gym (arXiv 2610.33503, SFT of a 4B agent, not RL) and DeepRetrieval (arXiv 2503.00223, Qwen2.5-3B with a recall reward on PubMed, MIT licence).
- No patent work studies how to split a fixed candidate budget across sources.

## Candidate directions, ranked

### 1. Decompose exposure loss into crowd-out and semantic distance (recommended first)

Add a label-free "cross-domain lane": dense retrieval restricted to families that share no IPC3 code with the query's own codes. Both sets of codes are metadata known at search time.

- A pair that enters the lane's Top-200 but not plain dense's was lost to crowd-out by in-domain families.
- A pair absent from both is semantically distant. Only bridging actions (LLM rewrites, a trained rewriter) can address those.
- Then study how to split the 200 slots between the plain and cross-domain lanes. A per-query adaptive split goes to Stage 2 only under cross-fitting.
- **Cost:** one dense run of minutes on dev, with no new LLM calls.
- **Novelty:** the subset protocol in DAPFAM is an evaluation device, not a deployable acquisition arm under a shared budget, and no paper reports this decomposition.
- **Risk:** reviewers may call the lane trivial because OUT is defined by IPC. The answer is that a searcher who wants cross-domain art can do exactly this, and the lane is the baseline any LLM method must beat.

### 2. A retrieval-reward-trained rewriter (exploratory, after 1)

GRPO with LoRA on Qwen 1.5–4B (DeepRetrieval or TongSearch-QR recipe), rewarded by strict-OUT recall on the semantically distant pairs.

- **Risks:**
  - V100 lacks bf16 and FlashAttention-2.
  - Only 349 dev OUT queries are available for training.
  - Reward hacking (SAGE, arXiv 2506.19783).
  - Retriever-specific overfitting (arXiv 2606.16817).
- Report it as exploratory under its own freeze.

### 3. A diagnostic paper (fallback, always available)

A combination of:
- the exposure decomposition;
- the protocol comparison (strict-OUT vs subset);
- the complementarity of LLM actions with an oracle ceiling;
- the negative routing results;

positioned against Weller et al., Kotte and the 22-model benchmark.

### Not recommended

- Per-query gating of LLM rewrites alone (Kotte; Magdy & Jones).
- Further encoder fine-tuning on one landscape (22-model benchmark).
- Pseudo-relevance feedback for OUT (Magdy & Jones).

## Papers to obtain manually

| Paper | Reason |
|---|---|
| Rethinking patent retrieval with language models, *World Patent Information* 2026, S0172219026000086 | Returned 403; same venue |
| CPC-aware neural patent retrieval with LLM-assisted query expansion, Springer 2026, 10.1007/s42488-026-00165-8 | Paywalled; closest to the IPC-shift action |
| DAPFAM, *Array* 29:100720 (2026), 10.1016/j.array.2026.100720 | Published version of the benchmark |
| SEARCHFORMER, *World Patent Information* 2023 | Same venue |
| LLMs across the patent lifecycle (systematic review), *World Patent Information* vol. 87 (2026) | Same venue; positioning |
| Lee & Sohn, *Scientometrics* 2021 | Low priority; technology convergence |

Also: access to the gated HF dataset `datalyes/retrieval_OUT`, for the leakage check.
