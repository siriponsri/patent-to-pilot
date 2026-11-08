# MTM dev phase 2: Qwen3-8B reranker, reranker fusion, function channel

- **Status:** PASS (run). V6 text generation is PARTIAL: 4 of 1,985 function texts failed and were scored as X, as declared.
- **Scientific result on dev:** **V4 (Qwen3-8B yes/no rerank of the X top 30, fused with dense) is the first method to beat the dense X lane on the primary cell.**
  - Its out-of-fold gain on P/main hit@20 is +0.017 [+0.010, +0.025].
  - It is the only method eligible for the single test read under the fixed carry-forward rule.
  - V5 and V6 are not eligible.
- **Split:** dev only (1,985 queries). The test split is sealed.
- **Methods:** entries V4–V6 in the [methods log](../../research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md), declared before the run and approved by the owner on 8 Nov 2026.
- **Run:** code `git archive 2691931`, run on dr-train (Tesla V100-SXM2-32GB) by [run_dev2.sh](run_dev2.sh) with `PROMPTS=N,C`. Every step exit=0, 06:55Z–11:53Z on 8 Nov 2026 ([status.log](status.log)). No retries.
- **V4 smoke test (dev, 300 pairs):** N 13.9 pairs/s and C 13.0 pairs/s, projecting 2.5 h for both prompts. That is under the 8 h rule, so both ran. The smoke scores were not analysed.
- **Private files:** raw scores, generated function texts and rankings stay on dr-train under `/home/chaw/patent-to-pilot-jobs/mtm-20261107/dev2/`. Only hashes are here.

## Files

| File | sha256 | Contents |
|---|---|---|
| [dev-phase2.json](dev-phase2.json) | `e91bfad5…` | all measures, contrasts, and the CV groups `llm`, `cef`, `fch` |
| [receipt-rerank-llm-P-dev.json](receipt-rerank-llm-P-dev.json) | `15217bbc…` | V4 scoring (details below) |
| [receipt-fusion-llmN-llmC-P-dev.json](receipt-fusion-llmN-llmC-P-dev.json) | `127cd1fe…` | V4 fusion |
| [receipt-fusion-cef-P-dev.json](receipt-fusion-cef-P-dev.json) | `6fb19e2e…` | V5 fusion, P |
| [receipt-fusion-cef-T-dev.json](receipt-fusion-cef-T-dev.json) | `125036b4…` | V5 fusion, T |
| [briefs-F-dev.out.jsonl.receipt.json](briefs-F-dev.out.jsonl.receipt.json) | `6d83e8c7…` | V6 generation |
| [receipt-fch-P-dev.json](receipt-fch-P-dev.json) | `1de7c884…` | V6 channel |

- **V4 scoring:**
  - Qwen3-8B, all 5 weight shards hashed; prompt sha256 N `4c894220…`, C `6d5feb5b…`.
  - Answer token ids: yes `[9693, 9454]`, no `[2152, 2753]`.
  - 59,550 pairs per prompt (1,985 × 30); 36.7 M prompt tokens.
  - N took 4,828 s (12.3 pairs/s) and C 5,226 s (11.4 pairs/s); peak GPU memory 18.3 GB.
- **Fusion sanity check:** λ = 1 reproduces the baseline head for **1,985 of 1,985** queries in every fusion receipt, and no query lacks scores.
- **V6 generation:** 1,985 calls, 4 failed (too short), 0 truncated, mean 3.3 s per call. 1,981 queries have a function text; the other 4 are scored as X.

## Primary: query view P, corpus view main (X hit@20 0.180, hit@100 0.313, MRR@100 0.065)

Δ is method − X on hit@20, with a paired bootstrap 95% CI (5,000 resamples, seed `20261107`). λ is the dense weight; λ = 0 is the method alone.

