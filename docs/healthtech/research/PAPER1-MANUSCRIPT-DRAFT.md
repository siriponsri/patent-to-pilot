# Source-preserving query representations and relation extraction for cross-domain patent retrieval

## Current R6 outcome and Graph repair, 11 November 2026

R6 Phase0 engineering completed, but the actual evaluator candidate failed the
frozen24-case calibration. All24 calls ended with EOS:23 responses were schema-valid
but interpreter-invalid, and one valid response had unrelated semantic flags.
The candidate is closed; this is not a native SACR or Graph fidelity result.

| Evidence layer | Current status | Boundary |
|---|---|---|
| Runtime engineering | PASS for frozen R6 package | 256 local tests and authored CPU transport; actual calibration completed24 calls |
| Actual critic calibration | FAILED / candidate closed | 23 contract-invalid; one contract-valid semantic failure; unchanged gold |
| SACR native fidelity | NOT_RUN | Shared critic prerequisite failed; native method quality NOT_ASSESSED |
| Graph original R6 admission | CLOSED_INPUT_RISK_CAP | 33 technical risks/114, preserved unchanged |
| Graph compact v2 admission | INPUT_ADMISSION_ONLY | 100 admitted/114;13 input limits+1 catalogue limit; no model screening |
| Human review | NOT_RUN, zero cards issued | Actual owner judgments required; ceiling60 unchanged |
| New comparative retrieval | NOT_RUN | No improvement estimate; measured B0 remains separate |

Calibration used1748.397555 seconds whole occupancy, charged1749 GPU+fidelity
seconds once;24 calls,33,988 input/15,799 output tokens, peak allocated GPU
17,713,604,608 bytes. The prompt omitted an explicit prohibition on supported-
dimension findings, although its interpreter rejects them. Four invalid cases
also omit required flagged findings, and two include findings without references.
The independent valid semantic error remains even if the contract wording is fixed.
No responses were repaired, regraded into acceptance or regenerated.

Compact Graph v2 clarifies that existing rule and compresses redundant transport
metadata while retaining full source/artifact text, evidence IDs, schema and
criteria. Its first actual CPU inspection used16.324545 seconds whole wall and
14.728927 CPU seconds; worker peak RSS996,880,384 bytes under aggregate2GiB limit
(aggregate peak not measured). All14 source units and86 alias units fit; the14
remaining alias risks stay in the fixed114 denominator. All100 source coverage
rows and86 extraction abstentions remain. Passing input admission is not fidelity.

Evidence: [calibration closeout](../audits/ptp-r6-calibration-20261111/README.md)
and [Graph actual token admission](../audits/ptp-sg-compact-v2-preparation-20261111/summary.json).
No owned job remains live at this checkpoint. New model-candidate authorization
and qualification remain before further semantic screening. Prior negative
rounds below are historical; their cost balances are not current allowances.

## Study scope

Working development manuscript, updated11 November2026; not submission-ready.
The measured dense baseline is available. SACR/S/G comparative retrieval has not
passed the required gates. R6 evaluator calibration is closed with a valid
semantic failure and separate contract failures; compact Graph v2 has only
technical input-admission evidence. The proposed R7 model candidate awaits an
owner decision. Both protected tests remain closed. Historical rounds are
identified below and their original status notes are retained in the appendix.

## Abstract — provisional

We investigate source-preserving query representations and deterministic relation
extraction for cross-domain patent retrieval under a bounded development protocol.
A dense baseline reusing existing passage vectors achieves Recall@200 of0.14772
on349 eligible cross-domain development queries;213 expose no known positive
within200 ranks. Corpus-wide deterministic extraction produces23,037 records and
18,326 cross-family pair-key incidences, which remain unvalidated candidate links.
Earlier generation and screening configurations failed prerequisite gates. The
latest evaluator calibration also failed:23 of24 responses violated the response
contract, and the remaining response failed the frozen semantic grading criteria.
A compact Graph transport subsequently admitted100 of114 fixed screening units,
with14 technical risks retained; this is input-admission evidence, not semantic
validation. No SACR or S/G retrieval comparison passed the required gates. These
results establish a measured baseline and configuration-specific engineering and
feasibility findings, without demonstrating retrieval improvement or general
impossibility.

