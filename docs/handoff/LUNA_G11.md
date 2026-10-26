# Luna handoff — G11 bounded offline adaptation and provider seam

Date: 2026-10-25
Status: **READY_FOR_REVIEW** — targeted audit slice only

## Outcome

Implemented an offline G11 slice that accepts the existing public workflow
contract (project_id, brief, profile/version, allowed evidence, options,
policy, and an explicit change event). It builds a dependency graph from
caller-supplied IDs, runs the same deterministic generator for full
regeneration and selective repair, persists typed route/revision records, and
exports a small JSON/Markdown/HTML report.

This is not full G11, G12 learning, a held-out benchmark, a model result, or a
claim that selective repair is scientifically superior.

## Graph and adaptation contract

src/patent_to_pilot/adaptation/ contains typed AdaptationInput, ChangeEvent,
DependencyGraph, and comparison/report models. Nodes include the project,
profile version, policy, explicitly supplied evidence IDs, options, and routes.
Links are observable and are created only from declared profile/policy/evidence
IDs and option evidence links. No evaluator answers, expected outputs, hidden
facts, or inferred text-only dependency graph enters the runtime packet.

For a change, the engine reverse-walks explicit links from changed_ids.
Selective repair replaces affected option/route/evidence-derived portions
from the same IntegrationPipeline generator and preserves unrelated option
and route records. Unknown or withdrawn evidence remains scoped to dependent
routes; it does not globally block unrelated routes. Full regeneration remains
the comparison reference using the same packet, evidence links, and generator.

Each revision records event ID/reason, before/after payloads, affected and
preserved fields, authoritative profile/version metadata from the current
input, stored route versions, and SQLite payload read-back. The repository is
append-only for the run and does not infer continuity from event order.

Dependency IDs are qualified (evidence:E1, policy:P1, route:PROJECT:O1).
If one unqualified external ID is used by more than one node type, traversal
rejects it instead of choosing a node silently.

## Provider-neutral adapter

src/patent_to_pilot/providers/openrouter.py separates common request,
response, capability, attempt, budget, and transport contracts from
adaptation logic. OpenRouterAdapter is an OpenRouter-shaped first adapter
with an injected MockHTTPTransport; it does not open a socket in tests.

Capabilities are checked before sending tools, structured-output schemas, or
parameters. JSON Schema Draft 2020-12 validation is performed with a real
validator, including integer/minimum/additionalProperties constraints.
Response schema validation is a separate step from evidence support
validation. A shared attempt ledger reserves request token bounds and spend
for every attempt before dispatch, includes retries and cumulative calls, and
keeps missing usage/cost as unknown_pending rather than zero. Usage is
normalized to input/output/total without double-counting total.

Requested and reported provider/model identities are stored separately. In
research mode, reported model/provider drift is rejected; a missing reported
provider remains unknown rather than being guessed. Attempt errors are stored
as safe code/class messages without raw exception text or headers.

The example is configs/g11-provider-example.toml: the model ID is a
placeholder, the key is referenced only by environment-name placeholder, live
calls are disabled, retries default to zero, and input/output/total-token,
timeout, and spend ceilings are explicit. Research mode requires an exact
provider/model pin and disables auto-routing/fallback.

Future extension points are listed for OpenAI, Anthropic, Google/Gemini, and
xAI/Grok; native adapters for those providers are not implemented or tested.

Official OpenRouter references used for the request boundary:

- https://openrouter.ai/docs/quickstart
- https://openrouter.ai/docs/guides/features/structured-outputs

No API key, auth.json, Codex credential, network inference, paid/free call,
GPU, or RunPod run was used.

## Verification

Targeted commands and observed results:

    python -m pytest tests/test_g11_adaptation.py tests/test_provider_adapter.py
    30 passed

    python -m pytest tests/test_provider_adapter.py
    18 passed

    python scripts/run_provider_pilot.py --dry-run
    status=DRY_RUN_NOT_EXECUTABLE, max_attempts_total=10,
    spend_cap_usd=1.0, live_transport=not_dispatched,
    input_allowance=4128, output_limit=1500, total_limit=5628

    python scripts/run_g11_demo.py --output results/development/g11
    state_count=3, revision_count=2, sqlite_readback=true,
    output_equivalence=true, unaffected_preservation=true,
    paid_api=false, model_calls=false

The actual demo outputs are local derived artifacts. The adaptation report now
distinguishes affected_nodes, generator_invocations, and
actual_recomputed_nodes. The current selective strategy invokes the full
deterministic generator and then merges scoped output, so it does not claim
selective recomputation or hard-coded cost savings:

- results/development/g11/adaptation.json
- results/development/g11/adaptation.html
- results/development/g11/adaptation.md
- results/development/g11/demo.sqlite (local-only SQLite evidence; do not commit)

The demo covers an initial state, a policy change, and evidence withdrawal.
The tests also cover overlapping dependencies, ambiguous qualified IDs,
irrelevant/new IDs, unknown evidence, SQLite read-back, schema-valid mock
success, integer/minimum/additionalProperties response validation, unsupported
capability, timeout, rate limit, missing usage/cost, cumulative budget,
retry reservations, model drift, and sanitized errors. The readable matrix is
tests/fixtures/g11_provider_regression_matrix.json.

## Provider ledger targeted audit closure

