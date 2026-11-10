# Prospective execution declaration binding

Checkpoint 2026-11-10 09:26:19 Bangkok; base 5118c8bd21a2c3ea58fd27374b3dae4ba05747f4. Authored inputs only. No scientific run or authorization change.

## Implemented

sacr_execution.bind_execution validates an independently pinned execution digest
against the six-stage dev plan before journal allocation. Required manifest references:
query, metadata, index, encoder, generator, prompts, code, method declaration and fidelity
policy. They must be complete-manifest SHA256 digests, not display names. Ordered source
rows exactly match the declared cohort; null explicitly records missing text. Source
hashes refer to allowed query text only, never labels. Output is detached from caller data.

Declared positive integer limits cover input/output/context/response size, call count,
wall/GPU seconds, peak memory, depth and views. Existing per-call and view/depth ceilings
are checked; total calls cannot exceed three per query. No real wall/GPU/memory envelope
has been selected by these tests. The small fixture memory/time values are artificial.

DevStageJournal accepts an optional execution declaration plus its required pin, persists
it exclusively, checks plan/slot/declaration consistency before every reservation and at
finalization, and includes its digest in completion. Existing unbound journals remain
available for authored component tests; that path is not an approved production runner.

## Evidence

70 focused tests PASS; full16 SACR test files:215 PASS. Ruff on three changed Python files
PASS. Negative cases include non-dev declarations, mismatched run/plan/source identities,
missing/extra identity fields, names instead of hashes, malformed/excess caps and changed
pins. Four mutation cases prove refusal before callback and before stage directory allocation.
Bound missing-input completion retains the execution digest.

## Limits and next action

This is declaration consistency, not file attestation or a security boundary. It does not
open or independently verify referenced manifests, adopt a fidelity policy, prove isolation,
check live GPU ownership/authorization, enforce cumulative resources or validate typed stage
outputs. Python callers and the filesystem are trusted; immutable external storage remains
necessary against concurrent/adversarial changes. Stage dependencies and actual text/embedding
provenance are not inferred from a COMPLETED callback.

Next connect allowed source bytes and existing preflight observations to these declarations,
then implement typed stage scheduling and live resource enforcement. Actual curator/R1,
generation compatibility and fidelity gates still precede research execution. No automatic
model retry, protected evaluation or anchor-only substitute is authorized.
