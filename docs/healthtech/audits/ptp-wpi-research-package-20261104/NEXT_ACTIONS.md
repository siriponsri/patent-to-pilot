# Next actions

Ordered by evidence value. Each item can be done without new owner input unless marked.

1. Done: the PI4PC replication (freeze `1665075`) did not replicate the dense advantage, and fusion reversed sign. A possible next study is a granularity-aware policy (document level → dense, paragraph level → fusion). It must be preregistered as new, with its own validation selection, and must not be re-tuned on these test results.
2. **Matched local-vs-API generation on the FDA pack (O3).** Run local Qwen3-8B on dr-train against the same three-case messages, and audit both with `content_audit.py`. The API side already exists. No new paid call is needed unless more cases are added.
3. **If more paid work is wanted**, the E2 allowance is USD 10 cumulative (owner, 2026-11-04). The epoch code (`providers/local_epoch.py`) still enforces USD 1, with USD 0.99945484 left. Raising it needs a recorded, append-only policy amendment in the existing ledger plus a test. Do this only when a planned paid study exceeds the current residual. Never reset the ledger.
4. **Clean-clone reproduction** of the Track A pipeline from the registry commands, on a fresh checkout of the pushed head.
5. **Owner (decision)**: see the decision packet in [READINESS.md](READINESS.md).
