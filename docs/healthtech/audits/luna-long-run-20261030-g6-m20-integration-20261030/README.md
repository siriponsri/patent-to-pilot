# HT-M21 G6 M20 sensitivity integration

- Run ID: `luna-long-run-20261030-g6-m20-integration-20261030`
- Run date: `2026-10-30` (Asia/Bangkok local execution)
- Status: `PASS_REPORT_INTEGRATION`
- Parent evidence: `luna-long-run-20261030-company-holdout-sensitivity-20261030`
- Source head before edit: `4e1210ae2a5a08ec40036b4ac31d6e25d3c13b57`
- Implementation commit: `aaecb92` (`docs(healthtech): integrate M20 sensitivity into G6`)

## Scope

This package integrates the already-completed M20 company-holdout sensitivity
results into the G6 manuscript methods skeleton. It adds the four held-out
company rows, the frozen cohort counts, the zero-cost/offline execution facts,
and explicit limits that keep product-level known-link recovery separate from
semantic relevance, generalization, and publication claims.

No new retrieval run, provider call, data acquisition, label creation, or
external transfer occurred in M21. The section is bound to the canonical M20
audit rather than recomputing or reinterpreting its scientific outputs.

## Outcome

G6 now records M20's macro known-link Recall@20 rows for Boston Scientific,
Stryker Neurovascular, Cook Medical, and Philips Image Guided Therapy over the
same `11`-device, `31`-patent, `38`-disclosed-pair composite. It states that
the four rows reuse the same local corpus and are not independent samples,
that unlisted pairs remain unjudged, and that the result is descriptive
sensitivity evidence only.

## Verification

- Focused G6 regression: `2 passed`.
- Adjacent report/analysis/holdout regressions: `8 passed`.
- Targeted Python compilation: exit `0`.
- `git diff --check`: exit `0`.
- Provider calls: `0`.
- Network acquisition: `0`.
- Paid cost: `USD 0.00`.
- Changed files committed: G6 skeleton and its focused regression only.

Exact commands and hashes are in `verification.json`.

## Boundaries

M21 does not create semantic gold, convert product disclosures into relevance
labels, establish exhaustive recall, prove method superiority, support pooled
statistical inference, or unlock live HT-B4. The rights-cleared semantic
judgment source, final semantic holdout, clinical/FTO review, deployment,
outreach, public raw-data release, and Claude UX/UI remain outside this
package.

## Next action

Obtain or authorize the rights-cleared semantic device-patent judgment source
with explicit `relevant` / `not_relevant` labels, source revision and SHA-256,
rights/intended-use decisions, adjudicator role, exact locators, multiple
independent company/family groups, and a predeclared untouched holdout. Apply
`ht-relevance-judgment-cohort-v1` without changing the frozen denominator or
unjudged policy, then rerun HT-B0a/B0b/B1/B2/B3.
