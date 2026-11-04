# Next actions

1. Review the three private outputs locally (case journal `ptp-e2-paid-canary-20261104T1354Z.jsonl`) against the frozen FDA fields. Record source-integrity findings only; do not treat schema validity as content correctness.
2. Any further paid work needs a new, explicit owner authorization and a new admission window: fresh key observation, MCP credit, and route pricing, all ≤300 s old. Never reuse this window's snapshots; the ledger rejects stale ones anyway.
3. The E2 epoch has USD 0.99945484 remaining. Do not reset or re-baseline it.
4. Before a matched paid comparison is used as a scientific result, freeze its cohort, splits, endpoints, and failure rules (see `GOAL.md` and the acceptance matrix). This canary is engineering evidence only.
5. Push to `origin/main` only when the owner asks.
