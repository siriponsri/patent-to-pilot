# Typed normal-return generation evidence

Engineering prerequisite, not failure-policy adoption or a new model attempt.

`bind_generation_record` binds the exact original private generation JSON bytes,
strict record fields, response hash/byte count, declared limits, and reported
model-call/input/output-token costs. INPUT_LIMIT must have zero model calls and
output tokens and an oversized prompt; normal returned statuses must agree with
token and byte caps. Unknown counts are not converted to zero. Failed,
interrupted, running and invented statuses are refused. The response JSON itself
is neither accepted, repaired nor salvaged by this binder.

`run_reserved_attempt` now writes a new private `generation-binding.json` after
persisting `generation.json`, using the actual serialized UTF-8 artifact bytes.
Original attempts are exclusive and unchanged; old directories are not upgraded.
Exceptions still preserve the existing failure record and propagate. A missing
binding after interruption is not a completed binding and does not authorize retry.

The status and token counts originate in the existing adapter, which checks output
shape, unchanged prompt prefix, token cap, terminal EOS ID and decoded byte cap.
The binding is consistency evidence, not independent proof of actual execution,
process termination, provider billing, durable fsync, live resource enforcement or
semantic fidelity. RESPONSE_BYTE_LIMIT retains the existing adapter's precedence
over EOS status; it does not establish whether an EOS token was present.

Validation: 38 focused tests passed (30 new binder cases plus 8 generation tests).
Cases cover every normal status, malformed-but-preserved response, inconsistent
limits, unknown/mismatching costs, hash/schema changes, exception preservation,
exclusive reservation and actual private artifact hash agreement. Ruff passed
all four changed Python files. Full related suite: 363 tests passed.

No actual data, labels, model, GPU, remote process or research outcome was used.
View controller still accepts bytes/metrics; its replay path must next consume
this binding and execution identity before adopting typed family rejection.
Profile generation binding into that controller is also pending. Neither a raw
record nor its self-computed hash independently authenticates model identity.
The generated-view failure policy remains PROPOSED/NOT_ADOPTED. Existing failed
model/grammar evidence remains intact. Actual R1 isolation/A03/baseline/native
parity, curator environment, generation/fidelity, resources and R3/R4 remain
open; R5 is not authorized and R6 is incomplete.
