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
