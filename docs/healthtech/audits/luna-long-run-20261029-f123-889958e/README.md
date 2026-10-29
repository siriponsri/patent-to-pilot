# HT-W26 Long-Run Audit

Run ID: `luna-long-run-20261029-f123-889958e`
Status: `PASS_ENGINEERING`
Scope: F1/F2/F3 backend repairs plus an offline Abbott development run
Candidate: `889958e+f123-working-tree`
Base and `origin/main`: `889958eeb3174a09df9ef3840231a0f0577f00f2`

## Outcome

This package records the completed local engineering work for HT-W26. The implementation adds purpose-aware external projections, versioned frozen-cohort integrity checks, and typed-rights provenance resolution. A fresh offline run over the derived Abbott public-device cohort completed for all three devices and all five available methods with zero provider calls and zero paid cost.

The work remains development-only. It does not establish exhaustive patent recall, semantic relevance, claim validity, FTO, clinical suitability, approval probability, investment merit, publication readiness, or generalization beyond the frozen slice.

## Canonical records

- `REPORT.md` - human-readable scope, evidence, results, and limitations.
- `verification.json` - machine-readable acceptance summary and hashes.
- `NEXT_ACTIONS.md` - continuation boundaries and the next authorized action.
- `abbott-provenance-verification.json` - typed-rights and disclosure coverage receipt.
- `reproduction/frozen_integrity_probe.py` - sanitized mutation-rejection reproduction.
- `results/healthtech/ht-abbott-integrity-probe-20261029-frozen-r1/summary.json` - probe output.

## Main evidence

- Frozen cohort: `results/healthtech/ht-public-cohort-20261029-frozen-r1/manifest.json`
- Fresh dossiers: `results/healthtech/ht-abbott-dossiers-20261029-frozen-r1/`
- Offline frontier: `results/healthtech/ht-real-baselines-20261029-frozen-r1/frontier_diagnostics.json`
- Run receipt: `results/healthtech/ht-real-baselines-20261029-frozen-r1/receipt.json`

## Verification summary

- Focused HealthTech repairs: 28 passed.
- Non-budget suite: 298 passed.
- Full suite with `PYTHONPATH=src`: 303 passed with one existing `fitz` deprecation warning.
- Compile check: passed.
- Diff whitespace check: passed.
- Frozen-integrity probe: valid copy accepted; runtime, raw-file, registry, and malformed-metadata mutations rejected.
- Provider calls: 0.
- Paid cost: `$0`.

The default full-suite invocation without an explicit `PYTHONPATH` has a local setup failure in the two subprocess tests because the package is not installed and pytest's `pythonpath` setting is process-local. The same five tests pass when `PYTHONPATH=src` is propagated to child processes. This is recorded as a setup distinction, not as a budget-policy failure.

## Handoff

The next action is a reviewed M4 readiness decision or acquisition of a rights-cleared independent cohort. Keep the Abbott branch development-only. Do not start live OpenRouter work, Claude UI integration, deployment, outreach, clinical/FTO analysis, or public redistribution from this record alone.
