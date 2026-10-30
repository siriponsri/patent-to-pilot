# Matched vector evaluation runner

Run ID: `luna-remote-embeddings-eval-20261030T160039Z`

Parent: `luna-remote-embeddings-20261030T155013Z`

Code candidate: `cd09fbc`

Status: `PASS_LOCAL_MATCHED_EVAL_RUNNER_REMOTE_NOT_RUN`

Added a local-only evaluation runner that consumes the validated vector
bundle, encodes queries with a hash-matched model/tokenizer, and evaluates
BM25, dense, and RRF-hybrid rankings under the existing DAPFAM evaluator.
Qrels are exported through DuckDB into a temporary directory and are never
sent to the remote encoder or written to the result directory.

The end-to-end smoke used the 64-row local canary bundle, two authored query
rows, and two authored qrel rows. It is a contract smoke, not a real DAPFAM
quality result. Full 45,336-row/1,247-query dense evaluation remains blocked
until the remote bundle is produced and returned.

See `EVAL_RUNNER_RECEIPT.json` for hashes, metrics, and exact boundaries.
