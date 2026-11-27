# E7b | Historical Orange Book patent links

## Result

**PASS for development execution.** By 2016-01-01, 1,065 of 26,107 filed Rai cases had a patent match in an eligible Orange Book edition. The join produced 1,270 distinct case–moiety pairs across 259 moieties. The at-risk NME cohort gained 69 TRUE leaves at that cutoff. FALSE remains available only at the three E7 cutoffs with a verified fresh FDA PIV edition.

| Cutoff | Rai cases with a listed patent / all filed cases | Case match rate | Moieties with a patent witness | Moieties with any Rai witness | At-risk NME with a patent witness | Before TRUE / FALSE / UNKNOWN | After TRUE / FALSE / UNKNOWN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2010-01-01 | 0 / 0 | — | 0 | 0 | 0 | 74 / 473 / 0 | 74 / 473 / 0 |
| 2011-01-01 | 0 / 1 | 0.00% | 0 | 0 | 0 | 86 / 448 / 0 | 86 / 448 / 0 |
| 2012-01-01 | 151 / 3,606 | 4.19% | 89 | 89 | 24 | 89 / 444 / 0 | 92 / 441 / 0 |
| 2013-01-01 | 331 / 9,077 | 3.65% | 144 | 144 | 41 | 1 / 0 / 538 | 41 / 0 / 498 |
| 2014-01-01 | 547 / 15,198 | 3.60% | 181 | 181 | 54 | 1 / 0 / 543 | 54 / 0 / 490 |
| 2015-01-01 | 707 / 20,280 | 3.49% | 217 | 218 | 63 | 2 / 0 / 543 | 64 / 0 / 481 |
| 2016-01-01 | 1,065 / 26,107 | 4.08% | 259 | 259 | 71 | 2 / 0 / 544 | 71 / 0 / 475 |

The filing denominator deduplicates the source on court, docket and filing date. E7's name-link rate used source rows. Any Rai witness includes patent matches and corroborated name witnesses. TRUE counts include the FDA PIV path. The 2016 row measures coverage only.

At 2016-01-01, both the patent path and raw name resolver assigned keys to 913 cases, with 912 exact key-set agreements and one partial overlap. There were 151 patent-only cases, 544 raw-name-only cases and 24,499 cases with neither assignment. Patent matches reached multiple moieties in 130 cases, including cases with several distinct asserted patents. The reviewed E7 name path agreed exactly on four of its seven admitted cases. The other three remain eligible through names. The patent inventory flags four pairs as ANDA-corroborated and 1,266 as unspecified.

| Rai TSV locator | Example of an unmatched row |
| --- | --- |
| Line 2 | Patent 5322055, S.D.Ohio 1:11-cv-00871, had no fresh availability-proven edition at filing. |
| Line 711 | E.D.Tex. 2:11-cv-00417 had an empty patent field. |
| Line 18 | Patent 5844596, D.Del. 1:11-cv-00339, was absent from the selected 2011-03-18 edition. |
| Line 38810 | Patent 7476652, D.Del. 1:14-cv-00113, was present in the 2013-08-30 edition and lacked a resolved moiety approved by filing. |

| Validation horizon | Rows | Drug clusters | Event clusters | OPEN | BLOCKED | CONTESTED |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 12 months | 2,161 | 609 | 90 | 87 | 587 | 1,487 |
| 24 months | 1,083 | 561 | 67 | 55 | 181 | 847 |

| Horizon | Arm | AURC80 | Brier | ECE | Coverage |
| --- | --- | ---: | ---: | ---: | ---: |
| 12 | B1 | 0.018575 | 0.039073 | 0.005471 | 100.00% |
| 12 | M1 | 0.012563 | 0.036756 | 0.006428 | 98.89% |
| 12 | M2 | 0.034704 | 0.039982 | 0.003845 | 100.00% |
| 12 | M3 | 0.011813 | 0.037107 | 0.008549 | 98.80% |
| 24 | B1 | 0.029330 | 0.073047 | 0.007294 | 100.00% |
| 24 | M1 | 0.019694 | 0.065274 | 0.020926 | 92.24% |
| 24 | M2 | 0.067111 | 0.075511 | 0.009583 | 97.14% |
| 24 | M3 | 0.020643 | 0.065436 | 0.015272 | 93.17% |

| Horizon | M3 − B1 ΔAURC80 (95% CI) | M3 − M1 ΔAURC80 (95% CI) | M1 − B1 ΔAURC80 (95% CI) |
| --- | ---: | ---: | ---: |
| 12 months | −0.006762 [−0.012407, −0.001366] | −0.000750 [−0.001898, +0.000549] | −0.006012 [−0.011853, −0.000421] |
| 24 months | −0.008688 [−0.019380, +0.001702] | +0.000949 [−0.001826, +0.005932] | −0.009636 [−0.018772, −0.001754] |

Each interval uses 2,000 valid paired drug-cluster draws. The M3 versus M1 intervals include zero at both horizons. The M3 versus B1 interval lies below zero at 12 months. Both M3 versus B1 point estimates fall short of the criteria v2 practical threshold of −0.010. M1 and M3 each tried three configurations per horizon and selected L2 = 100. The results are conditional on development tuning.

## Development protocol

Use the FIX2c cohort and the E7 development split, embargo, model features, grids, and calibration. Score validation at 12 and 24 months. Use E7's paired 2,000-draw drug-cluster bootstrap for M3−B1, M3−M1, and M1−B1. Apply the same challenge indicator and missingness flag to M1 and M3.

