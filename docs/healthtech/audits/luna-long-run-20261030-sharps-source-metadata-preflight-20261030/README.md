# HT-M27 sharps source metadata preflight

- Run ID: `luna-long-run-20261030-sharps-source-metadata-preflight-20261030`
- Run date: `2026-10-30` (Asia/Bangkok local execution)
- Status: `PASS_METADATA_PREFLIGHT_OWNER_ACCESS_REQUIRED`
- Parent audit: `luna-long-run-20261030-semantic-source-landscape-expansion-20261030`
- Source head at review: `147382e323b6881fad244a3683b9703d391a9d94`

## Purpose

Inspect the public Zenodo API metadata for the conditional sharps-disposal
device lead without downloading restricted files. The goal is to distinguish
what is now evidenced from what still requires owner authorization and actual
schema inspection.

## Findings

- Record `21101400`, DOI `10.5281/zenodo.21101400`, version `1.0`.
- Public metadata reports `access_right: restricted`.
- Public record metadata reports license `cc-by-4.0`.
- The description names raw search exports, screening support, reviewer and AI
  decision fields, and a processed patent dataset.
- The API response exposes no file inventory, byte counts, or SHA-256 hashes.

This changes the lead from a generic domain candidate to a concrete
owner-access intake target, but it does not make the source admissible. The
M23 manifest still cannot be completed until the exact file set, rights terms,
hashes, label semantics, adjudicator provenance, group structure, and holdout
are inspected.

## Verification

- Metadata endpoint read: `PASS`.
- Restricted payload download: `0`.
- Runtime inputs or semantic labels added: `0`.
- Provider/network calls for project execution: `0`.
- Paid cost: `USD 0.00`.
- Owner intake packet: `docs/healthtech/research/SHARPS_DISPOSAL_SOURCE_INTAKE_20261030.md`.
- Machine-readable evidence: `verification.json`.

## Next action

Obtain an owner-authorized access and terms decision for the exact restricted
file set. If approved, inspect the schema, build M23, stage through M25, and
ingest through M24. If not approved, retain the source as blocked and continue
the search for another semantically aligned source.
