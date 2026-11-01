# Changes

- Require an existing reviewed canonical SQLite identity at registration and at every reservation; reject empty/non-SQLite files, alternate registries, copied paths and direct-component bypasses. Preserve the existing cumulative authority and unresolved exposure.
- Separate durable authority hash from per-run pricing hash, retain per-attempt observations and allow a fresh price on the same verified ledger. Existing historical hash/schema migrations require explicit reconciliation, never a fresh zero ledger.
- Scope and expire account/key availability observations; consume conservative reservations atomically across runs/processes, including requests in flight when a snapshot was captured. Bind actual dispatch credential fingerprint without emitting secrets. Hashes and source labels remain assertions, not provider authentication.
- Prevent provider parameters from replacing bound request fields. Use byte/schema/framing bounds and the actual rate ceiling. Fix the bounded non-thinking snapshot envelope.
- Retain provider generation IDs and debit after output failure; distinguish unknown billing, unrun cases, mocked transport and actual wire payload hashes.
- Check pack integrity, unique source/evidence/candidate identities and exact non-synthetic model-visible field review. Unknown evidence fields cannot enter messages.
- Add offline sanitized export consistency checking without import or activation. Require external reconciliation for completeness and old-writer shutdown.
- Correct O4's remaining research requirements and prepare an updated PR description without publishing it.

Validation includes meaningful negative cases, process concurrency, crash/resume,
replay/settlement, price refresh, mid-flight credit capture, failed output cost,
payload tampering and full Python regression. See verification.json for exact
counts, commands, source hashes, skip and warnings.
