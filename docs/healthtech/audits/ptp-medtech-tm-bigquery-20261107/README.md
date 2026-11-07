# Medtech time-machine data: BigQuery checks (7 Nov 2026)

- **Status:** PASS. tm01 and tm02 ran. The owner raised the cap to 34 GiB for tm02.
- **Setup:**
  - The owner runs a service account. The key file is kept outside the repository, and credentials live in the git-ignored `.env.bigquery`, which the agent never reads or prints.
  - The per-query cap is 30 GiB, set by the owner. `google-cloud-bigquery` 3.47.0 was installed in the scout venv with owner approval.
- **Tool:** `scripts/healthtech/bq_probe.py` at commit `a98b404`. It dry-runs first, refuses any query over the cap, and sets `maximum_bytes_billed` to the cap.
- **Source:** Google Patents Public Data (`patents-public-data.patents.publications`).
  - Only aggregates are committed. Dataset terms still need to be checked before releasing anything derived from it.
  - The plan is to release IDs and labels that can be rebuilt from USPTO public-domain data.

## tm01: US citation categories (US B1/B2 grants, January 2018)

SQL: `scripts/healthtech/sql/tm01_us_citation_categories.sql`, sha256 `e85a9f70…02e41`.

| Run | Exit | Processed | Billed | Rows | Time |
|---|---|---|---|---|---|
| Dry run | 0 | estimate 7.504 GiB | — | — | — |
| Run | 0 | 8,057,270,376 bytes | 8,058,306,560 bytes | 14 | 3.5 s |

The run was not served from cache. Output (private): `../_private_artifacts/healthtech/medtech-time-machine/tm01_us_citation_categories.csv`, sha256 `6a8dd10f…8b50`.

| `citation.category` | Citations |
|---|---|
| APP | 1,114,419 |
| SEA | 218,902 |
| APP,APP | 218,841 |
| SEA,SEA | 6,182 |
| APP,SEA | 910 |
| TPO | 652 |
| PRS,SEA | 513 |
| other combinations | 43 |

**Reading:**
- US citations carry a category: APP for applicant-cited, **SEA for examiner-cited** (search), and TPO for third-party.
- Examiner-cited references can therefore be selected with `category LIKE '%SEA%'`, which is about 16% of citations here.
- The exact semantics of SEA should still be cross-checked against one USPTO grant XML file ("cited by examiner"), as the data plan says.
- `citation.type` is empty for these rows.

## tm02: population counts (run after the owner raised the cap to 34 GiB)

- SQL: `scripts/healthtech/sql/tm02_medtech_population_counts.sql`, sha256 `78e7a7eb…20d4`.
- **Population:** US B1/B2 device grants from 2010 to 2023 (CPC A61B/F/G/H/J/L/M/N).
- **Targets:** US patents the examiner cited (category contains SEA) that share no 3-character CPC code with the query and were filed at least 5 years earlier.

| Run | Exit | Processed | Billed | Rows | Time |
|---|---|---|---|---|---|
| Dry run | 0 | estimate 31.171 GiB | — | — | — |
| Run | 0 | 33,469,866,904 bytes | 33,470,545,920 bytes | 14 | 9.8 s |

The run was not served from cache. Output (private): `../_private_artifacts/healthtech/medtech-time-machine/tm02_medtech_population_counts.csv`, sha256 `26e02f05…579d`.

| Grant year | Device grants | With older cross-field examiner target | Pairs | Median gap (y) |
|---|---|---|---|---|
| 2010 | 13,463 | 3,130 | 7,319 | 15 |
| 2011 | 14,894 | 3,267 | 7,826 | 14 |
| 2012 | 17,906 | 3,583 | 8,095 | 14 |
| 2013 | 20,661 | 3,925 | 9,192 | 14 |
| 2014 | 22,374 | 4,409 | 10,585 | 14 |
| 2015 | 22,099 | 4,141 | 9,982 | 14 |
| 2016 | 22,981 | 4,182 | 10,130 | 14 |
| 2017 | 24,730 | 4,597 | 10,692 | 14 |
| 2018 | 24,221 | 4,369 | 10,461 | 14 |
| 2019 | 29,629 | 5,365 | 12,238 | 14 |
| 2020 | 29,609 | 5,214 | 12,385 | 14 |
| 2021 | 27,615 | 4,757 | 11,636 | 15 |
| 2022 | 27,370 | 4,208 | 9,761 | 15 |
| 2023 | 26,900 | 3,873 | 8,925 | 16 |
| **Total** | **324,452** | **59,020 (18.2%)** | **139,227** | — |

