# Solution Scout frozen evaluation, run P2: E3 grounding and E4 latency (7 Nov 2026)

- **Status: PASS.** E3 and E4 each ran once, as frozen in [SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md](../../research/SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md).
  - The three new generation receipts say `PARTIAL` because some calls failed to parse. The frozen rule scores those as 0 on G1 and G2; they are counted below, not retried.
- **E3 decision: `ADOPT_V1`.**
  - The product default is **not** switched in this run. That is the next step and needs the owner.
- No DAPFAM test data was read. No paid calls (USD 0). V100 time was about 66 min.
- Base commit: `4c5a882` (protocol freeze). Handoff commit before launch: `b928456`. `src/`, `scripts/` and `tests/` are unchanged since the freeze (`git diff --stat 4c5a882 -- src scripts tests` is empty). The candidate is the commit that adds this file.
- Results files: [e3-grounding.json](e3-grounding.json) (aggregates only) and [e4-latency.json](e4-latency.json).
  - Generated rationales and DAPFAM text stay in `../_private_artifacts/`. Only hashes and aggregates are here.

## E3: quote by reference (v1) vs free quotes (v0)

**Sample:** 236 candidate pairs in 68 clusters.
- **HUPD demo:** 56 pairs, 8 briefs.
- **DAPFAM dev:** 180 pairs, 60 OUT-eligible dev queries × other-fields top 3 of brief P.

**Model:** Qwen3-8B rev `b968826d9c46dd6066d109eabc6255188de91218`, greedy decoding, fp16, eager attention, max 400 new tokens, on a Tesla V100-SXM2-32GB.

### Decision rule outcome

| Measure | v0 | v1 | Δ v1 − v0 (cluster bootstrap) | 95% CI | Rule | Met |
|---|---|---|---|---|---|---|
| G1 fully grounded | 0.665 | 0.911 | **+0.237** | +0.176 to +0.300 | lower bound > 0 | yes |
| G2 NLI support proxy | 0.508 | 0.581 | **+0.075** | −0.013 to +0.166 | lower bound > −0.05 | yes |

- Bootstrap: 5,000 resamples, seed `20261106`. The unit is the cluster (one HUPD brief or one DAPFAM query). Bootstrap p: G1 0.0000, G2 0.0932.
- The v0 and v1 columns are pooled pair rates. Δ is the mean of per-cluster means, as `grounding_decision` computes it, so it is not exactly the difference of the pooled rates (G1 pooled: +0.246).
- G2 shows non-inferiority, not superiority: its CI includes 0.

### Per-sample rates (descriptive)

| Sample | Pairs | G1 v0 | G1 v1 | G2 v0 | G2 v1 |
|---|---|---|---|---|---|
| DAPFAM dev | 180 | 0.711 | 0.939 | 0.550 | 0.628 |
| HUPD demo | 56 | 0.518 | 0.821 | 0.375 | 0.429 |

### Failures, quotes, tokens, latency

| | v0 | v1 |
|---|---|---|
| Parse failures (of 236) | 1 (0.4%) | 18 (7.6%) |
| Quotes checked | 680 | 624 |
| Quotes matched literally | 578 (85.0%) | 618 (99.0%) |
| Invalid sentence references | — | 6 (all in HUPD) |
| Prompt tokens | 147,365 | 152,642 |
| Output tokens | 45,284 | 21,419 |
| Mean latency per call | 13.34 s | 6.37 s |

**Parse failures by cause:**
- **v0:** 1 DAPFAM call ran to the 400-token cap and returned no complete JSON object (`no JSON object`).
- **v1:** all 18 (11 DAPFAM, 7 HUPD) returned 4–9 sentence numbers where the prompt asks for 1–3 (`evidence must be 1-3 integers`). All other keys were well formed.
  - This is a model format failure under the frozen contract, not a code bug. Each is scored 0 on G1 and G2.
  - If v1 becomes the default, the product needs a declared rule for this case. Any such rule is a new design decision, not part of this result.

**Unmatched quotes:**
- **v1:** the 6 unmatched quotes are exactly the 6 invalid references. Every valid reference rendered to a literal match, as designed.
- **v0:** 102 quotes were unmatched paraphrases or joins.

### Caveats

