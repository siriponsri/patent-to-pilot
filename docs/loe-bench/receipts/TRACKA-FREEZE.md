# TRACKA-FREEZE | Prospective prediction freeze

**FROZEN in Git.** The manifest records the freeze at `2026-11-28T11:18:44Z` for the 27 November 2026 snapshot. Annotated tag `loe-track-a-freeze-20261127` points to commit `6712f32cdfb1252d66e192d770deaa867808a375`. The OSF external timestamp is pending audit and owner submission by 31 January 2027 at 23:59 UTC. [Registered protocol](../PREREGISTRATION.md#track-a-prospective-protocol) · [OSF update 4 sheet](../OSF-UPDATE-4-SHEET.md)

## RunPod attempts and spend

The owner authorized one Secure Cloud NVIDIA L4 in the US or EU at up to USD 0.69/hour with a USD 1.50 all-in cap. The worktree started clean at fetched `f285d069c76e7008b9882dab75fd49ba7d1e0ed1`, which includes `76a903a7`. [Owner decision](../../maintenance/OWNER-DECISIONS-20261122.md) · [Earlier TRACKA-GPU refusal](TRACKA-GPU.md)

| UTC, 28 Nov 2026 | Catalog and placement check | Result |
| --- | --- | --- |
| 10:15:45.452 | US-MO-2 LOW, USD 0.69/hour | Create returned HTTP 400 at 10:15:47.053 because matching capacity was unavailable. Refresh listed EU-RO-1 LOW. Pod inventory was empty. |
| 10:30:45.453 | No eligible US or EU Secure Cloud L4 | No create request. |
| 10:45:48.496 | EU-RO-1 LOW, USD 0.69/hour | RunPod created `r6fi2d2uyhjzfz` at 10:45:51.964. The retry schedule stopped after allocation. |

The pod read verified one L4, 45 GB of temporary container disk and no mounted volume. Host CUDA was 13.2. The image was `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404@sha256:4d1721e62b56d345c83b4fd6090664be6daf9312caab5b2e76f23d8231941851`. A watchdog started before the input upload. The detached job wrote a DONE marker and an inventory of result hashes. The deadline allowed 105 minutes from the create request, approximately USD 1.21844 including disk at the quoted rate. [RunPod disk rates](https://docs.runpod.io/pods/storage/types)

| Phase | Start UTC | End UTC | Exit |
| --- | --- | --- | ---: |
| `l1_stage` | 10:47:16Z | 10:48:35Z | 0 |
| `l1` | 10:48:35Z | 11:10:16Z | 0 |
| `c9_venv` | 11:10:16Z | 11:10:18Z | 0 |
| `c9_deps` | 11:10:18Z | 11:10:49Z | 0 |
| `c9_stage` | 11:10:49Z | 11:11:22Z | 0 |
| `c9_sft` | 11:11:22Z | 11:13:08Z | 0 |
| `c9_grpo` | 11:13:08Z | 11:15:21Z | 0 |

The job finished at `2026-11-28T11:15:21Z` with exit 0. The retrieved result archive matched SHA-256 `f65e915e62f65f92208b52ab26ad44b2acdcbb7e204926051e90351ea583cc79`, and all 40 member hashes verified at `2026-11-28T11:15:36.369Z`.

The delete request returned HTTP 204 and a fresh lookup returned HTTP 404 at `2026-11-28T11:15:40.109Z`. Estimated spend was **USD 0.346503**. The estimate covers 1791.613 seconds from create request through deletion verification at USD 0.69/hour for compute and USD 0.00625/hour for disk. The pod billing reads at deletion and closeout had zero posted records, so the finalized provider charge is unavailable. [RunPod disk rates](https://docs.runpod.io/pods/storage/types)

## Input integrity and admission

All 14 initial Track A files and all 33 C9TRAIN2 inventory members matched SHA-256. The two adapter payloads, their run manifests, the two shared training artifacts and the training archive also matched the C9TRAIN2 receipt. The input bundle matched SHA-256 `f3ce14b5e21f0ced0f26848da66f80aed2b91404c79cf885fa28d687a48bbee3` on both ends. Its research code and configuration matched the branch after LF normalization. The L1/L1e input and rendered-message hashes and the C9 ordered keys and rendered-message hashes reproduced. The 12- and 24-month panels share the same 651 ordered active-moiety keys. [TRACKA-CORE](TRACKA-CORE.md) · [PRIORARMS](PRIORARMS.md) · [C9TRAIN2](C9TRAIN2.md)

| GPU arm | Returned rows | Schema-valid | Abstentions | Malformed | Disposition |
| --- | ---: | ---: | ---: | ---: | --- |
| L1 | 1302 | 1302 | 97 | 0 | ADMITTED |
| L1e | 1302 | 1302 | 8 | 0 | ADMITTED |
| C9-SFT | 651 | 651 | 0 | 0 | ADMITTED |
| C9-GRPO | 651 | 651 | 651 | 0 | ADMITTED |

L1 and L1e each passed with 200 valid responses in the first 200 against the required 180, and returned the full roster. The C9 pair matched ordered keys, rendered prompts, token IDs and the L4 runtime. C9-GRPO chose the valid abstention action on all 651 rows. The registered C9 procedure retains the probability from a valid abstention for scoring, and both arms met paired admission. Prospective performance awaits outcome maturity. [SCORELLM](SCORELLM.md) · [C9 protocol](../C9-PROTOCOL.md)

## Frozen files

- [Freeze manifest](../../../loe-bench/data/TRACKA_FREEZE_MANIFEST.json) has LF SHA-256 `8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d`. It binds the roster, source versions and availability, code, models, calibration, policies and predictions.
- [GPU manifest](../../../loe-bench/data/TRACKA_GPU_MANIFEST.json) has LF SHA-256 `6f91e45cf776fe4ff0f80fa30f13c9371e4b9a7b5660043db9a3cbbf399db659`.
- Private prediction files are in `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/trackA`. The extended `SHA256SUMS` has 24 verified entries and SHA-256 `29b0b6ce9135a324ee67f22454c035ef31a173e43d1611a48bea04d95a448119`.
- The private archive `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/tracka-freeze-20261128/r6fi2d2uyhjzfz/freeze/trackA-predictions.zip` has SHA-256 `85e9521e8cf8d6a909d1a0f7333b3f66851c95dcfaded9116ebdceb744882da2`. All ten members were rehashed inside the archive.

| Arm | 12-month rows | 24-month rows | Prediction file | Byte SHA-256 |
| --- | ---: | ---: | --- | --- |
| B1 | 651 | 651 | `B1_predictions.jsonl` | `03512b32026d929e8cdcce2a352bfbdafef0d90473330e7177b6e6ca36346c13` |
| M1 | 651 | 651 | `M1_predictions.jsonl` | `a89086db767ba27e8c15927138c6c2eff2d0b52217679f0bee89c18b9997edd0` |
| M3 | 651 | 651 | `M3_predictions.jsonl` | `cee7d7a4f77dd57424b7420ccb5c7b5c48dda68a067242bebe52fee45598d410` |
| B3 | 651 | 651 | `B3_predictions.jsonl` | `06d02ec233363b16fed5673babe7ef72e4d18a5406b2ef5725a6c038a5971ace` |
| P1-RSF-OPEN | 651 | 651 | `P1-RSF-OPEN_predictions.jsonl` | `40a44ecc1c6b9f477d16e8d638a098fc73f4801624daf4e5476ce9d614470f1f` |
| P2-COX-OPEN | 651 | 651 | `P2-COX-OPEN_predictions.jsonl` | `2b0eff2b76a5da5968c434965c44d649469d533f4ea31485d8fb8d34d0dda29f` |
| L1 | 651 | 651 | `L1_predictions.jsonl` | `79c3b990ec4b6c38df4861ab51a193968cd4b532290da702d8dc1d6e612e9b41` |
| L1e | 651 | 651 | `L1e_predictions.jsonl` | `bf910f5635a3bb3c1808387924806d344c9f61ba2e1fba9294c9fcf065e4f51d` |
| C9-SFT | 0 | 651 | `C9-SFT_predictions.jsonl` | `cce35d54f27062e0f2eee1e6c13d1a0742a7181bfdaeed03150a8b5218936488` |
| C9-GRPO | 0 | 651 | `C9-GRPO_predictions.jsonl` | `75ab8e09e5210fa841818b503eda1b2cc6b42576fa542130c83fff9c263d9de7` |

## Verification, deviations and handoff

- From `loe-bench/`, `python -m unittest discover -s loe_bench/tests -t .` on CPython 3.12.10 passed with 253 run, 243 passed, 10 skipped and exit 0. The pinned PRIORARMS environment passed 248 with five skipped and exit 0. The existing Purple Book resource warnings appeared.
- From the repo root, `python -m pytest -o addopts= -q --tb=short --basetemp <short-fresh-path>` in the S4 validation venv and QA overlay returned 2,807 passed, 10 skipped, one xfailed and the eight allowed SACR r2/r3 budget failures. Raw exit was 1. An initial additional Workbench loopback failure (Windows error 10053) passed in isolation and in the full rerun. Full rerun log SHA-256 `c2a0a3a4a52918f81d10feb5fb22caed24b4a6c34b56f4e1b53f0a37f7ea4c2e`.
- The protocol requires a Git tag and provides a name for the S0 input tag. This card named the separate prediction freeze tag `loe-track-a-freeze-20261127` using the snapshot date.
- The C′ metric supplement is **NOT_RUN**. Zero protected C′ data were opened and zero post-t0 outcome sources were fetched during this card. Predictions remain fixed. The 12-month window matures on 27 November 2027 and the 24-month window on 27 November 2028.

Claude audits the [update 4 sheet](../OSF-UPDATE-4-SHEET.md). The owner files the update and the planner verifies the external timestamp. OSF submission and attachment handling are **NOT_RUN**.
