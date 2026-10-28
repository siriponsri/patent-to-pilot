# Rights-aware source boundary and independent cohort audit

Run id: `luna-patent-dossiers-20261028-rights-cohort`

Checked on October 28, 2026. Base commit: `630a6772463f7473bac48bb62037a53f745d8a03`. Implementation commit: `fae952e0cc519dd9e471faafbbd6cec77b5ef7dd`.

This continuation package has two bounded outcomes:

- A typed rights policy now travels with non-synthetic HealthTech sources, manifests, local exports, and source views. Product-display and redistribution requests fail closed when the recorded decision is local-only or unresolved.
- A separate Boston Scientific WATCHMAN development cohort was acquired from an official virtual patent-marking page/PDF and PMA `P130013`, then run through the same offline HT-B0a/B0b/B1/B2/B3 frontier.

## Acceptance matrix

| Package | Result | Evidence |
|---|---|---|
| Source-specific rights basis | PASS | `rights-matrix.json` records official clauses, URLs, checked date, basis hashes, intended use, and limits for openFDA, Abbott, Google-derived patent text, and Boston Scientific. |
| Typed product boundary | PASS | `SourceRights`, public-source validation, `RunManifest.rights_summary`, purpose-aware Markdown export, and purpose-aware source view. Restricted Abbott patent/disclosure surfaces raise `RightsBoundaryError`. |
| Independent non-Abbott cohort | PASS for development-only use | Two Boston WATCHMAN rows, one PMA family, seven patent documents, thirteen product-level disclosed pairs, one unjudged distractor pair, exact-overlap grouping, unknown family mapping, and no final holdout. |
| Offline frontier | PASS for bounded development run | Five methods, two devices, zero failed queries, zero provider calls, zero paid cost, raw rankings written before evaluator references were loaded. |
| Per-link disclosure provenance | PASS for Boston; legacy-only for Abbott | Boston: 13/13 reference pairs covered by exact disclosure evidence under a typed rights policy. Abbott: 61/61 pairs structurally covered, but the older cohort registry records free-text rights only. |
| Scientific generalization/public release | NOT_RUN | One company/PMA family, product-level marking only, no final holdout, Google-derived patent text remains local-only, Bridge reuse rights/cohort/split remain unresolved, and no redistribution is authorized. |

## Rights decisions

- openFDA: normalized PMA fields are allowed for local evaluation and product display/redistribution with attribution, subject to field-specific exceptions and service limits.
- Abbott product disclosures: local snapshot/evaluation only; product display and redistribution remain blocked.
- Google-derived patent HTML/text: local snapshot/evaluation only; no source-specific patent-text redistribution license was identified.
- Boston Scientific virtual patent marking: local snapshot/evaluation only; the official page documents a product-level marking relationship but does not grant a redistribution license.

The raw HTML, PDF, PMA response, and extracted patent pages remain in ignored local result folders. They are referenced by hashes and are not copied into this audit folder.

## Per-link provenance gate

`src/patent_to_pilot/evaluation/healthtech/provenance.py` and
`scripts/healthtech/verify_cohort_provenance.py` now verify the evaluator-only
boundary for each cohort. The gate checks that every disclosed pair maps to an
exact locator and quote/field, an `independent_disclosure` source, a registered
rights basis, and a patent in the frozen runtime universe. It also rejects
runtime leakage, duplicate IDs, extra or missing evidence pairs, and distractors
that overlap disclosed links.

- Boston receipt: `boston-provenance-verification.json` — `PASS`, 13/13 pairs, `TYPED_POLICY_ID`.
- Abbott receipt: `abbott-provenance-verification.json` — `PASS_WITH_LEGACY_RIGHTS`, 61/61 pairs, `LEGACY_TEXT_ONLY`.
- The Abbott receipt is structural provenance evidence only. Its older source registry must be regenerated or explicitly migrated before it is treated as a typed rights-aware artifact.

The verifier does not establish semantic relevance, claim scope, patent validity,
or redistribution permission. Unlisted pairs remain unjudged.

## Cohort and frontier

Fresh normalized cohort: `results/healthtech/ht-boston-watchman-20261028-r4/`

Fresh baseline frontier: `results/healthtech/ht-boston-baselines-20261028-r3/`

| Method | K=20 macro known-link recall | Query calls | Rerank pairs |
|---|---:|---:|---:|
| HT-B0a | 1.000000 | 2 | 0 |
| HT-B0b | 1.000000 | 2 | 0 |
| HT-B1 | 1.000000 | 2 | 14 |
| HT-B2 | 1.000000 | 8 | 56 |
| HT-B3 | 1.000000 | 2 | 14 |

These are realized development-slice values, not a generalization result. The cohort has two exact-patent-overlap devices from one applicant/PMA family and no final holdout; inferential uncertainty remains `NOT_ESTIMABLE`.

## Exact verification

```text
rtk python -B -m pytest -q -p no:cacheprovider tests/test_healthtech.py tests/test_healthtech_repairs.py tests/test_healthtech_prelive.py
PASS: 57 passed

rtk python -B -m compileall -q src/patent_to_pilot/evaluation/healthtech scripts/healthtech
PASS: exit 0

rtk python -B scripts/healthtech/verify_cohort_provenance.py --cohort results/healthtech/ht-boston-watchman-20261028-r4 --output docs/healthtech/audits/luna-patent-dossiers-20261028-rights-cohort/boston-provenance-verification.json
PASS: 13/13 Boston reference pairs covered; typed rights policy present

rtk python -B scripts/healthtech/verify_cohort_provenance.py --cohort results/healthtech/ht-public-cohort-20261028-r1 --output docs/healthtech/audits/luna-patent-dossiers-20261028-rights-cohort/abbott-provenance-verification.json
PASS_WITH_LEGACY_RIGHTS: 61/61 Abbott reference pairs covered; legacy free-text rights note only

rtk python -B scripts/healthtech/fetch_boston_watchman_cohort.py --output results/healthtech/ht-boston-watchman-20261028-r4
PASS: 2 devices, 7 patents, 13 disclosed pairs, 1 unjudged distractor pair

rtk python -B scripts/healthtech/run_real_baselines.py --runtime results/healthtech/ht-boston-watchman-20261028-r4/runtime.json --references results/healthtech/ht-boston-watchman-20261028-r4/evaluator/references.json --groups results/healthtech/ht-boston-watchman-20261028-r4/groups.json --model-root data/raw/healthtech/models --output results/healthtech/ht-boston-baselines-20261028-r3 --code-commit working-tree --protocol-hash fa8c6b531c59e5b330fb28f86207e2590cf25a9fcdd6f7bcb2b2b2b8343c9528 --cohort-manifest-hash cf2d0b6775b2b68a39b55f7023a805184a36b52b3a7f47cd02977c550d69104a
PASS: 5 methods, 2 devices, 7 patents, 13 pairs, 0 provider calls
```

Detailed machine evidence is in `verification.json`, `cohort_summary.json`, and `frontier_summary.json`.