The provider-only correction in this round does not modify
src/patent_to_pilot/adaptation/ or change the accepted G11 adaptation
contract. Billing handling is now separated from content handling:

- every dispatched attempt is reserved before transport;
- billing metadata (usage, reported cost, provider/model metadata) is settled
  immediately after transport and before content, model-drift, or JSON Schema
  validation;
- observed cost is compared with its reservation and added to cumulative
  actual debit; observed cost above the reservation marks a budget breach and
  blocks later dispatch;
- a cumulative spend cap blocks the next reservation before dispatch, while a
  confirmed debit over the cap is reported as a breach and never returns a
  success result;
- missing usage/cost remains unknown_pending and holds the conservative
  reservation; it is not treated as zero;
- live mode rejects requests without an explicit checkable cost_upper_bound_usd;
- schema-invalid content can still settle a real mocked debit, then retry;
  both attempt debits remain in the shared ledger.

Targeted mock regressions include two $0.006 reservations against a $0.01 cap,
observed cost above reservation, schema-invalid content followed by retry with
two $0.006 debits, live-mode missing cost bound, and fake-secret exception
sanitization. No HTTP request, API key, free/paid model call, GPU, or RunPod
run was used.

## OpenRouter HTTP transport targeted closure

Implemented in this round:

- exact URL parsing and allowlist before the Authorization header is attached:
  HTTPS openrouter.ai, base path /api/v1, and exact endpoint
  /chat/completions; redirects are disabled in the default urllib opener;
- HTTP payload sends the same effective max_tokens value used by the ledger
  reservation and rejects a conflicting max_tokens request parameter;
- effective input allowance includes prompt estimate plus schema/framing
  tokens; dry-run reports 4000 + 128 = 4128 input allowance and 1500
  output tokens;
- nested usage detail objects cannot invalidate scalar token fields or cost;
  scalar prompt/input, completion/output, total, and usage-level cost are
  normalized independently;
- transport timeout/error exception chains are removed before safe errors are
  surfaced, and formatted traceback tests use fake secrets only;
- routing metadata is pinned per selected model: google-ai-studio for
  Gemini Flash-Lite and openai for GPT-4.1 mini, with
  allow_fallbacks=false, require_parameters=true, and snapshot max_price.

The CLI scripts/run_provider_pilot.py remains preflight-only. It does not
dispatch a batch and has no hidden live path. Its dry-run is the default and
reports a proposed maximum of 10 attempts total and USD 1.00 cap. A future
dispatcher must reuse the same ledger for every retry and prove the total
attempt/cost guards with mocks before any live authorization.

Mock-tested in this round: HTTP success, billing metadata, 429, 5xx, timeout,
malformed response, missing billing, nested billing, redirect-disabled setup,
exact URL/path rejection, output limit/framing guards, routing/max-price
serialization, and sanitized traceback. Live HTTP is NOT_RUN; no key was
read and no request was sent.

The owner-selected model pair is recorded as planned configuration only:
google/gemini-2.5-flash-lite and openai/gpt-4.1-mini. No key was read or
created, and neither model was called.

## What is implemented versus not implemented

Implemented in this bounded slice:

- explicit-ID graph construction and reverse impact traversal;
- deterministic full versus selective comparison with measured elapsed time and
  recomputed-node counts;
- scoped policy/evidence revision, before/after diff, preservation check, and
  typed SQLite route/change payload read-back;
- provider-neutral OpenRouter-shaped request seam and mocked failure modes;
- shared attempt reservations, canonical usage normalization, model/provider
  drift checks, safe attempt errors, and full recomputation accounting;
- real JSON Schema validation via the project-local jsonschema dependency;
- secret-free config and local CLI demo/report.

Not implemented or not claimed:

- full G11 dependency coverage across every product artifact or source type;
- G12 cumulative/cross-project learning, memory promotion, or feedback loop;
- live provider compatibility, provider pricing validation, or reproducibility
  across any vendor beyond this mocked contract. The owner-selected models
  google/gemini-2.5-flash-lite and openai/gpt-4.1-mini are configuration
  targets only; neither was called or authenticated;
- semantic entailment, clinical/regulatory/legal validation, patentability/FTO,
  scientific utility, cost advantage, or AI superiority;
- paid/free API calls, GPU/RunPod, corpus download, main benchmark, or UI.

The current comparison is an engineering observation about this synthetic
bounded packet, not evidence that selective repair is faster or better in a
scientific study. The local demo uses SQLite :memory:; persistence/read-back
is tested, but no durable database artifact is part of the handoff.

The OpenRouter HTTP transport is implemented with a single-attempt urllib
boundary, timeout, sanitized transport errors, HTTPS/key preflight, and no
HTTP-client retry. It was exercised only through mocked openers; no real
OpenRouter request was sent. The adapter does not claim live provider
compatibility or endpoint reproducibility from these tests.

Pepo owns docs/research/pilot-next/; this work package did not modify it,
frozen methodology/evaluation fixtures, GOAL/AGENTS, or shared memory.

## Review boundary and next action

Review only the G11 files, targeted tests, config, demo script, and generated
report listed above. Keep the package uncommitted until review. If accepted,
the next bounded step is a targeted interface review and package selection;
do not start a paid provider call or claim full G11/G09/G10 completion.
