# Paper 2 acquisition harness: design note (prototype)

Status: PROTOTYPE, CPU-tested with authored doubles only. No model, GPU, corpus,
DAPFAM query or test data was used. Branch `claude/paper2-harness-0d504a`; not merged.

Code: `src/patent_to_pilot/research/acquisition_harness.py`.
Tests: `tests/test_acquisition_harness.py` (23 passed). Paper 1 modules are untouched.

## Purpose

Compare, under one per-query budget, (a) a fixed multi-view union and (b) an agent
that chooses retrieval tools step by step. The fixed union is the required
baseline: PatEx-Gym reported that a plain patent retriever beat its trained agent
on R@100.

## Components

- **Tools** (`ToolBox`): `dense_search(query, k)`, `bm25_search(query, k)`,
  `cpc_filter(candidates, codes)`, `citation_expand(family_id, k)`, `read(family_id)`.
  The backend is injected (`SearchBackend` protocol). Each tool has a declared cost
  from an injected cost model: tool calls, LLM calls, tokens, encoder passages, CPU,
  GPU and wall seconds. `read` returns text for the agent's context and does not
  add to the pool.
- **Budget** (`Budget`, `BudgetLedger`): hard caps on tool calls, LLM calls,
  tokens, wall seconds and, optionally, encoder passages. A call is admitted only if
  the spend after it stays within every cap. If not, it is refused before execution,
  recorded with the exceeded caps, never retried, and the controller stops.
  The declared cost is charged in full. LLM tokens are charged as
  prompt tokens + `max_output_tokens`, an upper bound.
- **Pool**: RRF (k=60) over every returned list, deduplicated, capped at
  `pool_size`. Ties are broken by best rank, then family id.
- **FixedUnionController**: a declared `Step` sequence. Search steps run on the
  original query or on an LLM view (`llm_view`, for example a function-level
  rewrite). `cpc_filter` and `citation_expand` act on the current pool.
- **AgentController**: an injected LLM (`LLMSpec.llm(messages, max_output_tokens)`)
  must return strict JSON `{"action", "args"}` from a closed schema. There is no
  repair: a non-JSON reply, an unknown action, wrong args, `k` out of range, or a
  `family_id` not in the pool is recorded as `INVALID_ACTION`. The agent then stops
  and returns the fixed-union ranking.
  An empty own pool also falls back (`EMPTY_POOL`).
  A budget refusal keeps the agent's own pool when that pool is not empty.
- **Trajectory**: one JSON record per event (`start`, `llm`, `tool`, `refused`,
  `invalid_action`, `agent_stop`, `fallback`, `stop`). Each record carries the
  declared and cumulative cost, result and pool hashes, and the stop reason.
  Records have no timestamps. Query text and LLM output are stored as hashes only.
  Logs are written once per query as JSONL; existing files are never overwritten.
- **`compare_matched_budget`**: runs both controllers on each query with the same
  `Budget`. The fixed union runs once per query and serves as the agent's fallback,
  so a fallback ranking is the identical fixed-union ranking. Reports agent cost and
  fallback cost separately, plus totals per controller: stop reasons and fallback count.

## Stop reasons

`SEQUENCE_COMPLETE`, `AGENT_STOP`, `BUDGET_REFUSED`, `INVALID_ACTION`,
`MAX_STEPS`, `EMPTY_POOL`.

## What the tests show (authored doubles)

- Budget refusal happens before execution, is recorded once, and is not retried.
  This holds for the tool-call, token and wall-time caps.
- An invalid action (10 variants) leads to a stop and the fixed-union fallback.
  This also holds after the agent has made some progress.
- Identical backends produce byte-identical trajectories.
- The pool cap holds and there are no duplicate families.
- Under matched budgets, every per-query cost stays within the caps.
- Trajectory files cannot be overwritten. Cost validation rejects negative and
  non-finite values.

## NOT yet validated

- Real backends: dense encoder, BM25 index, CPC lookup and citation graph. The
  cost model (`default_cost_model`) uses illustrative numbers. A study must freeze
  its own cost model from measured throughput.
- Wall time is enforced only as declared seconds. A runtime watchdog for measured
  time is still needed. Real model calls need the same journal, ledger and isolation
  controls as Paper 1.
- The token counter defaults to a whitespace stand-in. A real study must use the
  pinned tokenizer.
- Agent prompt quality, the action schema under a grammar-constrained decoder, and
  any retrieval effect are not tested. No metrics, examiner-cited qrels or
  statistics are wired in.
- Fallback cost policy: should the agent be charged the fallback spend inside the
  matched budget? It is reported separately here. The study protocol must decide
  this before any outcome is seen.
- A durable no-replay registry across runs: only per-file exclusive create exists.

## P2-OA extension: PatEx-style actions, arms E0-E2, funnel evaluator

