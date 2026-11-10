# Owner decisions — 10 November 2026

Source: explicit reply to the three consolidated chat questions. Applies prospectively.

1. Owner approved the entire bounded plan: CPU004 once120s+5s; if it passes, new
generation smoke once<=30min; baseline<=4h/benchmark; fidelity generation<=8h combined;
pilot20 deterministic dev queries/benchmark<=2h combined; full dev<=48h combined after
integrity/fidelity/resource gates. GPU<=72h cumulative this continuation, one job;
CPU<=8 threads, RAM<=32GiB, incremental disk<=40GiB combined (not a reset of existing
disk use), within existing V100 window. No automatic retries, paid services or test.

2. Owner accepted the solo isolation workflow and explicit limitation: owner-curator
runs mixed-source preparation separately; Codex may create temporary runtime and
dev-evaluator containers using existing Docker, no network, read-only allowlisted
mounts, no protected inputs/whole-job-root/Docker socket mounts or ACL/system changes.
Host-side orchestrator access remains; do not claim physically agent-blind evaluation.

3. Owner accepted the prospective failure policy: verified normally terminated unusable
families are rejected with full evidence/costs; retain independent valid anchor/compact;
no repair/refill. Infrastructure/unknown state and semantic ambiguity remain stopped.
Implementation is still pending; old FAILED receipts stay immutable.

Owner did NOT accept the proposed full manual fidelity workload as written. Instead,
requested an automation-first solo proposal, fixed sample/criteria before retrieval,
only genuinely necessary human judgments and explicit limitations. Independent work
must continue meanwhile. The existing human gate is not silently replaced or marked
passed; prepare the new concrete policy before generation/retrieval outcomes. Inclusion
of the extra source-anchor control was not separately confirmed in the free-text reply;
retain it as a prospective design item, not an adopted result or frozen test system.

The control-plane goal service still reports BLOCKED and has no exposed resume action;
this does not revoke the explicit owner work order. Continue in this same goal context,
never fabricate an ACTIVE service response or create a replacement goal.

## Fidelity follow-up adoption

Owner accepted automation-first screening with bounded escalations/sentinels, then explicitly required fixed sampling/pass-fail before retrieval and a total card cap covering both benchmarks and all configurations. Adopted policy: SACR_SOLO_FIDELITY_PROPOSAL_20261110_EN.md; maximum60 cards globally,30/benchmark across ALL configurations, category limits20 escalations+10 sentinels/benchmark. Critical unflagged-sentinel errors stop/review the configuration; no immediate PASS. Zero dev samples/cards/ratings yet. Work on other ready branches continues.

Owner also explicitly authorized opening a new goal. create_goal was attempted and rejected by the goal service because the old goal is unfinished; no replacement was created and old goal was not falsely marked complete.
