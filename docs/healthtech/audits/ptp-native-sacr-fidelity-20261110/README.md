# Native SACR fidelity profile attempt

Status: TIMEOUT / INCOMPLETE_PROFILE_COHORT_NO_PASS. Container
`ptp-native-sacr-fidelity-20261110-v1` exited137 at01:11:27 Bangkok on11 November2026;
OOMKilled was false. The SSH session51538 had already closed after connection
loss; the independent supervisor continued and enforced its original bound.
Never restart that attempt or reuse its output directory.

The supervisor interval was6966.460590522736 seconds, all charged once to both
the cumulative GPU ledger and shared fidelity budget. Of100 planned queries,
45 returned normally (42EOS,3OUTPUT_LIMIT),46 attempt directories exist,
one reserved attempt has unknown execution/token costs, and54 were not started.
The normal returns comprise33 structurally valid results awaiting semantic
review and12 rejected families. Known counts are45 model calls,41127 input
tokens and65098 output tokens; they are lower bounds because of the interrupted
attempt. Peak observed host cgroup usage was6973775872 bytes, not GPU memory.

The reviewed closeout used a fresh terminal Docker observation and revalidated
all normal-return records through the canonical binder. Terminal SHA256:
`b78281166cd0ce0021e96e745ade1e260cc45ab763cf7d1afbece37e8a805ec4`.
No semantic fidelity PASS, human cards, view/critic generation, pilot or new
retrieval score resulted. The frozen100-query sample remains unchanged.

## Authority, allocation and provenance

The owner approved up to8 hours of combined fidelity generation, within the
existing72-hour cumulative GPU allowance. The agent assigned this profile
stage a7200-second reservation, leaving21600 seconds initially unreserved for
generic/selective views and screening. **The2-hour stage allocation is an agent
operational choice, not an owner restriction or a scientific feasibility bound.**
The supervisor begins termination at6960 seconds to reserve240 seconds for
bounded observation and cleanup. No elapsed time or cost ledger is reset.

If this stage times out before100 queries, report an incomplete sample under
this chosen allocation. Do not infer that SACR cannot work, that the entire
8-hour budget was exhausted, or that the partial sample passed fidelity.
Preserve any interrupted attempt with unknown token/call costs separately
from normally returned rejected generations and genuinely unstarted queries.
Any continuation must respect the original sample, consumed attempts, no-retry
rule, remaining budget and infrastructure/fidelity gates; this receipt does
not itself authorize a restart or replacement generation.

The fixed sample, exact query bytes and per-query schema identities are bound
in the declaration. No qrels, corpus or protected tests are mounted. Actual
isolation readback verifies read-only code/dependencies/query inputs/model,
output and shared GPU lock as the only writable bind mounts, no network,
31GiB container memory plus1GiB supervisor allowance,8CPUs and one pinned GPU.

The original transferred supervisor is retained but was never launched.
Independent review found a cleanup gap and an insufficient termination margin.
The reviewed replacement `supervise-reviewed.py` was hash-verified and launched
once. Both findings were rechecked by the independent reviewer;11 supervisor
tests passed with4 tests skipped for historical supervisors lacking the new
lifecycle helper. Runtime/schema/critic/rejection fixtures passed16 tests.
These tests are engineering evidence, not actual-model semantic validation.

## Current evidence and closeout

- [Declaration](declaration.json): source/input/model/grammar pins and stage cap.
- [Transport receipt](transport.json): exact-byte archives, original and reviewed supervisor hashes.
- [Isolation readback](isolation-readback.json): observed configuration before start.
- [Fidelity protocol](../../research/plans/SACR-SOLO-FIDELITY-FREEZE.md): fixed sample, bundled cards, critical-error stop.
- [Resource ledger](../ptp-mtm-dapfam-resume-20261110/resource-ledger.json): cumulative charge and live reservation.

After verified termination, retain supervisor/runtime terminals and close out
with `scripts/healthtech/summarize_sacr_fidelity_attempt.py` using a freshly
captured Docker state. The aggregator refuses a live state or disagreement,
reports remaining queries, normal returns, assessments and unknown interrupted
execution, and charges the whole supervisor interval. Its byte/cost checks do
not substitute for external process observation or semantic adjudication.
Independent review identified incomplete duplicated generation checks in the
first closeout tool. The reviewed replacement uses the canonical generation
record binder with the original fixed limits before counting costs. Ten closeout
fixtures now cover interrupted reservations, preparation without a model
reservation, live-state refusal, tampering, impossible token/byte states and a
complete100-query cohort that still cannot claim semantic PASS. Together with
the canonical receipt suite,40 tests passed. The reviewer rechecked the repair.
See [closeout tool pin](closeout-tool.json); the earlier transferred helper is
retained, and only `summarize-reviewed.py` is intended for terminal accounting.

Terminal evidence: [supervisor](terminal.json), [fresh observed state](observed-terminal-state.json),
[aggregate closeout](aggregate-closeout.json). Remaining shared fidelity budget
is21833.539409477264 seconds (about6h03m54s); cumulative GPU charge is
7245.347415371332 seconds. Known cumulative generation calls are47 plus one
attempt with unknown call/token counts. There has been no automatic retry.
Preparing continuation for never-started queries does not authorize regenerating
the interrupted query or rerunning the45 completed queries. Consult the newest
HANDOFF/INDEX-PLAN checkpoint for the next contract and any owner decision.
