# Bound profile-stage controller

Checkpoint 2026-11-10 09:32:49 Bangkok; inspected base d5038ed35e7627c1af0909cd32e99301ca049dd5. Authored/injected adapters only.

BoundProfileController validates permitted input snapshots before allocating a bound
journal. Its profile adapter receives the checked source and query ID, never a separately
supplied replacement source. Canonical profile copying, source validation, component
compilation and compact-view checks happen inside the reserved callback, before its
COMPLETED seal. Invalid structure produces FAILED; missing source produces SKIPPED
without adapter execution. Exceptions preserve the journal's unknown-cost accounting.

Successful callbacks carry explicit decisions: structurally prepared but fidelity pending,
review required, failed-profile fallback required, or empty-profile fallback required.
None supplies rankings, semantic approval or automatic downstream dispatch. Retry uses
the same exclusive slot and is refused. Adapters must retain their raw private model
artifacts separately; this component does not capture a failing adapter's raw generation.

Eight new controller cases. Initial focused run:1 failed/40 passed due to malformed
unknown fixture; next full run:1 failed/246 passed due to fixture reason enum. Corrected
the authored fixture to the existing schema (no production validator relaxation).
Final18 SACR test files plus MTM bound runner:247 PASS; changed Python Ruff PASS.
No actual generation or data run; fixture failures are not research outcomes.

## Remaining integration and reconciliation issue

This is only the first stage, not a production six-stage controller. A valid canonical
profile can declare extraction_status=failed while its transport/validation callback
completes successfully. Current legacy reconcile_run expects PROFILE_FAILED to have a
FAILED/INTERRUPTED profile receipt. Do not mislabel such output PROFILE_EMPTY or forge
an exception merely to satisfy that rule. A subsequent integration must bind the typed
profile decision to the terminal output when reconciling fallback, and independently
attest the original anchor ranking. This package emits FALLBACK_REQUIRED, not a finalized
fallback outcome. No finalization or retrieval is attempted from these cases.

Next bind typed profile decisions to reconciliation, then view acceptance/dependencies
and downstream adapters. Actual artifact preflight, live caps, curator isolation/A03/parity,
generation compatibility and fidelity gates remain. R3/R4 absent; R5 not authorized.
