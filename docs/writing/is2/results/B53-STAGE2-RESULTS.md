# B53 Stage 2 — instruction contrasts across first stages on DAPFAM (MEASURED, 22 Nov 2026)

- **Protocol:** `docs/healthtech/research/plans/B53-PREDECLARATION.md`, Stage 2 section, frozen 19 Nov 2026 before any
  Stage 2 number (Stage 1 numbers were already known).
- **Scoring:** Qwen3-Reranker-0.6B @e61197ed (fp16, P(yes)) for the four Paper 53 Table I instructions, plus
  BGE-reranker-v2-m3 @953dc6f6 plain pair. Run on the dr-train V100 with `scripts/healthtech/b53_rerank.py` through
  `queue_b53_stage2.sh`; the log ends `B53_STAGE2_SCORES_DONE`. Each score file holds 202,012 unique (query, family)
  pairs.
- **Evaluation:** `scripts/healthtech/b53_stage2_eval.py` (sha256 93305f9e…, the same file as committed). Run on dr-train
  CPU on 22 Nov; it exited 0.
- **Aggregates:** [b53-stage2-results.json](b53-stage2-results.json) (sha256 944345bd…, identical to the dr-train copy).
  Rendered tables: [b53-stage2-tables.md](b53-stage2-tables.md). No per-query DAPFAM rows are stored in Git.
- **Cost:** shared V100 plus CPU, USD 0.
- **Status:** exploratory and evaluation-only on a previously exposed benchmark. This is a re-implementation, **not** a
  replication of Paper 53.

## Consistency checks (before reading any contrast)

- The no-rerank column reproduces the Stage 1 OUT nDCG@100 for every arm (F0 0.061, F1 0.041, F2 0.063, F3 0.048,
  F4 0.052).
- π@100 and the common-exposed set C (153 of 905 OUT queries) equal Stage 1.
- The accounting identity Δ_all = π·Δ_exp holds for every arm and system, to 4 decimals.

## B53.3 (primary): instruction contrasts on the common-exposed set C

Endpoint: strict OUT nDCG@100. Paired bootstrap B = 10,000, seed 20261119, Holm over the 10 contrasts. W/L = queries that
improved / worsened.

| First stage | Patent-aware − Generic [95% CI] (W/L) | Holm p | Claim-focused − Generic [95% CI] (W/L) | Holm p |
|---|---|---|---|---|
| F0 patembed-base | +0.004 [−0.005, +0.014] (78/71) | 1.000 | +0.006 [−0.003, +0.016] (74/74) | 1.000 |
| F1 BM25 | +0.001 [−0.007, +0.012] (62/74) | 1.000 | +0.004 [−0.005, +0.014] (64/72) | 1.000 |
| F2 RRF(BM25, F0) | +0.003 [−0.006, +0.013] (77/70) | 1.000 | +0.006 [−0.003, +0.016] (76/70) | 1.000 |
| F3 Arctic-embed-m-v2.0 | +0.007 [−0.003, +0.017] (84/64) | 1.000 | +0.009 [−0.000, +0.019] (81/65) | 0.695 |
| F4 RRF(BM25, F3) | +0.005 [−0.004, +0.016] (84/64) | 1.000 | +0.007 [−0.001, +0.018] (77/66) | 1.000 |

**None of the 10 contrasts is significant.** The smallest raw p is 0.070 (F3, Claim-focused); after Holm the smallest is
0.695. All point estimates are small and positive (+0.001 to +0.009), and every 95% CI includes 0.

## Descriptive (full OUT cohort, n = 905; unexposed queries score 0)

Mean strict OUT nDCG@100:

| First stage | π@100 | Generic | Patent-aware | Claim-focused | Scrambled | BGE plain | No rerank |
|---|---|---|---|---|---|---|---|
| F0 patembed-base | 0.371 | 0.062 | 0.063 | 0.063 | 0.063 | 0.054 | 0.061 |
| F1 BM25 | 0.266 | 0.043 | 0.043 | 0.044 | 0.043 | 0.039 | 0.041 |
| F2 RRF(F1, F0) | 0.376 | 0.064 | 0.065 | 0.066 | 0.065 | 0.057 | 0.063 |
| F3 Arctic-embed | 0.317 | 0.052 | 0.054 | 0.054 | 0.053 | 0.044 | 0.048 |
| F4 RRF(F1, F3) | 0.336 | 0.056 | 0.057 | 0.058 | 0.057 | 0.048 | 0.052 |

Contrasts against Generic, Δ_all with 95% CI:

- **Scrambled − Generic:** +0.0002 to +0.0010; every CI includes 0. The scrambled Claim-focused instruction performs like
  the real ones.
- **Claim-focused − Generic:** about +0.002. The lower CI bound touches 0 (+0.0000 to +0.0001) for F0, F3 and F4.
  This is a descriptive analysis on the full cohort, not the confirmatory test, and the size is negligible.
- **BGE plain pair − Generic:** −0.004 to −0.008. Every CI excludes 0, so the plain-pair secondary reranker is worse than
  the instructed Qwen3 reranker under every first stage.
- **No rerank − Generic:** −0.001 to −0.004. The CI excludes 0 only for F3 and F4: reranking with Qwen3 helps a little
  after Arctic-based first stages.
- **Response rate:** 91–98% of exposed queries change their endpoint under a different instruction. The instructions do
  reorder the pool; the net effect is close to zero.

## What this supports (wording policy of file 09 §6)

- **K2 (Stage 2):** the near-zero instruction effect holds under **all five** first stages on the matched population C.
  No first-stage substitution (BM25, Arctic, or their RRF hybrids) made Patent-aware or Claim-focused instructions beat
  Generic. Paper 53's diagnosis is therefore **not** an artifact of the patembed-base first stage, in this setting.
- **Instruction content carries little signal here:** a scrambled instruction does as well as the real ones, while about
  95% of exposed queries are reordered. This matches the Paper 53 reading that rankings move without systematic gain.
- **Ceiling:** absolute OUT nDCG@100 stays between 0.04 and 0.07 and tracks π@100. Exposure, not instruction wording,
  bounds the endpoint (Δ_all = π·Δ_exp).

## What it does not support

- It cannot say that exposure *causes* the instruction effect, or its absence (file 09 §6). C is a matched population,
  not an intervention on exposure.
- No claim of equivalence. The CIs are about ±0.01 nDCG, so small effects below that size cannot be excluded.
- Not a replication of Paper 53: the cohort (905 vs 692 or 724), the pipeline and the instruction token counts
  (13/28/113/113 vs the reported 13/29/119/113, O17) differ.
- DAPFAM is a previously exposed benchmark; these numbers must not select any new method (G03 uses allowed DEV only).

## Limitations recorded

- Truncation as in Stage 1: query ≤ 2,048 and document ≤ 4,096 tokens, right-truncated.
- The SDPA engineering change for V100 OOM (frozen protocol, Stage 2 section) leaves scores unaffected.
- BGE is a plain-pair secondary ranker, not instruction-capable; its gap is descriptive.
