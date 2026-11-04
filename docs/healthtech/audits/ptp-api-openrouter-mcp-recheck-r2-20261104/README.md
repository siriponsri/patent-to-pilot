# OpenRouter MCP follow-up after owner configuration

Date: 2026-11-04 (Asia/Bangkok)

## Scope

This follow-up continues the existing Patent-to-Pilot goal. It verifies the
owner's newly configured OpenRouter MCP entry and records the requested first
MCP key cap. It does not create a goal, epoch, project budget, zero ledger,
reservation, paid request, retry, GPU job, merge, push, or publication.

Candidate worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`

Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`

## Verified CLI state

The installed Codex CLI was invoked read-only from its resolved executable
path with:

```text
codex mcp list
codex mcp get openrouter
```

Observed result:

- `openrouter` is enabled.
- Transport is `streamable_http`.
- Endpoint is the configured OpenRouter MCP endpoint.
- Authentication mode is OAuth.
- The earlier login process is no longer present when polled by PID.

The CLI management output does not return account credit, key cap, or a
`get-credits` result. The current agent tool catalog has not exposed an
OpenRouter-specific action in this turn, and generic MCP resource discovery
does not list an OpenRouter resource. No tool call was invented or attempted.

## Actual MCP credit observation

After the owner configured the server, a separate Codex helper was run in
`--ephemeral --sandbox read-only` mode with an instruction to call only the
OpenRouter MCP `get-credits` action. The action completed successfully and
returned this sanitized account-level payload at the wrapper observation time
`2026-11-03T23:58:56.9604548Z`:

```json
{"data":{"total_credits":10,"total_usage":0.0001464}}
```

The MCP response did not include its own timestamp, an exact key remaining
limit, key scope, or an explicit unlimited status. The `total_usage` value
matches the existing four legacy settled receipts, but this does not prove
that historical coverage is complete. The owner-supplied `USD30` MCP key cap
is therefore kept separate from the account-level credit payload and is not
treated as measured project allowance.

## E2 reconciliation

The existing canonical journal was opened read-only after the new MCP
observation. `PRAGMA integrity_check` returned `ok`; the journal contains four
legacy settled receipts totaling `146400` nano-USD (`USD0.0001464`), zero
operational rows in `budget_attempts`, and zero rows in
`budget_attempt_context`. The MCP `total_usage` matches that legacy total.

This confirms the observed usage reconciliation without proving historical
completeness and without binding the MCP connection key to the E2 key scope.
The E2 journal was not written.

## Budget interpretation

The owner supplied a first-round MCP key limit of `USD30`. This is recorded as
an owner-supplied provider-key cap, not as a change to the Patent-to-Pilot
project authorization, E2 journal, prospective allowance, or historical spend.
It is not treated as evidence that USD30 is available for project inference.

The existing E2 ledger and paid gate remain authoritative. No reservation,
provider call, retry, ledger mutation, history reset, or budget reset occurred.

## Gate status

`PARTIAL_ACCOUNT_CREDIT_RECONCILED_BEFORE_RESERVATION`

The next valid action is a read-only `get-credits` call through the actual
authenticated MCP action once that action is exposed by the runtime. The
result must be saved as a sanitized receipt and reconciled with E2. A credit
result alone still does not prove the exact key remaining limit; keep the
key-limit/scope and fresh route-price requirements in force. The existing E2
ledger remains unchanged.

Until then, continue local/offline work and do not dispatch paid inference.

The current long-run overview and authorization/budget amendment were also
rebound to this evidence without changing historical policy text:

- `docs/healthtech/long-runs/README.md`
- `docs/healthtech/long-runs/AUTHORIZATION_AND_BUDGET.md`

Their relative-link checks passed with `31` and `4` links checked,
respectively, and zero missing links.

