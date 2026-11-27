# FIX2 | Active-moiety entity linkage

## Result

**Implemented and audited. Validation found residual linkage errors.** `build_entities` defaults to the GSRS-backed product moiety key. Use `key_mode="legacy"` to reproduce the prior ingredient key. The fresh development audit found 0 false merges, 11 false splits and 2 unresolved cases among 60 keys. The remaining 47 were supported within the available evidence. The repeated split between named and UNII-resolved records warrants planner review before benchmarking with the new key.

## Validation protocol

The resolver uses the 2026-08-06 public GSRS edition and the hash-verified S0 openFDA Drugs@FDA and Orange Book files. Full composition is a sorted set of UNII moieties per product. Keep separate product compositions within a mixed application. Use dated product evidence for mixed applications and retain unknown dates where the original approval cannot be allocated. Review semantic evidence from product fields, scoped harmonization, GSRS relationships and corroborating FDA records. Treat ambiguous linkage and insufficient evidence as unresolved.

Compare both methods on the same S0 inputs. Count entities, NDA-approved NME entities as of 2014-01-01, and at-risk NME rows on annual January 1 cutoffs 1995–2016 at horizons 12, 24 and 36 months. Report the subset whose label windows end strictly before 2017-01-01 separately. No model scoring.

Replay the 87 resolved T7 design verdicts against their cited anchors plus candidate neighbors. A correct grouping must preserve the supported same-set links and separate distinct product compositions. Grade repaired, residual error or unresolved with row locators. For the fresh audit, remove new keys containing any T7 sampled-key application or sharing their new composition keys, then draw 60 without replacement with Python Random(20261129) from lexically sorted keys with first NDA on or before 2014-01-01. Keep the draw fixed. Inspect native product and harmonized fields and independently corroborate aliases, composition or ambiguity as needed. Search for both composition collisions and aliases under other keys. Give false merge priority when both errors are supported. Report unresolved separately, including limited source evidence. The fresh sample estimates errors in the held-out development frame.

The initial packet contained two applications cited as cross-key anchors in T7. Before assigning fresh verdicts, extend the exclusion to all cited T7 anchors. Keep the original draw positions and fill the two affected slots from the remaining eligible keys using the same RNG state. This removed the alogliptin and trovafloxacin keys and inserted urea and trametinib. The final frame is 1,661 of the 1,771 eligible development keys. The 110 exclusions, replacement mapping and final draw are in [FIX2_counts.json](../../../loe-bench/data/FIX2_counts.json).

## Sources

