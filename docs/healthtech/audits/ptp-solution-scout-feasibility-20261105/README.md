# Solution-scout feasibility (development split): PARTIAL_LANE_ONLY

Status: `PARTIAL`. The pre-declared stop rule returned `PARTIAL_LANE_ONLY`. All arms ran on the 474 dev queries (349 strict-OUT eligible). The test split was not read.

Plan: [SOLUTION_SCOUT_FEASIBILITY_PLAN_20261105_EN.md](../../research/SOLUTION_SCOUT_FEASIBILITY_PLAN_20261105_EN.md), committed at `3c4294e` before any generation.

## Decision

On the problem brief P, the scout pool beat dense retrieval on the brief, but it was worse than the lane-only pool that uses no LLM. Under the plan, the LLM claim is not carried forward and there is no test run for this direction.

A post-hoc check (below) shows that the lane gain itself comes mainly from the candidate set. The lane mask is the same rule that defines strict-OUT. The lane is therefore not a finding about briefs or LLMs either.

## Pre-declared result ([feasibility-dev-results.json](feasibility-dev-results.json))

Strict-OUT Recall@200 on dev, brief P, n = 349. Paired query bootstrap, 5,000 resamples, seed 20261105.

| Comparison | Δ | 95% CI | Rule |
|---|---|---|---|
| scout − base | +0.0437 | +0.0205 to +0.0685 | ≥ 0.02 and lower bound > 0: met |
| scout − lane | −0.0664 | −0.0941 to −0.0395 | lower bound > 0: **not met** |
| lane − base | +0.1101 | +0.0820 to +0.1404 | lower bound > 0: met → `PARTIAL_LANE_ONLY` |
| scout − llm_no_lane (secondary) | +0.0637 | +0.0433 to +0.0861 | descriptive |

**Pools.** OUT R@100 is identical within each brief because every pool keeps the first 100 of D.

| Brief | Pool | OUT R@200 | OUT R@100 | OUT hit@200 | IN R@200 |
|---|---|---|---|---|---|
| P | base (D) | 0.1350 | 0.0857 | 0.372 | 0.466 |
| P | lane (D[:100] + X) | **0.2451** | 0.0857 | 0.496 | 0.368 |
| P | scout (D[:100] + FX, SX) | 0.1787 | 0.0857 | 0.427 | 0.368 |
| P | llm_no_lane (D[:100] + FD, SD) | 0.1151 | 0.0857 | 0.335 | 0.417 |
| T | base | 0.1211 | 0.0706 | 0.355 | 0.432 |
| T | lane | **0.2268** | 0.0706 | 0.473 | 0.331 |
| T | scout | 0.1756 | 0.0706 | 0.421 | 0.331 |
| T | llm_no_lane | 0.1086 | 0.0706 | 0.330 | 0.380 |

Brief T (title, no LLM) gives the same pattern: scout − lane −0.0512 (CI −0.0792 to −0.0241).

**Single arms (OUT R@200).** Lane arms have IN R@200 = 0 by construction.

| Brief | D | X | B | FD | FX | SD | SX |
|---|---|---|---|---|---|---|---|
| P | 0.1350 | **0.2919** | 0.0471 | 0.0960 | 0.1965 | 0.0965 | 0.1892 |
| T | 0.1211 | **0.2634** | 0.0662 | 0.0918 | 0.1823 | 0.0970 | 0.1777 |

Reference: full-patent dense (R2) is 0.1618.

## Post-hoc descriptive check (not pre-declared; no decision attached)

The lane drops every family that shares an IPC3 code with the query. Strict-OUT targets are defined as families sharing no IPC3 code with the query. The lane's candidate set is therefore exactly the set of possible OUT targets. To size this effect, the full-patent dense query (R2) was run under the same mask:

| Run | OUT R@200 | OUT R@100 | OUT hit@200 |
|---|---|---|---|
| R2, full candidate set | 0.1618 | 0.1120 | 0.407 |
| R2, IPC3-masked | **0.3341** | 0.2793 | 0.625 |
| R2[:100] + masked R2 | 0.2975 | 0.1120 | 0.570 |

- Masked R2 − R2: +0.1723 (CI +0.1392 to +0.2058). The mask about doubles OUT recall for the full patent too.
- Brief P masked − R2 masked: −0.0423 (CI −0.0704 to −0.0139). Under the same candidate set, the short brief loses modestly to the full patent.

## Reading

