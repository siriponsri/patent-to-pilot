# C9P | Paired SFT and GRPO training pipeline

## Scope and handoff

C9P implements the frozen C9 v2 design on `loe/C9P`, based on `research/loe-bench` at `a87f8407`. The frozen spec, C2 evidence renderer, response parser and S0 manifest are verified by LF digest. The SFT and GRPO runners share the roster, tokenizer, prompt order, frozen base and initial LoRA weights. C9P is ready for planner review. Production roster admission, the A10 run and paired forecasting remain `NOT_RUN`. Card spend was USD 0. [C9 spec](../../../loe-bench/data/C9_SPEC.json) · [C9 protocol](../C9-PROTOCOL.md) · [OSF update](../OSF-UPDATE-SHEET.md)

- The roster builder accepts a hash-pinned, bounded S0 development projection. It verifies the training cutoff, eligibility dates, linkage, coverage and outcome-window limit before selecting and cycling the 256 training slots in frozen hash order. Both arms receive the same C2 rendered prompt bytes. The standalone tokenizer check records hashes and rejects prompts above 2,048 tokens.
- The trainer runs 32 batches of eight prompts and two optimizer steps per batch. SFT averages assistant-target token loss within each example. GRPO draws four completions per prompt and retains the same trajectories, rollout log probabilities and rewards for both updates. Its loss applies the frozen per-token clip and base-policy KL before averaging per completion. Each adapter is saved after the 64th finite update.
- The predictor consumes the later Track A roster. It retains one greedy decoded completion per row, applies the frozen parser and retains malformed referrals with Brier probability 0.5 and rank score −1. Ordered identities, messages, token IDs, adapters and prediction artifacts are hashed for the freeze.
- The RunPod launcher works with an approved existing pod. It verifies placement before transferring the allowlisted files, stages the pinned checkpoint, runs the arms sequentially with equal time reservations and validates the retrieved files. It records estimated charges and prints the teardown steps on exit. [Projection schemas and commands](../../../loe-bench/c9/README.md)

## Dependencies and rights

The CPU environment is in `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/c9-venv`, on CPython 3.12.14. Runtime dependencies are installed outside Git. The trainers use explicit loss implementations so the declared token and completion reductions are visible in code. TRL and Datasets are available in the pinned environment for audit and later integration.

| Dependency | Version | License |
| --- | --- | --- |
| PyTorch | 2.8.0+cpu locally, 2.8.0+cu128 for the hosted run | BSD-3-Clause |
| Transformers | 4.55.2 | Apache-2.0 |
| PEFT | 0.17.1 | Apache-2.0 |
| TRL | 0.21.0 | Apache-2.0 |
| Datasets | 4.0.0 | Apache-2.0 |
| Accelerate | 1.10.0 | Apache-2.0 |
| NumPy | 2.2.6 | BSD-3-Clause |
| Hugging Face Hub | 0.36.2 | Apache-2.0 |
| Tokenizers | 0.21.4 | Apache-2.0 |
| Safetensors | 0.8.0 | Apache-2.0 |

