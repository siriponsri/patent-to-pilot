# RUNPOD-CLEANUP | Retire the E4b network volume

**PASS.** RunPod acknowledged deletion of `8n6rnzljwg` at `2026-11-28T13:34:39.286Z`. A direct read returned HTTP 404 and the account's network volume list was empty. The local preservation check covered the project outputs identified in the staging and run records. This receipt is the executor handoff and memory entry for the card.

The [owner decision, line 262](../../maintenance/OWNER-DECISIONS-20261122.md#L262) authorizes deletion after checking local copies and confirming the volume is unused. The register dates the decision 29 November. The execution timestamps below come from the live tool clock. The executor started on clean base `a69a90172d816fd16e2d23fdd6bd8a2a6e51886f` and used branch `loe/RUNPOD-CLEANUP`. The inventory below comes from the receipts, staging code and published manifests.

## Volume inventory and preservation

Local paths in the tables are relative to `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/`. A PASS against a recorded digest means equality of SHA-256 over file bytes unless the row specifies LF normalization.

| Recorded material | Class and placement | Local evidence |
| --- | --- | --- |
| Qwen2.5-7B-Instruct weights, tokenizer, config and ancillary files | Public, under `/workspace/e4b/model`. The 13 files total 15,242,805,751 bytes at revision `a09a35458c702b33eeacc393d103063234e8bc28` | Re-downloadable from the [publisher snapshot](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/tree/a09a35458c702b33eeacc393d103063234e8bc28). The [model manifest](../../../loe-bench/data/E4b_model.json) pins publisher objects. Local `E4b/verified_files.json` and the [staging manifest](../../../loe-bench/data/E4b_stage.json#L2) preserve the 13 observed SHA-256 values. |
| E4b dependencies | Public, installed to `/workspace/e4b/deps` from 18 pinned wheels. The stage script used a temporary wheel directory and removed it on exit. Torch came from the pinned image. | `E4b/dependencies.json` matches all 18 wheel records in the [staging manifest](../../../loe-bench/data/E4b_stage.json), including filenames, versions and digests. [Stage script](../../../loe-bench/scripts/runpod_e4b_stage.sh) |
| E4b harness, model manifest and staging files | Reproducible project inputs under `/workspace/e4b`, preserved in the E4b commit `2fef166f85d6d71e17d90223161f0ca1aba7f8c6` | Versioned in Git. The [stage record](../../../loe-bench/data/E4b_stage.json#L258) pins the transport tar SHA-256 `de4880e9de0b6062a551c8701e5fa13b5560b8e5545117e9aa02948b12c24f83`. The original transport tar bytes were unverified locally. |
| E4b smoke sample, raw responses, summary and log, staging log and manifests | Project evidence from the E4b pods. The smoke record identifies the mounted model and volume. Its output mount paths are unspecified, so the preservation check includes all recovered files. | `E4b/`, verified below. [E4b](E4b.md) · [Smoke record](../../../loe-bench/data/E4b_smoke.json) |
| L1DEV uploaded rows/config/harness and raw responses, summary, log and exit record | Project evidence associated with reuse of the E4b stage. Included in the check regardless of whether each file was on the mount or the pod's 20 GB container disk. | `llm_arm/`, verified below. [L1DEV](L1DEV.md) · [Pod ledger](../../../loe-bench/data/L1DEV_runpod_ledger.json) |

The E4b transfer probe ran on pod `a96jnvf4ki8i3j`, which was deleted at 15:03:56 UTC on 27 November, before this volume was created at 15:05:44 UTC. Its random 100 MB upload and publisher range download were throughput fixtures. The measurement and upload digest are retained in the [E4b ledger](../../../loe-bench/data/E4b_runpod_ledger.json#L164).

| Local file | Verified SHA-256 | Check |
| --- | --- | --- |
| `E4b/e4b-smoke-inputs.jsonl` | `07dca586b2dc34404923dc9a6d6e1d63d783da4441284e0cabe7ecf98dda0c2f` | PASS. Reconstructed from the public CRLF example CSV after matching its recorded digest. The generated input bytes match the smoke record. |
| `E4b/e4b-smoke-summary.json` | `5a5e517f390751652f982a0bbeab2c55794f7dbc925f87ac790655230a271155` | PASS against smoke record |
| `E4b/e4b-smoke-results.jsonl` | `c176e6a13067c4f9d9e457ca318a15681a5f08081f6fc60ed2e84b8bd371b76c` | PASS against smoke record |
| `E4b/e4b-smoke.log` | `aa7c9fda527d3a40a2460e1cc5a83f768240c9a22e3b32201474c360bb95a8b9` | PASS against smoke record |
| `E4b/e4b-stage.log` | `5262009ca3d13cb31f213f00ff974aeb06b93511b1f62cf6502092d1d16183ff` | PASS against recovered local source bytes. The E4b receipt gives no historical byte digest for this log. |
| `E4b/dependencies.json` | `387a2e73dc303888545d3ece5d8e296ac419c083421e1d7b285109616713d2f5` | PASS against recovered source bytes and parsed wheel records in the staging manifest |
| `E4b/verified_files.json` | `a360909ca1ed1eee2fa86c2d7255a757ddba16bcf191f660c558bc279b2ba1e3` | PASS against recovered source bytes and parsed model records in the staging manifest |
| `llm_arm/L1DEV_inputs.jsonl` | `b4fcbb06eac119cb1433c9b7855e0f38160313d1c74da937d1b41b2cf9a57837` | PASS against L1DEV receipt |
| `llm_arm/L1DEV_outputs.jsonl` | `2b0d5d04ed00a6040ff49efeae9bcd9145803495e1f0c47c1e2bc94fb2f80741` | PASS against L1DEV receipt |
| `llm_arm/L1DEV_summary.json` | `e477ae22651971695b2f2a1f55ff49d146989844e1d38d775e8edc6ac82c3d30` | PASS against L1DEV receipt |
| `llm_arm/L1DEV_run.log` | `8505eaf56e95c5a7b981f361b92f067b406885e58c1f8011bb9e9624b22d4f6a` | PASS against L1DEV receipt |
| `llm_arm/L1DEV_exit.txt` | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` | PASS against L1DEV receipt |
| `llm_arm/L1DEV_remote_SHA256SUMS.txt` | `3975731ec776c6b4cccbfba48ad00808c495c2aab8e049169c0fcc454e1f39b8` | PASS. All four listed digests agree with the L1DEV receipt and local output bytes. |
| `llm_arm/L1DEV_upload.tar.gz` | `4d0175a93f85247a5c028f4614712a6deebc493152344d1fc8d3a812a1f4e585` | PASS. All five members match the roster, LF config and three LF harness pins. [L1 config](../../../loe-bench/data/L1_FROZEN_CONFIG.json) |

The E4b directory was absent from the intended Desktop tree. The six original files were recovered from `C:/Users/User/.t3/worktrees/patent-to-pilot/_private_artifacts/loe-bench/E4b/`. Each destination copy was rehashed after copying. The initial smoke input reconstruction used the LF form of the public CSV and failed the source digest check. Repeating with the hash-matched CRLF source reproduced the exact pinned input.

## Later jobs and active dependencies

| Card | Evidence of volume use |
| --- | --- |
| [C2](C2.md) and [SCORELLM](SCORELLM.md) | The retained volume was in US-MO-2. Both cards restaged the pinned material on temporary container disks in other data centers. Their outputs were pulled from those pods. |
| [C9RUN](C9RUN.md) and [C9TRAIN](C9TRAIN.md) | Considered possible reuse. The production training preflights created no pod and wrote no artifacts to the volume. |
| [C9TRAIN2](C9TRAIN2.md) | Trained both adapters on temporary disk in EU-RO-1 without a network mount. The adapters and 33-file inventory were verified locally by that card. |
| [TRACKA-GPU](TRACKA-GPU.md) and [TRACKA-FREEZE](TRACKA-FREEZE.md) | The first request created no pod. The successful freeze used a 45 GB temporary disk in EU-RO-1 without a network mount. Its 40 result artifacts were verified locally by that card. |

The records identify no outstanding workload dependent on the retained stage. The volume file inventory was reconstructed from the records. No volume filesystem listing, pod creation, protected test data access or new inference occurred on this card.

## RunPod read-back and cost

The executor used the existing RunPod MCP connection and its v2 REST tools. The table gives client observation times in UTC. Every list completed with no further page.

| Observed UTC, 28 Nov 2026 | API operation | Result |
| --- | --- | --- |
| 13:34:35.225 | `list-network-volumes` | One volume. `8n6rnzljwg`, `ptp-loe-e4b-model-71bb4c8e-mo2`, 30 GB, STANDARD, US-MO-2. |
| 13:34:35.684 | `list-endpoints` | Zero serverless endpoints. |
| 13:34:35.701 | `list-pods`, including cluster members | Zero pods, including running and stopped pods. No pod could be attached or continue billing. |
| 13:34:39.286 | `delete-network-volume` | HTTP 204 for `8n6rnzljwg`. Requested at 13:34:35.702 UTC. |
| 13:34:42.183 | `get-network-volume` | HTTP 404 for `8n6rnzljwg`. |
| 13:34:43.860 | `list-network-volumes` | Zero network volumes. |
| 13:34:44.073 | `list-clusters` | Zero clusters. |
| 13:34:44.198 | `list-global-volumes` | Zero global volumes. |
| By 13:36:11.151 | `list-pods` and `list-endpoints` | Post-delete check found zero pods and zero endpoints. |

The project ledger closes at approximately **USD 4.08 of the USD 23 RunPod envelope**, based on the [Track A freeze closeout](../HANDOFF.md#track-a-frozen-28-nov-2026-111844-utc). This card incurred **USD 0 in new resource charges**. Deleting the volume ends its estimated USD 2.10/month storage charge. Any accrued retention before deletion is subject to final provider posting, which this card did not reconcile.
