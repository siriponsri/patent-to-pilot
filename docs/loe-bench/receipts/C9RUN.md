# C9RUN execution receipt

**BLOCKED on 28 November 2026.** SFT and GRPO are both `NOT_RUN`. The C′ gate passed. The registered training window has yet to open, the merged runtime rejects the approved L4, and the development projection is pending. The exploratory comparison and Track A predictions are `NOT_RUN`. [C′ gate receipt](GATE.md) · [Approved OSF update 2](https://api.osf.io/v2/schema_responses/6b0a61a4341762fcbae66946/) · [C9 protocol](../C9-PROTOCOL.md)

## Admission and deviation

- The OSF response `6b0a61a4341762fcbae66946` has approval status `approved` and modification timestamp `2026-11-28T05:10:26.286139Z`. It permits training in December 2026 or January 2027, after the C′ gate and before the core Track A freeze. This dispatch began on 28 November. C9 follows the core freeze schedule independently.
- **Approved hardware substitution, 28 November 2026.** The planner's placement check found no US A10 offer. The first author approved one 24 GB NVIDIA L4 on RunPod Secure Cloud in US-MO-2 at the quoted USD 0.69/hour, with an all-in envelope of approximately USD 4.50. Both arms must use the same GPU type. This substitution has yet to be exercised. A live itemized quote and the availability of the exact placement must be checked before creation. The approval names volume `8n6rnzljwg` for possible weight reuse, subject to suitability. Keep each arm within 2.5 GPU-hours and USD 3.50 in GPU charges. Account for setup, prediction, transfer and teardown in the registered USD 8 and approved approximately USD 4.50 total caps. Stop if the approved placement is unavailable.
- The C9P trainer and predictor share an A10-only production runtime guard. The combined RunPod launcher also requires an A10 and a full Track A roster and runs predictions immediately after each fit. The card requires the merged code as supplied and defers predictions to the freeze card. The planner needs to commission and review an L4-compatible execution path before renting the L4. [Trainer guard](../../../loe-bench/c9/train.py#L23) · [Launcher guards and phases](../../../loe-bench/c9/runpod.py#L34)

## CPU preparation and execution record

The checkout started clean. `loe/C9RUN` was cut from fetched `origin/research/loe-bench` at `6fdec7d855370bcbe4f6404f42779d4693b2a37a`, which contains the merged C9P code and the requested minimum base `51487726`. The receipt is this card's executor handoff and memory entry.

The documented C9 roster builder requires a planner-admitted `c9-development-v1` projection and its independently recorded byte SHA-256. The merged tree contains a loader and synthetic fixture. The private LOE-Bench artifact inventory yielded no admitted C9 development projection. The GATE custodian projection belongs to a different evidence role. No protected test partition or outcome record was opened. The data lane must deliver the projection with verified S0 coverage and linkage and as-of provenance for annual January 1 cutoffs from 1995 through 2014, with all outcome windows closing by 2016-01-01. [Projection contract](../../../loe-bench/c9/README.md#admitted-input-projections) · [C9P handoff](C9P.md#remaining-gates)

- **Checkpoint staging PASS.** The unchanged `python -m c9.checkpoint` downloaded and verified the Apache-2.0 Qwen2.5-1.5B-Instruct revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` in `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/c9/checkpoint`. `checkpoint.json` byte SHA-256 is `0a9deecdd2deb028c8555a236241f6fe4bc9d9fe9ee64be4493daa397527459e`. `model.safetensors` SHA-256 is `dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee`. The manifest records all eight file digests. [Pinned upstream checkpoint](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/tree/989aa7980e4cf806f80c7fef2b1adb7bc71aa306)
- **Fixture checks PASS.** `python -m unittest loe_bench.tests.test_c9_pipeline -v` ran in the existing C9 CPU environment from `loe-bench/`, with 10 tests passing in 70.867 seconds and exit code 0. The checks cover the frozen schedule and controlled optimizer steps, among other C9 contracts.

| Evidence | Status |
| --- | --- |
| Production development projection SHA-256, roster SHA-256, ordered key, message and token hashes | `NOT_RUN`, pending admitted input |
| At least eight distinct rows, both classes and 32 batches of eight | `NOT_RUN` on production rows |
| SFT 64 updates, wall time, loss summary and final adapter SHA-256 | `NOT_RUN`, zero production updates |
| GRPO 64 updates, wall time, loss summary and final adapter SHA-256 | `NOT_RUN`, zero production updates |
| Live quote, pod ID, GPU log, billing interval and deletion | `NOT_RUN`, no pod created and deletion inapplicable |
| Incremental card spend | USD 0 |

## Resume and freeze handoff

When the data lane delivers the projection and its expected byte SHA-256, run the frozen CPU builder from `loe-bench/`. Its source checks enforce the class and distinct-row minima. Check the resulting 256 slots, retain the manifest outside Git and record its digest in this receipt. The paths below refer to files in the C9 private workspace.

```bash
python -m c9.roster --checkpoint "$C9_CHECKPOINT" \
  --projection "$C9_DEVELOPMENT_PROJECTION" --projection-sha256 "$C9_DEVELOPMENT_SHA256" \
  --out "$C9_PRIVATE/roster-manifest.json"
```

After calendar and data admission and planner review of the hardware execution path, re-quote the approved placement. Verify GPU fit and throughput against the remaining budget before production updates. Run the two arms sequentially, retain adapters and logs locally under `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/c9/`, and verify pod deletion and billing. Preserve the training output tree, including `training-roster.json`, `initial.safetensors`, `sft/` and `grpo/`, since the predictor verifies it as a pair.

At the freeze card, set `C9_CHECKPOINT` to the verified checkpoint, `C9_TRAINED` to the retrieved paired training tree, `C9_TRACK_A_ROSTER` to the full label-free JSON, `C9_TRACK_A_SHA256` to its independently recorded byte digest and `C9_FREEZE_OUTPUT` to an existing private parent directory. Run from `loe-bench/` on the reviewed production runtime matching the training manifest, with fresh output directories. These commands have not been run on a production roster.

```bash
python -m c9.predict --checkpoint "$C9_CHECKPOINT" --trained "$C9_TRAINED" \
  --arm sft --track-a-roster "$C9_TRACK_A_ROSTER" --track-a-sha256 "$C9_TRACK_A_SHA256" \
  --output "$C9_FREEZE_OUTPUT/sft-predictions"
python -m c9.predict --checkpoint "$C9_CHECKPOINT" --trained "$C9_TRAINED" \
  --arm grpo --track-a-roster "$C9_TRACK_A_ROSTER" --track-a-sha256 "$C9_TRACK_A_SHA256" \
  --output "$C9_FREEZE_OUTPUT/grpo-predictions"
```

The freeze owner verifies both output files and the paired hashes before the independently scheduled core prediction freeze, before any post-S0 outcome intake and by the registered external deadline. Keep the core freeze on its own schedule if C9 remains blocked.
