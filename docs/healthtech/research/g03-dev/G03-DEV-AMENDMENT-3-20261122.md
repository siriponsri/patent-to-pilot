# G03 DEV amendment 3 (22 Nov 2026): LLM query expansion as new acquisition routes. FROZEN before any amendment-3 number

**Why (memo §3, §4a, §4b):**
- Protocol v1 (support_frontier_v0), amendment 1 (field obligations) and amendment 2 (learned selector) are all PARKED.
  Each only re-weighted or re-sliced the same four encoders over the same request text; none moved VAL ALL R@200 beyond
  ±0.005.
- The per-query oracle over fixed allocations (+0.079 ALL R@200 on P1-DEV) shows that the routes disagree, but the
  learned selector shows that query-side signals cannot predict which one wins. Owner decision **D2**: keep working on
  acquisition with a mechanism that brings in **new** candidates.
- LLM-generated pseudo-documents and keyword expansions are the established way to add vocabulary and framings the request
  does not contain (Query2doc, HyDE; API-BUDGET-PROPOSAL §5).

**H-M3:** routes built from LLM-written hypothetical prior-art abstracts and keyword queries surface relevant families that
the whole-query routes miss, at the same action budget and with the same final scorer.

**Money:** OpenRouter envelope **E1** (owner decision D9, 22 Nov): cap USD 8.00 and 35,000 requests, for this amendment
(pilot, then one full run) and Workbench profile checks (≤ USD 0.20). Balance read before freezing: total credits
USD 10.00, used USD 1.634. Embedding and BM25 stay local on dr-train (USD 0). No RunPod.

**Data:** allowed DEV only. P1-DEV selects; VAL decides. No TEST block is read; every script refuses TEST blocks. DAPFAM and
Gazette are not used.

## 1. LLM generation (runtime side, no labels)

**Input per query:** title, abstract and first independent claim from `bridgeret/texts-v1/queries.jsonl` (P1-DEV and VAL
rows only, extracted to `g03-dev/a3/queries-dev-val.jsonl`). Abstract and claim are each cut to 1,500 characters at the last
whitespace. A missing field stays empty and is never invented.

**Prompt** (fixed; the code constant in `scripts/research/g03_a3_llm_expand.py` must equal this text):

- system: `You are an experienced patent examiner searching for prior art.`
- user:

```text
Below is a patent application. Write three short hypothetical abstracts (50 to 70 words each) of EARLIER patent documents
that an examiner would likely cite against it. Make them different: (1) a document that solves the same technical
problem, (2) a document that discloses the key mechanism of the first claim, possibly in another field, (3) a document
from a closely related or broader technical field. Use the technical vocabulary such documents would use, including
synonyms. Then write one keyword search query of 15 to 25 distinctive technical terms and synonyms. Do not mention this
application. Reply with JSON only: {"priors": ["...", "...", "..."], "keywords": "..."}

Title: <title>
Abstract: <abstract>
First claim: <claim>
```

