# Generation evidence in view controller and replay

Scope: offline engineering integration; no model/data/GPU activity, no adoption of
generated-family rejection. Previous turn was verified implementation progress.

`BoundProfileController.generated_views` accepts original private generation-record
bytes, an identity receipt and costs. Before stage completion it checks query,
source hash, run, planned attempt, arm, generator manifest and prompt manifest
against the bound execution. It binds the record's exact bytes and counts, requires
EOS_COMPLETE, then performs existing strict JSON parsing and view screening. The
generic adapter still receives query/source only; selective also gets a detached
profile. Reservation precedes dispatch; attempts cannot be repeated.

New private `sacr-view-stage-v3` outputs retain original generation artifact text,
binding and identity alongside v2 screening evidence. No historical output is
rewritten. Before embedding, replay revalidates the generation evidence and screening
against current bound dependencies and the sealed cost event. The new journal cost
reader checks event bytes, slot identity and terminal status. Both a modified event
file and a validly sealed but inconsistent cost event stop replay.

Legacy v2 raw-response adapter remains available for existing fixtures. It is not
silently upgraded to generation-attested evidence. A production runner must require
the new contract and actual identity/preflight verification. The identity receipt
is a checked adapter assertion, not proof it actually used the model, exact prompt,
or source. Actual manifests/loading/prompt construction still need attestation.

Non-EOS, malformed responses, mismatching costs/identities and infrastructure
exceptions remain failed stages; there is no invented empty successful view or
retry. The adapter must preserve its private original attempt before returning,
including records rejected before controller completion. Failed callback costs
remain unknown in the journal; importing their observed costs safely is still
required before family-rejection policy integration. Profile generation binding
and a declared production requirement for evidence-bearing views remain open.

Validation: 19 new controller/replay tests passed. They cover both arms, exact
artifact retention, all eight identity fields, repeat refusal, non-EOS/malformed/
cost/infrastructure failures, and sealed-cost inconsistency or mutation. Existing
17 view/embedding-input regressions also passed. Ruff passed four changed Python
files. Full related suite: 382 tests passed.

R1 actual isolation/A03/baseline/native parity NOT_RUN; curator/environment still
unanswered. Prior failed model and grammar attempts unchanged; no automatic retry.
Generation/fidelity and live resource gates remain open; R3/R4 absent, R5 not
authorized, R6 incomplete. Engineering acceptance is not research success.

Next: preserve rejected generation records/observed costs inside reserved failure
evidence; bind profile generation and require typed evidence in a new execution
version; then resolve deterministic family rejection with a pre-run methods entry.
Curator/R1, actual identity/anchor provenance and memory/live caps remain independent
prerequisites to an actual pilot.
