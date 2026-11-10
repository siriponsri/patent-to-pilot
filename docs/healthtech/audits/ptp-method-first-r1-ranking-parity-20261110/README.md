# Dev baseline parity tooling and declaration
Implemented manifest-bound dev/main ordered-ranking comparison and CLI. Metadata/query cohorts and independent reference/candidate manifest hashes are required. Protected/wrong-view/lane/corpus manifests fail before payload reads. Missing available queries, duplicates, labels, excessive depth and hash mismatch fail closed. Reports contain only aggregate parity counts and digests, no labels or ranking IDs.

34 targeted tests passed in 3.22s, Ruff passed (16 parity cases plus bound-runner/preparation regressions). Includes full CLI mismatch nonzero exit and refusal to overwrite evidence. Synthetic only; actual ranking files have not been read.

Declaration: docs/healthtech/research/MTM_DEV_BASELINE_PARITY_DECLARATION_20261110_EN.md. P/main X+U exact depth-200 equality required; prefixes 20/100/200 diagnostic, no tolerance. Actual independent hashes, isolated inputs/environment and launch manifest are required before execution. A03 is separate. No GPU/model run or actual parity result.

Next generated-view/prompt contract and permitted model/software identity inspection; actual data branch awaits curator/environment handoff.
