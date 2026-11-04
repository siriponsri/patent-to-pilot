## Current owner amendment — 3 November 2026 local accounting epoch

This section supersedes earlier instructions below that require complete R1 recovery before all paid work or prohibit the owner-authorized accounting cutover. The USD100 cumulative ceiling and original GPU limits remain; this is not a fresh USD100 allowance. See [current repair handoff](../audits/pepo-blocked-goal-repair-20261103/README.md) and `LOCAL_ACCOUNTING_AND_GPU_FOLLOWUP.json` there.

- Owner explicitly authorized a new accounting epoch if historical R1 evidence cannot be recovered. Preserve original journals and proven 4 settled calls/USD0.0001464; unknown history remains unknown. Implemented one fixed E2 canonical journal under `%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`, shared across updated worktrees. No repeated creation, empty-ledger substitution or automatic epoch reset.
- Prospective E2 allowance is USD1, with USD98.9998536 held as an uncertainty buffer. This is not measured spending or a proven ceiling on missing history; lifetime budget guarantee is explicitly false. Current account/key credit and fresh route pricing are still required before paid dispatch; authorization alone does not prove available funds.
- Evidence, journals, outputs and receipts stay on the owner's Windows machine. Existing local `.env` is authorized for API; do not copy credentials to dr-train. dr-train performs computation with transient scratch only, returning outputs locally.
- Fresh patent encoder work completed on the approved V100 on 3 November 12:35:56–12:36:12 UTC, under the shared slot. This supersedes older no-GPU-run/access-blocked statements as the latest result; it does not reserve future capacity or close research goals.
- Do not demand R1 completeness as a gate for the accepted E2 cutover or ask for the approved GPU dates/UUID again. Keep pending/unknown billing blocked, preserve rights checks and resource conflict checks. Resume the same goal. The older note that a management key/MCP connection had not been created or tested is historical and is superseded by the 4 November read-only receipts below; no management key was created and no paid call was made.
- Current amendment 2026-11-04: the owner set an initial OpenRouter MCP/provider limit of USD30.00. A read-only account-level MCP `get-credits` receipt is recorded in `ptp-api-openrouter-mcp-recheck-r2-20261104`, and the sanitized `.env` observer recheck is recorded in `ptp-api-metadata-recheck-r12-20261104`. These observations do not bind exact dispatch-key remaining credit or scope: r12 reports an ordinary non-management key with HTTP 200, null provider limit/remaining limit, empty budgets, and `live_admission_enabled=false`. The older sentence saying MCP was not created/tested is historical and superseded; no management key was created and no paid call was made.

### Earlier authorizations and observations retained for provenance

# Owner one-time input / ข้อมูลจาก owner ครั้งเดียว

Status: `RECORDED / NO_REPEAT_NEEDED`

Recorded date: 2026-11-01 (Asia/Bangkok)

Project: Patent-to-Pilot HealthTech O1-O4

## Owner decisions

- The owner is running this as a solo project. There are no external participants, recruitment channels, or participant route for the current round.
- Do not wait for a participant route and do not ask for this information again.
- The current research design is a reproducible computational study with permitted real-data case studies. A human pilot and customer validation are future work, not mandatory gates for this round.
- Keep at least three real device cases for application and engineering demonstration. Three cases are not sufficient evidence for a comparative benchmark, user study, market validation, or a general business claim.
- Evaluate practical business value as potential operational value: citation quality, evidence coverage, dossier construction cost, machine time, GPU time, latency, and measured correction burden when available. Keep human time separate from machine time.
- If the owner runs the workflow personally, label the result `developer_self_evaluation` and report likely self-evaluation bias. Do not call it independent user validation.
- Do not claim willingness-to-pay, revenue, ROI, independent user validation, or customer adoption unless those facts are actually measured.
- Project deadline is 2026-11-15 (Asia/Bangkok). The date does not expand compute, dataset, paid-API, or data-transfer authorization.
- Historical original limits were USD8 and 24 hours. The recorded extension below supersedes those prospective ceilings; preserve the original ledger identity, history and start timestamps. Do not create a fresh budget, zero ledger or key.
- Any expansion beyond the recorded USD100/GPU extension still requires owner authorization; the extension below is already approved.

## Append-only resource extension recorded 2026-11-01

- The owner authorized continuation of the benchmark-expansion plan in `pepo-dataset-benchmark-expansion-20261101`.
- The cumulative project API ceiling for this continuation is USD100 across providers, including historical spend, pending/unknown reservations, and retries. This does not create a new ledger, reset the existing journal, or authorize automatic top-up.
- The existing V100 may be used at concurrency 1 through 2026-11-15 23:59 Asia/Bangkok, subject to live ownership/resource checks and the existing CPU/RAM/disk limits.
- Dataset downloads may proceed only for manifest-listed files after source, rights, expected size, checksum, and schema checks. NC or unresolved-rights data remains restricted to the permitted local research use and is not treated as commercial-release material.
- This extension supersedes only the earlier resource-ceiling sentence for new benchmark-expansion work. The solo-project, no-participant, no-repeat-needed decision and all historical receipts remain unchanged.

