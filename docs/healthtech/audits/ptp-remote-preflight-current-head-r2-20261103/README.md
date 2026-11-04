# Current-head remote preflight R2 — 2026-11-03

Status: `PASS_READ_ONLY_NO_ACTIVE_EXPERIMENT_ALLOCATION_UNKNOWN`.

This package refreshes the remote observation for the original Patent-to-Pilot
goal without starting a model job, touching the existing HTTP service, reading
the private ledger, or changing the 24-hour window.

## Observation

- Candidate: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Host: `dr-train`
- Remote observation: `2026-11-02T22:36:37Z`
- Relevant experiment processes: `0`
- Approved V100: visible and idle; `32,495 MiB` free, `0 MiB` used
- Other GPU: RTX 2080 Ti visible; not permitted for this goal
- Existing service: PID `1745699`, `serve_http.py`, port `18787`, start
  `2026-10-31T08:27:48Z`; left untouched
- GPU lock marker: present, `0` bytes; ownership/allocation cannot be inferred
- Allocation: `UNKNOWN_NOT_GRANTED_RESOURCE_OBSERVATION_ONLY`

## Decision

Do not launch the local Qwen or embedding branch from idle capacity. The
approved GPU is visible, but there is no current allocation/ownership/window
evidence and the lock marker is insufficient. Continue offline work and owner
review; refresh this gate only when an authorized allocation reference exists.

No API call, GPU job, dataset download, remote write, ledger mutation, budget
reset, or window reset occurred.

Machine-readable details are in [`verification.json`](verification.json).
