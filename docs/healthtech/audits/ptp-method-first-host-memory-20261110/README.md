# Host-memory observation before a research runtime exists

Status: OBSERVED_CAPACITY_ONLY; resource acceptance NOT_ESTABLISHED.

On 2026-11-10 at 04:10:09 UTC, a read-only SSH observer on the existing authorized
research host read selected /proc/meminfo counters and its own cgroup-v2 memory
counters through the visible ancestor chain. No corpus, labels, vectors, model files,
credentials or other process command lines were read. No job or allocation probe ran.

| Quantity | Bytes | Interpretation |
| --- | ---: | --- |
| Host MemTotal | 135035817984 | Physical memory reported by Linux |
| Host MemAvailable | 122095116288 | About 113.71 GiB; momentary OS estimate |
| One recorded vector payload | 6363865088 | Calculated from the existing A14 dimensions |
| Input plus detached array copy | 12727730176 | About 11.85 GiB; excludes overhead |
| Available minus those two arrays | 109367386112 | Arithmetic only; not a reserved budget |

All three observed cgroup levels reported memory.max and memory.high as `max`.
This means the inspected hierarchy did not provide a finite memory cap for this
SSH observer. It does not attest any future isolated runtime, other resource controls,
or permission to change global/cgroup settings. Ancestor memory.current includes other
work; it is neither this probe's RSS nor the research job's peak.

The observation does not show a host-capacity shortfall for the two-array payload.
Therefore capacity alone does not justify weakening BoundCPUIndex's detached-copy
invariant or replacing it with mutable borrowed storage. The original ownership
strategy remains unchanged. Model loading, Python identifiers, owner arrays, norm
temporaries, scoring buffers and library workspaces are not included in the estimate.
Memory mapping is not proof that all input pages remain nonresident.

## Remaining actual acceptance

Once the owner designates an isolated runtime, declare its memory budget, concurrency,
model/index residency policy and bounded termination behavior before any measured run.
Check limits and available memory inside that runtime, then collect peak process/cgroup
memory and stage-specific timing under the intended input scale, retaining failed runs.
The present snapshot cannot serve as that acceptance and must not become an automatic
launch decision. Do not start an allocation experiment or modify host controls here.

`observation.json` preserves raw allowed counters, timestamp and calculated payloads.
`observe_host.py` preserves the read-only collection procedure; rerunning it creates a
new observation and should use a separately versioned evidence destination rather than
overwrite this historical record. Host values can change immediately after collection.

CPU-ESCAPE-004, curator/isolation and view-family rejection decisions remain pending.
R1 real parity, generation/fidelity and R3–R6 gates remain incomplete. Previous CPU job
termination evidence is historical; this observation did not poll or restart that job.
