# HT-M15 declared rights policies and Philips review packet

- Run ID: `luna-long-run-20261029-m15-rights-packet-20261029`
- Date: `2026-10-29` (Asia/Bangkok)
- Status: `PASS_OFFLINE_M1_F3_AND_REVIEW_PACKET`
- Base commit: `e15ce7283091408b198929fc6fb33ad5920919a5`
- Tested code commit: `35ee0728a8b470029ea993d3362a5f9d8ef2bcbf`
- Parent dossier audit: `../luna-long-run-20261029-m14-philips-dossiers-20261029/README.md`
- Related judgment packet contract: `../luna-long-run-20261029-review-packet-20261029/README.md`

## Objective and scope

This package closes the declared-rights-policy seam identified in the M1/F3 long-run brief and records the corrected Philips semantic-review packet inputs. It covers local implementation, offline regressions, the committed-code Philips r5 dossier receipt, and packet construction. It does not acquire new data, dispatch providers, create semantic labels, or publish restricted source material.

## Outcome

The rights resolver now requires a declared `rights_policy_id` and fails closed for unknown, blank, mismatched, or structurally incompatible policy declarations. The Abbott, Cook, and Philips adapters bind each registry/source row to its declared typed policy before constructing runtime inputs. The repair is implemented in `35ee072` across `rights.py`, `abbott.py`, `cook.py`, `philips.py`, and `tests/test_healthtech_repairs.py`.

Adversarial evidence includes:

- External Markdown, JSON, and source-view projection remains rights-filtered after history save/reload across both languages.
- Unknown, mismatched, and blank policy IDs are rejected at the Abbott adapter boundary and remain unresolved in provenance verification.
- A stale Abbott source registry without `rights_policy_id` fails closed with `source registry lacks typed rights for openfda-pma-p100009-base`.
- A temporary clean exact-head worktree at `35ee072` passed the recorded 11-test M1/F3 check; the clean worktree was removed after verification.

The committed-code Philips r5 run is an inspectable local engineering output:

| Measure | Result |
|---|---:|
| Cases | 3 |
| Product-level disclosed links | 7 |
| History versions per case | 1 and 2 |
| Actual search calls | 3 |
| Returned lexical candidates | 0 |
| Provider calls | 0 |
| Paid cost | USD 0.00 |

The corrected review packet uses the sourced local evaluator-only family mapping rather than the company-group file. It contains 11 queries, 31 patents, 341 review pairs, 341 explicitly unjudged pairs, 0 semantic labels, 4 company groups, and a final holdout consisting of the 3 Stryker queries. Its family status is `SOURCED_LOCAL_EVALUATOR_MAPPING_ONLY`.

## Reproduction and verification

Commands run in this worktree:

```text
rtk proxy python -m pytest -q tests/test_healthtech_repairs.py
rtk proxy python -m pytest -q tests/test_healthtech_cook.py tests/test_healthtech_philips_dossiers.py tests/test_healthtech_philips_cohort.py tests/test_healthtech_review_packet.py tests/test_healthtech_judgment_submission.py
rtk proxy python -m py_compile src/patent_to_pilot/healthtech/rights.py src/patent_to_pilot/healthtech/abbott.py src/patent_to_pilot/healthtech/cook.py src/patent_to_pilot/healthtech/philips.py tests/test_healthtech_repairs.py
```

All three commands exited `0`. The only observed warning was the existing `fitz` deprecation warning. The Philips r5 output was produced by the already-verified local dossier runner at code commit `35ee072`; its manifest and receipt are referenced below. No network or provider call was made by this package.

## Evidence and hashes

- Philips r5 run manifest: `results/healthtech/ht-philips-dossiers-20261029-r5/manifest.json`; SHA-256 `c5a7fce38d02f805f0a651e443c605838c2204aa44cf6ba4268915b4bc7387b5`.
- Philips r5 resource receipt: `results/healthtech/ht-philips-dossiers-20261029-r5/receipt.json`; SHA-256 `17d7703a4651e5253e3ee5f77bf948c7834a110cf0aa7e30c045e6ab802a1f4a`.
- Philips cohort manifest: `results/healthtech/ht-philips-cardiovascular-20261029-r2/manifest.json`; SHA-256 `60b37a6df4e5f84c87220c00e2a6e243507ee7214c54f1870047486aa462273f`.
- Corrected review packet: `results/healthtech/ht-relevance-review-20261029-r2-philips/packet.json`; SHA-256 `21df358e9b1f387d4b4f1a6c33c94e38abff7ccf15b39df746fba3acec05a206`.
- Review family mapping: `results/healthtech/ht-google-family-mapping-20261029-r2-philips/family-mapping.json`; SHA-256 `f9637b3c7ea43bed86139293453bee95ecdaa717400f7266b3f5e2ca2bb470d2`.
- `src/patent_to_pilot/healthtech/rights.py`: `8ed61de970d2afa416b57d4fba70f6ca08955fe90045db66b80700236bf85385`.
- `src/patent_to_pilot/healthtech/abbott.py`: `e1bb25420620808987379cc602352754ecd6bd09968625c9c67aed7d55ffd13d`.
- `src/patent_to_pilot/healthtech/cook.py`: `82dc43602d1434226f72984a9f31a725d6b4d5e0dfb4fa9fbf1e017368100074`.
- `src/patent_to_pilot/healthtech/philips.py`: `b0dbcd5e0e4e6ea37d011809af67c968648ce4f2f513a8b3f228e591d105b410`.
- `tests/test_healthtech_repairs.py`: `0291d6e3453e85e9d16c4f3bf38d038b9a94c12a2d86a5924ba1032468f109f7`.

## Rights, privacy, and research limits

Philips marking material and Google-derived patent text remain local-only. The packet carries source IDs, revisions, locators, and hashes but intentionally does not copy restricted runtime patent content. Product-level disclosure rows are not claim-level semantic relevance gold. Unlisted pairs remain `UNJUDGED`, never negative. The packet does not establish exhaustive recall, stable generalization, clinical suitability, FTO, patent validity, investment merit, user validation, or publication readiness.

No paid inference, live-provider execution, semantic adjudication, statistical significance test, clinical/FTO review, customer study, deployment, outreach, or public raw-data release was performed.

## Handoff

The next discriminating step is to obtain or authorize a rights-cleared semantic device-patent judgment source with explicit labels, source revision/hash, intended-use policy, adjudicator role, exact locators, multiple independent company/family groups, and a predeclared untouched final holdout. Apply `ht-relevance-judgment-cohort-v1` without changing the frozen denominator or converting unjudged pairs into negatives, then rerun the frozen controls. Keep live/provider HT-B4, Bridge, public raw-data release, deployment, outreach, and Claude UX/UI paused.

See `verification.json`, `experiment-ledger.json`, `run-summary.json`, and `NEXT_ACTIONS.md` for the machine-readable record and continuation state.
