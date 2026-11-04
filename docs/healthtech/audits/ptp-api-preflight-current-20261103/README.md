# Current OpenRouter API preflight — 3 November 2026

This audit records a read-only current-route and rights preflight for the
existing Patent-to-Pilot goal. It does not record a paid provider generation.

The exact three-case rights-cleared pack remained valid with the same pack,
message, and payload hashes as the local current-head run. Public endpoint
metadata selected DeepInfra for `qwen/qwen3-32b` at the observed rates of
`USD0.08/M` prompt tokens and `USD0.28/M` completion tokens. The selected route
supports the reviewed structured-output contract.

The ordinary owner key was used only through the existing bounded read-only
metadata helper. The observation returned HTTP 200 for `/api/v1/key` and
reported lifetime usage `USD0.0001464` and daily usage `USD0`, matching the
four known settled legacy attempts in the existing audit. The helper could not
produce a scoped v2 account/key credit snapshot because the key is not a
management key; the observation therefore does not prove current credit or
remaining admission.

Paid dispatch remains `BLOCKED_BEFORE_RESERVATION`: the known canonical R1
registry/journal is still absent, and the current scoped v2 credit snapshot is
still unavailable. No journal, registry, reservation, attempt ID, retry,
provider generation, budget, or 24-hour window was changed.

The manuscript was rechecked after this preflight: 25 local links resolved with
zero missing targets; the current file SHA-256 is recorded in
`manuscript-integrity.json`. This is a documentation/link check, not a new
scientific evaluation.

Files:

- `preflight.json`: current pack/rights preflight, zero provider calls.
- `../ptp-api-current-metadata-20261103/public-endpoint-observation.json`:
  public route/pricing observation.
- `../ptp-api-current-metadata-20261103/model-snapshot.json`: exact runner
  snapshot derived from that observation.
- `../ptp-api-current-metadata-20261103/metadata-observation.json`: private
  sanitized `/api/v1/key` observation; do not publish or stage with public
  artifacts.

This audit is a checkpoint for the existing goal, not a new authorization and
not evidence of model quality, retrieval quality, citation correctness, or
business/user validation.
