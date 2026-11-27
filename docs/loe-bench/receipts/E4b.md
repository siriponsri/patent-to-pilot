# E4b RunPod infrastructure and LLM smoke

Branch `loe/E4b` from `71bb4c8e`. The [D40 owner envelope](../../maintenance/OWNER-DECISIONS-20261122.md#d40--loe-bench-becomes-the-active-program-27-november-2026) covers USD 20 for the T10 arm. E4b has a USD 4 cap.

**PASS.** The L4 smoke completed 20 of 20 label-free forecasts and all 20 responses met the strict JSON schema. All three E4b pods returned HTTP 404 after deletion. The staged 30 GB volume remains available in US-MO-2.

## Prompt, model and transfer

- The prompt forecasts whether a first **final FDA ANDA approval** occurs within the row's horizon after `t0`. Tentative approvals are excluded. The existing output field and action names remain stable. A response must be one JSON object with all three schema fields. Prose, code fences, duplicate keys and schema errors trigger `ABSTAIN_REFER_TO_EVALUATOR`. [REG endpoint review](../REGULATORY-RULES.md#summary-of-findings)
- Qwen2.5-7B-Instruct uses Apache-2.0 and revision `a09a35458c702b33eeacc393d103063234e8bc28`. The 13-file snapshot occupies 15.243 GB. All four weight SHA-256 values matched the publisher's LFS digests, and each remaining file matched its Git blob ID. The staging manifest records observed SHA-256 values, dependency wheel metadata and the image digests. [Publisher model card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/tree/a09a35458c702b33eeacc393d103063234e8bc28) · [Model manifest](../../../loe-bench/data/E4b_model.json) · [Staging manifest](../../../loe-bench/data/E4b_stage.json)
- The US-MO-2 L4 transfer pod accepted direct SSH and ran `nvidia-smi`. One SCP stream from the owner PC uploaded 100,000,000 random bytes in 231.019 s, or 0.433 MB/s. Local and remote SHA-256 matched. A 100,000,000-byte HTTP 206 request from the same pod to the pinned Hugging Face shard took 1.641 s, or 60.951 MB/s. The requests overlapped in time. The separate staging pod downloaded and checked the full pinned snapshot in 75.249 s with four workers. Rate comparisons depend on direction, concurrency and destination.
- The volume contains the staged model, harness and dependencies under `/workspace/e4b`. The staging pod exited successfully after importing PyTorch 2.8.0+cu128 and Transformers 4.55.2. The smoke used a separate pod and loaded only local model files.

## GPU smoke and later-run estimate

| Measurement | Observed value |
| --- | ---: |
| Valid JSON | 20/20 (100%) |
| Schema-valid abstentions | 1/20 |
| Mean end-to-end inference latency per row | 1.795 s |
| Slowest row | 2.624 s |
| Tokenizer and model load | 8.926 s |
| Peak PyTorch VRAM allocated / reserved | 14.284 / 14.414 GiB |

The single L4 ran fp16 with greedy decoding, 160 maximum new tokens, seed 20261127 and a 90% memory fraction. The runner checked the cumulative JSON validity rate after each row and would exit below 90%. The detached job had a 600 s timeout. No OOM occurred. The [smoke record](../../../loe-bench/data/E4b_smoke.json) contains the input and raw-output hashes. Raw artifacts are kept locally under `../_private_artifacts/loe-bench/E4b`.

Using the mean latency and a startup allowance of 120 s plus the measured load, 3,300 forecasts across both horizons project to **1.68 h and USD 1.16** of pod time. If 3,300 means rows per horizon, 6,600 forecasts project to **3.33 h and USD 2.30**. The sealed-period count remains unknown. A scenario of 1,000 forecasts is **0.53 h and USD 0.37** for one pod. Add storage for the actual retention interval. [Estimate and formula](../../../loe-bench/data/E4b_estimate.json)

## Spend and cleanup

| Resource | ID | Read-back |
| --- | --- | --- |
| L4 transfer pod, US-MO-2 | `a96jnvf4ki8i3j` | Deleted, HTTP 404 |
| Unused 30 GB volume, US-TX-3 | `l3cnfrkzpo` | Deleted, HTTP 404 |
| L4 staging pod, US-MO-2 | `vd5an5r0zd2mj6` | Deleted, HTTP 404 |
| L4 smoke pod, US-MO-2 | `o428rw4rvtzm3w` | Deleted, HTTP 404 |
| Staged 30 GB volume, US-MO-2 | `8n6rnzljwg` | Retained, read back after cleanup |

The live pod quote was USD 0.69/h for each L4. The elapsed-time estimate is **USD 0.152** at closeout. The prepaid balance changed from USD 27.53257 to USD 27.40782. The balance change is account-wide and the per-resource billing endpoints had no posted rows at closeout. The retained volume costs an estimated USD 2.10/month while it exists. The v2 catalog and volume schemas expose no storage rate, so the storage allowance uses RunPod's published rate. One month of future retention plus elapsed E4b usage totals approximately USD 2.25. [RunPod storage pricing](https://docs.runpod.io/pods/storage/types) · [Resource ledger](../../../loe-bench/data/E4b_runpod_ledger.json)

## Scope and local verification

- The smoke sampled ten rows per horizon, first 12 and then 24 months, with Python `random.Random(1).sample` in CSV order within each horizon. An allowlist retained `entity`, `t0` and `horizon_months`. The source is the published development example. No protected test inputs or outcome labels were opened or sent.
- `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` passed **167 tests**. Root `python -m pytest -q` ran and reported only the eight pre-existing SACR r2/r3 supervisor budget failures allowed by the standing rules.

## Failures and limitations

- RunPod returned HTTP 400 when secure RTX 4090 stock in US-TX-3 changed between the catalog read and creation. No pod ID was issued. The original empty volume was removed and verified absent. E4b used L4 in US-MO-2 with the replacement volume.
- The transfer host exposed cgroup v1. The initial v2 path check failed and a v1 read confirmed a 13.6-CPU quota and a 93,999,996,928-byte memory limit. The first staging collection check ran before the import completed. A later read returned exit 0 and pulled the verified manifests.
- Transformers warned that the model's temperature, top-p and top-k settings may be ignored during greedy generation. Both the startup and inference checks completed.
- The prompt date instruction cannot establish which facts were in the model's training data. The smoke measures runtime and output format on a small development sample. It supplies no accuracy, calibration or benchmark comparison against an observed outcome.

## Next action

The Planner can review the receipt and lock the T10 model revision, harness, scope, input allowlist and decoding before authorizing later runs. Confirm the number of development forecasts at each horizon and refresh L4 price and capacity before opening a pod. Preserve the test seal until the preregistration release and use only its label-free inputs for inference. Reconcile the posted E4b billing before allocating the rest of the arm budget.
