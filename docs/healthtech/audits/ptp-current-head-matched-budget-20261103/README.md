# Current-head matched-budget diagnostic

This audit records a post-hoc, descriptive first-action slice from the real
current-head offline development run. It is retained as a bounded diagnostic;
it is not a preregistered final endpoint and does not establish adaptive
superiority.

## Binding

- Goal: reused Patent-to-Pilot O1-O4; no new goal or budget/window was opened.
- Candidate: `88dc40471cb9078f929c02bb893cfa1e364da841`.
- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`.
- Cohort: 3 Abbott cardiovascular devices, 41 patents, 61 product-level disclosed pairs.
- Protocol: `configs/healthtech/g1_g2_public_cohort_protocol.json`, SHA-256 `582e7d9a551f2e4afefa6cec7be26f6c98f2af9fe32ffb4b16bab726b1f32508`.
- Source receipt: private artifact `ptp-current-head-baselines-20261103-r2`, frontier SHA-256 `edf7a0beb84b16434e33b5735e0a95f23eac97f251bacd8c089843e3ae785e42`.
- Source candidate receipt SHA-256: `4bab13befdcac5e195695463da2fcbd06dfc5eb428e07e44dd1e250b748361ba`.

The private raw rankings remain outside Git. Their SHA-256 is
`e21e2a84ff0f8757cae033a1a28d1a3bf3354c5e2f262e37b576a68444e8b5bf`.

## Design and result

The slice selects exactly 3 query calls and 123 rerank pairs from the frozen
frontier and compares HT-B1, HT-B2, and HT-B3 at prefix 1. All three methods
had zero failed queries and zero not-realized queries.

| Method | Prefix | Query calls | Rerank pairs | Macro known-link Recall@20 |
|---|---:|---:|---:|---:|
| HT-B1 | 1 | 3 | 123 | 0.498802 |
| HT-B2 | 1 | 3 | 123 | 0.498802 |
| HT-B3 | 1 | 3 | 123 | 0.498802 |

Observed range: `0.0`. HT-B4 is excluded because controller steps are not
directly comparable to query/rerank units in this receipt. The slice was
selected after the full frontier run and therefore is post-hoc.

## Claim boundary

This result shows only that the three selected first-action rows had the same
observed endpoint under the selected realized resource units. It does not show
that adaptive evidence acquisition improves quality, cost efficiency, dossier
completeness, or business value. The cohort is development-only, has no final
holdout, and uses product-level disclosed links rather than semantic relevance
gold. Historical candidates and Stryker diagnostics are not pooled here.

No API call, reservation, retry, ledger mutation, GPU job, dataset download,
budget reset, or time-window reset occurred for this audit.

## Reproduction and verification

The analyzer is `scripts/healthtech/analyze_matched_budget_prefix.py`. The
machine-readable result is `verification.json`; focused regression output is
`tests.xml` (`6 passed, 0 failed`). The source receipt and current-head offline
verification remain the authorities for the full frontier and are referenced
by hash rather than copied into this audit.

