# Solution Scout: frozen evaluation protocol (E1–E5), 6 Nov 2026

- **Status:** FROZEN at the commit that adds this file. It is written before any DAPFAM test label, test ranking or PatenTEB result is read. The owner approved plan A on 6 Nov 2026.
- **Changes after the freeze:** amendments only, dated, with reasons, and reported as deviations.
- Spec: [SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md](SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md).
- Dev evidence behind the hypotheses: [scout feasibility](../audits/ptp-solution-scout-feasibility-20261105/README.md) and [atlas headroom](../audits/ptp-solution-atlas-headroom-20261106/README.md).

## 0. Shared definitions

- **Benchmark.** DAPFAM (rev `a59a74ce…`, CC BY-NC-SA), Stage 0 split (sha256 `dd76c019…`).
  - Test: 773 queries.
  - A query is **OUT-eligible** if it has at least one positive with `domain_rel = OUT`, and **IN-eligible** if it has at least one positive with `domain_rel = IN`.
  - Unjudged pairs are not negatives. Recall uses positives only.
- **Retriever.** PatEmbed-large (`2d5c0f92…`), Stage 0 passages and vectors, MaxP. Runner `scripts/healthtech/run_dapfam_dense_pool.py`, unchanged in behaviour.
- **Query views (b):**
  - **P:** the problem brief written by Qwen3-8B with the frozen prompt `ptp-solution-scout-v1` (`PROBLEM` only), greedy decoding.
  - **T:** the title only, no LLM.
  - **R2:** the full patent query view from Stage 0, as a reference.
