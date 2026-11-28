# SCORE | Authorized C′ historical scoring

## Execution protocol

The governing text is the [OSF registration](https://doi.org/10.17605/OSF.IO/P2SMD) with approved [update 1](https://api.osf.io/v2/schema_responses/6b0a5e871c2cd96b1746bce7/) and [update 2](https://api.osf.io/v2/schema_responses/6b0a61a4341762fcbae66946/). Read it with the [audited preregistration at bef62d64](https://github.com/siriponsri/patent-to-pilot/blob/bef62d64/docs/loe-bench/PREREGISTRATION.md), [owner release](../../maintenance/OWNER-DECISIONS-20261122.md), [custodian decision](GATE.md), [FREEZE](FREEZE.md), [C3b](C3b.md) and [C4b](C4b.md).

The CPU runner verifies the live registration, lock, approval records, manifests, required source digests, frozen implementation and annual editions. The lock binds the canonical original OSF record. The latest approved schema response governs the analysis. Reconstruct the final development TRAIN fits once, and check the frozen calibration, policy and development scores before enabling the seal in the scoring process. The private custodian projection is outside the scoring inputs. Send dated features to the prediction functions and send event labels only to the scorer. Use the registered full C′ rosters and native scores at 12 and 24 months.

Each arm gets `floor(N/5)` slots per cutoff and expected allocation at the boundary tie. Use 2,000 common whole-drug resamples within each horizon, PCG64 seed 20261127, and linear percentile quantiles. Test H1, H2 and H3 in order and stop inference at the first lower bound that is undefined or at most zero. Keep estimable later contrasts descriptive. Report the +10 pp check separately. Preserve all draws and both per-row native score exports outside Git.

C3 uses the full 2017–2023 24-month queue rosters with 36-month applicant labels. Evaluate historical and pinned snapshot-sponsor rules using the registered bounds and failure rules. Look up the first eligible applicant listing in the pinned dated editions. The registered direct-evidence pack covers development approvals. C4 admits no origin from 2017 under the registered specification and its frozen outcome files stop at the 2016 origin's 2017 target year. The reserved C4 analysis is `NOT_RUN`. L1 and L1e belong to SCORELLM.

## Release checks

| Check | Disposition | Evidence |
| --- | --- | --- |
| Checkout and writer | PASS | Fetched origin and created the dedicated SCORE branch from e0f1872e. SCORELLM writes its own paths. |
| OSF registration | PASS | 10.17605/OSF.IO/P2SMD, public and accepted, registered 2026-11-28T03:59:09.365844 UTC. |
| OSF update 1 | PASS | Approved response `6b0a5e871c2cd96b1746bce7`. The lock binds the original canonical record. |
| OSF update 2 | PASS | Approved and current response `6b0a61a4341762fcbae66946`. The C9 timing amendment leaves the historical estimands unchanged. |
| Registration key | PASS | `python scripts/osf_lock.py` reproduced `3f91145251465b0ed9c89233337748e1b9fd84db8c4c2a6158860374670e1c77`. The canonical file and the wrapper's sha256 field match. The wrapper file's own SHA-256 is `7e37bd53485ee7a2981025d1351896d7a263d6b45f30c60f1ecf1e560e970b99`. |
| First author and custodian | PASS | Owner release of 28 November 2026, co-planner clearance for both OSF updates, and GATE verdict PASS. The executor read the receipt. |
| C3_SPEC.json canonical LF | PASS | `8179101bb7a0adf9e8659bcb0978c73bd32ee869506a50027537741a45e3b0fd` |
| C4_SPEC.json canonical LF | PASS | `c0644bb4c1ed9d6050e256191c85bb34dd120a73b6da78850a1faf80e2c400f0` |
| FROZEN_CONFIG.json canonical LF | PASS | `d40119189b9e3b3b319f16449ac672766d46de2272dd9579eadaa8d23eb27c39` |
| S0_INPUT_MANIFEST.json canonical LF | PASS | `7d40be5e2004d887480ce5f337afffd611909f26017622e90ad304a0386d2d1d` |
| Implementation | PASS | `f683017c4fb73aadd91bb97f3381f5dd9308c9ca`. All reused FREEZE runtime blobs match the pin. The SCORE adapter SHA-256 is `6b6f37e09d0ca209a4c83f65fdffd1a29cc295dd941fe64acde6e2eb2214450b`. |
| Local source and cutoff checks | PASS | All eight S0 payloads and the admitted Orange Book, PIV, Rai, corroborating files and GSRS passed their digests. All cutoffs have digest-matching, availability-proven FDA editions within six months. The outcome observation end is 2026-11-27. |
| Frozen development fits | PASS | Python 3.12.10, NumPy 2.5.4, CPU only. TRAIN settings and fitted policy matched the config, native B1 and M3 development exports matched exactly, and all three development queue audits matched. |
| Execution authorization | PASS | The process sets the verified lowercase LOE_PREREG_SHA256 only after release and development parity. The process removes it at exit. |

## Primary family

| Horizon | Annual cutoffs | Rows | Unique drugs | Event rows | Event drugs | Slots per arm |
| --- | --- | --- | --- | --- | --- | --- |
| 12 | 2017–2025 | 5259 | 803 | 202 | 202 | 1048 |
| 24 | 2017–2024 | 4639 | 771 | 368 | 202 | 924 |

| Step | Contrast | Difference, pp | Two-sided 95% CI, pp | One-sided lower, pp | Decision | ≥+10 pp | Undefined draws |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | 24m M3-B1 | +20.37 | [+14.37, +26.16] | +14.37 | PASS | Yes | 0 |
| H2 | 24m M3-M1 | +1.36 | [-2.20, +3.01] | -2.20 | FAIL | No | 0 |
| H3 | 12m M3-B1 | +16.69 | [+9.98, +24.21] | +9.98 | NOT_REACHED_DESCRIPTIVE | Yes | 0 |

All 2,000 draws per horizon were defined for each primary contrast. H2 stopped the fixed sequence. The H3 point and interval are descriptive. The +10 pp reporting threshold is independent of the family decision.

## Secondary analyses

| Horizon | M1 − B1 recall, pp | Paired 95% CI, pp | Undefined draws |
| --- | --- | --- | --- |
| 12 | +17.18 | [+9.88, +24.06] | 0 |
| 24 | +19.01 | [+13.34, +25.62] | 0 |

| Months | Arm | Recall | Precision | Distinct event-drug capture | Grouped AP | Brier | ECE | AURC80 | E-AURC | Decision loss |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | B1 | 0.5064 | 0.0976 | 0.5064 | 0.0871 | 0.0373 | 0.0098 | 0.0741 | 0.0671 | 0.6656 |
| 12 | M1 | 0.6782 | 0.1307 | 0.6782 | 0.1568 | 0.0354 | 0.0084 | 0.0092 | 0.0115 | 0.4449 |
| 12 | M3 | 0.6733 | 0.1298 | 0.6733 | 0.1643 | 0.0352 | 0.0110 | 0.0080 | 0.0104 | 0.4299 |
| 24 | B1 | 0.4648 | 0.1851 | 0.6319 | 0.1723 | 0.0713 | 0.0216 | 0.0259 | 0.0307 | 0.5168 |
| 24 | M1 | 0.6549 | 0.2608 | 0.6931 | 0.2592 | 0.0654 | 0.0200 | 0.0190 | 0.0231 | 0.4741 |
| 24 | M3 | 0.6685 | 0.2662 | 0.7079 | 0.2661 | 0.0647 | 0.0206 | 0.0175 | 0.0216 | 0.4759 |

| Months | Arm | Clear | Flag | Refer | Flag events | Referred events | Blocked conflict referrals | Missed clear events | Missed-clear 95% CI, % | ≤3% upper | Legacy coverage, % | Legacy AURC80 | Legacy E-AURC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | B1 | 72 (1.37%) | 1572 (29.89%) | 3615 (68.74%) | 19 | 169 | 0 | 14 | [8.52, 37.16] | FAIL | 77.43 | Undefined | Undefined |
| 12 | M1 | 1417 (26.94%) | 791 (15.04%) | 3051 (58.01%) | 117 | 71 | 0 | 14 | [0.04, 4.92] | FAIL | 89.96 | 0.0092 | Undefined |
| 12 | M3 | 1678 (31.91%) | 839 (15.95%) | 2742 (52.14%) | 109 | 77 | 494 | 16 | [0.05, 4.39] | FAIL | 90.49 | 0.0080 | Undefined |
| 24 | B1 | 0 (0.00%) | 272 (5.86%) | 4367 (94.14%) | 58 | 310 | 0 | 0 | Undefined | UNEVALUABLE | 96.92 | 0.0259 | Undefined |
| 24 | M1 | 1102 (23.76%) | 1022 (22.03%) | 2515 (54.21%) | 250 | 101 | 0 | 17 | [0.14, 5.97] | FAIL | 89.24 | 0.0190 | Undefined |
| 24 | M3 | 1413 (30.46%) | 1069 (23.04%) | 2157 (46.50%) | 220 | 120 | 210 | 28 | [0.29, 6.39] | FAIL | 87.43 | 0.0175 | Undefined |

| Months | Arm | ECE counts from lowest to highest bin |
| --- | --- | --- |
| 12 | B1 | 5259, 0, 0, 0, 0, 0, 0, 0, 0, 0 |
| 12 | M1 | 5162, 97, 0, 0, 0, 0, 0, 0, 0, 0 |
| 12 | M3 | 5116, 143, 0, 0, 0, 0, 0, 0, 0, 0 |
| 24 | B1 | 4061, 578, 0, 0, 0, 0, 0, 0, 0, 0 |
| 24 | M1 | 3404, 910, 272, 45, 8, 0, 0, 0, 0, 0 |
| 24 | M3 | 3417, 811, 334, 66, 10, 1, 0, 0, 0, 0 |

| 2024 young cohort | Rows | Event rows | Expected hits from full queue | Recall |
| --- | --- | --- | --- | --- |
| B1 | 36 | 0 | 0.000 | Undefined |
| M1 | 36 | 0 | 0.000 | Undefined |
| M3 | 36 | 0 | 0.000 | Undefined |

The young cohort restricts the first original NDA date to (2023-01-01, 2024-01-01] within 24-month eligibility. The full 2024 roster defines all queue allocations. The JSON preserves interval and undefined-draw counts by arm and metric.

### Annual eligibility and evidence

| Months | Cutoff | Dated NDA | No dated TYPE 1 | Prior final ANDA | Eligible | Events | Slots | Proven FDA edition | Eligible unlisted | Tie rows B1/M1/M3 | Expected hits B1/M1/M3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | 2017-01-01 | 1846 | 712 | 591 | 543 | 17 | 108 | 2016-12-16 | 4 | 20/0/0 | 10.35/12.00/12.00 |
| 12 | 2018-01-01 | 1892 | 728 | 608 | 556 | 24 | 111 | 2017-10-13 | 9 | 23/0/0 | 11.48/13.00/15.00 |
| 12 | 2019-01-01 | 1944 | 743 | 632 | 569 | 34 | 113 | 2018-08-17 | 22 | 25/0/0 | 17.16/23.00/22.00 |
| 12 | 2020-01-01 | 1994 | 758 | 666 | 570 | 16 | 114 | 2019-12-13 | 9 | 24/0/0 | 5.33/10.00/9.00 |
| 12 | 2021-01-01 | 2045 | 770 | 682 | 593 | 25 | 118 | 2020-11-02 | 12 | 23/0/0 | 11.96/20.00/19.00 |
| 12 | 2022-01-01 | 2087 | 781 | 707 | 599 | 25 | 119 | 2021-12-10 | 4 | 17/0/0 | 14.12/18.00/18.00 |
| 12 | 2023-01-01 | 2115 | 789 | 732 | 594 | 15 | 118 | 2022-11-10 | 7 | 29/0/0 | 7.90/12.00/12.00 |
| 12 | 2024-01-01 | 2162 | 800 | 747 | 615 | 27 | 123 | 2023-12-08 | 5 | 33/0/0 | 16.55/14.00/13.00 |
| 12 | 2025-01-01 | 2199 | 805 | 774 | 620 | 19 | 124 | 2024-12-13 | 6 | 31/0/0 | 7.45/15.00/16.00 |
| 24 | 2017-01-01 | 1846 | 712 | 591 | 543 | 41 | 108 | 2016-12-16 | 4 | 11/0/0 | 18.64/25.00/26.00 |
| 24 | 2018-01-01 | 1892 | 728 | 608 | 556 | 58 | 111 | 2017-10-13 | 9 | 13/0/0 | 25.38/36.00/36.00 |
| 24 | 2019-01-01 | 1944 | 743 | 632 | 569 | 50 | 113 | 2018-08-17 | 22 | 13/0/0 | 20.08/29.00/33.00 |
| 24 | 2020-01-01 | 1994 | 758 | 666 | 570 | 41 | 114 | 2019-12-13 | 9 | 12/0/0 | 19.00/29.00/29.00 |
| 24 | 2021-01-01 | 2045 | 770 | 682 | 593 | 50 | 118 | 2020-11-02 | 12 | 20/0/0 | 22.00/39.00/40.00 |
| 24 | 2022-01-01 | 2087 | 781 | 707 | 599 | 40 | 119 | 2021-12-10 | 4 | 0/0/0 | 19.00/29.00/29.00 |
| 24 | 2023-01-01 | 2115 | 789 | 732 | 594 | 42 | 118 | 2022-11-10 | 7 | 0/0/0 | 21.00/28.00/29.00 |
| 24 | 2024-01-01 | 2162 | 800 | 747 | 615 | 46 | 123 | 2023-12-08 | 5 | 18/0/0 | 25.94/26.00/24.00 |

| Months | Cutoff | Low-confidence keys | NCE missing | Other exclusivity missing | Patent count missing | Patent expiry missing | Patent submission missing | Challenge missing | Strength missing | Form/route missing | OPEN/BLOCKED/CONTESTED |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | 2017-01-01 | 39 | 4 | 4 | 4 | 280 | 543 | 2 | 19 | 4 | 30/188/325 |
| 12 | 2018-01-01 | 37 | 9 | 9 | 9 | 289 | 556 | 2 | 24 | 9 | 27/197/332 |
| 12 | 2019-01-01 | 37 | 22 | 22 | 22 | 307 | 339 | 2 | 37 | 22 | 27/210/332 |
| 12 | 2020-01-01 | 34 | 9 | 9 | 9 | 292 | 318 | 2 | 23 | 9 | 25/240/305 |
| 12 | 2021-01-01 | 33 | 12 | 12 | 12 | 294 | 313 | 2 | 26 | 12 | 29/256/308 |
| 12 | 2022-01-01 | 32 | 4 | 4 | 4 | 289 | 305 | 2 | 18 | 4 | 19/272/308 |
| 12 | 2023-01-01 | 32 | 7 | 7 | 7 | 286 | 299 | 2 | 22 | 7 | 16/272/306 |
| 12 | 2024-01-01 | 31 | 5 | 5 | 5 | 283 | 292 | 572 | 21 | 5 | 5/220/390 |
| 12 | 2025-01-01 | 30 | 6 | 6 | 6 | 280 | 287 | 2 | 22 | 6 | 21/297/302 |
| 24 | 2017-01-01 | 39 | 4 | 4 | 4 | 280 | 543 | 2 | 19 | 4 | 42/171/330 |
| 24 | 2018-01-01 | 37 | 9 | 9 | 9 | 289 | 556 | 2 | 24 | 9 | 39/179/338 |
| 24 | 2019-01-01 | 37 | 22 | 22 | 22 | 307 | 339 | 2 | 37 | 22 | 46/188/335 |
| 24 | 2020-01-01 | 34 | 9 | 9 | 9 | 292 | 318 | 2 | 23 | 9 | 40/221/309 |
| 24 | 2021-01-01 | 33 | 12 | 12 | 12 | 294 | 313 | 2 | 26 | 12 | 43/236/314 |
| 24 | 2022-01-01 | 32 | 4 | 4 | 4 | 289 | 305 | 2 | 18 | 4 | 28/258/313 |
| 24 | 2023-01-01 | 32 | 7 | 7 | 7 | 286 | 299 | 2 | 22 | 7 | 30/252/312 |
| 24 | 2024-01-01 | 31 | 5 | 5 | 5 | 283 | 292 | 572 | 21 | 5 | 10/169/436 |

The annual JSON includes mean native and calibrated risks, event prevalence, and edition availability proof. Five arm-horizons exceeded the missed-clear upper-bound limit. B1 at 24 months cleared zero rows and its safety rate is unevaluable. Decisions outside the primary review queue continue through the ordinary process. Policy losses assume perfect referral resolution and illustrative costs.

## C3 | Competition at launch

| Applicant rule | Status | Rows | Known positive rows / drugs | Unknown rows / drugs | Unresolved / linked ANDAs | M3 recall | B1 recall | M3 − B1, pp | Paired 95% CI, pp | Undefined / run draws |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | EVALUATED | 4024 | 173 / 92 | 4 / 4 | 50 / 903 | 0.798 | 0.497 | +30.11 | [+20.16, +36.86] | 0 / 2000 |
| sensitivity | EVALUATED | 4024 | 176 / 95 | 0 / 0 | 0 / 903 | 0.795 | 0.494 | +30.16 | [+20.32, +36.87] | 0 / 2000 |

| Applicant rule | Metric | All unknown negative | All unknown positive | Conditional outer interval |
| --- | --- | --- | --- | --- |
| primary | M3 recall | 0.798 | 0.791 | [0.789, 0.800] |
| primary | B1 recall | 0.497 | 0.491 | [0.488, 0.499] |
| primary | Difference, pp | +30.11 | +29.99 | [+29.59, +30.51] |
| sensitivity | M3 recall | 0.795 | 0.795 | [0.795, 0.795] |
| sensitivity | B1 recall | 0.494 | 0.494 | [0.494, 0.494] |
| sensitivity | Difference, pp | +30.16 | +30.16 | [+30.16, +30.16] |

| Cutoff | Slots per arm | Primary positive / negative / unknown | Sensitivity positive / negative / unknown | Primary unresolved ANDAs | Sensitivity unresolved ANDAs | Name matches / comparable |
| --- | --- | --- | --- | --- | --- | --- |
| 2017-01-01 | 108 | 32/511/0 | 32/511/0 | 0 | 0 | 145 / 296 |
| 2018-01-01 | 111 | 27/529/0 | 27/529/0 | 0 | 0 | 194 / 334 |
| 2019-01-01 | 113 | 24/545/0 | 23/546/0 | 0 | 0 | 176 / 257 |
| 2020-01-01 | 114 | 22/548/0 | 22/548/0 | 0 | 0 | 161 / 221 |
| 2021-01-01 | 118 | 29/564/0 | 29/564/0 | 0 | 0 | 212 / 274 |
| 2022-01-01 | 119 | 23/576/0 | 23/576/0 | 0 | 0 | 193 / 248 |
| 2023-01-01 | 118 | 16/574/4 | 20/574/0 | 50 | 0 | 100 / 117 |

Pooled exact applicant agreement was 568/853. One jointly determinate row crossed the three-applicant threshold, and four rows moved from unknown to determinate under the sponsor rule. Bounds condition on the observed, linked FDA approvals. They describe regulatory crowding.

## C4 | Medicaid demand and reimbursement

The governing registration and C4 v2 reserve origins on or after 2017-01-01. The local C4 file manifest freezes results through 2017Q4 for the December 2016 development origin. The first reserved origin would require 2018Q1–Q4, for which the registered manifest has no pinned SDUD outcome payload. A C′ queue alone cannot establish those outcomes or ingredient coverage.

| 2017 onward | Disposition |
| --- | --- |
| Mapped carry-forward and drift | NOT_RUN |
| M3/B1 reimbursement adjustment | NOT_RUN |
| Fit, target and Q4 identity coverage and completeness | NOT_RUN |
| As-of arm | NOT_RUN |

## Private outputs and verification

| Artifact | Path | Rows | SHA-256 |
| --- | --- | --- | --- |
| Native scores and event labels, 12m | `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/score/C1_scores_12m.json` | 5259 | `a644f1d40271c9a59a5405b840724906332ce975854d2afedd3d22c4ded80891` |
| Native scores and event labels, 24m | `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/score/C1_scores_24m.json` | 4639 | `c3b9e51891fd8f577dfce9f7fbbfb466f25f29ae50ed4edd9d8b2d0fcbcc84e7` |
| Native export manifest | `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/score/C1_score_export_manifest.json` | — | `bb27ec7f972fecbe92bbfea9d31596dca56c51e0ad422083f70ce026c3c2bd07` |
| All C1 bootstrap draws | `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/score/C1_bootstrap_draws.npz` | — | `492fbb8afb9b316517ce2f784f236bd2587476f6ea569fb93b43310c56532ff4` |
| C3 per-application identity evidence | `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/score/C3_applicant_evidence.json` | — | `11a9fac50e8266635f9614f28cd704fa015e6964fbed482f860b0b35d55ad340` |

SCORELLM can join each horizon's export on the unique pair `(key, cutoff)`. The fields are `key`, `cutoff`, `y`, `B1`, `M1` and `M3`. The [committed result](../../../loe-bench/data/SCORE_CPRIME_RESULTS.json) carries summary values only.

Run with `python -B scripts/score_cprime.py` from `loe-bench/` in a separate workspace with unused output paths. A closed-seal preflight also passed. No paid service, GPU, LLM run or post-S0 outcome fetch occurred.

| Verification | Outcome |
| --- | --- |
| `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` | **PASS**, 223 tests. The existing Purple Book file warnings appeared. |
| Root `python -m pytest --tb=short -p no:cacheprovider` | **FAIL**, 2,760 passed, 50 skipped, one xfailed and eight standing SACR r2/r3 supervisor budget failures. |
| Independent replay of native recall from the private exports | **PASS**, joint roster and event counts match. A separate sorted tie-block implementation reproduced all arm recall values and all 2,000 paired draws in each horizon within 1e-14. Every private SHA-256 matched. |
| Summary SHA-256 | `38f65240b57a4662349d3bdc89fd026908d888bdb2cfcb1ed63f430ed845d932` |

The initial generic web lookup could not open OSF. The official public API returned the registration and both approved responses. The lock script reproduced the canonical digest from the API. The outcome scoring run completed in one execution after the closed-seal preflight.

## Deviations and handoff

No deviation from the registered C′ inference procedure. The requested reserved-origin C4 analysis remains `NOT_RUN`. The main planner owns independent review, publication of any scientific claim, and the lane handoff and memory updates.
