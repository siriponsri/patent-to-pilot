# Exact R7 calibration pipeline qualification

PASS_AUTHORED_FULL_CALIBRATION_PIPELINE. Docker terminated with exit0, PID0 and no
OOM. Whole wall100.230837159 seconds; charged worker+controller CPU99.222875606
seconds; worker peak RSS1,138,241,536 bytes. Aggregate limit2GiB, aggregate peak
not measured. CPU2 threads, no network, model directory read-only.

The actual R7 worker executed24 authored calibration responses through the exact
compact messages, original schema, tokenizer, grammar/EOS, generation adapter,
durable reservations/raw records and unchanged calibration grading. All-supported
authored answers correctly failed14 required negative/uncertain verdicts. This
is an expected software fixture outcome, not a model outcome. 3,649 grammar tokens
were checked. Six additional scenarios used the unchanged R6 bundle runner,
including invalid envelopes, unknown backend, budget/deadline denial and missing
prompt. Those scenarios do not qualify R7 synthetic compact integration.

Total authored backend invocations31; actual model calls0 and GPU seconds0.
Hardware/model loading, GPU lock, telemetry and dispatch authority were explicit
doubles. The entire remote output tree is marked SIMULATED. Never import its
dummy model/GPU metrics into the research ledger. Only the measured outer CPU
was charged, releasing the1200-second CPU reservation.

`pipeline-fixture-summary.json` and `terminal-observation.json` preserve evidence.
`pipeline-fixture-declaration.json` binds the exact source package. Scoped helper
copies are in `tools/`; do not rerun completed staging/start/settlement commands.