**Reading** (descriptive; not yet a benchmark):
- About 59,000 device queries qualify. DAPFAM gives 25 dev queries, so this population is more than 2,000 times larger.
- About 18% of US device grants from 2010 to 2023 have at least one examiner-cited US patent from another field (no shared 3-character CPC) filed at least 5 years earlier. The median gap is 14–16 years.
- **Caveats:**
  - "Other field" is a coarse CPC3 rule, the same as DAPFAM's IPC3 rule.
  - Targets without CPC are excluded, and so are non-US documents and literature.
  - Medians are approximate (`APPROX_QUANTILES`).
  - Citation completeness varies by examiner. Unjudged is not negative.
- **Spend:** about 41.5 GB billed in total this month (tm01 plus tm02), inside the 1 TB free tier as far as the project's billing setup allows. The owner should check the billing page.

## tm03: MTM build query (dry runs only, 7 Nov 2026)

- **Inputs:**
  - SQL: `scripts/healthtech/sql/tm03_build_mtm.sql`, sha256 `1cf6c97d…7774`, per the rules draft.
  - Table metadata (free): 173,516,400 rows, 2,952 GiB.
- **Column probes** (dry run):

  | Column | Estimate |
  |---|---|
  | `title_localized` | 15.9 GiB |
  | `abstract_localized` | 199.1 GiB |
  | `claims_localized` | 116.4 GiB |

- **Full build:**

  | Variant | Estimate | Note |
  |---|---|---|
  | With the claims head | **365.1 GiB** | |
  | Without claims | **248.8 GiB** | the variant was generated in scratch by replacing the claims expression with NULL |

- **Not run:** both exceed the owner's 34 GiB per-query cap.
  - Running one needs the owner to raise the cap for that single run, and to confirm that the project's monthly free tier (1 TB) or billing setup covers it.
  - About 41.5 GB is used so far this month.

## SEA cross-check (7 Nov 2026)

**USPTO pilot: `BLOCKED`.**
- The old host `bulkdata.uspto.gov` no longer resolves. The data.uspto.gov file path returns the web app's HTML, not the zip.
- The ODP API (`api.uspto.gov/api/v1/datasets/products/PTGRXML`) returns **401** without an `X-API-KEY`.
- Unblocking needs one of two things from the owner:
  - a MyUSPTO account and ODP API key, registered by the owner (the agent does not log in); or
  - one weekly grant zip downloaded in the owner's browser.

**Spot check instead (`PASS`, weaker evidence):**
- tm01b (`scripts/healthtech/sql/tm01b_sea_examples.sql`, 2% table sample, 0.376 GB billed) returned 3 January 2018 grants with SEA and APP citations.
- On the public Google Patents pages, the "* Cited by examiner" marks match the BigQuery categories in **18 of 18** citations checked:
  - US9854751B2: 12 of 12 (SEA = "*", APP = unmarked);
  - US9854761B2: 6 of 6.
- Both views come from Google's processing of USPTO data, so this is not an independent check. The USPTO XML check stays open.

## SEA vs USPTO XML: independent check (`PASS`, 7 Nov 2026)

**USPTO side:**
- The owner downloaded `ipg180102.zip` (grants of 2 January 2018) in the browser to `data/raw/uspto/`, which is git-ignored.
  - Size 129,360,562 bytes, sha256 `a8dca2bb…7d35`.
- `scripts/healthtech/parse_uspto_grant_citations.py` streamed it with no text kept: 7,067 documents, 6,920 grants parsed.
  - v2 output (private) sha256 `885d0b57…a6f6`.
  - v1 had a number-format bug for pre-grant publications written as `2012/0323474`. It was fixed, and only v2 is used.

**BigQuery side:**
- tm01c (`scripts/healthtech/sql/tm01c_week_20180102_citations.sql`) returned the US B1/B2 grants of 2 January 2018 with their US citations: 6,251 grants, 18.8 GB billed.

**Comparison** (6,251 common grants, 206,070 matched citation pairs):

| USPTO XML category | BigQuery category | Pairs |
|---|---|---|
| cited by applicant | APP | 160,676 |
| **cited by examiner** | **SEA** | **45,377** |
| cited by third party | TPO | 17 |
| any other combination | — | 0 |

