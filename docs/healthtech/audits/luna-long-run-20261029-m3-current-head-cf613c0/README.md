# HT M3 current-head freeze receipt

- Run ID: `luna-long-run-20261029-m3-current-head-cf613c0`
- Tested source head: `cf613c08c9eeee340645cd6eb46d2aebe0c983ac`
- Scope: current-head deterministic freeze/evaluator receipt over existing HT-B0a/B0b/B1/B2/B3 outputs
- Verdict: `PASS_OFFLINE_ANALYSIS`
- Provider calls: `0`; paid cost: `$0`

This package reruns the deterministic Abbott/Boston comparison against the pushed
current head using the already-frozen local artifacts. It does not rerun neural
inference, acquire data, or open evaluator references as runtime inputs. The
comparator validates the shared five-method set, primary `K=20`, fixed-prefix
alignment, source hashes, and the rule that cross-cohort score deltas remain
descriptive only.

## Frozen development setting

- Abbott: 3 devices, 41 patents, 61 disclosed pairs, 62 unjudged distractor pairs,
  2 exact-patent groups, 1 company group, no final holdout.
- Boston Scientific WATCHMAN: 2 devices, 7 patents, 13 disclosed pairs, 1
  unjudged distractor pair, 1 exact-patent group, 1 company group, no final holdout.
- Methods: HT-B0a, HT-B0b, HT-B1, HT-B2, HT-B3.
- Primary endpoint: macro known-link Recall@20 on the frozen development artifacts.
- Fixed-prefix alignment: `PASS` for the shared control contract.

The Abbott frontier remains descriptive with low effective group count. Boston is
ceiling-limited because `K=20` exceeds its seven-document candidate universe. The
comparison is not a pooled scientific estimate and does not establish method
superiority, semantic relevance, exhaustive recall, or generalization.

## HT-T2 boundary

The repository contains SciFact evaluator parity receipts but no standalone
current HT-T2 prediction artifact from this long run. Therefore HT-T2 scoring and
any component metric remain `NOT_RUN`; this receipt does not promote evaluator
parity into a score or into patent-device evidence.

Machine-readable comparison data, source hashes, and the generated report are in
[`comparison.json`](comparison.json), [`verification.json`](verification.json), and
[`REPORT.md`](REPORT.md).

## Next action

Add a rights-cleared cohort with multiple independent company/family groups and a
predeclared final holdout, then rerun the same fixed-prefix frontier. Keep the paid
HT-B4 branch `BLOCKED_LOCAL` until all pricing, identity, credit, transfer-rights,
and reconciliation gates pass.
