# HT M3 cross-cohort frontier comparison

- Run ID: `luna-long-run-20261029-m3-current-head-cf613c0`
- Status: `PASS`
- Scope: descriptive offline comparison only; no final scientific or generalization claim.
- Provider calls: `0`; paid cost: `$0`.

## Objective and scope

Compare the Abbott and Boston Scientific WATCHMAN development frontiers under the shared HT-B0a/B0b/B1/B2/B3 runner. The comparison reports raw recall and realized local resources, then normalizes resources per device. It does not pool scores across cohorts or treat either cohort as expert semantic gold.

## Cohort boundaries

| Cohort | Devices | Patents | Disclosed pairs | Unjudged distractor pairs | Exact-patent groups | Company groups | Final holdout |
|---|---:|---:|---:|---:|---:|---:|---:|
| Abbott | 3 | 41 | 61 | 62 | 2 | 1 | 0 |
| Boston Scientific WATCHMAN | 2 | 7 | 13 | 1 | 1 | 1 | 0 |

Abbott is descriptive with low effective group count: three devices collapse to two exact-patent groups, one company group, and unknown family mapping. Boston is also descriptive and has one exact-patent group and one company group.

## Method deltas

The delta column is Boston minus Abbott. Resource columns are realized totals per device; they are not monetary costs.

| Method | Abbott recall@20 | Boston recall@20 | Delta | Abbott query calls/device | Boston query calls/device | Abbott rerank pairs/device | Boston rerank pairs/device |
|---|---:|---:|---:|---:|---:|---:|---:|
| HT-B0a | 0.443 | 1.000 | 0.557 | 1.000 | 1.000 | 0.000 | 0.000 |
| HT-B0b | 0.662 | 1.000 | 0.338 | 1.000 | 1.000 | 0.000 | 0.000 |
| HT-B1 | 0.499 | 1.000 | 0.501 | 1.000 | 1.000 | 41.000 | 7.000 |
| HT-B2 | 0.569 | 1.000 | 0.431 | 3.000 | 4.000 | 123.000 | 28.000 |
| HT-B3 | 0.499 | 1.000 | 0.501 | 1.667 | 1.000 | 68.333 | 7.000 |

## Interpretation

- Boston reports `1.0` recall@20 for every method because `K=20` exceeds its seven-patent candidate universe. The result is a ceiling-limited development observation, not method superiority.
- Abbott provides the more informative within-cohort spread at `K=20`: HT-B0b is the highest observed method, while HT-B1, HT-B2, and HT-B3 trade additional local resources for lower or mixed recall in this slice.
- Cross-cohort recall deltas are not transportable performance estimates because the cohorts differ in size, candidate-universe depth, company/group structure, and disclosure density.
- All reported rows are offline and completed with zero recorded failures in the source frontiers. Resource values remain local execution units, not dollars.

## Limitations and next test

- No confidence intervals, company-held-out sensitivity, family-held-out sensitivity, or final-holdout estimate is reported.
- Unlisted device-patent pairs remain unjudged; distractor lists are not negative labels.
- Product-level disclosures do not establish claim-level semantic relevance or any clinical, legal, or investment conclusion.
- Next discriminating test: add a rights-cleared cohort with multiple independent company/family groups, freeze its holdout rules, and rerun the same fixed-prefix frontier before considering a scientific comparison.

## Inspectable sources

- `abbott_distractors`: `results/healthtech/ht-abbott-development-20261028-r1/distractors.json` (SHA-256 `7d009f4e556e817254c9665a62987a59fa4bdbbc098c635f75dd0fdf83773ddb`)
- `abbott_frontier`: `results/healthtech/ht-real-baselines-20261029-frozen-r1/frontier_diagnostics.json` (SHA-256 `ffdd10689c48ebdefee94ed8abef7a9099b5b44b11a24c8e20225a882baf2c0d`)
- `abbott_groups`: `results/healthtech/ht-abbott-development-20261028-r1/protocol.json` (SHA-256 `f9b1fdf43d2bfd1fc94bee58e4c91738195456202dcd0f8e228af41887f938b8`)
- `abbott_protocol`: `results/healthtech/ht-abbott-development-20261028-r1/protocol.json` (SHA-256 `f9b1fdf43d2bfd1fc94bee58e4c91738195456202dcd0f8e228af41887f938b8`)
- `abbott_receipt`: `results/healthtech/ht-real-baselines-20261029-frozen-r1/receipt.json` (SHA-256 `9ec66c0316e99219987220c6fc68a52da8f43f22ac548823ae8ac4fd0c5e3571`)
- `abbott_split`: `results/healthtech/ht-abbott-development-20261028-r1/split_manifest.json` (SHA-256 `cdd04bee5c5c3ae2d7590d3760c6d068a1b502f7c521eade099f83d4c515bad4`)
- `boston_distractors`: `results/healthtech/ht-boston-watchman-20261028-r4/distractors.json` (SHA-256 `b3b0547e635673906bcffaf6ce65084dfdfb5de60831fc319b23647ce41bd2b0`)
- `boston_frontier`: `results/healthtech/ht-boston-baselines-20261028-r3/frontier_diagnostics.json` (SHA-256 `21f5ed31810a65fb54f7905113dfa26f17cbbead3d2c3668186e7be991bf0156`)
- `boston_groups`: `results/healthtech/ht-boston-watchman-20261028-r4/groups.json` (SHA-256 `c436978b32af31412407c4e2420938e80f502167c9112a8a36aa03a7449e54ef`)
- `boston_manifest`: `results/healthtech/ht-boston-watchman-20261028-r4/manifest.json` (SHA-256 `cf2d0b6775b2b68a39b55f7023a805184a36b52b3a7f47cd02977c550d69104a`)
- `boston_receipt`: `results/healthtech/ht-boston-baselines-20261028-r3/receipt.json` (SHA-256 `f194fdce6bd44f42d932374ab80e05799a66d824209b87bd056464b2d5cffd25`)
- `boston_split`: `results/healthtech/ht-boston-watchman-20261028-r4/split_manifest.json` (SHA-256 `fa8c6b531c59e5b330fb28f86207e2590cf25a9fcdd6f7bcb2b2b2b8343c9528`)
