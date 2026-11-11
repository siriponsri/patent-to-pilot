# Proposed goal: DAPFAM Paper 1 SACR and matched Structured/Graph evidence

## Owner-approved execution, 11 November 2026

Both decisions approved in call_172d9619b8e64a6781a0ff36fb183240. Execute within all ceilings and gates below. The following original proposal is retained as the approved specification; its pending wording is historical. New goal creation was rejected because an unfinished old goal exists; do not falsely complete that goal. Continue authorized work in this chat. Approval receipt: audits/ptp-r5-execution-20261111/owner-approval.json.

## Terminal execution, 11 November 2026

The conditional run closed at its declared gates: SACR synthetic candidate1 failed fidelity/critic acceptance; Graph stopped at21 source risk units in2612.905s, leaving79source+100alias units unscreened. No cards or accepted edges; native/pilot/full-dev/MTM NOT_RUN. All new attempts settled, Graph reservation released, historical unknowns preserved. Two synthetic candidate slots unused; no reroll to seek a favorable outcome. See [execution closeout](../../audits/ptp-r5-execution-20261111/README.md).

## Original approved proposal

Status: PROPOSED, NOT ACTIVATED. No new model generation is authorized by this
document. The owner requested diagnosis, immediate code fixes and CPU tests;
the following model/corpus/evaluation extension needs one combined
decision. Existing goal service reports blocked; this proposal does not overwrite
or falsely complete it.

## Outcome and completion rule

Produce a reproducible DAPFAM development-only B0/SACR/S/G comparison, or a
documented feasibility/fidelity failure for each stopped configuration, with
positive/negative results, integrity failures, uncertainty, resources and a
Paper 1 report/manuscript update. Preserve the existing paper53 alignment and
paper-to-paper DAPFAM comparison task, labeling differing splits, corpus fields,
models, aggregation and metrics as non-comparable rather than claiming
apples-to-apples replication. Protected tests, MTM and later papers stay closed.
The goal does not require beating B0. A pending required human judgment is a
pending gate, never a successful or failed scientific judgment by timeout.

## Current evidence and engineering gate

R4 smoke remains an unresolved InputBoundaryError with no raw return and unknown
calls/tokens; costs already settled. Do not reinterpret it from later fixtures.
The pinned LMFE integer parser ignores numeric minimum/maximum. R5 enumerates
every bounded integer domain, including condition references. A 33-case
character matrix plus seven numeric cases validates that correction; R4 admits
eight forbidden instances in that same matrix.

Actual tokenizer/callback testing then rejected three valid reversed-field
instances. Targeted fixtures show string cases fail at token10465 whereas a null
abstraction passes. A prospective reduced boundary-token trie preserves exact
parser traversal for fused string-ending tokens omitted by the freetext shortcut.
The final v3 adapter passed35/35 real tokenizer/callback/EOS cases in276.912s
whole wall time (peak1204183040bytes), plus one populated reversed-field fixture
on the original synthetic source in50.434s (1557input tokens). Earlier broad-trie
v1/v2 candidates were stopped for excessive CPU cost and remain failures. These
are authored-fixture qualifications, not exhaustive grammar or fidelity proof. No forced
field order, unconditional token allowance, output repair or relaxed compiler.

Private bounded diagnostics record backend dispatch/return, the first failure,
schema rejection path and at most4096 generated suffix token IDs, with a256KiB
per-stage ceiling. No prompt tokens, per-token filesystem logging or scalar GPU
copies during normal decoding. A backend invocation is not proof of completed
inference. Telemetry write failure must preserve the original exception.

## Budget snapshot and proposed stage ceilings

Authoritative ledger: audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json.
Snapshot after R4: GPU9525.762891649225s charged,681674.2371083507s remaining
(189.35395h); fidelity9246.876066800629s charged,221153.1239331994s remaining
(61.43142h). Preserve all historical unknowns. No budget reset.

| Stage | Proposed ceiling | Admission and retained result |
|---|---:|---|
| CPU diagnosis/qualification | 2CPU,2GiB,10min per bounded job | Authored positive/negative fixtures; no model/data access. Completed current tests do not need repeating unchanged. |
| Synthetic engineering candidates | At most3 prospective revisions,3 calls/30min each; total9 calls/90min | First fully passing candidate frozen before native data or retrieval. Each failed candidate preserved. No replay of its outputs. |
| Native bridge | First5 of fixed SACR100,≤15 calls/2h | No substitutions; retained outputs reused in100. Integrity/admission failures stop dependent work. |
| SACR fidelity remainder | Remaining95,≤285 calls/30h | Same frozen configuration; no regenerated bridge. Profile/generic/critic, independent strict validation. |
| Graph source attachment | Existing corpus one read,CPU1/2GiB/30min/output64MiB | Select existing fixed100 source IDs, including86 empty extractor results; no re-extraction, new census or qrels. Bind full source fields and hashes privately. |
| Graph screening | Fixed100 source units +100 alias-pair units,≤200 local critic calls/16h | Same local model; no corpus LLM extraction; source omissions and alias compatibility screened separately. |
| Pilot | Existing fixed20 dev queries,≤60 new calls/2h total | Only after human gates. Reuse already measured outputs. Readiness/cost gate, no score-tuned revisions. |
| Full dev | Existing474-query cohort,≤1422 new calls/128h total | Only passing arms; subtract cached calls/queries and all used budgets. Frozen controls/evaluator. |

