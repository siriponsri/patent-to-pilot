# Pilot readiness — bounded offline G09/G10 prototype

Date: 2026-10-25
Status: **engineering-ready for targeted review; scientific pilot not started**

This document defines the next bounded pilot decision. It does not report a
model result, prove utility, establish novelty, or authorize paid API/GPU
usage.

## Research question

When an allowed evidence or organization policy changes, can a source-linked
workflow reduce unsupported route decisions and preserve unaffected fields at
lower measured revision cost than simpler alternatives, under the same input,
evidence, validators, and budget?

The comparison must remain open to the result that deterministic rules are
enough, that a more complex method is not worth its cost, or that the current
packet coverage is inadequate to decide.

## Methods receiving the same information

Each method must receive the same staged brief, versioned fictional profile,
allowed evidence packet, policy/event input, output schema, and deterministic
validators. No method may receive evaluator-only answers, expected document
IDs, hidden facts, future events, or source archives outside the staged
allowlist.

Minimum development comparators:

1. **B0 direct rule path:** deterministic extraction and explicit policy checks
   with no adaptive retrieval or memory.
2. **B1 full regeneration:** regenerate the complete draft from the current
   packet after each change.
3. **B2 direct revision:** revise the prior draft using only the explicit
   change event and current allowed evidence.
4. **Proposed bounded workflow:** source-linked options/routes, scoped
   invalidation, unknown handling, preservation, and typed diff/read-back.
5. **B3 deterministic invalidation + same generator:** apply deterministic
   invalidation and regenerate with the same generator after each event. This
   is the required comparator for any claim that scoped invalidation helps.

For every method in one comparison track, the runner must pass the same
evidence-ID links, source versions, locators, profile version, brief, policy,
event, and validator inputs. A proposed method must not receive extra links or
checked facts. Missing or invalid evidence is reported as unknown under the
same contract for every method.

If a provider path is later authorized, it must use the same staged packet and
validator interface. Its calls, retries, token usage, latency, and costs are
logged separately; no paid call is part of this readiness document.

## Data still required before a scientific pilot

- Expand from the current three development cases to the proposed development
  coverage without treating state variants as independent projects.
- Prepare source-backed cases with stable source versions, evidence locators,
  family IDs, duplicate/family separation, and explicit unknown fields.
- Prepare organization/profile groups with at least three fictional profiles
  and record which profiles are reused for development versus held out. Do not
  claim cross-organization transfer from reusing the same profiles.
- Define a final dev/validation/test split only after coverage and pilot
  calibration. The current G06 contract is not a final freeze.
- Keep patent families, source snapshots, brief/template variants, and
  organization identity as separate grouping dimensions. Near-duplicate
  states from one family/change curriculum must not leak across splits.
- Create evaluator-only expected outputs and source witnesses in the curator
  layer later; do not expose them to the agent packet. Their construction and
  review are outside this offline prototype run.

## Measurements

Primary engineering-facing measurements:

- **Factual support:** fraction of source-backed claims/routes whose evidence
  IDs and locators resolve and whose integrity checks pass; record unsupported
  values and false-unknowns separately.
- **Policy errors:** per-option false pass, false fail, scope leakage, and
  route-local unknown errors under explicit policy changes.
- **Unaffected-field preservation:** fraction of fields/evidence/routes that
  remain byte/record-equivalent when an unrelated project name, policy scope,
  or source event changes; report affected and preserved fields, not only a
  single score.
- **Unknown handling:** count scoped unknowns, unsupported values, missing
  evidence blocks, and whole-pack overblocking.
- **Cost:** per episode calls, input/output tokens, retries, latency, provider
  cost, local compute time, and memory/processing cost where measured. Failed
  attempts and repair calls count toward the same budget.

Secondary diagnostic measurements may include route coverage, traceability
completeness, output schema failures, and time to produce a reviewer-readable
handoff. These are engineering diagnostics, not proof of clinical or
scientific correctness.

## Pilot design constraints

- Pair methods on the same current packet and event sequence.
- Keep **within-project revision** (the same project after a policy or evidence
  change) separate from **cross-project learning** (transfer to a different
  project or organization). This G09/G10 slice only exercises the former; it
  does not implement or measure cross-project learning.
- Keep source family, organization profile, brief/template, and change
  curriculum grouping visible in the run record.
- Use deterministic validators and identical evidence opportunities for every
  comparator.
- Preserve intentionally failing cases, retries, exclusions, and blocked
  inputs in the report; do not remove hard cases because they lower a score.
- Separate development tuning from any later held-out evaluation. The current
  three-case offline run is development evidence only.
- Do not use owner review, LLM/NLI scoring, or a real quote as independent
  clinical/legal/scientific gold.

## Decision rule: complexity versus simple baseline

Continue with a more complex method only if a pre-specified pilot summary
shows a material improvement in the target error/preservation trade-off over
the simple rule/direct-revision baselines, with measured cost and failure rate
within the approved ceiling, and without leakage or unsupported claims.

If the deterministic path matches the proposed method on the meaningful
engineering measures, or if complexity adds cost/retries without a robust
improvement, simplify the product and reduce the algorithmic claim. If results
are inconclusive because of coverage, family leakage, or unresolved evaluator
quality, mark the pilot inconclusive and prepare the missing data/contract
before choosing a winner. No winning outcome is assumed in advance.

## Current evidence and non-goals

Current offline evidence is limited to the G09/G10 bounded slice and a new
caller-supplied two-state synthetic workflow. It demonstrates schema
validation, source/integrity gating, route generation, scoped policy change,
unknowns, typed SQLite read-back, and JSON/Markdown/HTML export.

It does not establish scientific utility, clinical/regulatory/legal validity,
patentability/FTO, generalization, cost advantage, or AI superiority. It does
not implement G11 dependency repair or G12 cumulative learning. No paid API,
model, GPU, RunPod, or main benchmark was run.

## Readiness gate and next action

Engineering gate for this round: targeted tests pass, negative methods are
detected, new schema-valid input runs without case-ID lookup, changes preserve
unaffected fields, and generated reports contain measured results. This gate
is satisfied locally as documented in the G09/G10 handoff.

Scientific pilot gate remains open until data coverage, split/grouping,
validator/evaluator quality, provider/model version, and budget are explicitly
frozen and approved. The next action is Pepo's targeted review of this code,
tests, reports, and readiness document; no commit/push or paid pilot follows
automatically.
