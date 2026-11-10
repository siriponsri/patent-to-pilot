# Reserved query embedding adapter and row binding

2026-11-10 09:44:13 Bangkok; base 483df9fbf78e900c3498709e51a1eaed1f2d9137. Authored fake encoder only, no model or real corpus.

embedding_plan maps validated generic/selective views and relation/condition components
into a single ordered row list. Exact text duplicates share a row within the query under
one encoder mode; both anchors therefore share one vector. Encoder identity must bind
prefix/tokenizer/preprocessing as well as weights. Role distinctions remain in row maps
and component block references, not in separate encoder modes.

Controller embed replays inputs before reservation, then gives the injected adapter a
detached plan and pinned encoder-manifest digest. The adapter returns vectors, row/plan/
encoder/byte receipt and cost metrics. Float32, finite unit geometry, row count/order and
canonical vector bytes must agree before a completed output is sealed. Detached read-only
arrays are used during validation. Private per-query JSON vectors roundtrip through float32;
no full-corpus encoding or vector output is committed. Invalid returns retain FAILED attempts.

Nine new tests;22 SACR files + MTM bound runner:279 PASS. Ruff on three changed files PASS.
Tests cover reservation before adapter, shared anchor/exact-text reuse, sealed JSON replay,
wrong row/encoder/plan/bytes/dtype/geometry, NaN and review stopping before dispatch.

This is structural binding, not proof that an honest encoder used the stated text. Actual
adapter/model identity preflight, token/resource enforcement and dimensional compatibility
with the real index remain. Current vectors are authored two-dimensional fixtures. Cost
metrics are adapter reports; unknown costs on failure remain unknown. No fidelity approval.

Next connect sealed vectors through mapped views/components to existing CPU acquisition
and selector, binding eligible/index identity and preserving stage receipts/costs. Typed
finalization, anchor attestation, failed-generation policy and live resource controls remain.
R1 curator/isolation/A03/parity and generation/fidelity gates still block real research runs.
