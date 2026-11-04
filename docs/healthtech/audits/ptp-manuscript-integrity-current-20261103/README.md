# Current-head manuscript integrity checkpoint — 2026-11-03

This audit checks the manuscript against the current Patent-to-Pilot candidate
without rerunning the scientific benchmark or mixing historical receipts into
the current result. It is a documentation and evidence-binding check for the
existing O4 research package.

## Result

The manuscript is bound to candidate `88dc40471cb9078f929c02bb893cfa1e364da841`
and has SHA-256
`ac1a4396d1f0274007fca8e74d44115c330eddd53947f177b915576278600347` with
44,193 bytes. All 34 relative repository links resolve; no missing local link
was found.

The manuscript contains the current-head offline frontier values, the
post-hoc first-action budget diagnostic, the PatEmbed/multilingual-e5 component
diagnostic, the current PANORAMA component metrics, and the business-value
scenario inputs. It also states the required limitations: product-level
disclosed links are not semantic gold, unjudged pairs are not negatives, the
main cohort has no final holdout, realized budgets are not equalized, paid API
comparison is not run, and external business validation/revenue/ROI are not
claimed.

## Bound receipts

- Offline frontier: `ptp-current-head-offline-20261103/verification.json`
- Matched-budget diagnostic: `ptp-current-head-matched-budget-20261103/verification.json`
- PANORAMA component revalidation: `ptp-panorama-current-head-20261103/verification.json`
- Business-value scenario: `ptp-business-value-scenario-20261103/verification.json`

The receipt hashes and candidate binding are recorded in `verification.json`.
Older manuscript hashes in historical progress entries remain historical and
are not treated as the current manuscript.

## Decision

`PASS_CURRENT_HEAD_CLAIM_AND_LINK_RECONCILIATION`.

This does not upgrade O4 to a confirmatory scientific result. The final
holdout, semantic relevance gold, equal-total-budget adaptive comparison, paid
model comparison, independent user validation, and owner submission review
remain separate requirements.
