# G03 DEV amendment 3, revision 1 (A3r1): PROPOSED, not frozen

**Status: PROPOSED (22 Nov 2026, owner task P0-T04).** It is not frozen and authorises no call. It becomes frozen only at
owner task **P1-T03**, after the TRAIN-only format calibration (P1-T02) and after an approved envelope is recorded
(P1-T01). Until then every number below is a plan, not a result.

**Effectiveness state when this was written:** no A3 effectiveness pilot has run. No A3 DEV or VAL score exists. The only
A3 calls are the four A3r0 TRAIN format-smoke calls (USD 0.00064223). Every change proposed here is therefore
**pre-effectiveness**. If any A3 score is found to exist at freeze time, P1-T03 must disclose it and must not describe
these changes as made "before results".

**Sources:**
- [G03-DEV-AMENDMENT-3-20261122.md](G03-DEV-AMENDMENT-3-20261122.md) (A3r0, frozen);
- [g03-dev-a3-spend.json](g03-dev-a3-spend.json) (smoke receipts);
- [G03-DEV-DECISION-MEMO.md](G03-DEV-DECISION-MEMO.md);
- the owner package `docs/owner/owner-note-22112026/`: `research/A3_CHECKPOINT_AND_AMENDMENT.md`,
  `research/MODEL_AND_PROVIDER_PLAN.md`, `research/SCORE_AND_STATISTICAL_CONTRACT.md`, `config/a3r1_proposed.json`,
  `config/model_profiles.json`, `config/budget_plan.json`, `03_BUDGET_AND_AUTONOMY.md`;
- live free catalogue reads (OpenRouter model, endpoint and docs metadata; Typhoon public docs), retrieved
  2026-11-22T08:46Z. These are recorded in
  [docs/tracking/owner-note-22112026/receipts/P0-T04_provider_readiness.json](../../../tracking/owner-note-22112026/receipts/P0-T04_provider_readiness.json).

## 0. A3r0 is preserved unchanged

- `G03-DEV-AMENDMENT-3-20261122.md` stays as frozen. Its prompt, its 400-token setting and its four-model panel are
  history, not defects to repair in place. These records are kept as they are:
  - `qwen/qwen3.7-flash`, `deepseek/deepseek-v4-flash-0731`, `qwen/qwen3-32b`, `anthropic/claude-haiku-5.5`;
  - the four smoke generation ids;
  - the token counts (697/359, 691/299, 695/231, 1,040/400);
  - Haiku's truncation (3 priors salvaged, keywords lost);
  - USD 0.00064223 and 4 requests.
- Label: **"A3r0: format smoke only; no effectiveness pilot."** One TRAIN query per model is not retrieval evidence. It
  cannot estimate reliability, cost distribution or format completeness.
- The A3r0 caller (`scripts/research/g03_a3_llm_expand.py`, `MAX_TOKENS = 400`) is not changed by this document. Code
  changes for A3r1 belong to the implementation task, after freeze, and must write configuration hashes to receipts.
- **One envelope, versioned science:** A3r0 and A3r1 artifacts are versioned separately. Their spend and requests are
  accounted together in one envelope ledger. The four smoke calls are imported into that ledger.

## 1. Corrections carried from the owner audit

1. **The A3r0 panel was not Claude-heavy.** It was one Claude (Haiku 5.5), two Qwen (Qwen3.7 Flash, Qwen3-32B) and one
   DeepSeek (V4 Flash 0731): three lineages, with Qwen counted twice.
2. **Haiku's truncation is a format result, not a quality result.** It hit the 400-token ceiling and lost its keywords.
   The cause is the ceiling and the contract. It is no evidence that Haiku is a worse query-expansion generator.
3. **A3r0 had a cost-feasibility gap.**
   - The owner's single-query estimate puts a Haiku Stage B at about USD 7.8. That alone exceeds the E1 USD 6.00 stop.
   - Yet A3r0 allowed Haiku to win the pilot. A pilot could therefore select a model whose declared Stage B could not
     finish under the approved envelope.
   - A3r1 closes this gap with the Stage B eligibility rule in §6.
