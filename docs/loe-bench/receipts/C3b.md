# C3b | Historical applicant identity and native development scores

## Protocol before scoring

The main planner amended C3 after exact-day documentation resolved four of the 221 linked ANDAs in the 2013 window. Use the earliest historical Orange Book edition that lists the ANDA from its approval day through 12 calendar months later, inclusive. Keep documented approval-day holders and transfer intervals as overrides. Report the current Drugs@FDA sponsor as a sensitivity analysis. Apply the existing date-scoped aliases and preserve the published FDA applicant designation in the evidence trace. [C3 receipt](C3.md) · [C3 specification](../../../loe-bench/data/C3_SPEC.json)

Replay 12- and 24-month development scores with the pinned FREEZE implementation. Check exact numerical equality against the published report before releasing the per-row native scores. Use the full original predicted roster for each cutoff. Score 36-month C3 labels only at the 2013-01-01 cutoff using the original 24-month predictions. Keep the threshold, queue capacity, ties, missingness rules and bootstrap from C3. The replay uses local CPU, the closed seal and guarded development evidence. [FREEZE receipt](FREEZE.md)

Version 2 was pinned before replay at `28721e3ab7ec072cdb6aedca5aab4af1fd60a80f`. Its SHA-256 is `8179101bb7a0adf9e8659bcb0978c73bd32ee869506a50027537741a45e3b0fd`. [Checksum](../../../loe-bench/data/C3_SPEC.sha256)

## Applicant coverage and sensitivity

**DEVELOPMENT_ONLY.** The guarded intake reproduced 11,753 original final ANDAs through 2016-01-01, including 14 without an admissible group. The four audit cutoffs contributed 609 distinct linked applications. The replay checked 11 dated FDA ZIPs and six annual FDA editions hosted by NBER. The annual products chapters carry applicant names. The NBER Stata archive covers patents and exclusivity. Archive hashes and listing locations appear in the private report. ZIPs use the manifest edition date. Annuals follow the existing December 31 convention when publication dates are unavailable. [FDA edition manifest](../../../loe-bench/data/OB_EDITIONS.json) · [NBER manifest](../../../loe-bench/data/E8_NBER_MANIFEST.json) · [Approval-day evidence](../../../loe-bench/data/C3_DEV_APPLICANT_EVIDENCE.json)

| Cutoff | Rows | Linked ANDAs | FDA ZIP / annual / direct | Unresolved ANDAs | Applicant agreement | Primary / sponsor event rows | Threshold labels different |
| --- | ---: | ---: | --- | ---: | --- | --- | ---: |
| 2010-01-01 | 547 | 307 | 299 / 3 / 0 | 5 | 151/302 (50.00%) | 32 / 32 | 0 |
| 2011-01-01 | 534 | 282 | 277 / 0 / 2 | 3 | 138/279 (49.46%) | 28 / 29 | 1 |
| 2012-01-01 | 533 | 300 | 296 / 0 / 2 | 2 | 138/298 (46.31%) | 27 / 28 | 1 |
| 2013-01-01 | 539 | 221 | 215 / 0 / 4 | 2 | 73/219 (33.33%) | 21 / 21 | 0 |
| Pooled audit | 2,153 | 609 | 594 / 3 / 4 | 8 | 268/601 (44.59%) | 108 / 110 | 2 |

The pooled application counts deduplicate repeated windows. The primary rule resolved 601/609 linked ANDAs, including 219/221 in the scored window. Earliest used editions were 2–363 days after approval. Both rules gave determinate labels on all rows. Two rows crossed from primary negative to sponsor positive. The 108 primary event rows came from 59 distinct drugs, and the 110 sponsor event rows came from 60. The six predecessor threshold fixtures were determinate under the primary rule. The three two-application rows were negative and the three three-application rows were positive.

Agreement is exact under Unicode, case and whitespace normalization and any applicable evidenced aliases. FDA Orange Book applicant designations can be abbreviated. Differences therefore include naming conventions as well as possible changes of holder. The first available listing can follow a transfer. Whole-window bounds condition on the linked approvals observed in the pinned sources. The unknown applications in this run could not change a row at the three-applicant threshold.

## Native score export and verification

**PASS.** Replayed the FREEZE config and complete published development report with exact parsed-value equality from implementation `f683017c4fb73aadd91bb97f3381f5dd9308c9ca`. The observer recorded native risks from the validation calls. It passed the original values through to FREEZE scoring. Run-time guards removed later NDA approval values before decoding while retaining linkage metadata. The replay matched the original published configuration, inputs, fitting summaries, annual queue audits, pooled metrics and bootstrap values. Float serialization round-tripped exactly for the released scores. [Frozen config](../../../loe-bench/data/FROZEN_CONFIG.json) · [Published report](../../../loe-bench/data/FREEZE_dev_report.json) · [Export and verification manifest](../../../loe-bench/data/FREEZE_DEV_SCORES_MANIFEST.json)

