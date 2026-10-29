# HT-T2 SciFact lexical development score

- Run ID: `luna-long-run-20261029-ht-t2-lexical-dev-20261029`
- Status: `PASS_COMPONENT_SCORE_DEV_ONLY`
- Scope: deterministic offline SciFact component baseline on the pinned local development split
- Provider calls: `0`; paid cost: `$0`
- Source head before this package: `393ce5bc7b6328abf9998c4cc377dfb720c4ab6a`
- Final source head: `d66dbbd`

This package adds a reproducible HT-T2 prediction source and evaluator-only scoring
command. The generator reads the corpus and a runtime projection containing only
claim IDs and claim text. The scorer loads `claims_dev.jsonl` only after the
prediction artifact exists, then applies the strict local SciFact evaluator.

The run covers all 300 claims in the pinned development split over 5,183 corpus
documents. It writes 300 prediction rows and all 300 rows contain lexical
evidence. The result is a component development score only. It is not an official
hidden-test score, patent-device gold, clinical truth, or evidence of an adaptive
method.

Inspectable details are in [`REPORT.md`](REPORT.md), machine-readable checks are in
[`verification.json`](verification.json), and the continuation decision is in
[`NEXT_ACTIONS.md`](NEXT_ACTIONS.md).
