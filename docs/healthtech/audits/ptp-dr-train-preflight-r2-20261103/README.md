# dr-train allocation recheck (2026-11-03)

This is a read-only continuation checkpoint for the original Patent-to-Pilot O1-O4 goal. It re-polled the known `dr-train` host and preserved the existing service. No remote job, model inference, transfer, install, lock mutation, or service restart was performed.

## Candidate and host

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- SSH target: `chaw@100.77.149.83` via `dr-train`
- Host-key checking: strict; batch mode; one read-only probe
- Remote job root: `/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031`

## Result

- Approved V100 UUID `GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089` is visible with `0 MiB` used and `32,495 MiB` free.
- The remote resource record still says `UNKNOWN_NOT_GRANTED_RESOURCE_OBSERVATION_ONLY`; no allocation reference, quota, lease, or runtime window was evidenced.
- The pre-existing HTTP service PID `1745699` remains at start time `2026-10-31 08:27:48 UTC` and was left untouched.
- No separate encoder/generation process was observed after excluding the probe's own shell matches.
- The known GPU lock exists but is a zero-byte file; ownership cannot be inferred from it.
- The unapproved RTX 2080 Ti remains outside scope.

Observed free capacity is not an allocation. O2 therefore remains `PARTIAL_ALLOCATION_NOT_EVIDENCED`, and the next remote encoder batch must not start from idle capacity.

## Private evidence

Raw remote observation files remain outside Git under the permitted private-artifact root:

- `ptp-dr-train-preflight-r2-20261103/resource-observation.json` SHA-256 `8fb6dfc50b3f247a69eecb1a19201066ada03f34a2ffe9b9a4a49e84c4759ebd`
- `ptp-dr-train-preflight-r2-20261103/process-lock-observation.txt` SHA-256 `e7ee9257d3db21e85eb51cb91dc99bdc27f5d1ac0d8a3765bf050e679fce2d93`
- `ptp-dr-train-preflight-r2-20261103/lock-observation.txt` SHA-256 `7ebb0f1f5ecd8c0aab12ad296391144d1f32a3039641d1f02390d505971c313c`

No credentials or restricted payloads were copied into this audit.

## Next action

Obtain an authorized allocation reference, quota/lease, allowed job root, and runtime window. Then recheck the exact GPU/lock state and resume the existing resumable encoder. Keep the OpenRouter gate independent.
