# HT-M23 semantic source authorization preflight

- Run ID: `luna-long-run-20261030-source-authorization-preflight-20261030`
- Run date: `2026-10-30` (Asia/Bangkok local execution)
- Status: `PASS_ENGINEERING_OFFLINE_AUTHORIZATION_PREFLIGHT`
- Parent evidence: `luna-long-run-20261030-source-landscape-20261030`
- Implementation commit: `567bbd1` (`feat(healthtech): add semantic source authorization preflight`)

## Purpose

Add a fail-closed owner authorization boundary before a future semantic
device–patent source can be acquired or ingested. The preflight validates
source identity and hash, source-specific rights clauses, intended use, local
only transfer decisions, resumable acquisition, byte/file bounds, safe relative
storage paths, exact label vocabulary, unjudged-pair policy, independent group
minimums, and a predeclared final holdout.

The package accepts manifests only. It does not acquire source data, create
semantic labels, dispatch providers, or authorize public redistribution.

## Implemented artifacts

- `src/patent_to_pilot/evaluation/healthtech/source_authorization.py`
- `scripts/healthtech/validate_semantic_source_authorization.py`
- `tests/test_healthtech_source_authorization.py`
- `docs/healthtech/research/SEMANTIC_JUDGMENT_SOURCE_AUTHORIZATION.md`

## Verification

- Authorization and existing judgment/submission/G6 tests: `24 passed`.
- Targeted compilation: exit `0`.
- CLI synthetic smoke: `PASS` with no persisted gold labels.
- `git diff --check`: exit `0`.
- Corpus acquisition: `0`.
- Semantic labels created: `0`.
- Provider calls: `0`.
- Paid cost: `USD 0.00`.

Exact commands and artifact hashes are in `verification.json`.

## Boundaries

M23 does not prove that a future source is legally licensed; it requires a
source-specific rights clause and owner authorization to be supplied. It does
not replace `ht-relevance-judgment-cohort-v1`, convert disclosures into gold,
or unlock HT-B0a/B0b/B1/B2/B3 scoring. Bridge, paid HT-B4, deployment,
outreach, clinical/FTO, public raw-data release, and Claude UX/UI remain
paused or blocked.

## Next action

Supply an owner-authorized manifest that passes this preflight, acquire only
within its approved bounds, then bind the source to the existing judgment
contract and ingest explicit reviewer rows while preserving the frozen
denominator, split policy, holdout, and unjudged pairs.
