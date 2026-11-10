# R1 A03 exact-mask eligibility auditor

Date: 10 November 2026 (Bangkok). Base: `9378a2c4e777d639cb7f78f8775be575883c0b12`.
Status: IMPLEMENTED_SYNTHETIC_VERIFIED; real dev incidence NOT_RUN. Codex active writer; goal ACTIVE.

`scripts/healthtech/audit_mtm_dev_eligibility.py` accepts only staged development metadata and qrels, checks their hashes and identical populations, then invokes the actual frozen `run_mtm_dense_pool.keep_mask`. The original runner is imported without invoking its main function or loading GPU models. Corpus JSONL is streamed; only wanted target metadata is retained. The entire corpus is checked for duplicate family IDs. Outputs contain aggregate counts and input/source hashes, never target identities or texts.

The predicate is evaluated on one-element target slices in main/X. This preserves the original elementwise publication, own-family and shared-CPC predicate. For valid metadata the auditor therefore uses the exact existing rule, rather than a second approximate predicate. Unknown/malformed date or CPC metadata is classified indeterminate, not repaired or counted eligible. Missing targets are ineligible. Overlapping reason counts are separate from exclusive eligible/ineligible/indeterminate counts. Queries with zero verified eligible targets remain in the denominator. Labels are unchanged; query drops are always zero.

The auditor detects shared representative CPC even where a synthetic cited publication had a different class. It does not claim to recover actual cited-publication CPC from the corpus: that field is absent, and the report explicitly marks it not supplied. A measured mismatch explanation still requires permitted source evidence; no new acquisition is authorized.

## Verification

- `rtk proxy python -m pytest tests/test_mtm_eligibility.py tests/test_mtm_input_boundary.py tests/test_mtm_pipeline.py tests/test_mtm_methods.py`: exit 0, **44 passed in 3.44 s**.
- Changed-file Ruff: PASS before the final integration test addition; final check recorded with publication.
- Hand-counted eight-pair fixture: 1 eligible, 4 ineligible, 3 indeterminate; all 8 pairs and the query remain present. Overlapping own-family/shared-CPC reasons do not double count the exclusive denominator.
- Tests include exact cutoff date, future publication, missing corpus family, missing/malformed date, malformed CPC, representative-CPC mismatch, zero eligible queries, duplicate corpus IDs and population rejection before corpus access.
- CLI integration stages fictional dev/test rows, executes only the dev auditor, verifies a complete aggregate/hash report, and verifies existing output is refused and byte-preserved.
- No actual benchmark labels, test rankings or scores were opened. No GPU job, paid API, BigQuery pull, new scientific experiment or qrel amendment.

## Next actions

1. Implement A14 corpus/passage/model/vector identity and adversarial wrong-order checks using existing receipts.
2. Complete native DAPFAM parity and prospective runtime integration.
3. Arrange trusted staging outside development-agent label access, then run this auditor on safe dev inputs and establish real ranking parity. A01/A03 remain open pending that evidence.

Reviewable future invocation, only after safe staging:

```text
python scripts/healthtech/audit_mtm_dev_eligibility.py
  --runtime-dev <staged-runtime/dev>
  --dev-evaluation <isolated-dev-qrels>
  --corpus <existing-corpus.jsonl>
  --output <new-dev-eligibility-report.json>
```

There is no test-mode CLI argument and no mixed-query-metadata option. Historical unsafe scripts are unchanged; this package is the prospective dev audit path.
