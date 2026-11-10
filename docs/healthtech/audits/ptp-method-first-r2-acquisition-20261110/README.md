# SACR full-index acquisition implementation: synthetic evidence only
Implemented src/patent_to_pilot/research/sacr_acquisition.py: full-index chunked
NumPy float32 dot products, family MaxP across all passages/chunks, identical
caller-supplied eligibility for every view, stable global score/family-ID cutoff,
deduplicated union and anchor scores for every union family (including rescues).

Requires anchor first, one to three views, depth1–200 per view; hence union<=600.
Finite unit vectors are checked with absolute norm tolerance1e-4, no normalization
or re-encoding. Every family must have an indexed passage; invalid ownership or
dtype/dimension/mask fails. No hidden labels or corpus text are accepted.
Duplicate family appearances are counted, not replaced with extra views. Caller
still owns exact-text view deduplication and the source/profile acceptance gate.
An empty eligible population returns empty lists without dropping the query.

Unlike historical torch.topk followed by sorting only its retained subset, this
implementation admits every tie at the cutoff before family-ID ordering. The
historical baseline runner is unchanged; actual tie divergence and CPU/GPU
numerical parity remain NOT_RUN. This CPU implementation is not evidence of a
resource-feasible V100 pipeline and must not substitute for the declared final
backend without explicit versioning/parity/resource review.

33 targeted tests pass:18 acquisition and15 selector. Coverage includes exact
boundary ties, cross-chunk family MaxP, eligibility before top-k, empty universe,
duplicate accounting, malformed/nonfinite/nonunit inputs, exhaustive independent
family-reference comparisons over four chunk sizes, and acquisition-to-selector
integration without exposure expansion. Ruff passes for the two new files.
Synthetic ranking correctness does not establish real corpus/owner provenance,
query encoding identity, semantic fidelity or retrieval improvement.

Memory is bounded by the family score matrix, input arrays and chunk workspaces;
the passage matrix may be memory mapped. Current time includes scanning every
passage for every view and unit-norm checks on every call; optimize only with
equivalent verified behavior. Counts record views, families, passages, dot products,
chunks, union size and duplicates. GPU time/memory and real throughput are NOT_MEASURED.
Caller must bind owner/order/vector hashes, provide benchmark-specific runtime
eligibility and preserve failed/missing queries. Actual R1 isolation/A03/parity,
generation compatibility, fidelity audit and matched-control orchestration remain
open. No real data, model, GPU job, re-encoding, protected access or new pull occurred.
