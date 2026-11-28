# CPRIME-DESC | Historical calibration, predictors and eligibility

On 28 November 2026 (Bangkok), the executor pushed the [analysis note](CPRIME-DESC-NOTE.md) at `87ca03bbc4d0b5a00e4e6705470ba319fb49b02c` before computation. The opened historical C′ cohort is partly exposed. These post hoc summaries used no hypothesis tests and do not change any registered decision. [SCORE](SCORE.md) · [CLOSE-DISP](CLOSE-DISP.md#historical-aggregate-reporting-and-recovery) · [Joint sign-off](../JOINT-SIGNOFF.md)

Calibration passed. C′ predictor distributions are partial and the prior-ANDA reason split is `UNAVAILABLE`. The TRAIN and VAL predictor replay recorded `PASS`.

## Inputs and authentication

The runner matched both raw SCORE export digests before decoding and checked the released schema, horizon, implementation pin, unique drug/cutoff pairs and complete cutoff schedule. It matched the six per-arm ECE occupancy vectors and the pooled Brier and ECE statistics against SCORE within the locked tolerance. Development sources used the frozen pre-2017 projections described in the analysis note. Private filenames below are relative to the read-only private root. Public JSON is hashed with LF line endings and private inputs are hashed as raw bytes.

| Input | Verified SHA-256 |
| --- | --- |
| `data/FROZEN_CONFIG.json` | `d40119189b9e3b3b319f16449ac672766d46de2272dd9579eadaa8d23eb27c39` |
| `data/SCORE_CPRIME_RESULTS.json` | `38f65240b57a4662349d3bdc89fd026908d888bdb2cfcb1ed63f430ed845d932` |
| `score/C1_scores_12m.json` | `a644f1d40271c9a59a5405b840724906332ce975854d2afedd3d22c4ded80891` |
| `score/C1_scores_24m.json` | `c3b9e51891fd8f577dfce9f7fbbfb466f25f29ae50ed4edd9d8b2d0fcbcc84e7` |
| `challenge/e7_ampyra.pdf` | `aac33d48e18f9f1a3f99cd64c743a00aec0bec2e5d957e221672d6c44e049c92` |
| `challenge/e7_pennsaid.pdf` | `ef1d22414ec0f5061248519b3101c94fade482c44b0e82cd7f238952cef18df8` |
| `challenge/e7_rai_4789869.tsv` | `abb54817c8e6fbc90077007a42bb1cd7870a64940ce3aa7a7d36d83dafaa06e5` |
| `challenge/e7_rai_metadata.json` | `4c3f680cbb251bd42a1c7be4a62bc0000783d705f8978d4e46753ef95ae12b36` |
| `challenge/e7_toviaz.pdf` | `052e33e66b483d5fa67dcf42da93038b7f031bb63850cfc9a7b7b115a60ada4b` |
| `challenge/e7_xyrem_fda.pdf` | `67b597f4d2a9c9d51de46f310f13df9ede37c1ac9f01801bd1ebd659837798d9` |
| `data/E7_sources.json` | `c2e7ad988d860fb684cffffb4607ba1d1aca575f8209e4fc18d8ee47d3709c6f` |
| `data/OB_EDITIONS.json` | `6b59c08899ab4b5b7c514544e5c9aebcf93fd6775a61502f25f9086a41e77103` |
| `data/PIV_EDITIONS.json` | `f99562f2dd3344279ff788a20fae836cacc6c0acc87b540d0e94984175bc8352` |
| `data/S0_INPUT_MANIFEST.json` | `7d40be5e2004d887480ce5f337afffd611909f26017622e90ad304a0386d2d1d` |
| `moiety/dump-public-2026-08-06.gsrs` | `07be61aea161cd212545c6cc1057a376bdbefcfc634da7ab1b4903b99f7bacad` |
| `ob_editions/ob_20091104091455.zip` | `b111f4a516428a7198a70ee5247332f4ffed6a4a1bdc80a983a4a27d40e4ca13` |
| `ob_editions/ob_20111229223919.zip` | `ba3369151cb206a335470f6cf1ae2d3095afc7c4606d314384737beade36d6a3` |
| `ob_editions/ob_20120921215526.zip` | `a0d9b654bc89e007f9f1db173ab829f01df5a041ddecb5ae31c0b194d98bf000` |
| `ob_editions/ob_20130906105914.zip` | `ef3480d71564c919864dad734464306880b34355d09aa16675aaf86786f34c6e` |
| `ob_editions/ob_20140915104404.zip` | `ebe060c313165f2d5b68202cc15ba49cbb860764ac2d38dd3be9d7a25aa78fa2` |
| `piv/1bc16f687bd4381864bf1e897878d46279e95846efd2594bb428212a8036e55b.pdf` | `1bc16f687bd4381864bf1e897878d46279e95846efd2594bb428212a8036e55b` |
| `piv/324005e2507c9da03de5f72bcb89ce335984a0b88b18ac59ac093d81fb788969.pdf` | `324005e2507c9da03de5f72bcb89ce335984a0b88b18ac59ac093d81fb788969` |
| `piv/a3e21f188d7bb0573ddece7f5572cf88a13845cbfc15eca4fc1311591cc5330f.pdf` | `a3e21f188d7bb0573ddece7f5572cf88a13845cbfc15eca4fc1311591cc5330f` |
| `raw-20261127/df_anda.jsonl` | `9dbd25202e6abe12d468e9aaf67de96a3452b5389221ac150b50e4f7ddb193a6` |
| `raw-20261127/df_nda.jsonl` | `8df16f70fbfa3b7f2d8d422699af079b7ed73530ef4ca258ad6e27f4ef4d8b61` |
| `raw-20261127/ob_anda_2010s.jsonl` | `3e1f1fd7942ebc181db70c129a17ce524b8b8468abd0bef08493ce6c685d8aaf` |
| `raw-20261127/ob_anda_pre1982.jsonl` | `a6a21eb1bd87fc0059fec90fb1b79afc3f03025ffdb735c13dd9bf6cd8102cb2` |
| `raw-20261127/ob_anda_to2009.jsonl` | `5ae88b913d442c7504a3103b18bd962053bed36e915b52d08f14e95948b9b66d` |
| `raw-20261127/ob_nda.jsonl` | `395be13e1f80a79b0eb3dbb17db7d92a500bb2ac039138c099b2fe3386b0457f` |

The [aggregate JSON](../../../loe-bench/data/CPRIME_DESC.json) has LF SHA-256 `01a4664d309de44cbdd155fcae315a7f7683ac5865c014bfb502d28195aa76d3`. Run `py -3.12 -B loe-bench/scripts/score_cprime_desc.py --write` from the repository root to reproduce it with the named inputs. The verified run used Python 3.12.10 on local CPU and kept the source rows, identifiers and labels in the private workspace.

## C′ calibration

Each panel pools all annual drug-cutoff rows for its horizon and reapplies the frozen TRAIN sigmoid. Probabilities and Wilson 95% intervals are on the 0–1 scale. The intervals use a binomial row denominator and do not adjust for repeated drugs. Counts below five, including zero, appear as `<5`. `WITHHELD` is a suppressed count of at least five. A dash denotes a suppressed or undefined statistic. Some bin occupancies were already public in SCORE.

### 12 months · B1

| Calibrated probability | Rows | Events | Mean probability | Observed rate | Wilson 95% |
| --- | ---: | ---: | ---: | ---: | --- |
| `[0.0, 0.1)` | 5,259 | 202 | 0.048217 | 0.038410 | 0.033544 to 0.043950 |
| `[0.1, 0.2)` | `<5` | `<5` | — | — | — |
| `[0.2, 0.3)` | `<5` | `<5` | — | — | — |
| `[0.3, 0.4)` | `<5` | `<5` | — | — | — |
| `[0.4, 0.5)` | `<5` | `<5` | — | — | — |
| `[0.5, 0.6)` | `<5` | `<5` | — | — | — |
| `[0.6, 0.7)` | `<5` | `<5` | — | — | — |
| `[0.7, 0.8)` | `<5` | `<5` | — | — | — |
| `[0.8, 0.9)` | `<5` | `<5` | — | — | — |
| `[0.9, 1.0]` | `<5` | `<5` | — | — | — |

### 12 months · M1

| Calibrated probability | Rows | Events | Mean probability | Observed rate | Wilson 95% |
| --- | ---: | ---: | ---: | ---: | --- |
| `[0.0, 0.1)` | 5,162 | 181 | 0.041659 | 0.035064 | 0.030382 to 0.040438 |
| `[0.1, 0.2)` | 97 | 21 | 0.111233 | 0.216495 | 0.146188 to 0.308402 |
| `[0.2, 0.3)` | `<5` | `<5` | — | — | — |
| `[0.3, 0.4)` | `<5` | `<5` | — | — | — |
| `[0.4, 0.5)` | `<5` | `<5` | — | — | — |
| `[0.5, 0.6)` | `<5` | `<5` | — | — | — |
| `[0.6, 0.7)` | `<5` | `<5` | — | — | — |
| `[0.7, 0.8)` | `<5` | `<5` | — | — | — |
| `[0.8, 0.9)` | `<5` | `<5` | — | — | — |
| `[0.9, 1.0]` | `<5` | `<5` | — | — | — |

### 12 months · M3

| Calibrated probability | Rows | Events | Mean probability | Observed rate | Wilson 95% |
| --- | ---: | ---: | ---: | ---: | --- |
| `[0.0, 0.1)` | 5,116 | 170 | 0.041423 | 0.033229 | 0.028657 to 0.038501 |
| `[0.1, 0.2)` | 143 | 32 | 0.113135 | 0.223776 | 0.163206 to 0.298799 |
| `[0.2, 0.3)` | `<5` | `<5` | — | — | — |
| `[0.3, 0.4)` | `<5` | `<5` | — | — | — |
| `[0.4, 0.5)` | `<5` | `<5` | — | — | — |
| `[0.5, 0.6)` | `<5` | `<5` | — | — | — |
| `[0.6, 0.7)` | `<5` | `<5` | — | — | — |
| `[0.7, 0.8)` | `<5` | `<5` | — | — | — |
| `[0.8, 0.9)` | `<5` | `<5` | — | — | — |
| `[0.9, 1.0]` | `<5` | `<5` | — | — | — |

### 24 months · B1

| Calibrated probability | Rows | Events | Mean probability | Observed rate | Wilson 95% |
| --- | ---: | ---: | ---: | ---: | --- |
| `[0.0, 0.1)` | 4,061 | 252 | 0.073356 | 0.062054 | 0.055040 to 0.069896 |
| `[0.1, 0.2)` | 578 | 116 | 0.106678 | 0.200692 | 0.170064 to 0.235272 |
| `[0.2, 0.3)` | `<5` | `<5` | — | — | — |
| `[0.3, 0.4)` | `<5` | `<5` | — | — | — |
| `[0.4, 0.5)` | `<5` | `<5` | — | — | — |
| `[0.5, 0.6)` | `<5` | `<5` | — | — | — |
| `[0.6, 0.7)` | `<5` | `<5` | — | — | — |
| `[0.7, 0.8)` | `<5` | `<5` | — | — | — |
| `[0.8, 0.9)` | `<5` | `<5` | — | — | — |
| `[0.9, 1.0]` | `<5` | `<5` | — | — | — |

### 24 months · M1

| Calibrated probability | Rows | Events | Mean probability | Observed rate | Wilson 95% |
| --- | ---: | ---: | ---: | ---: | --- |
| `[0.0, 0.1)` | 3,404 | WITHHELD | 0.045949 | — | — |
| `[0.1, 0.2)` | 910 | 164 | 0.145133 | 0.180220 | 0.156607 to 0.206521 |
| `[0.2, 0.3)` | 272 | 74 | 0.234918 | 0.272059 | 0.222621 to 0.327846 |
| `[0.3, 0.4)` | 45 | 18 | 0.334684 | 0.400000 | 0.270249 to 0.545481 |
| `[0.4, 0.5)` | 8 | `<5` | 0.435516 | — | — |
| `[0.5, 0.6)` | `<5` | `<5` | — | — | — |
| `[0.6, 0.7)` | `<5` | `<5` | — | — | — |
| `[0.7, 0.8)` | `<5` | `<5` | — | — | — |
| `[0.8, 0.9)` | `<5` | `<5` | — | — | — |
| `[0.9, 1.0]` | `<5` | `<5` | — | — | — |

### 24 months · M3

| Calibrated probability | Rows | Events | Mean probability | Observed rate | Wilson 95% |
| --- | ---: | ---: | ---: | ---: | --- |
| `[0.0, 0.1)` | 3,417 | 103 | 0.045146 | 0.030143 | 0.024917 to 0.036425 |
| `[0.1, 0.2)` | 811 | 141 | 0.143574 | 0.173859 | 0.149330 to 0.201464 |
| `[0.2, 0.3)` | 334 | 94 | 0.236096 | 0.281437 | 0.235905 to 0.331940 |
| `[0.3, 0.4)` | 66 | 26 | 0.337315 | 0.393939 | 0.285030 to 0.514516 |
| `[0.4, 0.5)` | 10 | `<5` | 0.431146 | — | — |
| `[0.5, 0.6)` | `<5` | `<5` | — | — | — |
| `[0.6, 0.7)` | `<5` | `<5` | — | — | — |
| `[0.7, 0.8)` | `<5` | `<5` | — | — | — |
| `[0.8, 0.9)` | `<5` | `<5` | — | — | — |
| `[0.9, 1.0]` | `<5` | `<5` | — | — | — |

## Frozen predictors

Numeric entries give **observed count / missing count · mean / sample SD · Q5 / Q25 / Q50 / Q75 / Q95**. Indicator entries give **level 0 / level 1**. Numeric summaries use observed values on the frozen feature scale. These breadth summaries omit rows with the missing indicator set. The separate missingness indicators use the encoded 0/1 values. The C′ B1 logit is derived directly from the authenticated native score. The remaining C′ cells use the SCORE coverage and graph summaries where available, plus the NME eligibility rule.

### 12 months

| Frozen feature | TRAIN (547) | VAL (2,161) | C′ (5,259) |
| --- | ---: | ---: | ---: |
| `age_years` | 547 / `<5` · 19.896672 / 16.636405 · 1.247639 / 7.451061 / 13.289528 / 29.100616 / 53.672005 | 2,161 / `<5` · 21.126626 / 17.693888 · 1.130732 / 7.170431 / 15.619439 / 31.252567 / 57.278576 | 5,259 / `<5` · `UNAVAILABLE` |
| `age_sq` | 547 / `<5` · 67.214156 / 95.887841 · 0.155717 / 5.551840 / 17.661155 / 84.685132 / 288.068417 | 2,161 / `<5` · 75.926313 / 106.858211 · 0.127856 / 5.141508 / 24.396687 / 97.672293 / 328.083530 | 5,259 / `<5` · `UNAVAILABLE` |
| `nme` | `<5` / 547 | `<5` / 2,161 | `<5` / 5,259 |
| `orphan` | 453 / 94 | 1,703 / 458 | `UNAVAILABLE` / `UNAVAILABLE` |
| `priority` | 297 / 250 | 1,176 / 985 | `UNAVAILABLE` / `UNAVAILABLE` |
| `oral` | 547 / `<5` | 2,161 / `<5` | `UNAVAILABLE` / `UNAVAILABLE` |
| `injectable` | 547 / `<5` | 2,161 / `<5` | `UNAVAILABLE` / `UNAVAILABLE` |
| `n_nda_prior` | 547 / `<5` · 1.493601 / 0.951890 · 1.000000 / 1.000000 / 1.000000 / 2.000000 / 3.000000 | 2,161 / `<5` · 1.461823 / 0.953818 · 1.000000 / 1.000000 / 1.000000 / 2.000000 / 3.000000 | 5,259 / `<5` · `UNAVAILABLE` |
| `nce_remaining_years` | 543 / `<5` · 0.392294 / 1.090782 · 0.000000 / 0.000000 / 0.000000 / 0.000000 / 3.615606 | 2,125 / 36 · 0.426083 / 1.093599 · 0.000000 / 0.000000 / 0.000000 / 0.000000 / 3.496235 | 5,181 / 78 · `UNAVAILABLE` |
| `other_exclusivity_remaining_years` | 543 / `<5` · 0.418069 / 1.131367 · 0.000000 / 0.000000 / 0.000000 / 0.000000 / 2.610541 | 2,125 / 36 · 0.536410 / 1.402948 · 0.000000 / 0.000000 / 0.000000 / 0.000000 / 4.146201 | 5,181 / 78 · `UNAVAILABLE` |
| `listed_patent_count` | 543 / `<5` · 2.108656 / 3.197840 · 0.000000 / 0.000000 / 1.000000 / 3.000000 / 8.000000 | 2,125 / 36 · 2.310588 / 3.689899 · 0.000000 / 0.000000 / 1.000000 / 3.000000 / 9.800000 | 5,181 / 78 · `UNAVAILABLE` |
| `years_to_last_patent_expiry` | 290 / 257 · 7.405745 / 4.284259 · 0.459138 / 4.216290 / 7.586585 / 10.310062 / 14.401643 | 1,091 / 1,070 · 7.707070 / 5.083482 · -0.142368 / 3.611225 / 7.427789 / 12.135524 / 15.853525 | 2,659 / 2,600 · `UNAVAILABLE` |
| `years_since_earliest_patent_submission` | `<5` / 547 · — | `<5` / 2,161 · — | 2,007 / 3,252 · `UNAVAILABLE` |
| `nce_remaining_years_missing` | 543 / `<5` | 2,125 / 36 | 5,181 / 78 |
| `other_exclusivity_remaining_years_missing` | 543 / `<5` | 2,125 / 36 | 5,181 / 78 |
| `listed_patent_count_missing` | 543 / `<5` | 2,125 / 36 | 5,181 / 78 |
| `years_to_last_patent_expiry_missing` | 290 / 257 | 1,091 / 1,070 | 2,659 / 2,600 |
| `years_since_earliest_patent_submission_missing` | `<5` / 547 | `<5` / 2,161 | 2,007 / 3,252 |
| `b1_age_hazard_logit` | 547 / `<5` · -3.347599 / 0.835399 · -4.601644 / -4.023350 / -3.461729 / -2.592214 / -1.977426 | 2,161 / `<5` · -3.474416 / 0.831724 · -4.601644 / -4.168833 / -3.461729 / -3.118200 / -1.977426 | 5,259 / `<5` · -3.593824 / 0.773966 · -4.685828 / -4.353730 / -3.461729 / -3.220779 / -2.076258 |
| `challenge_present` | 473 / 74 | 1,910 / 251 | `UNAVAILABLE` / `UNAVAILABLE` |
| `challenge_missing` | 536 / 11 | 687 / 1,474 | 4,671 / 588 |
| `strength_count` | 529 / 18 · 2.298677 / 1.814717 · 1.000000 / 1.000000 / 2.000000 / 3.000000 / 5.000000 | 2,067 / 94 · 2.280600 / 1.959075 · 1.000000 / 1.000000 / 2.000000 / 3.000000 / 6.000000 | 5,047 / 212 · `UNAVAILABLE` |
| `form_route_count` | 543 / `<5` · 1.278085 / 0.584248 · 1.000000 / 1.000000 / 1.000000 / 1.000000 / 3.000000 | 2,125 / 36 · 1.254588 / 0.577867 · 1.000000 / 1.000000 / 1.000000 / 1.000000 / 3.000000 | 5,181 / 78 · `UNAVAILABLE` |
| `strength_missing` | 529 / 18 | 2,067 / 94 | 5,047 / 212 |
| `form_route_missing` | 543 / `<5` | 2,125 / 36 | 5,181 / 78 |
| `verdict_OPEN` | 526 / 21 | 2,074 / 87 | 5,060 / 199 |
| `verdict_BLOCKED` | 316 / 231 | 1,577 / 584 | 3,107 / 2,152 |
| `verdict_CONTESTED` | 252 / 295 | 671 / 1,490 | 2,351 / 2,908 |

### 24 months

| Frozen feature | TRAIN (547) | VAL (1,083) | C′ (4,639) |
| --- | ---: | ---: | ---: |
| `age_years` | 547 / `<5` · 19.896672 / 16.636405 · 1.247639 / 7.451061 / 13.289528 / 29.100616 / 53.672005 | 1,083 / `<5` · 21.084995 / 17.684924 · 1.029432 / 7.182752 / 15.923340 / 31.017112 / 56.877207 | 4,639 / `<5` · `UNAVAILABLE` |
| `age_sq` | 547 / `<5` · 67.214156 / 95.887841 · 0.155717 / 5.551840 / 17.661155 / 84.685132 / 288.068417 | 1,083 / `<5` · 75.704477 / 106.650645 · 0.105973 / 5.159194 / 25.355276 / 96.206124 / 323.501689 | 4,639 / `<5` · `UNAVAILABLE` |
| `nme` | `<5` / 547 | `<5` / 1,083 | `<5` / 4,639 |
| `orphan` | 453 / 94 | 850 / 233 | `UNAVAILABLE` / `UNAVAILABLE` |
| `priority` | 297 / 250 | 589 / 494 | `UNAVAILABLE` / `UNAVAILABLE` |
| `oral` | 547 / `<5` | 1,083 / `<5` | `UNAVAILABLE` / `UNAVAILABLE` |
| `injectable` | 547 / `<5` | 1,083 / `<5` | `UNAVAILABLE` / `UNAVAILABLE` |
| `n_nda_prior` | 547 / `<5` · 1.493601 / 0.951890 · 1.000000 / 1.000000 / 1.000000 / 2.000000 / 3.000000 | 1,083 / `<5` · 1.465374 / 0.971617 · 1.000000 / 1.000000 / 1.000000 / 2.000000 / 3.000000 | 4,639 / `<5` · `UNAVAILABLE` |
| `nce_remaining_years` | 543 / `<5` · 0.392294 / 1.090782 · 0.000000 / 0.000000 / 0.000000 / 0.000000 / 3.615606 | 1,057 / 26 · 0.401265 / 1.055125 · 0.000000 / 0.000000 / 0.000000 / 0.000000 / 3.448597 | 4,567 / 72 · `UNAVAILABLE` |
| `other_exclusivity_remaining_years` | 543 / `<5` · 0.418069 / 1.131367 · 0.000000 / 0.000000 / 0.000000 / 0.000000 / 2.610541 | 1,057 / 26 · 0.520070 / 1.343588 · 0.000000 / 0.000000 / 0.000000 / 0.000000 / 3.740452 | 4,567 / 72 · `UNAVAILABLE` |
| `listed_patent_count` | 543 / `<5` · 2.108656 / 3.197840 · 0.000000 / 0.000000 / 1.000000 / 3.000000 / 8.000000 | 1,057 / 26 · 2.253548 / 3.545704 · 0.000000 / 0.000000 / 1.000000 / 3.000000 / 9.000000 | 4,567 / 72 · `UNAVAILABLE` |
| `years_to_last_patent_expiry` | 290 / 257 · 7.405745 / 4.284259 · 0.459138 / 4.216290 / 7.586585 / 10.310062 / 14.401643 | 545 / 538 · 7.428025 / 5.115034 · -0.248049 / 3.446954 / 7.104723 / 11.986311 / 15.633128 | 2,319 / 2,320 · `UNAVAILABLE` |
| `years_since_earliest_patent_submission` | `<5` / 547 · — | `<5` / 1,083 · — | 1,674 / 2,965 · `UNAVAILABLE` |
| `nce_remaining_years_missing` | 543 / `<5` | 1,057 / 26 | 4,567 / 72 |
| `other_exclusivity_remaining_years_missing` | 543 / `<5` | 1,057 / 26 | 4,567 / 72 |
| `listed_patent_count_missing` | 543 / `<5` | 1,057 / 26 | 4,567 / 72 |
| `years_to_last_patent_expiry_missing` | 290 / 257 | 545 / 538 | 2,319 / 2,320 |
| `years_since_earliest_patent_submission_missing` | `<5` / 547 | `<5` / 1,083 | 1,674 / 2,965 |
| `b1_age_hazard_logit` | 547 / `<5` · -2.644886 / 0.828215 · -3.983413 / -3.225290 / -2.875368 / -1.887264 / -1.271031 | 1,083 / `<5` · -2.765957 / 0.820067 · -3.983413 / -3.398440 / -2.875368 / -2.012013 / -1.271031 | 4,639 / `<5` · -2.918101 / 0.769801 · -4.068283 / -3.674538 / -2.875368 / -2.503118 / -1.724599 |
| `challenge_present` | 473 / 74 | 988 / 95 | `UNAVAILABLE` / `UNAVAILABLE` |
| `challenge_missing` | 536 / 11 | 95 / 988 | 4,053 / 586 |
| `strength_count` | 529 / 18 · 2.298677 / 1.814717 · 1.000000 / 1.000000 / 2.000000 / 3.000000 / 5.000000 | 1,028 / 55 · 2.289883 / 1.966025 · 1.000000 / 1.000000 / 2.000000 / 3.000000 / 6.000000 | 4,449 / 190 · `UNAVAILABLE` |
| `form_route_count` | 543 / `<5` · 1.278085 / 0.584248 · 1.000000 / 1.000000 / 1.000000 / 1.000000 / 3.000000 | 1,057 / 26 · 1.253548 / 0.575748 · 1.000000 / 1.000000 / 1.000000 / 1.000000 / 3.000000 | 4,567 / 72 · `UNAVAILABLE` |
| `strength_missing` | 529 / 18 | 1,028 / 55 | 4,449 / 190 |
| `form_route_missing` | 543 / `<5` | 1,057 / 26 | 4,567 / 72 |
| `verdict_OPEN` | 512 / 35 | 1,028 / 55 | 4,361 / 278 |
| `verdict_BLOCKED` | 345 / 202 | 902 / 181 | 2,965 / 1,674 |
| `verdict_CONTESTED` | 237 / 310 | 236 / 847 | 1,952 / 2,687 |

## C′ eligibility flow

Counts pool registered annual cutoff rows within each horizon. The same history can contribute at several cutoffs.

| Gate or subcount | 12 months | 24 months |
| --- | ---: | ---: |
| Dated original NDA by cutoff | 18,284 | 16,085 |
| Excluded for no dated eligible TYPE 1 | 6,886 | 6,081 |
| Dated TYPE 1 candidates | 11,398 | 10,004 |
| Excluded for prior final ANDA | 6,139 | 5,365 |
| Of those, final ANDA strictly before first dated original NDA | `UNAVAILABLE` | `UNAVAILABLE` |
| Of those, other prior final ANDA, including same day | `UNAVAILABLE` | `UNAVAILABLE` |
| Eligible rows | 5,259 | 4,639 |
| Event rows | 202 | 368 |

## Availability and Planner handoff

- **C′ predictor values.** Full distributions remain `UNAVAILABLE` for the ten numeric features other than the B1 logit, along with level counts for orphan, priority, oral, injectable and challenge present. Eligible-row exports contain native scores and labels. SCORE supplies aggregate missingness, graph verdicts and denominators. They do not identify the remaining feature values.
- **Prior-ANDA reasons.** The split remains `UNAVAILABLE` at both horizons. The eligible-row exports omit excluded rows and SCORE gives only the combined prior-ANDA count. A custodian would need to supply authenticated aggregate counts for the two reasons.
- **Implementation attempts.** The first run failed at a calibration result-field lookup. After the lookup was fixed, the development import exposed two obsolete DEVX scanner names from T4. The runner restores the original scanner patterns during import. The pre-registration-only T1v3 check also refused the existing registration record. The runner uses SCORE's post-registration development check, which requires absent seal authorization and enforces the pinned development-only cutoffs and observation limit. The registration record stayed in place.
- **Deviations from the note.** None. The attempts above occurred before a completed development replay. The runner preserved the same frozen feature definitions, partitions and inputs. No sealed cohort reconstruction, GPU or paid API.
- The main Planner owns scientific review and integration into the lane handoff and memory. The historical use restrictions and registered interpretation remain those in JOINT-SIGNOFF.

## Verification

- `py -3.12 -m pytest tests/test_org_adaptive_terminology.py -q` → **PASS**, 2 tests.
- `py -3.12 -m pytest loe-bench/loe_bench/tests/test_score_cprime_desc.py -q` → **PASS**, 5 synthetic tests.
- The descriptive and existing supplement fixtures also passed jointly, 12 tests.
- The aggregate audit checked the receipt links, all 29 input digests as recorded in the JSON, all 60 calibration cells, all 28 feature names in each of the six horizon/partition panels, cohort arithmetic and the absence of row keys in the JSON.
- All 32 spot checks against [CLOSE-DISP development summaries](CLOSE-DISP.md#development-predictor-distributions) matched the published indicator counts and rounded age medians.
- Root `py -3.12 -m pytest --tb=short -p no:cacheprovider` returned exit 1 with 2,760 passed, 50 skipped, one xfailed and the eight standing SACR r2/r3 supervisor budget failures. [SCORE baseline](SCORE.md#private-outputs-and-verification)
