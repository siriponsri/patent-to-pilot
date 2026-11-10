# MTM and DAPFAM resumed work order

Owner explicitly requested continuation on 10 November 2026 using the attached
PTP_MTM_DAPFAM_LONG_RUN_HANDOFF_20261110_TH_EN.md. Its proposed approvals are not
owner grants. This package records takeover and a single consolidated pending
decision request, not a new R0 audit or scientific result.

Base main and origin/main both verified at
85de926818e8f9ed5a162386c9de57e5d0ab0648. Previous writer explicitly stopped at that
checkpoint. Codex in the same chat now owns repository writes; no additional agent
or GPU job has been started. Preserve the owner's untracked November 9 handoff.
The goal service still reports the existing goal BLOCKED; its exposed tools cannot
resume that status. Do not create a replacement goal or claim the service is ACTIVE.
The owner's renewed work request authorizes preparation in this same goal's scope.

## Current continuation matrix

| Workstream | Status | Next concrete action |
| --- | --- | --- |
| Shared archive packaging | READY | Reuse verified byte-stable packager; keep CPU-003 immutable |
| CPU-ESCAPE-004 | NEEDS_OWNER_DECISION | New declaration and one bounded attempt after answer |
| MTM dev inputs | NEEDS_OWNER_DECISION + NEEDS_INPUT | Owner-curator runs supplied staging outside agent; verify only dev receipts |
| MTM A03/P-main-X/U baseline parity | NEEDS_INPUT | Existing tools/declaration; requires actual isolated dev inputs |
| DAPFAM native dev | NEEDS_INPUT | Preserve existing split, stage native TA queries and full TAC corpus/provenance |
| DAPFAM native baseline | NEEDS_INPUT | Reuse verified existing vectors; quantify backend/protocol differences |
| Family-rejection/fidelity | NEEDS_OWNER_DECISION | Adopt prospectively; typed evidence exists, rejection continuation is not implemented |
| Actual SACR generation | BLOCKED_BY_FAILURE | CPU compatibility, approved one smoke and runtime/load identities first |
| Pilot/full dev | NEEDS_OWNER_DECISION + NEEDS_INPUT | Concrete budget requested; run only after own integrity/fidelity/resource gates |
| Final test | NOT_AUTHORIZED | Both protected sets stay closed; later immutable freeze proposal only |

## Live evidence and isolation option

At 2026-11-10T10:51:17Z, SSH succeeded. No V100 compute process or unclassified
project Python process was observed. PID1745699 is the retained HTTP service; it was
not stopped. CPU-003 terminal remains FAILED and its child PID is absent. These are
snapshots, not a reservation: repeat the relevant check and acquire the shared slot
at actual launch. See live-preflight.json.

Docker exists and the current account can access its socket. Existing base images
include Python3.12, Ubuntu24.04 and PyTorch2.6/CUDA12.6; see existing-base-images.json.
Image presence is not compatibility or isolation acceptance. In particular, the
existing research venv's historical Torch2.8 is not reproduced by the PyTorch2.6
image. No image was pulled, started, modified or inspected for secrets. An initial
image listing returned unrelated image metadata; only relevant base-image fields
are retained. Two Windows wildcard source searches failed and were replaced by
bounded explicit-file/directory searches; no dataset contents were read.

Proposed solo workflow: owner acts as curator, executes preparation separately,
and returns only counts/hashes and allowed dev paths. Runtime and evaluator use
separate temporary unprivileged containers, no network, read-only allowlisted inputs,
no protected/mixed source mounts, no whole-job-root mount and no Docker socket.
No ACL/account/daemon/security-setting changes. Runtime resource ceilings must be
enforced and independently checked before data use. Container compatibility remains
to be tested after approval, using safe fixture inputs first.

This requires a transparent protocol amendment: the host-side Codex orchestrator
still has host SSH access, although it will not open mixed/protected files. Therefore
the arrangement isolates computational runtime/evaluation, not the agent's entire
host identity. It cannot be described as physically agent-blind. Owner may instead
provide an already isolated environment; no environment is invented or assumed.

## Consolidated proposal sent to owner — PENDING, not adopted

1. CPU-004 once: same14 authored cases/schema/candidate, packaging-only change,
   120s plus5s termination grace, zero model calls, no retry. If successful, one
   new model smoke <=30min; baseline <=4h per benchmark; fidelity generation <=8h
   combined; pilot20 deterministic allowed-dev queries per benchmark <=2h combined;
   full dev <=48h combined after all preregistered gates. Cumulative GPU <=72h in
   this continuation, one job at a time, <=8CPU threads, <=32GiB RAM and <=40GiB
   combined incremental storage within the existing V100 authorization window.
   These are proposed hard ceilings, not throughput predictions or fresh disk
   allowances. Include all attempts and preserved artifacts in accounting.
2. Owner-curator plus the runtime-isolation amendment above, or an explicitly
   supplied isolated environment. No changes to system privileges are proposed.
3. Adopt prospective family rejection only for verified normal terminal unusable
   generation; retain independent valid anchor/compact, all failures and costs.
   No repair/refill. Unknown process state/infra failure or unresolved semantics
   still stops the dependent work. Owner reviews fixed up-to100 dev queries per
   benchmark, source first and without retrieval labels/scores. Critical defects
   or unresolved required judgments fail the configuration; no human per-query
   edits/filtering and no independent-expert claim. Add the source-anchor plus
   matched-coverage dev control, fully define it before observing its outcomes.

No positive-score gate is proposed. Engineering/fidelity/resource acceptance
controls automatic pilot-to-full-dev progression. A required owner fidelity review
is a finite real review dependency, not something an agent can silently impersonate.
No automatic retries, paid APIs, training, corpus re-encoding, BigQuery or protected
evaluation. An exceeded budget stops only its dependent action. No policy adopted
and no actual job dispatched while the consolidated question remains unanswered.

## Source-level DAPFAM preparation finding

build_dapfam_acquisition_stage0.py builds query text through dense_query_text using
title, abstract and claims; it also reads mixed qrels/queries and recomputes the split.
Do not execute it in the development-agent session or reuse its historical TAC query
file as native TA. The current dapfam_native.py contract uses title+abstract queries,
TAC corpus and full candidate universe, with IN/OUT selecting positive qrels.
Curator staging must reuse the original split assignment and project only permitted
dev TA queries. Existing TAC passage vectors may be reusable only after exact
construction/order/model binding. Native semantic parity is not reproduction of a
published baseline with different embeddings/chunking. No query/vector/data file
was opened to establish this code-level finding.

Next: record owner's exact answers once; prepare runnable staging/container assets
within the accepted isolation model; declare CPU004; advance whichever benchmark's
actual inputs are ready. Do not repeat R0 or manufacture repeated dependency audits.
