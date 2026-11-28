# C9 paired training and prediction

Run the commands from `loe-bench/` using Python 3.12. Keep the environment, projections, checkpoints and run outputs outside Git. The [frozen C9 spec](../data/C9_SPEC.json) governs all production values. The [C9P receipt](../../docs/loe-bench/receipts/C9P.md) records verification and handoff.

## Local CPU smoke

Use an empty directory for each checkpoint or run. The example uses a Windows PowerShell session with `uv`.

```powershell
uv venv --python 3.12 C:/path/to/private/c9-venv
$c9python = 'C:/path/to/private/c9-venv/Scripts/python.exe'
uv pip install --python $c9python --torch-backend cpu -r c9/requirements.txt
& $c9python -m c9.checkpoint C:/path/to/private/tiny-qwen --dry-run
& $c9python -m c9.dry_run --checkpoint C:/path/to/private/tiny-qwen --output C:/path/to/private/c9-smoke
& $c9python -m unittest loe_bench.tests.test_c9_pipeline
```

The smoke uses 16 synthetic training prompts across two batches, one update per batch per arm, and 16 synthetic forecast prompts per arm. The smoke retains the frozen prompt renderer, tokenizer interface, loss reductions, LoRA settings and 160-token cap. A random checkpoint can produce malformed JSON for every row. The end-to-end check requires captured completions, not forecasting quality. Smoke adapters cannot pass the production prediction checks.

## Admitted input projections

Supply two JSON files and their **independently recorded byte SHA-256**. Both envelopes have exactly `schema`, `s0_manifest_lf_sha256` and `rows`. Use the S0 manifest digest from the spec. The code opens these projections and the repository manifest. Construct the projections in the authorized data lane using FIX2c active-moiety identity and eligibility, cutoff availability, and independently verified source coverage.

| Schema | Required fields per row |
| --- | --- |
| `c9-development-v1` | `drug_key`, `forecast`, `original_nda`, `type1`, `first_final_anda`, `covered_through`, `resolved_linkage`, `provenance` |
| `c9-track-a-v1` | `drug_key`, `forecast`, `provenance` |

- `forecast` is the exact L1e row with `entity`, `t0`, `horizon_months` and `as_of_evidence`. Use the frozen source projection, including missingness. `drug_key` is the frozen active-moiety key, which may differ from the display name.
- Use ISO dates. `original_nda` and `type1` are eligibility dates. The development exporter clips final original ANDA and coverage to the row's 24-month window end. Use `null` for absent events or unknown coverage and a Boolean for resolved linkage. Include prior final approvals when needed to exclude an ineligible row. Never export outcomes after the window end or rows outside 1995–2014. A zero requires resolved linkage and independently verified complete coverage.
- Each `provenance.as_of` entry has `source_id`, `version`, `sha256`, `locator`, `record_date` and `available_on`. Use dates at or before the forecast cutoff. Training rows additionally have `provenance.outcome` with the same fields for S0 coverage and outcome evidence. An outcome record date must fall by window close. Its source availability can extend to S0. The file hash fixes the exact proof supplied. The data lane attests the truth and completeness of the projection.
- Track A supplies the full eligible S0 roster, including rows with missing evidence, in freeze order. Use S0 cutoff `2026-11-27` and horizon `24` for all rows. The C9 code rejects extra fields and duplicates. The Track A freeze owner supplies the full-roster attestation and expected hash.

To check and freeze a training roster on CPU with the production tokenizer, stage the production checkpoint without `--dry-run`, then run:

```text
python -m c9.roster --checkpoint /private/checkpoint --projection /private/training.json --projection-sha256 TRAIN_SHA --out /private/roster-manifest.json
```

The manifest pins ordered keys, serialized messages, token IDs, model and input hashes. Both arms repeat this preparation and verify the same manifest before training. The 2,048-token limit applies after the checkpoint's chat template.

Use the [C9PROJ receipt](../../docs/loe-bench/receipts/C9PROJ.md) for the frozen development artifacts, their provenance and the training-only launch with a roster hash check.

## Approved RunPod execution

Admission requires the C′ gate pass, the approved development projection and a live itemized quote approved before creation. The C9 runtime accepts one approved 24 GB NVIDIA A10 or NVIDIA L4. Both arms and Track A prediction must match the detected GPU and runtime in the shared training manifest. The C9RUN2 deviation limits its placement to one L4 on Secure Cloud in US-MO-2. Use the pinned CUDA 12.8 and Torch 2.8 runtime, Linux with Python 3.12 and direct OpenSSH/SCP access. Verify the pod's SSH host key using the approved identity record. Record the pod creation or billing start at the earliest billed instant and round time reservations conservatively. Schedule teardown before either arm's cap or the core Track A freeze. [C9RUN2 receipt](../../docs/loe-bench/receipts/C9RUN2.md)

For the training-only card, run the two commands below in order on the admitted pod after verifying fit and throughput. Use the same output directory so GRPO verifies the training roster, runtime and initial adapter saved for SFT. Pull the full trained directory with both arm logs and verify the file hashes before terminating the pod. The freeze card supplies the Track A roster and runs predictions later.

```text
python -m c9.train --arm sft --checkpoint /private/checkpoint --projection /private/training.json --projection-sha256 TRAIN_SHA --output /private/trained
python -m c9.train --arm grpo --checkpoint /private/checkpoint --projection /private/training.json --projection-sha256 TRAIN_SHA --output /private/trained
```

The combined launcher below additionally requires the full Track A roster.

Store the following approval fields in a private JSON file. `live_quote_ref` points to the itemized quote, including storage, transfer, taxes, fees and provider billing increments. `owner_approval_ref` and `cprime_pass_ref` point to recorded decisions. Use timezone-qualified timestamps. Enter equal `arm_seconds` for each arm's training and predictions. Split time already billed and the `setup_seconds`, `pull_seconds` and `teardown_seconds` reservations evenly when checking arm caps.

```text
gpu, gpu_count, data_center, pod_id, ssh_host, ssh_port,
live_quote_ref, owner_approval_ref, cprime_pass_ref,
gpu_usd_per_hour, non_gpu_total_usd, ephemeral_storage_gib,
billing_started_utc, core_freeze_utc,
setup_seconds, arm_seconds, pull_seconds, teardown_seconds
```

```text
python -m c9.runpod --approval /private/approval.json --identity /path/to/ssh-key --projection /private/training.json --projection-sha256 TRAIN_SHA --track-a-roster /private/track-a.json --track-a-sha256 TRACK_SHA --output /private/new-c9-run
```

The launcher checks the pod ID and GPU name, stages the allowlisted code and projections, and downloads the pinned Hugging Face files with digest checks. It runs SFT then GRPO with separate equal phase deadlines. Each phase fits its adapter and predicts on the same Track A roster. The local launcher verifies the retrieved inventory and paired manifests and records estimated charges to launch exit. On any exit, follow the teardown checklist immediately and record the final provider charges and deletion readback. Treat an incomplete, unverified or over-budget pair as `NOT_RUN`.

The prediction script can also consume the later frozen roster directly on the approved production runtime.

```text
python -m c9.predict --checkpoint /private/checkpoint --trained /private/trained --arm sft --track-a-roster /private/track-a.json --track-a-sha256 TRACK_SHA --output /private/sft-predictions
```

Each prediction result has one `predictions.jsonl` row per roster row with the captured completion, parsed fields, Brier probability and rank score. `prediction.json` records exact hashes and malformed counts. For a completed pair, freeze the full hash packet with the planner before the core Track A freeze, before any post-S0 outcome intake and by the spec's external deadline.
