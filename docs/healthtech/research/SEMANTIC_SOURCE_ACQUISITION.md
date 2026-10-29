# Semantic source acquisition

This boundary stages an already-authorized local snapshot for later semantic
judgment ingest. It does not discover rights, fetch URLs, send data to a
provider, create labels, or publish raw source material.

## Prerequisites

1. Prepare an `ht-semantic-source-authorization-v1` manifest and validate it
   with `scripts/healthtech/validate_semantic_source_authorization.py`.
2. Set `source.source_sha256` to the canonical snapshot hash produced by
   `source_snapshot_sha256(...)` for the exact local file or directory.
3. Set `acquisition.expected_bytes` and `expected_files` to the exact snapshot
   totals. The declared maxima remain hard ceilings.
4. Keep the source and destination roots separate. The helper rejects overlap.

## Local staging

```powershell
rtk proxy powershell -NoProfile -Command "python scripts/healthtech/acquire_semantic_source.py --authorization-manifest C:\path\authorization.json --source-root C:\path\authorized-snapshot --destination-root C:\path\local-healthtech-data --receipt C:\path\local-healthtech-data\acquisition-receipt.json"
```

The command is local-only. It preserves the source-relative file layout under
`acquisition.storage_relpath`, writes an atomic receipt checkpoint after each
file, resumes verified files, and resumes interrupted `.partial` files only
when their existing prefix still matches the source.

## Verification

The receipt is `PASS` only when the authorization binding, source hash, exact
byte/file counts, per-file hashes, and destination writes all verify. A failed
copy leaves a `FAILED` receipt and does not convert the source into a usable
judgment manifest. Inspect the receipt before invoking
`scripts/healthtech/ingest_relevance_judgments.py` with the same authorization
manifest.

The helper records the declared raw and normalized relative paths, but it does
not infer or rewrite their contents. Omitted judgment pairs remain unjudged,
and no semantic labels are created by acquisition.

## Current status

The repository contains only authored synthetic fixtures for regression tests.
No real semantic source was acquired in this package; owner authorization and a
rights-cleared, semantically aligned source remain required before real ingest.
