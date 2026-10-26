# Provider identity repair — offline handoff

Status: READY_FOR_REVIEW_OFFLINE. No further live inference was performed during this repair.

## Observed live result and limit of diagnosis

The existing Phase A journal contains exactly one attempt, `smoke-1-1`, status
`model_drift`, settled API-reported debit USD 0.0000132, 32 input and 25 output
tokens. There is no unknown billing reservation. GPT has not been sent.

The original adapter used the same exception for model and provider mismatch and
did not persist response identity on rejection. The actual live mismatch is
therefore UNKNOWN. The mock reproduction demonstrates a code defect, not the
cause of that historical response. No historical identity or success is invented.

## Minimal repair

- `ProviderConfig.provider` / `requested_provider` identify the broker, OpenRouter.
- `routing_only` / `requested_upstream_providers` identify approved upstream tags.
- Response `reported_provider` is an upstream label, not a broker identity.
- Exact supported upstream labels: `Google AI Studio` and `google-ai-studio` map
  to `google-ai-studio`; `OpenAI` and `openai` map to `openai`. Exact configured
  route tags also match themselves. Other labels do not gain permission through
  case folding, prefix matching, or region/priority collapsing.
- Pinned research/live requests require model and upstream identity. Missing,
  malformed or unapproved identities fail closed. Model comparison remains exact;
  date/version aliases are not silently accepted. Legacy unpinned offline mocks
  retain their optional-identity behavior; production transport requires pinning.
- Requested/reported identity and an attributable `identity_error` are captured
  before identity/content/schema validation. Durable billing settlement persists
  them before rejection. Known/configured public identities are retained; other
  response strings are recorded only as SHA256 digests, not arbitrary error text.
- New attempt fields have defaults so legacy journal records remain readable.
- Mock CLI and affected fixtures now supply the correct upstream label/tag.

## Focused verification

88 tests passed, zero failures/errors/skips. Scope:

```text
tests/test_provider_identity.py
tests/test_provider_adapter.py
tests/test_provider_pilot.py
tests/test_provider_env_file.py
tests/test_g11_adaptation.py
```

Tests ran with Python bytecode/cache disabled, socket connection/DNS guards, a
fake process key and a guard against opening the production `.env`. Observed
network attempts: 0. Production `.env` reads: 0. SQLite test outputs were isolated
outside the project. Added identity regressions cover valid labels, missing/wrong
model/provider, strict model aliases, secret-like identity redaction, pre-validation
identity capture, legacy failure resume, cumulative cap retention and unchanged
approved request hashes. Source compilation and changed-line whitespace checks pass.

The production `live.sqlite3`, `.started.json` and `approval-smoke.json` are
byte-for-byte unchanged by this repair. No adaptation, G09/G10, frozen evaluation,
research/pilot-next, credentials, global settings, commit or push was changed.

## Remaining GPT-only command — NOT RUN

Run from the project root only after the repair review authorizes continuation:

```powershell
rtk proxy python -B scripts/dispatch_provider_pilot.py --live --env-file .env --phase smoke --approval results/development/provider-pilot/approval-smoke.json --state results/development/provider-pilot/live.sqlite3
```

Do not delete, recreate, replace or change the journal, activation marker or
approval. Do not switch to the default/mock state path.

Resume reads the historical Gemini attempt and its debit, skips that job because
its one-attempt quota is spent, and can send only `smoke-1-2` once. The unchanged
phase ceiling is USD 0.60, not a new USD 0.60 allowance. Prior debit plus the GPT
reservation is USD 0.4214436. This reservation uses the existing advertised context
and price assumptions, not a newly proven tokenizer bound or an external account
spending limit. Unknown billing or a breach still blocks continuation.

A TEMP-only regression reproduces this legacy-row resume and proves that the
original row remains identical, only GPT is dispatched, two total attempts cannot
be exceeded, and prior debit can block a new reservation. Re-running after both
slots are spent sends nothing.

Even if GPT succeeds, the overall status remains `PHASE_FAILED`: the original
Gemini failure cannot become a success. Phase B is not authorized by this receipt.
An additional Gemini trial would need a separately reviewed plan/approval that
preserves prior history; it must not be achieved by resetting state.

## Approval and payload identity

The plan was not edited. Its SHA256 remains:
`6cf9bd14059f1df9f11ff6f913d31bcc5e5c60f3f993ac4766621bf1c7c148b2`.
The existing receipt still validates for the remaining Phase A job; no plan-based
reapproval is required solely because of this offline code repair. This handoff
is not an instruction to dispatch before review.

The outgoing compact JSON bodies still hash to:

- Gemini: `f31be6bc37b4c522b7bfa38a7e79d17e0000e9e129ee3ad332a90f1133fcadf9`
- GPT: `0696c7d66be448776810d1981129ffcf9849388330ec383e6a359bf8722e22ba`

No prompt, schema, model, route, endpoint, fallback, retry or token setting changed.
