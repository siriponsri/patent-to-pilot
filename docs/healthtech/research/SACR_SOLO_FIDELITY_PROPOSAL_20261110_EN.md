# Solo fidelity: automated screening with bounded human escalation

Status: ADOPTED PROSPECTIVELY by the owner's explicit 10 November reply and follow-up;
no fidelity outputs/ratings or retrieval scores observed under this policy. Reduces
manual work without impersonating human judgment. CPU/baseline preparation remains
independently actionable. The filename preserves the proposal's original identity.

## Fixed population and blinding

Retain the existing up-to100 dev-query sample per benchmark. Use UTF-8 bytes of
`sacr-v0-fidelity-20261110|benchmark|query_id`, SHA256 ascending then exact query ID
as tie-break. Benchmark strings are exactly `MTM` and `DAPFAM`; use unchanged opaque
IDs, no Unicode normalization. Select the first min(100, population size). This is
deterministic hash sampling, not a probability claim or a score-selected sample.
The base sample is shared across configurations within each benchmark. Freeze the allowed population and sample manifest
before generation; never sample baseline failures or replace missing/failed queries.
Review source/profile/all proposed generic and selective views without qrels,
candidate lists, retrieval scores or method performance. Fixed manifests/configs
are shared across arms; private source/generated text remains outside public Git.

## Three review layers

1. **Deterministic checks on all100 (or fewer).** Verify source/quote identity,
   structure, explicit literal numbers/units/comparators, negation/direction and
   represented conditions where mechanically decidable. Keep all original artifacts.
   A check returning no issue means only that its implemented rule found none.
   Lexical mismatch is a flag, not automatically a semantic error. A definite
   structural/source-identity defect stays a failure without asking the owner to
   repair it. Missing outputs are unassessable and stay in denominators.
2. **Automated semantic screen on mechanically assessable outputs.** Use the
   already approved local model only under a separate fixed, costed declaration
   inside the8h fidelity envelope. Source-first relation inventory, bidirectional
   assertion/requirement comparison and exact quoted rationales; fixed output schema,
   prompt and token limits, no outcome feedback or self-repair/retry. Treat all
   missing/invalid/disagreeing or uncertain judgments as escalations. Using the
   generator as reviewer creates correlated errors and is not independent validation.
   No actual reviewer-model path or observed performance is claimed by this draft.
3. **Bounded owner review.** Send only (a) unresolved source/role/attachment/context
   judgments, disputed lexical flags or claimed semantic defects, plus (b) a fixed
   ten-query sentinel sample from the provisionally unflagged group per benchmark.
   Select sentinels by ascending SHA256 of
   `sacr-solo-sentinel-20261110|benchmark|query_id`, before retrieval outcomes.
   Review all sampled source/profile/views for each chosen query, including generic
   controls. If fewer than10 unflagged queries exist, use all of them. The sentinel
   check is necessary to detect some false negatives; checking flagged cases alone
   cannot assess the screen's blind spots.

## Human workload and stopping rule

One compact card per query: source requirements, highlighted source/output spans,
automated concern or sentinel label, proposed classification and rationale. The owner
chooses faithful / unsupported / ambiguous / unassessable; no text editing or per-query
arm filtering. Record elapsed review time and all initial/corrected decisions.

The hard cap is **60 human cards TOTAL across both benchmarks and ALL configurations
in this continuation**, with at most30 for MTM and30 for DAPFAM, including at most20
escalations and10 sentinel cards per benchmark across configurations. It is not a
per-configuration allowance. One card is `(benchmark, configuration_digest, query_id)`;
a new configuration on the same query consumes a new card. All arms' source/profile/
views for that tuple appear together on one card. Reopening the same card for a
recorded adjudication does not create another card but its additional review time counts.

Reserve the complete required card set in one private append-only ledger before
presenting it; no per-benchmark/configuration ledger reset. Count previously issued,
unfinished and completed cards. No cards have yet been issued. Before any new
configuration, verify its full required escalation/sentinel allocation fits the
remaining global and benchmark/category limits; otherwise mark HUMAN_BUDGET_EXHAUSTED
and stop that configuration without inventing an automatic PASS. A larger human
allowance requires a new explicit owner decision. This is a maximum workload, not a promise that the configuration
will pass within it. If more than20 escalated queries exist, mark REVIEW_CAP_EXCEEDED
and stop that configuration before requesting a larger human batch. Do not silently
ignore remaining cases or replace them with automatic acceptance. Definite critical
defects can end review early, preserving the unseen/unfinished counts.

Any confirmed invented mechanism/parameter, corrupted polarity/quantity/direction,
role reversal, wrong attachment or omitted explicit requirement fails this
configuration. Any unresolved required judgment prevents PASS. A sentinel critical
error also fails the screen/configuration; do not just expand the sample until an
acceptable rate appears. No prompt repair after seeing retrieval outcomes.

If the automated checks and complete bounded human work find no critical defects,
the most that can pass is **SOLO_SCREEN_AND_SENTINEL_GATE_PASS**. This explicitly
replaces, and is weaker than, the previous completely human-reviewed100-query gate.
It is not SAMPLE_FIDELITY_GATE_PASS under the old policy. The owner adopted this
weaker amendment before new fidelity sampling and before retrieval outcomes.

## Reporting and limits

Report the full fixed sample, available/attempted/valid outputs, failures, duplicates,
fallbacks, automatic flags, unflagged queries, escalations, sentinels, reviewed/assessed
queries/views, confirmed critical errors and unresolved judgments separately. Never
describe unreviewed automatic negatives as human-verified faithful. Do not extrapolate
an overall human error rate from risk-selected escalations. The sentinel population
and small sample have their own limits; no zero-population-risk claim.

Report automatic-review calls/tokens/time/memory within the same resource ledger and
owner time separately. Reviewer agreement is not ground truth. This is solo formative
review with algorithmic triage, not expert consensus or independent validation.

## Dependencies and adoption

No extra paid model, training or test access. Actual isolated dev inputs, viable
generation, a pinned screening implementation and a runtime projection fitting the
approved fidelity envelope remain required. If those are infeasible, report the
specific issue; do not manufacture ratings. Baseline parity, container preparation
and other permitted independent work continue while implementation and actual review
remain incomplete. The owner explicitly requires stopping/reviewing the configuration
when a sentinel critical error is found; the policy never declares immediate PASS
after such a discovery. The new model smoke used only authored synthetic text and
is outside this dev-fidelity sample; its failure is retained separately.
