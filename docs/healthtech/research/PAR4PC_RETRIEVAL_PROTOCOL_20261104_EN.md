# Protocol: lexical, dense, hybrid and cost-aware cascade ranking for claim-level prior-art options (PANORAMA PAR4PC)

- Protocol ID: `ptp-wpi-par4pc-protocol-v1`
- Written: 2026-11-04 (UTC). This document is frozen together with the validation-phase selections in `docs/healthtech/audits/ptp-wpi-research-package-20261104/par4pc-freeze.json` before any new method is scored on the test split.
- Study type: solo, reproducible computational study. No human assessors, no training or fine-tuning, no paid inference.

## 1. Purpose and fit

Track A of the WPI research package uses an established public patent-information benchmark. The task is to rank the eight candidate prior-art patents attached to one application claim so that examiner-cited documents appear first. Track B (the device dossier cases) is a separate application demonstration and is not pooled with these results. Results here do not validate device–patent linkage, freedom to operate, or any medical-device claim.

## 2. Data and labels

- Source: PANORAMA PAR4PC validation and test parquet files, source revision `5c40de5fb1de842d3a44ec4b9f5bb9c44d47a77d`, license CC BY-NC 4.0. Used for local, non-commercial research and evaluation only. Raw text is not redistributed in Git.
- File SHA-256: validation `d84d34779c2d741b9eb3aebd7db009836dc0d78ba4c78aee1cfa410f5092594d`, test `f1f8e33d32bfd2a6a2a7f1e740e94a6512c5d79598fdfb6b431829b21b6565e3`.
- Unit: one row per (application, rejected claim), each with eight options A–H.
- Label semantics, as published by the dataset authors: `gold_answers` are prior-art documents cited by the USPTO examiner in rejecting that claim; `silver_answers` are other documents cited in the same examination context; `negative_answers` are the remaining options. Examiner citations are a documented proxy for relevance, created independently of every method evaluated here. They are incomplete and examiner-specific, and they are not exhaustive relevance judgments.
- Size: validation 3,029 rows over 221 applications; test 2,896 rows over 222 applications. No application appears in both splits. 149 option patents appear in both splits; this is shared prior art, not label leakage, because no method is trained.
- Prior exposure: a deterministic per-row BM25 baseline was previously run on both splits (Hit@1 0.7336 validation and 0.7151 test). No new method, formulation, or threshold has been scored on test before this freeze.

## 3. Research questions and hypotheses

- **RQ1 (primary).** Does a dense patent encoder, or a fixed lexical–dense hybrid, rank examiner-cited prior art higher than the existing BM25 baseline?
  - H1: the selected dense ranker beats BM25-full on application-macro MRR.
  - H2: the fixed hybrid beats BM25-full.
  - H3: the fixed hybrid beats the selected dense ranker.
- **RQ3 (supporting cost trade-off).** Can a cost-aware cascade escalate only uncertain rows to dense scoring while staying within a prespecified tolerance of the always-hybrid policy?
  - H4: on test, the lower 95% bound of (cascade − hybrid) MRR is ≥ −0.01, and the escalation rate is < 1.

## 4. Methods (all zero-shot and label-free at runtime)

| ID | Method |
|---|---|
| A0 `bm25_full` | Existing per-row BM25 (k1 = 1.2, b = 0.75, IDF over the row's eight options). Query = title + abstract + all claims. |
| A0' `bm25_claim` | Same scorer. Query = target claim + title + abstract. |
| A1 `patembed_{full,claim}` | PatEmbed-base (pinned weights on dr-train, `retrieval_MIXED` prompt, max 512 tokens, mean pooling + projection, L2). Cosine between query and option vectors. |
| A2 `e5_{full,claim}` | multilingual-e5-base (`query:` / `passage:` prefixes, max 512 tokens, mean pooling, L2). |
| A3 `hybrid` | Reciprocal-rank fusion (k = 60) of the selected BM25 formulation and the selected dense ranker. Fixed, not tuned. |
| A4 `cascade` | Rank by the selected BM25 first. If the relative top-two BM25 margin `(s1 − s2) / s1` is ≥ τ, keep it; otherwise use `hybrid`. Only escalated rows require dense scoring. |

Option text = title + abstract + claims. Inputs sent to the GPU host contain no labels.

## 5. Validation-only selection rules (applied once, then frozen)

1. For BM25, PatEmbed and e5 separately, pick the query formulation (`full` or `claim`) with higher validation application-macro MRR.
2. Selected dense ranker = the better of PatEmbed\* and e5\* on validation application-macro MRR.
3. `hybrid` = RRF(BM25\*, Dense\*).
4. τ = the smallest value on the grid of validation BM25-margin quantiles {0, 0.05, …, 1.0} such that validation cascade MRR ≥ validation hybrid MRR − 0.01. A larger τ escalates more rows, so the smallest qualifying τ gives the lowest escalation rate. If no grid value qualifies, τ = +∞, which always escalates.

## 6. Endpoints

- Primary: application-macro MRR of the first gold option (rows averaged within each application, then across applications).
- Secondary: application-macro Hit@1, gold Recall@3, and graded nDCG@8 (gold = 2, silver = 1); row-micro versions; escalation rate; dense encodings needed; measured encoding and CPU time.

## 7. Analysis

- Paired contrasts on test: C1 Dense\* − BM25-full, C2 hybrid − BM25-full, C3 hybrid − Dense\*. Each uses an application-level paired cluster bootstrap (10,000 resamples, seed 20261104, 95% percentile CI, two-sided bootstrap p), with Holm adjustment across C1–C3.
- C4 cascade − hybrid is a tolerance check against −0.01 MRR. It is not an equivalence claim.
- All rows are kept; a row with a ranking failure counts as reciprocal rank 0. The number of failures is reported.
- Non-significant differences are reported as such and are not called equivalence. Every method on every formulation is reported on test, not only the selected ones.

## 8. Known limitations (declared before test)

- Examiner citations are incomplete and proxy relevance. Closed eight-option ranking is easier than open-corpus prior-art search.
- PatEmbed's training data may overlap USPTO citation data; contamination cannot be ruled out and is reported as a limitation.
- 512-token truncation drops most claims of long documents.
- One run per configuration: the methods are deterministic, so seeds are not independent samples.