## 1. Motivation and research questions

Cross-domain patent retrieval seeks useful functional correspondences despite
different application terminology. Query abstraction may improve lexical or
semantic matching, but it can also remove conditions that distinguish the
technical requirement. Corpus relations may expose shared mechanisms, yet
extraction coverage and cross-record linkage must be demonstrated before
traversal can be evaluated.

The planned study asks whether a source-preserving query intervention improves
known-family recovery over a fixed dense anchor, and whether adding extracted information helps retrieval. In R6, direct
postings S and one-key traversal G use the same data and scorer and are
implementation-equivalence controls, not independent improvement claims: an extraction-empty configuration cannot provide a valid
test of traversal benefit. The intended B0/SACR/S/G panel is retained in the
protocol; unavailable arms must remain explicitly unavailable in reporting.

## 2. Data and evaluation contract

We use the existing 474-query development assignment and all 45,336 candidate
families. Query input is the exact native title-and-abstract text; candidate
passages derive from title, abstract and claims. The runtime receives no qrels.
A separate evaluator reads only the prepared development projection. The
restricted DAPFAM and MTM tests remain closed.

Positive qrels are interpreted by the pinned native adapter before applying
IN/OUT partition filters. Candidate search remains over the full corpus in all
partitions. Scores are query-macro averages over queries with at least one
known positive in that partition. Missing or empty eligible rankings score
zero; queries without partition positives are counted and excluded from that
partition's denominator. Known positives are binary, and nDCG ideals use all
known partition positives up to the cutoff. Incomplete judgments prevent
interpreting every unjudged candidate as a false positive.

The primary development endpoint is OUT Recall@200. nDCG@10 is a descriptive
bridge to supplied literature, not a new confirmatory endpoint. Historical
development exposure and shared-positive dependence limit independent
generalization claims. No feasible paired comparator exists for component-based effect uncertainty;
no confidence intervals or significance claims are supplied here.

## 3. Methods and fidelity controls

### 3.1 Dense anchor

B0 uses the existing PatEmbed-large fp32 passage vectors with 384-word windows
and 64-word overlap, query-only encoding, the established retrieval prefix,
and family MaxP aggregation. Global lexical family-ID tie ordering precedes
top-200 selection. The run binds 188,944 passage vectors to the existing corpus
and encoder identity. It does not construct new corpus embeddings.

### R6-specific evidence boundaries

Authored critic calibration tests response-contract compliance and agreement
with frozen semantic gold; it does not estimate native fidelity. The prospective SACR projection retains literal complete
source context; a compact view identical to its anchor reuses the same vector
and is reported as a duplicate control. Graph tests only retained claims with
their full family context. All100 source families remain in coverage reporting,
including86 extraction abstentions that are not fidelity passes. Its14 nonempty
source units and100 alias pairs were closed by input admission before model
screening. The newer compact transport is engineering work, not an accepted
Graph comparator. Earlier criteria and outcomes below retain their round scope.

### 3.2 Source-linked query method

The prospective SACR pipeline uses the existing local Qwen3-8B model with
greedy, non-thinking fp16/eager generation. Per-query JSON grammar binds the
query identity and exact source hash. Validation checks literal quote alignment,
source order and structural constraints; these checks do not establish semantic
fidelity. Normally completed unusable generations are retained and charged,
without repair or replacement calls. Infrastructure failures stop dependent
work. Independently valid anchors are not evidence that abstraction succeeded.

The fixed 100-query fidelity sample is selected by a published deterministic
hash rule. Complete query bundles undergo structural, lexical and local-model
screening before human cards or new SACR retrieval scores. At most 20 flagged
queries and exactly 10 hash-selected unflagged sentinels are reviewed. Any
critical error, including a false-negative sentinel, stops the configuration;
incomplete judgments cannot pass. This is automated screening plus limited
owner review, not independent expert validation. Same-model criticism may
share generation blind spots. See the frozen fidelity specification for the
full rule and cumulative 60-card allocation across SACR and S/G.

### 3.3 Fixed relation extraction configurations