**Call settings (every model):** OpenRouter chat completions; reasoning off (`reasoning: {"enabled": false}`, or effort
`none` where that is the model's switch); `max_tokens` 400; temperature 0; seed 20261122; usage accounting on. Anthropic
models on OpenRouter do not accept `temperature`/`seed`; they are sent and ignored, so Haiku outputs are not guaranteed
reproducible. Provider routing is left to OpenRouter and the serving provider is recorded per response.

**Parsing:** take the first JSON object in the reply. If the reply was cut at `max_tokens`, every complete string already
present in `priors` is kept and `keywords` is empty. A response is **usable** if it yields ≥ 1 non-empty prior or a
non-empty keyword string. Unusable responses are not retried; that query simply has no output on the new routes (it scores
from its other windows only), exactly like a missing field in amendment 1.

**Retries:** only transport failures (HTTP 408/429/5xx, timeouts, connection errors), at most 2 retries per request with
back-off. Every attempt counts against the request cap; its cost is counted when billed.

**Ledger:** one JSON line per attempt in `../_private_artifacts/g03-a3/<model>/<block>.jsonl`: app_id, model, provider,
generation id, status, raw text, parsed fields, prompt/completion tokens, `usage.cost`, finish reason, wall time.
Aggregates (no text) are committed.

## 2. New routes (built on dr-train; same masks as the protocol-v1 routes)

For model m:

- **H_m (HyDE with PatEmbed):** v = normalise(e_q + Σ_i e_d(prior_i)), where
  - e_q = the PatEmbed-large query vector of the whole-query text used by `runs/z-patembed` (`ser-patembed-v1/queries.jsonl`,
    prompt `encode query for mixed document retrieval: `);
  - e_d = the PatEmbed-large document vector of each prior (prompt `encode document for mixed retrieval: `), each
    L2-normalised before the sum;
  - mean pooling, 512 tokens, fp16, approved V100 under the GPU lock (memory fraction 0.12);
  - retrieval exactly as `dense_bridgeret_v3.py`: exact inner product against `runs/z-patembed/passages.f16.npy`, units
    first published on or after the filing date masked, the own unit masked, top 1,000, ties score desc then unit order.
  - A query with no usable prior has no H output.
- **K_m (BM25 on the LLM text):** query text = `keywords` + newline + the priors joined by newlines. Scoring exactly as
  `bm25_bridgeret.py` (k1 1.5, b 0.75, lowercase `[a-z0-9]+`, no stemming or stop list, index over `ser-arctic-v1`
  passages, same filing-date mask and own-unit mask, only documents matching ≥ 1 term, top 1,000).

**Disclosed defect found while writing this file:** the amendment-1 field routes (`g03_field_routes.py`, routes T and C)
did **not** apply the filing-date mask or the own-unit mask that `dense_bridgeret_v3.py` applies. Later-published units
and the query's own unit could occupy their windows, which can only have hurt T and C. The amendment-1 decision stands as
recorded (no silent repair); the defect is reported in memo §4a. The A3 routes apply both masks.

## 3. Stage A: pilot (P1-DEV only)

- **Pilot sample:** 2,000 P1-DEV tasks present in the protocol-v1 F\* run (`runs/P1-DEV/alloc-L0-Q2-P2-A0.tsv`), those with
  the smallest sha256(`g03-a3-pilot-v1` + app_id).
- **Models (4):** `qwen/qwen3.7-flash`, `deepseek/deepseek-v4-flash-0731`, `qwen/qwen3-32b`, `anthropic/claude-haiku-5.5`
  (proposal §2; the optional Sonnet sensitivity sample is not run). 8,000 requests.
- **Arms per model:** the 70 fixed allocations at B = 4 over routes (L, Q, P, H_m, K_m), with the protocol-v1 action model and
  final scorer, on the pilot apps (`--apps-file`), evaluated by the unchanged `eval_bridgeret_dev.py`.
- **Integrity gate:** `alloc-L0-Q2-P2-H0-K0` must equal the protocol-v1 F\* per-query values on every pilot app.
- **Per-model score G_m:** the best pilot-mean ALL R@200 among allocations with ≥ 1 H_m or K_m window.
- **Model selection:** m\* = argmax G_m; ties within 0.0005 → the lower measured pilot cost.
- **Go / no-go for Stage B (written before any pilot number):** let Δ = G_{m\*} − F\* on the 2,000 pilot apps, paired, with
  the protocol-v1 cluster bootstrap (art unit, B = 10,000, seed 20261119).
  - **GO** if Δ ≥ +0.005 **and** the lower 95% bound > 0.
  - Otherwise **STOP**: H-M3 is not supported on the pilot; no Stage B spend; report.
  - The pilot Δ is optimistic (best of ~66 allocations chosen on the same queries). It only gates spending; it is not a
    result.
- **Reported for every model:** G_m, Δ_m, IN and OUT R@200 of its best allocation, pool recall (ALL/IN/OUT) of H_m and K_m
  alone at window 1, the share of pilot queries with usable output, tokens, cost and failures.

## 4. Stage B: one full run with m\* (only on GO)

- Generate with m\* for every remaining P1-DEV task in the F\* run, and every VAL task in the VAL F\* run (pilot responses are
  reused, not regenerated). About 25,600 requests.
- Build H and K for P1-DEV and VAL; all 70 allocations on both blocks; unchanged evaluator.
- **F3\*** = the best allocation on P1-DEV by ALL R@200. Ties within 0.0005: fewer routes, then route order P, Q, H, K, L.
- **Principal on VAL: F3\* − F\*** (F\* = `alloc-L0-Q2-P2-A0`, i.e. `alloc-L0-Q2-P2-H0-K0`). Same endpoint, same IN/OUT
  non-inferiority margin δ = 0.005, same cluster bootstrap, same continue / revise / park rule as protocol v1 §7.
- If F3\* contains no H or K window, H-M3 is "not supported on DEV"; VAL is then descriptive only.
- **Disclosed: this is the fourth look at VAL in G03** (v1, A1, A2, A3). DEV phase only; the paper's confirmatory
  comparison is a later frozen G04 run.
- **Descriptive:** the full 70-allocation table on both blocks; H alone and K alone vs P and L; overlap of H/K top-200 with
  Q and P; the share of F3\*'s final top-200 relevant units that only H or K acquired.

## 5. Spend controls and stop rules (E1)

- `get-credits` is read before and after each stage and recorded.
- The caller stops by itself when the ledger reaches **USD 6.00** cumulative or **35,000** attempted requests, writes its
  state, and the run is reported as incomplete. Stage B never starts after a STOP in Stage A.
- Unknown cost is recorded as unknown, never as 0.
- Concurrency ≤ 8 requests in flight. The caller is resumable: it skips app_ids that already have a usable or content-failed
  response for that model.

## 6. Threats to validity (declared now)

- **Memorisation and temporal leakage:** the LLMs were trained on public patent text, including documents published after
  these filing dates and possibly the examiners' citations. A gain may partly reflect recall of real cited documents rather
  than reasoning. This cannot be removed on P1 data; it is reported as a limitation, and a G04 run on a set with known
  publication dates relative to the model cut-offs is the place to probe it.
- **Model drift:** OpenRouter models and providers change. Raw responses are saved so the routes can be rebuilt without new
  calls.
- **Licence:** PatEmbed is research-only (CC BY-NC-SA). A product variant would use Qwen3 and BM25 routes.
