# R5 claims download plan (sizes from the owner's ODP inventory, 2026-11-18)

R5 (owner, 17 Nov): list files and sizes first, then download only what fits under 60 GB. The list is now recorded
(`PATENTSVIEW-ODP-INVENTORY-20261118.md`). Proposed subset:

| Set | Why | Files | ZIP size |
|---|---|---|---|
| `pg_claims_2001` … `pg_claims_2016` | query side (tasks filed 2006-2013 publish 2006-2016) + cited pre-grant publications | 16 | 5.01 GB |
| `g_claims_1976` … `g_claims_2013` | cited grants (RPD visibility ends 2013) | 38 | 6.27 GB |
| **Total** | | 54 | **11.28 GB** |

Not needed now: g_claims 2014-2025, pg_claims 2017-2025 (7.9 GB) — after every split's RPD window.
Already downloaded for P2/P1: ~2.7 GB (16 Nov) + 0.87 GB continuity. Running total after this ≈ 14.8 GB of 60 GB.
Files are read streaming from the zip; no unzip to disk is planned. Abstracts: `g_patent_abstract` (1.5 GiB in the 2025 mirror)
and the pre-grant abstract table are still to be checked against what `g_patent`/`pg_published_application` already hold.
Download needs the owner's ODP sign-in (CAPTCHA), destination `data/raw/uspto/` as before.