4. **The request cap leaves little retry headroom.** Planned initial requests are 4 smoke + 128 calibration + 8,000
   pilot + 25,545 Stage B = **33,677**. Under the E1 cap of 35,000, that leaves 1,323 requests (3.9%) for transport
   retries and Workbench checks. A3r0's "up to 2 retries per request" cannot be exercised for every request.
5. **Stage B count.** A3r0 wrote "about 25,600". From the recorded manifests the figure is
   25,626 − 2,000 + 1,919 = **25,545**. This must be re-verified at freeze; see §11, item 1.
6. **Routing price spread.** A3r0 left provider routing to OpenRouter. The live endpoint list shows a wide spread for
   DeepSeek V4 Flash 0731: completion prices from USD 0.132 to USD 1.32 per 1M tokens, and quantizations fp4, nvfp4, fp8
   and fp32. Unpinned routing makes both the cost bound and the served-model identity unknown. A3r1 pins routing (§3).
7. **Price drift is already visible.** The owner config lists DeepSeek V4 Flash 0731 input at USD 0.0419/M. The live
   catalogue reads USD 0.0443/M. Prices are re-read at freeze, never copied from older notes.
8. **Haiku ignores `temperature` and `seed` on OpenRouter**, so A3r0 Haiku outputs were not reproducible. This is kept
   as a disclosed property of the historical panel.

## 2. Panel (proposed): four models, three backbone lineages

| Profile | Exact model id | Provider route | Lineage | Role |
|---|---|---|---|---|
| `qwen3_32b` | `qwen/qwen3-32b` (canonical `qwen/qwen3-32b-04-28`; weights `Qwen/Qwen3-32B`) | OpenRouter | **Qwen3** | Reproducible open-weight reference; continuity with A3r0 smoke |
| `deepseek_v4_flash` | `deepseek/deepseek-v4-flash-0731` (canonical `deepseek/deepseek-v4-flash-20260731`; weights `deepseek-ai/DeepSeek-V4-Flash-0731`) | OpenRouter | **DeepSeek** | Independent general challenger |
| `gemini_25_flash_lite` | `google/gemini-2.5-flash-lite` (canonical same; closed weights) | OpenRouter (Google AI Studio is the only upstream) | **Gemini** | Independent closed challenger |
| `typhoon25_api` | `typhoon-v2.5-30b-a3b-instruct` (weights card `typhoon-ai/typhoon2.5-qwen3-30b-a3b`) | **Typhoon native API** `https://api.opentyphoon.ai/v1`, not on OpenRouter | **Qwen3 (Thai-adapted)** | Thai-adapted challenger |

**Why this is three lineages, not four:**
- Typhoon2.5 is built on Qwen3 30B-A3B. Its card says "based on Qwen3 30B A3B", and its licence link points to
  `Qwen/Qwen3-30B-A3B-Instruct-2507`; the exact parent checkpoint is not declared.
- Qwen3-32B and Typhoon2.5 therefore share the Qwen3 pretraining family and its tokenizer. Most pretraining data is
  shared, and so are the systematic errors and memorisation that come with it. Typhoon adds Thai-focused continued
  training and post-training.
- The architectures differ (32B dense vs 30B-total, 3B-active MoE), but architecture is not lineage. Agreement between
  these two models is weaker evidence than agreement between, say, DeepSeek and Gemini.
- The panel is a purposeful set of roles, not four independent samples of the LLM population. Any "consistent across
  models" statement must say "across three lineages, two of them single-model".

**Optional controls (not in the primary panel, not run unless a declared need arises):**
- `qwen/qwen3.7-flash` (efficiency control);
- `anthropic/claude-haiku-5.5` (historical reference). It must pass the same calibration before any use, and it has no
  temperature or seed control;
