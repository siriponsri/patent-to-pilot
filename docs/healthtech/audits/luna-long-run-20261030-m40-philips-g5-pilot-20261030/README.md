# HT-M40 Philips G5 offline pilot-task expansion

- Run ID: `luna-long-run-20261030-m40-philips-g5-pilot-20261030`
- Date: `2026-10-30` (Asia/Bangkok local execution)
- Parent dossier audit: `docs/healthtech/audits/luna-long-run-20261030-m38-philips-dossiers-r6-20261030/README.md`
- Tested code commit: `66b2fafe11938276b33b89006d8032d8514a97eb`
- `origin/main` at verification: `66b2fafe11938276b33b89006d8032d8514a97eb`
- Status: `PASS_OFFLINE_ENGINEERING_TASK_3_PHILIPS_CASES`

## Scope

This package expands the existing G5 engineering dry-run from one Cook case to
all three current Philips dossiers. Each task uses a case-specific FDA 510(k)
source and the allowed `k_number` field under `local_research`, then exercises
seeded correction, versioned history, selected version-2 exports, and the
external rights boundary. It is not a participant or commercial study.

## Results

| Case | FDA source | History | Export | External boundary | Engineering time |
|---|---|---|---|---|---:|
| AngioSculpt Scoring Balloon | `openfda-510k-k050629` | `1 -> 2` | JSON/EN/TH v2 | `BLOCKED_LOCAL` | `0.1144s` |
| Thromcat Thrombectomy System | `openfda-510k-k060016` | `1 -> 2` | JSON/EN/TH v2 | `BLOCKED_LOCAL` | `0.1154s` |
| Turbo-Elite Laser Catheter | `openfda-510k-k170059` | `1 -> 2` | JSON/EN/TH v2 | `BLOCKED_LOCAL` | `0.1240s` |

All three receipts report `PASS_OFFLINE_ENGINEERING_TASK`, selected version
`2`, zero provider calls, zero network calls, and `USD 0.00` paid cost. Every
receipt-recorded artifact hash matches its generated file. A direct
`product_display` probe with the correct FDA source IDs fails closed with
`RightsBoundaryError` for all three dossiers because Philips marking and
Google-derived patent sources remain `BLOCKED_LOCAL`.

## Verification

Machine-readable details and source/output hashes are in
[`verification.json`](verification.json). The ignored local outputs are under
`results/healthtech/ht-g5-philips-pilot-20261030-r2/` and are intentionally not
copied into this audit folder.

The initial probe also confirmed that using `product_display` as the task
purpose for a dossier containing blocked local-only sources must fail closed.
The successful task path therefore uses `local_research` and checks the
external projection separately, matching the G5 task packet's intended-use
boundary.

## Boundaries

- This is backend engineering evidence, not observed participant task time,
  usability, willingness-to-pay, repeat use, ROI, or product-market fit.
- Philips product-level disclosed links are not semantic relevance gold, claim
  support, exhaustive recall, clinical evidence, FTO, patent validity,
  investment merit, or publication evidence.
- Semantic device-patent labels remain `NOT_RUN`; Zenodo record `21101400`
  remains restricted.
- Live/provider HT-B4, Bridge, deployment, outreach, clinical/FTO, public raw
  data release, and Claude UX/UI remain blocked or paused.

## Next action

Keep the task packet and these dry-runs local-only. Obtain an owner-authorized,
rights-cleared semantic judgment source before M23/M25/M24 and any semantic
rerun. Do not treat these engineering timings as user timings or service-level
claims.