For filings through each cutoff, group Rai rows by court, docket, and filing date. Normalize each patent as a single US grant number, preserving design, reissue, and plant prefixes. Choose the newest Orange Book edition dated and proven available by filing, subject to the existing six-calendar-month freshness rule. Verify the ZIP digest before using its contents. Join each exact patent hit through the listed NDA product to the FIX2c active-moiety key. Require the moiety's first NDA approval by filing. Count a patent match even when its NDA identity is unresolved, but admit a witness only for a resolved key. Retain all resolved keys and flag shared patents through the case-level agreement audit. A listed patent with a delisting flag still supplies a listing witness, with the flag retained.

Use E7's corroborated name path as secondary evidence and retain both paths where they agree. Compare the entire nonempty case-level key sets produced by patent matching and by E7's raw brand/ingredient resolution. Also compare the sets produced by patent matching and by the admitted name witnesses. Classify exact agreement, partial overlap, disjoint sets, and one-path-only cases. Keep the FDA PIV freshness and evidence rules from E7. A timely witness from any admitted source makes the leaf TRUE. With zero witnesses, a verified fresh FDA PIV edition makes it FALSE. Otherwise it is UNKNOWN.

Rai's public-at-filing assumption applies to the event date. An Orange Book match is a patent-linked challenge proxy and may include 505(b)(2) or other litigation. Carry E7's reviewed case type only where its product attribution agrees. Keep EDGAR outside this replay.

## Evidence

From `loe-bench/` with Python 3.12.10 and the pinned local input directories:

```powershell
python -m unittest discover -s loe_bench/tests -t .
python -B scripts/e7b_dev_run.py
```

The unittest command exited 0 with 115 passing tests and existing Purple Book file-handle warnings. The E7b fixtures cover US grant normalization, the filing and cutoff boundaries, proof and freshness, digest mismatch, the dated NDA requirement, witness deduplication and preservation of both paths.

From the repository root, `python -B -m pytest --tb=short --basetemp C:/Users/User/AppData/Local/Temp/ptp-e7b-500b02f1 -p no:cacheprovider` exited 1. It reported 2,760 passed, 50 skipped, one xfailed and the eight accepted SACR r2/r3 supervisor budget failures. [Repository test policy](../../../AGENTS.md)

The Rai TSV is Harvard Dataverse version 1.0, file 4789869, released 2021-06-10 under CC0 1.0. Replay verifies the TSV, metadata, E7 corroboration, dated Orange Book ZIPs, and FIX2c inputs. The witness inventory identifies each case and patent by its TSV line. Each matching Orange Book listing carries the ZIP digest, availability proof and patent table data-row number, counted from 1 after excluding the header and empty rows. It also carries the FDA application and product numbers. [Rai data release](https://doi.org/10.7910/DVN/YCMKVU) · [E7 source manifest](../../../loe-bench/data/E7_sources.json) · [Orange Book edition manifest](../../../loe-bench/data/OB_EDITIONS.json)

The replay exited 0. The output audit verified matching E7 baseline counts, identical cohorts and B1 AURC80, Brier and ECE, witness and edition date bounds, source digests, case and pair totals, graph verdict totals and paired draw counts. The preregistration lock and seal environment variable were absent. [Development summary](../../../loe-bench/data/E7b_dev_summary.json) · [Patent witness inventory](../../../loe-bench/data/E7b_patent_witnesses.json) · [E7 FDA and name witness inventory](../../../loe-bench/data/E7_witnesses.json)

| Output | SHA-256 |
| --- | --- |
| Development summary | `9826261061c0e1118ef0eb1cec4d878bf8192290511b763966bf5b4dcb4a0808` |
| Patent witness inventory | `3da2ac19400227e892d5ed20033e451cef09951f59a69079e3dfb38c4e598682` |

## Failures and limitations

- The Rai table reports the case filing date and a patent association. The original complaint and the date when each patent entered the record were unverified for the new pairs. Patents added to a case later could therefore be dated too early. The data provide no ANDA or 505(b)(2) field. A shared patent may also attribute a single case to more than one drug. E7's corroborated names retain their own source and review trail. [Rai et al., Section III.B](https://btlj.org/wp-content/uploads/2023/02/0003-37-1-Rai.pdf#page=18)
- The six-month requirement leaves gaps at filing. Recent listings between the selected edition and filing can also be missed. The modern FIX2c identity crosswalk can resolve aliases retrospectively. A case witness stays positive at later cutoffs and carries no resolution, expiry, exclusivity or entry outcome.
- The FDA PIV negative remains an operational absence under the fresh-edition rule. Unmatched FDA rows and unobserved, unclassified or delayed filings can leave relevant information outside the join.
- The initial replay was stopped before it wrote artifacts after the normalization tests extended support to historical US kind A and zero-padded grant identifiers. The final replay used the expanded normalization. The Berkeley article landing page returned HTTP 403 in the web reader and the DOI resolver was unavailable there. The journal's published PDF supplied the methods section. The replay used the local E7 inputs.
- The first push of `2bf7240` returned GitHub's `[remote rejected] (failed)` response without a specific cause. A follow-up `git ls-remote origin refs/heads/loe/E7b` returned no ref. Publication is retried from the same checkout with an explicit refspec.

## Next action

The main planner can review the patent-only and shared-patent links against original complaints before deciding whether to preregister this challenge proxy. The protected test remains sealed.