- Typhoon `typhoon-v2.1-12b-instruct` (Gemma lineage; Gemma terms).

**No silent substitution.**
- There is no OpenRouter Typhoon id; none was found by catalogue search ("typhoon", "scb10x", "thai").
- If Typhoon access cannot be verified, the arm is recorded as **incomplete**. No other checkpoint replaces it.
- See §6.3 for the pre-pilot fallback.

## 3. Common generation contract (proposed)

| Item | A3r0 | A3r1 proposal | Pre-effectiveness justification |
|---|---|---|---|
| Prompt (system + user) | A3r0 text | **Identical to A3r0, byte for byte** | Unchanged; keeps H/K route definitions comparable |
| Input fields | title, abstract, first claim; abstract and claim cut to 1,500 chars at last whitespace | Unchanged | — |
| `max_tokens` | 400 | **800 for every model** (common ceiling) | Haiku truncated at 400; 3 × 70-word abstracts + 25 terms + JSON ≈ 350–450 tokens leaves no margin at 400 |
| Temperature | 0 | 0 | — |
| Seed | 20261122 | 20261122 where supported; disclosed where not (Typhoon docs do not list `seed`) | — |
| Reasoning | off | off, by the model's own switch: Qwen3-32B `reasoning.enabled=false`; DeepSeek V4 Flash `reasoning.effort="none"` (its default is reasoning **on**, effort `high`); Gemini 2.5 Flash-Lite `reasoning.enabled=false` (internal reasoning would be billed at the output rate); Typhoon2.5 is an instruct model with no documented switch, so nothing is sent | Reasoning tokens are billed as output and count against `max_tokens`; calibration records `reasoning_tokens` per response |
| `response_format` / JSON mode | not used | **Not used** (Typhoon does not document it; one model with a constrained decoder would break the common contract) | — |
| Other sampling parameters | defaults | Provider defaults; `repetition_penalty` is **not** set. The Typhoon card suggests 1.05; using it for one model only would break the common contract. Disclosed | — |
| Provider routing (OpenRouter) | left to OpenRouter | **Pinned** per model (below) with `require_parameters: true`, `allow_fallbacks` limited to the listed providers, and `max_price` set to the reservation ceiling. The served provider, quantization and tier are recorded per response | Removes the 10× price spread and unknown quantization (§1, item 6) |
| Typhoon transport | n/a | Native OpenAI-compatible endpoint. Rate limits are 5 req/s and 200 req/min; the caller must throttle below them. 429 counts as a transport failure | — |

**Proposed routing pins** (finalised at P1-T01 from a fresh catalogue read):
- **Qwen3-32B:** `only` DeepInfra and Tenstorrent, fp8; `max_price` 0.14 / 0.42 per 1M. This excludes the SiliconFlow
  endpoint, which reads status −2 (degraded).
- **DeepSeek V4 Flash 0731:** `quantizations: ["fp8"]`, seed-supporting providers only (`require_parameters`);
  `max_price` 0.15 / 0.30 per 1M. Live fp8 endpoints within that ceiling that list `seed`: DeepInfra flex, standard and
  priority, Cohere, Parasail, CoreWeave, and Nebius (degraded).
- **Gemini 2.5 Flash-Lite:** Google AI Studio standard tier; `max_price` 0.10 / 0.40. The flex tier at 0.05 / 0.20 may
  serve some requests, and the tier is recorded. Priority at 0.18 / 0.72 is excluded.

**Input-length check.** Typhoon docs disagree on context:
- the models page says 128K;
- the API reference and tokens page say `max_tokens` ≤ 8,192 shared between prompt and completion.

The A3 prompt (≈ 700–1,100 tokens) plus 800 output tokens fits the stricter 8K reading. Calibration must still confirm
that no request is refused for length.

## 4. Format calibration (P1-T02, TRAIN only)

