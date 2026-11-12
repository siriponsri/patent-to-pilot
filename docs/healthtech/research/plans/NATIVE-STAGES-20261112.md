# Native stages after synthetic qualification (frozen 12 Nov 2026, before any native output)

**Owner decisions.**
- Continue native SACR.
- Raise the CPU cap to 24 h (journal generation 48, 32,285 s remaining).
- Explicit Graph override: Graph v3 proceeds although gate G2 failed (8/20 pilot queries with structure versus 10 required). This is labelled `POST_HOC_OWNER_OVERRIDE_OF_FROZEN_FEASIBILITY_GATE` and must be disclosed in every Graph result and in the manuscript.

**Fixed for both tracks.**
- Pilot-20 is the frozen set from the census (IDs private; `pilot_ids_sha256` is in the census and v3 receipts).
- The pilot is development evidence. A pilot win or loss is not a full-dev gate; only technical validity, integrity and resource feasibility are.
- One GPU job at a time. No qrels are used before the evaluation step. The protected test set is never opened.

## SACR (configuration: marking v4 + review v2, unchanged)

1. **`fidelity` stage (native screening).**
   - The automatic SACR pipeline runs on the 20 pilot query texts, at most 2 calls per query.
   - Caps: at most 40 calls and 3,600 s wall in one job.
   - Outcome per query: `USE_SCREENED_CANDIDATE`, or a fallback (rejected, abstained, flagged or uncertain), or HOLD for unknown state.
   - Every query stays in the denominator.
2. **`pilot` stage (retrieval).**
   - Queries with a screened candidate are re-encoded with the pinned B0 encoder in one GPU job capped at 20 encodes and 1,800 s. All other queries reuse their B0 ranking unchanged.
   - SACR rankings are scored by the existing evaluator on the pilot subset (CPU).
   - Reported: OUT Recall@200 (primary), Recall@100, nDCG@10/100, plus coverage and fallback counts.
   - Controls: B0, and SACR-anchor (the original query through the same path, identical to B0 by construction).
3. **`full_dev`** (474 queries) is declared with caps from the measured pilot throughput: per-call cost × 948 calls plus the encode stage. It runs only if the pilot was technically valid.

## Graph (extractor v3, override)

1. **Screening sample** (frozen rule, before any GPU use).
   - Screen every relation reachable through the pilot queries' direct usable keys.
   - Fill up to a total of **300 relations** from the bridge relations, ranked by `sha256('ptp-graph-screen-20261112|' + relation_id)`.
   - Unscreened relations abstain. The screened, flagged, uncertain and abstained counts are reported.
2. **`fidelity` stage (Graph screening).**
   - One review call per relation (KM review v2, track GRAPH), using the full source unit and the relation candidate.
   - Caps: at most 300 calls and 21,600 s wall per job. The work may be split across jobs, each declared separately.
   - Over-limit inputs are recorded as `invalid_output`, so the relation abstains.
3. **`pilot`.**
   - S, G and S-deep (from `sg_automatic_traversal`) run over screened postings only.
   - Each is fused with B0 by RRF (k=60, top 200).
   - Queries without structure fall back to B0.
   - Reported: G vs S-deep (primary attribution) and G vs S (secondary), with coverage and fallback.

## Journal

`amend_authority` gains append-only stage envelopes for `fidelity` and `pilot`. Each declaration names a settled technical predecessor attempt:
- `fidelity` needs a completed synthetic attempt;
- `pilot` needs a completed `fidelity` attempt.

`qualify_stage` and `claim` accept these stages only under such envelopes. GPU-stage host CPU stays telemetry only.

## Addendum: SACR pilot retrieval details (frozen 12 Nov 2026, before any SACR retrieval score)

Based on a read-only survey of `run_dapfam_native_baseline.py`, `native_dense_ranking.rank_maxp`, `evaluate_dapfam_native_baseline.py` and `automatic_screening.complete_query_panel`.

- **Encoding.** SACR candidate text is encoded as `DENSE_QUERY_PREFIX + candidate`, with exactly the B0 query format, encoder (`MeanPoolEncoder`, PatEmbed-large fp32, pinned `MODEL_PINS`), passage vectors (`VECTOR_SHA`), owner construction and `rank_maxp` depth 200. Only the query text differs from B0.
- **Anchor control.** The same GPU job also re-encodes the 20 original pilot TA texts. If their rankings do not reproduce the pinned B0 rankings exactly, the SACR comparison uses these re-encoded anchors as the B0 reference, and the drift is reported. It is never hidden.
- **Panel.** `complete_query_panel` builds the SACR arm: a screened candidate's ranking where one exists; otherwise the B0 ranking, unchanged. HOLD aborts. Scores are carried through so the evaluator's ordering check still applies.
- **Evaluation.** An evaluator variant takes an explicit rankings file (hash-recorded) and a pilot ID subset. It uses the same `native_dev_task` partitions (ALL/IN/OUT) and keeps per-query rows private.
- **Reported.** OUT Recall@200 (primary), Recall@100, nDCG@10/100; the candidate/fallback counts; and the anchor-reproduction check.
- **Decision rule.** No significance claim on 20 queries; the pilot only checks technical validity and resource feasibility before full-dev.