The initial R1 extractor was declared before its output inspection. Its100-family
sample used25 hash-selected families from each of four corpus text-length rank
strata, without qrels or retrieval outcomes. R1 required explicit configured/
adapted/operable-to clauses and proposed exact whole-clause cross-record aliases.

The later retained R2 extractor uses semicolon-aware statement units and literal
action/operand keys with fixed normalization. Full source context is attached as
screening evidence; it is not silently included in the alias key. Shared keys
propose a shared positive technical function with separate witness conditions,
not device interchangeability. Neither configuration uses inferred synonyms or
LLM corpus extraction. Corpus census and materialization use the retained R2
extractor. Their candidate incidence counts are not semantically accepted links.

S and G use the same extracted information, scorer and candidate scope. Direct
postings and one-key graph traversal are implementation-equivalence controls.
No retrieval/storage benefit or graph novelty is established merely by choosing
one representation. Full-source screening and human gates remain prerequisites.

## 4. Results available at this checkpoint

### 4.1 Native dense development baseline

| Partition | Eligible queries | nDCG@10 | nDCG@100 | Recall@100 | Recall@200 |
|---|---:|---:|---:|---:|---:|
| ALL | 474 | 0.17239 | 0.20893 | 0.25222 | 0.34262 |
| IN | 450 | 0.20691 | 0.27972 | 0.39413 | 0.51370 |
| OUT | 349 | 0.02328 | 0.04490 | 0.09732 | 0.14772 |

There were no missing or empty rankings. The 24 IN-ineligible and 125
OUT-ineligible queries are excluded only from their respective metric
denominators. IN and OUT are overlapping eligible populations, not disjoint
subsets whose sizes should sum to 474.

### 4.2 Historical sample feasibility and later corpus census

Five of 100 sampled families yielded six records; 95 yielded none. Among 43
cue-bearing segments, 24 exceeded the configured length bound. No cross-family
exact-alias candidate pair was produced. The configuration failed its graph
feasibility gate and could not supply ten record-bearing sentinel cases.
At that initial checkpoint, no full-corpus extraction, structured index,
accepted graph edge or S/G retrieval comparison followed. Semantic fidelity was not assessed.
Zero sample alias candidates do not establish zero possible corpus links.

A separately declared R2 revision used semicolon-aware statement units and
literal action/operand candidate keys, preserving source context and allowing
only casefolding, whitespace and leading-article normalization. On the same
exposed100-family sample it produced29 records from14 families, but again zero
cross-family candidate pairs. Of159 explicit cue occurrences,17 were over length
and113 did not match the fixed action vocabulary/parser. The predeclared graph
feasibility gate therefore stopped R2 as well. The increased record coverage is
not a retrieval gain or an independent validation. At that R2 checkpoint, no accepted edges, full-corpus extraction, semantic
screening, human cards or S/G retrieval measurement followed.
The run took1.485 seconds of CPU wall time, wrote135639 private bytes and used
no model/GPU calls. No synonym widening or replacement sample was attempted.

A later separately authorized corpus-wide census and materialization processed
45,336 families with the retained extractor, producing23,037 records,13,736 keys
and18,326 cross-family pair-key incidences. Pair-key incidences are not unique
family pairs or validated relations. Materialization reproduced the census
counts, used26.376899 seconds of whole wall time in a CPU-only job and wrote
63,574,824 private bytes. The fixed
source100 and alias100 samples retained their hashes; the later full-context
attachment covers282 families. This later evidence supersedes only the earlier
absence of corpus-wide execution, not the failed sample gates or fidelity status.

### 4.3 Incomplete native query-generation run

The first profile stage used an agent-selected2-hour suballocation within the
owner-approved8-hour combined fidelity budget. It stopped at the declared
supervisor threshold after6966.461 seconds, without an OOM event. Of the fixed
100-query sample,45 returned normally, one reserved attempt was interrupted,
and54 were not started. The normal returns included42 EOS completions and
three output-limit returns;33 passed structural checks and12 were rejected.
Structural acceptance is not semantic fidelity. No query was regenerated and
the sample was not reduced to the completed subset.