**Population:** allowed TRAIN rows of `bridgeret/texts-v1/queries.jsonl` with `block == "TRAIN"`. App 12000001 (the
A3r0 smoke app) is excluded so that calibration is a fresh sample. No P1-DEV, VAL or TEST row is read. No label, qrel or
retrieval score is read or computed.

**Deterministic selection (same 32 cases for every model):**
- Let h(a) = sha256(`"g03-a3r1-format-v1" + app_id`) as lowercase hex, ordered ascending.
- **Long stratum (16):** the 16 smallest h(a) among TRAIN rows whose abstract **and** first claim both reach the
  1,500-character cut. These stress the input and output contract (model plan §7: "include long inputs").
- **General stratum (16):** the 16 smallest h(a) among the remaining TRAIN rows.
- The 32 app_ids and their input sha256 are written to `P1-T02_calibration_manifest.json` before the first call.

**Attempts:** 32 per model × 4 = **128 initial attempts**. Only transport failures are retried (§5). Every attempt,
retry and billed failure is kept.

**Recorded per response:**
- raw text;
- parse class (`json`, `salvaged`, `none`);
- number of non-empty priors, and whether keywords are non-empty;
- `finish_reason` and truncation;
- prompt, completion and reasoning tokens;
- `usage.cost` (or "unknown");
- served provider, quantization and tier;
- generation id and wall time.

**Format gate (a model may enter the DEV pilot only if all hold):**
- (a) **complete** responses ≥ 30 of 32. Complete means valid JSON, exactly 3 non-empty priors, non-empty keywords and
  `finish_reason` = stop;
- (b) truncations at 800 tokens ≤ 1 of 32;
- (c) `reasoning_tokens` = 0 on every response, or is reported and billed in a way the ledger reconciles;
- (d) cost is reconciled for every billed response. For Typhoon, the zero-cost status is recorded (§6.3).

**If a model fails the gate:**
- The only permitted repair is a **common** contract change applied to every model. Examples: a common ceiling of
  1,200, or a declared common provider mapping fix.
- The change is frozen as a new calibration config. All four models are re-run once on the **same 32 cases**. This is a
  contract change, not a content retry, and all earlier attempts are preserved.
- At most **one** such revision is allowed. A model that still fails is **format-ineligible**, which is a material
  panel change (owner question). It is not reported as a retrieval loser.
- No per-model salvage is called "equivalent". Missing keywords are recorded as missing.

**Measured token statistics for each model** (mean, p95 and max of prompt and completion tokens) replace the planning
assumptions in §6 at freeze.

## 5. Failure and truncation policy (DEV pilot and Stage B)

- **Transport failures:** HTTP 408, 429 and 5xx, timeouts and connection errors.
  - Retried up to 2 times with exponential back-off and jitter.
  - Each attempt reserves one request and its own conservative cost **before** dispatch.
  - Retries draw on a declared **global retry pool**: 3% of planned initial requests per stage, about 60 per model
    pilot and about 766 for Stage B.
  - When the pool is empty, a failed request is recorded as `transport_failed` and is not retried.
- **Content failures** are never retried: empty reply, unparsable reply, truncation, or a refusal.
- **Route construction is common and unchanged from A3r0:**
  - H uses every complete prior string present, including those salvaged from a truncated reply;
  - K uses `keywords` plus the priors;
  - a response is **usable** if it yields ≥ 1 non-empty prior or non-empty keywords;
  - a query with no usable response gets no H/K output and **stays in the analysis population**. It scores from its
    other windows only, exactly as in A3r0.
- **Reported for every model and stage:**
  - counts of complete, partial (salvaged or missing keywords), failed-content and failed-transport responses;
  - the usable share, the truncation share and the retry count.
- **Unknown cost** pauses new paid dispatch until it is reconciled. It is never recorded as 0.

## 6. Eligibility, cost forecast and envelopes

### 6.1 Rule (declared before any pilot number)

For each primary model m:

