# O4 local-generation HTTP action — 2026-10-31

Status: `PARTIAL_O4_HTTP_GENERATION_HARNESS_READY_O3_API_BLOCKED_LOCAL`.

This package binds the existing frozen local Qwen3 evidence-pack contract to
the same loopback HTTP job, history, and export lifecycle used by the local
retrieval engine. It does not claim a new Qwen run: the current checkout does
not expose an authorized vector configuration plus local-generation model
configuration for the three-case browser harness.

## Implemented

- Server-owned `local-generation` provider with fail-closed availability.
- Lazy child-process execution of the existing pack builder and Qwen runner;
  the HTTP server does not import `torch` or `transformers` at startup.
- Single-case frozen evidence-pack construction using the existing
  `ht-o3-qwen3-frozen-evidence-pack-v1` contract; source payloads stay out of
  the pack and temporary dossier/pack files are removed after each action.
- Durable `generation.json` job artifact, `GET /jobs/<id>/generation`, and
  generation data in the existing result response.
- Frontend persistence and display of structured generation output alongside
  backend history; a browser harness can submit an already validated
  `DossierInput` without changing the normal synthetic UI journey.
- Named Abbott browser harness with explicit environment gates. It writes the
  temporary case bundle outside Git and deletes it during teardown.

## Verified

- HTTP/provider/history/export regression: `6 passed`.
- Vector HTTP/evaluation regressions: `5 passed`.
- Frontend unit suite: `74/74`.
- Existing Chrome loopback integration: `PASS_BROWSER_HTTP_BACKEND_HISTORY_EXPORT`.
- Python compile and `git diff --check`: pass.
- Single-case pack smoke: `PASS_FROZEN_LOCAL_RESEARCH_PACK`; `source_payloads`
  are excluded from the generated pack.

## Not run or still blocked

- The three named Abbott browser harness is `NOT_RUN_ASSET_GATED`; it requires
  `HEALTHTECH_ABBOTT_COHORT`, `HEALTHTECH_ABBOTT_RIGHTS_MATRIX`, and a
  server-owned `HEALTHTECH_ABBOTT_VECTOR_CONFIG`.
- Real local Qwen HTTP generation is `NOT_RUN` in this checkout because the
  server-owned `ht-http-local-generation-config-v1` was not available in the
  permitted working tree. The injected provider test is contract evidence,
  not model-quality evidence.
- OpenRouter `qwen/qwen3-32b` comparison remains `BLOCKED_LOCAL`; no paid or
  provider request was dispatched.
- No clinical, legal, FTO, patent-validity, exhaustive-recall, investment,
  deployment, publication, or commercial claim is supported.
