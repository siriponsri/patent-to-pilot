# Solo fidelity: automated screening with bounded human escalation

Status: PROPOSED, NOT ADOPTED; no new fidelity outputs/ratings or retrieval scores
observed under this proposal. Responds to the owner's 10 November request to reduce
manual work without impersonating human judgment. The approved failure policy and
CPU/baseline work do not wait for adoption of this separate semantic-review gate.

## Fixed population and blinding

Retain the existing up-to100 dev-query sample per benchmark and the existing
SHA256 ordering key from SACR-v0. Freeze the allowed population and sample manifest
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

Propose at most20 escalated queries plus10 sentinels per benchmark (<=30 cards each,
<=60 across both). This is a maximum workload, not a promise that the configuration
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
It is not SAMPLE_FIDELITY_GATE_PASS under the old policy. Owner must adopt this
amendment prospectively before the new screen is used to authorize R3.

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
and other permitted independent work continue while this proposal awaits adoption.