This is an incomplete run under the chosen stage allocation, not evidence that
SACR is generally infeasible or that the full8-hour allowance was exhausted.
The interrupted attempt retains unknown token/call costs; all supervisor time
is charged. Any further work must preserve the fixed sample and failure history
and respect the remaining budget and prohibition on automatic retries.

### 4.4 Frozen review-cap stop and unavailable comparisons

The sealed continuation processed only previously unstarted entries. It added
11 normal EOS returns in 1597.807 seconds before the frozen gate stopped the
configuration. Across both intervals, 56 queries returned normally: 42 were
structurally pending fidelity and 14 were rejected. Two attempts were interrupted
with unknown execution counts, and 42 queries were never started. The fixed
100-query denominator remains unchanged. The separately approved single-query
regeneration exception was not used after the configuration became ineligible.

Fourteen rejected profiles and seven additional compact-view lexical flags
established 21 distinct flagged queries, above the prospectively fixed limit of
20 risk cards plus 10 sentinels. Later critic judgments cannot erase these flags.
The stop therefore applies the declared gate, without changing it using retrieval
outcomes. It does not establish 21 semantic errors or a negative retrieval effect.
No human cards, critic calls, pilot or SACR retrieval comparison were completed.

A retained-output audit reproduced all 56 structural assessments. Rejections
comprised nine absent/ambiguous quotations, one source-order violation, three
output-limit returns and one condition not backed by source text. Numeric or
polarity inventories flagged seven other queries. These are diagnostic categories,
not independently adjudicated semantic errors. A prospective renderer now unions
overlapping source occurrences while preserving distinct identical occurrences;
its 20 engineering tests do not demonstrate real-data fidelity or retrieval gain.

S/G retrieval effects remain unavailable after both declared extraction configurations
failed feasibility. Neither missing comparison is a zero treatment effect. New
round authority preserves prior failures and cumulative budgets. MTM has a
conditional unused-card transfer only after DAPFAM fidelity and pilot pass;
those conditions are unmet. No protected-test result exists.

### 4.5 Latest evaluator and input-admission outcomes

The current status table separates runtime qualification, evaluator calibration,
native fidelity and retrieval. Actual R6 calibration returned24 EOS responses.
All satisfy the JSON schema, but23 violate the interpreter contract. A missing
explicit prompt prohibition on supported-dimension findings is one engineering
gap; four responses also omit flagged findings and two include empty references.
The remaining valid response flags unrelated dimensions under the frozen gold.
That independent semantic grading failure closes the evaluator candidate. No
native SACR/Graph quality or retrieval effect can be inferred from this result.

Original R6 Graph admission stopped at33 technical risks/114. The separately
prepared compact v2 transport retains source/artifact characters, occurrence IDs,
schema, criteria and sample identities. It admits100/114 units:14 sources and86
aliases. Thirteen alias input limits and one catalogue limit remain in the fixed
denominator and risk pool. All86 extraction-empty source families remain
abstentions in the100-family coverage report, never fidelity passes. New semantic
screening requires a separately authorized, qualified evaluator candidate.

## 5. Cost, failures and reproducibility

At the latest R6 checkpoint, actual calibration occupied1748.397555 supervisor
seconds and was charged1749 GPU/fidelity seconds once. Its24 calls consumed33,988
input and15,799 output tokens, with peak allocated GPU memory17,713,604,608 bytes.
Graph compact v2 admission used16.324545 wall and14.728927 process CPU seconds;
worker peak RSS was996,880,384 bytes, not a measured aggregate-memory peak. It
made no model calls. All prior failures and unknown costs remain in the ledger;
per-call operation times are not added again to whole-stage charges.

### Additional R2 engineering outcome

A prospectively declared source-token-reference revision was tested once on an
authored synthetic valve requirement, without benchmark data. The existing
Qwen3-8B model returned a normal EOS profile (1096 input and 1083 output tokens),
but a condition's text was not backed by its selected source span. The profile
was rejected without repair or regeneration. Generic, selective and critic
stages were not dispatched, and native R2 fidelity/pilot/retrieval remain unrun.
This is a synthetic source-reference acceptance failure, not a retrieval result
or a general impossibility finding. Earlier CPU tokenization of the original
100 dev inputs passed its size limit (maximum2788/8192 tokens); that check did
not predict successful generation.

