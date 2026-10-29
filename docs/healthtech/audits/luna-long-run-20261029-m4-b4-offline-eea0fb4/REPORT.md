# HT-B4 offline controller report

## Objective and scope

The remaining engineering gap after HT-M4-R1 and the M3 cross-cohort receipt was a bounded HT-B4 controller seam. This package implements the smallest inspectable controller contract and runs it offline on the already frozen Abbott and Boston Scientific public disclosure cohorts. The run is intended to validate action/state boundaries and resource accounting, not to close the HealthTech study.

Inputs were the frozen runtime manifests, evaluator-only reference files, exact-patent group files, and the existing local model cache under `data/raw/healthtech/models`. The controller did not read evaluator references until runtime predictions and raw rankings had been written.

## Controller contract

The controller sees only structured retrieval observations: query ID, step/call/candidate budgets, source availability, available/used feature indices, last new-candidate count, lexical/dense disagreement, and the last action. The response schema is strict and permits only:

- `technical_search` at step zero;
- `feature_search` for one currently available feature index; or
- `stop`.

Hard budget exhaustion, source unavailability, step caps, repeated feature use, unsupported feature indices, and extra response fields fail closed. The deterministic offline policy stops on no novelty or a high-yield low-disagreement prefix and otherwise requests the next declared feature.

## Observed results

Boston WATCHMAN produced two completed queries. Each used the shared technical prefix and stopped after the first retrieval because the seven-patent universe was fully returned; the run recorded two query calls, fourteen returned candidates, four controller steps, and macro/micro recall of `1.0` at `K=20`. The score is ceiling-limited by the small universe.

The Abbott slice produced three completed queries. MitraClip and TriClip used one feature follow-up before stopping for low novelty; Tendyne stopped after the technical prefix. The run recorded five query calls, 205 returned candidates, eight controller steps, and macro/micro recall of `0.49880241951853205` / `0.47540983606557374` at `K=20`. Exact-patent group recall was `0.3364389233954451` for the MitraClip/TriClip group and `0.8235294117647058` for the Tendyne group.

The first technical query in each cohort matched the fixed HT-B1/B2/B3 prefix. All per-device statuses were `completed`; no source-frontier failure occurred. The controller schema hash was stable across both runs: `e4c9c57ca91573cc3a883ccc978273db732c01d6b26e1997324a1c59f427384f`.

## Evidence interpretation

The evidence supports an engineering claim: the bounded offline controller can select from a constrained action set, preserve raw attempts, record local resource usage, and maintain runtime/evaluator separation on two frozen cohorts. It does not support a scientific claim that adaptive acquisition improves recall, reduces cost, generalizes across companies, or represents an LLM controller. No independent final holdout exists, and the declared disclosure relationships are not expert semantic relevance labels.

## Next discriminating test

Acquire or construct a rights-cleared cohort with multiple independent company and family groups, freeze the query/universe/split/denominator protocol, and define the HT-T2 prediction manifest before scoring. Then compare the offline deterministic policy with fixed HT-B2 and simple HT-B3 controls under the same failure and resource rules. A live or paid HT-B4 run remains outside the current authorization until OpenRouter metadata, approved credential/credit, transfer rights, payload bounds, and reconciliation gates are evidenced.
