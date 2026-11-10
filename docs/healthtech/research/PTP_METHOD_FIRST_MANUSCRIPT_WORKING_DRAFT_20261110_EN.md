# Selective Abstraction with Requirement Preservation for Cross-Domain Patent Retrieval

Working manuscript material — INCOMPLETE, NOT FOR SUBMISSION.
This draft follows the owner's research handoff §19. It preserves the intended
method-first study; it is not a completed empirical paper or a diagnostic-only pivot.
No protected results, novelty clearance or publication readiness are claimed.

## Research question and intended contribution

Can query abstraction that retains explicit technical relations improve known-citation
recovery beyond a fixed passage retriever and resource-matched generic multi-query
controls? SACR is the proposed, untested procedure. The intended study distinguishes
changes in candidate acquisition from changes in selection at a fixed output depth.
An external family-level benchmark, DAPFAM, and the specialized retrospective Medtech
Time Machine (MTM) collection serve complementary roles. Their outcomes must be
reported separately because their candidate and label semantics differ.

An abstract claiming an empirical advantage is deliberately absent. The evidence
currently supports a method specification and partial engineering/integrity work,
not SACR retrieval effectiveness. A [targeted primary-source comparison](SACR_PRIOR_ART_COMPARISON_20261110_EN.md)
now bounds seven related sources against the implemented selector. It is non-exhaustive;
full-method access and broader coverage remain necessary before novelty language. The owner's separate conference work must be cited using its
verified publication status at manuscript review; no DOI is inferred here.

## Task and evaluation boundaries

MTM uses only the frozen problem text for the primary query view. Candidate eligibility
is evaluated with the declared date, own-family and cross-class rules. Native DAPFAM
uses the selected title/abstract query view shared by controls; native OUT filters
qrels rather than removing candidate families. The project-specific filtered X lane
must not be presented as native DAPFAM OUT. Full-release reference results and project
dev-subset results are also different estimands.

Runtime inputs exclude qrels, construction roles and hidden target fields. Prospective
loaders, curator tooling and manifests exist, but real physical isolation and baseline
ranking parity have not been established for this continuation. A hash binds bytes;
it does not establish access isolation or eliminate prior knowledge. The mixed-label
source must be handled by the owner-designated curator outside development-agent access.

## Proposed method

SACR extracts source-linked relation blocks with explicitly attached conditions from
the allowed query. It proposes a selective abstraction and a deterministic relational
serialization alongside the unchanged anchor, with at most three views. Exact quote
alignment rejects absent or ambiguous quotations without normalization. It cannot
certify correct role assignment, condition attachment or preservation of omitted content.

The proposed acquisition stage searches the same eligible fixed passage index for
each usable view, at depth 200, forming a deduplicated union of at most 600 families.
The selector combines anchor similarity with local coverage using the specified
rank normalization. For each block, relation and condition similarities are combined
within a single passage before taking maxima over passages and blocks. Consequently,
separate requirements cannot be assembled from different passages for one block,
while the maximum over blocks still permits partial matching. This is not a global
all-requirements test, semantic entailment score or engineering compatibility judgment.

The [versioned specification](SACR_V0_SPECIFICATION_DRAFT_20261110_EN.md) defines
the arithmetic, fixed proposed weights, tie handling and failure behavior. Selector
arithmetic has synthetic tests; full-index acquisition and injected-stage integration have synthetic checks;
production end-to-end SACR and actual retrieval validation remain incomplete.
An anchor fallback is a recorded failed/empty transformation outcome, not evidence
that SACR itself succeeded. No automatic alternative research method is substituted.

## Intended experimental design

Retain the frozen passage baseline and report historical V4 separately. Compare generic
and invariant-preserving view construction crossed with mean-only and local-bottleneck
selection. Match raw inputs, available views, search depths, candidate/output caps and
model budgets; expose shared profile extraction costs rather than concealing them as
free preprocessing. A reranker moved to a new candidate head is a new comparison.

The existing MTM primary endpoint and carry-forward rule remain authoritative. Acquisition
rescue, fixed-depth selection rescue, losses and selection losses are distinct outcomes.
Report every attempted query, including unavailable text, invalid generation and fallback.
Choose uncertainty procedures appropriate to shared-family dependence and declare
multiplicity handling before protected evaluation. Do not claim non-inferiority without
a prespecified margin. No numerical threshold or final panel is adopted by this draft.

