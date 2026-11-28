# SCORELLM | Exploratory C′ L1 and L1e

## Admission and input freeze

The first author released the registered exploratory comparisons under the [owner decision](../../maintenance/OWNER-DECISIONS-20261122.md). The [custodian gate](GATE.md) returned **PASS**. The original [OSF registration](https://osf.io/p2smd) reproduced canonical SHA-256 `3f91145251465b0ed9c89233337748e1b9fd84db8c4c2a6158860374670e1c77`. Updates 1 and 2 were both approved in the live OSF read-back. The registration digest was set in the local Python process environment. The wrapper `PREREG_LOCK.json` stores the digest of the canonical record.

The S0 snapshot provides observation through 27 November 2026. Use the registered 12-month cutoffs from 2017 through 2025 and 24-month cutoffs from 2017 through 2024. The sealed runner verified the frozen manifests, selected historical FDA ZIPs and local sources. The two label-free inputs contain the same 9,898 forecast identities ordered by horizon, cutoff and active-moiety key. Scores and labels stay with the local evaluator. [Preregistration](../PREREGISTRATION.md#secondary-and-exploratory-analyses)

| Arm | Forecast rows | Input SHA-256 | Rendered message SHA-256 |
| --- | ---: | --- | --- |
| L1 | 9,898 | `50fba18d9564e10bc2e0b818b07c91c3ebe5474dff18ca1bda10b45fcacc838c` | `5219d2db076dc5a855a067c17bd1c69312694373b31efceb95915c317385a3f6` |
| L1e | 9,898 | `2b351168e15ff94df8f40a11d1a90ad256dc211b90a2fcaf711d0add9196485e` | `94fd4de2b58e49275d30182e211ff64e73d0d64737c67912fdffed9eed8ada40` |

The local active-moiety roster hashes to `b39405c6a0cb67a1b0cae7234ac50c12e9bdace9ea20e0c23895fbaaad23d240`. Both inputs use the frozen Qwen2.5-7B-Instruct model at `a09a35458c702b33eeacc393d103063234e8bc28` under Apache-2.0, the pinned tokenizer and chat template, fp16, greedy decoding, eight-row batches and the pinned parser. Each arm must independently return at least 180 schema-valid responses in its first 200 rows and the complete roster. [L1DEV](L1DEV.md) · [C2](C2.md)

## RunPod allowance before provisioning

RunPod reported one Secure Cloud L4 at USD 0.69/hour with low stock in US-GA-2. The existing stage volume was in US-MO-2, so the placement requires a 50 GB temporary container disk and the pinned C2 restage. At USD 0.10/GB/month for that disk and USD 2.10/month for retained storage, the prorated total is about USD 0.70/hour. The measured development rates imply about 2.95 hours of generation. Allow at most four hours and five minutes from the create request through deletion verification, including staging, transfer and cleanup. The estimate at that limit is USD 2.86. [RunPod storage rates](https://docs.runpod.io/pods/storage/types)

## Execution checkpoint

The create request was logged at 05:28:29 UTC on 28 November 2026. RunPod created pod `hmo8vrw0fq4pw2` in US-GA-2, confirmed USD 0.69/hour, and reported start at 05:28:35.147 UTC. Only the task bundle was transferred. Its remote SHA-256 matched `95a8637e6ac7c4eda7d0a91efc2209e0d6fef04deb7fb2d672c3bff8e4610afb`. The initial launch SSH connection timed out after the transfer. A read-back found no launch artifacts, and the retry started a single run on the same pod. The local deadline for inference is 09:23:29 UTC with deletion confirmation budgeted by 09:33:29 UTC.

The restage checked all pinned model shards, tokenizer assets and dependency wheels. L1 ran from 05:35:56 to 06:47:33 UTC. L1e ran from 06:47:41 to 08:30:19 UTC. Both generation and staging exit records returned zero. The monitoring session was unavailable on resumption at 09:04:49 UTC, so the pod remained billable after the 08:30:20 UTC completion record. The eight output and log files matched their remote SHA-256 values after transfer. [Pinned dependency wheels](../../../loe-bench/data/E4b_stage.json)

The delete request at 09:06:25 UTC returned HTTP 204. The pod lookup at 09:06:29 UTC returned HTTP 404. The 13,080-second request-to-confirmation window gives a conservative **USD 2.543 estimated total**. It includes USD 2.507 compute, USD 0.025 temporary disk and USD 0.011 prorated retained storage. The billing endpoint had posted USD 1.831 for this pod at close and had incomplete coverage of the final hours. The existing US-MO-2 volume was retained. [RunPod storage rates](https://docs.runpod.io/pods/storage/types)

## Evaluation

Read the hash-verified SCORE export from the private artifact directory. Require an exact join on active-moiety key, cutoff and horizon. Rank by native `p_entry` for schema-valid completions, and use −1 for invalid responses. Compute recall and precision at each cutoff's capacity `floor(N/5)` with expected boundary ties, and compute pooled grouped AP. The 2,000 paired whole-drug draws per horizon use seed 20261127, rebuild each queue and report two-sided linear percentile intervals and undefined draw counts. All contrasts are exploratory.

L1e adds both dated evidence fields and an evidence-only instruction. The contrast estimates the joint effect of those changes for this frozen checkpoint and retrospective roster. The model's pretraining coverage of later approvals remains unknown. The bootstrap intervals condition on the frozen model outputs and comparator risks.

The evaluator uses the archived GPU outputs. Run the following from `loe-bench/` in a dedicated PowerShell process. The score command verifies both arms against the input freeze, verifies the SCORE file digests and writes the aggregate results JSON.

```powershell
$env:LOE_PREREG_SHA256 = '3f91145251465b0ed9c89233337748e1b9fd84db8c4c2a6158860374670e1c77'
rtk proxy python -B scripts/scorellm_local.py score --private 'C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/scorellm' --score-manifest 'C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/score/C1_score_export_manifest.json'
```

## Local verification

- **PASS.** A hand-checked fixture rejected an outcome key in the label-free export, rejoined shuffled SCORE rows, and reproduced the expected tied queue allocation, grouped AP, paired contrast and undefined-draw handling.
- **PASS.** `python -B -m unittest discover -s loe_bench/tests -t .` ran 220 tests from `loe-bench/` with the existing Purple Book resource warnings.
- **PASS with standing exceptions.** Repository `python -B -m pytest --tb=short -q -p no:cacheprovider` exited 1 with the eight recognized SACR r2/r3 supervisor budget failures.

## Exploratory C′ results

Both arms passed the first-200 gate and completed the full common roster. The local parser independently revalidated every returned row.

| Arm | Valid at gate | Complete roster | Schema-valid | Abstentions |
| --- | ---: | ---: | ---: | ---: |
| L1 | 200/200 | 9,898 | 9,898 | 1,019 |
| L1e | 200/200 | 9,898 | 9,898 | 825 |

The private SCORE manifest SHA-256 is `bb27ec7f972fecbe92bbfea9d31596dca56c51e0ad422083f70ce026c3c2bd07`. Both horizon exports matched their manifest hashes and every key in the frozen roster.

| Horizon | Rows | Drug clusters | Event rows | Queue slots per arm |
| ---: | ---: | ---: | ---: | ---: |
| 12 months | 5,259 | 803 | 202 | 1,048 |
| 24 months | 4,639 | 771 | 368 | 924 |

| Horizon | Arm | Recall at 20% [95% CI] | Queue precision [95% CI] | Grouped AP [95% CI] |
| ---: | --- | ---: | ---: | ---: |
| 12 | L1 | 26.58% [24.07%, 29.29%] | 5.12% [4.31%, 5.98%] | 0.04858 [0.04144, 0.05743] |
| 12 | L1e | 14.50% [10.92%, 18.51%] | 2.79% [2.05%, 3.68%] | 0.04116 [0.03553, 0.04747] |
| 12 | B1 | 50.64% [43.33%, 57.05%] | 9.76% [8.02%, 11.42%] | 0.08707 [0.06902, 0.11159] |
| 12 | M3 | 67.33% [60.76%, 72.92%] | 12.98% [11.01%, 14.95%] | 0.16431 [0.13362, 0.21285] |
| 24 | L1 | 26.14% [23.54%, 28.95%] | 10.41% [8.93%, 12.07%] | 0.09872 [0.08510, 0.11420] |
| 24 | L1e | 12.36% [9.82%, 14.85%] | 4.92% [3.73%, 6.21%] | 0.08123 [0.07087, 0.09323] |
| 24 | B1 | 46.48% [40.27%, 52.34%] | 18.51% [15.67%, 21.50%] | 0.17226 [0.14277, 0.21022] |
| 24 | M3 | 66.85% [60.95%, 72.21%] | 26.62% [22.94%, 30.15%] | 0.26609 [0.22646, 0.32136] |

| Horizon | Contrast | Recall difference, pp [95% CI] | Precision difference, pp [95% CI] | AP difference [95% CI] |
| ---: | --- | ---: | ---: | ---: |
| 12 | L1 − B1 | -24.06 [-30.78, -16.58] | -4.64 [-6.02, -3.19] | -0.03850 [-0.06022, -0.02248] |
| 12 | L1 − M3 | -40.75 [-46.44, -33.98] | -7.85 [-9.34, -6.29] | -0.11573 [-0.16391, -0.08681] |
| 12 | L1e − B1 | -36.14 [-43.59, -27.60] | -6.97 [-8.64, -5.24] | -0.04592 [-0.06823, -0.02993] |
| 12 | L1e − L1 | -12.08 [-16.41, -7.45] | -2.33 [-3.24, -1.39] | -0.00742 [-0.01398, -0.00210] |
| 12 | L1e − M3 | -52.83 [-59.34, -45.19] | -10.18 [-11.95, -8.32] | -0.12315 [-0.17138, -0.09439] |
| 24 | L1 − B1 | -20.33 [-26.22, -13.96] | -8.10 [-10.49, -5.59] | -0.07354 [-0.10722, -0.04773] |
| 24 | L1 − M3 | -40.70 [-46.06, -34.81] | -16.21 [-18.87, -13.39] | -0.16737 [-0.21947, -0.13020] |
| 24 | L1e − B1 | -34.11 [-41.34, -27.29] | -13.59 [-16.58, -10.67] | -0.09103 [-0.12575, -0.06553] |
| 24 | L1e − L1 | -13.78 [-17.71, -10.32] | -5.49 [-7.09, -4.05] | -0.01749 [-0.02697, -0.00937] |
| 24 | L1e − M3 | -54.48 [-61.18, -47.61] | -21.70 [-24.95, -18.21] | -0.18486 [-0.23698, -0.14831] |

All 2,000 draws were defined for each horizon, arm and contrast.

## Artifact verification

Private run artifacts are in `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/scorellm/`. The compact predictions contain the native risk and roster key. The rendered-chat digest binds the ordered sequence of per-row chat-template hashes.

| Arm | Raw output SHA-256 | Predictions SHA-256 | Ordered chat hashes SHA-256 |
| --- | --- | --- | --- |
| L1 | `362b1f9920b8c7db78cb6fa7f17dfd46c6b074061c11bb73b575969bbc3978e6` | `65bb85aef29a3e3320ed807072d996eb5dccf58bac8f9805fe4f7cac91f478c7` | `b9ade58e27629bf9a21607a631f90f13bb4f4d769888d99cb864372a4649d773` |
| L1e | `35cdcb982ab12928a946888305cb9a115f4857792c6373d1dad44e557a82fc49` | `4eed6b3b1e851fa93883a8c556dc9fd9cbc42ea9aebf396da3bde75c97f86bc6` | `7a8b41b8ac9b587f562603feb8130acbaee5066c6aeef567e33dfca8f935050f` |

The aggregate result SHA-256 is `569e0c69760a1d022fbe526b3f2f8b964598cb951f443841d0f5361421b0226a`. The main planner reviews the result before integration. [Machine results](../../../loe-bench/data/SCORELLM_CPRIME_RESULTS.json)
