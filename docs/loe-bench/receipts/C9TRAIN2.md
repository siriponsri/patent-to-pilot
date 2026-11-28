# C9TRAIN2 training receipt

**PASS on 28 November 2026.** SFT and GRPO finished all 64 updates each on one L4. The final adapters, manifests and logs matched the on-pod SHA-256 inventory. RunPod confirmed deletion at 09:45:15 UTC. Estimated all-in card spend was USD 0.21765. Track A predictions and paired outcome scoring are `NOT_RUN` on this card. This receipt is the executor handoff and project memory entry.

## Authorization and admission

The 28 November 2026 evening owner decision authorized one 24 GB NVIDIA L4 in RunPod Secure Cloud at EU-RO-1 or EUR-IS-2, up to USD 0.69/hour. The card has a USD 4.50 all-in cap within the USD 23 program envelope, with about USD 3.51 already used. Each arm has a 2.5 GPU-hour and USD 3.50 GPU-charge cap. EU-RO-1 is a placement change under the existing L4 hardware deviation. [Owner decision](../../maintenance/OWNER-DECISIONS-20261122.md) · [C9RUN2](C9RUN2.md)

The executor cut `loe/C9TRAIN2` from fetched `origin/research/loe-bench` at `4351c34be340ee280052c380ae602025dd57dec0`. The worktree was clean and origin had no C9TRAIN2 ref. OSF p2smd update 3 was verified by the main planner at 09:09 UTC. C′ had passed. A fresh origin check immediately before training showed `research/loe-bench` at `00fe70dcc3da2d8f54c5133e6e112332e22f3ae5` with no core Track A prediction-freeze tag or manifest. The existing S0 input tag and development freeze branch predate this card. [Update 3](../OSF-UPDATE-3-SHEET.md) · [Verification](../MEMORY.md) · [C′ gate](GATE.md) · [Development freeze](FREEZE.md)

## Provisioning and frozen inputs