New GPU reservations across these stages total at most179.5h, inside the current
189.35395h remainder. Synthetic/bridge/SACR/Graph are charged to fidelity as well
as GPU, at most49.5h versus61.43142h remaining. Pilot/full-dev accounting remains
inside cumulative GPU192h; full dev128h is not an additional GPU allowance.
This is a ceiling, not a time prediction or a target to consume. Reconcile the
ledger before every reservation; any lower authoritative remainder wins.
CPU evaluation/joins/reporting ≤8CPU-hours total for this proposed extension.
Global limits remain one GPU job, CPU≤8, RAM≤32GiB, added disk≤40GiB cumulative.
Reserve at most8GiB new artifacts for this extension only after proving space
remains; do not delete evidence to make room. No paid API, training, corpus
re-encoding, system-rights changes or network-enabled experiment containers.

## Graph continuation and fixed human workload

Retained sample integrity passes:100 source families,29 extracted records from14
families,86 empty;100 pair-key sample units,215 unique records checked across
both samples. This does not measure source recall or semantic fidelity. Full
source text is missing for empty families and must be attached before screening.
No resampling of the frozen R4 source/alias populations or representative witnesses.
An empty extractor result is not an automatic fidelity pass.

Keep SACR30 cards and S/G30 cards,60 TOTAL across all configurations; currently0
issued. No automatic transfer to MTM, no replenishment after failed configurations.
For SACR use the existing fixed100 queries. For S/G use both fixed100-source and
100-alias populations; one source unit or one two-witness alias pair is one card.
All critical/ambiguous/rejected/incomplete screening units form the risk pool.
If a branch has more than20 risk units, STOP that configuration without issuing
an oversized batch or silently dropping difficult examples. Otherwise issue all
risk units plus10 sentinels from the remaining screening-pass units.

Sentinel ranking is SHA256 over UTF-8 `ptp-r5-sentinel-v1-20261111|` + canonical
JSON `[branch, frozen_config_sha256, unit_type, stable_unit_id]`, sorted ascending
with canonical JSON as tie breaker, before seeing retrieval outcomes. SACR takes
10 query units. S/G takes5 source and5 alias units; if a stratum has fewer than5
screening-pass units, stop the gate rather than silently reallocating. Freeze
the resulting manifest and all risk decisions before evaluator scores are read.
S/G and SACR share no card slots. Record source/alias strata and actual counts.

Automated local critic screening is not independent expert review. Owner reviews
all issued risk and sentinel cards. Any critical error, including in an automated
pass sentinel, stops and triggers configuration review; never immediately pass
that configuration or repair per-query output. Missing human decisions keep the
gate pending. Human acceptance cannot be inferred from absence or elapsed time.
Other independent CPU/documentation work continues while waiting. No cards are
issued in the current diagnosis package.

## Controls and gates before scores

Use the existing DAPFAM corpus, query fields, fixed474 development cohort,
family aggregation and evaluator. Primary OUT Recall@200; report nDCG, acquisition
rescue, final-top200 loss/displacement, IN/ALL context, failures and complete costs.
Preserve source-anchor and matched-coverage controls. S and G share extraction,
aliases and scorer. Include the exact posting-list-join equivalent; one-key graph
traversal is not a novel retrieval method merely because it is stored in Neo4j.
No score-informed prompt, threshold or query-level edits. Deterministic tie/order
rules and artifact/config hashes must be frozen before scoring.

Neo4j/MCP is optional infrastructure, not a scientific gate or novelty claim.
Continue offline graph/posting controls without importing or altering databases.
Database writes, installations or rights/network changes are excluded from this
proposal; if later essential, return with an exact separate scope. No second
instance, credentials in files, or automatic widening of authority.

## Proposed autonomous repair authority

Allow immediate local code/packaging/test/documentation fixes when defects are
found, under one writer and read-only reviewers. Each revision records cause or
remaining hypotheses, tests and a new declaration hash BEFORE execution; retain
all old configurations/results. Engineering can iterate within the CPU ceiling.

Permit up to2 replacement CPU/packaging attempts per stage only when receipts
prove no backend invocation/data operation began; preserve failed receipts and
charge whole time. Synthetic model revisions are limited by the3-candidate/9-call
ceiling above. No automatic native-query regeneration, no retry after unknown
backend state, no late threshold change, no extension of cards or resources.
If the same failure persists or a semantic/human gate fails, close that candidate
and report it. A correction to integrity/accounting can proceed immediately but
does not convert old failures into successes or allow scoring inadmissible data.

## Combined owner decisions requested

1. Activate this bounded long-run goal and its gated model/source-attachment/
   evaluation plan, including the two-stratum Graph human-review rule within60
   cards and all ceilings above.
2. Approve the bounded autonomous repair/replacement policy above so routine
   engineering corrections need no repeated permission. Native unknown/rejected
   generation remains non-retriable.

Screened publication already has an earlier explicit owner approval in this
conversation (code/documents/public evidence including pending documents).
Do not request that same permission again. Any publication must still screen
the exact staged tree and exclude raw/private evidence, credentials, corpora,
model artifacts and the unrelated owner handoff file. The current diagnosis
checkpoint is local/uncommitted; no claim of synchronization is made. Include
screened publication in the approved continuation after its release checks.

Approval of the budget alone is not approval of these new executions. The owner
may approve the whole proposal in one reply; until then CPU fixes and reporting
continue, while new model/corpus/evaluation dispatch stays NOT_RUN.
