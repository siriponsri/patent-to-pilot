# HT-M16 local semantic-review task export

- Run ID: `luna-long-run-20261029-m16-review-tasks-20261029`
- Date: `2026-10-29` (Asia/Bangkok)
- Status: `PASS_OFFLINE_REVIEW_TASK_EXPORT`
- Base commit: `dd1cecd1d7295f3ffcf53dabfd781f8f20e98dae`
- Tested code commit: `23acfd468570ea2eac47d0f5790b7362268aa2d1`
- Parent packet: `../luna-long-run-20261029-m15-rights-packet-20261029/README.md`

## Objective and scope

This package adds a deterministic local-only task exporter for the corrected 11-query/31-patent semantic-review packet. It prepares reviewer-visible metadata and empty response fields without creating labels, copying patent text, exposing evaluator split/family metadata, or opening provider transfer.

## Outcome

The new `review_tasks.py` module validates the upstream unlabeled packet, creates deterministic `HT-REVIEW-000001` through `HT-REVIEW-000341` rows, and fails closed if any packet row is labeled, any response is prefilled, or forbidden patent/evaluator fields appear in the reviewer-visible task. The CLI writes separate `manifest.json` and `tasks.jsonl` artifacts.

The real Philips-expanded export contains:

| Measure | Result |
|---|---:|
| Queries | 11 |
| Patents | 31 |
| Tasks/pairs | 341 |
| Prefilled responses | 0 |
| Semantic labels | 0 |
| Forbidden metadata/text hits | 0 |
| Provider calls | 0 |
| Paid cost | USD 0.00 |

Reviewer-visible tasks retain device/patent metadata, source revision/hash, source date, URL, and empty response fields. They omit split, company-group, frozen-group, family, product-disclosure, evaluator, abstract, claims, text, and copied content fields. The output is marked `LOCAL_REVIEW_ONLY`.

## Verification

```text
rtk proxy python -m pytest -q tests/test_healthtech_review_tasks.py tests/test_healthtech_review_packet.py
rtk proxy python -m py_compile src/patent_to_pilot/evaluation/healthtech/review_tasks.py scripts/healthtech/build_review_tasks.py tests/test_healthtech_review_tasks.py
rtk proxy python -B scripts/healthtech/build_review_tasks.py --packet results/healthtech/ht-relevance-review-20261029-r2-philips/packet.json --output results/healthtech/ht-relevance-review-tasks-20261029-r1
rtk proxy python -c "<source-path setup>; validate manifest.json and tasks.jsonl"
```

The focused test command passed 11 tests, the compile command exited `0`, and the real exporter returned `PASS` with 341 tasks, zero responses, and zero semantic labels. The first standalone validation attempt omitted the checkout's `src` path and failed before reading the generated task data; the corrected source-path validation passed with zero forbidden hits.

## Evidence and hashes

- Input packet: `results/healthtech/ht-relevance-review-20261029-r2-philips/packet.json`; SHA-256 `21df358e9b1f387d4b4f1a6c33c94e38abff7ccf15b39df746fba3acec05a206`.
- Task manifest: `results/healthtech/ht-relevance-review-tasks-20261029-r1/manifest.json`; SHA-256 `bf4ee05fc76f26f5be891866843e7f4a24a01d0fab8249c9db8c339ce09ce6d6`.
- Task rows: `results/healthtech/ht-relevance-review-tasks-20261029-r1/tasks.jsonl`; SHA-256 `7274129bd3cbe01449ae046e75c89b9d099aa4f78311e3b8db69ed9ab7382d8c`.
- `src/patent_to_pilot/evaluation/healthtech/review_tasks.py`: `37b7ef46982bf5bdf9e904d74e374622a80a5926fba8f58a68416c2f6503b9fb`.
- `scripts/healthtech/build_review_tasks.py`: `fab43312e88c8b6d08978ee0bb9e34770ba68717f17d4b98f61c8bf13ffd0687`.
- `tests/test_healthtech_review_tasks.py`: `499ce54cbdd1add8c38b7f8f7c8da1ba63e6f7cbeb3f03fa4a8e89c3d1655eba`.

## Rights and limits

The task pack is local-review preparation, not a judgment source. It does not grant semantic-label rights, provider-transfer rights, public redistribution rights, clinical/FTO authority, patent-validity authority, or publication readiness. Philips marking material and Google-derived patent text remain local-only. The Stryker final holdout remains untouched, and absent pairs remain `UNJUDGED` rather than negative.

No paid inference, live provider request, external reviewer contact, semantic adjudication, statistical significance test, user study, or commercial validation occurred.

## Handoff

The next information-gaining step is an authorized, rights-cleared reviewer submission that binds each explicit label to source revision/hash, locator, basis, and adjudicator role. Ingest it through `ht-relevance-judgment-cohort-v1` without changing the frozen 341-pair denominator or holdout. Keep paid HT-B4, Bridge, deployment, outreach, and Claude UX/UI paused.
