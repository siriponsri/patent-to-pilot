# Next actions

1. Confirm the named `dr-train` job root, GPU UUID or CPU quota, wall-time window, VRAM/RAM/disk limits, and Podi/shared-service restrictions.
2. Reuse the validated runtime export; do not include qrels, gold labels, split labels, or raw restricted payloads.
3. Run the bounded 32-100 document canary, validate model/config/text/order/dimension/norm, then resume the full shard job only if the canary passes.
4. Transfer only named shard artifacts with SHA-256 verification and import them through `load_vector_bundle`.
5. Run matched BM25/dense/hybrid evaluation and three permitted dossier cases using returned vectors; preserve failure denominators and unjudged policy.

Current stop boundary: local implementation and authored regression evidence are complete; remote execution is `NOT_RUN`, not mocked as complete.
