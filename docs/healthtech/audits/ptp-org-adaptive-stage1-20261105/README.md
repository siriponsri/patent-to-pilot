# Stage 1 (development split): original gate PASS, learnable headroom FAIL

Status: `PARTIAL`. All six actions ran on the 474 dev queries (349 strict-OUT eligible). The test split was not read.

The preregistered headroom gate passed. Under Amendment 1, no fixed mix and no per-section mix beat the dense baseline on held-out dev queries. Per the amendment, neither the fixed-mix claim nor the organization-adaptive claim goes forward. The next step is an owner decision; Stage 2 is not started.

## Results ([stage1-dev-results.json](stage1-dev-results.json))

Strict-OUT Recall@200 on dev, n = 349:

| Action | OUT R@200 | OUT R@100 | OUT hit@200 | IN R@200 | LLM calls/query |
|---|---|---|---|---|---|
| R1 BM25 (title+abstract+claims) | 0.0717 | 0.0448 | 0.238 | 0.290 | 0 |
| **R2 dense passages (F\*)** | **0.1618** | **0.1120** | **0.407** | **0.518** | 0 |
| R3 RRF(R1, R2) | 0.1395 | 0.0963 | 0.384 | 0.474 | 0 |
| Q1 RRF(dense, BM25) of the functional query | 0.1184 | 0.0828 | 0.332 | 0.375 | 1 |
| Q2 dense functional query, IPC-restricted | 0.1225 | 0.0813 | 0.287 | 0.106 | 1 |
| Q3 dense pseudo-document | 0.1358 | 0.0904 | 0.347 | 0.331 | 1 |

- **M\* = R2.** Of the 63 subsets under the 200-family round-robin budget, none beat R2 alone. The next best was R2+R3+Q2+Q3 at 0.1591.
- **Oracle:** 0.2605 overall, 0.1806 without LLM actions, 0.2557 when choosing one action per query.
- **Unique strict-OUT positives across all actions:** R actions 397, Q actions 401, Q-only 120, union 517.

**Preregistered gate: PASS**

| Check | Value | Required |
|---|---|---|
| Oracle − F\* | 0.0987 | ≥ 0.03 |
| Q-only share of unique positives | 23.2% | ≥ 10% |

**Amendment 1 (5-fold query-level cross-fitting, stratified by first-IPC section)**

| Check | Δ | 95% CI | Decision |
|---|---|---|---|
| Cross-fitted global mix − F\* | −0.0141 | −0.0280 to −0.0019 | Fixed-mix claim not carried to test |
| Per-section mix − global mix | −0.0080 | −0.0237 to +0.0072 | Organization-adaptive policy not carried to Stage 2 |

- Selection inflation: the R-only oracle is 0.0187 above F\*. The LLM actions add 0.0799 of oracle headroom on top of that, so the per-query headroom is real but no fixed or section-level rule captures it.
- Held-out OUT R@200: F\* 0.1618, global mix 0.1477, per-section mix 0.1397.

**Reading.** The LLM actions reach different cross-domain prior art: 120 positives that no conventional action reaches. Under an equal 200-family budget, merging them in displaces more of R2's positives than it adds. Choosing one mix per IPC section is worse than one global mix, which is consistent with too few queries per section (15 to 128) for section-level choices.

## Loss map ([loss-map-dev.json](loss-map-dev.json))

- Strict-OUT pairs: 2,990. Missing from the R2 Top-200: 2,628 (87.9%; query-macro 83.8%). IN pairs missing: 54.2%.
- Missing pairs that at least one Q action reaches in its own Top-200: 160 of 2,628 (6.1%). By action: Q1-dense 61, Q1-BM25 31, Q2 76, Q3 58. BM25 R1 reaches 35.
- One shared-target component holds 374 dev queries and 2,571 of the 2,990 OUT pairs. Pair counts lean toward it; query-macro shares are reported too.
- [loss-map-dev-r.json](loss-map-dev-r.json) is the earlier R1/R2-only version.
- A private claude.ai dashboard ("Lost Cross-Domain Prior Art") shows the R1/R2 aggregates.

## Qwen3-8B generation (dev)

- Prompt `ptp-org-adaptive-qwen-actions-v1`; greedy, fp16, eager attention; Tesla V100-SXM2-32GB.
- 948 calls, 1 failed (functional-query action for one query), no retries, no truncation.
- Tokens: 606,994 prompt and 123,855 output. Mean latency 9.48 s per call; 8,990 s in total.
- Input sha256 `1a38e1af…`, output sha256 `c4dc14c9…`. Generated texts stay in private artifacts.
- Label-free observations:
  - Functional queries run 37–80 words (median 55), below the 60–120 the prompt asked for.
  - Proposed IPC classes are generic: G01 in 267 and F16 in 221 of 473 queries; 63 distinct classes.
  - 15 queries got no usable class, so Q2 is empty for 16 queries (including the failed call).

## Inputs

| Artifact | sha256 (prefix) |
|---|---|
| R1 rankings | `6c86ed4c` |
| R2 rankings | `cb53eaad` |
| Q1-dense rankings | `5dc65b78` |
| Q1-BM25 rankings | `7fa3dc51` |
| Q2 rankings | `f2b0c10e` |
| Q3 rankings | `18539516` |
| Action inputs | `q1-dense` `968e05f1`, `q2-dense` `d2817366`, `q3-dense` `4520a12c`, `family-ipc3` `b401e1d0` |
| Split | `dd76c019` |

Full hashes are in the results JSON.

The dense runner's sha256 `5c9f7236…` was checked on dr-train before the run; it reused the Stage 0 passage vectors.

## Commands

- `python scripts/healthtech/build_dapfam_action_inputs.py --qwen-output <private>/stage1/qwen-dev-v1.out.jsonl --output-dir <private>/stage1/action-inputs`
- dr-train: `run_q_dense_dev.sh` (`run_dapfam_dense_pool.py` for q1-dense, q2-dense and q3-dense with `--family-ipc3`)
- `python scripts/healthtech/run_dapfam_bm25_pool.py --corpus <private>/corpus-tac.jsonl --queries-jsonl <private>/stage1/action-inputs/q1-bm25.jsonl --output <private>/stage1/rankings-q1-bm25-dev.jsonl`
- `python scripts/healthtech/analyze_dapfam_stage1.py --r1 … --r2 … --q1-dense … --q1-bm25 … --q2 … --q3 … --split <private>/split.json --output docs/healthtech/audits/ptp-org-adaptive-stage1-20261105/stage1-dev-results.json --private-output <private>/stage1/per-query.json` (exit 0)
- `python scripts/healthtech/build_dapfam_loss_map.py --rankings R2=… R1=… Q1d=… Q1b=… Q2=… Q3=… --split <private>/split.json --output docs/healthtech/audits/ptp-org-adaptive-stage1-20261105/loss-map-dev.json`

Cost: USD 0 in paid calls. About 2.5 h of V100 time for generation, plus a few minutes of dense query encoding.
