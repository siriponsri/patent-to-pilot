# HT-T2 SciFact report

## Objective and scope

Verify that the local SciFact wrapper matches the pinned upstream evaluator on valid prediction semantics, while preserving the stricter local input contract and the separation between runtime inputs and evaluator labels.

## Source matrix

| Source | Revision/hash | Use | Boundary |
|---|---|---|---|
| Local SciFact release | Registry `scifact-release-20261027-r1`; archive SHA `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be` | Local format/count/hash receipt | No public test labels; no held-out score |
| Official evaluator code | Commit `68b98a56d93e0f9da0d2aab4e6c3294699a0f72e`; `data.py` SHA `90d1c0d6c52a78c2893f13906095de544f8b3218965fe0bf1e7d874622732ce8`; `metrics.py` SHA `b8669a1d36a05c76d2f5a06691cde4c4d81b939f42edd37b6703b58b6ee9946d` | Differential reference | Public Apache-2.0 code used temporarily, not staged |
| Local wrapper | `src/patent_to_pilot/evaluation/healthtech/scifact.py` SHA `fbbe881297d979fc057c882c1f2284d4faaea02537d850a6af089225d0774ff0` | Candidate implementation | Component evaluator only |

## Results

Three authored valid cases passed exact parity across abstract label-only, abstract rationalized, sentence selection, and sentence label metrics:

- `exact_single_rationale`: all metrics `1.0`
- `partial_and_false_document`: abstract F1 `0.5`; sentence selection/label F1 `0.22222222222222224`
- `wrong_label_and_empty_evidence`: all F1 values `0.0`

The receipt retains official and local precision/recall/F1 values for every metric. Equality here is evaluator parity, not a model-quality result.

## Claim/evidence ledger

| Claim | Evidence | Status |
|---|---|---|
| Local release is the pinned SciFact snapshot | `scifact-release-receipt.json` and registry manifest hashes | PASS |
| Local wrapper matches upstream valid-input metric semantics | `receipt.json`, 3/3 parity cases and 4/4 metrics per case | PASS |
| Local malformed-input guards are no weaker than upstream | Existing strict validation tests; differential scope is valid inputs only | PASS_WITH_SCOPE |
| Official held-out test score is reproduced | Public release omits test labels | NOT_RUN / NOT_ESTIMABLE |
| SciFact result establishes patent-device entailment or clinical truth | Outside task scope and unsupported by this receipt | NOT_SUPPORTED |

## Limitations and next test

The upstream evaluator accepts some malformed or out-of-range structures that the local wrapper rejects; those are intentionally reported as local contract hardening, not upstream parity. The next useful offline step is a frozen HT-T2 evaluator manifest with declared prediction source, split, missing/unknown-ID handling, and denominator before any component score is reported. Keep SciFact separate from HT-T1 known-link retrieval and from product claims.
