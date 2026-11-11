# Prospective R4 SACR and Graph round

## Verified R4 closeout, 11 November 2026

R4 authorized first stage is terminal. CPU replacement v2 PASS: six positive grammar fixtures and tokenizer admission, 12.341282328 seconds, no model/GPU calls. Positive fixtures do not establish complete live grammar correctness or semantic fidelity.

The subsequent authorized synthetic smoke FAILED with InputBoundaryError in the unsettled profile attempt. Whole wall time 198.974029466 seconds was charged once to GPU and fidelity; the 1800-second reservation was released. No generation.json or detailed exception message was retained. Model calls/tokens and exact failure location remain UNKNOWN; no normal-return events were recorded. This is not evidence of normal EOS rejection or semantic failure. Generic, critic, native fidelity, pilot and full dev remain NOT_RUN. No retry is authorized.

Graph materialization completed 45,336 families, reproducing census counts: 23,037 records and 18,326 pair-key incidences (not unique pairs). Whole CPU time 26.376899449 seconds; output 63,574,824 bytes. Fixed source100 and alias-pair100 hashes are retained in the audit. Samples remain unscreened; accepted edges and issued cards are zero. No Neo4j writes or protected-test access occurred.

Next: add prospective bounded private failure telemetry and CPU negative grammar qualification, then prepare a concrete new-attempt proposal. Preserve all failed artifacts and cumulative costs. Budget caps remain GPU192h/fidelity64h/full-dev128h, with fidelity/full dev inside GPU192h. Additional budget does not authorize additional experiments. Current canonical receipts: docs/healthtech/audits/ptp-r4-preparation-20261111/smoke-result/aggregate.json and the cumulative resource ledger. Parent is sole writer; changes remain local/uncommitted, last verified base ac48e02.

## Previous planning and evidence (historical status)

Current status: FIRST_STAGE_APPROVED_AND_PARTLY_EXECUTED. Owner approved the
budget expansion and first-stage package in call_c4ec345a29784975ab45f71412715d87.
Graph materialization completed all45,336families with census counts identical,
fixed100source and100alias-pair samples,26.376899s whole CPU time,63,574,824bytes
artifacts. These remain unscreened, with0accepted edges/cards/model calls.
CPU preflight failed before grammar qualification because no temporary directory
was writable. A separately frozen tmpfs repair awaits one-time replacement
approval; smoke has not started. Parent remains sole writer. Preserve old attempts.
The detailed prospective rules below remain applicable to unfinished stages.

## SACR diagnosis and repair

R3 completed one EOS response but selected16 individual-token context references
in each block. Its quantity40 and unitC roles lay outside those selections,
including outside their union. The strict validator correctly rejected it.
The evidence does not show that relaxing containment would be justified.

R4 preserves the R3 literal compiler, selective abstraction, source retention,
role/direction/condition/negation/quantity/unit critic and human-review gates.
Only proposal generation changes: select exactly one complete context interval
per block, from deterministic sentence, adjacent-sentence or full-source options.
Each branch of the grammar confines roles to that selected interval. There is
no automatic expansion or repair of model outputs. Cross-sentence condition
attachment remains an assertion requiring review, even if all literals match.

Sentence boundaries use token-final punctuation; decimal points inside tokens
do not split. Abbreviations may split, so a full-source option remains available.
More than16 detected units is an explicit input-limit stop, never truncation or
replacement. Schema branch bounds do not prove semantic role correctness.
The unchanged compiler still rejects reversed ranges and bad ordering/identity.

New modules: sacr_evidence_prompt_v4, sacr_generated_evidence_v4,
sacr_generated_critic_v4 and sacr_r4_bundle_runner. The runtime uses the corrected
Engine API controller. Old source files and failed generated output are unchanged.
The compact output shape is explained in the prompt; the repeated branch schema
is enforced by grammar and again after generation, without serializing its full
27,445characters into the synthetic prompt (5,272characters). Character counts
are not tokenizer measurements. Live grammar compatibility and token admission
still require CPU preflight before model dispatch.

21 authored CPU tests PASS across context selection and full mocked three-stage
orchestration. Initial20PASS/1FAIL exposed mutable schema aliasing; repaired by
independent evidence/role subtrees, without weakening the test. No live success
or fidelity claim follows from these fixtures.

## Graph path from census

