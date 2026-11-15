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
