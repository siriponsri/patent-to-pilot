# manifest-v2: family-aware canonical split (2026-11-18)

Status: BUILT on dr-train, **not frozen**. Metadata only; `pairs.tsv`/labels not read; no GPU/API; USD 0.

## Inputs
- PatentsView ODP release 2026-04-10, downloaded by the owner 2026-11-18 (ODP sign-in), copied to dr-train `/data/ptp-paper2/patentsview/` (read-only):
  `g_us_rel_doc.tsv.zip` 380ede32…, `pg_us_rel_doc.tsv.zip` 60785fb4…, `pg_rel_app_text.tsv.zip` a64c195d…, `g_rel_app_text.tsv.zip` 1946296c… (zip CRC test OK, local = remote SHA256).
- Grouping rule declared in `scripts/healthtech/build_continuity_related.py` and committed (94de206) before the first run.
  Primary edges: continuation, CIP, division, substitution, reissue, continuing-reissue (grant + pre-grant tables). Provisional links = sensitivity only.

## Continuity run (CPU, 4 min 57 s, 3.7 GB RSS)
| Variant | groups | tasks in multi-task groups | max tasks/group | tasks with any link |
|---|---|---|---|---|
| primary (used) | 350,857 | 46,708 (12.4 %) | 75 | 131,752 |
| + provisional (sensitivity) | 345,945 | 53,570 | 192 | 192,912 |

## Manifest (CPU, 5.2 s) — manifest_sha256 `c8443600d74fed015213237e070882efd1ddeefef7e66b6f3d6f7bb2f31e8039`
| Block | v1 (singleton) | v2 (family-aware) |
|---|---|---|
| TRAIN 2006-2009 | 100,376 | 100,376 |
| VAL 2010 | 2,000 | 2,000 |
| P1-DEV / P2-DEV 2011 | 26,320 / 26,486 | 26,575 / 26,231 (imbalance 0.65 %) |
| P1-TEST 2012 tail | 10,000 | 10,000 (identical membership rule) |
| P2-TEST 2012 prefix | 44,074 | **43,587** (option A removed 487 tasks sharing a family with P1-TEST) |
| P3-TEST 2013 | 55,307 | 55,307 |

Assertions: A1-A4 PASS; **L-B PASS** (0 shared groups P1-DEV/P2-DEV, 0 shared groups P1-TEST/P2-TEST); A3 PASS.
Cross-year family exposure (reported as stratum `seen_family`, never deleted): P1-TEST 581, P2-TEST 2,222, P3-TEST 2,722 tasks
share a group with TRAIN/VAL(sample)/DEV.

Limits: grouping covers US domestic continuity only (no foreign priority / DOCDB family); VAL cross-check uses the 2,000 sampled
2010 tasks, not all of 2010. Raw-id manifest and salted public view stay on dr-train `/data/ptp-paper2/manifest-v1/out-v2/` (mode 700).
v1 is kept as the superseded singleton build.
