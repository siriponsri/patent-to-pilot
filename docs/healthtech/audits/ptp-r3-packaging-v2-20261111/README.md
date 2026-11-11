# R3 controller packaging replacement

Current status: APPROVED_AND_SETTLED. The owner approved the replacement in
call_12d552cdf34f41599caeed36e2ae3239. Census completed all45,336families with18,326
pair-key incidences; smoke failed profile acceptance after one normal-EOS call.
See census-result/aggregate.json and smoke-result/aggregate.json. No further retry.
The prospective preparation text below is historical and does not override these
settled outcomes. This package changed the controller, not the method.

## Observed failure

The approved census v1 invocation failed at Docker create before a container was
created or any corpus row processed. Its terminal receipt records
0.009423678740859032 supervisor seconds; zero model/GPU use. All staged inputs,
declarations and failed evidence remain in place. No retry was performed.
SACR smoke v1 was held before invocation because it shares the launcher defect.

The inherited RLIMIT_AS restricted the Go Docker CLI's virtual address reservation.
Read-only Docker version probes failed at 512MiB and 1GiB; setting GOMAXPROCS=1
did not fix it. These are controller failures, not extraction/fidelity failures or
evidence that actual resident memory exhausted the approved RAM cap.
See [diagnosis](../ptp-r3-preexecution-20261111/launcher-failure-diagnosis.json).

## Concrete repair and verification

The new controller uses Python standard-library HTTP over the existing local
Docker socket. No new rights, network listener, package or database change is
required. The socket is never mounted into either research container. It uses
[Docker Engine API 1.47](https://docs.docker.com/reference/api/engine/version/v1.47/)
with bounded replies and timeouts, exact container isolation readback, polling,
stop/kill/reobservation and durable terminal receipts including pre-create errors.
The original controllers and frozen declarations are preserved.

- 12 CPU fixture tests PASS: API bounds/version, readback, forbidden extra mount,
  pre-start mismatch, normal termination, timeout and unknown/lost-stop handling.
- Four new files parse successfully.
- Both worker files are byte-equivalent to v1 after replacing only the run ID.
- Read-only live Engine version probe PASS under 512MiB RLIMIT_AS; measured
  peak RSS18,821,120bytes, wall0.010943097062408924s. Engine29.8.2 advertises
  API1.40 through1.56, covering selected1.47.
- Actual container creation/start/isolation with the revised controller is
  NOT_RUN. Fixtures and a read-only connection do not establish runtime success.

The [freeze receipt](freeze-receipt.json) binds both revised declarations.
Approval requested: one replacement census attempt plus the still-unused smoke
under corrected packaging. Same model/extractor/prompts/decoder and resource
caps; sequential jobs; at most3 model calls and1800s GPU/fidelity reserved from
the existing ledger. Combined added disk remains1GiB including retained failed
staging, replacement staging, transport and results. No reset, further retry,
cards, tests, Neo4j write, native generation or retrieval authorization.

## Resume

1. Read owner reply and persist a separate APPROVED receipt binding the two
   declaration hashes. Elapsed time is not consent.
2. Refresh source pins, ledger, disk, job names and GPU occupancy. Stage into new
   v2 job paths; do not overwrite v1. Validate transport/corpus hashes.
3. Run census once, settle its terminal state/cost, then smoke once. If state is
   unknown, stop dependent work and do not redispatch.
4. Preserve all outputs and failures; charge actual GPU/fidelity whole wall once,
   retain unknown call counts where appropriate, release only settled reservation.
5. Report engineering, source fidelity, graph linkage and retrieval separately.
   Continue only under the remaining gates and scope.