- **G1 under v1 is high partly by construction.** The system renders the cited sentences itself, so a valid reference is always literal. G1 shows that the mechanism removes misquotes. It does not show that the model picked the right sentences; G2 is the closer check on that.
- **G2 is a proxy.** `cross-encoder/nli-deberta-v3-base` is an NLI model, not expert judgement. Its premise is only the matched quotes, its hypothesis is `what_it_does`, and the threshold is P(entailment) ≥ 0.5. No developer or expert relevance judgement was made here.
- **Sample size.** The sample is small (68 clusters), and the HUPD part (8 briefs) is weighted equally per cluster with the DAPFAM queries.
- **Scope.** These are dev and demo data only. E3 says nothing about retrieval quality.
- **HUPD v0 provenance.** The HUPD v0 output was generated on 6 Nov 2026 (receipt `PASS`, 56/56), before the freeze. All 472 stored `messages_sha256` values (HUPD v0 and v1, DAPFAM v0 and v1) were recomputed from the frozen prompts and inputs, and every one matches. So both arms used the frozen prompt text.
- **`build-dapfam` reads all qrels.** It loads `qrels_all.parquet` in full and keeps only queries the Stage 0 split assigns to `dev`. No test label enters the sample or any output.

## E4: CPU live search on the HUPD index

Measured on the owner's laptop: Windows 11, 12 logical CPUs, torch 2.15.0+cpu, 8 threads, PatEmbed-large. Index: 56,528 families, 74,670 passages. 8 demo briefs × 5 repeats after one warm-up.

| Stage | Median | Max | n |
|---|---|---|---|
| Brief encode | 533.4 ms | 759.4 ms | 40 |
| Search | 124.1 ms | 134.1 ms | 40 |

The whole script, index load included, took about 59 s wall time. No local server was running during the measurement.

**V100 rationale latency per call (from the E3 outputs):**

| Run | Calls | Median | Max | Output tokens (median / max) | Receipt total |
|---|---|---|---|---|---|
| HUPD v0 (6 Nov) | 56 | 11.79 s | 21.48 s | 172.5 / 315 | 695 s |
| DAPFAM v0 | 180 | 13.24 s | 28.34 s | 189 / 400 | 2,454 s |
| DAPFAM v1 | 180 | 6.23 s | 9.43 s | 91 / 118 | 1,148 s |
| HUPD v1 | 56 | 6.39 s | 7.49 s | 90.5 / 107 | 356 s |

- Model load took about 4 s per run.
- Peak GPU memory was 16.8–17.3 GB.
- v1 halves output tokens and latency because it returns numbers instead of copying passages.

## Commands and exit codes

All local commands ran from the repository root. Here P = `../_private_artifacts/healthtech/ptp-org-adaptive-20261105`, H = `../_private_artifacts/healthtech/scout-public-demo`, and J = `/home/chaw/patent-to-pilot-jobs/scout-public-demo` (dr-train).

| # | Command | Exit |
|---|---|---|
| 1 | `hf download cross-encoder/nli-deberta-v3-base --revision 6c749ce3425cd33b46d187e45b92bbf96ee12ec7 --local-dir C:/Users/User/.ptp-models/nli-deberta-v3-base --exclude "onnx/*" "pytorch_model.bin"` | 0 |
| 2 | `python scripts/healthtech/run_qwen_scout_rationales.py build-dapfam --split $P/split.json --qwen-dev $P/scout/scout-dev-v1.out.jsonl --records $P/scout/scout-dev-records.jsonl --x-rankings $P/scout/rankings/rankings-x-P-dev.jsonl --output $P/scout/e3-dapfam-dev-inputs.jsonl` → 60 queries, 180 pairs | 0 |
| 3 | `scp` script to `code-v3/scripts/healthtech/` and inputs to `$J`; sha256 checked on both sides | 0 |
| 4 | On dr-train: `setsid nohup $J/run_e3_generate.sh` ([copy](run_e3_generate.sh)); three `generate` runs in sequence on `CUDA_VISIBLE_DEVICES=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089`, 05:39:38Z–06:46:07Z | dapfam-v0 0, dapfam-v1 0, hupd-v1 0 |
| 5 | `C:/Users/User/.ptp-scout-venv/Scripts/python scripts/healthtech/analyze_scout_grounding.py --inputs $H/rationale-inputs.jsonl $P/scout/e3-dapfam-dev-inputs.jsonl --v0 $H/rationales-v0.out.jsonl $H/e3-dapfam-v0.out.jsonl --v1 $H/e3-hupd-v1.out.jsonl $H/e3-dapfam-v1.out.jsonl --nli-model-dir C:/Users/User/.ptp-models/nli-deberta-v3-base --output docs/healthtech/audits/ptp-scout-frozen-eval-20261107/e3-grounding.json` (06:46:56Z–06:53:52Z) | 0 |
| 6 | `C:/Users/User/.ptp-scout-venv/Scripts/python scripts/healthtech/measure_scout_latency.py --data-dir ../_private_artifacts/healthtech/scout-public-demo --model-dir C:/Users/User/.ptp-models/patembed-large --output docs/healthtech/audits/ptp-scout-frozen-eval-20261107/e4-latency.json` (06:54:06Z–06:55:05Z) | 0 |
| 7 | `python -m pytest` → 746 passed, 1 skipped | 0 |
| 8 | `cd frontend/healthtech-web && npm test` → 81 passed, 1 skipped | 0 |

