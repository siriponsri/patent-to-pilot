# LOE-Bench benchmark card

**Task.** Rank eligible US small-molecule drug histories for review. Each row is one active-moiety set at a cutoff, with a dated final original NDA and a dated `TYPE 1` final original NDA by that date and no linked final ANDA by that date. The event is the first linked Drugs@FDA final original ANDA (`ORIG/AP`) in `(cutoff, cutoff + horizon]`. Both classes require complete follow-up. Actual launch and freedom to operate are outside the endpoint. [Registration and updates](https://doi.org/10.17605/OSF.IO/P2SMD) · [Eligibility](PREREGISTRATION.md#unit-of-analysis-missing-data-outliers-and-weights)

| Cohort | 12 months | 24 months |
| --- | --- | --- |
| Development TRAIN | 1 Jan 2010, 547 rows, 25 event rows | 1 Jan 2010, 547 rows, 46 event rows |
| Development validation | 1 Jan 2012–2015, 2,161 rows, 90 event rows | 1 Jan 2013–2014, 1,083 rows, 91 event rows from 67 drugs |
| Historical C′ | 1 Jan 2017–2025, 5,259 rows, 803 drugs, 202 event rows from 202 drugs | 1 Jan 2017–2024, 4,639 rows, 771 drugs, 368 event rows from 202 drugs |
| Prospective Track A | 27 Nov 2026, 651 drugs, 130 slots, matures 27 Nov 2027 | Same roster and capacity, matures 27 Nov 2028 |

Historical observation ends 27 Nov 2026. Train windows close before validation begins. Track A was frozen on 28 Nov 2026. [Development freeze](receipts/FREEZE.md) · [Historical results](receipts/SCORE.md) · [Track A manifest](../../loe-bench/data/TRACKA_FREEZE_MANIFEST.json) · [Freeze tag](https://github.com/siriponsri/patent-to-pilot/tree/loe-track-a-freeze-20261127)

**Comparators and metrics.** B1 uses drug age, M1 adds dated tabular evidence, and M3 adds graph features. Rank native scores into `floor(N/5)` slots at each cutoff. Split remaining slots uniformly at a boundary tie. The fixed H1–H3 sequence compares expected event-row recall with 2,000 paired whole-drug bootstrap draws. Secondary reporting includes queue precision, distinct event-drug capture, grouped average precision, Brier, ten-bin calibration and workload/safety. Clearance failed its safety criterion. [Frozen config](../../loe-bench/data/FROZEN_CONFIG.json) · [SCORE](receipts/SCORE.md)

| Input and edition | SHA-256 inventory and recorded rights |
| --- | --- |
| openFDA Drugs@FDA and Orange Book S0, fetched 27 Nov 2026 | Per-query raw digests in the [S0 manifest](../../loe-bench/data/S0_INPUT_MANIFEST.json). Relevant API fields generally CC0 1.0 under [openFDA terms](https://open.fda.gov/terms/). |
| FDA Orange Book ZIPs and Paragraph IV archives | Edition, capture date, URL and raw hash in the [Orange Book](../../loe-bench/data/OB_EDITIONS.json) and [Paragraph IV](../../loe-bench/data/PIV_EDITIONS.json) manifests. Orange Book editions require proof of availability within the cutoff rules and six-calendar-month freshness. FDA-authored material is public domain under [FDA website policy](https://www.fda.gov/about-fda/about-website/website-policies). |
| Rai court records, Dataverse v1.0, 2021, file 4789869, and corroboration | CC0 table and public court/FDA records. Exact files, dates, URLs and digests in the [evidence manifest](../../loe-bench/data/E7_sources.json) and [publisher record](https://doi.org/10.7910/DVN/YCMKVU). |
| FDA/NCATS GSRS, 6 Aug 2026 | Identity only. Raw hash in [frozen config](../../loe-bench/data/FROZEN_CONFIG.json), `input_sha256.gsrs`. [CC0 unless noted](https://gsrs.ncats.nih.gov/licensing). |

**Access and limits.** Code, manifests and aggregates are at [the pinned revision](https://github.com/siriponsri/patent-to-pilot/tree/bc4dc19e74c97a6b5c9ca2692e27574916947cd3). Retrieve listed publisher versions or captures and match raw SHA-256. Requerying S0 may return revised bytes. Request controlled access to exact caches and historical labels through the study authors via OSF. Independent historical restoration and a public historical dataset archive are **UNAVAILABLE**. NBER was excluded from the frozen replay. Earlier development use had limited personal, noncommercial access and restricted redistribution. Retrospective identities, FDA snapshot gaps, missing evidence and overlapping earlier baseline exposure limit interpretation. [NBER recipe and terms](../../loe-bench/data/E8_NBER_MANIFEST.json) · [Prospective scoring](HOW-TO-SCORE-TRACK-A.md)

**Track B.** The [first biosimilar timing table](../../loe-bench/data/trackB_first_biosimilar.csv) describes 21 proper-name reference groups and 96 distinct 351(k) BLAs in the October 2026 Purple Book snapshot (2,270 rows overall, 261 351(k) rows). It uses the earliest Original-row approval per BLA. Eight groups map to multiple 351(a) BLAs. Coverage may miss products removed before April 2020. Dates describe recorded approvals. Track B supplies no forecast evaluation. The [Purple Book manifest](../../loe-bench/data/PURPLEBOOK_FILES.json) pins raw bytes by edition and includes the public FDA download route. E3 records the general FDA public-domain policy and leaves AccessData-specific terms unverified. [Track B receipt](receipts/E3.md)

**Reviewer checks.** The [CLOSE-DISP receipt](receipts/CLOSE-DISP.md) provides the development tie, missing-patent, exclusion, calibration and predictor checks, plus the C8 claim audit.
