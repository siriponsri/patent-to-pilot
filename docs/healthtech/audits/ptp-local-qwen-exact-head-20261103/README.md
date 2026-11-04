# Current-head local Qwen3-8B run — 2026-11-03

This audit records one exact-head local generation pass for the existing
Patent-to-Pilot O1–O4 goal at candidate
`88dc40471cb9078f929c02bb893cfa1e364da841`. It is a contract/smoke run over
the three frozen FDA-only development cases, not a device–patent retrieval
evaluation and not evidence of semantic correctness.

## Exact staging and run

The isolated remote code directory
`codex-exact-head-88dc4047` was populated from the current worktree's
`src/patent_to_pilot` and `run_qwen_generation_evidence_pack.py`. The frozen
pack was copied from the owner-private pack and hash-checked before launch.
The runner used `PYTHONPATH=src`, the pinned Qwen3-8B revision, non-thinking
guided JSON decoding, `float16`, eight CPU threads, and the exact approved
V100 UUID. The shared GPU lock was free immediately before launch and the GPU
was idle after completion.

The pass completed `3/3` schema-valid cases. The raw receipt remains private
on `dr-train`; this repository stores only sanitized metrics, hashes, and
paths in `verification.json`.

The current worktree's full Python suite also passed `611` tests with `0`
failures, `0` errors, and `1` existing optional tokenizer skip; two existing
warnings remain. The JUnit receipt is `full-tests.xml`.

An earlier receipt under the separate `20261103` output root is retained as a
historical runtime-bound artifact, but it is not used as current-head evidence
because its full code/input/output root binding was not established. It is not
merged into this result.

## Boundaries

- Provider calls: `0`.
- Paid cost: `USD0.00`.
- API paired comparison: not run; canonical R1 ledger and current v2 credit
  snapshot remain absent.
- Schema validity does not establish retrieval quality, semantic entailment,
  citation correctness, or research superiority.
