# HT M32 adversarial boundary regression

- Run ID: `luna-long-run-20261030-m32-adversarial-boundary-regression-20261030`
- Date: `2026-10-30`
- Base commit: `b602311a018e479d894db7c33d9662961a857940`
- Status: `PASS_ENGINEERING_ADVERSARIAL_REGRESSION`
- Source change: `tests/test_healthtech_boundary_matrix.py`

## Scope

Added a current-head regression for the external rights boundary after history reload. The fixture combines a nested restricted payload (`openfda`) with an encoded restricted value in a reviewed-field evidence item, then checks both values across English and Thai Markdown, redistribution JSON, and purpose-aware source view.

The regression preserves the intended projection: only the reviewed `trade_name` field is exported, the nested field is omitted, the encoded evidence is rebuilt from the source payload, and a direct unreviewed field request fails closed.

## Verification

- Focused HealthTech suite: `106 passed`, `0 failed`; one pre-existing `fitz` deprecation warning.
- Compilation: `rtk proxy python -B -m compileall -q src scripts tests` exited `0`.
- Diff check: `rtk git diff --check` exited `0`.
- Provider/network calls: `0`.
- Semantic labels or restricted payload acquisition: `0`.
- Paid cost: `USD 0.00`.

## Limits and next action

This closes additional regression coverage for the already repaired F1 boundary. It does not create semantic device–patent gold or change the M30 cohort, denominator, holdout, family groups, or `UNJUDGED` policy. Bridge, live HT-B4, Zenodo record `21101400`, deployment, outreach, clinical/FTO work, public raw-data release, and Claude UX/UI remain blocked or paused.

Next: obtain owner-authorized rights-cleared semantic judgment data, validate it through M23, stage it through M25, ingest it through M24, and rerun the frozen HT-B0a/B0b/B1/B2/B3 controls without changing the frozen denominator or holdout.

