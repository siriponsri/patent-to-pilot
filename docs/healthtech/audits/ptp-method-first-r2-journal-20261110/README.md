# Durable injected-stage journal and offline integration
DevStageJournal validates an expected dev plan before creating an exclusive run
directory. Every stage gets an exclusive hashed-ID directory and a flushed/fsynced
reservation before callback invocation. Private output, terminal receipt, measured
operation-wall time/cost event and a final stage seal are written exclusively.
A run-level completion record binds outcomes/reconciliation hashes. Existing runs
or stage reservations cannot be reused or overwritten.

Exceptions preserve FAILED/INTERRUPTED receipts with exception type only, unknown
costs and measured operation duration; no exception-message text is copied into the
journal. A hard crash or partial write leaves no final seal and cannot be classified
as terminal by this reader. Finalization checks actual reservation/receipt/event/
output bytes against seals before record reconciliation. It does not infer a stopped
process from a stale file. No retry, automatic resume, process killing or recovery
is implemented.

Validation:36 focused tests (9 journal,12 reconciler,15 outcome); all181 tests across
15 SACR test files then passed. A subsequent fixture-only query-ID alignment was
checked with all9 journal tests passing. Ruff passed for three changed Python files.
The six-stage integration uses an authored profile/views and injected vectors,
then actual component compilation/binding, NumPy acquisition and factorial kernels.
Its deliberately repeated acquisition is counted (24 index dot products,9 component
dot products);0 model calls. These are fixture operation counts, not a pilot budget.
Tampered output/event/receipt, unsealed attempts, duplicate execution, test plans,
runtime exception and keyboard interruption are tested.

Limits: this is a stage execution journal, not an end-to-end production SACR runner.
The trusted caller still controls dependency order, profile/view validation, callback
query/source identity, real encoder/index preflight, cooperative GPU ownership,
model-specific budgets, process supervision and data isolation. Arbitrary injected
callbacks are not sandboxed. File fsync does not prove atomic directory durability
under every power-loss/filesystem scenario, and seals are consistency checks rather
than protection from a writer replacing all records. Recorded caller metrics need
actual instrumentation; zero fixture metrics are not measurements of real work.

No benchmark data/model/GPU run occurred. Real generation compatibility and resource
gate remain failed/unresolved; actual curator/isolation/A03/parity and fidelity
observations remain absent. Do not add an automatic further generation attempt.
Next meaningful independent work: inspect closest prior art against the actual
implemented method and document the novelty boundary. Before any actual run, bind
real source/model/index/cap manifests and complete controller integration; the current
37-item readiness audit remains INCOMPLETE, not ready R3 or R5.
