# SACR fidelity acceptance policy

Status: HISTORICAL FULL-HUMAN-REVIEW PROPOSAL / NO RATINGS COLLECTED.
The owner prospectively adopted the weaker automation-first solo policy in
[SACR_SOLO_FIDELITY_PROPOSAL_20261110_EN.md](SACR_SOLO_FIDELITY_PROPOSAL_20261110_EN.md)
on10 November2026, with a60-card total cap across both benchmarks/all configurations.
The old fully human-reviewed100-query gate below is retained for comparison and must
not be claimed as passed by the new automated-screen/sentinel gate.
This elaborates the [specification](SACR_V0_SPECIFICATION_DRAFT_20261110_EN.md)
and [audit form](SACR_FIDELITY_AUDIT_FORM_20261110_EN.md), following the owner
handoff §§12.2, 13.7–13.8. It does not amend the frozen retrieval endpoint or
authorize a pilot. Adoption requires a dated methods-log entry before generation,
review or new retrieval outcomes. The generation compatibility gate remains failed.

## What the review decides

Review tests whether the proposed transformation preserves the information supplied
in the allowed query. It does not decide whether a retrieved patent is relevant.
Reviewers receive the source, profile and generated views with immutable identities;
they do not receive candidate lists, qrels, baseline failures or method scores.
Prior developer exposure to historical results must still be disclosed.

The output is a batch-level formative decision about a fixed configuration. Human
review must not selectively edit, approve or remove individual generated views in
the official automatic retrieval arm. Doing so would create a human-assisted system
and require its own declaration and cost accounting. Mechanical runtime rejection
rules remain the same for every query; the developer audit is not an oracle filter.

## Unit and rubric

Review every available sampled source, attempted profile and proposed view, including
duplicates, anchor-only outcomes and partial failures. First enumerate explicit source
relations and conditions independently of the generated profile. Then compare both
directions: every output assertion against the source, and every explicit source
requirement against the output. A faithful quotation attached to the wrong action
is an error. Omitted context is not presumed disposable.

| Dimension | Pass evidence | Error or unresolved condition |
|---|---|---|
| Relation roles | Action, operand and effect keep their stated roles | Role reversal or invented causal link |
| Quantity and units | Literal quantity, range, comparator and unit preserved | Added threshold, altered inequality or unstated conversion |
| Polarity and direction | Negation, exception and direction retained | Lost negation, reversed flow/direction, changed exception |
| Attachment | Condition remains attached to its stated relation | A real phrase assigned to another relation |
| Completeness | Each explicit requirement is represented or an omission is identified | Dropped condition or source relation |
| Context abstraction | Replacement demonstrably preserves the stated requirement | Material/anatomy/environment relevance is uncertain |
| New content | No new mechanism, parameter or solution asserted | A plausible but unstated solution is introduced |

Use faithful, unsupported, ambiguous or unassessable. A missing output is unassessable,
not faithful. Record source/output spans and rationale for every error/uncertainty.
The same rubric applies to generic and selective views; generic controls do not
receive an unreported semantic advantage or a different human correction policy.

## Proposed batch gate, fixed before observation

Use the existing deterministic sample proposal: up to 100 authorized dev queries per
benchmark, ordered by the declared SHA256 key. This is a workload bound, not a power
calculation. It cannot execute until the authorized population is isolated and pinned.

1. Missing generation, invalid structure or source mismatch is an engineering failure.
   Keep the query in all denominators. Do not replace it with another sampled query.
2. Any observed invented mechanism/parameter, corrupted polarity/quantity/direction,
   role reversal, wrong attachment or omitted explicit requirement blocks progression
   of that configuration. This intentionally conservative proposed gate is not an
   estimate of the population error rate or a universal fidelity standard.
3. An unresolved abstraction or unassessable required judgment prevents a PASS. Record
   REVIEW_INCOMPLETE rather than treating uncertainty as absence of a defect.
4. A completely reviewed sample with none of these defects may receive
   SAMPLE_FIDELITY_GATE_PASS, conditional on the engineering and integrity gates.
   It does not certify all future outputs or justify semantic-support claims.
5. If a defect is disputed, preserve the initial judgment and an append-only rationale
   for adjudication. No independent adjudicator is currently assigned; do not claim
   consensus, inter-rater reliability or independent expert validation.

If this proposal is too restrictive, revise it before inspecting outputs and record
why. Never relax a threshold after observing the intended configuration's results.
No non-inferiority margin is selected here. The historical MTM carry-forward rule
remains unchanged. Failed configurations and original outputs remain immutable.

## Rates, costs and dependence

Report separate denominators: full sample, available inputs, attempted profiles,
mechanically valid profiles, proposed views, reviewed views and assessed views.
Report missing, failure, fallback, duplicate, condition-present and conjunction-active
counts separately. Provide query-level incidence as well as view-level counts so
multiple views from one query do not masquerade as independent observations.

Describe the fixed dev sample and uncertainty limitations. Do not present a zero-error
sample as zero population risk, or a binomial interval as accounting for shared-family
dependence. Record review time separately from model and retrieval time; it is study
audit labor, not an automatic inference cost. Preserve all reviewer decisions privately;
only permitted aggregates/hashes enter Git. Test records are never part of this audit.

## Current disposition

No sample has been drawn and no source-fidelity ratings exist under this policy.
SACR cannot advance on this document alone. Needed: approved input isolation and real
R1 checks; a viable declared generation path; pinned sample/configuration; rubric
adoption; observed complete audit; then a bounded R3 declaration with matched controls.
