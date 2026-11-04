# OpenRouter dispatch-key metadata recheck r12

Recorded: 4 November 2026 (Asia/Bangkok), observation started at
`2026-11-04T07:24:13.771567+07:00`.

This is a read-only continuation of the existing Patent-to-Pilot goal. The
owner-supplied `.env` was passed only to the existing metadata observer. The
credential value was not printed, copied, staged, persisted, or used for a
generation request.

## Observation

- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Endpoint: `/api/v1/key`
- HTTP status: `200`
- Key class: ordinary non-management key
- Key scope: sanitized SHA-256 only
- Lifetime usage: `USD0.0001464`
- Daily/weekly/monthly usage: `USD0`
- Provider-reported `limit`: `null`
- Provider-reported `limit_remaining`: `null`
- Provider-reported budgets: empty
- Account scope binding: not reconciled
- Account credit endpoint: not requested because this key is not a management key
- Live admission: `false`
- History completeness: not proven

The owner-set USD30.00 initial MCP/provider limit remains recorded as
provider-side metadata. This observation does not expose a key-level limit or
remaining credit and therefore does not convert that limit into paid-dispatch
admission evidence.

## Gate decision

`PAID_BLOCKED_BEFORE_RESERVATION`. The existing E2 journal, legacy spend, and
unknown-history boundary remain unchanged. No reservation, paid provider
call, retry, ledger mutation, budget reset, or runtime-window reset occurred.

The next paid prerequisite remains one permitted current scoped credit/limit
observation that binds the dispatch key, followed by fresh route pricing in
the admission window. The local/O4 branch remains independent and usable.

## Receipt

- Sanitized observation: `metadata-observation.json`
- Observation response SHA-256:
  `e84b6015e81e54607537040502062eb3a7b5b5f704bdf7565adac8ac99775521`
- Sanitized file SHA-256:
  `63dab1d55cd74a77343a1d060cef98cb075ac2783dae316100d683357ebad5f4`
- Observer: `scripts/healthtech/collect_openrouter_metadata.py`
- Observer regression: `20 passed, 0 failed, 0 skipped` from
  `tests/test_openrouter_metadata_observation.py`