```text
planned_total(m) = reconciled_prior_spend (0.00064223 smoke + any later envelope spend)
                 + calibration (all models) + pilot (all pilot-eligible models)
                 + Stage_B(m) + Workbench reserve (0.20 under E1)
                 + 15% transport/price reserve on calibration + pilot + Stage_B(m)
```

Each stage is costed at the **reservation bound**:
- the routing `max_price` ceiling (§3);
- × the per-model **max** prompt tokens measured in calibration, or 1,100 tokens if larger;
- + 800 completion tokens (the hard cap).

A model is **Stage-B-eligible (selectable as m\*)** only if all three hold:
- (i) it passed the format gate;
- (ii) `planned_total(m)` ≤ the **approved** operational ceiling, and the planned attempted requests fit the approved
  request cap with the retry pool. Under E1 the ceiling is the USD 6.00 stop-and-report point, not the USD 8 nominal
  cap. Under E1R, if approved, it is the USD 50 hard dispatch limit;
- (iii) its cost and output-limit semantics are reconciled.

A model that passes the format gate but fails (ii) is **pilot-descriptive only**:
- it may be piloted if its pilot cost fits;
- it is reported in the table, but it is not a candidate for m\*.

**The eligibility table is frozen at P1-T03, before the pilot.** Rules after the pilot:
- An expensive model is never removed after it wins.
- A model never becomes eligible after the pilot.
- If price drift or a provider change makes a declared model unaffordable mid-run, that lane pauses and is amended
  transparently. A budget decision is not an effectiveness result.

**No partial programme.** If **no** primary model is Stage-B-eligible under the approved envelope, the pilot is **not
dispatched**. Running a pilot whose winner cannot finish is the A3r0 gap this revision closes.

### 6.2 Forecast (planning; replaced by calibration measurements at freeze)

Requests per stage: calibration 32, pilot 2,000 and Stage B 25,545 per model. Live list prices were read 2026-11-22. All
figures are in USD.

| Model | Price in / out per 1M (list → reservation ceiling) | Calibration (32) central / bound | Pilot (2,000) central / bound | Stage B (25,545) central / bound |
|---|---|---|---|---|
| Qwen3-32B | 0.08 / 0.28 → 0.14 / 0.42 | 0.006 / 0.016 | 0.363 / 0.980 | 4.64 / 12.52 |
| DeepSeek V4 Flash 0731 | 0.0443 / 0.30 → 0.15 / 0.30 | 0.005 / 0.013 | 0.317 / 0.810 | 4.05 / 10.35 |
| Gemini 2.5 Flash-Lite | 0.10 / 0.40 → 0.10 / 0.40 | 0.008 / 0.014 | 0.494 / 0.860 | 6.31 / 10.98 |
| Typhoon2.5 (native API) | **no published price**; free tier "for light usage" | unknown, not 0 | unknown, not 0 | unknown, not 0 |
| *Haiku 5.5 (optional, not in panel)* | 0.10 / 0.50 | 0.009 / 0.016 | 0.574 / 1.020 | 7.33 / 13.03 |

The scenarios:
- **Central:** 870 input tokens (midpoint of the observed 691–1,040 smoke range) and 400 output tokens (just above the
  observed 231–359 for complete replies), at list price.
- **Bound:** 1,100 input and 800 output tokens at the reservation ceiling. This is a hard per-request upper bound if
  routing is pinned and reasoning is off.
- **Low:** 700 / 300 tokens at list price. This gives Stage B of 3.58, 3.09 and 4.85 for the three paid models.

**Three paid primaries together:**

| Item | Central (USD) | Bound (USD) |
|---|---|---|
| Calibration (96 calls) | 0.019 | 0.043 |
| Pilot (6,000 calls) | 1.17 | 2.65 |

**planned_total(m), including smoke, all three paid pilots, the USD 0.20 Workbench reserve and the 15% reserve:**

