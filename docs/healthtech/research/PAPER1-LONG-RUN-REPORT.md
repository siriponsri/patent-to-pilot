# Paper1 bounded long-run report, 11 November2026

The authorized run produced a measured DAPFAM baseline and negative outcomes
for both SACR rounds and both S/G configurations. It did not establish an
improved retrieval method. Failed prerequisite gates legitimately prevented the
conditional pilot, full dev and MTM stages; these stages are NOT_RUN, not passed.

## Outcomes and completion audit

| Requirement | Outcome | Evidence |
|---|---|---|
| Native dev preparation, isolation and baseline | PASS execution; OUT Recall@200=0.14772, nDCG@10=0.02328 over349 eligible queries | [Native baseline](../audits/ptp-native-dense-preparation-20261110/README.md) |
| SACR R1 | STOPPED:21 flagged queries exceed20;56 normal returns,2 interrupted,42 never started of100 | [Continuation](../audits/ptp-sacr-unstarted-continuation-20261111/) |
| SACR fixes and R2 | Engineering fixtures passed; actual single synthetic profile failed source-backed condition validation | [R2 smoke](../audits/ptp-sacr-r2-synthetic-smoke-20261111/) |
| S/G R1 | FAIL:6 records/5 of100 families,0 cross-family candidate pairs | [R1 extraction](../audits/ptp-sg-feasibility-20261110/README.md) |
| S/G R2 | FAIL:29 records/14 of same100 families,0 cross-family pairs | [R2 extraction](../audits/ptp-sg-feasibility-r2-20261111/) |
| Human fidelity | NOT_RUN: gates stopped configurations before issuing cards;0/60 used, no semantic certification | [Frozen policy](plans/SACR-SOLO-FIDELITY-FREEZE.md) |
| Pilot and full dev comparisons | NOT_RUN: no new method passed required gates; unavailable effects are not zero effects | [Manuscript](PAPER1-MANUSCRIPT-DRAFT.md) |
| MTM | NOT_ACTIVATED: DAPFAM fidelity/pilot conditions unmet; conditional card transfer unused | [Handoff](../../../HANDOFF.md) |
| Neo4j | Connection verified previously by authenticated RETURN1; no graph import or graph-quality evidence | Failed S/G gates above |
| Paper53 alignment | Implemented descriptive exposure from existing sealed B0 metrics; paired effect analysis unavailable | [Exposure](../audits/ptp-native-exposure-20261111/README.md) |
| Apples-to-apples literature task | Protocol/source matrix and measured metric bridge complete; direct published replication NOT_ESTABLISHED | [Comparison supplement](plans/DAPFAM-PAPER-COMPARABILITY.md) |
| Report and draft | Negative findings, costs, limits and evidence retained; not submission-ready | This report and manuscript |
| Paper2/3, adaptive work | Plans only, not activated | MASTER-PLAN and Paper plans |

The baseline used474 dev queries,45,336 families and188,944 existing passages.
No corpus re-encoding or training occurred. The OUT exposure aggregate shows
136/349 queries with at least one known positive by200, and213 without one;
this query coverage is different from mean Recall@200. No paired comparison
or significance claim can be inferred from this baseline-only analysis.

## Resources and failures

The cumulative ledger charges9006.484789591283 GPU seconds and8727.597964742686
fidelity seconds, leaving250193.51521040872 and20072.402035257313 seconds.
Known model calls are at least59; two interrupted R1 attempts leave execution
and token counts incomplete. Full supervisor intervals remain charged. R2 smoke
used163.330 seconds whole time,1096 input/1083 output tokens and16,917,964,800
bytes peak allocated GPU memory. Normal process exit did not imply acceptance.

S/G R1/R2 consumed1.797/1.485 seconds CPU wall time respectively, with no model
or GPU calls. The additional exposure aggregation used0.575 seconds whole time,
1CPU/512MiB limits, zero model/GPU calls, and a1MiB disk reservation. Its peak
memory was not measured. Nine recall aggregates match the original receipt.
The existing conservative storage accounting is approximately11.23GB plus later
explicit reservations, below40GiB; it is not an exact current disk inventory.
See the [append-only cost records](../audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json)
for individual scopes, failed attempts and reservations. Limits are not measured
peaks. Unknown costs are never silently assigned zero.

## Boundaries and next decision

Both protected tests remain closed. No paid API, new model training, corpus
re-encoding or system-permission change was used. Existing failures and raw
private evidence remain preserved; public artifacts contain only screened code,
documents and aggregate evidence. Credentials and source records are excluded.
There is no active GPU job and no required human card decision for these stopped
configurations. Remaining resource allowance does not reopen failed gates.

Any future methodological revision needs a separately defined configuration,
prospective sampling/fidelity policy and budget decision. This report closes
the authorized bounded attempt; it does not claim the scientific hypotheses
were resolved or that a publishable improvement was found. Protected-test
evaluation and submission remain separate decisions.