## Hashes and revisions

**Models:**

| Model | Revision | Notes |
|---|---|---|
| Qwen3-8B | `b968826d9c46dd6066d109eabc6255188de91218` | Path `/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/qwen3-8b` |
| NLI `cross-encoder/nli-deberta-v3-base` | `6c749ce3425cd33b46d187e45b92bbf96ee12ec7` | Apache-2.0 per its model card. config.json `897e756eb59d3183adb505952e7910e7cbc7750a43f3b3747a96b688d2b02a47`; model.safetensors `d8148c6d49e0a7925134294c56326c71fe0ab1dc390e37355e00c7efbb488afa`; labels 0 contradiction, 1 entailment, 2 neutral |
| PatEmbed-large | as in the [public demo audit](../ptp-scout-public-demo-20261106/README.md) | — |

**Software on dr-train:** torch 2.8.0+cu128.

**Code (sha256 of working-tree files at the freeze):**

| File | sha256 |
|---|---|
| `scripts/healthtech/run_qwen_scout_rationales.py` (identical on dr-train `code-v3`) | `64ef8149a183e3ed7cd45ca7212769106b988eea955da2a35ca16c72c175af7d` |
| `src/patent_to_pilot/healthtech/local_execution.py` (identical on dr-train) | `f6e56c4d7ac3699e88b158299a9c62428a7f15fb37af0ab0d082d4b58c306cf2` |
| `scripts/healthtech/analyze_scout_grounding.py` | `956f3235889cca322eaa91718c745ac1e6e1d822b3024e3ca50bcec3cf4ab10b` |
| `scripts/healthtech/measure_scout_latency.py` | `6a6869d017b1753028168309f8c378a63e9aa7e5629a84454062ee63cdbf8b6b` |
| `src/patent_to_pilot/evaluation/scout_frozen.py` | `78d06b52486fd0e32b951a21dd97885f2da73a381cfdbb313fa5661205fa816f` |
| `src/patent_to_pilot/healthtech/scout.py` (`check_quote`) | `2f827ffd39a44cad28d73ea0720bce5103fc3f68f9fe23c38371f69b7b7d486f` |

**Data (private; files stay outside Git):**

| File | sha256 |
|---|---|
| `$H/rationale-inputs.jsonl` (HUPD, 56) | `c26c97422e178927c5c2f7c06047f9524c1531cfe81360b766dd96a2cdf8c7cc` |
| `$P/scout/e3-dapfam-dev-inputs.jsonl` (DAPFAM dev, 180) | `db4ca964ff4a814e0401298aaa08497989528c835e51192f6f9c9a3b962ae10a` |
| `$H/rationales-v0.out.jsonl` (HUPD v0) | `f5c072de16e8309d3e85d1148b7b32fa8e374036110b6773a22bebb97b60e4d0` |
| `$H/e3-dapfam-v0.out.jsonl` | `b469078f8c877ec8cff1217bed26fff81aef11e6bb89deb35e957c105fd1a6c6` |
| `$H/e3-dapfam-v1.out.jsonl` | `8e203f6835feb93754cf52f2f6e6ac93499caf6366f825d197471dca468f7637` |
| `$H/e3-hupd-v1.out.jsonl` | `eb2bc0669d246ab9ab49995e68be9a001ba5fdfcccb7695b3752f13dcf637b54` |

The outputs and their `.receipt.json` files are in `$H`, and also on dr-train in `$J`. Their sha256 values match on both sides.

**Results (in Git):**

| File | sha256 |
|---|---|
| `e3-grounding.json` | `8f0b8a3c091445c81cc581f0b2f69e47192cdd71ffe1300b0149d5a3801eacbc` |
| `e4-latency.json` | `066514f522b31b356909df8eb55ef4c2a92efff0479754ca67f9d92e1a2a3308` |

## Next

1. **Owner decision:** switch the product default to v1, as E3 permits.
   - This needs a declared rule for answers with more than 3 sentence numbers.
   - Until then, the demo keeps the v0 book, with unmatched quotes flagged.
2. **P3:** the one-time DAPFAM test read (773 P-brief calls, then U/O/X rankings, then `analyze_scout_frozen_test.py` once). Not started.
