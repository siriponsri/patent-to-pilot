# Next actions

1. Verify the existing strict SSH trust state without printing keys or credentials.
2. Confirm the named `dr-train` job root, GPU UUID or CPU quota, wall-time window, VRAM/RAM/disk limits, and Podi/shared-service restrictions.
3. Export the permitted runtime corpus and queries using the new JSONL contract; do not include qrels, gold labels, split labels, or raw restricted payloads.
4. Run the bounded 32-100 document canary, validate model/config/text/order/dimension/norm, then resume the full shard job only if the canary passes.
5. Transfer only named shard artifacts with SHA-256 verification and import them through `load_vector_bundle`.
6. Run matched BM25/dense/hybrid evaluation and three permitted dossier cases using returned vectors; preserve failure denominators and unjudged policy.

Current stop boundary: local implementation and authored regression evidence are complete; remote execution is `NOT_RUN`, not mocked as complete.
