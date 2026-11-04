# OpenRouter route-pricing recheck — 4 November 2026

Status: `PASS_FRESH_PUBLIC_ROUTE_PRICING_PARTIAL_API_GATE`

This is a read-only public endpoint observation for the existing Patent-to-Pilot
goal. It does not read the dispatch key, reserve the canonical ledger, send a
provider request, retry an attempt, or change budget/history state.

## Candidate

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Observation UTC: `2026-11-04T00:54:43.4535612Z`

## Fresh route observation

The public endpoint metadata for `qwen/qwen3-32b` returned three provider
endpoints. The selected route remains `DeepInfra` with `deepinfra/fp8`, status
`0`, context length `40,960`, and maximum completion tokens `16,384`.

| Route | Prompt USD/M | Completion USD/M | Context | Max completion |
|---|---:|---:|---:|---:|
| DeepInfra / `deepinfra/fp8` | 0.08 | 0.28 | 40,960 | 16,384 |
| Tenstorrent / `tenstorrent/fp8` | 0.14 | 0.40 | 20,000 | 16,400 |
| SiliconFlow / `siliconflow/fp8` | 0.14 | 0.57 | 131,072 | 117,964 |

The sanitized observation is in `public-route-observation.json`. The runner-
shaped pricing snapshot is in `model-snapshot.json`; its `snapshot_sha256`
binds to the observation file rather than to any credential or response body.

## Gate boundary

This receipt satisfies the fresh public route-pricing observation only. It does
not prove account credit, exact dispatch-key scope, key remaining limit, ledger
admission, rights to transfer a dossier payload, or scientific completion.

The owner-supplied USD30 provider-side cap remains separate from the project
USD100 cumulative ceiling and E2 prospective USD1 allowance. No ledger policy
or canonical journal was rebound in this checkpoint; the existing E2 journal,
unknown history, and legacy receipts remain authoritative.

## Resource mutations

- Paid provider calls: `0`
- Reservations or ledger writes: `0`
- Retries or pending-attempt changes: `0`
- GPU jobs: `0`
- Dataset downloads: `0`
- Secrets read or persisted: `0`

Next admission step: obtain or expose a current non-secret observation binding
the exact `.env` dispatch key scope and remaining limit (or explicit unlimited
status), then recheck the canonical journal and bind this fresh route snapshot
inside the same admission window before any reservation.
