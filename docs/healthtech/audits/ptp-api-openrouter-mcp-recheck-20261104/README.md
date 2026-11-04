# OpenRouter MCP credit-check capability recheck

Date: 2026-11-04 (Asia/Bangkok)

## Scope

This is a bounded, read-only capability check for the existing Patent-to-Pilot
goal. It does not create a goal, epoch, budget, zero ledger, reservation, paid
request, retry, GPU job, merge, push, or publication.

Candidate worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`

Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`

The candidate is intentionally dirty with existing owner/Claude/Luna and
research changes. No reset, clean, stash, or unrelated-file cleanup was done.

## Official MCP capability

The owner-supplied OpenRouter MCP documentation was fetched read-only at
`https://openrouter.ai/docs/guides/overview/mcp-server` with HTTP 200 on
2026-11-03T23:52:17Z. The page documents a `get-credits` tool for remaining
account credit. It also documents that first-time MCP consent creates a
dedicated connection key separate from other keys, expiring within 7 days and
starting with a $10 spend cap that can be edited during approval.

That connection-key behavior is an account/authentication change. It is not
the existing E2 journal key and must not be created implicitly for this goal.

## Runtime discovery

The actual tool catalog was inspected without invoking any external account
action:

- Exact OpenRouter-specific MCP actions found: `0`.
- MCP resources/templates advertising an OpenRouter server: `0`.
- Local Codex CLI executable available as `codex`: `false`.
- Local Codex MCP configuration contains `mcp_servers.openrouter`: `false`.
- No authenticated OpenRouter MCP session was available to call `get-credits`.

The check therefore proves only capability/documentation availability, not the
owner's current OpenRouter credit. No API key, OAuth token, or secret was read,
printed, or persisted.

## Existing E2 gate

The prior E2 credit/route recheck remains authoritative and unchanged:

- Existing local E2 journal and legacy spend are preserved.
- Existing legacy actual debit remains `USD0.0001464`.
- No new reservation, provider call, retry, or ledger mutation occurred.
- Paid comparison remains `PENDING_CURRENT_SCOPED_CREDIT` before reservation.

An MCP `get-credits` result, if later obtained through an approved existing
session, would provide account-credit evidence only. The paid gate still needs
the exact key remaining limit (or explicit unlimited status), observation time,
key scope, and a fresh route-price observation inside the runner admission
window. It must be bound to the existing E2 ledger and frozen payload.

## Handoff

Do not add an OpenRouter MCP server or initiate consent from this worktree.
If the owner enables an approved MCP session outside this task, run only the
read-only `get-credits` action and save a sanitized receipt. Otherwise request
the already-defined single non-secret current credit/key-limit observation and
continue local/offline research without closing the goal.

