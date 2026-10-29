# M24 report

## Decision

Make source authorization a required input to semantic judgment ingestion.
This prevents a future reviewer submission from bypassing the owner-rights,
transfer, storage-bound, and study-design preflight.

## Changes

- `ingest_relevance_judgments.py` now requires `--authorization-manifest`.
- `build_relevance_judgment_manifest` validates the authorization manifest.
- The authorized source ID, revision, source hash, rights policy, and
  authorization-manifest hash are recorded in `authorization_binding`.
- Source-manifest identity, rights policy, and intended-use mismatches fail
  closed.
- Tests cover missing authorization and mismatched authorization hash.

## Evidence

The temporary synthetic smoke produced one explicit judgment and preserved
three absent pairs as unjudged. No source payload or real label was acquired.
The existing judgment contract remains responsible for label, locator,
adjudicator, split, and leakage validation.

## Not run

No real reviewer submission, semantic adjudication, source acquisition,
provider call, paid inference, or HT-B0a/B0b/B1/B2/B3 rerun was performed.
