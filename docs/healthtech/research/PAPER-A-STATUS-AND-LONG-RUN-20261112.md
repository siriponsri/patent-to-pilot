# Paper A status and proposed long run — 12 November 2026

Naming assumption: Paper A refers to the current Paper1 / HT-ST1 DAPFAM study.
The repository does not establish a separate formal Paper A identifier. This
report uses that mapping and does not rename the study or activate a goal.

R6 is complete as bounded execution and stopped-branch reporting. Paper completion
is not established: only B0 has measured retrieval results. R7 remains proposed,
with one combined owner decision already requested and still pending.

## Verified progress

| Area | Evidence state | What it establishes |
|---|---|---|
| B0 |474 dev queries; eligible OUT349 Recall@200 .14772;213/349 expose no known positive in top200 | Measured baseline, not a new-method comparison |
| Runtime | Frozen R6 qualification256 tests and actual24-call calibration | Execution and evidence trail work; evaluator qualification failed |
| Evaluator |23 contract-invalid plus one valid semantic grading failure | R6 candidate closed; no automatic semantic retry |
| Graph corpus |45,336 families;23,037 records;13,736 keys;18,326 pair-key incidences | Candidate structures, not accepted semantic relations |
| Graph compact v2 |29 authored tests; actual100/114 input-admitted,14 retained risks | Technical admission only; all14 source units and86 aliases fit |
| Fidelity/retrieval | No accepted SACR/S/G comparison; no human cards | Native fidelity and new-method effect remain unestablished |
| Writing | Current report, coherent working manuscript, Paper53/DAPFAM supplement | Evidence-backed development draft, not submission-ready |

## Work still needed for the intended method paper

1. Complete compact-v2 runtime integration: exact message/schema/output binding,
   initial14 Graph risks within the fixed114 cohort, and an explicit authorized
   new-candidate transition in the existing journal. Helper tests do not replace
   actual worker/controller qualification.
2. Qualify the proposed critic once on the unchanged24 authored cases. Preserve
   exposure history and zero-error gate. A failure ends that candidate.
3. Pass synthetic and native fidelity gates for each feasible branch. Preserve
   the fixed100 SACR queries and Graph source/alias populations. Obtain actual
   owner decisions for the required risk/sentinel cards, at most60 total.
4. Run pilot20 and then full dev474 only for passing branches, reusing caches and
   existing corpus vectors. Baseline-only outputs cannot substitute for this.
5. Produce paired dev results, controls, uncertainty, exposure/win-loss diagnostics,
   coverage, failure rates and full costs. Primary OUT Recall@200 remains fixed;
   descriptive nDCG@10 and other existing metrics are not new tuned endpoints.
6. Finish the manuscript around the evidence that survives. S/G are equivalent
   implementation controls under the current same-information/same-scoring
   protocol. Compare structured augmentation and SACR against B0/declared controls;
   do not retain a superseded claim that G must outperform identical S.
7. Any protected-test evaluation or actual submission is a separate owner decision.
   MTM, Neo4j import and a wider model search are not required by proposed R7.

## Recommended long run

Use [R7 single-candidate continuation](plans/R7-SINGLE-CANDIDATE-CONTINUATION.md),
with the following sequence and stop conditions:

| Step | Maximum | Gate / next action |
|---|---|---|
| Local integration and qualification |3600 additional CPU seconds inside remaining allowance | Freeze exact runnable package; no hidden model calls |
| One critic calibration |24 calls /2h | Any contract/semantic failure closes candidate |
| SACR synthetic |≤6 calls /1h under existing conditional engineering-repair rule | No method-quality reroll |
| Native SACR5, then95 |15+285 calls /2h+30h | Same fixed sample; no regeneration |
| Graph screening |≤100 calls /12h | Keep14 initial technical risks; seventh further risk stops at21 |
| Human review |SACR30+Graph30,60 total | All required judgments; critical sentinel error stops configuration |
| Pilot20 |≤2h GPU | Measured quality/integrity/resource gates |
| Full dev474 and analysis |≤128h GPU | Passing arms only, mandatory cache reuse |
| Report and manuscript |No claim of benefit before measurement | Measured comparison or precise stopped-branch outcome |

GPU ceiling177h, fidelity47h and full-dev128h are inclusive within original
limits, not additional independent budgets. No ledger reset. Existing remaining
cumulative GPU677141.386495s (~188.09h), fidelity216620.273320s (~60.17h), and
conservative CPU-only3724.907748s (~62.08min) are checkpoint balances, subject to
fresh admission. Keep one GPU job, CPU≤8 threads, aggregate RAM≤32GiB and disk≤40GiB.
No paid API, training, corpus re-encoding, protected test or Neo4j writes.

These are ceilings, not a completion-date forecast. The next useful estimate
comes from native5 and pilot measurements. Failure at calibration can end the
run early; passing branches may need substantial runtime plus owner-review time.

## One remaining authorization boundary

The pending R7 decision must explicitly permit a new candidate after R6's valid
semantic calibration failure. Ordinary engineering-repair authority does not
supersede that stop. Accepting the proposed long run does not grant automatic
human fidelity decisions or protected-test/submission authority. No new goal,
model call or resource reservation was started for this status request.

Evidence: [R6 completion audit](../audits/ptp-r6-calibration-20261111/COMPLETION-AUDIT.md),
[Graph input receipt](../audits/ptp-sg-compact-v2-preparation-20261111/summary.json),
[working manuscript](PAPER1-MANUSCRIPT-DRAFT.md),
[comparability supplement](plans/DAPFAM-PAPER-COMPARABILITY.md).
