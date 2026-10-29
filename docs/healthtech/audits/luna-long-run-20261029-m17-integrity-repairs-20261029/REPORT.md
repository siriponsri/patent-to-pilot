# M17 report

## Decision

Engineering and offline-development gates pass. The typed-rights migration is complete locally, the external-boundary matrix is covered, and the corrected five-method baseline run is reproducible from the frozen derived cohort. The package does not clear scientific, licensing, semantic-gold, provider, clinical/FTO, deployment, or publication gates.

## Evidence

- Migration receipt: `results/healthtech/ht-public-cohort-20261029-frozen-r2-typed/rights-migration.json`.
- Derived cohort manifest: `results/healthtech/ht-public-cohort-20261029-frozen-r2-typed/manifest.json`.
- Development protocol: `results/healthtech/ht-abbott-development-20261029-m17-r1/protocol.json`.
- Baseline receipt: `results/healthtech/ht-real-baselines-20261029-m17-r2/receipt.json`.
- Baseline frontier: `results/healthtech/ht-real-baselines-20261029-m17-r2/frontier_diagnostics.json`.
- Corrected M1 reproduction: `after-reproduction-summary.json`.

## Interpretation

HT-B0b is the highest observed macro known-link recall@20 in this three-device Abbott slice, followed by HT-B2, HT-B1/HT-B3, and HT-B0a. This ordering is descriptive only. The frozen protocol keeps unlisted pairs unjudged, and the two exact-patent groups are insufficient for an estimable group-level uncertainty claim. No method is labeled adaptive, LLM-controlled, or scientifically superior from this run.
