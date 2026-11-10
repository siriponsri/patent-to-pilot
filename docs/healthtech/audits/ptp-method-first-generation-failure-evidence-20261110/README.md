# Preserve rejected generation evidence and observed costs

Offline engineering change; no actual model, labels, GPU or remote jobs. Previous
turn made verified controller/replay progress. Research acceptance is unchanged.

After generation identity, raw record, token agreement and complete cost-schema
validation, non-EOS return or failed view acceptance raises a typed private
`GenerationEvidenceFailure`. The journal seals a `sacr-generation-failure-v1`
output with original artifact bytes, identity, generation binding and categorical
reason. The stage remains FAILED and the exception propagates. No empty successful
view, fallback ranking, retry, or generated-family rejection policy is introduced.

The journal preserves validated reported costs, overwriting only operation wall
time with its own measured duration. Unknown metrics remain null. Identity/hash/
count/invalid-cost failures and infrastructure exceptions do not become trusted
generation evidence: their costs remain unknown except measured operation time.
Keyboard interruption remains INTERRUPTED. Costs are adapter-reported consistency
evidence, not independent provider billing or model-execution attestation.

The private output is fsynced and hashed before the terminal seal. If its write
fails, the reservation remains unsealed; inspection is required, and reservation
reuse still fails. Readers verify failed output bytes; completed-output readers
refuse FAILED even when it has an output. Reconciliation already includes failed
events; downstream view failure still blocks the cohort pending a declared policy.

Validation: 391 related tests passed; Ruff passed four changed Python files.
Nine new regression cases cover both arms with malformed/non-EOS returns, retained
counts and GPU time, unknown peak memory, byte mutation, no retry, invalid identity/
cost, infrastructure interruption and failure-evidence disk error. The previous
19 controller tests were updated only where verified failure now retains output.

Remaining: bind profile generation and require typed evidence prospectively in a
new execution declaration; define/declare family rejection and propagate counts
without erasing failures. Existing actual model/grammar failures stay unchanged.
Actual R1 isolation/A03/baseline/native parity NOT_RUN; curator/environment still
unanswered. Actual identity, anchor lineage, full-index resources and fidelity are
unverified. R3/R4 absent, R5 not authorized, R6 incomplete. No pilot is authorized
by these engineering checks and no positive SACR result is claimed.
