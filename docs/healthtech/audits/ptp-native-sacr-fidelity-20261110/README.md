# Native SACR fidelity profile attempt

Status at this checkpoint: RUNNING, not a fidelity or retrieval result.
Container `ptp-native-sacr-fidelity-20261110-v1`, attached session51538.
Use the same handle or inspect the same container; never redispatch because a
status connection times out. The live aggregate observer is `status-v2.py` in
the remote job directory. It exposes no source text or query identifiers.

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

No terminal result or full-stage cost is claimed yet. Consult the newest
HANDOFF/INDEX-PLAN checkpoint for the latest observation.
