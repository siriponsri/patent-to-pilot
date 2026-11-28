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
