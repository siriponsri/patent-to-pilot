# Report: Stryker Neurovascular offline package

## Objective and scope

Extend the lawful public HealthTech development surface with a third company source and execute the existing offline retrieval baselines. The package is limited to Stryker Neurovascular products with official product-level U.S. patent marking, FDA/openFDA regulatory facts, and public patent-page metadata/text used for local retrieval.

Excluded: Bridge corpus reuse, paid inference, provider calls, clinical or FTO analysis, public raw-data release, claim-level relevance judgment, family inference without a source, and final scientific generalization.

## Source and rights ledger

| Source | Role | Local use | Product display / redistribution |
|---|---|---|---|
| openFDA PMA `P180031` | NeuroForm Atlas regulatory record | Allowed with attribution | Allowed only for reviewed normalized fields with attribution |
| openFDA 510(k) `K252694` | Target XL regulatory record | Allowed with attribution | Allowed only for reviewed normalized fields with attribution |
| openFDA 510(k) `K223305` | Trevo ProVue regulatory record | Allowed with attribution | Allowed only for reviewed normalized fields with attribution |
| Stryker neurovascular marking page | Evaluator-only product-level disclosure | Local snapshot and offline evaluation | Blocked locally pending separate clearance |
| Google Patents pages | Patent document acquisition for retrieval | Local snapshot and offline evaluation | Blocked locally for raw HTML/extracted text |

The typed policy catalog is in `rights-matrix.json`; the structural verifier resolved the Stryker disclosure policy for all 13 evidence rows.

## Cohort freeze

The predeclared rows are NeuroForm Atlas Stent System, Target XL 360 Soft Detachable Coils, and Trevo ProVue Retrievers. The resulting candidate universe is 13 unique grant documents. Exact-patent groups are conservative single-row groups because the three selected rows have no shared exact document in this extract. All rows map to Stryker Neurovascular, so company-held-out sensitivity is not estimable. Family mapping is unknown and no final holdout is claimed.

Runtime JSON contains FDA metadata and patent text/metadata only. Evaluator JSON contains disclosed links and per-link source locators. A runtime validator rejects disclosure-source IDs, evaluator fields, and missing exclusion declarations before the runtime artifact is written.

## Retrieval results

| Method | Queries | Failures | Recall@10 | Recall@20 | Query calls | Rerank pairs |
|---|---:|---:|---:|---:|---:|---:|
| HT-B0a | 3 | 0 | 0.8190 | 1.0000 | 3 | 0 |
| HT-B0b | 3 | 0 | 0.9524 | 1.0000 | 3 | 0 |
| HT-B1 | 3 | 0 | 0.8381 | 1.0000 | 3 | 39 |
| HT-B2 | 3 | 0 | 0.8381 | 1.0000 | 12 | 156 |
| HT-B3 | 3 | 0 | 0.8857 | 1.0000 | 5 | 65 |

`K=20` is above the 13-document candidate universe and is therefore ceiling-limited. The rows measure known-link recovery against product-level disclosed relationships only; they are not exhaustive recall or a lower bound on exhaustive recall.

## Verification

- Focused parser, typed-policy, and runtime-separation tests passed before acquisition.
- The two-file HealthTech repair/pre-live regression pass completed with exit code 0 after implementation changes.
- Compile checks passed for the affected scripts and the HealthTech evaluation package.
- Acquisition stayed under the 40,000,000-byte transfer cap and 80,000,000-byte storage cap: 11,983,081 transferred bytes and 12,305,180 stored bytes including manifest.
- Provenance verification passed with 13/13 disclosed pairs covered and 0 unresolved rights policies.
- Baselines completed 15 method/query runs with 0 failed queries, 0 provider calls, and `$0.00` paid cost.

## Limitations and next test

This is a development-only one-company slice with unknown family mapping and no untouched holdout. The next discriminating package is a rights-cleared cohort with multiple independent companies and sourced family/group mappings, followed by a predeclared final holdout before any pooled scientific comparison. Keep Bridge, live/provider HT-B4, UI, deployment, outreach, clinical/FTO, and public raw-data release out of scope.
