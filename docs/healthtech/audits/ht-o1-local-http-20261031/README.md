# HT O1 local HTTP jobs audit

Status: `PASS_LOCAL_HTTP_BROWSER_INTEGRATION`.

This package implements and verifies the local loopback HTTP workflow for the
2026-10-31 research-product goal. The browser acceptance covers job start,
running cancellation, resume/retry, source inspection, history reopen/edit,
reload, and selected-version JSON/Thai/English exports. It does not claim live
provider execution, remote embeddings, local Qwen generation, or the three
real-device end-to-end cases.

## Scope

- Base commit: `0d049802d36bc2eebe60331ec444d62469fd767f`
- Candidate: uncommitted isolated worktree `codex/research-product-o1-20261031`
- Provider mode: local offline engine only
- Paid calls: `0`
- Network provider calls: `0`
- Durable root: caller-owned `--data-dir`; the browser cannot select an output path
- Browser/backend origins: loopback only

## Implemented

- `POST /jobs` with bounded `Idempotency-Key` and canonical `DossierInput` validation.
- Durable queued/running/cancel_requested/cancelled/succeeded/failed metadata.
- Single-worker local execution around the existing `run_dossier` engine.
- Atomic job metadata writes plus existing atomic dossier history publication.
- `GET /jobs/{id}`, cancel acknowledgment, and fail-closed resume for failed/interrupted/unknown jobs.
- Versioned history read/edit with expected-parent conflict handling.
- Rights-aware source inspection and selected-version JSON/Markdown export.
- `GET /providers` exposes local availability and a closed paid-provider budget gate without guessing remaining funds.
- Frontend loopback adapter and provider selector preserve the existing file-import and IndexedDB path.
- Browser integration runs against a real temporary Chrome profile and a temporary backend root using synthetic data only.

## Verification

| Check | Result | Evidence |
|---|---|---|
| Focused backend, pre-live, and rights regressions | PASS with one existing optional tokenizer skip | `rtk proxy python -B -m pytest -q -rA -p no:cacheprovider tests/test_healthtech_http.py tests/test_healthtech_prelive.py tests/test_healthtech_repairs.py` |
| Frontend unit and adapter contract tests | PASS, 74 tests | `rtk proxy npm test` from `frontend/healthtech-web` |
| Real Chrome loopback HTTP acceptance | PASS | `browser-http-integration.json` |
| Full Python repository suite | PASS with one existing optional tokenizer skip | `rtk proxy python -B -m pytest -q -p no:cacheprovider` |
| Python compile check | PASS | `rtk proxy python -B -m compileall -q src/patent_to_pilot/healthtech/http.py scripts/healthtech/serve_http.py tests/test_healthtech_http.py` |
| CLI entrypoint smoke | PASS | `rtk proxy python scripts/healthtech/serve_http.py --help` |
| Whitespace check | PASS | `rtk proxy git diff --check` |

## Browser acceptance receipt

- Status: `PASS_BROWSER_HTTP_BACKEND_HISTORY_EXPORT`.
- Backend origin: loopback; frontend CSP and backend CORS remain loopback-only.
- Job lifecycle: start, cancel while running, resume/retry, and final success.
- History: version `1` reopened, edited, and published as version `2`.
- Source inspection: `PASS`; no source mismatch surfaced.
- Exports: selected version `2` JSON, Thai Markdown, and English Markdown.
- Provider calls: `0`; paid cost: `USD 0.00`.

## Not run / remaining

- Live OpenRouter or paid calls: `NOT_RUN` and intentionally blocked pending ledger reconciliation.
- Remote embedding, local/API generation comparison, and three real-device cases: `NOT_RUN`.
- Scientific semantic device-patent gold validation, commercial/user validation, deployment, and public release remain outside this package.

The next bounded action is candidate review, followed by the authorized commit
and push path if accepted. Keep live-provider, remote-compute, semantic-gold,
deployment, and commercial-validation branches separate.

