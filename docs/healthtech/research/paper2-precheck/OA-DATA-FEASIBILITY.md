# Paper 2 pre-check, stream 3: office-action data feasibility

Status (2026-11-16): desk research done; owner approved D1-D4 (owner-oa-download-approval.json). D3 (DAPFAM HF metadata, hashes match the pinned manifest) and D4 (panorama.parquet, 167,031,631 B, sha256 827a3940...) downloaded. **D1 and D2 BLOCKED**: since 2026-06-18 the USPTO Open Data Portal (which now hosts both the OA dataset and PatentsView) requires a signed-in USPTO.gov account with MFA; the unauthenticated API returns 403 and the UI returns a login dialog. OA overlap numbers are therefore NOT_RUN; DAPFAM-side aggregates are in section 7.

Question: can we build a legally grounded, cross-domain evaluation set from USPTO prosecution records? That means using examiner citations that back a 35 USC 102 or 103 rejection as relevance labels, split into IN/OUT by IPC domain. How large would it be?

Rules followed: no paid API or subscription, no file download without owner approval, no access to the sealed DAPFAM test folder, dev data only, and only aggregates in the repo.

## 1. Source table

| Source | Files / access | Size | License / terms | Key fields | How cited art is identified |
|---|---|---|---|---|---|
| USPTO Office Action Research Dataset for Patents, 2017 release (OCE; covers 2008 to mid-2017, no longer updated) | `office_actions.csv.zip`, `rejections.csv.zip`, `citations.csv.zip` (also `.dta.zip`). Linked from the [USPTO page](https://www.uspto.gov/ip-policy/economic-research/research-datasets/office-action-research-dataset-patents), which now issues temporary signed URLs; also in the ODP Bulk Data Directory. Old path `bulkdata.uspto.gov/data/patent/office/actions/bigdata/2017/` did not resolve from here. | CSV: 79.5 MB, 99.3 MB, 623 MB (about 800 MB total). DTA: 75.8 MB, 112 MB, 1.12 GB | US government work. The data.gov catalog lists it as public domain ([catalog](https://catalog.data.gov/dataset/patent-application-office-actions-research-dataset-for-academia-and-researchers-2008-2017)). Cite Lu, Myers & Beliveau 2017, USPTO Economic Working Paper 2017-10 | **office_actions**: `app_id` (8-digit US application number), `ifw_number`, `mail_dt`, `art_unit`, `uspc_class`, `rejection_101/102/103/112/dp`, `cite102_gt1`, `cite103_gt3`, `cite103_eq1`, `cite103_max`. **rejections**: `app_id`, `ifw_number`, `action_type` (35 USC section), `action_subtype`, `claim_numbers`. **citations**: `app_id`, `ifw_number`, `citation_pat_pgpub_id`, `parsed`, `form892`, `form1449`, `citation_in_oa`, `action_type`, `action_subtype` ([variable tables](https://www.uspto.gov/sites/default/files/documents/Variable%20tables_v20171120.pdf), [schema](https://www.uspto.gov/sites/default/files/documents/dataset_schema_v20171120.pdf)) | `parsed` holds a **US patent number or US pre-grant publication number**, parsed from the raw citation string. US documents only: no foreign patents and no NPL. A citation is tied to a rejection basis through `action_type` (102 or 103) and `citation_in_oa` (cited in the action sentence). This is exactly the "legal basis" label we need. 4.4M office actions on 2.2M applications |
| USPTO ODP Office Action Rejections API v2 | REST API on [data.uspto.gov](https://data.uspto.gov/apis/office-action-rejections/search). Covers OAs mailed from 2018-06-01 (catalog) to about 180 days before today, refreshed daily ([catalog](https://catalog.data.gov/dataset/office-action-rejection-api-version-2)) | API, no file | Free, but ODP requires a USPTO.gov account and API key | Rejection flags per OA, application number. v2 field names differ from v1 | n/a (rejections only) |
| USPTO ODP Office Action Citations API v2 | REST API ([API catalog](https://developer.uspto.gov/api-catalog/uspto-office-action-citations-api), [data.gov](https://catalog.data.gov/dataset/office-action-citations-api-version-2)). Covers OAs from 2017-10-01. The v1 beta and Enriched Citation v1 were decommissioned on 2026-01-30 | API | Free, API key | Citations from PTO-892, PTO-1449 and OA text. Enriched Citation API v2 adds an examiner-cited flag and OA category ([Enriched Citation v2](https://developer.uspto.gov/node/165464)) | US patent / publication numbers. 102/103 linkage per citation is still to be confirmed from the v2 field mapping |
| PTAB (trials and appeals) | ODP PTAB API v2 plus bulk download ([PTAB IT systems](https://www.uspto.gov/patents/ptab/ptab-it-systems)) | Not stated | Free, API key | Proceedings, decisions, documents | Decision text only. No structured prior-art labels, and too few appeals per IPC pair. **Not proposed** |
| PANORAMA (LG AI Research, NeurIPS 2025, [arXiv 2510.24774](https://arxiv.org/abs/2510.24774)) | HF `LG-AI-Research/PANORAMA`: `panorama.parquet`, `spec_app-2.zip`, `spec_cited.zip`, and `{PAR4PC,PI4PC,NOC4PC}/{train,validation,test}.parquet` | Repo total 18.17 GB (no per-file sizes listed). Already local: PAR4PC val+test (2,896 + 3,029 rows, about 25 MB) in `../_private_artifacts/healthtech/benchmark-expansion-20261101/` | **CC BY-NC 4.0** (HF API). An aggregator lists BY-NC-SA, but the HF card says BY-NC | 8,143 records (2015-2024) with application, cited references and non-final rejection; 102/103 tags. PAR4PC fields: `application_number`, `claim_number`, `options.{A..H}.patent_id`, `gold_answers`, `silver_answers`, `negative_answers` | `patent_id` (US patent / publication numbers). Small, and the labels are already in a multiple-choice format. Useful as a sanity check, not as the main set |
| PatEx-Gym / PatEx-Bench ([arXiv 2610.33503](https://arxiv.org/abs/2610.33503)) | Project site patex-gym.wangqiyao.me; GitHub `AIforIP/PatEx-Gym` | 1,000 tasks; 2,946 cited patents + 178 papers; corpus 1.01M patents + 52K papers | Not stated | Built from "publicly available USPTO research datasets", first OA per application; statute F1 | Google Patents corpus. No 102/103 breakdown and no cross-domain split. Data release not verified |
| PatentAgentBench ([arXiv 2610.35031](https://arxiv.org/abs/2610.35031)) | No dataset URL on the abstract page | 510 instances, 8 suites | Paper CC BY 4.0; data license not stated | Includes an office-action-response suite | Not a retrieval label set. **Not useful** for this purpose |
| PatentsView bulk tables (now under USPTO ODP) | `g_ipc_at_issue.tsv.zip`, `g_application.tsv.zip`, `pg_published_application.tsv.zip`, and similar ([download tables](https://patentsview.org/download/data-download-tables), redirects to data.uspto.gov) | g_ipc_at_issue about 355 MB zip ([DataLumos mirror](https://www.datalumos.org/datalumos/project/223582/view)); pg_published_application about 1.7 GB zip (unconfirmed). Exact sizes to be read at download time | US government data, free | patent_id to IPC; patent_id to application number; pgpub document number to application number and IPC | Needed to put an IPC domain on both sides of an OA citation (citing application and cited patent/publication) |
| DAPFAM (`datalyes/DAPFAM_patent`, rev 780f4011...) | `corpus.parquet` 1,149,928,014 B; `queries.parquet` 62,667,355 B; `qrels_all.parquet` 828,375 B | as listed | **CC BY-NC-SA 4.0** | Corpus/queries: `relevant_id`/`query_id`, `earliest_claim_jusrisdiction` (sic), `jurisdiction` (list), `ipcr_codes_str`, `earliest_claim_date`, IPC3 list, text. Schema from the HF datasets-server `/info`, read without downloading | **No member publication or application numbers.** Ids are Lens.org ids of the earliest-claim publication of a simple family ([DAPFAM paper](https://arxiv.org/abs/2506.22141)). Relevance comes from Lens forward/backward citations with no examiner/applicant or X/Y/102/103 distinction. Paper Table 6: US is the primary jurisdiction for 77.7% of queries and 61.0% of targets |

Local check (shapes only, no text printed): the staged dev files `runtime-dev/corpus.jsonl`, `queries-ta.jsonl` and `dev-evaluation/qrels-dev.jsonl` carry only `id` (format `NNN-NNN-NNN-NNN-NNN`, the Lens id pattern), text fields, and `query_id`/`relevant_id`/`relevance_score`/`domain_rel`. The staging dropped jurisdiction and date.

## 2. What this means

1. **A new OA-derived cross-domain set is clearly buildable from free public data.** The 2017 OA dataset alone links each examiner citation to a 102 or 103 rejection (`citations.action_type` + `citation_in_oa`), at the application level, over 2.2M applications. PatentsView IPC tables give the domain on both sides, so pairs can be labelled IN (shared IPC3/IPC4, or same section) versus OUT (no shared IPC3, or a section mismatch). Size is still to be measured, but even a small OUT share of hundreds of thousands of 102/103 citation pairs would be far larger than DAPFAM's 5,193 OUT positives.
   - Caveat 1: cited art is US-only.
   - Caveat 2: query text (the application as filed) must come from pre-grant publications (PatentsView `pg_*` text or ODP), because the OA data has no text.
   - Caveat 3: OAs after mid-2017 need the free ODP API key.
2. **Relabelling DAPFAM dev with 102/103 is blocked on identifiers, not licenses.** DAPFAM releases Lens ids only. Mapping a Lens id to a US publication or application number needs either:
   - (a) the Lens.org API. It needs a registered token; free non-commercial access may be possible, but that is a terms question for the owner, and the rule says no paid subscription. Or
   - (b) a local deterministic match of DAPFAM records (US earliest-claim jurisdiction + earliest-claim date + exact normalised title) against PatentsView `g_patent`/`pg_published_application`. This needs the DAPFAM HF `queries.parquet` and `corpus.parquet` for jurisdiction and date. The match runs locally and only aggregates leave it. Precision must be reported, with ambiguous matches abstaining.

   Even after mapping, the 2017 OA data covers only OAs mailed 2008 to mid-2017. DAPFAM query families of other years, or without a US member that received an OA, cannot be labelled. The expected overlap is therefore partial; the size estimate is section 4.

## 3. Recommended path

- Primary: build the OA-derived cross-domain set (A1). Use DAPFAM relabelling (A2) only as a linkage check that shows how DAPFAM's citation-based OUT pairs relate to legally grounded 102/103 citations.
- 2018+ OAs (ODP APIs) are a later extension, after the 2008-2017 set is sized.

## 4. Planned measurements (after approval; aggregates only)

A1, OA-derived set:
- citation rows with `action_type` in {102, 103} and `citation_in_oa=1`;
- distinct (application, cited document) pairs;
- share of citing applications and cited documents with an IPC in PatentsView;
- cross-tab of 102/103 by IN/OUT under three rules: shared IPC3, shared IPC4, IPC section mismatch;
- counts by citing section × cited section.

A2, DAPFAM dev linkage:
- share of the 474 dev query families with US earliest-claim jurisdiction;
- share mappable to a US publication/application number (with match-rule precision);
- share whose application appears in the OA data;
- share of dev qrels pairs (IN/OUT) that appear as 102 or 103 examiner citations;
- cross-tab IN/OUT × 102/103.

Scripts go in `docs/healthtech/research/paper2-precheck/oa/`. CPU is metered with `scripts/healthtech/meter_local_cpu.py`.

## 5. Downloads proposed (NONE done; each needs owner approval)

| # | File | Source | Size | Destination |
|---|---|---|---|---|
| D1 | `office_actions.csv.zip`, `rejections.csv.zip`, `citations.csv.zip` | USPTO OCE OA Research Dataset 2017 (uspto.gov / ODP bulk) | 79.5 + 99.3 + 623 MB = about 0.80 GB | remote `/data/ptp-paper2/oa2017/` |
| D2 | `g_ipc_at_issue.tsv.zip`, `g_application.tsv.zip`, `g_patent.tsv.zip` (title, date), `pg_published_application.tsv.zip` | PatentsView via USPTO ODP | about 0.36 GB + small + about 0.2-0.3 GB + about 1.7 GB; exact sizes to be confirmed on the page before transfer | remote `/data/ptp-paper2/patentsview/` |
| D3 | `queries.parquet`, `corpus.parquet` (rev 780f4011d60297fc6e97a4119b0c516d13afea2d) | HF `datalyes/DAPFAM_patent` | 62.7 MB + 1.15 GB | local `../_private_artifacts/healthtech/ptp-paper2-oa-dapfam-meta/` (dev ids used only; test ids never read) |
| D4 (optional) | `panorama.parquet` | HF `LG-AI-Research/PANORAMA` | not listed (repo 18.2 GB total); size to be read before transfer, skipped if over 2 GB | remote `/data/ptp-paper2/panorama/` |
| Not proposed | Lens.org API token; ODP API key (2018+ OAs) | registration | n/a | separate owner decision |

Note on D3: `corpus.parquet` contains the whole DAPFAM corpus. Only jurisdiction/date/title metadata of dev-split ids is used. The sealed test folder is never opened, and test query ids are not selected.

Incidental: two USPTO documentation PDFs (variable tables, a working paper) were cached by the web-fetch tool under the session's tool-results folder while reading field definitions. They are documentation, not datasets, and are not in the repo.

## 6. Owner approval record

Approved 2026-11-16: D1, D2, D3, D4 (`owner-oa-download-approval.json`). Lens API and ODP API key not approved. D1/D2 need either the owner signing in to a USPTO.gov account (free, MFA) in the browser, or approval of a different source (e.g. the DataLumos archive of PatentsView); asked.

## 7. DAPFAM dev aggregates (no OA data needed)

Script `oa/dapfam_dev_us_profile.py` (metadata columns only, dev split only; 0.56 s CPU, receipt `oa/local-cpu.jsonl`); output `oa/dapfam-dev-us-profile.json`.

- 474 dev query families: earliest-claim jurisdiction US 351 (74.1%); any US member 472 (99.6%).
- Earliest-claim (priority) year: 2001-2005 = 249 queries (52.5%), 2006-2017 = 225; any-US and 2006-2017 = 223 (47.0%). The 2017 OA dataset covers OAs **mailed** 2008 to mid-2017, so most 2001-2004 families had their first US OA before 2008 and cannot be matched. Realistic upper bound for an OA-labelled query: about 47-58% of dev queries (2005/2006 onward), before checking that an OA with a 102/103 citation exists.
- 9,480 dev positive pairs: IN 6,490, OUT 2,990. Both sides have a US member: IN 6,406, OUT 2,949. OUT pairs with an IPC **section** mismatch: 2,031 (68% of OUT); the other 959 OUT pairs share a section but no IPC3.
- DAPFAM positives include forward citations (target later than query). A 102/103 examiner citation can only exist for backward-cited, earlier targets, so the OA-confirmable share of OUT pairs is further reduced.
- Identifier gap stays: Lens ids must still be mapped to US application/publication numbers (PatentsView title+date match, needs D2) before any OA overlap is computed.

Interim conclusion: relabelling DAPFAM dev with 102/103 can at best cover about half of the queries and a fraction of their (backward) pairs. The OA-derived new test set (A1) is the more promising route, and its size can only be measured once D1/D2 are retrievable.