The unchanged R2 extractor found951 multi-family keys and18,326 pair-key
incidences over45,336 families. Do not widen aliases or verbs based on outcomes.
Next prepare a private deterministic relation artifact with original source
locators, exact extractor/config/corpus hashes and bounded posting lists. This
new full-corpus materialization requires explicit authority despite the completed
count-only census. It must reproduce census aggregates; disagreement stops it.

Use the existing fixed100 source-family sample for source fidelity; retain its
exposure history and empty outputs. For new full-corpus candidate alias review,
canonicalize `(alias_key, smaller_family_id, larger_family_id)` as compact JSON,
sort by SHA256(`ptp-sg-r4-full-alias-v1-20261111|` + canonical JSON), tie by JSON,
and take the first min(100,N). These are pair-key units, not deduplicated by
retrieval outcome. Save selected IDs/hash before reading semantic judgments or
retrieval results. One card includes both endpoints and their source context.
For each family/key, choose the lexicographically smallest relation_id as the
fixed witness before selecting pair-key units. Preserve all extracted records
separately. A reviewed witness does not certify other records sharing that key;
subsequent S/G controls must use identical witness selection. This is a canonical
selection rule, not selection by relevance, semantic quality or retrieval score.

Source sample and alias sample are distinct units. Screen all selected units;
no substitution for failures. Preserve the shared SG pool of30 cards: every
unresolved risk case up to20, then10 sentinels (8 acceptable sources and2 acceptable
aliases under the existing SG sentinel salt/rules). If fewer aliases exist, use
the existing source-fill rule; fewer10 acceptable units or more20 risks stops.
A critical sentinel defect or missing judgment never passes. SACR retains30;
global60 across all configurations, no reset or automatic borrowing. No cards
are authorized for issuance by the first-stage request below.

S and G must share extraction, aliases, seeds, exclusions, scores, tie order and
family aggregation. One shared-key family-key-family traversal is equivalent to
posting lookup and must be reported as a parity control. Added graph novelty is
not assumed. Multi-hop/composed relations are not included in this round.

## Bounded approval package

Request one combined first-stage authorization for:

1. CPU-only tokenizer/grammar preflight, up to10minutes,CPU2/RAM2GiB, existing
   tokenizer and grammar dependencies, authored fixtures only, no model/GPU.
   If exact constrained grammar or token budget fails, no model run occurs.
2. One R4 synthetic full-bundle smoke, maximum3 calls and1800seconds including
   cleanup, existing Qwen3-8B/decoder/GPU,CPU8/RAM32GiB total,network off. Charge
   whole wall to both existing GPU and fidelity budgets. Same exposed synthetic
   requirement; this is engineering development, not independent validation.
3. One deterministic corpus relation/posting materialization with fixed source
   and alias sample manifests, CPU1/RAM2GiB/1800seconds, maximum45,336families,
   362,688relations and128MiB output. No model,query,qrels,test or database mounts.
   Code/supervisor tests and declaration hashes must be frozen and checked before
   this new worker runs; owner approval is conditional on those checks, not a waiver.

Run sequentially; one GPU job. Added disk reservation at most1GiB for this new
package within the original40GiB cumulative ceiling, counting transport and
retained outputs. No retry, output repair, model training, corpus reencoding,
paid API, protected test, Neo4j write, new installation/permissions or publication.
Keep prior costs and known60calls plus2unknown historical attempts.

Current ledger: GPU remaining249,873.21113781678s; fidelity19,752.09796266537s.
Reserve1800s for smoke only after approval, leaving17,952.09796266537s fidelity
before actual settlement. CPU/disk are additional accounted work, not a new cap.
Do not reserve the same remaining time independently for SACR and Graph.

## Subsequent gates, not silently authorized by this package

Native fidelity, human-card issuance, pilot/full dev and Neo4j imports remain
conditional future work. Their exact declarations are not yet defensible from
failed smoke data alone. After the above results, prepare one combined admission
decision with a cost estimate for the complete fixed cohorts and all controls.
Do not reduce100 SACR queries or omit generic/critic stages just to fit the budget.
R3 profile time alone (261.62s) would exceed the remaining fidelity budget over
100queries; R4 must be measured before any claim that the next cohort fits.

If a conservative complete-cohort forecast does not fit remaining fidelity time,
mark that branch BUDGET_INFEASIBLE and report it. Do not ask to raise the budget
unless the owner explicitly wants that alternative. If gates pass, preserve OUT
Recall200 primary plus nDCG, rescue, final200 loss/displacement, failures and full
costs; B0 remains reused. MTM/Paper2/Paper3 stay deferred.
