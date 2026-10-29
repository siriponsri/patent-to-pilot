# Semantic review task export

Status: `PASS_OFFLINE_REVIEW_TASK_EXPORT / LOCAL_REVIEW_ONLY / NOT_GOLD`.

The exporter at `scripts/healthtech/build_review_tasks.py` converts the frozen unlabeled review packet into deterministic reviewer-visible task rows. It preserves device/patent identifiers, titles, source revisions, source hashes, source dates, and source URLs, but excludes patent text, family IDs, split/group metadata, product-disclosure flags, evaluator relations, and semantic labels.

## Input and output

- Input packet: `results/healthtech/ht-relevance-review-20261029-r2-philips/packet.json`.
- Output directory: `results/healthtech/ht-relevance-review-tasks-20261029-r1/`.
- Output files: `manifest.json` and `tasks.jsonl`.
- Task count: `341`.
- Response count: `0`.
- Semantic label count: `0`.
- Distribution: local review only; no provider transfer and no public redistribution.

Each task contains a named device, one patent metadata row, an exact source locator/hash, and an empty response object. The response schema reserves fields for `label`, `basis`, source identity/hash, locator, adjudicator role, and notes, but every field is `null` until an authorized judgment source is available.

## Reproduction

```text
rtk proxy python -B scripts/healthtech/build_review_tasks.py --packet results/healthtech/ht-relevance-review-20261029-r2-philips/packet.json --output results/healthtech/ht-relevance-review-tasks-20261029-r1
```

Validate the generated task pack with `PYTHONPATH=src` or the equivalent source-path setup used by this checkout. The exporter revalidates the upstream packet before writing and refuses labeled, partially judged, or structurally incomplete input.

## Limits

This artifact does not create semantic relevance gold, promote product disclosures, establish patent validity/FTO, or authorize provider transfer. Unlisted pairs remain `UNJUDGED`, and the packet's three-query Stryker holdout remains untouched. Any future reviewer submission must pass `ht-relevance-judgment-cohort-v1` with explicit source rights, revision/hash, locator, basis, and adjudicator role before evaluation.