The failed smoke consumed163.330 seconds of whole supervisor time and102.543
seconds of generation time. Peak GPU allocated memory was16917964800 bytes;
this differs from the host-cgroup measures below. Its whole time is charged to
both GPU and fidelity budgets, bringing cumulative charges to9006.485 and
8727.598 seconds respectively. At that R2 checkpoint the fidelity allowance had20072.402 seconds remaining;
this historical balance is not the current allowance. Historical R1 figures below retain their original checkpoint scope.

The B0 supervisor interval was 40.455 seconds, including 5.829 seconds of query
encoding and 9.985 seconds of ranking. Peak sampled host cgroup usage was
1,960,681,472 bytes; this is not GPU memory. The first evaluator attempt failed
on an import before reading data (0.701 seconds). A separately preserved
dependency-mount repair completed evaluation in 7.978 seconds, with no GPU use.

The relation feasibility task used 1.797 seconds of wall time and wrote 54,639
private bytes, with no GPU/model calls or human cards. Its approximately0.047
seconds of in-memory extraction is too short and too narrow to support a
reliable full-corpus resource forecast. Do not extrapolate it into approval.

SACR engineering history includes a failed source-order smoke and one subsequent
authorized successful smoke. Their costs remain in the cumulative resource
ledger. The native profile intervals total 8564.268 seconds, bringing conservative
cumulative GPU time to 8843.155 seconds. Native generation recorded at least
56 calls, 51088 input tokens and 79724 output tokens; two interrupted attempts
have unknown counts. Peak sampled host cgroup usage was 6973775872 bytes for
the original interval and 4869136384 bytes for the continuation.
These figures neither assign zero cost to the interrupted attempt nor establish
its peak GPU memory. The full supervisor interval is included despite incomplete
generation. That historical remaining allowance was subsequently reduced by the R2 smoke;
the R2-checkpoint remainder was20072.402 seconds. Later rounds and approved
ceiling changes are recorded separately in the cumulative ledger.

Private source records, per-query outputs and qrels are not published. Public
reproducibility artifacts include code, source/configuration hashes, aggregate
receipts, failure states and the sampling protocol. All relevant model and
dataset rights require assessment before any wider artifact release.

## 6. Relation to the supplied papers

The supplied Paper53 motivates exposure-aware analysis and paired wins/losses
rather than a single average-effect headline. Its fixed-pool decomposition
cannot be applied unchanged to SACR acquisitions that alter candidate unions.
For changed pools, report exposure/rescue/loss strata and distinguish acquisition
from within-pool selection; do not label these diagnostic strata causal effects.

The DAPFAM papers use different cohorts, encoders, precision and passage/view
configurations. Our 474-query dev results are not apples-to-apples replications
of published all-query scores. The paired local comparison must hold the query
cohort, candidate universe, qrels, fields, encoder/index and metrics fixed.
Published values belong in a separately labeled context table, without direct
percentage-gain claims. The protocol comparison and source-page references are
maintained in DAPFAM-PAPER-COMPARABILITY.md; files01 and38 are byte-identical and
must not be counted as independent studies.

## Descriptive exposure of the existing baseline

These fixed coarse bins were declared before aggregation of the existing sealed
dev per-query metrics. They are not exact first-positive ranks. No retrieval was
rerun and no new method scores were inspected. All nine recomputed macro recall
values match the original published dev receipt.

| Partition | Eligible | First positive 1–10 | 11–100 | 101–200 | None at 200 |
|---|---:|---:|---:|---:|---:|
| ALL | 474 | 308 | 115 | 19 | 32 |
| IN | 450 | 299 | 110 | 21 | 20 |
| OUT | 349 | 37 | 67 | 32 | 213 |

The OUT baseline exposes at least one known positive for 136/349 queries at200;
213/349 expose none. This is distinct from macro Recall@200=0.14772. Unexposed
does not mean semantically irrelevant: judgments are incomplete. IN/OUT eligible
populations overlap. Paper53-inspired paired wins/losses, rescue and uncertainty
analyses are NOT_RUN because no comparator passed the prior gates.