| Method | λ | hit@20 | Δ hit@20 [95% CI] | MRR@100 |
|---|---|---|---|---|
| V4 R-neutral | 0 (alone) | 0.191 | +0.012 [+0.003, +0.020] | 0.073 |
| V4 R-neutral | 0.5 | 0.197 | +0.017 [+0.010, +0.025] | 0.077 |
| V4 R-neutral | 0.7 | 0.195 | +0.015 [+0.008, +0.021] | 0.072 |
| V4 R-neutral | 0.9 | 0.186 | +0.007 [+0.003, +0.011] | 0.068 |
| V4 R-cross | 0 (alone) | 0.183 | +0.003 [−0.007, +0.013] | 0.064 |
| V4 R-cross | 0.5 | 0.189 | +0.010 [+0.002, +0.017] | 0.071 |
| V4 R-cross | 0.7 | 0.190 | +0.010 [+0.004, +0.017] | 0.068 |
| **V4 CV, 2 prompts × 6 λ (out of fold)** | — | **0.197** | **+0.017 [+0.010, +0.025]** | 0.077 |
| V5 bge + dense | 0 (alone) | 0.153 | −0.027 [−0.043, −0.013] | 0.051 |
| V5 bge + dense | 0.6 | 0.188 | +0.008 [−0.001, +0.017] | 0.069 |
| **V5 CV (out of fold)** | — | **0.187** | **+0.007 [−0.001, +0.015]** | 0.068 |
| V6 function channel | 0 (alone) | 0.099 | −0.081 [−0.096, −0.066] | 0.034 |
| V6 function + P | 0.9 | 0.177 | −0.003 [−0.007, +0.002] | 0.065 |
| **V6 CV (out of fold)** | — | **0.177** | **−0.003 [−0.007, +0.002]** | 0.065 |

CV choices by fold:

- **V4:** R-neutral λ 0.5 in all 4 folds, which is also the full-dev choice.
- **V5:** λ 0.7, 0.6, 0.7 and 0.6; the full-dev choice is λ 0.6.
- **V6:** λ 0.9 in all 4 folds.

V4 and V5 reorder only the head (top 30 and top 100), so their hit@100 equals X's (0.313) by construction. V6 can change the top 100. Out of fold it adds 0.8% new@100 and loses 0.9%. Alone it adds 2.7% but loses 13.1%.

## Secondary cells

- **V5 on query view T, main** (X hit@20 0.129): CV out of fold +0.015 [+0.008, +0.023], with λ 0.6, 0.6, 0.5 and 0.5. Fused with dense, the bge reranker helps the short title query, but not P.
- **V6 in the other corpus views (P):** CV out of fold is −0.002 (small), −0.005 (matched) and −0.001 (uniform). Every CI includes 0.
- **V4 ran on P/main only, as declared.**

## Findings

1. **An LLM reranker fused with dense is the first dev gain on the primary cell.**
   - Out of fold, hit@20 rises from 0.180 to 0.197, +9.5% relative, about 34 of 1,985 queries. MRR@100 rises from 0.065 to 0.077.
   - The gain comes from reordering the top 30: targets at ranks 21–30 move into the top 20. Recall at depth is unchanged.
2. **The cross-field prompt did not help. The neutral prompt was better at every λ below 0.9 and equal at 0.9.**
   - Alone, R-neutral gives +0.012 and R-cross +0.003 (CI includes 0).
   - Telling the model that the patent "may come from a different technical field" weakened its ranking.
   - This is a prompt-sensitivity result, in the line of the owner's published reranking work.
3. **Fusion matters.**
   - Every reranker alone is weaker than or close to its fused form: V4 neutral +0.012 alone vs +0.017 fused; bge −0.027 alone vs +0.007 fused.
   - The dense score carries signal that the rerankers miss.
4. **The function channel does not help**, which agrees with the earlier DAPFAM finding that LLM function rewrites lower recall. Alone it loses 13% of the baseline's top-100 hits.

## Carry-forward (fixed rule; the owner freezes the list)

- **Eligible:** V4 only (CV out-of-fold lower bound +0.010 > 0 on P/main). With one carried method, Holm needs no adjustment.
- **The frozen configuration, if the owner approves:**
  - Qwen3-8B with the same weights;
  - prompt R-neutral;
  - X top 30, λ 0.5 (the full-dev choice);
  - the same system message, candidate text and score.
- **What test needs:** V4 scores on the test X top 30 (about 58,650 pairs, about 1.3 h on the V100), then the fusion, then one scoring read under rules §14. The run scripts refuse `-test` names now, so test mode needs a small, separately reviewed change after the freeze.
- **Not eligible:**
  - V5 (lower bound −0.001);
  - V6 (lower bound −0.007);
  - every phase-1b entry.

## Limits

- These are dev results. The test estimate can be smaller: λ and the prompt were chosen on dev, and the out-of-fold estimate corrects for that only within dev.
- One LLM (Qwen3-8B), two prompts and one depth (30) were tried. Deeper heads and other models are untested.
- The gain is in early precision (hit@20, MRR) only. Targets outside the dense top 30 cannot be reached.
- The P query is itself generated by the same Qwen3-8B. The reranker therefore scores a brief written by the same model.
