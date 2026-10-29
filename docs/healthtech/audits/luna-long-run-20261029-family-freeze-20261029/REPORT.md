# HT-M3 family-aware cohort freeze report

## Decision

Freeze the family-aware composite as an evaluator-side cohort artifact and preserve its split/family metadata for future analysis. Do not rerun or relabel existing retrieval baselines from this package alone.

## Inputs

- Parent composite: `results/healthtech/ht-multicompany-20261029-r3`
- Boston cohort: `results/healthtech/ht-boston-watchman-20261028-r4`
- Stryker cohort: `results/healthtech/ht-stryker-neurovascular-20261029-r1`
- Cook cohort: `results/healthtech/ht-cook-zenith-20261029-r1`
- Evaluator-only family mapping: `results/healthtech/ht-google-family-mapping-20261029-r1/family-mapping.json`
- Reviewed rights matrix: `docs/healthtech/audits/luna-long-run-20261029-cook-expansion-20261029/rights-matrix.json`

## Acceptance checks

1. Preserve canonical patent IDs and parent source provenance.
2. Add family metadata without changing runtime query, patent, or evaluator inputs.
3. Reject family groups that cross development and final holdout splits.
4. Keep unlisted device-patent pairs unjudged.
5. Verify typed rights coverage for every disclosed pair.
6. Record hashes, commands, resource boundaries, and the no-new-baseline limitation.

All six checks pass.

## Frozen artifact

Output: `results/healthtech/ht-multicompany-20261029-r3-family-r2`

- Manifest SHA-256: `1b42b7c4a52b697d9c5c4f7db4f9236b7d5d239d83584863a6ba844591adef75`
- Cohort SHA-256: `0f35a29ccc08ce5980f22dc0a3de9b1ce834a67165efa66796c157da0927d52b`
- Runtime SHA-256: `f9f61277ec95557ffd9c87528311378bdd30a83f1ea937cf30ccdb9b4de5024f`
- References SHA-256: `3f99c4e6791bf68ebd133d76960836e217de9ba51111b2d622003ab096c00e11`
- Source registry SHA-256: `beb557571fd716e5f62f1a7c672e1229712fd3375b0ee8baeb912c2b775204a8`
- Split SHA-256: `ae522ba91f6eca3f38f104fe30e1f97fb368ff7ab82ccb2280315bd93b6b4d1a`
- Family mapping SHA-256: `e4baa2e4eb1295c4abf9314fe5f2a60dd853151c7089f032801dc7fdef31f898`

## Interpretation

The freeze adds a sourced evaluator-side family grouping layer and a split leakage guard. It does not establish that patents are relevant to devices, does not convert product marking into semantic gold, and does not provide a stable generalization estimate. The final holdout remains a single-company transfer check with descriptive uncertainty only.

The existing baseline outputs were generated from the prior composite manifest. Reusing their metrics with the new family-aware manifest would mix artifacts across cohort versions, so this package intentionally stops at freeze and provenance verification.

## Resource and rights boundary

No provider calls, paid inference, neural inference, or new network acquisition occurred. The output is derived from existing local snapshots. The reviewed rights matrix resolves all `31/31` disclosed pairs, but the matrix is a use-control record rather than a redistribution grant. Raw third-party pages and evaluator-only relations remain outside the audit folder.

## Next step

Acquire or author a rights-cleared relevance-judgment cohort with multiple independent company/family groups, an untouched final holdout, frozen denominators, and explicit source provenance. Only after that freeze should a fresh baseline run and pooled scientific comparison be considered.