1. **LLM abstraction lowered recall at every level.** Function texts and solution sketches were below the plain brief, both without the mask (FD/SD ≈ 0.096 vs D 0.135) and with it (FX/SX ≈ 0.19 vs X 0.29). This agrees with Weller et al. (2024): expansion hurts strong retrievers.
2. **The lane result is mostly definitional.** Masking by the query's own IPC3 codes uses only search-time metadata and no relevance labels. Its gain, however, comes from removing in-domain competitors from a ranking that is scored only on cross-domain targets. It is the protocol question that DAPFAM leaves open (whether OUT ranks only OUT candidates or the full set). As a product feature ("show me only fields outside my classes") it is legitimate. As a research claim it is not new evidence.
3. **The lane has a cost.** IN R@200 fell from 0.466 to 0.368 on brief P, because half of the budget leaves the query's own classes.
4. **Short briefs lose little.** Title-only and problem briefs are within about 0.01–0.04 of the full patent under the same candidate set. This matches DAPFAM's own query-view results.

## Generation (Qwen3-8B, dev)

- Prompt `ptp-solution-scout-v1`; greedy decoding, fp16, eager attention; Tesla V100-SXM2-32GB; torch 2.8.0+cu128.
- 2,370 calls (474 × 5), 6 failed, 0 retries, 0 truncated. Runner status `PARTIAL` because of the failures.
  - All 6 failures were function texts that came out 1–2 words below the 25-word minimum: 5 on brief P, 1 on brief T. Each gives an empty FD/FX list for that query.
- Tokens: 715,973 prompt and 211,154 output. Mean latency 6.29 s per call; 14,903 s in total; peak GPU memory 17.6 GB.
- Word counts (mean, range):
  - brief P 51.9 (33–85);
  - F on T 39.5 (26–56);
  - F on P 36.6 (25–55);
  - S on T 122.1 (102–141);
  - S on P 119.3 (100–142).
- Input sha256 `be023ee9…`, output sha256 `daf8bf02…`. Generated texts stay in private artifacts.
- Not done:
  - the LLM target-recall probe;
  - the vocabulary-overlap check between brief P and the targets.

  Both were to be added only if the check passed.

## Inputs and code

| Artifact | sha256 (prefix) |
|---|---|
| Rankings, brief P | `d` `83397f6c`, `x` `42db52e1`, `bm25` `5ae3f5fa`, `f` `28bf2ff8`, `fx` `7b18a3d3`, `s` `be661ef5`, `sx` `aadc1d70` |
| Rankings, brief T | `d` `c6ca3fc8`, `x` `7b1a1e30`, `bm25` `81a21634`, `f` `80958a76`, `fx` `57c3ab30`, `s` `87490184`, `sx` `d027fd22` |
| Masked R2 rankings (post hoc) | `6ec5f011` |
| Masked R2 input (dev ids only) | `10323214` |
| Split | `dd76c019` |
| `run_qwen_scout_actions.py` (checked on dr-train) | `5b635176` |
| `run_dapfam_dense_pool.py` (checked on dr-train) | `4112c277` |

Full ranking hashes are in the results JSON. The dense runs reused the Stage 0 passage vectors (`9a385bcf…`), PatEmbed-large revision `2d5c0f92`, and `family-ipc3` `b401e1d0`. All 13 dense runs and both BM25 runs reported `PASS` and `labels_used: false`.

## Commands

- dr-train: `run_scout_dev.sh` (`run_qwen_scout_actions.py generate`, about 4.1 h)
- `python scripts/healthtech/build_scout_inputs.py --records <private>/scout/scout-dev-records.jsonl --qwen-output <private>/scout/scout-dev-v1.out.jsonl --output-dir <private>/scout/inputs` (exit 0)
- dr-train: `run_scout_dense_dev.sh` (12 runs of `run_dapfam_dense_pool.py`), plus one post-hoc run on `x-R2.jsonl`
- `python scripts/healthtech/run_dapfam_bm25_pool.py --corpus <private>/corpus-tac.jsonl --queries-jsonl <private>/scout/inputs/bm25-{P,T}.jsonl --output <private>/scout/rankings/rankings-bm25-{P,T}-dev.jsonl` (exit 0)
- `python scripts/healthtech/analyze_solution_scout_dev.py --rankings-dir <private>/scout/rankings --r2 <private>/dense-single/rankings-dense-single-top200.jsonl --split <private>/split.json --masked-r2 <private>/scout/rankings/rankings-x-R2-dev.jsonl --output docs/healthtech/audits/ptp-solution-scout-feasibility-20261105/feasibility-dev-results.json` (exit 0)

The first run had no `--masked-r2`. With the option added, the pre-declared part of the output is identical (checked by parsed-JSON comparison); only the `post_hoc_descriptive` block and one input hash are new.

Base revision `e4bdbab`. Cost: USD 0 in paid calls; about 4.1 h of V100 for generation plus a few minutes of dense encoding.
