# FIX2b | Active-moiety linkage

## Result

**Implemented. All 11 previously observed FIX2 splits now link at their cited product anchors.** The new development audit found **0 false merges, 1 false split, 2 unresolved and 57 supported groupings** among 60 keys. The split was bupivacaine hydrochloride with epinephrine versus epinephrine bitartrate. The observed split fraction is 1/60 (1.7%) in the held-out development frame.

| Audit | Supported | False merge | False split | Unresolved |
| --- | ---: | ---: | ---: | ---: |
| T7 design, 87 resolved | 83 | 1 | 3 | 0 |
| FIX2 design, 60 rechecked | 58 | 0 | 0 | 2 |
| FIX2b fresh development, 60 | 57 | 0 | 1 | 2 |

| Count | Legacy | FIX2 | FIX2b |
| --- | ---: | ---: | ---: |
| Entities | 2,520 | 2,504 | 2,445 |
| NME entities at 2014-01-01 | 1,092 | 1,070 | 1,070 |
| 12-month rows, development cutoffs | 11,992 | 11,756 | 11,694 |
| 24-month rows, development cutoffs | 11,992 | 11,756 | 11,694 |
| 36-month rows, development cutoffs | 11,992 | 11,756 | 11,694 |
| 12-month rows, windows ending before seal | 11,425 | 11,205 | 11,148 |
| 24-month rows, windows ending before seal | 10,861 | 10,654 | 10,603 |
| 36-month rows, windows ending before seal | 10,299 | 10,104 | 10,059 |

## Audit protocol

Use the hash-verified S0 snapshot and GSRS 2026-08-06 export from FIX2. Resolve products before aggregating approval events. Compare complete moiety sets and preserve specifically listed electrolytes. Exact normalized product ingredient sets can link compatible unresolved keys to resolved keys. Record incompatible identifier sets. The linkage uses source records without audit verdicts.

Recheck the 87 resolved T7 design rows and the 60 FIX2 audit rows as exposed design evidence. Evaluate earlier same-set and distinct-set judgments at their cited product anchors in the new key space. Review residual split, merge and unresolved cases at product level. Preserve the target grouping from the earlier audit where its evidence still supports it.

For the fresh audit, start with FIX2b keys with first NDA on or before 2014-01-01. Exclude any key sharing an application with the T7 design frame (all sampled legacy keys and cited anchor applications) or the FIX2 audit (all member and cited anchor applications). Exclude a candidate key if any of its member applications are exposed, even when the relevant product differs. Sort the remaining keys lexically. Draw 60 without replacement using Python `random.Random(20261130).sample`, with no replacement after review. Inspect the sampled membership and look across keys for aliases and overlapping identities. Classify each row as correct, false merge, false split or unresolved using native product fields, scoped FDA labels and GSRS locators. A confirmed merge takes priority over a split. Insufficient evidence stays unresolved. Report all four counts over the 60 sampled keys. This audit is single-executor adjudication of a held-out development frame.

For legacy, FIX2 and FIX2b, count entities, NME entities at 2014-01-01 and at-risk NME rows for the 1995–2016 annual January 1 grid at 12, 24 and 36 months. Also count the subset with windows ending strictly before the 2017-01-01 seal. Count eligibility directly without building labels or scoring models.

## Evidence

