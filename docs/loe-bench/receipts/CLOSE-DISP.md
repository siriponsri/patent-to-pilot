# CLOSE-DISP | Research reporting dispositions

Branch `loe/CLOSE-DISP`, evidence cut `bc4dc19e74c97a6b5c9ca2692e27574916947cd3`. This receipt is the executor handoff and project memory for the card. The Planner owns integration. The [research completion checklist](../RESEARCH-COMPLETION.md) assigns the C8, reproducibility and Track B checks. The [benchmark card](../BENCHMARK-CARD.md) provides the reviewer entry point.

| Item | Status | Evidence | Denominator |
| --- | --- | --- | --- |
| Registered C8 hash target | SHORT | [Inventory](#c8-claim-inventory) finds 32 URL-only Thai FDA NDI claims. | 1,757/1,789 material claim instances in 32 development dossiers |
| Product URL-or-hash traceability | MET | [PRD1 contract](../../product/PRD1.md) and the rerun of the dossier audit | 1,789/1,789 |
| Benchmark card and restricted-input route | MET | [Card](../BENCHMARK-CARD.md) links frozen source records, rights and access routes. | One benchmark card |
| Independent exact-input historical restoration | UNAVAILABLE | [Recovery record](#historical-aggregate-reporting-and-recovery) documents the controlled route and archive gap. | Two historical horizon panels |
| Manual development tie | MET | [B1 calculation](#development-boundary-tie) agrees with FREEZE. | 544 rows, 108 slots, 50 events, 12 boundary ties |
| Development missing-patent check | MET | [Feature check](#missing-patent-check) distinguishes unknown and zero listing counts. | 547 TRAIN, 2,161 and 1,083 validation rows |
| Development pre-dated-NDA exclusions | MET | [Eligibility audit](#pre-dated-nda-exclusions) finds one distinct key. | 1/987 TRAIN, 4/4,232 12m validation candidates, 2/2,118 24m validation candidates |
| Historical C′ pre-dated-NDA exclusions | UNAVAILABLE | [SCORE aggregate](#historical-aggregate-reporting-and-recovery) combines all prior approvals. | 11,398 and 10,004 candidates, including 6,139 and 5,365 prior-ANDA exclusions |
| Development calibration bin means | MET | [Bin tables](#validation-calibration-bins) match frozen occupancy and reconcile Brier and ECE. | Three arms × two horizons × ten bins, 2,161 or 1,083 rows per arm |
| Historical C′ calibration bin means | UNAVAILABLE | [Committed counts](#historical-aggregate-reporting-and-recovery) and pooled metrics cannot recover the full tables. | Three arms × two horizons × ten bins, 5,259 or 4,639 rows per arm |
| Development predictor distributions | MET | [TRAIN and validation tables](#development-predictor-distributions) report numeric, binary and graph features. | 547, 2,161 and 1,083 rows, with per-feature counts |
| Historical C′ published predictor distributions | MET | [Aggregate table](#historical-aggregate-reporting-and-recovery) sums published missingness and graph counts. | 5,259 and 4,639 scored rows |
| Historical C′ remaining predictor distributions | UNAVAILABLE | [Aggregate limits](#historical-aggregate-reporting-and-recovery) leave continuous quantiles and non-missing feature levels unavailable. | 5,259 and 4,639 scored rows |
| Track B timing table | MET | [Recount](#track-b-coverage-check) and benchmark-card link | 21 reference-name groups, 96 351(k) BLAs |

## C8 claim inventory

**SHORT under registered C8.** The audit covers 1,757/1,789 claim instances (98.21%) with at least one identifiable, hash-backed citation. All 1,789/1,789 satisfy the product audit, which accepts a resolvable URL in place of the hash. The registered denominator is every material claim in the 32 post-EVP development dossiers, counted once per dossier claim ID across both languages. Repeated statements in different cutoff/horizon dossiers count separately. Checklist actions, reference entries and the separate outcome reveal are outside the `claims` array. An explicit unknown status remains a material claim and counts toward the denominator. The gap is 32/1,789. [C8 protocol](../PREREGISTRATION.md#secondary-and-exploratory-analyses) · [Product contract](../../product/PRD1.md) · [Audit implementation](../../../product/mwd/audit.py)

The [PRD1 receipt](PRD1.md) recorded 1,688/1,720 hash-backed with its original Thai status fallback. [UIBUILD](UIBUILD.md) fixed the percent-encoded [EVP fragment](../../product/evidence/) lookup and merged dated evidence. The 1,757/1,789 count is for that rebuilt development inventory. Each of the 32 residual claims below is `th-fda-status`, an unknown registration status, with one source ID. Each cites [Thai FDA NDI](https://ndi.fda.moph.go.th/drug_info), version 2026-11-28. Its exact locator records that the robots connection failed, the public endpoint timed out and the case search was never submitted. Each `sha256` is null. There was no case-response payload to hash. The strict target applies to every listed row, including the repeated instances. [EVP access dispositions](EVP.md#c7--current-thai-and-asean-lookup)

Dossier IDs below identify `product/demo/data/dossier-<ID>.json` at the evidence revision. Claim IDs identify the affected entries within those files.

| Development dossier ID | Claim ID | Source ID |
| --- | --- | --- |
| `U-82VFR53I78-2012-01-01-12m` | `th-fda-status` | `ndi-U-82VFR53I78` |
| `U-82VFR53I78-2013-01-01-12m` | `th-fda-status` | `ndi-U-82VFR53I78` |
| `U-82VFR53I78-2013-01-01-24m` | `th-fda-status` | `ndi-U-82VFR53I78` |
| `U-82VFR53I78-2014-01-01-12m` | `th-fda-status` | `ndi-U-82VFR53I78` |
| `U-82VFR53I78-2014-01-01-24m` | `th-fda-status` | `ndi-U-82VFR53I78` |
| `U-82VFR53I78-2015-01-01-12m` | `th-fda-status` | `ndi-U-82VFR53I78` |
| `U-A8910SQJ1U-2012-01-01-12m` | `th-fda-status` | `ndi-U-A8910SQJ1U` |
| `U-A8910SQJ1U-2013-01-01-12m` | `th-fda-status` | `ndi-U-A8910SQJ1U` |
| `U-A8910SQJ1U-2013-01-01-24m` | `th-fda-status` | `ndi-U-A8910SQJ1U` |
| `U-A8910SQJ1U-2014-01-01-12m` | `th-fda-status` | `ndi-U-A8910SQJ1U` |
| `U-A8910SQJ1U-2014-01-01-24m` | `th-fda-status` | `ndi-U-A8910SQJ1U` |
| `U-AZV954TZ9N-2012-01-01-12m` | `th-fda-status` | `ndi-U-AZV954TZ9N` |
| `U-AZV954TZ9N-2013-01-01-12m` | `th-fda-status` | `ndi-U-AZV954TZ9N` |
| `U-AZV954TZ9N-2013-01-01-24m` | `th-fda-status` | `ndi-U-AZV954TZ9N` |
| `U-AZV954TZ9N-2014-01-01-12m` | `th-fda-status` | `ndi-U-AZV954TZ9N` |
| `U-AZV954TZ9N-2014-01-01-24m` | `th-fda-status` | `ndi-U-AZV954TZ9N` |
| `U-AZV954TZ9N-2015-01-01-12m` | `th-fda-status` | `ndi-U-AZV954TZ9N` |
| `U-OCY3U280Y3-2012-01-01-12m` | `th-fda-status` | `ndi-U-OCY3U280Y3` |
| `U-OCY3U280Y3-2013-01-01-12m` | `th-fda-status` | `ndi-U-OCY3U280Y3` |
| `U-OCY3U280Y3-2013-01-01-24m` | `th-fda-status` | `ndi-U-OCY3U280Y3` |
| `U-OCY3U280Y3-2014-01-01-12m` | `th-fda-status` | `ndi-U-OCY3U280Y3` |
| `U-OCY3U280Y3-2014-01-01-24m` | `th-fda-status` | `ndi-U-OCY3U280Y3` |
| `U-QXS94885MZ-2012-01-01-12m` | `th-fda-status` | `ndi-U-QXS94885MZ` |
| `U-QXS94885MZ-2013-01-01-12m` | `th-fda-status` | `ndi-U-QXS94885MZ` |
| `U-QXS94885MZ-2013-01-01-24m` | `th-fda-status` | `ndi-U-QXS94885MZ` |
| `U-QXS94885MZ-2014-01-01-12m` | `th-fda-status` | `ndi-U-QXS94885MZ` |
| `U-QXS94885MZ-2014-01-01-24m` | `th-fda-status` | `ndi-U-QXS94885MZ` |
| `U-U188XYD42P-2012-01-01-12m` | `th-fda-status` | `ndi-U-U188XYD42P` |
| `U-U188XYD42P-2013-01-01-12m` | `th-fda-status` | `ndi-U-U188XYD42P` |
| `U-U188XYD42P-2013-01-01-24m` | `th-fda-status` | `ndi-U-U188XYD42P` |
| `U-U188XYD42P-2014-01-01-12m` | `th-fda-status` | `ndi-U-U188XYD42P` |
| `U-U188XYD42P-2014-01-01-24m` | `th-fda-status` | `ndi-U-U188XYD42P` |

## Development boundary tie

Used B1 on 1 Jan 2014 at 24 months, a committed validation cutoff also used by the evidence pilot. The [development queue](../../../product/demo/data/queue-2014-01-01-24m.json) gives 544 scores and 50 events. Tallying at the native B1 boundary score `0.13155674307411053` yields 97 rows above it (14 events), 12 tied (2 events), and 435 below (34 events).

By hand, `floor(544/5) = 108` slots. Assign weight 1 above and 0 below. Each tied row receives `(108 − 97)/12 = 11/12`. The weights sum to `97 + 12 × 11/12 = 108`. Expected hits are `14 + 2 × 11/12 = 95/6 = 15.833333`. Recall is `(95/6)/50 = 31.6667%` and precision is `(95/6)/108 = 14.6605%`. This matches the tie block, expected hits, recall and precision in the [development aggregate manifest](../../../loe-bench/data/FREEZE_DEV_SCORES_MANIFEST.json) and the queue allocation in the [FREEZE report](../../../loe-bench/data/FREEZE_dev_report.json). The product's `in_queue` field is a lexical M3 queue.

## Guarded development replay

Before recomputing, fixed the primary TRAIN and validation cells from the [frozen configuration](../../../loe-bench/data/FROZEN_CONFIG.json), the existing feature and calibration definitions, and the strict date comparison below. Used Python 3.12.10 and NumPy 2.5.4. The S0, Orange Book, PIV and court manifest LF hashes matched the configuration. The guarded reader verified source inputs and reproduced the frozen raw S0/GSRS digest inventory and edition-availability metadata. The development readers excluded approvals after 1 Jan 2016 before decoding outcomes and used cutoffs earlier than 2017. All outputs from this check were aggregates. [Guard](../../../loe-bench/scripts/c3_dev_guard.py) · [Previously verified replay](C3b.md)

To repeat on permitted development inputs, use the [guarded development input adapter](../../../loe-bench/scripts/devx_run.py) with the NDA wrapper in [FREEZE score export](../../../loe-bench/scripts/freeze_dev_scores.py). Build `PRIMARY` partitions only and use the replay's embargo check. Apply `freeze_run.inner_fits` to TRAIN and `t1v3_run.native` to validation, with the observation limit set to the day before the first validation cutoff. Use the fitted sigmoid on the native logit. The replay matched TRAIN and validation row/event counts, frozen calibrator parameters, point queue tables and all six validation bin occupancies. Recomputed Brier and ECE matched within `1e-14`. [Frozen evaluation code](../../../loe-bench/scripts/freeze_run.py) · [Frozen aggregate](../../../loe-bench/data/FREEZE_dev_report.json)

### Pre-dated-NDA exclusions

A pre-dated-NDA exclusion is a dated-`TYPE 1` candidate with its first linked final ANDA strictly earlier than its first dated original final NDA. The cohort builder excludes such a history through its prior-ANDA rule. The broader prior-ANDA count includes approvals up to and including the cutoff. One distinct qualifying key accounts for all five cutoff instances in the union of the development schedule. There were zero same-day first NDA/ANDA pairs among the prior-ANDA exclusions at each cutoff. [Eligibility and outcome construction](../../../loe-bench/loe_bench/dataset.py)

| 1 January cutoff | Partition and horizons | Dated-`TYPE 1` candidates | All prior-ANDA exclusions | First ANDA earlier than first NDA |
| --- | --- | ---: | ---: | ---: |
| 2010 | TRAIN, 12m and 24m | 987 | 440 | 1 |
| 2012 | Validation, 12m | 1,019 | 486 | 1 |
| 2013 | Validation, 12m and 24m | 1,048 | 509 | 1 |
| 2014 | Validation, 12m and 24m | 1,070 | 526 | 1 |
| 2015 | Validation, 12m | 1,095 | 550 | 1 |

The 12-month validation totals are 4/4,232 candidate cutoff rows, or 4/2,071 within the prior-ANDA exclusions. The 24-month totals are 2/2,118, or 2/1,035 within prior-ANDA exclusions. The shared TRAIN cutoff contributes 1/987 in each horizon. These counts depend on linking and date coverage in the guarded source.

### Missing-patent check

Every missing patent count in the development partitions was a `NOT_LISTED` key in a fresh edition. Each encoded zero count with its missing bit set and also had missing expiry. Known-zero counts came from linked products with no observed patent number in the admitted edition. All positive counts had a dated expiry feature. All rows lacked the earliest patent submission feature. The zeros describe the archived feature representation. They cannot establish patent absence beyond the linked listing. [Feature encoding](../../../loe-bench/loe_bench/t2_features.py) · [Existing missingness fixture](../../../loe-bench/loe_bench/tests/test_t2.py#L138)

| Development partition | Rows | Unknown listing count | Known zero | Positive count | Expiry missing | Earliest submission missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TRAIN, shared across horizons | 547 | 4 | 253 | 290 | 257 | 547 |
| Validation, 12 months | 2,161 | 36 | 1,034 | 1,091 | 1,070 | 2,161 |
| Validation, 24 months | 1,083 | 26 | 512 | 545 | 538 | 1,083 |

### Validation calibration bins

Each cell gives row count / mean calibrated probability / observed event mean as an exact event fraction. Empty bins have undefined means. Each arm sums to 90 events in 2,161 rows at 12 months and 91 in 1,083 at 24 months.

| 12 months, probability interval | B1 | M1 | M3 |
| --- | --- | --- | --- |
| `[0.0, 0.1)` | 2,161 / 0.047489 / 90/2161 | 2,111 / 0.046357 / 76/2111 | 2,095 / 0.047059 / 72/2095 |
| `[0.1, 0.2)` | 0 / — / — | 50 / 0.112877 / 14/50 | 66 / 0.115996 / 18/66 |
| `[0.2, 0.3)` | 0 / — / — | 0 / — / — | 0 / — / — |
| `[0.3, 0.4)` | 0 / — / — | 0 / — / — | 0 / — / — |
| `[0.4, 0.5)` | 0 / — / — | 0 / — / — | 0 / — / — |
| `[0.5, 0.6)` | 0 / — / — | 0 / — / — | 0 / — / — |
| `[0.6, 0.7)` | 0 / — / — | 0 / — / — | 0 / — / — |
| `[0.7, 0.8)` | 0 / — / — | 0 / — / — | 0 / — / — |
| `[0.8, 0.9)` | 0 / — / — | 0 / — / — | 0 / — / — |
| `[0.9, 1.0]` | 0 / — / — | 0 / — / — | 0 / — / — |

| 24 months, probability interval | B1 | M1 | M3 |
| --- | --- | --- | --- |
| `[0.0, 0.1)` | 884 / 0.074671 / 58/884 | 206 / 0.072071 / 3/206 | 197 / 0.062793 / 2/197 |
| `[0.1, 0.2)` | 199 / 0.108288 / 33/199 | 599 / 0.142279 / 39/599 | 570 / 0.140134 / 34/570 |
| `[0.2, 0.3)` | 0 / — / — | 230 / 0.240031 / 34/230 | 248 / 0.240945 / 33/248 |
| `[0.3, 0.4)` | 0 / — / — | 40 / 0.340286 / 13/40 | 53 / 0.334461 / 17/53 |
| `[0.4, 0.5)` | 0 / — / — | 6 / 0.431539 / 2/6 | 12 / 0.429780 / 4/12 |
| `[0.5, 0.6)` | 0 / — / — | 0 / — / — | 1 / 0.537945 / 1/1 |
| `[0.6, 0.7)` | 0 / — / — | 1 / 0.666953 / 0/1 | 1 / 0.604879 / 0/1 |
| `[0.7, 0.8)` | 0 / — / — | 1 / 0.755264 / 0/1 | 1 / 0.700922 / 0/1 |
| `[0.8, 0.9)` | 0 / — / — | 0 / — / — | 0 / — / — |
| `[0.9, 1.0]` | 0 / — / — | 0 / — / — | 0 / — / — |

### Development predictor distributions

Numeric cells give the number summarized, then minimum / Q1 / median / Q3 / maximum using linear quantiles. Orange Book numeric summaries exclude rows with the corresponding missing bit set. Breadth counts use the encoded predictor across all rows, with their missing bits below. Age squared uses the model scale (`age_years² / 10`). The model also uses a horizon-specific logit derived from the B1 age table. The table describes the underlying age predictor.

| Numeric predictor | TRAIN (547 rows) | 12m validation (2,161) | 24m validation (1,083) |
| --- | --- | --- | --- |
| `age_years` | 547 · 0.1259/7.4511/13.2895/29.1006/67.6523 | 2,161 · 0.0027/7.1704/15.6194/31.2526/72.6516 | 1,083 · 0.0027/7.1828/15.9233/31.0171/71.6523 |
| `age_sq` | 547 · 0.0016/5.5518/17.6612/84.6851/457.6833 | 2,161 · 0/5.1415/24.3967/97.6723/527.8256 | 1,083 · 0/5.1592/25.3553/96.2061/513.4051 |
| `n_nda_prior` | 547 · 1/1/1/2/7 | 2,161 · 1/1/1/2/9 | 1,083 · 1/1/1/2/9 |
| `nce_remaining_years` | 543 · 0/0/0/0/4.7283 | 2,125 · 0/0/0/0/4.8761 | 1,057 · 0/0/0/0/4.6626 |
| `other_exclusivity_remaining_years` | 543 · 0/0/0/0/6.6366 | 2,125 · 0/0/0/0/9.5962 | 1,057 · 0/0/0/0/6.8145 |
| `listed_patent_count` | 543 · 0/0/1/3/24 | 2,125 · 0/0/1/3/34 | 1,057 · 0/0/1/3/32 |
| `years_to_last_patent_expiry` | 290 · -1.5003/4.2163/7.5866/10.3101/19.0719 | 1,091 · -1.5031/3.6112/7.4278/12.1355/18.5051 | 545 · -1.5031/3.447/7.1047/11.9863/18.5051 |
| `years_since_earliest_patent_submission` | 0 · — | 0 · — | 0 · — |
| `strength_count` | 547 · 0/1/2/3/14 | 2,161 · 0/1/2/3/26 | 1,083 · 0/1/2/3/25 |
| `form_route_count` | 547 · 0/1/1/1/4 | 2,161 · 0/1/1/1/5 | 1,083 · 0/1/1/1/5 |

Binary counts give the number of ones. The denominators include both observed and missing encodings. Graph verdicts are the three M3 indicator counts, with separate TRAIN columns by horizon.

| Binary predictor | TRAIN (547 rows) | 12m validation (2,161) | 24m validation (1,083) |
| --- | ---: | ---: | ---: |
| `nme` | 547 | 2,161 | 1,083 |
| `orphan` | 94 | 458 | 233 |
| `priority` | 250 | 985 | 494 |
| `oral` | 0 | 0 | 0 |
| `injectable` | 0 | 0 | 0 |
| `nce_remaining_years_missing` | 4 | 36 | 26 |
| `other_exclusivity_remaining_years_missing` | 4 | 36 | 26 |
| `listed_patent_count_missing` | 4 | 36 | 26 |
| `years_to_last_patent_expiry_missing` | 257 | 1,070 | 538 |
| `years_since_earliest_patent_submission_missing` | 547 | 2,161 | 1,083 |
| `challenge_present` | 74 | 251 | 95 |
| `challenge_missing` | 11 | 1,474 | 988 |
| `strength_missing` | 18 | 94 | 55 |
| `form_route_missing` | 4 | 36 | 26 |

| Graph verdict counts | 12m TRAIN (547) | 24m TRAIN (547) | 12m validation (2,161) | 24m validation (1,083) |
| --- | ---: | ---: | ---: | ---: |
| BLOCKED | 231 | 202 | 584 | 181 |
| CONTESTED | 295 | 310 | 1,490 | 847 |
| OPEN | 21 | 35 | 87 | 55 |

## Historical aggregate reporting and recovery

The [SCORE aggregate](../../../loe-bench/data/SCORE_CPRIME_RESULTS.json) has LF SHA-256 `38f65240b57a4662349d3bdc89fd026908d888bdb2cfcb1ed63f430ed845d932`. Summing `horizons → eligibility_and_coverage` across the committed annual cutoffs gives these predictor and evidence distributions. A drug can contribute at several cutoffs. Compute each binary missingness complement from its column denominator.

| Published count | C′ 12 months (5,259 rows) | C′ 24 months (4,639 rows) |
| --- | ---: | ---: |
| Orange Book FRESH / NOT_LISTED | 5,181 / 78 | 4,567 / 72 |
| Graph BLOCKED / CONTESTED / OPEN | 2,152 / 2,908 / 199 | 1,674 / 2,687 / 278 |
| Patent listing count missing | 78 | 72 |
| Last patent expiry missing | 2,600 | 2,320 |
| Earliest patent submission missing | 3,252 | 2,965 |
| NCE remaining duration missing | 78 | 72 |
| Other exclusivity duration missing | 78 | 72 |
| Challenge observation missing | 588 | 586 |
| Form/route breadth missing | 78 | 72 |
| Strength breadth missing | 212 | 190 |

The two horizons record 6,139 and 5,365 prior-ANDA exclusions among 11,398 and 10,004 dated-`TYPE 1` cutoff candidates. That aggregate includes all approvals dated on or before the cutoff. It supplies no split by first NDA date, so C′ pre-dated-NDA exclusion totals are **UNAVAILABLE**. The committed calibration counts give bin occupancy. B1 at 12 months put every case in the first bin, so the observed mean there is 202/5,259 (0.038410). The C′ aggregate gives no per-bin sum of probabilities or per-bin event counts for the other populated panels. A pooled Brier score and absolute ECE do not identify the missing means. A full table of C′ bin means, continuous predictor distributions and non-missing feature levels is **UNAVAILABLE** from the committed aggregates. Filling these fields requires a custodian-authorized aggregate release.

The benchmark card links the immutable source/code revision, the publisher routes and the protected-input custodian route. The [SCORE receipt](SCORE.md#private-outputs-and-verification) documents a prior same-project replay of native recall from private exports. Independent restoration from exact historical inputs and an independently retrievable historical dataset archive are **UNAVAILABLE** for this card. A prospective forecast package follows its own [release and scoring procedure](../HOW-TO-SCORE-TRACK-A.md).

## Track B coverage check

Recounted the [committed CSV](../../../loe-bench/data/trackB_first_biosimilar.csv) at LF SHA-256 `48515a2edf440bf8471a56e3781521f1e37f23510464e49134fe8a62b7bf89f2`. There are 21 reference proper-name rows, with 96 distinct 351(k) BLAs and 54 listed interchangeable on the BLA counts in the table. Eight rows list multiple reference BLAs. Earliest listed first approval is 6 Mar 2015 and the latest is 15 May 2026. The October 2026 source snapshot has 2,270 rows, of which 261 are 351(k), with raw SHA-256 `f688373c4f1fd274fbfad55d2f7228d00dcea54672f2f17348c5c107ab9fadf1`. [Publisher route and digest](../../../loe-bench/data/PURPLEBOOK_FILES.json) · [E3 definitions and limitations](E3.md)

## Verification and Planner handoff

- `py -3.12 -m pytest tests/test_org_adaptive_terminology.py -q` passed 2 tests, exit 0.
- From `loe-bench/`, `py -3.12 -m pytest loe_bench/tests/test_t2.py -q -k no_record_and_incomplete_expiry` passed the existing fixture, exit 0.
- `py -3.12 -B -m product.mwd.audit --data-dir product/demo/data` replayed URL-or-hash coverage successfully, exit 0. The first supplementary inventory display tried to read a nonexistent claim `status` field. Repeating the inventory against the claim IDs and source records recovered all 32 exceptions and reconciled to the audit.
- Checked 59 relative links, the correspondence of all 32 listed claim instances to their source dossiers, calibration row and event totals for all six development panels, and all 14 dispositions.
- The replay used local CPU and read-only development source access. Historical C′ evidence came from the committed aggregate only.

For integration, retain the registered C8 shortfall alongside the product audit and cite the benchmark card and this receipt in the Planner's closeout records. An authorized custodian would need to release the missing historical aggregate fields or arrange exact-input restoration. The development findings supply their own denominators and replay checks.
