# B53 Stage 1 — first-stage exposure on DAPFAM (MEASURED, 19 Nov 2026)

- Protocol: `docs/healthtech/research/plans/B53-PREDECLARATION.md`, frozen at 274af5de before any B53 number.
- Code: `scripts/healthtech/b53_first_stage.py` (sha256 374e79cd…) with `tests/test_b53_first_stage.py`. Run on dr-train
  through `scripts/healthtech/queue_b53_stage1.sh`; every step exited 0.
- Aggregates: `b53-stage1-results.json` (sha256 cdff79f7…). Per-query rows stay on dr-train only, because they are DAPFAM-derived.
- Inputs: `b53-inputs-manifest.json` (DAPFAM revision a59a74ce, whose data equals 780f4011).
- Cost: shared V100 plus CPU, USD 0.
- Status: exploratory, evaluation-only. This is a re-implementation of Paper 53's first stage, **not** a replication.

## Cohorts
905 OUT-eligible queries (≥ 1 positive OUT family), 1,217 IN, 1,247 ALL. The pre-declaration said "expected 724"; that is the
size of Paper 53's cohort, whose filter cannot be recovered. The frozen definition (≥ 1 positive OUT) was kept, so 905 is
the B53 cohort. This difference is reported, not adjusted.

## Primary: exposure at K = 100 (share of OUT queries with ≥ 1 known OUT family in the top 100)

| Arm | π@100 | π@200 | π@1000 | OUT R@100 | OUT R@200 | OUT nDCG@100 | IN R@100 | median first-OUT rank (exposed) |
|---|---|---|---|---|---|---|---|---|
| F0 patembed-base (MIXED prompts) | **0.371** | 0.471 | 0.733 | 0.160 | 0.241 | 0.061 | 0.541 | 22 |
| F1 BM25 | 0.266 | 0.344 | 0.548 | 0.107 | 0.148 | 0.041 | 0.345 | 20 |
| F2 RRF(BM25, F0) | 0.376 | 0.469 | 0.701 | 0.170 | 0.228 | 0.063 | 0.519 | 24 |
| F3 Arctic-embed-m-v2.0 | 0.317 | 0.419 | 0.632 | 0.125 | 0.194 | 0.048 | 0.454 | 22 |
| F4 RRF(BM25, F3) | 0.336 | 0.431 | 0.643 | 0.141 | 0.199 | 0.052 | 0.462 | 22 |
| F0-OUT patembed-base (OUT prompts) — sensitivity | 0.401 | 0.490 | 0.750 | 0.185 | 0.254 | 0.071 | 0.517 | 19 |
| F6 patembed-large — secondary | 0.374 | 0.477 | 0.733 | 0.166 | 0.249 | 0.061 | 0.549 | 22 |
| F7 Qwen3-Embedding-0.6B — secondary | 0.347 | 0.430 | 0.640 | 0.141 | 0.193 | 0.057 | 0.458 | 22 |

## B53.1: change in π@100 against F0 (paired bootstrap B = 10,000, seed 20261119; exact McNemar; Holm over the 4 core contrasts)

| Arm | Δπ@100 | 95% CI | gained / lost | Holm p | Family |
|---|---|---|---|---|---|
| F1 BM25 | −0.105 | [−0.136, −0.075] | 55 / 150 | 9.1e−11 | core |
| F2 RRF(BM25, F0) | +0.004 | [−0.015, +0.024] | 46 / 42 | 0.75 | core |
| F3 Arctic | −0.054 | [−0.077, −0.032] | 34 / 83 | 2.0e−5 | core |
| F4 RRF(BM25, Arctic) | −0.035 | [−0.061, −0.010] | 54 / 86 | 0.017 | core |
| F0-OUT (prompt) | +0.030 | [+0.013, +0.046] | 44 / 17 | — | descriptive |
| F6 patembed-large | +0.002 | [−0.009, +0.013] | 15 / 13 | — | descriptive |
| F7 Qwen3-Embedding | −0.024 | [−0.048, −0.001] | 47 / 69 | — | descriptive |

Common-exposed set C (exposed at K = 100 under all five core arms) = **153** of 905 queries. This is the matched population for
Stage 2.

## What this supports (wording policy of file 09 §6)
- **K1b:** in this setting, replacing the patembed-base first stage with BM25, Arctic, or their RRF hybrids did **not** raise
  OUT exposure at K = 100. BM25 lowered it by 10.5 points; RRF(BM25, F0) left it statistically unchanged. "Use BM25/hybrid"
  is therefore not a fix for the 37% exposure ceiling on DAPFAM.
- **K2a (first part):** the first stage changes exposure, both down (BM25, Arctic) and up (F0-OUT prompt +3.0 points,
  descriptive). Each of these is a real manipulation of the first stage, so B53.1 can state "changing the first stage
  changed exposure".
- **K1a context:** among the zero-shot first stages tested, patembed-base is at or near the top. patembed-large is
  indistinguishable (+0.002), and Qwen3-Embedding and Arctic are lower. This measures the choice Paper 53 made; it does not
  rationalise it after the fact.
- **Exposure ceiling:** even at K = 1,000, 27% of OUT queries have no known OUT family under the best core arm (F0 π@1000 = 0.733).

## What it does not support
- F0's π@100 = 0.371 numerically equals Paper 53's 37.1% (257/692). The cohort (905 vs 692), the pipeline and the keys all
  differ. Report it as a coincidence of magnitude, **not** a replication.
- Nothing here concerns instructions yet; that is Stage 2.
- Judgments are incomplete; "exposure" means exposure of *known* OUT families.

## Limitations recorded
- **Truncation:** 92% of TAC records (41,793 / 45,336) and 95% of TAC queries exceed 512 tokens, so claims are cut. This
  follows the record-level reading of Paper 53. A passage/MaxP variant would be a separate sensitivity analysis.
- **Self-hits:** 135 queries whose own family is in the corpus rank it first under every arm (MTEB-native setting, no
  exclusion). This affects ALL/IN, not OUT, because a family cannot be OUT relative to itself.
- **Prompt choice matters:** F0-OUT gains 3 points over F0. The primary F0 uses the MIXED prompts declared before the run.
