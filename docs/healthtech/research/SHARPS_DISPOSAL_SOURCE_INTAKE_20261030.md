# Sharps disposal source intake

This is a source-specific owner intake packet for Zenodo record
`10.5281/zenodo.21101400` (`Global Patent Landscape Review of Sharps Disposal
Devices in Healthcare: Code and Dataset`). It is a draft, not an authorization
and not a request to bypass restricted access.

## Public metadata observed

- Record version: `1.0`.
- Record date: `2026-07-01`; metadata updated `2026-07-09`.
- Access state: `restricted`.
- Record metadata license: `CC-BY-4.0`.
- Public description names raw WIPO, USPTO, Google Patents, and Espacenet
  exports, screening support, a processed patent dataset, a reviewer-decision
  field, an AI-decision field, and technical feature extraction.
- Public API response exposed no file inventory, byte counts, or file hashes.

The metadata license and access state are not enough to authorize local use of
the restricted files. Per-file terms, the actual bytes, and the data schema
must be inspected after an owner-authorized access decision.

## Required owner decision

Authorize or reject local research use of the exact restricted file set under
the intended use `semantic_relevance_judgment`. The decision must state:

1. Whether the named researchers or record owner authorize local copying.
2. Whether raw and normalized files may remain in permitted local storage.
3. Whether provider transfer and public redistribution are prohibited.
4. Attribution and citation requirements.
5. The permitted acquisition method, storage location, byte ceiling, and file
   ceiling.

No outreach, download, or transfer is performed by this packet.

## Schema inspection gate

If access is authorized, inspect the exact files before creating an M23
manifest. The public description suggests, but does not prove, that
`dataset_ec01_com_probabilidade.xlsx` contains reviewer and AI decision
columns. Treat AI decisions as non-gold until provenance is explicit. Verify:

- reviewer label vocabulary and whether it maps exactly to `relevant` and
  `not_relevant`;
- row-level source locator, revision, and adjudicator role;
- whether non-selected rows are observable or must remain unjudged;
- named device/product or comparator query identity;
- company and patent-family identifiers with no cross-split leakage;
- an untouched final holdout that can be frozen before ingestion;
- raw/normalized hashes and reproducible file counts.

## Execution sequence after authorization

1. Build and validate `ht-semantic-source-authorization-v1` with exact source
   hash, rights clause, intended-use decision, bounds, labels, groups, and
   holdout.
2. Stage the authorized snapshot through M25 using
   `scripts/healthtech/acquire_semantic_source.py`.
3. Bind explicit reviewer rows through M24 using
   `scripts/healthtech/ingest_relevance_judgments.py`.
4. Inspect the real validation report and preserve the existing denominator,
   unjudged policy, and untouched holdout.
5. Rerun HT-B0a/B0b/B1/B2/B3 only after the real judgment manifest passes.
