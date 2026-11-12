# Graph track: automatic round plan (12 Nov 2026)

Status: PROSPECTIVE, frozen before any Graph retrieval score of this round. The owner approved running Graph and SACR round 2 in parallel (`docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112/owner-parallel-round2-approval.json`). The rules stay: one repo writer and one GPU job at a time; paid API, Neo4j writes, full-corpus LLM extraction and protected tests are excluded.

## What exists (read-only survey, 12 Nov)

| Need | Component |
|---|---|
| Deterministic relation and alias extraction | `sg_relations_v2.extract_family_v2`. Pattern: configured, adapted or operable to + verb + operand. At most 8 records per family. Alias key `sha256(action|operand)` after casefold and article stripping |
| Corpus materialization | `sg_materialization_v1.materialize`. R4 run: 23,037 records, 13,736 keys, 12,785 of them single-family, largest key 69 families, no hub above 100 |
| Automatic relation screening | `km_automatic_review` with track GRAPH: 6 checks with literal quotes. `automatic_screening.route_result` turns any non-screened relation into `ABSTAIN_RELATION` and `not_run` into `HOLD` |
| Screened postings | `sg_automatic_evidence.bind_screened_relations` re-extracts, binds the screening hashes and counts omitted relations |
| G vs S | `sg_bounded_traversal.rank_structured_and_graph`: bounded breadth-first search with hop, edge, degree, reverse-edge and frontier budgets. G adds hop-2 families at score 0.5. The `sg_r6_scoring` structured path is parity-only and stays an implementation check |
| Fusion and baseline | `sg_r6_scoring.query_keys` and `fuse` (RRF k=60 over B0 top-200). B0 comes from `run_dapfam_native_baseline` + `evaluate_dapfam_native_baseline` (OUT Recall@200 primary) |

## Protocol decisions (fixed now, before outcomes)

1. **Screening scope.** Screen only relations reachable from the frozen pilot-20 query keys within one key hop, never the whole corpus. The call cap per stage is declared from the CPU census below, before any GPU dispatch.
2. **Input limit.** A relation whose review request exceeds 8,192 tokens is recorded as `invalid_output`, so the relation abstains. It is never `not_run`, which would HOLD the run. Its count is reported.
3. **S scoring contract.** The flat 1.0 score is replaced. S scores a family by the number of distinct matched query keys, with ties broken by a fixed salted hash of the family ID, not alphabetically. G uses the same rule at hop 1 and adds hop-2 families at a fixed lower weight.
4. **Matched work.** A third arm, S-deep, is a non-traversal control that spends the same edge budget as G by scanning further down direct postings. The comparison is G vs S-deep at equal edges. G vs S is reported as secondary. A frozen topology perturbation (key-family edges rewired with a fixed seed) is diagnostic only.
5. **Abstention and denominators.** Families whose relations are all abstained or unscreened contribute nothing structured. A query with no keys or no hits falls back to B0 and stays in the denominator. Coverage and fallback rates are reported for every arm.
6. **Pilot-20.** Twenty query IDs are drawn from the 474 dev queries by a stable salted SHA-256 ranking, frozen before any Graph score. Pilot results are development evidence; win or loss is not a full-dev gate.
7. **Journal.** Stages beyond `synthetic` need new qualification and live-admission code with explicit per-stage call and time caps, added through an append-only authority amendment.

## Ordered work (CPU unless noted)

1. Query-side coverage census: `query_keys` over the 474 query texts, counting queries with zero keys or zero hits. Cheap; it uses no qrels.
2. Freeze pilot-20 IDs; compute the reachable relation set and the screening call estimate.
3. Implement the S/G scoring contract, S-deep and the perturbation diagnostic, with authored fixtures.
4. Graph screening runner (one call per relation, input-limit abstention) on the SACR runner pattern; CPU fixture.
5. Journal stage qualification for `graph_screening` and `pilot`; authority amendment with caps.
6. GPU: bounded relation screening for the pilot scope; settle.
7. Arm adapter and pilot evaluator variant (pinned B0 rankings, pilot subset); pilot run; then full-dev per gates.

## Open uncertainties

- Whether the remote R4 `relations.jsonl` still exists; a CPU re-materialization is cheap (about 26 s at R4).
- Which query text view `query_keys` hashes (TA vs OUT prefix); to be fixed in step 1 from the pinned query manifest.
- The CPU budget is limited (about 4,700 s left after the SACR v4 bookings). CPU job precharges should be tightened, e.g. 120 s bounds instead of 600 s, because actual use is about 25 s.