| m\* candidate | Central (USD) | Bound (USD) | E1 (stop USD 6.00) | E1R (hard limit USD 50, pending) |
|---|---|---|---|---|
| Qwen3-32B | 6.91 | 17.69 | **not feasible** | feasible |
| DeepSeek V4 Flash 0731 | 6.23 | 15.20 | **not feasible** | feasible |
| Gemini 2.5 Flash-Lite | 8.83 | 15.93 | **not feasible** | feasible |
| Typhoon2.5 | unknown | unknown | **unknown → not eligible until resolved** | unknown → not eligible until resolved |

**Readings:**
- **Under the current E1, no primary model is Stage-B-eligible**, even at the central estimate. Only the low scenario
  fits: DeepSeek ≈ 4.8 and Qwen3-32B ≈ 5.4, including the Workbench and 15% reserves; Gemini ≈ 6.8 still does not. The
  low scenario is not a bound and may not be used for eligibility. By §6.1 the A3r1 pilot therefore waits for E1R or another approved envelope.
- **Under E1R, if approved,** every paid primary fits with wide margin:
  - the worst bound is about USD 17.7, against the USD 50 hard limit and the owner's USD 40 notification point;
  - the owner's allocations are also met: calibration 1, pilot 6, Stage B 18.
- **Requests:** 33,677 planned initial requests. That is 96.2% of the E1 cap of 35,000, and 33.7% of the E1R cap of
  100,000. Typhoon's requests count toward the envelope's request cap even though they are not billed by OpenRouter.
- **Credit balance is not authority.** OpenRouter credits read total 10, usage 1.63501153, so about USD 8.365 remains.
  The OpenRouter-billed part of the complete programme at the bound (about 2.7 for calibration and pilot plus up to
  12.5 for Stage B) exceeds that balance. Under E1R the account needs a top-up before Stage B; this is an owner action.

### 6.3 Typhoon-specific eligibility

- **Access:**
  - the key comes from `playground.opentyphoon.ai/api-key` under the owner's account;
  - the proposed environment variable is `TYPHOON_API_KEY`;
  - status: **credential not verified**. No key was read or tested.
- **Cost:**
  - Typhoon docs describe a free tier, "zero cost for light usage". They publish no per-token price, no daily quota and
    no research/commercial terms.
  - A paid "API Pro" is offered through Together AI, also without a published price.
  - A 2,000-request pilot or a 25,545-request Stage B may or may not count as "light usage".
- **Typhoon is pilot-eligible** only if, at P1-T01:
  - the key is present (presence check only);
  - the account's terms show the free tier applies to this volume, or an exact price is recorded within the envelope.
- **Typhoon is Stage-B-eligible** only if, in addition, a 25,545-request run is confirmed within its quota. At
  200 req/min that is about 2.2 h minimum wall time.
- **Fallback if access or terms are unresolved at P1-T03 (declared now):**
  - the freeze records Typhoon as **deferred (access)**;
  - the pilot runs as a declared three-model, three-lineage panel;
  - Typhoon may later be run on the same 2,000 pilot apps as a **descriptive** arm only, never as an m\* candidate;
  - this is a material panel change and is raised with the owner as one question before the freeze.

## 7. Effectiveness rules: unchanged from A3r0

These rules are kept exactly. None is altered by A3r1.