- **Rankings per view** (depth 200, label-free; the query's own IPC3 codes are search-time metadata):
  - **U:** full candidate set.
  - **O:** own field. Only families sharing at least one IPC3 code with the query (runner `allowed_ipc3`).
  - **X:** other fields. Only families sharing none (runner `excluded_ipc3`).
- **Failures.** A failed P generation (outside 25–120 words) is not retried. That query's P rankings are empty and score 0. The count is reported.
- **Statistics.**
  - Paired bootstrap over queries, 5,000 resamples, seed `20261106`. The unit is the query.
  - Effects are reported as Δ with 95% percentile CIs.
  - Holm correction applies within the primary family only.

## E1. What an analyst sees: two-lane shortlist vs a single list (DAPFAM test)

**Pools at budget k ∈ {20, 200}, split evenly:**
- **single** = U[:k].
- **two-lane** = O[:k/2] followed by X[:k/2]. The two lanes are disjoint by construction.

**Primary family (Holm, m = 2), brief P, k = 20:**
- **H1a:** two-lane − single on **OUT Recall@20**, over OUT-eligible queries.
- **H1b:** two-lane − single on **IN Recall@20**, over IN-eligible queries.

These are reported as a trade-off, with no sign predicted.

**Secondary (descriptive, with CIs):** the same contrasts at k = 200; the same contrasts for briefs T and R2; OUT hit@20.

## E2. Protocol effect and brief cost (DAPFAM test)

**E2a, protocol effect.** X[:k] − U[:k] on OUT Recall@k (k = 20, 200) for P, T and R2. This shows how much the reported cross-domain recall depends on whether IN families compete for slots.

**E2b, brief cost:**
- D(P) − D(R2) and D(T) − D(R2) on OUT Recall@200, under the full-candidate set (U) and under the other-fields set (X);
- the same contrasts for IN Recall@200 under U.

Both are descriptive, with CIs. No decision rides on them.

## E3. Grounding of transfer rationales (method: quote by reference)

**Variants:**
- **v0** (`ptp-scout-rationale-v0`): the model copies 1–3 quotes word for word.
- **v1** (`ptp-scout-rationale-v1`):
  - The candidate text is split into numbered sentences (`[S1] …`), using the rule in `split_sentences` in `run_qwen_scout_rationales.py`.
  - The model returns 1–3 sentence numbers, and the system renders those sentences as the quotes.
  - Numbers outside the range are invalid references and count as unmatched quotes.

Same model (Qwen3-8B `b968826d…`), greedy decoding, the same brief and the same candidate text.

**Sample (fixed before generation):**
- **HUPD demo:** the 56 candidates already recorded for v0 (8 authored briefs × own top 2 + other top 5). v1 runs on the same 56.
- **DAPFAM dev:**
  - Draw 60 OUT-eligible dev queries by sha256(`20261106:` + query_id) order.
  - For each, take the other-fields top 3 of brief P (X-P dev rankings from the feasibility check), giving 180 pairs.
  - The brief is the dev P brief. The candidate text is title + abstract + first claim, in the same format as `scout_live.source_text`.
  - Both v0 and v1 run.

**Measures per rationale:**
- **G1 fully grounded:** every quote is found literally in the candidate text (server `check_quote`).
- **G2 support proxy:** a local NLI cross-encoder, `cross-encoder/nli-deberta-v3-base`, Apache-2.0, revision recorded at download.
  - Premise: the matched quotes joined with a space. Hypothesis: `what_it_does`.
  - Supported means P(entailment) ≥ 0.5. A rationale with no matched quote is unsupported.
  - Labelled a proxy: NLI is not expert judgement.
- **Also reported:** parse failures, invalid references, quotes per rationale, prompt and output tokens, latency.

**Decision rule** (pairs pooled; bootstrap over clusters, a cluster being one DAPFAM query or one HUPD brief):
- **Adopt v1 as the product default** if both hold:
  - **G1:** v1 − v0 has 95% lower bound > 0;
  - **G2:** v1 − v0 has 95% lower bound > −0.05 (non-inferiority).
- **Otherwise** v0 stays, and the product keeps flagging unmatched quotes.

## E4. Cost and latency (descriptive)

- **CPU live search on the HUPD index** (`scout_live`, the owner's laptop): 8 demo briefs × 5 repeats; median and max encode and search time.
- **V100 rationale latency and tokens:** from the E3 receipts.

## E5. Replication of the brief cost on independent data (PatenTEB `retrieval_OUT` test)

**Data:**
- PatenTEB `retrieval_OUT` test triplets (15,462 rows, 8,410 query families, 23,774 candidate families). Every positive and negative is cross-domain by construction, so this is an OUT-only candidate set.
- No IPC codes are available, so lanes and protocol effects cannot be replicated here. Only E2b is replicated.
- Text format: `title [SEP] abstract…`.

**Corpus and queries:**
- Candidates: all distinct `pos` and `neg` families, with text split at the first `[SEP]` into title and abstract.
- Positives of a query: all its `pos` families.
- Overlap exclusion, pre-declared: drop every query family and every candidate family that is a DAPFAM query or corpus family.

**Views:**
- **full:** title + abstract with the query prompt.
- **T:** title only.

Same encoder, MaxP over passages.

**Measure:** T − full on Recall@20 and Recall@200 (paired query bootstrap, 5,000, seed `20261106`). Descriptive replication of E2b; no decision.

**Caveat:** the PatenTEB authors also built PatEmbed. The test split is held out from its training, but the same team's design choices may favour it. This is stated in the paper.

## Order of runs and what is read when

1. Commit this file, the code below, and passing tests. **← freeze**
2. **E3** (dev and HUPD only; no test data). Then **E4**.
3. **Test P briefs:** 773 calls, `PROBLEM` only, no retries.
4. **Test rankings:** U/O/X for P, T and R2.
5. **E1/E2 analysis:** one run of `scripts/healthtech/analyze_scout_frozen_test.py`. The first output is final. A bug fix is allowed only as a dated amendment that reports both outputs.
6. **E5:** encode on the V100, then one run of `scripts/healthtech/analyze_patenteb_brief_gap.py`.

## Code frozen with this protocol

| Code | Role |
|---|---|
| `src/patent_to_pilot/evaluation/scout_frozen.py` | Pools, E1/E2 contrasts with Holm, the E3 decision rule, the E5 gap |
| `scripts/healthtech/run_qwen_scout_actions.py` | `build --split-name test`; `generate --actions P` |
| `scripts/healthtech/build_scout_test_inputs.py` | U/O/X inputs for P, T and R2 |
| `scripts/healthtech/analyze_scout_frozen_test.py` | E1/E2; refuses to overwrite its output |
| `scripts/healthtech/run_qwen_scout_rationales.py` | `generate --prompt-version v0/v1`; `split_sentences` (every unit 5–60 words and literal by construction); `build-dapfam` |
| `scripts/healthtech/analyze_scout_grounding.py` | E3 |
| `scripts/healthtech/measure_scout_latency.py` | E4 |
| `scripts/healthtech/analyze_patenteb_brief_gap.py` | E5 `build` / `analyze` |

- Tests: `tests/test_scout_frozen.py`.
- The dense runner and its prompts are unchanged from Stage 0.

## Compute and spend

- About 5–6 V100 hours in total. USD 0 in paid calls.
- Texts derived from DAPFAM and PatenTEB stay in `../_private_artifacts/`. Only aggregates and hashes go into Git.