- The default dataset builder looks up native names and synonyms in GSRS. It distinguishes exact-name ambiguity from a known identifier. Products with the same fully resolved composition already have the same key. A union-find proposes additional links on the exact normalized full product name set, then accepts a component only when its complete identifier sets agree, any partial identifiers remain present, and the electrolyte sets match. A conflicting component is rejected as a whole, including unresolved bridges. The pinned inputs produced 176 noncanonical aliases and zero rejected components. The synthetic conflict cases exercise direct and transitive rejection. Equal resolved sets with deliberately distinct electrolyte components retain separate keys. [Conflict report](../../../loe-bench/data/FIX2b_conflicts.json) · [Counts and frozen draw](../../../loe-bench/data/FIX2b_counts.json)
- The polacrilex rule handles a singleton native resin name and a matching singleton FDA label substrate with a corroborating GSRS identifier. For the audited formulation, ANDA074507 product 001 and NDA018612 list nicotine polacrilex, the ANDA SPL lists nicotine as the active moiety, and NDA020076 lists nicotine with UNII `6M3C89ZY6R`. This label-supported step operates on source fields. [Original nicotine evidence and pinned source hash](FIX2.md#sources) · [FIX2 design recheck](../../../loe-bench/data/FIX2b_fix2_design.csv)
- The T7 design replay improves agreement from 74/87 to 83/87. The FIX2 design replay repairs all 11 splits and preserves the 47 supported cases and two unresolved cases. The fresh draw uses seed `20261130` from 1,561 eligible held-out keys after excluding 167 of 1,728 keys. The candidate screen uses normalized native names, resolved key components, and moiety targets of exact GSRS name candidates. The audit inspected full native product sets and FDA label or Orange Book corroboration where available. [T7 design replay](../../../loe-bench/data/FIX2b_t7_design.csv) · [FIX2 design replay](../../../loe-bench/data/FIX2b_fix2_design.csv) · [Fresh adjudication with product locators](../../../loe-bench/data/FIX2b_fresh_audit.csv)
- The input hashes cover the 2026-11-27 S0 Drugs@FDA and Orange Book snapshots and the FDA/NCATS public GSRS export dated 2026-08-06. The original rights and source references are listed in FIX2. Runtime linkage uses those public inputs. Supplemental sources below inform adjudication only. [S0 manifest](../../../loe-bench/data/S0_INPUT_MANIFEST.json) · [GSRS export and rights](FIX2.md#sources)

| Supplemental source | Edition and locator | SHA-256 |
| --- | --- | --- |
| [FDA Orange Book](https://www.fda.gov/media/71474/download) | 46th edition, A071166/001 and N018304/004 | `667506e66165928a0cac4280c62fc8a7dc8e4355960953c12cf69664e90d9575` |
| [FDA Technescan HDP label](https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/018321s025%2C017538s022lbl.pdf) | 2025, NDA 018321/S-025, Description and Drug Characteristics | `c281d04180132061f7f9b505d1b250aada370666f0f8d72c41f551f8a5ee2e26` |
| [FDA withdrawal notice](https://www.govinfo.gov/content/pkg/FR-2007-11-07/pdf/E7-21886.pdf) | 2007-11-07, 72 FR 62859, NDA 18-489 | `dcdd49e13243da43b6a71b1e8c7b81a18a6a2465606e09f50180eb5f843fa142` |

Run from `loe-bench/`. The first command generates the packets in the supplied scratch location and reproduces the tracked counts and conflict report. The three CSVs hold the executor's adjudications.

```powershell
$fix2bRoot = 'C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench'
rtk proxy python scripts/fix2_audit_b.py --raw-dir "$fix2bRoot/raw-20261127" --gsrs "$fix2bRoot/moiety/dump-public-2026-08-06.gsrs" --packet "$fix2bRoot/moiety/FIX2b_packet.json"
rtk proxy python -m unittest discover -s loe_bench/tests -t .
```

- Python 3.12.10 completed the LOE-Bench unittest suite with **88 passed**, exit 0. The existing Purple Book file-handle warnings appeared. A repeated packet run reproduced the count report, conflict report and adjudication packet byte for byte. The count report SHA-256 is `26da2dd5ab4e57b44dcd7978dcbfa88a8c16680e80acef09c048587942e4c56c`. The packet SHA-256 is `a39aca3172e95df26994b3374d79c6842a8c1f7d28138510eb3ea994f9bf09b6`. The CSV draw order, unique keys, date cutoff and row locator coverage were checked against the packet.
- From the repository root, `python -B -m pytest --tb=short --basetemp C:/Users/User/AppData/Local/Temp/ptp-fix2b-5781-check` returned 2,760 passed, 50 skipped, one xfailed and the eight allowed SACR r2/r3 supervisor-budget failures, exit 1.

## Failures and limitations

- The T7 replay retains three splits (pemetrexed sodium, alatrofloxacin and procaine penicillin G) and the earlier helium false merge. The helium oxygen-mixture records share a key already produced by FIX2. Two FIX2 design cases remain unresolved (pentetate zinc trisodium and VERARD). The new unresolved cases are Technescan HIDA and HDP, where supplied kit ingredients and prepared radiolabeled drugs represent different evidence scopes.
- The fresh audit is a single-executor estimate of the held-out key frame. The observed zero merges is sample evidence. The screen depends on names and identifiers available in the open snapshot and can miss aliases with no indexed overlap. Earlier audit cohorts and the fresh frame have different selection rules.
- Snapshot feature lookup applies the canonical aliases from the entity table. The standalone historical edition index still derives its keys directly from the edition ingredient strings and GSRS. Historical feature equivalence for the new aliases remains unverified. The 2026 release and annotations also require a documented as-of methodology decision before benchmark use.
- The protected evaluation split and preregistration seal were left intact. No model metrics were computed.

## Next action

The main planner reviews the independently drawn sample, the residual cases and the historical edition join before authorizing benchmark use. Preserve the fresh draw as exposed evidence for any subsequent resolver change.
