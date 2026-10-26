# G10 bounded offline comparison handoff

Status: **READY_FOR_PEPO_AUDIT**
Source revision: `612483f` (`main`) plus uncommitted working-tree artifacts; no commit, push, deploy, provider call, or paid compute
Date: 27 October 2026

## Scope

This package adds one additive offline comparison slice over the public PTP-0001 packet and two public revision states after the initial state:

- `S0 → S1`: declared silicon-substrate policy change.
- `S1 → S2`: display-name-only no-op revision.

The slice compares rules-only, full regeneration, direct revision, deterministic invalidation plus the same generator, and the existing public-input workflow wrapper. It measures mechanics, before/after diffs, preservation, deterministic validators, call accounting, and retained failure traces. It does not measure model quality, semantic validity, scientific utility, clinical validity, legal status, patentability, or FTO.

## PASS / FAIL / BLOCKED / NOT_RUN

- **PASS:** public staging, same-input/schema/validator contract, B0 rules-only, B1 full regeneration, B2 direct revision, B3 deterministic invalidation plus same generator, existing workflow wrapper, no-op preservation, affected-field preservation, validator checks, mock call accounting, and report generation.
- **FAIL:** none in the normal comparison run. A controlled timeout probe is covered by `tests/test_g10_offline_comparison.py` and is retained as a failure trace without retry.
- **BLOCKED:** none for this bounded offline package.
- **NOT_RUN:** B4-RG adaptive-search plus regeneration, B4-DR adaptive-search plus direct revision, scientific/held-out pilot, provider/model quality comparison, full G10 completion, and all paid/network execution.

## Implementation

- `src/patent_to_pilot/evaluation/comparison.py` stages only the public packet/schema, enforces evaluator-only field rejection, runs the five comparison wrappers, records mock calls/failures, and writes evidence outputs.
- `scripts/run_g10_offline_comparison.py` is the reproducible offline entry point.
- `tests/test_g10_offline_comparison.py` covers normal execution, no-op preservation, affected-field limits, same-input hashes, controlled timeout traces, and fail-closed packet/schema guards.

## Evidence

Command:

```text
rtk proxy python -B scripts/run_g10_offline_comparison.py
```

Observed result: `status=PASS`; states `S0,S1,S2`; five methods; nine mock provider calls; mock cost USD `0.0000000`; network calls `0`; retries `0`.

Outputs:

- `results/development/g10-offline-comparison/comparison.json`
- `results/development/g10-offline-comparison/comparison.md`
- `results/development/g10-offline-comparison/comparison.html`
- `results/development/g10-offline-comparison/before-after-diff.json`
- `results/development/g10-offline-comparison/validator-results.json`
- `results/development/g10-offline-comparison/method-traces.json`
- `results/development/g10-offline-comparison/evidence-manifest.json`

Focused checks:

```text
rtk proxy python -B -m pytest -p no:cacheprovider tests/test_g10_offline_comparison.py
exit code 0; 6 passed

rtk proxy python -B -m compileall -q src/patent_to_pilot scripts/run_g10_offline_comparison.py
exit code 0
```

## B4-RG boundary

B4-RG is marked **READY_FOR_FUTURE / NOT_RUN**. The current public case has no verified distractor and recoverable-evidence pool outside the initial active packet, so running adaptive search here would not satisfy the protocol’s same-pool comparison requirement. This package therefore does not claim full G10 completion.

## Next action

Pepo should audit this bounded candidate once against the generated evidence and changed-file diff. Any provider-backed or broader adaptive-search run requires a new explicit scope and a frozen protocol extension.