The isolated aggregation used0.575023457 seconds whole supervisor time,1CPU,
512MiB memory limit,0GPU/model calls, no network and no protected-test mounts.
Peak memory was not measured. Four hand-computable validation fixtures passed.

## 7. Discussion, limitations and conclusion

The native baseline is executable, but cross-domain known-positive exposure is
limited. Neither source-preserving generation nor deterministic graph candidates
passed the declared prerequisites. The broader retrieval hypotheses therefore
remain unanswered; unavailable comparisons are not zero or negative effect sizes.
R2 engineering improvements and greater extraction coverage did not establish
semantic fidelity or downstream usefulness. Reusing the exposed sample also
prevents treating R2 as independent validation.

The earlier bounded round is closed with negative configurations preserved;
the subsequent R6 evaluator also failed calibration, while the owner-requested
compact Graph transport admitted100 of114 fixed units, retaining14 technical
risks; semantic screening has not run. R7 model approval is pending.
No human cards were issued, no independent expert review occurred, and no test
generalization, inventive-design success or product usefulness is established.
Pilot/full dev and conditional MTM were not dispatched because their gates failed.
Remaining budget does not justify retrying failed declarations. This is a draft
negative feasibility report, not a validated four-system comparison or a
submission-ready method paper. Submission and protected tests remain separate.

## Evidence links

- [Native baseline and evaluator receipt](../audits/ptp-native-dense-preparation-20261110/README.md)
- [Native aggregate metrics](../audits/ptp-native-dense-preparation-20261110/dev-metrics-v1.json)
- [S/G feasibility receipt](../audits/ptp-sg-feasibility-20261110/README.md)
- [S/G extraction result](../audits/ptp-sg-feasibility-20261110/extraction-result.json)
- [Solo fidelity freeze](plans/SACR-SOLO-FIDELITY-FREEZE.md)
- [Paper comparison protocol](plans/DAPFAM-PAPER-COMPARABILITY.md)
- [Cumulative resource ledger](../audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json)
- [Incomplete native SACR profile closeout](../audits/ptp-native-sacr-fidelity-20261110/aggregate-closeout.json)

- [R2 SACR failure](../audits/ptp-sacr-r2-synthetic-smoke-20261111/aggregate-closeout.json)
- [R2 S/G failure](../audits/ptp-sg-feasibility-r2-20261111/README.md)
- [Baseline exposure](../audits/ptp-native-exposure-20261111/README.md)


## Appendix A. Historical development checkpoint notes

These retained notes describe their original rounds, not current authority,
resource availability or runtime state. The main body and current evidence table
above supersede their present-tense wording.

## R6 Graph input-admission outcome, 11 November 2026

The approved R6 Graph configuration is **CLOSED_INPUT_RISK_CAP**, before any model
inference or retrieval. A single source-only pass attached the complete original
fields for the fixed282-family union (2,472,676 private output bytes; no new
extraction). Exact input admission covered14 nonempty source units and100 alias
units, while retaining all100 source-family coverage rows and86 abstentions.

Of114 screening units,81 were admitted and33 were technical input risks:1 source
and31 alias requests exceeded8,192 model tokens, and1 alias request exceeded the
256-unit evidence catalogue bound before token counting. Token counts among the
113 constructed requests ranged3,136–12,236. The predeclared risk cap was20, so
the configuration stopped without truncation, substitution, resampling or model
calls. Human cards issued0; accepted graph edges0; retrieval/pilot/full dev for
this configuration NOT_RUN. These outcomes do not establish semantic errors or
a negative retrieval effect of graph methods.

The actual CPU tokenizer/grammar qualifications separately passed14 profile and
38 critic authored cases. They qualify syntax/reference handling, not native
critic accuracy or fidelity. At that earlier checkpoint SACR was still active;
its later calibration failure and dependent stop are recorded above. R5 outcomes
are unchanged.

Evidence: `docs/healthtech/audits/ptp-r6-phase0-execution-20261111/`.


## R6 preparation addendum, 11 November 2026

Historical preparation checkpoint: three read-only agents reviewed evaluator correctness, scientific criteria and runtime integration; the initial53 local tests preceded owner approval. That pending-decision status is superseded by the approved R6 execution table above. R5 results are unchanged. See [R6 preparation and review](../audits/ptp-r6-preparation-20261111/README.md) and [proposed R6 goal](plans/R6-BOUNDED-LONG-RUN.md).