At 09:26:13 UTC, RunPod `get-gpu-type` and `get-data-center` showed Secure Cloud NVIDIA L4 availability `LOW` in EU-RO-1 at USD 0.69/hour, with a CUDA 13.2 host satisfying the 12.8 floor. EUR-IS-2 had no L4 entry in either read. The 20 GB temporary container disk was quoted at USD 0.10/GB/month, about USD 0.0028/hour using a 720-hour month. Estimated compute and disk over five hours were USD 3.464. The registered USD 1 combined ceiling for all non-GPU items, including disk, bounded total reservation at USD 4.45. No persistent disk or network volume was attached. [RunPod storage pricing](https://docs.runpod.io/pods/storage/types)

The executor issued the create request at 09:26:24 UTC. Pod `kwo2osyic0u3ts` started at 09:26:27.928 UTC in EU-RO-1. The image was `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`, with direct SSH on the sole explicitly requested port. The SSH ED25519 fingerprint matched the provider's container log. The Windows OpenSSH key scanner failed to negotiate the advertised key exchange. The Git for Windows scanner retrieved the matching key, which was pinned for subsequent OpenSSH and SCP connections.

| Private input | Verified SHA-256 |
| --- | --- |
| `c9_dev_projection.json` | `d6a824d3f4ed0a6cd4c8d1c581e70fa3d449a213c386671f0edd7e87356c8e1c` |
| `c9_dev_roster.jsonl` | `f77b777415c5246eedee831068ac2c003a4ba354c87af5a8abdd8f7ccdfc316c` |
| `checkpoint/checkpoint.json` | `0a9deecdd2deb028c8555a236241f6fe4bc9d9fe9ee64be4493daa397527459e` |

The 1,389,320-byte input archive carried the reviewed code, required small manifests, launch scripts, frozen roster and projection. Its local and pod SHA-256 matched `65bb6c64737cfe15d63d66d1418805be3a29ec6cb36eae2e8a8ffec221df37b3`. The first staging attempt stopped before dependency setup because the cgroup v2 diagnostic path was absent. The second attempt read cgroup v1 limits on the same pod and retained the first attempt's logs. Effective limits were 5.1 vCPUs and 61,999,996,928 bytes of RAM. The pod detected one NVIDIA L4, 23,034 MiB VRAM, driver `595.112.07`, CPython 3.12.3, Torch `2.8.0+cu128`, Transformers `4.55.2` and PEFT `0.17.1`.

The checkpoint was downloaded directly from Hugging Face on the pod at the pinned Apache-2.0 revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. Its manifest hash matched the local pin and the on-pod roster replay matched all 12 committed fields. The frozen launch sequence reserved 8,100 seconds for each arm, including the five-second timeout grace, with the remaining 30 minutes split between shared preparation and teardown. The training schedule uses seed `20261127`, 64 updates per arm, and SFT before GRPO. [C9TRAIN input pins](C9TRAIN.md) · [Launch sequence](C9PROJ.md#training-card-launch) · [Pinned checkpoint](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/tree/989aa7980e4cf806f80c7fef2b1adb7bc71aa306)

## Training results and artifact verification

Both arms completed on the first training attempt with exit 0. Each used the frozen 32 batches of eight prompts and two updates per batch. The shared runtime and roster matched across arms. Both started from the same initial adapter. The seconds in the table are from each trainer's run manifest. The UTC times delimit the full arm commands, including startup and input verification.

| Arm | Start–stop UTC | Trainer seconds | Updates | Loss, first / last / mean | Peak CUDA allocation |
| --- | --- | ---: | ---: | --- | ---: |
| SFT | 09:30:48–09:32:35 | 100.561 | 64/64 | 0.372023314 / 0.007157402 / 0.049459008 | 3,342,494,720 bytes |
| GRPO | 09:32:35–09:44:28 | 707.006 | 64/64 | −0.000000022 / 0.001928456 / 0.001258935 | 5,468,441,600 bytes |

GRPO logged 103 malformed training rollouts out of 1,024, handled by the frozen reward rule. Losses summarize different training objectives. Forecast quality and paired effects will require the registered Track A evaluation after mature outcome coverage is verified.

| Artifact | Verified SHA-256 |
| --- | --- |
| Shared `training-roster.json` | `dfa874956fd8b9b53b89cde0fe30bb95790e81ba9e4bfa19cf203087f6d98fe7` |
| Shared `initial.safetensors` | `0d0e368c70c0d34ac5c2e1ec7459c49fb9646004a7518d024cc8d7c8911e74ce` |
| SFT `adapter_config.json` | `7cc48c89f59dde31fc84275dff3c9ade30d5179d5eaf23ba56297cec80ad5d22` |
| SFT `adapter_model.safetensors` | `6d65d4d5a8d94f178c203540a51149132a6d263ef83241d93bf5d901531435cc` |
| SFT `run.json` | `b410fff5410de36fdeffbba5a8ab1edef72ba3100dbec7865718baa541c65ef2` |
| GRPO `adapter_config.json` | `44b39a431f5ed2f882ffe4ac2c3133a72dd4efcc3743e6928cb95d3cbad234ce` |
| GRPO `adapter_model.safetensors` | `5dad8fb18941bb76aaad9f65915ba8180cc177ac47697ffbb9fc6ddcbd8c2ab8` |
| GRPO `run.json` | `8861d5d99d05dd360ee70ed94a138744403bfb14be922aa0dd37b505ce860156` |
| `results.tar.gz` | `8cffe2e67529ea15f4077be79d92ab530516c185882dda9f30d0bf55220dae38` |

The 18,690,434-byte archive is under `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/c9/c9train2-eu-l4-20261128/`. Local SHA-256 verified all 33 files covered by its on-pod `SHA256SUMS`. The extracted `results/trained/` directory contains the paired adapter payload and shared manifest. The archive includes both arm logs, launch diagnostics and the failed setup attempt. Git carries the hash record in this receipt.

## Billing and teardown

Training stopped at 09:44:28 UTC. After local verification the executor requested deletion at 09:45:11 UTC. RunPod returned HTTP 204. The 09:45:15 UTC lookup returned HTTP 404 and the account pod inventory was empty. The conservative billing window from the create request to deletion confirmation was 1,131 seconds. The calculation assigns each arm its elapsed command time plus half of the 311 seconds spent on shared work. Both arms completed inside the GPU time and charge caps.

| Arm | Allocated billed seconds | Estimated GPU, USD | Estimated total with disk, USD |
| --- | ---: | ---: | ---: |
| SFT | 262.5 | 0.05031 | 0.05052 |
| GRPO | 868.5 | 0.16646 | 0.16713 |
| Card | 1,131 | 0.21678 | 0.21765 |

The first billing query returned HTTP 400 because it omitted the end time. An hourly `list-pod-billing` query for 09:00–10:00 UTC with both endpoints returned no posted records for the pod at close. Final provider charges and any fees or tax therefore remain unverified. The table uses the catalog GPU rate and published temporary disk rate. [RunPod storage pricing](https://docs.runpod.io/pods/storage/types)

## Local tests

**PASS.** From `loe-bench/`, `python -m unittest discover -s loe_bench/tests -t .` ran 239 tests in 20.956 seconds with exit 0 and no skips. The interpreter was `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/c9-venv/Scripts/python.exe` (CPython 3.12.14). The existing Purple Book file-handle warnings appeared.

## Freeze handoff

The post-training origin check showed the separate core forecast package at `151e53d5441be18753ef1eedb97a3a0d3776538e`, with its receipt marking the external prediction freeze `NOT_RUN`. The registered freeze tag remained absent. The Track A freeze card can use the verified `results/trained/` directory with the pinned checkpoint, the matching L4 runtime and the full label-free Track A roster. It owns generation of both C9 prediction files and their inclusion in the registered freeze and OSF timestamp. [TRACKA-CORE receipt](https://github.com/siriponsri/patent-to-pilot/blob/151e53d5441be18753ef1eedb97a3a0d3776538e/docs/loe-bench/receipts/TRACKA-CORE.md) · [C9 protocol](../C9-PROTOCOL.md)
