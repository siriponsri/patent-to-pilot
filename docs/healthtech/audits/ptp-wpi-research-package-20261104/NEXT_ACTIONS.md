# Next actions

Ordered by evidence value. Each item can be done without new owner input unless marked.

1. **Replication on PI4PC (paragraph-level)**, using the same frozen methods and the same validation-then-test rule, with a new freeze before test. This tests whether the dense > BM25 and fusion < dense pattern holds on a second task. GPU only; no paid calls.
2. **Matched local-vs-API generation on the FDA pack (O3).** Run local Qwen3-8B on dr-train against the same three-case messages, and audit both with `content_audit.py`. The API side already exists. No new paid call is needed unless more cases are added.
3. **If more paid work is wanted**, the E2 allowance is USD 10 cumulative (owner, 2026-11-04). The epoch code (`providers/local_epoch.py`) still enforces USD 1, with USD 0.99945484 left. Raising it needs a recorded, append-only policy amendment in the existing ledger plus a test. Do this only when a planned paid study exceeds the current residual. Never reset the ledger.
4. **Clean-clone reproduction** of the Track A pipeline from the registry commands, on a fresh checkout of the pushed head.
5. **Owner (decision)**: see the decision packet in [READINESS.md](READINESS.md).
