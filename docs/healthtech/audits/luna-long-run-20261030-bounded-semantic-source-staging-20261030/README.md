# HT-M25 bounded semantic source staging

- Run ID: `luna-long-run-20261030-bounded-semantic-source-staging-20261030`
- Run date: `2026-10-30` (Asia/Bangkok local execution)
- Status: `PASS_ENGINEERING_OFFLINE_BOUNDED_LOCAL_STAGING`
- Base revision: `e44b6584cab96bc9936c9ae39cad224dc61c900f`
- Implementation commit: `6e6eb0deb0a51ee9883165f124992c7e7d57cf38`

## Purpose

Add the next executable boundary after M23/M24: stage an already-authorized
local semantic-judgment source while preserving the exact source hash, byte and
file ceilings, raw/normalized relative paths, per-file hashes, and resumable
checkpoints. The helper is deliberately local-only and does not discover
rights, fetch URLs, transfer data to providers, create labels, or publish raw
source material.

## Changes

- Added `source_acquisition.py` with fail-closed authorization binding, exact
  snapshot inventory hashing, bound checks, overlap rejection, atomic per-file
  staging, prefix-checked `.partial` resume, and machine-readable receipts.
- Added `acquire_semantic_source.py` for the local CLI path.
- Added focused unit, negative-path, resume, and CLI smoke coverage.
- Added the operator runbook at
  `docs/healthtech/research/SEMANTIC_SOURCE_ACQUISITION.md`.

## Verification

- Focused authorization, acquisition, judgment, submission, and G6 tests:
  `25 passed`.
- Targeted compilation: exit `0`.
- `git diff --check`: exit `0`.
- Scoped secret/privacy scan: no credential or private-path hits; the only
  matching phrase is the synthetic fixture rights clause.
- Synthetic local smoke: two authored files, 12 bytes, complete staging,
  verified-file reuse, interrupted `.partial` resume, and CLI execution all
  passed in temporary storage.

## Boundaries

- Real source acquisition: `0`.
- Real semantic labels created: `0`.
- Provider/network calls: `0`.
- Paid cost: `USD 0.00`.
- The source hash used by this helper is the canonical file-inventory hash
  `ht-semantic-source-snapshot-v1`; an owner-authorized manifest must pin that
  exact hash before a real snapshot is staged.
- The helper does not authorize a source. M23 remains the authorization gate;
  M24 remains the judgment-ingest gate.

## Next action

Obtain an owner-authorized, semantically aligned, rights-cleared source whose
exact local snapshot can pass M23 and this M25 staging receipt. Then invoke M24
with the same authorization manifest, inspect the real validation report, and
only after that rerun HT-B0a/B0b/B1/B2/B3 without changing the frozen
denominator, untouched holdout, or unjudged-pair policy.
