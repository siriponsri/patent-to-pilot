# E2 paid canary: qwen/qwen3-32b via DeepInfra

- Run ID: `ptp-e2-paid-canary-20261104T1354Z`
- Status: **PASS**. This is an engineering and accounting canary only. It is not a scientific result, and schema validity does not mean the content is correct.
- Authorization: owner chat instruction (2026-11-04), under `PTP-HT-OR-E2-20261103-USD100`. Only the three frozen cases, USD1 cap, existing E2 ledger, no retry, GPU, long run, worktree, ledger reset, or push.
- Checkout: existing `main` at `e948cd5`, clean at dispatch.
- Parent: [MCP admission check](../ptp-normal-mcp-admission-check-20261104/README.md)
- Machine-readable record: [verification.json](verification.json). Sanitized runner receipt: [sanitized-receipt.json](sanitized-receipt.json). Exact gate and dispatch script: [e2_window.py](e2_window.py).

## Admission window (one window, limit 300 s)

The window opened at `13:54:32.9Z`. Pricing was captured at `13:54:59.2Z` and dispatch started at `13:55:07.5Z`, when the credit observation was 34.6 s old and the pricing 8.3 s old. Every gate below passed before any reservation:

| Gate | Result |
|---|---|
| Writer quiescence | PASS: no python/git process on the repo or private tree, clean tree, ledger hash unchanged, no SQLite sidecars |
| Account credit (MCP `get-credits`) | PASS: USD 9.9998536 remaining |
| Exact-route pricing (public endpoint and MCP) | PASS: DeepInfra `deepinfra/fp8`, USD 0.08/M prompt and 0.28/M completion, context 40960; max price enforced on the request |
| Dispatch-key scope (existing collector, `GET /api/v1/key`) | PASS: `sha256:7cbe4013…` matched; hashed creator and workspace IDs matched; not a management key |
| Credit join (`credit_from_metadata`) | PASS: snapshot `dfc5aee7…` |
| Rights and payload identity (fresh dry-run) | PASS: pack `e146ab85…` and all case message/payload hashes equal the rights receipt; openFDA `ALLOWED_WITH_ATTRIBUTION` |

## Result

| Case | Status | Input tokens | Output tokens | Latency (s) | Cost (USD) | Billing |
|---|---|---:|---:|---:|---:|---|
| HT-DEV-MITRACLIP | SUCCESS, schema-valid | 1017 | 363 | 14.41 | 0.000183 | settled |
| HT-DEV-TENDYNE | SUCCESS, schema-valid | 1036 | 356 | 16.55 | 0.00018256 | settled |
| HT-DEV-TRICLIP | SUCCESS, schema-valid | 1020 | 350 | 11.89 | 0.0001796 | settled |
| **Total** | 3/3 | 3073 | 1069 | 42.85 (wall 43.96) | **0.00054516** | 3 settled, 0 unknown |

There were 3 provider calls, 0 retries and 0 reasoning tokens. The conservative pre-run bound was USD 0.0018. The account usage reported by MCP `get-credits` rose from 0.0001464 to 0.00069156, a delta equal to the run cost. MCP `get-generation` for the first case reports DeepInfra, the same cost and tokens, a single provider response, and `finish_reason=stop`.

## Ledger

The canonical ledger was updated only by the existing runner (`d0041eda…` → `d19f58ec…`). Integrity is `ok` and it holds 3 settled attempts, none pending or unknown. The epoch scope row is now bound to `owner-asserted-account:7cbe…` / `sha256:7cbe…`, following the existing `owner_credit_capture` naming convention. The four legacy receipts are preserved. Known actual spend including legacy is USD 0.00069156, and USD 0.99945484 remains in the E2 epoch cap. The ledger was not reset.

## Boundaries

- Generated text exists only in the private local case journal (`%LOCALAPPDATA%/…/evidence/api-generation/ptp-e2-paid-canary-20261104T1354Z.jsonl`, SHA-256 `5884e20c…`). It is not in Git.
- "SUCCESS" means valid JSON matching the frozen schema. Literal source match is not semantic entailment, and three FDA-only cases do not show adaptive benefit or any statistical effect.
- No key, `.env` content, raw account or workspace identifier, or generated text is stored in this folder.

Next: [NEXT_ACTIONS.md](NEXT_ACTIONS.md).