The [pinned requirements](../../../loe-bench/c9/requirements.txt) apply to both environments. The launcher captures the full hosted package inventory. The production checkpoint is Apache-2.0. Its staging path validates the pinned model SHA-256 and tokenizer/config Git blob IDs, then records per-file SHA-256. The public synthetic-smoke fixture `yujiepan/qwen2.5-tiny-random` declares no license in the model card. Its files and derived smoke adapters stay in the private local workspace. [Production revision](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/tree/989aa7980e4cf806f80c7fef2b1adb7bc71aa306) · [Smoke revision](https://huggingface.co/yujiepan/qwen2.5-tiny-random/tree/0354728bb14944308c3134cf48d29302030a72c0)

The CPU dependency inventory `c9p-cpu-dependencies.json` in the same private LOE-Bench directory records 45 installed distribution versions, license metadata and SHA-256 of each installed `RECORD`. Its byte SHA-256 is `c71fb63432904865a52b963206e5975c589aad79be991ddce6b9ad61538e4546`.

## CPU dry run

**PASS.** The pinned tiny Qwen2.5 test checkpoint ran on CPU over 16 distinct synthetic training prompts and 16 synthetic forecast rows. The longest rendered training prompt was 526 tokens. Each arm performed two updates in the smoke schedule, one per eight-prompt batch. Both produced a finite saved adapter that reloaded successfully, and both generated 16 captured completions in the same roster order. The forecast parser treated all 32 completions as malformed and assigned the frozen fallback values. The 64 GRPO rollouts were also malformed, giving equal rewards within each group and zero standardized advantages. This exercises the full IO and optimizer path. The unit fixtures cover unequal reward and KL behavior.

| Arm | Completed updates | Fit and adapter save (s) | Prediction phase (s) | Captured rows |
| --- | ---: | ---: | ---: | ---: |
| SFT | 2 | 2.485 | 6.953 | 16 |
| GRPO | 2 | 122.297 | 5.844 | 16 |

Artifacts are under `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/c9p-smoke`. The checkpoint manifest is in the sibling `c9-tiny-qwen` directory. Both arm reports point to the same training roster and initial adapter. Both prediction manifests point to Track A token ID SHA-256 `b2a5e2bb61bfa62a57639cb18459e58e956579d73496756a1040e43a57c183c4`.

| Smoke artifact | SHA-256 |
| --- | --- |
| Tiny checkpoint manifest | `dc765d739e22f6d1dc000bac4cd5535674620f37ca778a5b5d758a8559c2038f` |
| Training roster manifest | `a06d0e6d639b32fbb5fe4522f5c3e1497af7acb6405488433408e06a20ee5942` |
| Initial adapter | `a8155cb33fe61d776e68946947b9c37268d8540258bbc2792df91ada84bb53ca` |
| SFT final adapter | `01134b2b815ab09d0cc271d6b2e007da2f826b1bc5e5788f6e28c79ea3e29dd3` |
| GRPO final adapter | `605d5995c7545eea810f0281843335cf41159509b59d2abdc526edec52b408b6` |
| SFT predictions | `ba8720ddcacab206d06b4e847e0a738ae0a68301c346bdbd2d4c7692b3866669` |
| GRPO predictions | `8bab27710476626f5ea3efab193d2ee814f9462e824943c36e627ae2b8f55fac` |

The first dependency resolver invocation selected the wrong PyTorch index. The CPU backend install succeeded. The first smoke process overlapped changes to the roster module and stopped at import. A fresh run after the source stabilized exited 0. The first roster unit test used an incorrect expected order and was corrected against the frozen SHA-256 rule before the successful suite.

## Tests

| Command | Result |
| --- | --- |
| `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/`, base CPython 3.12.10 | `PASS`, 230 tests, 2 optional training tests skipped, exit 0. Existing Purple Book resource warnings appeared. |
| `python -m unittest loe_bench.tests.test_c9_pipeline -v` in the CPU environment | `PASS`, 10 tests, exit 0. The controlled optimizer fixture exercised 64 steps per arm and one GRPO rollout per prompt batch. |
| `ruff check c9 loe_bench/tests/test_c9_pipeline.py` from `loe-bench/` | `PASS`, exit 0. |
| `uv pip check` and requirement resolution in the CPU environment | `PASS`, all 45 installed packages compatible and the pinned install required no changes. |
| `python -m pytest` from the repository root, base CPython 3.12.10 | Exit 1 with 2,760 passed, 50 skipped, one xfailed and two warnings. The eight failures match the documented SACR r2/r3 supervisor budget failures for `nan`, `inflated`, `erased` and `insufficient`. |

## Budget estimate and placement

The public RunPod catalog and its unauthenticated GPU-types query returned no priced A10 placement during C9P. The estimate below uses the frozen maximum rate of USD 1.40/GPU-hour. A live A10 quote, stock and approval remain pending. The storage estimate uses the published USD 0.10/GB-month container rate, 20 billable GB and a 730-hour month for planning. The USD 1.00 combined non-GPU reservation includes disk, transfer, fees, taxes and cleanup. [RunPod catalog](https://www.runpod.io/gpu-models) · [Pod pricing](https://docs.runpod.io/pods/pricing) · [Frozen caps](../../../loe-bench/data/C9_SPEC.json)

| Allocation | GPU-hours at cap | GPU USD at 1.40/h | Disk USD estimate | All-in USD with full non-GPU reserve |
| --- | ---: | ---: | ---: | ---: |
| SFT | 2.50 | 3.50 | 0.007 | 4.00 |
| GRPO | 2.50 | 3.50 | 0.007 | 4.00 |
| Combined | 5.00 | 7.00 | 0.014 | 8.00 |

## Remaining gates

After the C′ gate, the planner admits the S0 development projection and Track A owner verifies the full roster and its expected hash. The C9P code checks the projection and proof structure. Independent data-lane evidence establishes the source coverage, eligibility and completeness. Schedule the approved training window in December 2026 or January 2027. A10 availability, GPU fit, throughput, hosted installation, SSH transfer and final billing remain unverified. Keep sufficient time for setup, artifact pull, deletion and timestamping within the caps. Freeze the core Track A arms on their independent schedule. [OSF update](../OSF-UPDATE-SHEET.md) · [Run commands and admission](../../../loe-bench/c9/README.md#approved-runpod-execution)

This receipt is the executor handoff and project-memory entry for planner integration. Preserve the CPU smoke as engineering evidence. Calendar, data and budget release remain separate from source review and the future Track A score.
