# HT-M42 DAPFAM lexical coverage screen

- Run ID: `luna-long-run-20261030-m42-dapfam-coverage-20261030`
- Date: `2026-10-30` (Asia/Bangkok)
- Status: `PASS_OFFLINE_DAPFAM_COVERAGE_SCREEN`
- Tested working-tree base: `799a2e4b6d1f5ebb27d086f7ef6c36b649267689`
- Implementation commit: `d42fc36a9bf238b4b14281e0961dc5e7aa55df31`
- Parent package: `docs/healthtech/audits/luna-long-run-20261030-dapfam-code-provenance-20261030/README.md`

## Objective

Measure whether the local DAPFAM patent-family retrieval diagnostic has a
transparent lexical screen for medical-device-like text, without promoting
the dataset into semantic device-patent gold or copying research-only raw
payloads into the audit.

## Implementation

- Added `scripts/healthtech/analyze_dapfam_coverage.py`.
- Added `tests/test_healthtech_dapfam_coverage.py`.
- The analyzer uses DuckDB `v2.0.0 (Cyanoptera) d54cbbe3df` to query the
  existing parquet inputs in place.
- The screen is case-insensitive substring matching over `title_en +
  abstract_en` using declared `medical_device` and `pharma_biologics`
  lexicons. It is a lexical coverage diagnostic only.
- The output contains aggregate counts, input hashes, a report, and a
  manifest. It does not export row-level text, qrels, or raw parquet data.

## Real result

- Corpus: `45,336` rows; lexical medical-device hits: `2,859`.
- Queries: `1,247` rows; lexical medical-device hits: `86`.
- Positive qrels: `24,929` rows from `49,869` total qrels.
- Medical-device lexical hits in positive qrels: `836` IN-domain pairs and
  `65` OUT-domain pairs where both query and target matched the screen.
- All title and abstract fields were present in the scanned corpus and query
  inputs.

Full aggregate output: `results/healthtech/ht-dapfam-coverage-20261030-r1/`.

## Verification

- `rtk proxy python -B -m pytest -q -p no:cacheprovider tests/test_healthtech_dapfam_coverage.py` -> `5 passed`.
- `rtk proxy python -B -m py_compile scripts/healthtech/analyze_dapfam_coverage.py tests/test_healthtech_dapfam_coverage.py` -> `PASS`.
- `rtk git diff --check` -> `PASS`.
- `rtk proxy python -B -m pytest -q -p no:cacheprovider` -> `PASS` with the
  two existing warnings.
- `rtk proxy python -B scripts/healthtech/verify_offline.py <fresh-output-outside-repository> --suite all` -> `459/459` passed, `0` failures/errors/skips, `0` network attempts, `0` credential-file reads, and `0` provider calls.
- Full parquet run -> `PASS`; `0` provider calls, `0` network calls, and
  `USD 0.00` paid cost.
- Input hashes match the existing DAPFAM BM25 manifest for corpus, queries,
  and qrels.

## Boundaries

- DAPFAM remains a separate citation-based patent-family retrieval diagnostic
  under `CC-BY-NC-SA-4.0` research-only terms.
- Lexical hits do not establish named device identity, clinical suitability,
  semantic patent relevance, FTO, validity, or exhaustive recall.
- This package does not change HT-T1 denominators, family/company groups,
  frozen controls, holdout membership, or the `UNJUDGED` policy.
- Owner-authorized semantic source access is still required for M23, M25, and
  M24; live/provider HT-B4, participant validation, deployment, outreach, and
  Claude UX/UI remain blocked, not run, or paused as previously recorded.
