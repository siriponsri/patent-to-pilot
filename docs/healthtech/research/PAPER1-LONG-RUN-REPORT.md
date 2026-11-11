# Paper1 bounded long-run report, 11 November2026

## Current R5 execution checkpoint, 11 November 2026

The owner approved the bounded R5 long run and limited replacement policy. Earlier planning and closeout sections below are historical; they do not describe current permissions or running jobs.

SACR synthetic candidate 1 completed three calls in 170.946 seconds whole wall time (2,745 input / 1,442 output tokens; peak allocated GPU memory 17,323,849,216 bytes). It did not pass: the critic envelope used incorrect literal-quote key names, while independent inspection also found missing source mechanism/constraint coverage and lost quantity units. The malformed critic's labels are not validated semantic findings. This candidate is closed; native SACR, pilot and full-dev comparisons remain NOT_RUN. These are construction and acceptance failures, not measured negative retrieval effects. No native query was regenerated.

Graph fixed-source attachment completed 100 families in 2.245 seconds CPU wall time, preserving the original source text privately. Exact critic contract/tokenizer preflight passed 4/4 authored cases in 18.327 seconds; 28 targeted local fixtures passed. Graph screening is RUNNING in `ptp-sg-r5-screening-20261111-v1`, with fixed source100 followed by alias100, at most 200 calls and 16 hours reserved inside existing cumulative limits. Essential source omissions remain risks even outside the extractor's cue vocabulary. Risk 21 stops the configuration; only complete screening with at most 20 risks can produce the frozen 5-source + 5-alias sentinel selection and risk cards. Human judgments remain required. Cards issued and accepted edges remain zero.

Before Graph settlement, cumulative charged GPU time is 9,696.709 seconds and fidelity time is 9,417.822 seconds; the separate Graph reservation is 57,600 seconds in each budget, not a completed charge. Historical unknown attempts remain unknown. Caps are GPU192h/fidelity64h/full-dev128h, with the latter two inside GPU; no ledger reset. Canonical evidence: `docs/healthtech/audits/ptp-r5-execution-20261111/` and the cumulative resource ledger. Both benchmark tests remain closed; no Neo4j writes or new retrieval comparison has occurred. Existing native baseline and literature comparability limitations remain unchanged.

## R5 engineering qualification, 11 November 2026

R5 CPU engineering complete:86 local tests PASS; pinned character33+7numeric cases PASS; real tokenizer/callback/EOS35/35 PASS276.912s, exact original synthetic source1/1 PASS50.434s,input1557. Confirmed integer-bound omission and fused string-boundary token10465 omission; original R4 cause remainsUNKNOWN. Broad boundary adaptersv1/v2 stopped for cost and retained. Private bounded diagnostics preserve first failure and avoid normal-path GPU scalar copies; independent read-only review found no remaining blocker. All6ownedCPUcontainers terminal/PID0, no new model/GPU/fidelitygeneration/cards/retrieval. Graph integrity PASS100source families(86empty,29records),100alias units,215unique records; fullsource attachment code6fixturesPASS, corpus execution NOT_RUN. Cumulative GPU/fidelity charges unchanged; CPU costs in canonical audit ptp-r5-diagnosis-20261111/summary.json. Frozen smoke-proposal.json and R5-BOUNDED-LONG-RUN.md await combined goal/model/source/evaluator and bounded repair-policy approval; GPU192/fidelity64/fulldev128,60cards unchanged. Existing screened-publication permission retained, no duplicate approval requested; current changes local/uncommitted/unpushed, main/baseac48e02. Parent sole writer. Next: obtain2combined decisions; reserve/rebind ledger without method changes; dispatch one qualified smoke; proceed only through declared integrity/fidelity/human/resource gates. No native retry or test opening.


## Verified R4 closeout, 11 November 2026

R4 authorized first stage is terminal. CPU replacement v2 PASS: six positive grammar fixtures and tokenizer admission, 12.341282328 seconds, no model/GPU calls. Positive fixtures do not establish complete live grammar correctness or semantic fidelity.

The subsequent authorized synthetic smoke FAILED with InputBoundaryError in the unsettled profile attempt. Whole wall time 198.974029466 seconds was charged once to GPU and fidelity; the 1800-second reservation was released. No generation.json or detailed exception message was retained. Model calls/tokens and exact failure location remain UNKNOWN; no normal-return events were recorded. This is not evidence of normal EOS rejection or semantic failure. Generic, critic, native fidelity, pilot and full dev remain NOT_RUN. No retry is authorized.

Graph materialization completed 45,336 families, reproducing census counts: 23,037 records and 18,326 pair-key incidences (not unique pairs). Whole CPU time 26.376899449 seconds; output 63,574,824 bytes. Fixed source100 and alias-pair100 hashes are retained in the audit. Samples remain unscreened; accepted edges and issued cards are zero. No Neo4j writes or protected-test access occurred.

Next: add prospective bounded private failure telemetry and CPU negative grammar qualification, then prepare a concrete new-attempt proposal. Preserve all failed artifacts and cumulative costs. Budget caps remain GPU192h/fidelity64h/full-dev128h, with fidelity/full dev inside GPU192h. Additional budget does not authorize additional experiments. Current canonical receipts: docs/healthtech/audits/ptp-r4-preparation-20261111/smoke-result/aggregate.json and the cumulative resource ledger. Parent is sole writer; changes remain local/uncommitted, last verified base ac48e02.

## Previous planning and evidence (historical status)

## R3 continuation: corpus linkage census

The owner subsequently authorized a separate full-corpus signature census with
the unchanged R2 extractor. The first launcher failed before container creation
and processed0rows (0.009424s); an explicitly approved replacement completed all
45,336families in25.316453s whole supervisor time, with0model/GPU calls. Both
attempts remain in the cumulative ledger.

The census found23,037records,13,736keys and951keys shared by multiple families.
It counted18,326cross-family pair-key incidences, with at most69families/key and
no hubs above the predeclared100-family threshold. Incidences are not unique
family pairs. The frozen counter did not record the number of nonempty families.
These results establish linkage opportunities under this extractor, not
source/alias compatibility, accepted graph edges or retrieval improvement.
The earlier zero-pair100-family samples cannot be generalized to the full corpus.
Evidence: [census aggregate](../audits/ptp-r3-packaging-v2-20261111/census-result/aggregate.json).

R3 SACR synthetic smoke ended with one normal-EOS profile rejected by the frozen
compiler: quantity/unit roles pointed outside their declared relation evidence.
Replay of the unchanged validator reproduced the rejection; no output was repaired.
The two blocks each used16single-token evidence references, but their role
assertions included source positions outside those selections. Generic and critic
stages were NOT_RUN. This is a profile acceptance failure, not retrieval evidence.
The attempt used2387input/3395output tokens,320.304073s whole supervisor time and
18,331,955,712bytes peak allocated GPU memory. Whole wall was charged once to both
GPU and fidelity budgets. Evidence: [smoke aggregate](../audits/ptp-r3-packaging-v2-20261111/smoke-result/aggregate.json).
Both R3 first-stage authorizations are consumed; no further retry is allowed.
The prior bounded-round results below remain unchanged historical evidence.

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
