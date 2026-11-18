# B53 — First-Stage Substitution Study on DAPFAM (executable draft; NOT_RUN; not frozen)

Source design: owner file `owner-note-19112026/09_PAPER53_BRIDGE_AND_COMMITTEE_RESPONSE.md` (B53-0.1) and registry §5.
This draft binds that design to assets that exist in this repo / on dr-train, so it can be frozen and run once the owner
answers the open items in §8. Exploratory; outside every P1/P2/P3 confirmatory family; never used to train, tune or select.

## 1. What already exists (verified 19 Nov 2026)
| Item | Value | Where |
|---|---|---|
| DAPFAM corpus | 45,336 families, TAC; 188,944 MaxP passages (PatEmbed passage rule) | `methodology/datasets/research-only-nc/` (CC BY-NC-SA 4.0 per repo records), native staging `audits/ptp-dapfam-native-staging-20261110` |
| Queries | native dev 474 (OUT-eligible 349); native test 773 (sealed after the single P1-DAPFAM look) | staging receipts |
| Paper 53 cohort | 724 OUT-positive queries (692 held-out + 32 excluded); original keys/pools unrecovered | Paper 53 §IV-A (`literature-review/internal/paper53_ieee_express.pdf`) |
| F0 encoder | datalyes/patembed-base @`244ba452908a3093be11efb8a44396652317fb14` = the Paper 53 ref. [18] revision | dr-train `research-product-o1-o4-20261031/models/patembed-base`; `audits/ht-research-product-20261031/manifest.json` |
| Rerankers | bge-reranker-v2-m3 @`953dc6f6…` present (= Paper 53 ref. [20]); **Qwen3-Reranker-0.6B @`e61197ed45024b0ed8a2d74b80b4d909f1255473` NOT on disk** | dr-train models dir |
| Instruction texts | Generic (13 tok) / Patent-aware (29) / Claim-focused (119) / Scrambled (113, seed 42) verbatim in Paper 53 Table I (checked visually) | Paper 53 p. 3 |
| Prior DAPFAM first-stage evidence (dev, exposed) | B0 PatEmbed-large OUT R@200 0.1477; BM25 0.0690; RRF −0.0197 OUT / −0.0555 IN; OUT exposure @200 136/349 | `paper2-precheck/HEADROOM-RESULT.md`, `audits/ptp-native-exposure-20261111` |

## 2. Question and factors
Holding queries, labels, TAC rendering, pool depth, reranker weights, instruction bodies and evaluation code fixed, how do
known-OUT exposure and the instruction contrasts change when **only the first stage** changes?

| First stage | Definition |
|---|---|
| F0 | patembed-base @244ba452, TAC, MaxP over PatEmbed passages, cosine, deterministic ties (re-implementation; not a replication) |
| F1 | BM25, k1 1.5, b 0.75, lowercase `[a-z0-9]+` (same as P1 B-BM25) over TAC |
| F2 | RRF(F1, F0), k = 60 |
| F3 | Arctic-embed-m-v2.0 @95c27414 zero-shot (query prefix "query: ") |
| F4 | RRF(F1, F3), k = 60 |
| F5 (conditional) | P1 S\* and RRF(BM25, S\*) after P1 freezes; never trained or tuned on DAPFAM |
| F6 (proposed, owner) | PatEmbed-large (the P1-DAPFAM B0) — already measured on dev; adds the P1-DAPFAM link |

Depth K = 100 (primary, as Paper 53) and 200; exposure curve to 1000 for F0–F4 (no reranking beyond 200).
Rerank arms on every pool: no-rerank, Qwen3-Reranker Generic / Patent-aware / Claim-focused / Scrambled, BGE plain-pair.
Reranker inputs as Paper 53: query ≤ 2,048 tokens, document ≤ 4,096 tokens, right-truncated; raw scores, ties by first-stage
rank then key.

## 3. Endpoints (file 09 definitions)
Exposure X_K(q) (≥ 1 known OUT family in pool), π_K, first-OUT rank r1, strict OUT nDCG@100 (ideal over all known OUT
families), in-pool oracle headroom H(q), Δ and Δ_exp, common-exposed set C (exposed under every first stage compared).

## 4. Analyses (numbering reconciled: file 09 numbering is used; registry §5 numbering differs — conflict R-15)
| ID | Quantity | Inference |
|---|---|---|
| B53.1 | π_K(F) − π_K(F0) | paired cluster bootstrap (component of shared OUT targets), paired exact test |
| B53.2 | median r1, share r1 ≤ 10 among exposed | descriptive |
| B53.3 | Δ_exp on C: Patent-aware, Claim-focused vs Generic, per first stage; wins/losses/ties | CI; Holm over B53.3 only |
| B53.4 | headroom H by first stage; share realised by each instruction | descriptive |
| B53.5 | F0 re-implementation exposure vs the reported 37.1% (K = 100) | descriptive, no threshold, not a replication |
Language policy: file 09 §6 (identity = accounting; only B53.1/B53.3 support "changing the first stage changed …").

## 5. Cohorts (needs owner choice, §8)
- **B53-DEV (no conflict):** native dev OUT-eligible 349 queries (already exposed; P1-DAPFAM dev descriptive line).
- **B53-FULL:** all OUT-positive queries (expected 724 = Paper 53's full cohort) — requires reading DAPFAM **test** qrels again.

## 6. Compute (local dr-train only; DAPFAM never leaves dr-train/this PC)
Encoding 188,944 passages: patembed-base and Arctic each < 30 min on the shared V100 (from overnight measured rates:
Arctic 1M passages ≈ 70 min shared). Reranking is the cost driver: 724 × 100 × 5 instruction/ranker arms × 5 first stages
≈ 1.8M pairs at up to 6k tokens; NOT_MEASURED for Qwen3-Reranker on the V100 — a 1,000-pair timing run must size it first.
If it exceeds about one week of shared-V100 time, reranking on F0–F4 at K = 100 only for B53-DEV is the fallback.

## 7. Isolation
No P1/P2/P3 TEST data. DAPFAM is evaluation-only. Results never select anything in P1/P2/P3. Licence: recorded as
CC BY-NC-SA 4.0 in repo records; owner file still says UNVERIFIED — local runs only.

## 8. Owner decisions needed before freezing (lane C)
1. **R-16 conflict:** CLAUDE.md standing rule "never re-open the [P1-DAPFAM] test qrels" vs file 09 (B53 may use DAPFAM test). Allow B53-FULL (724) or keep B53-DEV (349) only?
2. Download Qwen3-Reranker-0.6B @e61197ed (≈1.2 GB, Apache-2.0) to dr-train (needed for Paper 53's reranker).
3. O16: rationale for patembed-base in Paper 53 (not found in repo; owner must write it).
4. O17: confirm the Table I bodies above are the ones to freeze (verbatim from the published paper).
5. Add F6 (PatEmbed-large) and/or Qwen3-Embedding zero-shot as extra first stages? (overnight OA DEV: PatEmbed-large 0.328, Qwen3 0.274, Arctic 0.225 OUT R@200).
6. O14 budget line: GPU cost is USD 0 on dr-train; only time.
