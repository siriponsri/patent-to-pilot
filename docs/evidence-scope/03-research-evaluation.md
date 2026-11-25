# S3 · Matched research evaluation

**Status:** complete, NEGATIVE on controlled Thai DEV, uninformative English transfer. **Track:** research. **Entry:** an S1 controlled pilot and frozen measurement packet. **Consumer:** S5. [Master plan](MASTER-PLAN.md) · [Data phase](01-research-data.md) · [Frozen questions and decision rules](FREEZE.md) · [Execution receipt](../healthtech/audits/S3-20261125/RESULTS.md).

## S3-T01 · Implement the decision and replay contract

Use the shared evidence unit and typed relations from S1. The runtime input contains the request, ordinary source metadata, allowed initial pool and the searchable licence-cleared corpus. Maintain conditions, candidate evidence IDs, explicit source relationships, compatibility constraints, actions taken and budget left. A trial needs a policy ID/revision, initial-pool hash, index/model identity, action trace and final decision with exact cited units. Distinguish “not found after these actions” from an explicit conflicting source. Keep the evaluator and runtime independent.

Implement three choices under the fixed envelope: preserve or stop with available evidence, rerank the current pool, or acquire additional candidates for a specific missing relationship. A pool can match every keyword while lacking a coherent assignment across all conditions. The compatibility-aware policy may seek the missing original version, parent clause, permitted embodiment or row header. Inferred relationships are marked as such and retain the underlying passage.

Before using benchmark content, check four hand-verifiable fixtures: a correctly scoped answer that should remain stable, a displaced witness recoverable by reranking, an absent witness recoverable by acquisition, and a finite corpus with insufficient evidence. Include a valid cross-source reference and an invalid same-document combination. Replay trace IDs to the same decisions under deterministic settings; log provider variation separately.

## S3-T02 · Lock comparisons and operations

| Arm | Components and interpretation |
|---|---|
| Static production baseline | Use a frozen commercial-use-compatible retrieval stack and the existing local hybrid route where available. Preserve text, source versions and search budget. Report actual candidate depth and costs. |
| Compatibility reranker | Allow the strongest eligible compatible candidate to move up within the fixed initial pool. It cannot recover a witness outside that pool. |
| Coverage controller plus compatibility reranker | **Primary comparator.** Use coverage and marginal return to acquire or stop. Use the same typed compatibility ranker, model, index, corpus and skills as the proposed policy. |
| Scope-aware acquisition | Same stack. Expose joint compatibility to the action selector so it can recover missing witnesses or preserve a valid pool. Report changes in action, provenance and rank. |
| Ablation | Remove only the scope signal at action selection and retain it at reranking. Reuse the matching control run when the resulting implementations are identical. |
| Offline optimization | Compare fixed skill/fixed harness, SkillOpt only, bounded HarnessOpt only, and both. Keep the target model, training families, edit-selection allowance, development examples and optimizer cost ceilings matched. Run this factorization after the core pilot if resources allow. Otherwise mark missing cells NOT_RUN and withhold optimizer-specific attribution. |

Reserve the primary contrast and one frozen nominated method before independent DEV evaluation. Other arms are exploratory. Candidate plan changes can touch only declared skill text and policy choices. Keep scoring, rights, evidence locators, test access and resource ceilings outside optimizer edits. Reuse stable resource accounting and record direct/hosted cost, latency, tokens, number of candidates inspected and stop reasons. If an arm overruns, count its request according to the freeze and preserve its receipt. Request new cost authority only when the existing envelope does not cover a proposed job.

## S3-T03 · Execute the three-state pilot

1. Start with the same ordered cases, initial pools and cap in every arm. Include cases whose correct source is present outside the shared seed pool. Issue no numbers until the data, scorer and settings receipt exists.
2. Score the primary Thai controlled set as specified in [the freeze](FREEZE.md). Report numerator/denominator and paired change within each state, the equally weighted primary change and its cluster interval, all coverage errors, invalid cross-scope evidence and answer rates. Report failures as recorded, including source and infrastructure failures. Use family as the resampling unit. Preserve sibling changes and invariances within each draw.
3. For each condition-changing pair, measure whether the decision or required evidence changed in the expected direction. Separately count invariance pairs whose outputs stayed correct. Show harm to previously correct evidence and the number of requests the system declined. Compare false support at a fixed answering rate only as a diagnostic with its threshold frozen on optimizer-development families.
4. Audit what changed in the top results and use blinded source review where an ambiguous natural passage needs human interpretation. Publish sample selection rules before choosing examples. Quantify saved search actions in already-sufficient cases and extra action cost in missing-witness cases.
5. The first English controlled run uses the identical frozen policy with its English patent source adapter. Report transfer independently from Thai results. Any later within-domain tuning earns an expressly labeled row.

