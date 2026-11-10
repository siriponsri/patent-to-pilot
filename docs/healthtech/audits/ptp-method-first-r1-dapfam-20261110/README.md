# R1 native DAPFAM semantics and denominator parity

Date: 10 November 2026 (Bangkok). Base: `6202c58966e85b3c75d306c14228bb09d0161c74`.
Status: SYNTHETIC_DIFFERENTIAL_PASS. Real dev evaluation, full MTEB/model execution and published-result replication NOT_RUN. Codex active writer; goal ACTIVE. No protected labels, dataset rows, paid calls or GPU jobs.

## Pinned owning sources

Inspected public MTEB source at `9242b36a1d400fc8c3af573e6a6e0705c0b96e3d`, dataset revision `780f4011d60297fc6e97a4119b0c516d13afea2d`:

- [DAPFAM task loader](https://github.com/embeddings-benchmark/mteb/blob/9242b36a1d400fc8c3af573e6a6e0705c0b96e3d/mteb/tasks/retrieval/eng/dapfam_patent_retrieval.py), `load_data`: all partitions retain the full corpus. IN/OUT select binary positive qrels. Corpus title is separate from abstract/claims text; TA query composition excludes claims. Empty-positive queries are omitted from qrels.
- [Retrieval task](https://github.com/embeddings-benchmark/mteb/blob/9242b36a1d400fc8c3af573e6a6e0705c0b96e3d/mteb/abstasks/retrieval.py), `_filter_queries_without_positives`, `_evaluate_subset`: query eligibility is restricted to the positive-qrel population before retrieval.
- [Metric implementation](https://github.com/embeddings-benchmark/mteb/blob/9242b36a1d400fc8c3af573e6a6e0705c0b96e3d/mteb/_evaluators/retrieval_metrics.py), `calculate_retrieval_scores`, `parse_metrics_from_scores`: calls pytrec_eval and averages returned query scores, rounded to five decimals.
- [Retrieval evaluator](https://github.com/embeddings-benchmark/mteb/blob/9242b36a1d400fc8c3af573e6a6e0705c0b96e3d/mteb/_evaluators/retrieval_evaluator.py), `evaluate`: identical-ID removal and first-result skipping are optional, default false in this task. No MTM X mask belongs here.

Source hashes are in [differential.json](differential.json). Raw public sources were cached outside Git; no benchmark dataset was downloaded. MTEB source LICENSE is Apache-2.0 (inspected); no third-party source is vendored by this package. Two initial evaluator URLs were obsolete and returned 404; the pinned repository tree resolved the current paths above.

## Implementation and verified behavior

`evaluation/dapfam_native.py` defines prospective dev-only TA/TAC loading and binary NDCG/Recall on explicit ranked lists. It rejects X candidate filtering, duplicate corpus/query/relation identities, duplicate ranked families, unknown IDs and invalid metric cutoffs. It preserves the full corpus and reports input queries, positive-qrel denominator, excluded no-positive queries, missing rankings and empty rankings separately.

The raw metric backend was experimentally confirmed to omit a missing query from returned scores. Empty result dictionaries receive zero scores. Our wrapper therefore averages over the complete eligible qrel population: a missing or empty ranking scores zero, including an all-failed run. This is an explicit failure-accounting safeguard, not a claim that the unwrapped backend automatically preserves missing queries. Queries without positives in the selected partition are excluded consistently with the native task and counted explicitly.

Ranked-list order is preserved via strict ordinal scores in parity tests. Raw-score tie handling is a separate retrieval-backend contract; this package does not claim exact published-backend tie reproduction. Duplicate IDs are rejected prospectively instead of the source loader's dictionary last-write behavior; no real duplicates were inspected or repaired.

## Checks

- `rtk proxy python -m pytest tests/test_dapfam_native.py tests/test_dapfam_acquisition.py tests/test_mtm_input_boundary.py tests/test_vector_identity.py tests/test_mtm_eligibility.py`: **61 passed in 4.39 s**, exit 0.
- Changed-file Ruff for the module, verifier and tests: PASS, exit 0.
- `verify_dapfam_native_parity.py`: **12 synthetic differential cases PASS**, 3 qrel partitions × complete/missing/empty/all-missing outcomes. Executes hash-pinned actual loader and positive-query-filter functions with a synthetic dataset stub, then actual `pytrec_eval` and pinned MTEB metric aggregation. There is no dataset network access in the verifier.
- Backend: `pytrec-eval-terrier==0.5.11`, Windows CPython 3.12 wheel, installed with `--only-binary=:all: --no-deps --target` into the project's private artifact area. No global environment or remote research venv was changed. This pins the tested backend, not an inferred historical paper dependency.
- Hand-calculated fixtures independently verify NDCG/recall, including an OUT-positive at rank 3 behind same-domain candidates, and failure denominators.

Reproduce the differential check with the exact public source cache and isolated backend directory:

```text
python scripts/healthtech/verify_dapfam_native_parity.py
  --source-cache <private>/method-first-r1-public-sources
  --backend-dir <private>/dapfam-parity-deps
  --output <new-synthetic-parity-receipt.json>
```

The cache filenames use repository paths with `/` replaced by `__`; the verifier checks every executed source's SHA256. Source URLs and revision are listed above. Existing output is refused. All fixtures are fictional.

## Remaining work

The current method-first progress pointer was found nested in the first legacy work-package object (the earlier text insertion matched an inner brace after a BOM). It is now a root-level field. A parsed structural comparison confirms all historical progress content is unchanged. This repairs a handoff location, not a study result.

Integrate the safe MTM runtime and vector identity checks into the prospective parity runner. Arrange trusted staging before actual dev label-dependent A03/parity checks; do not parse mixed protected metadata in the agent. Bind DAPFAM staged dev manifests and its actual denominator before scoring. The existing DAPFAM split/history remains unchanged. R1 is not complete and these fixtures are not a new scientific result or method approval.
