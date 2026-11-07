# Medtech time-machine data: BigQuery checks (7 Nov 2026)

- **Status:** PASS for tm01 (run). tm02 is `NOT_RUN`: its dry-run estimate is over the owner's cap.
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

## tm02: population counts (dry run only)

- SQL: `scripts/healthtech/sql/tm02_medtech_population_counts.sql`, sha256 `78e7a7eb…20d4`.
  - It counts, by grant year, US device grants (A61B/F/G/H/J/L/M/N) from 2010 to 2023.
  - For each it counts examiner-cited US targets that share no 3-character CPC code with the query and were filed at least 5 years earlier.
- **Dry-run estimate: 31.171 GiB, over the 30 GiB cap, so it was not run.**
- Column probes (dry run): `cpc.code` over US rows is 13.0 GiB, and `citation.publication_number` over US rows is 9.6 GiB. The query is close to minimal for this join.
- Running it needs the owner to raise the cap in `.env.bigquery`, for example to 34 GiB.
  - Spend so far is about 8 GB of the 1 TB monthly free tier; with tm02 it would be about 39 GB.
