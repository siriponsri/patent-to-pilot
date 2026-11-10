# Bound CPU retrieval controller integration

2026-11-10 09:50:59 Bangkok; base 5acdfce338d738b1bbc3d41f6467dccfe9ba0734. Authored source, fake encoder, four-passage index only.

BoundCPUIndex checks pinned manifest bytes, ordered family/passage ownership and vector
hash/geometry, then detaches read-only arrays. Query mask digest is predeclared and checked
against the same family order. Controller identity must equal the declared index manifest.
This proves agreement, not correctness of the mask policy or physical isolation.

Controller acquisition/selection replay source/view/embedding inputs, reconstruct exact
text-row mappings, bind query/index dimensions, and journal stages separately. Acquisition
runs existing full-index CPU MaxP for both arms. Selection checks sealed acquisition against
query/index/mask/embedding/depth, then reuses it without search. Actual acquisition/component
dot products are separated; CPU GPU time is zero, peak memory stays unknown. Journal measures
callback wall time, which excludes preflight/replay and is not end-to-end time.

Seven new tests;26 focused PASS, full24 SACR files + MTM bound runner:297 PASS (exit0 verified).
Ruff on four changed Python files PASS. One six-stage authored fixture reaches record
reconciliation with12 index dot products and9 component dot products. Forbidden search
callback during selection proves no repeat. Excluded family absent; changed masks, identities,
vector content and sealed acquisition refused; caller array mutation does not alter snapshot.

## Critical limits

No real index/model/data use. Index construction copies the full matrix and current
vector_digest may allocate a full canonical byte buffer: full-scale memory/time acceptance
is NOT established. Do not launch against the actual corpus before bounded preflight and
resource design. Snapshot hashes must originate from trusted real corpus/encoder receipts;
fixture-generated hashes are not such provenance. Mask values need actual R1/A03 validation.

Controller lacks a finalizer binding supplied outcome rankings to sealed selection; low-level
journal reconciliation remains weaker for downstream records. Six-stage fixture success is
not production end-to-end SACR, fidelity approval, actual ranking parity or effectiveness.
Typed finalization, fallback anchor attestation, failed-view policy, live caps, generation
compatibility and real curator isolation remain. Next close final-output binding, then
resource/real preflight gaps. R3/R4 absent; R5 not authorized.
