# B53 pre-declaration, Stage 1: first-stage exposure (FROZEN 2026-11-19, before any B53 number)

Authority: owner, 19 Nov 2026. B53-FULL (all DAPFAM queries), F6/F7 as declared secondary arms, and the whole plan were
approved; see `paper1-bridgeret/owner-decisions-20261118.json` 'later'. Design source:
`B53-FIRST-STAGE-SUBSTITUTION-DRAFT.md` and the owner strategy `PTP_IS2_Paper53_Research_Program_University_Impact_2026-11-19.md` §3.
Status: exploratory, evaluation-only, local only (dr-train / this PC). It is never used to train, tune or select anything in
P1, P2 or P3. It is a **re-implementation, not a replication** of Paper 53: the original pools, keys and qrels mapping were not
recovered.

Stage 2 (reranking with the Paper 53 instructions) is declared separately after a 1,000-pair timing run. Stage 1 numbers can
not change Stage 2's arms, instructions or metrics. The Stage 2 skeleton is fixed in §7.

## 1. Data
- DAPFAM `datalyes/DAPFAM_patent`, data bytes identical at revisions 780f4011 and a59a74ce
  (`paper1-bridgeret/b53-readiness-20261119.json`).
- Corpus: 45,336 families. Queries: 1,247 families.
- Relevance: a qrel is positive iff `relevance_score > 0` (as the MTEB tasks); `domain_rel` ∈ {IN, OUT}.
- Text view: **TAC** for both queries and records = `title_en + "\n" + abstract_en + "\n" + claims_text`. This is the
  record-level reading of Paper 53 §III-B: "indexed 45,336 frozen TAC records ... returned 100 candidates per query".
- Truncation: 512 tokens of each model's tokenizer, right-truncated, for every dense arm. The truncation share is reported.
- Self-match: query families that also occur in the corpus are **not** excluded, as in the MTEB tasks. The number of rank-1
  self-hits per arm is reported, as Paper 53 also did.
- Cohorts:
  - **B53-FULL-OUT** = queries with ≥ 1 positive OUT family (expected 724) → primary;
  - **ALL** = 1,247 (macro over queries with ≥ 1 positive);
  - **IN** = queries with ≥ 1 positive IN family.
  - Paper 53's 692 held-out ids are not recoverable, so B53 does not restrict to them.

## 2. First stages (exact settings)
| Arm | Role | Definition |
|---|---|---|
| F0 | core | `datalyes/patembed-base` @244ba452 via sentence-transformers (mean pooling + 2_Dense 1024→768, L2-normalised); prompts `retrieval_MIXED` (query "encode query for mixed document retrieval: ", document "encode document for mixed retrieval: "), the same prompt family as P1 clarification CL-1 |
| F0-OUT | sensitivity of F0 (prompt only) | as F0 with the model's `retrieval_OUT` prompts ("encode query for different document retrieval: " / "encode document for different retrieval: ") |
| F1 | core | BM25 k1 = 1.5, b = 0.75, lowercase `[a-z0-9]+` tokens, no stemming or stop list (P1 B-BM25 settings), over TAC |
| F2 | core | RRF(F1, F0), k = 60, depth 1,000 per list, ties broken by family id |
| F3 | core | `Snowflake/snowflake-arctic-embed-m-v2.0` @95c27414, CLS pooling, query prefix "query: ", documents without prefix, fp16 (DAPFAM paper used int8) |
| F4 | core | RRF(F1, F3), k = 60, depth 1,000 |
| F6 | declared secondary | `datalyes/patembed-large` (P1-DAPFAM B0 model; revision as on dr-train), sentence-transformers, `retrieval_MIXED` prompts |
| F7 | declared secondary | `Qwen/Qwen3-Embedding-0.6B` @97b0c614, last-token pooling, left padding, query instruction "Instruct: Given a patent, retrieve prior art patents\nQuery: ", documents without prefix |
| F5 | conditional | P1 S* and RRF(BM25, S*) once S* is frozen; never trained or tuned on DAPFAM |

All dense arms score by exact inner product, keep the top 1,000, and break ties by family id.

## 3. Endpoints (strict OUT unless stated)
Let K_OUT(q) be the positive OUT families of q, and P_F,k(q) the top k of arm F.
- **Primary:** exposure π_F,100 = share of B53-FULL-OUT queries with K_OUT(q) ∩ P_F,100(q) ≠ ∅.
- Secondary:
  - π at k = 200 and k = 1,000 (exposure curve);
  - zero-exposure rate 1 − π;
  - first OUT hit rank r1 (median over exposed; share with r1 ≤ 10);
  - OUT Recall@100/200, ALL/IN Recall@100/200;
  - strict OUT nDCG@100 (gain = relevance_score, ideal over all positive OUT families);
  - common-exposed set C = queries exposed at k = 100 under every core arm (|C| reported).
- In-pool oracle headroom H at k = 100: ideal-reorder OUT Recall@100. Achieving it requires the pool, not a model.

## 4. Inference
- B53.1 contrasts: π_F,100 − π_F0,100 for F ∈ {F1, F2, F3, F4}.
  - Paired bootstrap over queries, B = 10,000, seed 20261119, 95% percentile CI.
  - Exact paired counts (gained / lost / both / neither) with a two-sided exact McNemar test.
  - Holm adjustment over these four core contrasts only.
- Secondary arms (F0-OUT, F6, F7) and secondary endpoints are reported with CIs and no adjustment. They are labelled descriptive.
- Language: file 09 §6. The identity Δ_all = π·Δ_exp is accounting only, never a causal claim. Only B53.1 (a real
  manipulation of the first stage) supports wording of the form "changing the first stage changed exposure".

## 5. Comparison with the DAPFAM paper (B53.0)
Run separately with the public MTEB tasks (6 in-paper tasks, nDCG@100 / Recall@100, all 1,247 queries). Arctic fp16 is the
reproduction check against the paper's int8 numbers. B53.0 numbers are never mixed with Stage 1 exposure numbers.

## 6. Isolation and resources
- DAPFAM text and labels stay on dr-train and this PC: never RunPod, never committed (only aggregates are committed).
- P1/P2/P3 TEST data are not touched.
- GPU: the shared V100 under the existing per-process memory cap and GPU lock. USD 0.

## 7. Stage 2 skeleton (to be completed after timing; listed now so Stage 1 cannot steer it)
- Rerankers: Qwen3-Reranker-0.6B @e61197ed with the four Paper 53 Table I instruction arms (Generic, Patent-aware,
  Claim-focused, Scrambled) plus no-rerank; BGE-reranker-v2-m3 plain-pair as a secondary.
- Inputs: query ≤ 2,048 tokens and document ≤ 4,096 tokens, as in Paper 53. Pools: k = 100 from every core arm.
- Endpoints: Δ_exp on C and per arm, as in file 09.
- The same reranker and instruction bodies are used for every first stage.