## S3-T04 · Preserve the IS1 / Paper 53 research bridge

| Study | Independent scoreboard and conditions |
|---|---|
| IS1 promised depth experiment | Compare PatEmbed candidate depths 100 and 1,000 with Generic, Patent-aware, Claim-focused and Scrambled instructions, restricted to authorized research DEV material. Keep rendering, encoder, reranker, corpus, family handling and tie policy fixed within each comparison. Report strict OUT nDCG@100, early reach and first known OUT hit, including no-hit counts. Budget shortfalls yield a named partial matrix. The supplied Paper 53 reports 257/692 exposed queries in frozen top-100 pools; original run records were unavailable. Other cohorts require their own matched controls. |
| P2 lexical/dense reference | Preserve the older 2,000-query complete-content fusion and seed-only comparison, known-link ALL Recall@200 and IN/OUT clusters. Include a separate deployable stack with its own fresh index for any product claim. A different cohort or encoder needs a matched rerun of its own baseline. The earlier +0.010 threshold and CI guards govern only the comparable P2 score-win claim. P2-T04 remains NO_GAIN. |
| Native DAPFAM and auxiliary benchmarks | If eligible material and implementation are available under the standing TEST restriction, use the native task unit and predeclared scorer. Exposed literature aggregates are eligible context where rerunning would cross that boundary. Write NOT_RUN for unavailable rows. Keep document-family retrieval, supplied-document grounding, legal text retrieval and controlled scope scores in distinct tables. |

This bridge may proceed in parallel with the controlled study when resources allow. Its incomplete rows must never promote controlled-packet results to historical benchmark gains or block the product track.

## S3-T05 · Decide and hand off

The receipt contains manifest and policy hashes, deviations, resource bookings, per-arm completion, counts, intervals, subgroup directions, the selected disposition and the private location of allowed per-query traces. S5 receives aggregate tables and a short claim-evidence map. Use the existing private/committed separation and update the handoff and tracker at each major event.

| Observed result | Next action and permissible conclusion |
|---|---|
| Positive paired DEV primary estimate | One follow-up is allowed, including when the interval crosses zero. Freeze eligible new DEV families, fixed policy and resources first. Report any imprecision. A pilot alone demonstrates an exploratory signal. |
| Flat or negative primary estimate | Close the phase with the result and mechanism diagnostics. Retain the simpler successful product route. Preserve the negative research arm and its evidence. |
| Mixed domains or outcome strata | Report where the estimate changed and its uncertainty. Keep the original primary result. A subgroup may motivate a separately frozen future hypothesis. |
| Incomplete controls, missing state or insufficient independent judgments | Deliver a feasibility or diagnostic receipt, name the missing comparison and constrain the scope of conclusions. S4 can continue with cleared demo material. |

**Suggested first instruction for GPT 6.2 high:** verify the S1 receipt, scorer and common budgets, implement the common controller and one-signal ablation, and exercise the synthetic fixtures first. The key deliverable is a reproducible matched comparison whichever direction the estimate takes.

## Dispatch status

| Task | State | Receipt |
|---|---|---|
| S3-T01 | COMPLETE | S1 verification and 13 independent S3 checks. See [preregistration](../healthtech/audits/S3-20261125/PREREGISTRATION.md) |
| S3-T02 | COMPLETE | [Frozen nomination, code, inputs and ceilings](../healthtech/audits/S3-20261125/freeze.json) |
| S3-T03 | COMPLETE | [Thai and English originals, paired outcomes, accounting and independent audit](../healthtech/audits/S3-20261125/RESULTS.md) |
| S3-T04 | COMPLETE | [Eligibility, historical metrics and NOT_RUN cells](../healthtech/audits/S3-20261125/BRIDGE.md) |
| S3-T05 | COMPLETE | NEGATIVE. Tested arm parked and [handoff](../../HANDOFF.md) updated |
