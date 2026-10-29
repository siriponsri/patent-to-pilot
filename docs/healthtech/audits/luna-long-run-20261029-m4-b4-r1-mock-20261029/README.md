# HT-M4/B4 R1 provider-shaped mock audit

- Run ID: `luna-long-run-20261029-m4-b4-r1-mock-20261029`
- Date: `2026-10-29` (Asia/Bangkok)
- Implementation commit: `4e4ce3ed96d494ac903587d72d80ce21a4466d31`
- Status: `PASS_PROVIDER_SHAPED_MOCK; LIVE_BLOCKED_LOCAL`
- Tree state: dirty with unrelated owner artifacts preserved

## Scope

This package adds and exercises the substantive HT-B4 provider-shaped runner over the frozen Boston/Stryker/Cook development view. The runner binds structured controller observations and actions to the versioned USD8 R1 ledger, exact model/provider routing, current endpoint pricing metadata, provider-transfer checks, response-schema validation, and runtime-before-evaluator output ordering.

The run used the frozen development inputs at `results/healthtech/ht-multicompany-20261029-r3-family-r2/views/development/` with 5 devices and 24 patents. The protocol hash is `1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b`; the cohort manifest hash is `1b42b7c4a52b697d9c5c4f7db4f9236b7d5d239d83584863a6ba844591adef75`.

## Result

The mock run completed all 5 devices and 12 structured controller calls. Every mock response validated against the fixed action schema and remained pinned to `openai/gpt-4.1-mini` through upstream `openai`. Macro and micro known-link recall at `K=20` are both `1.0` on this development reference view. This is descriptive product-disclosure retrieval evidence only; it is not semantic relevance gold, exhaustive recall, clinical suitability, FTO, patent validity, investment merit, or a publication result.

The R1 SQLite ledger settled all 12 mock attempts with no pending or unknown billing, no budget breach, `0.0012` simulated USD, and `$0.00` paid cost. The runtime predictions and raw rankings were written before evaluator references were loaded.

## Current endpoint snapshot

The exact OpenRouter endpoint metadata was fetched from `https://openrouter.ai/api/v1/models/openai/gpt-4.1-mini/endpoints` and saved as sanitized inputs. The selected route is `OpenAI: GPT-4.1 Mini`, with prompt price `$0.40 / 1M` and completion price `$1.60 / 1M`; the B4 request scope disables tools and uses structured text output only. The snapshot hash is `a990baa4d0ac46e188981b3c8b400c84da38250c5d2ab9fb23eb420ffeb8a267`.

## Live boundary

Live execution was intentionally not attempted. The CLI preflight blocked before any transport when `--transfer-manifest` was omitted. The frozen public cohort includes local-research-only sources without an approved remote-transfer manifest, so no patent or regulatory source payload was sent to a provider. Credential, credit, transfer-rights, payload, reconciliation, and paid-canary gates remain unresolved.

## Artifacts

- Mock output: `results/healthtech/ht-b4-r1-mock-20261029-r4/`
- Endpoint inputs: `results/healthtech/ht-b4-r1-inputs-20261029-gpt41mini/`
- Verification: [`verification.json`](verification.json)
- Experiment ledger: [`experiment-ledger.json`](experiment-ledger.json)
- Continuation: [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md)
