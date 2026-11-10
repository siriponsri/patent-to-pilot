# Quote-profile generation binding through finalization

Offline engineering integration; no real model, data, GPU or remote activity.
Previous turn repaired the reproduced v3 finalization gap.

`generated_profile` reserves the declared profile attempt before its adapter.
The adapter returns original generation bytes, identity and complete costs. Query,
source, run, attempt and declared generator/prompt manifest identities are checked;
the generation record binds counts, limits and raw artifact bytes. Only explicit
quote-profile v1 responses are accepted and aligned by unique exact codepoint
matching, with no normalization, offset repair or JSON salvage.

New private profile-stage v2 output retains canonical profile/components/compact
view, original generation artifact, identity, binding and alignment receipt.
Before view dispatch, embedding preparation and cohort finalization, replay derives
the same canonical profile from the original response and checks sealed costs.
Journal finalization independently checks v2 generation evidence before passing
the derived canonical v1 record to existing outcome reconciliation. Historical
v1 profiles remain unchanged; their evidence is not upgraded by relabelling.

Non-EOS and malformed/unalignable profile returns use the existing typed failure
path: FAILED with private raw evidence and validated costs, exception propagated,
no retry. Structurally valid empty/failed/review profiles preserve their existing
stop/fallback-required decisions; missing source skips dispatch. Verified original
anchor remains mandatory before any profile fallback ranking can be finalized.

Validation: 11 new tests pass, including all six authored stages through finalization
with three model-call records/nine input/six output tokens, stop profiles, malformed
and non-EOS failure preservation, source/artifact/derived-alignment/cost tampering,
and missing-source skip. Full related suite: 407 tests pass. Ruff initially found
one unused test import; removed it, and all four changed Python files pass.

These counts are authored fixtures using a fake encoder and tiny CPU index, not
observed model performance. Identity receipts remain adapter assertions; actual
model loading, exact prompt construction, process/resource enforcement and semantic
fidelity are not independently attested. Legacy adapters remain callable; requiring
typed generation evidence in a new prospective execution version is next.

No generated-family rejection policy adopted. Prior real model/grammar failures
unchanged. R1 actual isolation/A03/baseline/native parity NOT_RUN; curator/environment
unanswered. Actual identity/anchor/resource/fidelity gates remain open, R3/R4 absent,
R5 not authorized, R6 incomplete. Goal remains ACTIVE.