## Consequences for this round

Engineering O1-O4 may continue independently. Offline retrieval/evaluation, rights-aware dossier work, reproducibility artifacts, protocol, manuscript, and submission materials are not blocked by the absence of participants.

External business validation remains `NOT_VALIDATED`. Any future human-study materials in this repository are preparation templates only; they are not recruitment, consent collection, or evidence of user validation.

The manuscript may report the computational study and real-case application evidence, but it must keep developer self-evaluation, external business validation, market outcomes, and journal acceptance separate from the computational results.

## One-time owner action

None for participant access. Future owner action is required only for a new spend/data/time allowance, external outreach, human-study activation, or article submission/agreement.

## Paid-branch gate evidence / หลักฐาน gate ฝั่ง paid ที่ยังขาด

The cumulative USD100 ceiling and GPU window through November 15 are already approved. This does not create a new ledger, key, budget or reset any historical timing. The accepted E2 cutover is already bound to the shared local journal; missing or incomplete R1 history remains an explicit uncertainty boundary and is not a separate gate for the current paid branch.

1. Provide one current scoped v2 credit snapshot through the approved channel, with `provider=openrouter`, `source=approved_integration` or `owner_sanitized_snapshot`, fresh UTC timestamp, `authorization_id`, `account_scope`, `key_scope`, USD currency, remaining account/key credit or an explicit unlimited observation, and `snapshot_sha256`. Do not send the secret key.
2. If an R1 activity export later becomes available, it may be inspected read-only with `inspect_r1_history_export.py` and reconciled without treating consistency as proof of completeness. Do not create a zero ledger, relabel the four legacy receipts, or retry unknown calls.

The candidate will first run the read-only validator:

```text
python scripts/healthtech/inspect_r1_history_export.py --export <sanitized-export> --output <sanitized-receipt>
```

Only after the current scoped credit check passes will it recheck route, pricing, writer quiescence, rights, and conservative reservation. A missing or stale item keeps paid dispatch closed and does not stop local/offline work.

## Latest checkpoint binding

The latest repair handoff is [pepo-blocked-goal-repair-20261103](../audits/pepo-blocked-goal-repair-20261103/README.md), based on HEAD `88dc40471cb9078f929c02bb893cfa1e364da841` plus scoped uncommitted patches. Resume the existing goal. Do not ask the owner to repeat the USD100 approval, participant decision, secret key or GPU deadline. Paid dispatch still needs the one current scoped credit/limit observation above; route pricing is refreshed by the runner at action time. Remote work also needs permitted host access and live resource checks. These do not block independent CPU/offline work.


## Evidence located / remaining source request — 3 November, 19:23 Thai

The authorized SSH retry succeeded; do not ask for the already approved V100 dates/UUID again. Two preserved legacy journals were located and rechecked read-only: four settled attempts, USD0.0001464, unchanged original hashes. They are pre-R1 history and must not be relabelled a complete canonical R1 journal. See the final follow-up and ACCESS_AND_HISTORY_FOLLOWUP.json in the linked repair audit.

The owner does not need to construct JSON or create a ledger. An existing provider/account activity or billing export covering R1 from October 28 onward, together with current balance and account/key scope evidence, is an acceptable source for the implementer to inspect and map truthfully to the internal review schema. Include failures/pending items if the source records them; do not invent absent attempt IDs, phases, or amounts. This source request supersedes any interpretation above that the owner must manufacture the exact internal export format. If completeness cannot be established from that source, preserve the uncertainty and keep only paid dispatch blocked. No secret/new key/top-up is requested.

## One-time paid-branch handoff — current missing field

The participant decision, USD100 project authorization, E2 cutover, and owner-supplied USD30 initial provider limit are already recorded. Do not resend those approvals. The only remaining paid-branch input is a current, non-secret observation bound to the dispatch key used by the existing Windows `.env`:

- `provider`: `openrouter`
- observation time in UTC (`as_of_utc`)
- key scope or stable non-secret key identifier (a hash is acceptable)
- `limit_remaining` in USD, or an explicit `unlimited` result
- account/workspace scope, if the provider exposes it
- the provider response or receipt hash, if available

Do not send the API key, a management key, a screenshot containing credentials, or a newly created budget/key. A sanitized MCP response or the non-secret fields from `/api/v1/key` are sufficient. The implementer will bind the observation to the existing E2 journal, recheck the already-recorded route price, validate rights/writer quiescence, and reserve only the bounded canary if the canonical admission transaction passes. If the provider cannot expose the key limit, record that fact once; paid dispatch remains closed and the goal continues with the existing local/manuscript evidence.