- SEA as a predictor of "cited by examiner": **precision 1.000, recall 1.000**.
- Unmatched pairs: 83 on the XML side only and 24 on the BigQuery side only.
- **Conclusion:** the MTM target rule `category LIKE '%SEA%'` selects exactly the references the USPTO marks as cited by the examiner.

**Spend:** about 61 GB billed this month before tm03 (tm01 8.1, tm01b 0.4, tm02 33.5, tm01c 18.8).

## tm03: MTM build run (`PASS`), and a corpus design issue found in validation (7 Nov 2026)

- **Run:** the owner raised the cap to 370 GiB. The dry run estimated 365.1 GiB.
  - Exit 0 after 1,604 s. 392,073,437,102 bytes processed; 392,074,100,736 billed; not served from cache.
  - Output (private): `../_private_artifacts/healthtech/medtech-time-machine/tm03_mtm_build.csv`, 1.06 GB, 455,404 rows, sha256 `65ffa97f…e23d`.

**Validation** (counts only; no rankings or scores exist):

| Item | Value |
|---|---|
| Queries | 2,000 dev + 2,000 test; 0 family overlap between splits |
| Targets per query | dev mean 2.11 (median 1, max 39); test mean 2.26 (median 1, max 51) |
| Target families | 8,518; all present in the corpus |
| Matched distractors | 442,886. Main corpus: 451,404 families, no duplicates. Small corpus: 93,690 |
| Missing text | claims head missing for 2,329 documents; abstract missing for 2 |

**Issue: the corpus has almost no recent documents.**

Priority years in 5-year bins:

| Role | Bins (start year: count) |
|---|---|
| Queries | 1995: 15, 2000: 273, 2005: 1,081, 2010: 1,110, 2015: 1,364, 2020: 157 |
| Targets | … 1995: 1,629, 2000: 1,985, 2005: 1,324, 2010: 483, 2015: 15 |
| Distractors | … 1995: 84,708, 2000: 103,220, 2005: 68,848, 2010: 25,116, 2015: 780 |

- The matched rule copies the targets' age profile. Targets are at least 5 years older than their queries by definition.
- So, as of a query's date, the corpus lacks most of the recent documents a real search would rank against. That would make U and X easier than reality.
- This is a design flaw found before any scoring.

**Proposed fix (tm04, dry run only):** `scripts/healthtech/sql/tm04_uniform_distractors.sql`, sha256 `6a11db61…0f55`.
- It draws a **uniform** sample of 470,000 US families (English title and abstract, priority ≤ 2023) by sha256 order. Families already in tm03 are dropped locally.
- Dry run: **349.8 GiB** (cap 370 GiB).
- Proposed primary corpus: targets + matched + uniform, about 900k families. Targets cannot then stand out by age, and recent competitors are present.
- Sensitivities: targets + matched, and targets + uniform.
- **Not run; owner approval needed.** Monthly billed so far is about 453 GB; with tm04 it would be about 829 GB, under 1 TiB.

## tm04: uniform distractors run (`PASS`, 7 Nov 2026)

- **Run:** the owner approved it. Exit 0 after 1,648 s. 375,577,542,687 bytes processed; 375,577,903,104 billed; not served from cache.
  - Output (private): `tm04_uniform_distractors.csv`, 470,000 rows, sha256 `7181788a…9e9b`.
- **Overlap with tm03:**
  - 21,566 families are already in the tm03 corpus and will be dropped by `build_mtm_inputs.py`, leaving **448,434 new families**.
  - 2 have no abstract.
- **Age mix** (priority, 5-year bins; not matched to the targets): 1965: 5,773; 1970: 16,092; 1975: 15,600; 1980: 16,273; 1985: 20,795; 1990: 24,941; 1995: 37,111; 2000: 59,049; 2005: 66,468; **2010: 72,050; 2015: 77,010; 2020: 58,576**.
  - The recent documents missing from the tm03 corpus are now present.
- **Monthly billed so far:** about 829 GB (tm01 8.1, tm01b 0.4, tm02 33.5, tm01c 18.8, tm03 392.1, tm04 375.6).
- **Next:** tm05 (publication dates, dry run 4.48 GiB) needs owner approval. The owner can lower the per-query cap now.
