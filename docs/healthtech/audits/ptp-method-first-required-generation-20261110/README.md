# Execution v3 requires generation evidence

Prospective engineering contract; not experiment authorization, a production
preflight certificate, or adoption of generated-family rejection.

`sacr-dev-execution-v3` retains the exact v2 fields and mandatory predeclared
original-anchor bundle. Its version additionally requires profile-stage v2 and
view-stage v3 evidence for every completed generation stage. A missing anchor
binding fails before the run directory is reserved. Existing v1/v2 declarations
and historical outputs retain their previous semantics.

Controller legacy profile/view entry points are refused before callback dispatch
or reservation for v3; bindings are checked before that choice, so changing the
in-memory version cannot downgrade the requirement. Replay also requires the typed
versions. The journal checks actual original-record replay, source/identity,
alignment/screening and costs before sealing completion and again at finalization.
Calling the low-level journal with legacy output cannot bypass the v3 contract.

Missing source still skips generation through the generated-profile entry point.
Failed/interrupted infrastructure is not forced to invent a completed-generation
artifact. Valid empty/failed profile and malformed generation retain existing
failure distinctions and can only finalize fallback using the separately bound
original anchor. Failed view generation remains a stop pending policy adoption.

Validation: 10 new cases pass, covering pre-reservation missing-anchor rejection,
three legacy dispatch refusals, low-level legacy-output refusal, execution downgrade,
all six authored stages, and empty/failed/malformed profile fallback. Full related
suite: 417 tests pass. Ruff passes six changed Python files. All successful run
evidence is authored with fake generation records/encoder and a tiny CPU index.

The version does not authenticate model loading, exact prompt construction, source
isolation, eligibility policy, original baseline lineage, native parity, GPU identity,
live resource caps, semantic fidelity or permission to score protected test. Identity
receipts remain checked assertions. R1 actual checks remain NOT_RUN; curator/environment
unanswered. Generation/fidelity failures persist; R3/R4 absent, R5 not authorized,
R6 incomplete. No actual data/model/GPU/remote work or retry occurred.

Next: deterministic family-rejection integration with preserved failure counts and
a pre-run methods declaration; actual curator/R1 and anchor/identity attestations;
resource/generation/fidelity acceptance before a bounded pilot. Goal ACTIVE.