## R5 bounded-run closeout, 11 November 2026

The approved conditional run has reached its stopping gates. SACR candidate 1 and the Graph screening configuration did not qualify for native comparison. Consequently native SACR5/100, pilot20, full dev474 and conditional MTM are NOT_RUN. There is no new retrieval effect estimate, not a measured zero or negative effect. Both protected tests remain closed.

| Stage | Observed result | Time and resources |
|---|---|---|
| SACR synthetic candidate1 | Three EOS calls; critic envelope rejected; separately observed source-coverage and unit omissions; candidate closed | 170.946s whole wall; 2,745 input / 1,442 output tokens; peak allocated GPU17,323,849,216bytes |
| Graph fixed-source attachment | 100 original family texts attached privately; no re-extraction | 2.245s CPU wall |
| Graph exact-critic preflight | Four authored real-tokenizer cases passed; software evidence only | 18.327s CPU wall |
| Graph fixed source100 + alias100 screening | Stopped at21 risk units after21 completed source units; 179 units not screened | 2612.905s whole wall; 21 observed model calls; 63064 input / 22554 output tokens; peak allocated GPU26555098624bytes |
| Human review / accepted graph edges | 0 cards issued / 0 accepted edges; cap gate prevents card release | No human judgments requested |
| Native comparative evaluation | NOT_RUN because prerequisites failed | No new ranking scores or significance tests |

Graph risk reasons: {"ESCALATE": 12, "MALFORMED_OR_UNGROUNDED_CRITIC": 9}. Invalid or ungrounded critic responses are failures of the screening evidence, not validated semantic findings. The remaining escalations are automated risk judgments, not independent expert review. Source-first processing and the prospective risk21 stop left the alias stratum untested; neither a corpus-wide error rate nor alias incompatibility can be estimated from this stopped prefix. No output was repaired or regenerated, and no threshold was changed after observing results.

The SACR profile omitted mechanism/constraint coverage and quantity units independently of the critic's incorrect finding-key names. Fixing that envelope alone would not establish fidelity; no additional candidate was used to reroll the failed profile. Two prospective synthetic candidate slots remain unused. This closes the tested candidate, not the general research hypothesis.

At R5 closeout, cumulative charged GPU time was12309.614s and cumulative fidelity time was12030.727s. The then-remaining allowances were 188.581h GPU and 60.658h fidelity. The 57,600-second Graph reservation was released after charging actual whole supervisor time once. Known model calls are a lower bound of84; historical unknown attempts remain retained. Caps stay GPU192h/fidelity64h/full-dev128h, with fidelity/full dev inside GPU. Remaining allowance does not reopen failed gates. No paid API, training, corpus re-encoding, Neo4j write or permission change occurred.

Canonical evidence: [R5 execution audit](../audits/ptp-r5-execution-20261111/README.md), [Graph terminal aggregate](../audits/ptp-r5-execution-20261111/graph-screen-result/aggregate.json), and [cumulative ledger](../audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json). Raw source/model records remain private. Engineering checks include 35/35 tokenizer/callback/EOS cases, the exact-source admission case, and 61 final integrated local tests; these do not certify semantic quality.

The measured native baseline and Paper53-style descriptive exposure remain the only retrieval results. Direct replication of published DAPFAM scores remains NOT_ESTABLISHED because cohort, model and protocol differ. Paired effects, wins/losses, rescue/displacement and uncertainty analyses remain NOT_RUN. The manuscript is an evidence-backed research draft, not submission-ready. Any later methodological revision requires a new prospective specification; protected-test evaluation and submission remain separate decisions.

Earlier planning and closeout sections below are historical. Their old resource figures, permissions and running-state statements do not supersede this current closeout.

## R5 engineering qualification, 11 November 2026

