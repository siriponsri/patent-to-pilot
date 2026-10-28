# Typed public-cohort registry audit

Date: 2026-10-28 (Asia/Bangkok)

Status: `PASS_ENGINEERING`; fresh third-party acquisition `NOT_RUN`

Candidate commit: `aecc7f3` (`healthtech: type public cohort rights registry`)

## Outcome

`scripts/healthtech/fetch_public_device_cohort.py` now binds every newly emitted
source-registry row to a canonical `rights_policy_id`:

- `openfda-pma-records` for PMA regulatory records
- `abbott-product-patent-disclosures` for the Abbott product disclosure page
- `google-patents-pages` for Google-derived patent pages

The builder also writes the sorted policy-ID set into `manifest.json`. Unknown
source IDs or source types fail closed instead of receiving a guessed policy.
Existing free-text `rights` notes remain for compatibility and explanation.

## Verification

- `rtk python -B -m pytest -q tests/test_healthtech_repairs.py` -> `PASS`, 18 passed
- `rtk python -B -m compileall -q src scripts tests` -> `PASS`
- `rtk git diff --check` -> `PASS`

The regression covers all three public source classes and the unsupported-source
failure path. The implementation commit contains only the builder and its test.

## Boundary

This change updates future acquisition output. It does not rewrite the ignored
`results/healthtech/ht-public-cohort-20261028-r1` artifact or claim that its
existing registry is typed. A future fresh acquisition or an explicitly audited
migration is required before the Abbott provenance receipt can change from
`LEGACY_TEXT_ONLY` to `TYPED_POLICY_ID`.

The policy IDs reference the existing source-specific rights matrix; they do not
grant product-display or redistribution rights. No network acquisition, paid
provider call, scientific benchmark, deployment, or external communication was
performed for this package.

Machine-readable details are in `verification.json`.
