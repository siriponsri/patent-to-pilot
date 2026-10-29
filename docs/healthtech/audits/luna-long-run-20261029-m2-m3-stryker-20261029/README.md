# Stryker Neurovascular cohort expansion

Status: `PASS_OFFLINE_DEVELOPMENT`
Date: 2026-10-29 (Asia/Bangkok)
Base revision: `c8c5dfc09270053c5a0082aaed495dfb044288f0`
Implementation commit: `71c8d66`

## Outcome

Implemented and ran a bounded Stryker Neurovascular device-patent development cohort using the official Stryker U.S. neurovascular intervention patent-marking page, three FDA records, and public Google Patents pages retained in ignored local results only.

- Cohort: 3 named devices, 13 unique U.S. patent documents, 13 product-level disclosed pairs, 26 unjudged distractors.
- Regulatory sources: PMA `P180031`; 510(k) `K252694` and `K223305`.
- Provenance: `PASS`, typed rights policy resolved, 13/13 disclosure pairs covered.
- Groups: 3 exact-patent groups, 1 company group, family mapping `UNKNOWN_NOT_ASSUMED`, no final holdout.
- Methods: HT-B0a, HT-B0b, HT-B1, HT-B2, HT-B3; all 3/3 queries completed with zero frontier failures.
- Cost boundary: 0 provider calls and `$0.00` paid cost; no credentials or `.env` content read.

The primary runner endpoint remains descriptive development evidence. `K=20` exceeds the 13-document candidate universe, so the reported `1.0` recall rows at `K=20` are ceiling-limited. At `K=10`, macro known-link recall is `0.8190` for HT-B0a, `0.9524` for HT-B0b, `0.8381` for HT-B1, `0.8381` for HT-B2, and `0.8857` for HT-B3.

## Canonical artifacts

- Rights matrix: `rights-matrix.json`
- Structural provenance: `stryker-provenance-verification.json`
- Machine verification: `verification.json`
- Detailed report: `REPORT.md`
- Continuation note: `NEXT_ACTIONS.md`
- Ignored cohort manifest: `results/healthtech/ht-stryker-neurovascular-20261029-r1/manifest.json`
- Ignored baseline receipt: `results/healthtech/ht-stryker-baselines-20261029-r2/receipt.json`

## Executed commands

```text
rtk proxy python -B -m pytest -q tests/test_healthtech_repairs.py -k "stryker or boston_marking or public_cohort_registry"
rtk proxy python -B -m compileall -q scripts/healthtech/fetch_stryker_neurovascular_cohort.py scripts/healthtech/verify_cohort_provenance.py
rtk proxy python -B scripts/healthtech/fetch_stryker_neurovascular_cohort.py --output results/healthtech/ht-stryker-neurovascular-20261029-r1 --max-transfer-bytes 40000000 --max-storage-bytes 80000000
rtk proxy python -B scripts/healthtech/verify_cohort_provenance.py --cohort results/healthtech/ht-stryker-neurovascular-20261029-r1 --rights-matrix docs/healthtech/audits/luna-long-run-20261029-m2-m3-stryker-20261029/rights-matrix.json --output docs/healthtech/audits/luna-long-run-20261029-m2-m3-stryker-20261029/stryker-provenance-verification.json
rtk proxy python -B scripts/healthtech/run_real_baselines.py --runtime results/healthtech/ht-stryker-neurovascular-20261029-r1/runtime.json --references results/healthtech/ht-stryker-neurovascular-20261029-r1/evaluator/references.json --groups results/healthtech/ht-stryker-neurovascular-20261029-r1/groups.json --model-root data/raw/healthtech/models --output results/healthtech/ht-stryker-baselines-20261029-r2 --code-commit working-tree --protocol-hash 7dab96b735c70bcf60b99f191477c5add04d95c337d437c2d17b546e8b226cf2 --cohort-manifest-hash 25dcace7fd248ad9dc0c9f05eeefdfcd9c45d9bc1dfcc6274b9733bf129aa25b
rtk proxy python -B -m compileall -q src/patent_to_pilot/evaluation/healthtech scripts/healthtech
rtk proxy git diff --check
```

## Boundaries

The Stryker page is product-level patent-marking evidence, not claim-level semantic gold. Unlisted links remain unjudged and are not negatives. No family merge is inferred. Raw HTML, FDA snapshots, Google-derived patent HTML/text, evaluator references, and model artifacts remain local ignored data and are not staged for Git publication. This package does not establish exhaustive recall, clinical suitability, FTO, patent validity, investment merit, publication readiness, or generalization beyond the development slice.

The main Bridge study remains `BLOCKED_LOCAL` on rights, cohort reconciliation, and split reproducibility. The paid/provider branch remains `BLOCKED_LOCAL`.