| Item | Rule |
|---|---|
| Pilot population | The same 2,000 P1-DEV apps as A3r0: tasks in the protocol-v1 F\* run (`runs/P1-DEV/alloc-L0-Q2-P2-A0.tsv`) with the smallest sha256(`g03-a3-pilot-v1` + app_id) (`apps-pilot.json`) |
| Arms | 70 fixed allocations at B = 4 over L, Q, P, H_m, K_m; unchanged action model, RRF final scorer and evaluator |
| Routes | H_m (PatEmbed HyDE) and K_m (BM25 on LLM text), exactly as A3r0 §2, with filing-date and own-unit masks |
| Integrity gate | `alloc-L0-Q2-P2-H0-K0` equals protocol-v1 F\* per query on every pilot app |
| Per-model score | G_m = best pilot-mean ALL R@200 among allocations with ≥ 1 H_m or K_m window |
| Selection | m\* = argmax G_m **among Stage-B-eligible models (§6, frozen before the pilot)**; ties within 0.0005 → lower measured pilot cost |
| Pilot GO | Δ = G_{m\*} − F\* ≥ +0.005 **and** lower 95% cluster-bootstrap bound > 0 (art unit, 10,000 replicates, seed 20261119); otherwise STOP, with no Stage B |
| Pilot interpretation | Optimistic (best of about 66 allocations × up to 4 models on the same apps); a spending gate, not a result |
| Stage B | m\* only; reuse pilot responses; generate the remaining declared P1-DEV and VAL apps |
| F3\* | Best P1-DEV ALL R@200; ties within 0.0005 → fewer routes, then route order P, Q, H, K, L |
| VAL principal | F3\* − F\*, ALL R@200 |
| Decision | CONTINUE: ALL lower CI > 0 and both IN and OUT lower CIs > −0.005. REVISE: ALL CI includes 0 and both guards hold. PARK: ALL upper CI < 0, or a guard is not established (protocol v1 §7) |
| No H/K in F3\* | H-M3 "not supported on DEV"; VAL descriptive only |
| Disclosure | **Fourth G03 look at VAL**; exploratory DEV phase only. IN and OUT are reported in the pilot; no IN/OUT pilot threshold is added |

**The one textual change to the selection row** is "among Stage-B-eligible models". It restricts the candidate set
before any score exists, so it is pre-effectiveness. It is the only way to prevent a selected model that cannot finish.

**The pilot also reports, for every piloted model** (eligible or descriptive):
- G_m, Δ_m, and IN/OUT R@200 of its best allocation;
- H_m-alone and K_m-alone pool recall at window 1;
- the usable share, the §5 failure counts, tokens and measured cost.

## 8. Prompt and the Thai-adapted arm

- **The A3r0 prompt is kept verbatim.** A change is allowed only if calibration shows a **common** need, for example
  every model wrapping JSON in prose. Any change is one common prompt for all models, frozen before the pilot. A Thai
  translation of the prompt or of the patent text for one model is not allowed (model plan §2).
- **What the Typhoon arm tests:**
  - It tests whether a Thai-adapted Qwen3 derivative keeps English patent-domain generation quality, compared with its
    Qwen3 sibling and two other lineages.
  - It does **not** test Thai ability. An English A3 result neither supports nor refutes Typhoon for Thai Gazette work.
- **What a Typhoon versus Qwen3-32B difference does not isolate:** size, MoE versus dense, parent checkpoint and
  serving stack all differ. Such a difference is not attributable to Thai adaptation.
- **A Thai-language query-expansion arm**, if wanted, is a separate pre-declared study on permitted Thai development
  material, under scoreboard C (§10).

## 9. Threats to validity (in addition to A3r0 §6)

**Memorisation and temporal leakage.** The models were trained on public patent text and possibly on examiner
citations. Known cut-offs:
- Qwen3-32B: 2025-03-31;
- Gemini 2.5 Flash-Lite: 2025-01-31;
- DeepSeek V4 Flash 0731: not published (the 0731 revision is from 2026);
- Typhoon2.5: not published.

This leakage cannot be removed on P1 data. Typhoon2.5 and Qwen3-32B share Qwen3 pretraining, so their leakage is
correlated. To be reported:
- the share of F3\*'s new relevant units that only H or K acquired;
- the cut-off table.

**Provider drift.** Each of these can change between calibration and Stage B:
- OpenRouter prices, which already drifted for DeepSeek (§1, item 7);
- the endpoint set, quantization (fp4, nvfp4, fp8, fp32 for DeepSeek) and service tier (Gemini flex, standard,
  priority);
