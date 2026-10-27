# HealthTech Pre-Live Offline Receipt

Date: 2026-10-27
Track: HealthTech
Status: PRE-LIVE OFFLINE COMPLETE

## Scope and boundary

This package covers local migration, public-source preparation, offline engineering checks, and an HT-specific API dry-run. It does not authorize paid inference, live provider calls, deployment, clinical or human studies, external outreach, or publication claims.

The package stops before live/provider execution. Zero retrieved patent candidates in the public dossiers are an unresolved corpus gap, not a negative device-patent finding.

## Implemented outputs

- SciFact release is pinned locally from the AllenAI release commit `68b98a56d93e0f9da0d2aab4e6c329469a0f72`.
  - Archive: `3,115,079` bytes.
  - Archive SHA-256: `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`.
  - Counts: `5,183` corpus documents, `809` train claims, `300` dev claims, `300` unlabeled test claims.
  - Runtime claim/corpus loading is separated from evaluator-only gold loading.
  - Receipt: `data/manifests/healthtech/scifact-release-20261027-r1.json`.
- Three bounded openFDA 510(k) public records were normalized with provenance, hashes, source fields, rights notes, and explicit patent-evidence gaps: `K190167`, `K163345`, and `K121849`.
  - Raw batch bytes: `8,742`.
  - Manifest: `results/healthtech/public-510k-20261027-r1/manifest.json`.
- Three fresh public-source dossier drafts were regenerated after the policy-layer patch:
  - `results/healthtech/public-dossiers-20261027-r3/K190167`
  - `results/healthtech/public-dossiers-20261027-r3/K163345`
  - `results/healthtech/public-dossiers-20261027-r3/K121849`
  - Each contains JSON, English Markdown, Thai Markdown, acquisition events, and a manifest.
- Local dossier history and source inspection were rechecked from the fresh `K190167` dossier:
  - `results/healthtech/public-history-20261027-r2/`
  - Versions `1 -> 2`, with a recorded user edit key `review_note`.
- The HT-specific API seam was dry-run verified with no transport execution.
- Offline policy labels now cover HT-B0a, HT-B0b, HT-B1, HT-B2, and HT-B3 engineering controls. These remain engineering baselines and do not establish scientific benefit.

## Verification receipt

Commands executed:

```text
rtk proxy python -B scripts/healthtech/export_schemas.py schemas/healthtech
rtk proxy python -B -m pytest -q -p no:cacheprovider tests/test_healthtech.py tests/test_healthtech_prelive.py tests/test_provider_adapter.py
rtk proxy python -B scripts/healthtech/run_api_dry_run.py configs/healthtech/api_dry_run.json
rtk proxy python -B scripts/healthtech/verify_offline.py results/healthtech/verify-offline-final-public --suite public
rtk proxy python -B scripts/healthtech/verify_offline.py results/healthtech/verify-offline-final-all --suite all
```

Results:

- Focused HealthTech/provider tests: PASS.
- Guarded public suite: `269/269` tests passed; `0` failures, `0` errors, `0` skips.
- Guarded all suite: `269/269` tests passed; `0` failures, `0` errors, `0` skips.
- Public verification receipt: `results/healthtech/verify-offline-final-public/verification.json`.
- All verification receipt: `results/healthtech/verify-offline-final-all/verification.json`.
- Guarded counters for both suites: `network_attempts=0`, `forbidden_credential_read_attempts=0`, `provider_calls=0`, `paid_cost_usd=0`.
- API dry-run receipt: `status=DRY_RUN_NOT_EXECUTED`, `network_attempts=0`, `provider_calls=0`, `paid_cost_usd=0`.
- No live/provider API call was started.

## Rights, limits, and unresolved work

- The openFDA records are regulatory source facts only. They do not establish clinical suitability, FTO, patent validity, or investment merit.
- No patent corpus was acquired in this package. Disclosed links remain unjudged where source evidence is absent.
- SciFact is an evidence-verification component, not device-patent gold. Official test labels are absent from the pinned release.
- Raw third-party responses remain local output and are not intended for Git publication. The original input pack was preserved unchanged.
- The Bridge release audit remains blocked on reuse rights, cohort reconciliation, and split rules; it was not reexecuted here.
- HT-G4/W14, HT-G5/W17, publication readiness, and production readiness remain open.

## Next bounded action

Acquire or receive a rights-cleared patent corpus for one named public device, freeze the cohort and provenance rules, and rerun the dossier with disclosed-link evidence. Keep SciFact official evaluator integration as a separate engineering package. Do not start paid/live provider execution without fresh explicit authorization and the existing budget ledger.
