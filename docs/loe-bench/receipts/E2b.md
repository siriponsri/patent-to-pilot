# E2b receipt · Orange Book annual cutoff backfill

**Partial coverage.** The manifest has a fresh edition with documented pre-cutoff availability for 15 of 16 annual cutoffs. The 2011-01-01 cutoff lacks a July–December 2010 ZIP. FDA documented the December 2010 release, and the file itself could not be recovered from the checked archive locations.

## Acquisition protocol

Use the [CP2 freshness rule](../PLAN.md#cp2-co-planner-review-and-main-planner-decision-27-november-2026) and the [E2 edition-date rule](E2.md). For each January 1 cutoff from 2010 through 2025, an edition is fresh if its maximum ZIP member modification date is between July 1 and December 31 of the preceding year, inclusive. Availability requires a matching Wayback capture on or before the cutoff date (UTC) or an FDA record identifying that exact edition and its publication date. The [FDA FAQ](https://www.fda.gov/drugs/drug-approvals-and-databases/frequently-asked-questions-orange-book) describes a general publication schedule, which alone does not prove availability of a specific ZIP.

Reuse qualifying E2 bytes. Query Wayback CDX for E2 locations and FDA legacy paths. Try October–December captures newest first for the assigned priority years, then July–September for uncovered windows. Where no timely edition can be found, inspect January–February captures for missing fresh bytes and mark later-only evidence explicitly. Replay exact original URLs in raw mode, at least one second apart, and admit only usable FDA data-file ZIPs. Verify all three tables and deduplicate by SHA-256, recording an earlier capture as additional evidence when its bytes match an existing file. Record the existing date-based selector's result for every cutoff and identify any timely alternative separately.

## Coverage

The table reports the edition selected by `OBHistory.edition_asof`. Staleness is cutoff minus edition date. Capture timestamps are UTC. The last column applies the calendar-month freshness rule. Availability is evaluated separately for the selected edition.

| Cutoff | Chosen edition date | Staleness (days) | Wayback capture | Availability proven | Six-month rule |
| --- | --- | ---: | --- | --- | --- |
| 2010-01-01 | 2009-12-22 | 10 | `20100113002223` | No | PASS |
| 2011-01-01 | 2009-12-22 | 375 | `20100113002223` | Yes | FAIL |
| 2012-01-01 | 2011-12-14 | 18 | `20111229223919` | Yes | PASS |
| 2013-01-01 | 2012-09-17 | 106 | `20120921215526` | Yes | PASS |
| 2014-01-01 | 2013-08-30 | 124 | `20130906105914` | Yes | PASS |
| 2015-01-01 | 2014-09-10 | 113 | `20140915104404` | Yes | PASS |
| 2016-01-01 | 2015-09-18 | 105 | `20151006063349` | Yes | PASS |
| 2017-01-01 | 2016-12-16 | 16 | `20161227030040` | Yes | PASS |
| 2018-01-01 | 2017-10-13 | 80 | `20171114202140` | Yes | PASS |
| 2019-01-01 | 2018-08-17 | 137 | `20180908074144` | Yes | PASS |
| 2020-01-01 | 2019-12-13 | 19 | `20191214001219` | Yes | PASS |
| 2021-01-01 | 2020-11-02 | 60 | `20201112023717` | Yes | PASS |
| 2022-01-01 | 2021-12-10 | 22 | `20211228215048` | Yes | PASS |
| 2023-01-01 | 2022-11-10 | 52 | `20221128232655` | Yes | PASS |
| 2024-01-01 | 2023-12-08 | 24 | `20231220045755` | Yes | PASS |
| 2025-01-01 | 2024-12-13 | 19 | `20241226235539` | Yes | PASS |

For 2010-01-01, the manifest also has a fresh, availability-proven alternative dated 2009-10-16 (77 days stale), captured on 2009-11-04 at 09:14:55 UTC. The current selector orders by edition date. The FDA data-file page captured 2010-01-05 shows a page update date of 2009-12-22 and a ZIP size of 483 KB, consistent with the selected edition's member date and 495,019 bytes. Because the listing uses a shared download URL and a rounded size, the table retains `No` for exact availability proof. Use the October ZIP for the 2010 cutoff when exact proof is required. [Raw Wayback capture](https://web.archive.org/web/20091104091455id_/http://www.fda.gov/downloads/Drugs/InformationOnDrugs/UCM163762.zip) · [FDA data-file listing](https://web.archive.org/web/20100105054958id_/http://www.fda.gov:80/drugs/informationondrugs/ucm129689.htm)

## Evidence and failed retrievals

- The [backfill script](../../../loe-bench/scripts/ob_backfill.py) added 12 distinct ZIPs to the [manifest](../../../loe-bench/data/OB_EDITIONS.json) and retained all 19 E2 entries and original metadata. The `e2b` ledger records CDX queries, replay outcomes and the earlier capture for the byte-identical December 2016 edition. Each raw replay was checked against its CDX digest when present, and SHA-256 identifies the local bytes. All 31 files were rehashed, their edition dates recomputed and the table reproduced using the real selector and local ZIPs. Files reside in `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/ob_editions/`.
- The FDA EOB data-file page captured on 2010-12-23 identifies a 503 KB ZIP at `UCM163762.zip` and dates its update to 2010-12-20. The contemporaneous Orange Book homepage describes data through November 2010. This establishes a publication by the 2011 cutoff. The versioned bytes and their ZIP member dates are still missing. The exact-URL CDX query, including all statuses, and the filename prefix query found no captures from April 2010 through March 2011. Legacy `cder/ob` ZIP prefixes on both FDA and AccessData and the FDA Archive-It collection returned no relevant results. [FDA data-file page](https://web.archive.org/web/20101223152935id_/http://www.fda.gov:80/Drugs/InformationOnDrugs/ucm129689.htm) · [FDA Orange Book homepage](https://web.archive.org/web/20101223220931id_/http://www.fda.gov/Drugs/InformationOnDrugs/ucm129662.htm) · [Exact-URL CDX](https://web.archive.org/cdx/search/cdx?url=www.fda.gov%2Fdownloads%2FDrugs%2FInformationOnDrugs%2FUCM163762.zip&from=2010&to=201103&output=json&fl=timestamp%2Coriginal%2Cstatuscode%2Cdigest%2Cmimetype&filter=statuscode%3A.%2A) · [FDA Archive-It CDX](https://wayback.archive-it.org/7993/timemap/cdx?url=http%3A%2F%2Fwww.fda.gov%2Fdownloads%2FDrugs%2FInformationOnDrugs%2FUCM163762.zip&from=200910&to=201103&fl=timestamp%2Coriginal%2Cstatuscode%2Cdigest%2Cmimetype)
- The Wayback availability API returned the 2011-04-01 capture for searches dated 2010-12-31 and 2011-02-01. E2 had already pinned that ZIP with member date 2011-03-18. Broader FDA prefix queries for alternate filenames timed out. The Archive-It calendar returned a rate-limit notice, and the collection CDX query returned an empty response. [Wayback availability lookup](https://archive.org/wayback/available?url=http%3A%2F%2Fwww.fda.gov%2Fdownloads%2FDrugs%2FInformationOnDrugs%2FUCM163762.zip&timestamp=20101231)
- A 2022 legacy URL replay returned HTTP 302. The corresponding `media/76860/download` capture supplied the qualifying edition. Two September 2012 HTTP-origin replays failed to connect. The HTTPS-origin URL replayed the same 2012-09-21 timestamp and matched the CDX digest. The January 2013 fallback yielded an edition dated after the 2013 cutoff and is recorded as outside the target window.

## Verification and handback

- From the repository root, run `python loe-bench/scripts/ob_backfill.py` to query the public archive and fill eligible gaps in the local manifest. Optional `--year` arguments specify the prior edition year, so `--year 2010` targets cutoff 2011-01-01.
- `cd loe-bench` then `python -m unittest discover -s loe_bench/tests -t .` passed all 52 tests with the private ZIPs present. The new manifest-level regression checks all 16 annual cutoffs through the real selector and verifies that future-dated editions are never selected or loaded.
- Repository `python -m pytest` exited 1 with 2,760 passed, 50 skipped, 1 expected failure and the eight known SACR r2/r3 budget supervisor failures listed in [AGENTS.md](../../../AGENTS.md).
- For an availability-gated analysis, the Planner can pin the 2009-10-16 alternative and the 14 fresh, proven selections in the table. Leave 2011-01-01 outside that set unless the December 2010 ZIP or another qualifying FDA data-file ZIP is recovered. FDA directs requests for historical data files to FOIA. [FDA Orange Book Q&A, question on previous editions](https://www.fda.gov/media/160167/download)
