# Controller integration inspection and early-plan repair

Checkpoint: 2026-11-10 09:23:10 Bangkok. Inspected base: e45de84883f7ad5f12d8c5628c45c93ec20ee8a0. This package is engineering progress,
not a new experiment, successful generation, or completed R1/R3 gate.

## Reproduced defect and repair

DevStageJournal calls validate_plan before creating its directory, but that
validator previously accepted empty cohorts, duplicate IDs, and a string in place
of a query-ID list. Some malformed slots raised raw TypeError rather than the
sanitized boundary exception. Cohort checking later in reconciliation was too late:
a malformed declared cohort could already have reserved/executed callbacks.

Added nonempty list, per-ID, uniqueness and slot-container/type checks before
reservation. Twelve authored regression cases produced 6 failures and 6 passes
before repair. After repair, journal/reconciliation/outcomes tests:48 PASS; changed
Python Ruff check PASS. No callbacks, data or GPU work were run outside fixtures.
A mistyped initial test-file lookup used tests/research; actual tests are under tests/.

## Remaining integration boundaries

| Boundary | Current evidence | Required next evidence |
|---|---|---|
| Cohort/slot declaration | validate_plan now rejects malformed cohort before output allocation; exact six stages enforced | Trusted ordered cohort must be bound to curator query/metadata manifests; a self-supplied hash is insufficient |
| Input/index identity | mtm_preflight checks projected corpus, vectors, model/encoder source and trusted projection receipt; run_mtm_dev_bound checks query/metadata pins before dynamic runner import | Actual curator isolation and pinned real receipts, A03 counts and baseline parity. Existing baseline entry point is not a SACR controller |
| Component provenance | compile_components binds source/profile and text rows; bind_component_vectors checks supplied encoder/row/vector receipts | Trusted encoding adapter must produce those receipts from actual declared text/encoder; injected vectors do not establish execution |
| Acquisition/selection | compare_factorial checks same anchor, ordered passages and shared eligible mask; CPU acquire_union caps depth/views | Connect immutable preflight identity to exactly the arrays passed to both kernels; prove actual encoder/index parity and resource behavior |
| Dependencies/acceptance | Journal records callbacks and seals output; reconciliation checks some terminal state consistency | Controller must inspect typed generation/validation outcomes before scheduling dependent stages. A COMPLETED callback is not a usable profile/view or approved semantic fidelity |
| Resources/authorization | generate_once enforces per-call token/byte caps; journal reserves slots and reports actual/unknown costs | Model loader identity, GPU UUID/live-job guard, authorization clock, whole-run call/token/time/memory envelope, process stop accounting. Journal does not enforce these |

Do not add boolean readiness claims to substitute for missing bindings. Do not launch
SACR through the baseline runner or generic journal. No complete production SACR
entry point was established by this inspection. Remaining controller work must preserve
profile fallback, per-view rejection and unresolved-review distinctions; cannot silently
replace the intended method with successful anchor-only runs.

## Next bounded action

Specify one immutable execution manifest joining the existing ordered cohort, allowed
source, prompt/model/encoder/index identities and declared resource limits. Validate
its relationship to the six-stage plan before allocating a journal. Implement only
with authored inputs until curator and generation gates are resolved. Manifest agreement
will still not establish authorization, isolation, semantic fidelity or actual encoding.
This is continuation of the intended method, not approval of another model attempt.
