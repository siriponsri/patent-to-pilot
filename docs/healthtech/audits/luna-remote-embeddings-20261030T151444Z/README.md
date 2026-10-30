# Luna remote embeddings package

Run ID: `luna-remote-embeddings-20261030T151444Z`

This run closes the local, inspectable portion of the remote-embedding work:

- runtime-only text export with stable dataset-scoped IDs and text hashes;
- resumable float32 vector shards with atomic publication and strict import validation;
- exact deterministic NumPy/memmap-compatible retrieval injection for `SharedRetriever`;
- optional vector-backed candidate augmentation in the dossier engine while preserving lexical defaults;
- DAPFAM evaluator guards for duplicate rankings, unknown IDs, metric bounds, and explicit failure denominators;
- clean-checkout authored cross-cohort fixtures and external-parent integration-contract handling.

Remote SSH canary/full encoding, vector transfer, real dense evaluation, and real vector-backed dossier cases remain `NOT_RUN` because the audited host key, allocation, job root, and execution window were not available in this run.

Canonical evidence is in `CHECKPOINT.json`, `MORNING_REPORT_TH.md`, and `NEXT_ACTIONS.md`.
