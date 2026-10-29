# HT-M26 semantic source landscape expansion

- Run ID: `luna-long-run-20261030-semantic-source-landscape-expansion-20261030`
- Run date: `2026-10-30` (Asia/Bangkok local execution)
- Status: `PASS_OFFLINE_SOURCE_SCREENING_NO_ADMISSIBLE_REPLACEMENT`
- Parent audit: `luna-long-run-20261030-source-landscape-20261030`
- Source head at review: `d1f166027225789f3044289f223c48aca798bb96`

## Purpose

Expand the public-source screen after M22 while preserving the existing Bridge
blocker and avoiding restricted payload acquisition. The screen asks whether a
candidate can satisfy the exact HT-T1 device-product-to-patent judgment
contract, not whether it is merely about patents or medical technology.

## Result

PatentMatch and PatentBench are rejected for task mismatch. A sharps-disposal
device landscape on Zenodo is the closest domain-aligned lead, but its files
are restricted and the public metadata does not establish the rights, judgment
schema, adjudicator, group, and holdout requirements. It remains
`PROMISING_DOMAIN_BUT_BLOCKED_LOCAL`, not a dataset acquisition or gold source.

## Verification

- Public metadata/landing-page screen completed for three new candidates.
- Existing Bridge branch preserved as `BLOCKED_LOCAL`.
- Restricted payload acquisition: `0`.
- Runtime inputs and semantic labels added: `0`.
- Provider/network calls for project execution: `0`.
- Paid cost: `USD 0.00`.
- Candidate matrix: `docs/healthtech/research/SEMANTIC_JUDGMENT_SOURCE_LANDSCAPE_20261030.md`.
- Exact source identifiers and search coverage: `verification.json`.

## Next action

Obtain owner-authorized access and source-specific terms for the sharps-disposal
lead, or obtain another source that passes the full M23 manifest. Do not
download restricted files, infer labels from screening metadata, or rerun
scientific controls until the real source passes M23, M25, and M24.
