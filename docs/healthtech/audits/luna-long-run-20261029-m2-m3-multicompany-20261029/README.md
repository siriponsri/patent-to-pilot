# Audit: multi-company cohort and final holdout

## Objective and scope

Compose a lawful local research cohort from the existing typed-policy Boston Scientific WATCHMAN and Stryker Neurovascular snapshots, preserve raw/canonical IDs and source hashes, predeclare a company-level final holdout, and run the shared offline HT-B0a/B0b/B1/B2/B3 methods.

This package excludes Bridge acquisition, paid inference, provider calls, public raw-data release, clinical/FTO analysis, claim-level semantic judgment, and family inference without a sourced mapping.

## Inputs and freeze

- Boston parent: `results/healthtech/ht-boston-watchman-20261028-r4`
- Stryker parent: `results/healthtech/ht-stryker-neurovascular-20261029-r1`
- Composite: `results/healthtech/ht-multicompany-20261029-r1`
- Composite counts: 5 devices, 20 patents, 26 disclosed pairs, 74 unjudged distractors, 4 exact-patent groups, 2 company groups.
- Development: both Boston WATCHMAN queries.
- Final holdout: all 3 Stryker Neurovascular queries.
- Family mapping: `UNKNOWN_NOT_ASSUMED`; exact-patent groups are carried forward from product rows only.

The composite builder is deterministic over the parent manifests. A rebuild into a fresh directory produced the same cohort hash `26e9f0ebc16721a3d6a85de8f7fad6a03a4ddb3701869bdfc84f309b03bf0dd7`.

## Commands

```text
rtk proxy python -B scripts/healthtech/compose_multicompany_cohort.py --boston-cohort results/healthtech/ht-boston-watchman-20261028-r4 --stryker-cohort results/healthtech/ht-stryker-neurovascular-20261029-r1 --output results/healthtech/ht-multicompany-20261029-r1 --holdout-company "Stryker Neurovascular"
rtk proxy python -B scripts/healthtech/verify_cohort_provenance.py --cohort results/healthtech/ht-multicompany-20261029-r1 --rights-matrix docs/healthtech/audits/luna-long-run-20261029-m2-m3-multicompany-20261029/rights-matrix.json --output docs/healthtech/audits/luna-long-run-20261029-m2-m3-multicompany-20261029/provenance-verification.json
rtk proxy python -B scripts/healthtech/run_real_baselines.py --runtime results/healthtech/ht-multicompany-20261029-r1/views/development/runtime.json --references results/healthtech/ht-multicompany-20261029-r1/views/development/references.json --groups results/healthtech/ht-multicompany-20261029-r1/views/development/groups.json --model-root data/raw/healthtech/models --output results/healthtech/ht-multicompany-baselines-20261029-dev-r2 --code-commit dbcac2f --protocol-hash 1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b --cohort-manifest-hash 678cd54c672e70ce9223ee08d19dcc6e24c1ab7663234a19e986951719415af8
rtk proxy python -B scripts/healthtech/run_real_baselines.py --runtime results/healthtech/ht-multicompany-20261029-r1/views/final_holdout/runtime.json --references results/healthtech/ht-multicompany-20261029-r1/views/final_holdout/references.json --groups results/healthtech/ht-multicompany-20261029-r1/views/final_holdout/groups.json --model-root data/raw/healthtech/models --output results/healthtech/ht-multicompany-baselines-20261029-holdout-r2 --code-commit dbcac2f --protocol-hash 1ac535330960bd86fd3d5720671309411844dab24a922cf18b4684fba7c06a7b --cohort-manifest-hash 678cd54c672e70ce9223ee08d19dcc6e24c1ab7663234a19e986951719415af8
```

## Results

At `K=10`, development recall is `0.8452 / 1.0000 / 1.0000 / 0.6905 / 1.0000` for HT-B0a/B0b/B1/B2/B3. The untouched Stryker holdout is `0.4952 / 0.7619 / 0.7905 / 0.7905 / 0.8381`.

At `K=20`, every method reports `1.0000` on both views because the frozen universe has exactly 20 patents. Those rows are ceiling-limited and are not the discriminating result.

Both runs completed all scheduled queries with zero failures, zero provider calls, and `$0.00` paid cost. Full sanitized metrics and resource counts are in `baseline-summary.json`.

## Verification and limits

Typed provenance passes for all 26 disclosed pairs across two independent disclosure sources with no unresolved policy IDs. Runtime views exclude disclosure/evaluator/split labels; the evaluator reference files are opened only after rankings are written.

This is descriptive offline development evidence. The final holdout is a single-company transfer check, not a stable generalization estimate. Product-level marking is not independent semantic relevance gold; unlisted pairs remain unjudged. Google-derived patent text and third-party marking evidence remain local-only.

See `verification.json`, `provenance-verification.json`, `protocol.json`, and `NEXT_ACTIONS.md` for machine-readable evidence and continuation boundaries.
