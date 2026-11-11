# Requested cumulative budget expansion, 11 November 2026

## Verified R4 closeout, 11 November 2026

R4 authorized first stage is terminal. CPU replacement v2 PASS: six positive grammar fixtures and tokenizer admission, 12.341282328 seconds, no model/GPU calls. Positive fixtures do not establish complete live grammar correctness or semantic fidelity.

The subsequent authorized synthetic smoke FAILED with InputBoundaryError in the unsettled profile attempt. Whole wall time 198.974029466 seconds was charged once to GPU and fidelity; the 1800-second reservation was released. No generation.json or detailed exception message was retained. Model calls/tokens and exact failure location remain UNKNOWN; no normal-return events were recorded. This is not evidence of normal EOS rejection or semantic failure. Generic, critic, native fidelity, pilot and full dev remain NOT_RUN. No retry is authorized.

Graph materialization completed 45,336 families, reproducing census counts: 23,037 records and 18,326 pair-key incidences (not unique pairs). Whole CPU time 26.376899449 seconds; output 63,574,824 bytes. Fixed source100 and alias-pair100 hashes are retained in the audit. Samples remain unscreened; accepted edges and issued cards are zero. No Neo4j writes or protected-test access occurred.

Next: add prospective bounded private failure telemetry and CPU negative grammar qualification, then prepare a concrete new-attempt proposal. Preserve all failed artifacts and cumulative costs. Budget caps remain GPU192h/fidelity64h/full-dev128h, with fidelity/full dev inside GPU192h. Additional budget does not authorize additional experiments. Current canonical receipts: docs/healthtech/audits/ptp-r4-preparation-20261111/smoke-result/aggregate.json and the cumulative resource ledger. Parent is sole writer; changes remain local/uncommitted, last verified base ac48e02.

## Previous planning and evidence (historical status)

Current status: APPROVED by owner reply call_c4ec345a29784975ab45f71412715d87.
Ledger ceilings were amended without changing prior charges. The proposal and
estimation assumptions below are retained. Current first-stage execution status:
Graph artifacts complete; CPU preflight failed before grammar/model due missing
writable temporary space; corrected CPU replacement awaits one-time exception.

## Verified current usage

Authoritative resource ledger: GPU9,326.788862183224s (2.5908h) used of72h;
fidelity9,047.902037334628s (2.5133h) used of8h. Remaining GPU69.4092h and
fidelity5.4867h. Known model calls60 are a lower bound; two prior interrupted
attempts retain unknown counts. Their supervisor wall charges remain included.
Human cards0/60, SACR30 + SG30. No reset or refund of historical costs.

## Why the old fidelity cap is insufficient for the conservative scenario

The completed R3 profile took320.304073s whole supervisor time for one call;
261.621883s was generation. It is one failed synthetic profile, not a reliable
distribution or timing guarantee for the changed R4 pipeline. Use whole time
as a deliberately conservative per-call planning scenario, including repeated
loading overhead rather than assuming it disappears.

| Planning cohort | Maximum planned calls | Scenario wall |
|---|---:|---:|
| Fixed100 SACR fidelity queries, profile/generic/critic | 300 | 26.69h |
| Graph source100 plus alias-pair100 screening, at most one critic/unit | 200 | 17.79h |
| Remaining374 dev queries, at most three calls/query | 1122 | 99.83h |
| One complete synthetic smoke | 3 | 0.27h |

The first two alone total44.49h, versus5.49h remaining fidelity. Adding25%
planning margin yields55.61h, plus prior2.51h =58.12h cumulative fidelity.
All1625 planned calls total144.58h;25% margin plus prior2.59h is183.32h GPU.
This scenario overcharges load overhead but may still underpredict difficult
outputs. It is not a statistical upper confidence bound or a reservation.
Actual R4 smoke and runtime admission remain mandatory; strict timeouts apply.

## Requested ceilings

- Cumulative GPU:192h, replacing72h (includes all already charged time).
- Cumulative fidelity generation/screening:64h, replacing8h, inside GPU192h.
- Full-dev stage:128h, replacing48h, also inside GPU192h; not an additive grant.
- Synthetic smoke remains one run,3calls/1800s including cleanup. No retries.
- CPU<=8threads, RAM<=32GiB, one GPU job, added disk<=40GiB cumulative unchanged.
- Cards<=60 cumulative, SACR30/SG30, risk20+sentinel10 unchanged.

Pilot keeps20 dev queries/benchmark and2h combined retrieval cap; existing native
B0 is reused. There is no train/reencode/test/paid-API/new-system-rights authority.
The new budget is a ceiling, not a target to exhaust. Stages stop when failed or
not scientifically justified, even when time remains. No unbounded configuration
search or automatic retry. Any individual stage must fit both its sub-cap and
the remaining cumulative GPU/fidelity cap; never double-allocate them.

## Combined execution decision

Ask together with the R4-SACR-GRAPH-ROUND first-stage package: CPU grammar/tokenizer
preflight, one new synthetic bundle, and one bounded deterministic Graph artifact
plus fixed sample preparation. Preserve no-retry and freeze exact code/input/
config hashes before execution. Graph worker and isolation checks must pass before
its dispatch; a budget approval does not waive engineering readiness.

Budget expansion alone does not certify or silently authorize an unspecified
native/fidelity/pilot/full-dev configuration. Those exact admission manifests
must describe all controls, selected cohorts and scoring before running. Human
sentinel judgments remain an owner action. Database writes, corpus-wide LLM
extraction, publication and protected-test opening remain excluded. Prepare any
remaining execution permissions as one package after measured first-stage gates,
rather than asking separately for every routine command.