The [fidelity policy proposal](SACR_FIDELITY_ACCEPTANCE_POLICY_DRAFT_20261110_EN.md)
keeps developer source review separate from retrieval relevance and prohibits unreported
human filtering of the automatic arm. Its sample, adoption and observations are pending.
Any protected comparison requires an owner-approved immutable freeze of at most four
total systems under the current conservative interpretation. This draft grants no access.

## Evidence available at this checkpoint

| Evidence | Supported statement | What remains unproven |
|---|---|---|
| [A14 observation](../audits/ptp-method-first-r1-vectors-20261110/README.md) | Observed corpus/vector hashes match historical receipts | Original tokenizer/order attestation and actual ranking parity |
| [DAPFAM synthetic differential checks](../audits/ptp-method-first-r1-dapfam-20261110/README.md) | Synthetic adapter behavior was compared with the pinned native implementation | Actual native benchmark replication |
| [First model smoke](../audits/ptp-method-first-r2-smoke-20261110/README.md) | Profile failed source offsets; failure preserved | Reliable extraction or semantic fidelity |
| [Quote-profile model smoke](../audits/ptp-method-first-r2-quote-smoke-20261110/README.md) | JSON failed before quote alignment | Viable quote-only generation |
| [Configured grammar CPU check](../audits/ptp-method-first-r2-full-schema-v2-20261110/README.md) | Eight of ten authored token checks matched expectations; two escape cases failed; follow-up timed out | Compatible, resource-feasible generation integration |
| [Execution-v3 contract](../audits/ptp-method-first-required-generation-20261110/README.md) | Authored integration tests cover generation evidence, sealed costs, original-anchor binding and six-stage finalization | Actual model loading/prompt identity, isolation, corpus-scale resources, fidelity and retrieval effectiveness |
| [Bounded vector hashing](../audits/ptp-method-first-vector-hash-20261110/README.md) | Canonical hashes preserved with bounded temporary hash buffers on authored arrays | Whole-index copies and deployment memory acceptance |

These are engineering observations, not retrieval results. No SACR pilot, full dev
comparison or protected comparison is reported. Historical baseline/V4 results belong
in a separately sourced development-history table, not as fresh SACR evidence. The
final results table remains unfilled until run receipts and complete denominators exist.

The [readiness refresh](../audits/ptp-method-first-readiness-refresh-20261110/README.md)
distinguishes implemented orchestration from the still-open scientific gates. A
proposed rule for discarding an unusable generated family remains an owner protocol
decision; current failed-stage behavior is retained until a decision is recorded.
No successful fallback or fixture execution is counted as a successful abstraction.

## Limitations to retain in the eventual paper

Citation judgments are incomplete proxies; unjudged families are not confirmed
irrelevant. Recovery of known citations does not establish a complete solution,
successful technology transfer, clinical suitability, legal clearance or business value.
MTM problem texts and classifications are retrospective, and its constructed candidate
universe retains target families alongside sampled distractors. Publication-date
eligibility does not make pretrained models historically contemporaneous. Representative
family texts and truncation may omit relevant material.

Developer fidelity review is formative and may reflect prior exposure to project
outcomes. There is no independent expert panel or user validation. Local model hashes
identify observed files without proving original provenance or training-set exclusion.
Grammar compliance and literal source matching do not establish semantic preservation.
Current failed generation/grammar checks preclude an effectiveness claim; they also
do not show that all requirement-preserving retrieval methods are ineffective.

## Reproducibility and completion requirements

Keep code commits, input/model/tokenizer manifests, prompt/schema versions, all failed
attempts and resource receipts. Distinguish directly measured runtime from projections.
Publish only permitted aggregates, hashes and authored code/text; raw benchmark texts,
generated model outputs, private rankings and scores stay outside Git. Data, model,
code and paper rights require separate review before any release.

Before manuscript review: finish actual integrity gates, a viable method implementation,
adopted fidelity review, bounded pilot, full dev decision and owner-approved final
evaluation if proceeding. Complete the result/uncertainty/cost tables, closest-prior-art
comparison, verified citations, rights ledger and author/AI-assistance disclosures.
Current journal instructions must be checked when submission preparation is authorized.
No submission, fee commitment, public deployment or external contact is authorized here.
