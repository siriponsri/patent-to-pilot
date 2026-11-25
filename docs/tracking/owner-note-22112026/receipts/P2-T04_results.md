# P2-T04 matched screen results, 25 Nov 2026

**Execution complete. Progression decision: NO_GAIN.** The unresolved-relation search reached ALL R@200 of 0.44372
against 0.44998 for complete-content fusion, a paired change of −0.00626 [−0.00902, −0.00369]. The locked rule
required at least +0.010 and an ALL lower bound above zero. The IN and OUT lower bounds were also below the
−0.005 guard. Park this arm. P2-T05 confirmation for this arm remains NOT_RUN.

The cohort was the frozen 2,000-app P1-DEV sample. It contained 1,999 apps with ALL positive support, 1,693 with
IN support and 1,953 with OUT support. For the strongest reported ALL comparator, complete-content fusion and
seed-only tied at 0.44998. The frozen arm-ID tie rule selected complete-content fusion. The historical A3r1 F3*
is shown separately as a C0-route reference. It was excluded from comparator selection. These are exploratory
DEV results. No protected TEST data was opened.

## Recall at 200

| Arm | ALL | IN | OUT |
|---|---:|---:|---:|
| `unresolved_relation` | 0.44372 | 0.51170 | 0.35725 |
| `complete_content_fusion` | 0.44998 | 0.51723 | 0.36218 |
| `seed_only` | 0.44998 | 0.51723 | 0.36218 |
| `original_query_deeper` | 0.43468 | 0.49928 | 0.34824 |
| `static_requirement` | 0.44216 | 0.51124 | 0.35235 |
| `generic_feedback` | 0.44474 | 0.51278 | 0.35590 |
| `extractive_feedback` | 0.44363 | 0.51200 | 0.35598 |
| `shuffled_binding` | 0.44904 | 0.51624 | 0.36199 |
| `original_A` | 0.32148 | 0.38503 | 0.24548 |
| `original_L` | 0.23750 | 0.27518 | 0.19241 |
| `original_P` | 0.43901 | 0.51200 | 0.34828 |
| `original_Q` | 0.36781 | 0.42214 | 0.29899 |
| `archived_a3r1_f3` | 0.45021 | 0.51892 | 0.36625 |

## Paired contrasts

Subtract each reference from the unresolved-relation arm. Brackets give 95% intervals from 10,000 examiner
art-unit bootstrap replicates, seed 20261119. New and displaced positives count ALL judgments at rank 200.

| Reference | ALL Δ [95% CI] | IN Δ [95% CI] | OUT Δ [95% CI] | New candidates | Recovered / displaced ALL positives |
|---|---:|---:|---:|---:|---:|
| `complete_content_fusion` | -0.00626 [-0.00902, -0.00369] | -0.00553 [-0.00944, -0.00178] | -0.00492 [-0.00842, -0.00158] | 14,275 | 11 / 58 |
| `seed_only` | -0.00626 [-0.00902, -0.00369] | -0.00553 [-0.00944, -0.00178] | -0.00492 [-0.00842, -0.00158] | 14,275 | 11 / 58 |
| `original_query_deeper` | +0.00903 [+0.00633, +0.01191] | +0.01242 [+0.00824, +0.01695] | +0.00901 [+0.00438, +0.01398] | 35,857 | 88 / 16 |
| `static_requirement` | +0.00156 [-0.00139, +0.00452] | +0.00046 [-0.00409, +0.00510] | +0.00490 [-0.00004, +0.00999] | 26,935 | 62 / 46 |
| `generic_feedback` | -0.00103 [-0.00373, +0.00170] | -0.00108 [-0.00520, +0.00313] | +0.00135 [-0.00281, +0.00563] | 21,575 | 34 / 43 |
| `extractive_feedback` | +0.00009 [-0.00262, +0.00265] | -0.00030 [-0.00428, +0.00370] | +0.00127 [-0.00312, +0.00563] | 23,753 | 45 / 39 |
| `shuffled_binding` | -0.00532 [-0.00790, -0.00298] | -0.00454 [-0.00790, -0.00144] | -0.00474 [-0.00847, -0.00127] | 13,562 | 12 / 49 |
| `original_A` | +0.12224 [+0.11209, +0.13227] | +0.12667 [+0.11225, +0.14142] | +0.11177 [+0.09667, +0.12648] | 244,988 | 1182 / 254 |
| `original_L` | +0.20622 [+0.19369, +0.21893] | +0.23653 [+0.21677, +0.25581] | +0.16484 [+0.14686, +0.18321] | 309,674 | 1820 / 255 |
| `original_P` | +0.00470 [-0.00323, +0.01277] | -0.00030 [-0.01260, +0.01192] | +0.00897 [-0.00146, +0.01969] | 149,050 | 402 / 348 |
| `original_Q` | +0.07590 [+0.06801, +0.08390] | +0.08956 [+0.07655, +0.10272] | +0.05826 [+0.04768, +0.06887] | 144,874 | 713 / 152 |
| `archived_a3r1_f3` | -0.00650 [-0.01541, +0.00238] | -0.00721 [-0.02067, +0.00627] | -0.00900 [-0.02244, +0.00460] | 178,949 | 468 / 525 |

The targeted arm expanded 1,010 queries and took the no-unresolved-relation fallback on 990. It added 17,853
candidate instances before reranking. Against complete-content fusion, the final top 200 contained 14,275 new
candidate instances and recovered 11 judged positives while displacing 58. The net was −47. IN recovery and
displacement were 7 and 30. OUT recovery and displacement were 4 and 24.

## Execution and verification

- BM25 gate PASS under the [owner-approved amendment](P2-T04_frozen_protocol.md). Reproduction was exact
  for 1,996 queries and four satisfied the raw-score cutoff exception. The gate preserved ordered top-200
  rows and displayed scores for all 2,000.
- Guarded CPU runtime and separate evaluator completed at 11:19:38 UTC on dr-train. Runtime took 22 min 26 s
  with 6,098,152 KiB peak RSS. Evaluation took 3 min 33 s with 616,208 KiB peak RSS. No watchdog abort
  occurred and the process group exited. RunPod spend was USD 0.
- The transcript, evaluation, 12 ranking files, timings and manifest pins were verified. The 22 pulled
  artifacts and digest list are in `../_private_artifacts/p2t04-preflight-20261124/screen-v1-cutoff-tie/`.
  Evaluation SHA-256 is `9de996ea2f5751c28ce7cf9690e18ec365476b8279111b32f6a409adc55a580b`.
  The compressed trace decompresses to the evaluator's original trace digest. The prior exact-gate
  failures and the cutoff census remain in the [execution receipt](P2-T04_execution.md).
- This resolves the P2-T04 screen. It leaves no positive matched method-evidence claim and gives no
  authorization to launch a later phase.
