# Normal-round OpenRouter MCP admission check

- Run ID: `ptp-normal-mcp-admission-check-20261104`
- Observed: `2026-11-04T13:31:38Z` to `13:36:30Z` (UTC)
- Checkout: existing `main` at `a8c8e229e6489bb29ae6f88f310f7307c8a09441`, equal to `origin/main` (`0 0`)
- Parent: [E2 Normal-round addendum](../ptp-e2-admission-recheck-20261104/NORMAL_ROUND_20261104.md)
- Scope: read-only inspection of MCP credit, key, and pricing, plus account binding, rights, writer quiescence, the E2 ledger, and dr-train reachability. No paid model call, reservation, ledger write, GPU job, long run, worktree, push, or merge.
- Machine-readable record: [verification.json](verification.json)

## Result

| Gate | Status | Basis |
|---|---|---|
| MCP tools usable in this session | PASS | `ping`, `get-credits`, `get-current-key`, `list-model-endpoints`, `list-models` all returned data; no billable tool was called |
| Fresh account credit | PASS | Account `total_credits` 10, `total_usage` 0.0001464 (remaining 9.9998536 USD) at `13:33:10Z`; usage equals the four legacy receipts |
| Same-window exact-route pricing | PASS | `qwen/qwen3-32b`, DeepInfra `deepinfra/fp8`, USD 0.08/M prompt, 0.28/M completion, context 40960; unchanged from snapshot `c680da33…` |
| Account binding | PASS | MCP key `creator_user_id` and `workspace_id` SHA-256 values equal those recorded for the dispatch key at `11:21:15Z` |
| Dispatch-key scope binding | **BLOCKED** | The MCP key is a separate OAuth key; it cannot observe the dispatch key `sha256:7cbe4013…d7b97` that the ledger requires |
| Credit freshness at dispatch | **BLOCKED** | This round forbids reservation, so the observation expires before any lawful dispatch; it was not written as a ledger snapshot |
| Rights | PASS | Receipt and preflight agree on all three case message/payload hashes; openFDA `ALLOWED_WITH_ATTRIBUTION` |
| Writer quiescence | PASS at observation | Dirty patch, ledger hash, private E2 tree and retained worktrees unchanged across a 4-minute recheck; a Codex app-server is running, so recheck before any reservation |
| E2 journal (ledger) | PASS | Read-only open; integrity `ok`; SHA-256 `d0041eda…b8c1d2` unchanged; 0 attempts, 0 scope rows, 4 legacy receipts; no output journal because nothing was dispatched |
| dr-train SSH | PASS | One read-only BatchMode session; RTX 2080 Ti and V100 32GB idle, no GPU compute apps |

Paid status remains `BLOCKED_BEFORE_RESERVATION`. The blocker has changed from "stale credit" to "dispatch-key scope binding plus round authorization". Account-level credit and pricing can now be observed fresh through MCP at any time.

## Findings

1. **Erratum (fixed with owner approval):** the parent audit, its verification files, the Normal addendum, and `progress.json` recorded the normalized credit hash as `…3eb80408e9e9a5f06c5d`. The embedded value, and the value recomputed by `normalize_credit()`, is `87ca37f6789519fdd1184afaa157423fedea33b61b6a3eb80408f9e9a5f06c5d`. One hex digit differed. All five files now carry the correct value and nothing else changed in them. The wrong value remains in committed history at HEAD. The Normal addendum's own SHA-256 changed to `c61cfa7e…1c1688`; `verification.json` maps the before and after values for both untracked files.
2. **MCP key limit:** the current MCP key reports `limit=null` (UNLIMITED) and expires `2026-11-11T12:27:55Z`. The earlier USD30 note and the announced USD10 cap are not visible on this key. The account balance is the effective bound.
3. **Preserved work:** the prior uncommitted patch (`git diff --binary` SHA-256 `c264ee38…3062bf`, 38428 bytes, plus two untracked audit files) was left byte-for-byte unchanged.

## Not recorded

No API key, key label, raw account or workspace identifier, `.env` content, raw payload, or private path content beyond `%LOCALAPPDATA%` references is stored in this folder.

Next steps: [NEXT_ACTIONS.md](NEXT_ACTIONS.md).
