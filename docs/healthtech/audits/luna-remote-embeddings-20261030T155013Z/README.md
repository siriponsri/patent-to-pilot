# Luna remote-embedding continuation

Run ID: `luna-remote-embeddings-20261030T155013Z`

Parent run: `luna-remote-embeddings-20261030T151444Z`

Code candidate: `7812c8f`

Status: `PASS_LOCAL_REAL_CANARY_REMOTE_BLOCKED_ALLOCATION`

## Completed

- Rebound vector manifests to stable model identity plus immutable model and tokenizer artifact hashes; absolute host paths are no longer part of the model binding.
- Ran the targeted vector/runtime/integration/DAPFAM suite: `22 passed`.
- Ran a real ONNX/tokenizer local canary over 64 runtime rows with batch size 8 and shard size 32.
- Produced two little-endian float32 shards at dimension 384, interrupted after shard 0, resumed from the partial manifest, imported the completed bundle, and ran exact cosine search with a local query encoder.
- Verified finite vectors, stable artifact hashes, no partial manifest after completion, and no evaluator fields in the runtime input.
- Performed a strict read-only SSH/capacity check to `chaw@100.77.149.83`; host identity and capacity were observed, but no allocation was inferred.

## Still blocked

No remote input/model transfer or remote encoder job was started. The remote parent job root is absent, and the authorized GPU/CPU allocation, execution window, resource limits, Podi/shared-service constraints, and controlled-processing authorization are still not recorded.

The live capacity observation is evidence only: V100 and RTX 2080 Ti were idle at check time. It is not an allocation and no process was started, stopped, or changed.

Machine-readable evidence is in `REMOTE_CAPACITY_RECEIPT.json`, `CANARY_RECEIPT.json`, and `NEXT_ACTIONS.md`.
