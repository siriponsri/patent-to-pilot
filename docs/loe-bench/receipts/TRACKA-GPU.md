# TRACKA-GPU | Track A prediction run

**BLOCKED on 28 November 2026.** RunPod rejected the one provisioning request with HTTP 400 because the requested L4 capacity had gone. The immediate refresh reported no eligible Secure Cloud L4 capacity in the US or EU. The account pod inventory was empty after the rejection. All four prediction arms are **NOT_RUN**. Estimated spend is **USD 0.00**.

## Authorization and quote

The [owner decision](../../maintenance/OWNER-DECISIONS-20261122.md) authorized one 24 GB NVIDIA L4 in RunPod Secure Cloud in the US or EU at up to USD 0.69/hour, with a USD 1.50 all-in cap and no network volume. The executor cut `loe/TRACKA-GPU` from fetched `origin/research/loe-bench` at `b1c3553bf9d2769c4c6a436b49cbf2e6aaf2c359`.

| UTC on 28 Nov 2026 | Operation | Observed result |
| --- | --- | --- |
| 09:59:16 | `get-gpu-type` and `get-data-center` quote refresh | NVIDIA L4 24 GB, Secure Cloud, USD 0.69/hour. Only EU-RO-1 showed `LOW`. Host CUDA 13.2 satisfied the 12.8 floor. |
| 09:59:27 | Create request for one L4 in EU-RO-1 | HTTP 400. RunPod reported that instances matching the request were no longer available. No pod ID or creation timestamp was returned. |
| 09:59:37 | `get-gpu-type` and `get-data-center` after rejection | GPU availability `NONE` in the approved footprint. EU-RO-1 had no L4 entry. |
| After capacity refresh | `list-pods` | Zero pods, with no further page. No stop or delete action was needed. |

The request used the frozen image `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` with AMD64 digest `sha256:4d1721e62b56d345c83b4fd6090664be6daf9312caab5b2e76f23d8231941851`, direct SSH and a 45 GB temporary container disk. At USD 0.10/GB/month using a 720-hour month, the planned disk would add USD 0.00625/hour. The planned 105-minute outer budget, including provisioning, transfer and deletion, would total USD 1.21844 for compute and disk. No storage was allocated. [RunPod storage rates](https://docs.runpod.io/pods/storage/types)

## Verified inputs

- All 12 private Track A files matched `SHA256SUMS`. The core manifest byte digest was `6497ab59ba41b0429a6169d5118c6afd14680233076a6a6693c03599d0176628`. The frozen L1/L1e consumer revalidated both input and renderer digests, the pinned harness and the ordered common roster of 1,302 rows per arm. [TRACKA-CORE](TRACKA-CORE.md)
- The C9 Track A projection byte digest was `4b30e77359f8b4fc7e855ee11ef8d71b91a3f66db3f3eb95b796dd255c3ebe54`. The predictor's input loader verified all 651 rows at 24 months and reproduced the rendered message digest from the private package. All 33 files in the C9TRAIN2 private results inventory verified. The eight adapter, run and shared file digests independently matched the C9TRAIN2 receipt. The private training archive matched `8cffe2e67529ea15f4077be79d92ab530516c185882dda9f30d0bf55220dae38`. [C9TRAIN2](C9TRAIN2.md)
- The first local staging check found that its allowlist omitted the core manifest's `FROZEN_CONFIG.json` pin. Adding the existing config to the allowlist resolved the check. The resulting private input bundle was 18,751,377 bytes with SHA-256 `f3ce14b5e21f0ced0f26848da66f80aed2b91404c79cf885fa28d687a48bbee3`. It was never uploaded. The detached launcher and deadline script passed Bash syntax checks. Their remote behavior is **NOT_RUN**.

## Predictions and validation

| Arm | Planned rows | Returned rows | Schema-valid | Abstentions | Status |
| --- | ---: | ---: | --- | --- | --- |
| L1 | 1,302 | 0 | Unmeasured | Unmeasured | NOT_RUN |
| L1e | 1,302 | 0 | Unmeasured | Unmeasured | NOT_RUN |
| C9 SFT | 651 | 0 | Unmeasured | Unmeasured | NOT_RUN |
| C9 GRPO | 651 | 0 | Unmeasured | Unmeasured | NOT_RUN |

L1/L1e were staged for Qwen2.5-7B-Instruct at revision `a09a35458c702b33eeacc393d103063234e8bc28`, fp16, greedy decoding, batches of eight and a 160-new-token cap. The per-arm gate requires at least 180 schema-valid responses in the first 200 and a verified full roster. Malformed responses count as abstentions and rank below valid probabilities. The C9 arms were staged for Qwen2.5-1.5B-Instruct at revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, with the frozen greedy decoder and identical 24-month projection. The C9 pair requires two full outputs with matching roster, prompt and runtime pins. Both checkpoint downloads and GPU runtime detection are **NOT_RUN**. [SCORELLM](SCORELLM.md) · [C9 protocol](../C9-PROTOCOL.md)

There are no output digests or GPU result manifest. The private Track A inventory retains its original entries. No protected C′ data were opened and no outcome sources were fetched. No freeze, tag or OSF action was taken.

**Local tests PASS.** From `loe-bench/`, CPython 3.12.10 ran `python -m unittest discover -s loe_bench/tests -t .` with 243 tests, 238 passed, five skipped and exit 0. The existing Purple Book file-handle warnings appeared.

## Handoff

The freeze card is the next owner of the combined package. This attempt supplies no GPU predictions for inclusion. An authorized retry needs a fresh `get-gpu-type` and `get-data-center` quote for an allocatable L4 before creation. On completion, the freeze card combines TRACKA-CORE, P1/P2 from PRIORARMS and the eligible GPU predictions before applying the freeze, tag and OSF update 4.
