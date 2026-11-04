# Next actions

1. Keep the private encoder snapshot and manifest outside Git.
2. Do not infer a GPU allocation from an idle device or an empty lock file.
3. Obtain the live `dr-train` allocation/ownership receipt before transfer.
4. Run `encode_transformer_shards.py` only with the pinned model binding,
   approved V100, concurrency 1, and the existing resumable output protocol.
5. Validate returned vector bundles before any O4 retrieval comparison.
6. Keep OpenRouter paid dispatch blocked until the existing canonical R1
   history/export and current scoped credit snapshot are supplied and bound.

