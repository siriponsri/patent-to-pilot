# HT-M24 authorization-bound judgment ingest

- Run ID: `luna-long-run-20261030-authorization-bound-judgment-ingest-20261030`
- Run date: `2026-10-30` (Asia/Bangkok local execution)
- Status: `PASS_ENGINEERING_OFFLINE_AUTHORIZATION_BOUND_INGEST`
- Parent evidence: `luna-long-run-20261030-source-authorization-preflight-20261030`
- Implementation commit: `a25cd4f` (`feat(healthtech): bind judgment ingest to authorization`)

## Purpose

Enforce the M23 authorization gate at the semantic judgment ingestion boundary.
The CLI now requires an authorization manifest, validates it before building a
judgment manifest, binds its source ID/revision/SHA-256/rights policy to the
judgment source manifest, and records the authorization-manifest hash in the
output. Missing or mismatched authorization fails closed.

## Verification

- Authorization, judgment, submission, and G6 tests: `25 passed`.
- Targeted compilation: exit `0`.
- Synthetic ingest CLI: `PASS`; `1` judged pair and `3` unjudged pairs.
- Authorization binding in output: source `expert-fixture`, manifest SHA recorded.
- `git diff --check`: exit `0`.
- Real corpus acquisition: `0`.
- Real semantic labels created: `0`.
- Provider calls: `0`.
- Paid cost: `USD 0.00`.

The synthetic CLI used temporary authored fixtures only; it is not semantic
gold and was not persisted as a research result.

## Boundaries

M24 does not supply an authorized source, adjudicate labels, or rerun the
scientific controls. It preserves the existing open-world policy: omitted
pairs remain unjudged and are not negatives. Bridge, paid HT-B4, deployment,
outreach, clinical/FTO, public raw-data release, and Claude UX/UI remain
paused or blocked.

## Next action

Once an owner-authorized source manifest passes M23, invoke the ingest CLI with
the same authorization manifest, inspect the validation report, preserve the
frozen denominator and untouched holdout, and only then rerun HT-B0a/B0b/B1/B2/B3.
