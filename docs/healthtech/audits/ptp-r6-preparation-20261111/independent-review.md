# Independent read-only review of the R6 preparation

All reviewers were explicitly authorized by the owner. Parent remained the sole
writer. These are agent engineering/scientific-design reviews, not independent
domain-expert fidelity judgments, and consume no owner fidelity cards.

| Reviewer | Focus and evidence | Final disposition |
|---|---|---|
| r6_evaluator_review | Code-review guidance; reproduced schema-mutation bypass, invalid Unicode, empty evidence pointers, cross-artifact grammar allowance and calibration shortcut | Reference-contract fixes independently verified,28 tests PASS; real tokenizer/model/runtime still NOT_RUN |
| r6_research_review | ML-evaluation and experiment-loop guidance; reproduced equality/blanket shortcut, audited Graph estimand/alias semantics and required source+candidate evidence | Revised24-case fixture semantics/grader accepted for freezing;12 calibration tests PASS; no native-fidelity or GPU approval |
| r6_runtime_review | Test-engineering guidance; inspected R5/native/Graph/component/evaluator paths and ran51 existing component tests | R6 end-to-end execution NOT_READY; concrete blockers incorporated in mandatory Phase0 |

Reference critic reviewed SHA256:
`cf7ee86befcfe46cda30b9743e7922fb421b513c6a8c4bebe5e8295fc257d1bd`.
Calibration reviewed SHA256:
`119a677c9fd4bf95c8723190aed7140cf0dfa1a704c47b55abc8a3ddaff5ed5a`.
Task-criteria reviewed SHA256:
`3fa013a5c275d4c2d9d09e8dfd19f9854072a740586a0180c31256ed122037f6`.
Calibration tests reviewed SHA256:
`288d0078e8946a03543f65d88de5c791556a56a752ba1d5b818a6178511e8020`.
These match the final candidate freeze. No model output existed when these
fixtures were revised; rejected draft acceptance logic was never used for a run.

## Why another immediate model run is not justified

The R5 synthetic worker would reuse an exclusive grammar filename for a second
guarded stage. The native runner is profile-only with obsolete72h/8h assumptions.
The source join caps100 IDs; Graph screening requires200 units. R6 requires282
context families and114 screened units with100 coverage outcomes. Full component
embedding can require77 rows/query, not four. A native S/G scorer is absent.
All are integration work, not a reason to spend another model call diagnosing
packaging. Phase0 must reproduce the complete staged interfaces using authored
fixtures before GPU admission, including exact prompt-token limits and no-replay.

Final runtime proposal review confirmed the179h/49h arithmetic and77-row bound.
Two specification ambiguities were corrected: profile/view admission precedes
generic generation, while the complete critic request is checked after generic
and before critic; query text maps verbatim into R2 abstract with empty title/claims,
and all positive-key matches enter structured ranking without pre-fusion truncation.
The reviewer endorsed this as a conditional proposal, never as runtime admission.

Final SACR review independently passed29 evidence tests. Full-source evidence is
now constrained in the grammar as well as the prompt and independent compiler;
the reviewed candidate SHA256 is
`8e7f8577d9502d87d5fd5230a6ee3c270a26e720b4430fcb3c2c9a913d2c5b4a`.
A boundary probe admitted16 sentences and rejected17 in schema/prompt construction.
This inherited limit must be reported as pre-model technical admission failure,
not a semantic defect; real-tokenizer qualification remains NOT_RUN.

## Remaining limitations

Evidence-ID integrity cannot prove semantic entailment. Text-reference compression
is lossless in tests but model comprehension is unmeasured. Calibration uses
authored exposed cases and permissive allowed flags only where dimensions overlap;
it is not a native-accuracy estimate. The partial-Graph claim changes the estimand
prospectively and requires approval; R5 remains failed under its old full-source
gate. Source and alias units are dependent and must not be pooled as independent
samples for an unqualified accuracy interval. Human critical-error/sentinel gates
remain mandatory, with no acceptance inferred from absence of an answer.

Tooling note: one initial reviewer import command failed before tests because
`src` was absent from the import path; corrected invocation succeeded. A parent
PowerShell hash command was unavailable; hashes were produced using Python
`hashlib`. Neither incident involved a model or data job.