| Horizon | Scope | Rows | Event rows | Slots | Published checks |
| ---: | --- | ---: | ---: | ---: | --- |
| 12 | 2012-01-01 | 533 | 23 | 106 | All three arms, exact annual audit |
| 12 | 2013-01-01 | 539 | 17 | 107 | All three arms, exact annual audit |
| 12 | 2014-01-01 | 544 | 24 | 108 | All three arms, exact annual audit |
| 12 | 2015-01-01 | 545 | 26 | 109 | All three arms, exact annual audit |
| 12 | Pooled | 2,161 | 90 | 430 | All three arms, exact recall, precision and AP |
| 24 | 2013-01-01 | 539 | 41 | 107 | All three arms, exact annual audit |
| 24 | 2014-01-01 | 544 | 50 | 108 | All three arms, exact annual audit |
| 24 | Pooled | 1,083 | 91 | 215 | All three arms, exact recall, precision and AP |

The published annual audit stores roster size, capacity, allocated slots, expected event hits and boundary tie counts. The published event rows, recall, precision and AP reference values are pooled by horizon. The manifest records cutoff event counts, recall, precision and AP as replay diagnostics, along with all published equality checks.

| Private artifact under `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/` | Rows | SHA-256 |
| --- | ---: | --- |
| `FREEZE_dev_scores.json` (24 months) | 1,083 | `53c1aaae5b3bd474e181774f3eacdee3c76a0b4b2cee8e920e5bd186152e5f79` |
| `FREEZE_dev_scores_12m.json` (12 months) | 2,161 | `e9f7d9af0033207488adf1bb582e24a12982d5d72039ce8c8c611b1792227db7` |

Both files preserve the full original validation rosters. Each row contains the cutoff, drug key and native M3 and B1 probabilities. C2 can reuse the files by digest.

## C3 development queue result

**DEVELOPMENT_ONLY.** The mature 2013-01-01 validation cutoff has 539 rows and 107 slots in each arm. Both identity rules yielded 21 event rows from 21 drugs, 518 negative rows and zero unknown rows. The 24-month risks rank the 36-month competition outcome.

| Rule | M3 recall | B1 recall | M3 minus B1, pp | Paired 95% interval, pp |
| --- | ---: | ---: | ---: | ---: |
| Historical edition with direct override | 71.43% | 45.83% | +25.60 | [+6.25, +45.00] |
| Current Drugs@FDA sponsor | 71.43% | 45.83% | +25.60 | [+6.25, +45.00] |

Each interval used 2,000 paired drug-cluster draws and had zero undefined draws. The arms captured 15.000 and 9.625 expected event rows, respectively, under the fractional tie rule. The all-unknown-negative, all-unknown-positive and conditional outer capture bounds each equal the point recalls and difference because no row is threshold-ambiguous.

The private report `C3b_dev_report.json` has SHA-256 `60d931d4f39082540bd8d8e19475fa1cf5599bf30437f95d1686d365b3597ebb`. It records the edition-by-edition source inventory, per-application decision and provenance, six fixture rows, per-cutoff agreement and unrounded estimates.

## Reproduction and checks

Use Python 3.12.10, NumPy 2.5.4 and PyMuPDF 2.0 with the pinned local archives. From the C3b repository root, create the detached checkout and a fresh destination.

```powershell
$pinned = 'C:/Users/User/ptp-C3b-freeze-f683017c'
$replay = Join-Path $env:TEMP "ptp-C3b-$([guid]::NewGuid())"
[System.IO.Directory]::CreateDirectory($replay) | Out-Null
rtk proxy git worktree add --detach $pinned f683017c4fb73aadd91bb97f3381f5dd9308c9ca
rtk proxy python loe-bench/scripts/freeze_dev_scores.py --implementation $pinned --out-dir $replay --manifest (Join-Path $replay 'FREEZE_DEV_SCORES_MANIFEST.json')
```

From `loe-bench`, run the following with a new report path.

```powershell
$report = Join-Path $env:TEMP "C3b-$([guid]::NewGuid()).json"
rtk proxy python scripts/c3_dev_run.py --history data/C3_DEV_APPLICANT_EVIDENCE.json --history-sha256 961c5df8be29a33a4d6260d4ca68dd46b1acb1cb19e769c408e3a49d8acfe506 --frozen-scores C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/FREEZE_dev_scores.json --scores-sha256 53c1aaae5b3bd474e181774f3eacdee3c76a0b4b2cee8e920e5bd186152e5f79 --output $report
rtk proxy python -m unittest discover -s loe_bench/tests -t .
```

- **PASS**, LOE-Bench unittest discovery, 199 tests and exit 0. The existing Purple Book tests emitted file-handle ResourceWarnings.
- **Standing failures**, root `python -m pytest -q`, exit 1. The eight failures were the known SACR r2/r3 supervisor budget cases.
- **PASS**, both private exports rehashed against the manifest after writing. The scorer checked the entire 24-month export schedule and exact keys at the C3 cutoff.

## Main-planner handoff and memory

The closeout evidence supports development applicant coverage and a measured C3 queue comparison on one mature cutoff. Preserve the applicant designation limits and the pooled-versus-annual reference distinction for preregistration v2. The main planner should review this receipt, integrate C3b and pass the pinned score files to C2. Confirmatory scoring remains subject to the existing seal and the preregistration release. This receipt is the executor's handoff and project-memory entry for planner integration.
