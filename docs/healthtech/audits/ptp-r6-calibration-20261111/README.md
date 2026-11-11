# R6 actual evaluator calibration: failed candidate retained

Status: FAILED_CALIBRATION / CANDIDATE_CLOSED. The container exited0, PID0,
without OOM. All24 calls returned EOS; model/runtime completion is distinct from
evaluator correctness. The exact frozen24 raw answers were rechecked against the
pinned source package and assessor, with matching task/message/reservation,
generation/cost and backend dispatch/return records. No output was repaired.

## Findings

- All24 responses satisfy the JSON schema, but23 violate the stricter interpreter
  contract by including findings for supported dimensions. The prompt required
  findings for unsupported/uncertain dimensions but did not explicitly prohibit
  supported-dimension findings. This is a generation-instruction/validator gap.
- Four responses also omit findings for flagged dimensions; two contain findings
  without any reference. These overlap the23 rejected responses. A wording
  clarification does not prove that all rejection causes are repaired.
- One response satisfies the interpreter contract but flags all seven dimensions
  on an SG_RECORD negative case allowing only polarity/context/roles flags.
  The frozen assessor correctly records an unrelated-dimension failure.
- The valid semantic calibration failure closes this evaluator candidate under
  the approved R6 stopping rule. The unused second revision is not automatic
  permission to reroll semantic qualification. Native SACR/Graph fidelity is
  NOT_ASSESSED; synthetic/native/pilot/full retrieval are NOT_RUN for this critic.
  These results do not establish that the native research methods fail.

## Cost and scope

Whole supervisor occupancy1748.397555 seconds, conservatively charged1749 seconds
to both GPU and fidelity within the shared budget. The per-operation sum1691.077153
seconds is descriptive and is not added again.24 calls,33,988 input and15,799 output
tokens; peak allocated GPU memory17,713,604,608 bytes. This is an allocated-GPU
peak, not aggregate host RAM. Controller CPU9.590293 seconds is GPU-stage overhead.

Global journal reconciled once to generation1 and no active dispatch. Cumulative
known calls108 remain a lower bound because historical unknown attempts persist.
GPU remaining677141.386495 seconds; fidelity remaining216620.273320 seconds at
this reconciliation. Prior pending200 conservative local CPU seconds were charged
once. Subsequent CPU-only Graph work is recorded in the cumulative ledger and
must not be lost when preparing any future journal-backed GPU declaration.

## Evidence

- [Terminal and full costs](terminal-observation.json)
- [Pinned raw24 verification](terminal-verification.json)
- [Layered contract diagnosis](calibration-diagnosis.json)
- [Accounting terminal classification](accounting-terminal.json)
- [Global journal reconciliation](reconciliation.json)
- [Ledger snapshot](reconciled-ledger.json) and [scope snapshot](reconciled-scope.json)

Prospective compact Graph v2 clarifies the existing finding rule without changing
gold/schema/semantic criteria. Its CPU admission is a separate engineering result,
not retrospective qualification of R6. Any new model candidate needs its own
approved declaration and must retain this failure and exposed-calibration history.