- the served Typhoon revision.

Mitigations:
- pin routing (§3);
- record the provider, quantization and tier per response;
- re-read prices before each stage;
- pause on drift beyond the reservation ceiling;
- save raw responses so routes can be rebuilt without new calls.

Typhoon's served revision is not exposed by the API beyond the model id. The model page lists the latest update as
2025-10-20. A silent server-side revision cannot be detected; this is disclosed.

**Reproducibility:**
- Gemini is closed-weight.
- The DeepSeek and Qwen3-32B weights are public, but the served precision (fp8 or fp4) differs from the reference
  weights.
- Typhoon does not document `seed`.
- Temperature 0 does not guarantee determinism on batched inference.

**Typhoon Thai adaptation on English patents:** see §8. The model is used outside its primary design target. A weak
result there is not evidence against the Thai product profile.

**Lineage overlap:** see §2. Three lineages, with Qwen3 counted twice.

**Free-tier fragility (Typhoon):** rate limits (5 req/s, 200 req/min) and unknown quota can produce many 429s. Those are
transport failures and draw on the retry pool. A high Typhoon failure rate is a service result, reported as such, and
not a model-quality result.

**Repeated VAL exposure:** this is the fourth G03 VAL look. Every result is exploratory, and the paper's confirmatory
comparison is a later frozen run. Exposed DAPFAM does not become a fresh hold-out by being named G04.

**Licence:** PatEmbed (in the H route) is CC BY-NC-SA, research only. A product variant would use Qwen3 and BM25 routes.
Generated pseudo-documents are query-expansion artifacts and are never cited as sources.

## 10. Separate-scoreboard rule

- A3r1 results belong only to **scoreboard A** (existing G03 checkpoint): ALL R@200, the exact F\*, and the pilot and
  Stage B thresholds above.
- They are never merged into scoreboard B (native DAPFAM: nDCG@100, Recall@100) or scoreboard C (Thai Gazette:
  nDCG@10, Recall@20, coverage@20, structural packets).
- A Typhoon A3 number does not appear in a Thai table, and a Thai number does not appear in the A3 table.
- An A3r1 CONTINUE is an "exploratory development gain" under the owner's claim levels. It is not a supported matched
  gain and not a published-baseline win.
- The owner's prospective practical target of +0.010 for the *new* acquisition method (score contract) is not
  retro-fitted onto A3's frozen +0.005 pilot GO.

## 11. What P1-T01 to P1-T03 must settle before freeze

1. **Denominators.**
   - Recorded A3 manifests: `apps-P1-DEV.json` 25,626 and `apps-VAL.json` 1,919.
   - Evaluator populations in `g03-dev-gate.json`: P1-DEV ALL n = 26,547 and VAL ALL n = 1,999.
   - Freeze must state exactly which apps are generated in Stage B.
   - It must also state that apps evaluated but not generated stay in the analysis population with no H/K output.
     Otherwise it must regenerate the manifests from the F\* runs. No silent reduction of the evaluated population is
     allowed.
2. **Envelope.** Record the approved envelope: E1R as proposed, or an approved alternative. Under E1, §6.1 blocks the
   pilot.
3. **Credentials** (presence check only): `OPENROUTER_API_KEY` and `TYPHOON_API_KEY`.
4. **Fresh catalogue read.** Read ids, canonical slugs, endpoints, prices and supported parameters again, and finalise
   the routing pins and `max_price`.
5. **Typhoon terms.** Free-tier volume and terms for about 2,032 pilot and calibration requests, and for 25,545 Stage B
   requests, or the "deferred" fallback (§6.3).
6. **Calibration.** Run calibration (§4) and replace the §6.2 planning assumptions with measured token maxima.
7. **Freeze.** Write configuration hashes, the panel, the prompt hash, the cap, the failure policy, prices, the
   eligibility table and the complete-stage forecast to `P1-T03_freeze_receipt.json`. Then reserve the budget.
