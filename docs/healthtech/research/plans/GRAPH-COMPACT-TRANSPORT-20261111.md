# Graph recovery: prospective compact transport

Current status: compact v2 actual token admission passed its risk cap, with100
admitted parents and14 technical risks among fixed114. Model screening NOT_RUN.
See [actual evidence](../../audits/ptp-sg-compact-v2-preparation-20261111/summary.json)
and [proposed next candidate](R7-SINGLE-CANDIDATE-CONTINUATION.md). The original v1
preparation below predates the calibration contract diagnosis and was not run.
Owner requested Graph repair while the original R6 critic calibration was active.
The parent remains the sole repository writer. Historical Graph R6 remains
CLOSED_INPUT_RISK_CAP_33_OF_114_NO_MODEL. This document does not reopen that run.

## Supported diagnosis

The existing Graph request combines complete family source, serialized retained
records, evidence catalogue offsets and the output schema. The measured R6
preflight found 32 input-token limits and one catalogue limit across 114 parents.
This is a technical input-admission failure, not observed semantic or retrieval
failure. Neither installing Neo4j nor changing storage resolves this boundary.

## Implemented candidate

`sg_compact_transport.py` adds a separate versioned wire representation. It keeps
every source/artifact character, catalogue occurrence ID, schema, criterion,
scope and original binding. Ordered [ID, text] entries omit redundant offsets
from the model request; repeated exact text uses backward references. Original
offsets remain in the bound receipt and interpretation. Reconstruction checks
the complete wire and original receipt, rejecting mutations. No frozen R6
worker, prompt, configuration or live package was changed.

The candidate retains 8192 input tokens, 256 catalogue units, fixed114 parents,
100 source coverage rows, 86 abstentions and the risk cap20. No resampling,
truncation, source summarization, corpus extraction or Neo4j writes occur.
The preflight counts all parents; passing it grants no semantic acceptance or
dispatch authority. The known catalogue-limit parent is not silently repaired.

## Verification and remaining work

12 authored local tests PASS via `python -m pytest tests/test_sg_compact_transport.py -q`.
Coverage includes Unicode/whitespace, empty artifacts, cross-artifact references,
source offsets, artifact membership, tampering, unchanged catalogue cap, input
token boundary, risk20/21 and token-counter mutation. Counts in these fixtures
are authored doubles, not measurements with the production tokenizer.
Independent evaluator review found no blocking transport defect in the first
seven tests; its requested additional fixtures are included in the final12.
Conservatively allocate100 CPU seconds for local repair/tests/review overhead
at the next ledger reconciliation; actual CPU was not separately metered here.
Do not reset the active dispatch journal or modify its frozen ledger snapshot.

Next steps, in order:

1. Freeze candidate code/tests and prepare a CPU-only declaration using the
   existing private Graph inputs and pinned tokenizer, at most600 seconds,
   CPU2/aggregate2GiB and no new model calls. Reconcile outstanding resources
   before execution; keep the same114 parents and save exact request hashes.
2. Measure all114 requests. A character reduction is not proof of token savings.
   If risks exceed20, close this transport candidate without threshold changes.
3. If admitted, freeze a concrete calibration/screening declaration within the
   remaining cumulative budget. Bind execution to compact messages SHA, version
   and package, not only the unchanged content binding. Consolidate any missing
   authorization for the new Graph configuration and model-call allocation.
4. Require qualified calibration before Graph screening, then actual human gates
   within Graph30 cards. Keep critical errors, pending judgments and risk>20 as
   failures. Retrieval stays NOT_RUN until every applicable gate passes.

The active R6 calibration remains a separate unchanged job. Its result does not
automatically qualify this altered wire representation. No extra GPU job is
started while it is active, and no extra model-call allocation is inferred from
the owner's request to repair Graph.

## Alternative rejected as an automatic fix

Splitting complete sources across calls can preserve all bytes while losing
cross-part exceptions, scope and alias comparison. All local slices saying
supported does not establish a globally supported parent. Such decomposition
requires a separately specified aggregation/uncertainty and calibration protocol;
it must not be introduced merely to make the existing gate pass.
