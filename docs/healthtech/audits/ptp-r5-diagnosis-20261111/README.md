# R5 SACR diagnosis and independent Graph preparation

Final status: CPU_ENGINEERING_READY_FOR_OWNER_LONG_RUN_DECISION. Local86 tests
PASS; final real tokenizer/callback/EOS35/35 PASS, original smoke-source1/1 PASS.
All six owned CPU containers are terminal with PID0; whole observed container
wall time1117.113758234s, plus character probe2.063s. New model/GPU/fidelity
generation costs are zero. See `summary.json`, `terminal-observation.json`,
`smoke-proposal.json` and `freeze.json`. No model dispatch is authorized yet.

Current owner scope: diagnose and fix SACR, complete CPU grammar qualification,
advance independent Graph preparation, propose a bounded long goal and batch
missing permissions. Parent is sole repository writer; grammar/code reviewer
was read-only. No model generation, corpus extraction/census, retrieval, cards,
database write or publication in this diagnosis package.

## Findings and interventions

1. **Confirmed decoder/schema mismatch.** Pinned LMFE0.11.3 integer parsing does
   not enforce minimum/maximum. The retained source SHA for jsonschemaparser.py
   is6bc4a8a10621c6d38d70ebb5ae1dc21aaa98c0454a2e80be1896586f10dccf94.
   R4 uses these bounds for roles and condition references. Its previous CPU gate
   used empty roles/conditions. R5 replaces every finite bounded integer range
   with a numeric enum; it does not relax the independent schema/compiler.
2. **Confirmed token-path qualification gap.** The actual tokenizer/callback
   rejects three valid reversed-property proposals that the character parser
   accepts. Targeted ASCII/Unicode/escaped variants all fail at token10465; null
   abstraction passes. The freetext cache omits tokens that close a string and
   continue syntax internally, while original extra traversal covers only
   backslash-root tokens. New adapter adds a reduced boundary trie traversed
   with the exact parser. It does not force property order or admit tokens
   unconditionally. The final tokenizer receipt records token10465's decoding.
3. **Resource failure preserved.** Broad boundary trie v1 (3250 tokens) and
   cache-omission-only v2 (2497 tokens) are too expensive for this gate; both
   were deliberately stopped, with terminal PID0/exit137 and no OOM. Partial
   positive cases are not a completed pass. v3 retains725 potential boundary
   tokens after excluding only lexically impossible prefixes; partial escapes
   and partial Unicode escapes remain admissible for exact parser checking.
4. **Historical R4 cause remains UNKNOWN.** These fixture bugs do not recover
   missing R4 generated text, detailed exception or tokens. Do not relabel the
   original InputBoundaryError as a proven semantic rejection or zero-call event.

## Evidence and limits

- `character-probe/`:33 authored cases per schema plus7 numeric enum cases.
  R4 has8 false admissions; R5 matches all expectations. Pinned character-only
  namespace bootstrap, not full package initialization or token qualification.
- `token-result/`: first real tokenizer matrix,30/33 expectations matched;
  three false rejections. Terminal CPU179.716016793s, peak1158594560bytes.
- `token-diagnosis/`: five discriminating variants; four string cases reject,
  null case passes. This is a diagnosis result, not a passing admission gate.
- `boundary-preflight/`, `boundary-preflight-v2/`: preserved stopped performance
  candidates, terminal receipts and partial cases. No automatic model retries.
- `boundary-preflight-v3/`: final35/35 PASS,276.912s whole, peak1204183040bytes.
- `exact-source-preflight/`: populated reversed-field authored fixture using the
  original synthetic smoke source:1/1 PASS,50.434s whole,1557 input tokens,
  before any proposed model dispatch. Token10465 is confirmed as `.\",`.

Grammar qualification covers the declared fixture matrix, not every possible
JSON tokenization or native source. Reversed/zero-width spans and duplicate
block IDs remain compiler-only rejection checks. Semantic role/condition
attachment, completeness, abstraction fidelity and retrieval remain separate
gates. Native source admission and runtime resource limits remain mandatory.

## Diagnostic evidence for future attempts

The new optional private diagnostics keep durable dispatch/return markers, the
first failure location/message, last schema-rejection path and at most4096
generated suffix token IDs. Each stage is capped at256KiB. Prompt token IDs are
excluded. The callback retains a bounded view and copies tokens to CPU only on
failure, avoiding scalar synchronization at each generation step. Diagnostic
storage faults preserve the original exception. Tests inject failed writes.

Observed backend invocation counts are distinct from completed inference and
token counts. The old ledger's unknown attempts stay unknown. No rewriting or
repair of old results. Diagnostic files stay private and are excluded from
public evidence; only reviewed aggregates may be published if authorized.

## Graph work completed

Both frozen sample hashes match the R4 materialization receipts. Checked spans
against retained units, alias normalization/hashes, relation identities, source
field/hash shape, witness-family/key bindings, fixed sampling hashes/order and
same-ID conflicting record bodies. `graph-integrity-v2.json` is the current
integrity result; the earlier narrower result is retained.

There are100 source families,29 records from14 families,86 empty families,
100 alias-pair units and215 unique records across samples. No source recall,
semantic fidelity, compatibility or accepted graph edges follows from integrity.
Full source evidence for empty families is not present in these artifacts.
The prospective fixed-source attachment module and fixtures are prepared but
NOT_RUN on corpus; the combined proposal asks for one bounded source-only join.

## Next gate and authority

See `../../research/plans/R5-BOUNDED-LONG-RUN.md`. Proposed ceilings remain inside
the previously approved cumulative192GPU/64fidelity/128full-dev hours, with
existing charges retained and60 human cards total. New model/native/evaluator
work awaits one combined owner decision. Earlier screened-publication approval
is retained, not requested again; exact staged-tree screening is still required.
Offline fixes
do not imply permission to retry native generations or reset a ledger.

HANDOFF.md, CLAUDE.md and INDEX-PLAN.md carry matching current checkpoints.
Checkout main, verified base ac48e02aef848143edd6c5b58623b8ee9ec42e33; local
changes uncommitted/unpushed. The unrelated owner handoff document is untouched.
