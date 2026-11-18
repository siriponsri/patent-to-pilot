# Continuity tables for family grouping (D1): exact file list

Approved by the owner on 2026-11-18 (`owner-decisions-20261118.json`). Nothing is downloaded yet.

## Why the agent cannot download them itself
- USPTO ODP (data.uspto.gov, the PatentsView host since 2025) needs a USPTO.gov sign-in with MFA and a CAPTCHA
  (checked 2026-11-18 in the browser). The 16-Nov files were downloaded the same way, by the owner.
- The old S3 URLs (`s3.amazonaws.com/data.patentsview.org/...`) return HTTP 403.
- The DataLumos/ICPSR mirror (project 223582, V1, 2025-03-19) lists the grant tables only and needs its own sign-in to download.

## Files

| # | File | Covers | Size (zip / tsv) | Rows | Source of size | Status |
|---|---|---|---|---|---|---|
| 1 | `g_us_rel_doc.tsv.zip` | US related documents (continuation, divisional, CIP, provisional ...) of **granted** patents, 2002+ | 245.6 MiB / 1.1 GiB | 15,778,510 | DataLumos V1 (snapshot 2025-03-17) | required |
| 2 | `pg_rel_app.tsv.zip` (name `UNVERIFIED`) | related-application data of **pre-grant publications** (covers tasks never granted) | `NOT_VERIFIED` | `NOT_VERIFIED` | not in the mirror | required if present on ODP |
| 3 | `g_rel_app_text.tsv.zip` | free-text related-application paragraph of granted patents | 219.3 MiB / 1.1 GiB | 2,583,210 | DataLumos V1 | optional fallback |

Total about 0.5-1 GB zipped, far inside the 60 GB R5 cap. The ODP release may be newer than the 2025-03 mirror; record the actual size and SHA256 at download.

## Owner steps
1. Sign in to data.uspto.gov, open the PatentsView granted and pre-grant bulk tables, download files 1 and 2 (and 3 if wanted).
2. Copy them to dr-train `/data/ptp-paper2/patentsview/` (or put them on this PC and tell the agent; it will scp and hash them).

## What happens after (no further approval needed)
- CPU on dr-train: build `related.tsv` (app_id, related_app_id) for the 378,109 tasks; connected components over
  continuation/divisional/CIP links; rebuild the manifest as `manifest-v2` with `--related`; report L-B
  (group overlap P1-DEV/P2-DEV and P1-TEST/P2-TEST), option-A removals from P2-TEST and the cross-year stratum.
- Limit to state: grant-side continuity misses applications that were never granted unless file 2 exists.
