# Patent-to-Pilot parallel local/API checkpoint — 2026-11-03

Status: `PASS_SHARED_CONTRACT_LOCAL_RUNTIME_NOT_RUN_API_DISPATCH_BLOCKED`.

This checkpoint continues the original Patent-to-Pilot O1–O4 goal at candidate
`88dc40471cb9078f929c02bb893cfa1e364da841`. It separates the local Qwen path
from the paid OpenRouter path while binding both to the same owner-private
FDA-only evidence pack, exact message contract, output schema, and source
hashes.

## Shared contract

- Pack SHA-256: `e033456a1f9fe53a3bf8b2c4d1e6c07e1e6727796620f94f35f1ad505499526e`.
- Pack file SHA-256: `0b2bef9fcf8c3eff6106a1786885e4407ea4b8c9e628397ab8e52a392204ced9`.
- Cases: `HT-DEV-MITRACLIP`, `HT-DEV-TENDYNE`, `HT-DEV-TRICLIP`.
- Exact message hashes match in both branches; the complete per-case hashes are
  recorded in `local-preflight.json`, `api-preflight-receipt.json`, and
  `verification.json`.
- Model-visible data is rights-cleared metadata and reviewed structured FDA
  fields only. Raw source payloads, evaluator labels, gold-derived queries,
  credentials, and generated output are excluded from the API manifest.

## Local path

The current-head contract preflight passed for all three cases, but no new
Qwen3-8B inference was started. The permitted model root is not exposed in
this worktree, `dr-train` SSH returned `Permission denied (publickey,password)`,
and the historical HTTP service on port `18787` actively refused the read-only
probe. The existing service was not touched. The prior private guided/unguided
receipts remain historical artifacts and are not promoted to current-head
inference results.

The local runner remains bound to the exact approved V100 UUID, concurrency
one, the existing 15 November 2026 23:59 Thailand window, shared slot, and
no-overwrite receipt behavior.

## API path

The current source-backed transfer review now matches the actual model-visible
messages and route spelling at the boundary. The three-case API dry-run passed
rights/payload validation with `ALLOWED_WITH_ATTRIBUTION`; provider calls and
paid cost were both zero.

Paid dispatch remains blocked before reservation. The canonical registry/journal
is not present in the known canonical location, and no current v2 account/key
credit snapshot is available. The historical visible debit of `USD0.0001464`
is preserved; no replacement ledger, zero ledger, budget reset, new attempt ID,
or retrospective cost was created. No retry is permitted for any unresolved
attempt until the existing journal is reconciled.

## Verification

- Focused regression: `33 passed, 0 failed, 0 skipped`.
- Full Python suite: `611 passed, 0 failed, 1 skipped`.
- Compileall: `PASS`.
- `git diff --check`: `PASS`.
- New API calls, GPU jobs, dataset downloads, ledger mutations, budget resets,
  and 24-hour-window resets: `0`.

Required owner evidence, once only: the exact existing canonical R1 journal
location or a sanitized all-attempt export, plus a current sanitized
account/key credit snapshot if the approved integration cannot supply it. Do
not send a key or secret. Until then, continue local/offline and manuscript
work independently and keep O3 `PARTIAL`.