Status: PROTOTYPE, CPU-tested with authored doubles only (zero model calls). Follows
the proposed (not frozen) plan `PAPER-2-3-MERGED-PLAN-20261116.md` section 5.

Code:
- `src/patent_to_pilot/research/patex_arms.py` (runtime);
- `src/patent_to_pilot/research/funnel_eval.py` (evaluator only).

Tests: `tests/test_patex_arms.py` (31 passed). The earlier harness tests (23) and the
Paper 1 spot checks (10) still pass.

### Runtime (`patex_arms`)
- **Actions:** `SEARCH(query, method, top_n)` with method dense / bm25 / hybrid
  (hybrid = RRF of the two), `VISIT(id, fields)`, `SELECT(id, passage_locations)`
  and `STOP`.
  - Locators are UTF-8 byte offsets into a field, with an optional quote.
  - Every action has a declared cost (`ActionCost`) and is admitted against one
    `ArmBudget` before it runs. The budget caps actions, LLM calls, tokens, wall
    seconds and, optionally, returned ids, visits, selects, observation bytes,
    rerank docs and USD.
  - A refused action is logged, never retried, and ends the episode.
- **Observations logged per action:**
  - SEARCH: returned ids and versions;
  - VISIT: version, per-field excerpt bytes, full bytes, excerpt sha256 and tokens;
  - SELECT: locators, with each quote stored as its sha256;
  - every action: declared seconds and cumulative cost.
  - Query text, LLM output, excerpts and quotes appear only as hashes.
- **Funnel order is enforced at runtime:**
  - VISIT requires an id returned by an earlier SEARCH (`UNSEARCHED_ID`).
  - SELECT requires a visited id (`UNVISITED_ID`) and a visited field (`BAD_LOCATIONS`); an id can be selected once.
  - So Select ⊆ Visit ⊆ Search holds by construction.
- **Arms.** All arms take the same `PatexEnv` (same tools) and the same `ArmBudget` object. `run_arms` refuses to run them otherwise, and also requires one shared pool size.
  - **E0** `FixedRetrievalArm`: one SEARCH, then a declared `FixedFunnelPolicy` (visit the top v; select the top s on the visible bytes of one field).
  - **E0-deep** `DeepRetrievalArm`: one deep SEARCH, then a fixed reranker hook on the top `rerank_top`. The hook is costed as RERANK and must return a permutation. The funnel policy then follows.
  - **E1** `MultiQueryArm`: pre-declared `QueryTemplate`s (original text or one LLM rewrite per template), fused with RRF, then the funnel policy.
  - **E2** `ReActArm`: an injected solver returns strict JSON. Anything invalid (static or state) stops the agent and it falls back to the injected fixed arm (E0). The fallback cost is reported separately. An empty search also falls back (`EMPTY_SEARCH`).
  - A fixed arm whose declared schedule exceeds the shared budget is rejected at construction.
- **Final ranking:** selected ids in selection order, then the RRF of the search lists (or of the reranked order for E0-deep), capped at the pool size.

### Evaluator (`funnel_eval`)
- **Recall per stage:** Search-R, Visit-R and Select-R per query, with hits/k denominators.
- **Strata:** ALL, IN, OUT, 102, 103 and the domain×basis crosses. Basis `both` counts in both 102 and 103.
- **NA rules:** K=0 gives NA (`K_EMPTY`); a stage not run gives `STAGE_NOT_RUN`; a missing label set gives `NO_LABELS`.
- **Aggregation:** macro over eligible queries only, micro from summed hits/k, and NA counts by reason.
- **Unjudged documents:** documents outside K are only counted (unjudged, other_citation). They are never negatives.
- **Grounding (mechanical):**
  - the source exists;
  - the version matches;
  - the locator is in range and on UTF-8 character boundaries;
  - the quote matches after normalisation `nfc-collapse-whitespace-strip-v1`.
  - No LLM judge.
- **Label isolation:** runtime and evaluator never import each other (AST-checked in tests). `Query` has only `query_id` and `text`. Arm `run(query)` takes nothing else. A K-only id never reaches solver prompts, logs or reports.

### Not yet validated (in addition to the list above)
- Real OA data: query text, corpus, distractors, 102/103 and IN/OUT labels. Gate G2.0 coverage is not checked.
- A real reranker and the E0 method choice on DEV.
- E2 prompt quality under a grammar-constrained decoder.
- The cost model (illustrative only).
- Real tokens and time: they are declared, not measured.
- Paired statistics (cluster bootstrap, Holm) and the endpoint rule of section 5.4 are not wired in.
- nDCG@10 is not implemented yet.
- Fallback-cost policy: still open, and must be decided before outcomes are seen.
- Funnel records contain quotes and must stay private.
