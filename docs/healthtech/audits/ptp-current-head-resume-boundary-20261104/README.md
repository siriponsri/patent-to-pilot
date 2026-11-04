# Patent-to-Pilot current-head resume boundary

This checkpoint resumes the existing Patent-to-Pilot goal on the intentionally
dirty candidate. It does not create a goal, reset the E2 journal, replay a
pending request, launch a new GPU job, or dispatch paid API inference.

## Candidate and ownership

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Working tree: intentionally dirty; owner, Claude, Luna, research, and audit changes preserved.
- The previous stale O1 receipt bound to `a7d064dc...` is not used as evidence for this checkpoint.

## What is verified on this candidate

1. The loopback UI -> HTTP vector job -> source inspection -> history edit/reopen -> JSON/Thai/English export path was rechecked by the browser integration. The fresh synthetic browser receipt is one case with history versions `1 -> 2`, no browser errors, zero provider calls, and USD0.00 paid cost. The named 3-case current-head vector receipt remains the separate artifact at `ptp-local-http-vector-20261103`.
2. The Python HTTP contract suite covers local-generation provider catalog, job execution, generation result, history, and export using an injected test provider. It is contract evidence, not a Qwen model result.
3. The current private Qwen3-8B run remains bound to this HEAD and the frozen rights-cleared pack. It produced schema-valid output for 3/3 patent-candidate cases with 7,301 prompt tokens, 1,448 output tokens, mean latency 54.320437 seconds, zero provider calls, and USD0.00 paid cost. The raw and parsed output remain private.
4. The fresh V100 PatEmbed and multilingual-e5 encoding/retrieval diagnostic remains a separate protocol. It is not pooled with the local generation run or the older HT-B0b/B4 frontier.

## Explicit boundary

The browser test started without a server-owned local-generation config. The
browser `local-generation` option therefore remained unavailable. The named
Abbott browser harness exists and supports `HEALTHTECH_ABBOTT_PROVIDER=local-generation`,
but the current checkout has no authorized cohort/rights/vector/generation
configuration for a new 3-case browser generation run. This is recorded as
`NOT_RUN_ASSET_GATED`; the older browser-generation receipt is not promoted to
current-head evidence.

This distinction leaves the evidence as:

- browser-verified current-head local vector lifecycle;
- Python/HTTP local-generation contract lifecycle;
- private current-head Qwen3-8B generation receipt;
- paid qwen/qwen3-32b branch not run.

## E2 paid boundary

The canonical E2 journal remains read-only and intact:

- SQLite integrity: `ok`;
- four legacy settled receipts, known actual debit `USD0.0001464`;
- zero operational attempts and zero pending/unknown rows;
- prospective allowance `USD1.00`;
- historical completeness `UNKNOWN_OWNER_ACCEPTED_CUTOVER`.

The latest sanctioned observation has lifetime usage only. Current scoped
credit and remaining key limit are unavailable, so the paid branch is
`BLOCKED_BEFORE_RESERVATION_CURRENT_SCOPED_CREDIT_UNAVAILABLE`. No route
refresh, reservation, provider call, retry, ledger mutation, budget reset, or
time-window reset occurred in this checkpoint. Do not replay any unknown or
pending request.

## Research and business boundary

The local generation and source-binding values are operational/computational
evidence. They do not establish semantic relevance gold, adaptive superiority,
clinical or FTO validity, independent user validation, revenue, ROI, or
willingness-to-pay. The research goal remains active and descriptive.

## Evidence files

- `verification.json` - machine-readable candidate, tests, protocol separation, and paid gate.
- `CHECKPOINT.json` - short resumable state.
- `focused-python.log` - current focused Python command output.
- `frontend-unit.log` - current frontend unit output.
- `browser-http-integration.log` - current browser loopback output.
- `node-check.log` - syntax check for the named browser harness.

## Next action

Continue offline reproducibility and owner-review work. If the paid model
comparison remains required, obtain one non-secret current scoped credit/limit
snapshot for the same account/key. Then reconcile E2, refresh exact route
pricing inside the admission window, revalidate the rights-cleared payload, and
reserve no more than the existing USD0.25 canary through the same journal.

