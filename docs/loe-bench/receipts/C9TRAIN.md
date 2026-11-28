# C9TRAIN training receipt

**BLOCKED on 28 November 2026.** RunPod reported no available Secure Cloud NVIDIA L4 in the United States. No pod was created. SFT and GRPO are `NOT_RUN`, with zero updates and USD 0.00 in incremental card spend. This receipt is the executor handoff and project memory entry for C9TRAIN.

## Authorization and checkout

The main planner verified OSF registration p2smd update 3, schema response `6b0a99f9c46379c38a46bcd3`, approved at 09:09 UTC. The training window opens after the C′ gate and closes at the core Track A prediction freeze. The C′ gate passed and the dispatch confirmed that the core freeze had yet to occur. Update 3 supersedes the calendar check in the C9PROJ launch block. The production roster, seed `20261127`, SFT then GRPO order, and 64 updates per arm remain frozen. [Update 3 wording](../OSF-UPDATE-3-SHEET.md) · [Planner verification and dispatch](../MEMORY.md) · [C′ gate](GATE.md) · [Launch block](C9PROJ.md#training-card-launch)

The first author approved one 24 GB NVIDIA L4 on RunPod Secure Cloud at up to USD 0.69/hour, with a USD 4.50 all-in card allowance within the registered USD 8 cap. Each arm is limited to 2.5 GPU-hours and USD 3.50 in GPU charges. The program GPU envelope is USD 23, with about USD 3.51 recorded as used at dispatch. US-MO-2 was preferred, with other US data centers permitted at the same rate ceiling. [Hardware deviation](C9RUN2.md) · [Frozen protocol](../C9-PROTOCOL.md)

The executor cut `loe/C9TRAIN` from fetched `origin/research/loe-bench` at `6f803c573b36cad71e81ca3690cf095ef75c9e63`. The start-of-card worktree was clean and the local and remote branch checks showed no existing C9TRAIN branch.

## Provider quote and placement

RunPod `get-gpu-type` returned 24 GB, Secure Cloud pricing of USD 0.69/hour and US pod availability `NONE`, with and without a CUDA 12.8 floor. Unrestricted availability was `LOW` at EU-RO-1, EUR-IS-1 and EUR-IS-2 on CUDA 13.2 hosts. The fully paginated North America data-center read listed 17 US data centers with no available L4 entry. The direct US-MO-2 read likewise showed no L4. Rechecks at approximately 09:14 and 09:15 UTC still showed US availability `NONE`.

The volume read confirmed `8n6rnzljwg` is the existing 30 GB STANDARD volume in US-MO-2. Its suitability for C9 weight reuse remains unverified. It was left as found. The live compute quote matched the approval. With no eligible placement, a placement-specific itemized quote and admission were `NOT_RUN`.

## Frozen input verification

Recomputed byte digests matched both committed manifests. The existing pinned Windows C9 Python 3.12 environment also replayed `python -m c9.roster` against the private projection and checkpoint. All 12 generated manifest fields matched, including the ordered keys, messages and prompt token IDs. The replay retained 256 slots and a maximum of 757 prompt tokens. The private replay manifest is `c9train-roster-preflight-189891b4bba34de5b49f573bcd8b9f76.json` in `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/c9/`.

| Private input | SHA-256 |
| --- | --- |
| `c9_dev_projection.json` | `d6a824d3f4ed0a6cd4c8d1c581e70fa3d449a213c386671f0edd7e87356c8e1c` |
| `c9_dev_roster.jsonl` | `f77b777415c5246eedee831068ac2c003a4ba354c87af5a8abdd8f7ccdfc316c` |
| `checkpoint/checkpoint.json` | `0a9deecdd2deb028c8555a236241f6fe4bc9d9fe9ee64be4493daa397527459e` |

[Projection manifest](../../../loe-bench/data/C9_DEV_PROJECTION_MANIFEST.json) · [Roster manifest](../../../loe-bench/data/C9_DEV_ROSTER_MANIFEST.json)

## Execution and handoff

| Evidence | Status |
| --- | --- |
| SFT | `NOT_RUN`. 0 of 64 updates. Runtime, loss summary and final adapter hashes unavailable. |
| GRPO | `NOT_RUN`. 0 of 64 updates. Runtime, loss summary and final adapter hashes unavailable. |
| GPU detection and logs | `NOT_RUN`. No training manifests or logs were generated. |
| Pod ID, start, stop and deletion | No pod created. Deletion confirmation and timestamp are inapplicable. |
| Incremental card spend | USD 0.00. No billable request was issued. |
| Track A predictions and outcome evaluation | `NOT_RUN`. |

**PASS.** From `loe-bench/`, `python -m unittest discover -s loe_bench/tests -t .` ran 239 tests in the pinned C9 Python 3.12 environment with exit 0 and no skips. The existing Purple Book file-handle warnings appeared. The preliminary system Python 3.12 run also exited 0, with five optional runtime tests skipped.

At the next admission, confirm that the core freeze window remains open and refresh the US Secure Cloud L4 quote. Once stock is confirmed, run the training-only launch sequence from C9PROJ under the update 3 timing rule. Retrieve and rehash the paired outputs before deleting the pod. Hand the verified adapters and detected GPU/runtime to the freeze card.