- FDA-curated NCATS GSRS public export, 2026-08-06. The downloaded gzip has 329,396,273 bytes and SHA-256 `07be61aea161cd212545c6cc1057a376bdbefcfc634da7ab1b4903b99f7bacad`. Read the tab-delimited JSON record, locate by `approvalID`, and inspect `names[].name` and `relationships[type="ACTIVE MOIETY"].relatedSubstance`. The usage terms dedicate public data to CC0 1.0 unless noted. [Download](https://gsrs.ncats.nih.gov/assets/downloads/dump-public-2026-08-06.gsrs) · [Public release](https://gsrs.ncats.nih.gov/) · [GSRS data licence](https://gsrs.ncats.nih.gov/licensing)
- S0 openFDA Drugs@FDA and Orange Book snapshots, frozen 2026-11-27. Seven file hashes were verified. The manifest records each exact API URL template, query, edition and hash. The relevant fields are generally CC0 1.0 under the openFDA data terms. [S0 input manifest](../../../loe-bench/data/S0_INPUT_MANIFEST.json) · [Data terms](https://open.fda.gov/terms/)
- FDA's active-moiety definition excludes the appended portions of salts, esters and noncovalent derivatives. GSRS supplies substance relationships, and its multiple targets can require reconciliation with product-specific evidence. [FDA Orange Book preface, note 7](https://www.fda.gov/drugs/development-approval-process-drugs/orange-book-preface)

The additional public source copies below support only the audit. The SPLs are publicly available company submissions, subject to the cited DailyMed terms and limitations. The VERARD approval package is FDA-published material. The raw copies are outside Git. [DailyMed terms and disclaimer](https://dailymed.nlm.nih.gov/dailymed/about-dailymed.cfm) · [FDA website policy](https://www.fda.gov/about-fda/about-website/website-policies)

| Local file and edition | SHA-256 | Source |
| --- | --- | --- |
| `FIX2_pentetate_spl.html`, 2026-11-16 v6 | `041cb7b911cd3cc3d0bb3f308475c2c735db4e522f2416fcb8046ab834867da6` | [NDA021751 pentetate zinc trisodium SPL](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=366e7ca9-4fd3-4688-bd83-1f369885e0fc) |
| `FIX2_nicotine_074507_spl.html`, 2026-08-19 v31 | `b44be6c09888c58da5fcdaa4adabf548b7a98ecbfda89f797523a7eb96613a66` | [ANDA074507 nicotine polacrilex SPL](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=1fc88637-4329-486e-82ab-19eeb06080a6) |
| `FIX2_azstarys_spl.html`, 2026-05-13 v9 | `12c7d643c6fbfbfa3f19082580d6c6fb9ed61535039c5fe918c429e42538d474` | [NDA212994 AZSTARYS SPL](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=00b5e716-5564-4bbd-acaf-df2bc45a5663) |
| `FIX2_verard_fda.pdf`, 1939-08-30 original approval package | `1f99215d8e54fed758e221e5aa95676db88cd959a0d29e10b38c0cfda77b384d` | [NDA001504 VERARD approval package](https://www.accessdata.fda.gov/drugsatfda_docs/nda/pre96/001504Orig1s000.pdf) |

## Evidence

- **T7 design sample:** 74/87 agreed overall. FIX2 repaired 15/22 confirmed errors and preserved 59/65 correct groupings. The other 13 include the retained helium false merge and 12 split cases, two of which were originally compound-level merges repaired only in part. [T7 replay with product and label locators](../../../loe-bench/data/FIX2_design_audit.csv)
- **Fresh audit:** 47 supported groupings, 0 observed false merges, 11 false splits and 2 unresolved. The observed split fraction is 11/60 (18.3%). The 11 splits include 10 identical native ingredient sets separated by annotation availability and one nicotine polacrilex versus nicotine split. Review used the applications under each selected key and screened neighboring keys for duplicate full sets. The audit description, candidate screen and labels support a single-executor assessment of this held-out frame. [Fresh 60 with adjudication and locators](../../../loe-bench/data/FIX2_fresh_audit.csv)
- The default reads the pinned export from a sibling `moiety/` directory beside the raw snapshot directory. Supply `gsrs_path` to point to another copy of the same verified export. A missing default file yields low-confidence name resolution. The registry joins exact normalized aliases and uses harmonized UNIIs to disambiguate matching candidates. Names without a usable UNII may fall back to conservative trailing salt and hydrate rules. Explicit listed electrolyte identities preserve the cation and phosphate qualifiers. Product-scope corroboration is required before harmonized fields add any component. The current snapshot and historical edition lookup use the moiety representation. The historical lookup uses raw historical ingredient names without current label supplementation.

| Count | Legacy | Moiety |
| --- | ---: | ---: |
| Entities | 2,520 | 2,504 |
| Entities with first NDA by 2014-01-01 | 1,783 | 1,771 |
| NME cohort as of 2014-01-01 | 1,092 | 1,070 |
| Low-confidence keys | Not tracked | 268 |
| 12-month rows, development cutoffs | 11,992 | 11,756 |
| 24-month rows, development cutoffs | 11,992 | 11,756 |
| 36-month rows, development cutoffs | 11,992 | 11,756 |
| 12-month rows, windows ending before seal | 11,425 | 11,205 |
| 24-month rows, windows ending before seal | 10,861 | 10,654 |
| 36-month rows, windows ending before seal | 10,299 | 10,104 |

From `loe-bench/` with Python 3.12.10:

```powershell
$fix2Root = 'C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench'
rtk proxy python scripts/fix2_audit.py --raw-dir "$fix2Root/raw-20261127" --gsrs "$fix2Root/moiety/dump-public-2026-08-06.gsrs" --packet-dir "$fix2Root/moiety"
rtk proxy python -m unittest discover -s loe_bench/tests -t .
```

The packet command reconstructs the frame, draw, counts and source packets. A rerun reproduced the counts file SHA-256 `f67a8c95ed2f4811095b1c036a9d09ce0aee0d80f0eadcd13d0ffea69f0d42c5`. The two CSVs preserve the executor's row-level adjudication. The unittest suite passed 82 tests, exit 0. The existing Purple Book ResourceWarnings remain. Repository root pytest with `--tb=short --basetemp C:/Users/User/AppData/Local/Temp/ptp-fix2-7ea7-check` returned 2,760 passed, 50 skipped, one xfailed and the eight allowed SACR r2/r3 supervisor-budget failures, exit 1. No real-data model, protected evaluation split or lock was used.

## Failures and limitations

- Missing or ambiguous exact-name evidence accounts for most residual splits. For example, the carvedilol and amlodipine series contain identical native substance names assigned differently depending on usable UNII hints. GSRS and application-level labeling can also disagree. The pentetate zinc SPL names pentetic acid alone, while the GSRS export has two targets for the registered zinc trisodium substance. No second full matching key was confirmed for that case. The VERARD package identified a trade name without sufficient active-ingredient evidence.
- For mixed original applications, a product can inherit the application date when verified product evidence supports its presence by that date. Later or undated variants with no corroborating original date have a key with an unassigned event date. This changes dated cohort and ANDA linkage counts. It cannot reconstruct earlier approval status or historical labeling for every product. The historical Orange Book lookup cannot recover a missing product component from its ingredient string alone.
- A supplemental nicotine SPL URL failed the evidence-content check. The audit used the pinned ANDA074507 SPL identified in S0 instead. Two seen anchor rows entered the first fresh draw through the cross-key exclusion oversight. The documented uniform replacements corrected this before adjudication. The original normalization-only T7 script should be replayed at its original revision because it calls the builder default.
- The fresh rates apply to a held-out slice of the new key space. T7 used stratified sampling from the legacy key space. A claim that one system has a lower population error rate would require a common audit design and denominators. Historical use of the 2026 GSRS edition also requires an explicit methodology decision for any as-of claim.

## Next action

The main planner reviews the row-level evidence, decides how to resolve conflicting exact-name aliases and GSRS/SPL differences, and updates the lane records. Preserve both audit draws as exposed evidence for subsequent resolver revisions. Use a new held-out draw to assess a revised mapping before adopting it in a locked evaluation.