R5 CPU engineering complete:86 local tests PASS; pinned character33+7numeric cases PASS; real tokenizer/callback/EOS35/35 PASS276.912s, exact original synthetic source1/1 PASS50.434s,input1557. Confirmed integer-bound omission and fused string-boundary token10465 omission; original R4 cause remainsUNKNOWN. Broad boundary adaptersv1/v2 stopped for cost and retained. Private bounded diagnostics preserve first failure and avoid normal-path GPU scalar copies; independent read-only review found no remaining blocker. All6ownedCPUcontainers terminal/PID0, no new model/GPU/fidelitygeneration/cards/retrieval. Graph integrity PASS100source families(86empty,29records),100alias units,215unique records; fullsource attachment code6fixturesPASS, corpus execution NOT_RUN. Cumulative GPU/fidelity charges unchanged; CPU costs in canonical audit ptp-r5-diagnosis-20261111/summary.json. Frozen smoke-proposal.json and R5-BOUNDED-LONG-RUN.md await combined goal/model/source/evaluator and bounded repair-policy approval; GPU192/fidelity64/fulldev128,60cards unchanged. Existing screened-publication permission retained, no duplicate approval requested; current changes local/uncommitted/unpushed, main/baseac48e02. Parent sole writer. Next: obtain2combined decisions; reserve/rebind ledger without method changes; dispatch one qualified smoke; proceed only through declared integrity/fidelity/human/resource gates. No native retry or test opening.


## Verified R4 closeout, 11 November 2026

R4 authorized first stage is terminal. CPU replacement v2 PASS: six positive grammar fixtures and tokenizer admission, 12.341282328 seconds, no model/GPU calls. Positive fixtures do not establish complete live grammar correctness or semantic fidelity.

The subsequent authorized synthetic smoke FAILED with InputBoundaryError in the unsettled profile attempt. Whole wall time 198.974029466 seconds was charged once to GPU and fidelity; the 1800-second reservation was released. No generation.json or detailed exception message was retained. Model calls/tokens and exact failure location remain UNKNOWN; no normal-return events were recorded. This is not evidence of normal EOS rejection or semantic failure. Generic, critic, native fidelity, pilot and full dev remain NOT_RUN. No retry is authorized.

Graph materialization completed 45,336 families, reproducing census counts: 23,037 records and 18,326 pair-key incidences (not unique pairs). Whole wall time in a CPU-only job 26.376899449 seconds; output 63,574,824 bytes. Fixed source100 and alias-pair100 hashes are retained in the audit. Samples remain unscreened; accepted edges and issued cards are zero. No Neo4j writes or protected-test access occurred.

Next: add prospective bounded private failure telemetry and CPU negative grammar qualification, then prepare a concrete new-attempt proposal. Preserve all failed artifacts and cumulative costs. Budget caps remain GPU192h/fidelity64h/full-dev128h, with fidelity/full dev inside GPU192h. Additional budget does not authorize additional experiments. Current canonical receipts: docs/healthtech/audits/ptp-r4-preparation-20261111/smoke-result/aggregate.json and the cumulative resource ledger. Parent is sole writer; changes remain local/uncommitted, last verified base ac48e02.

## Previous planning and evidence (historical status)

## R3 development addendum

A separately authorized census applied the unchanged R2 extractor to all45,336
corpus families. It produced23,037records and13,736keys;951keys occurred in multiple
families. The18,326cross-family pair-key incidences are not unique family pairs.
Maximum family frequency was69, below the predefined hub threshold of more than100.
This overturns no sample observation: the earlier100-family samples contained no
cross-family pairs, while the full corpus contains candidate linkage opportunities.
Semantic compatibility, accepted edges and retrieval effects remain untested.
One-key graph traversal must retain an equivalent posting-list control.

R3 synthetic SACR generation returned a complete profile but failed structural
acceptance because role positions fell outside selected relation evidence.
The unchanged validator reproduced the rejection. No generic/critic/native or
retrieval stages followed. One call used2387input and3395output tokens; whole
supervisor time320.304073s was included in cumulative GPU/fidelity costs.
The census took25.316453s with no model/GPU calls, after a preserved0.009424s
pre-create launcher failure and explicit replacement approval. These development
results do not establish improved retrieval or independently validated fidelity.
See [census](../audits/ptp-r3-packaging-v2-20261111/census-result/aggregate.json)
and [smoke](../audits/ptp-r3-packaging-v2-20261111/smoke-result/aggregate.json).
