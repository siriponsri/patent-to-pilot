# O2/O4 research-product report — 2026-10-31

This report records the completed offline/remote engineering package for the
transformer vector path and the three named-device dossier checks. It does not
claim semantic medical-device/patent gold, exhaustive recall, clinical/FTO,
patent validity, investment merit, or publication readiness.

## DAPFAM matched diagnostic

Frozen inputs are 45,336 runtime corpus rows, 1,247 runtime query rows, and
49,869 qrel pairs. Rankings use `k=100`, RRF `k=60`, the imported passage and
query bundles for each model, and the existing failure denominator: failed or
missing queries remain in the macro denominator and unlisted pairs remain
unjudged.

| Method | Macro Recall@100 | Micro Recall@100 | Macro nDCG@100 | Dense failures |
|---|---:|---:|---:|---:|
| BM25 | 0.214225 | 0.213928 | 0.192397 | 0 |
| PatEmbed dense | 0.422525 | 0.422319 | 0.348830 | 0 |
| PatEmbed RRF | 0.377698 | 0.377472 | 0.311402 | 0 |
| multilingual-e5 dense | 0.287414 | 0.287296 | 0.244781 | 0 |
| multilingual-e5 RRF | 0.282910 | 0.282643 | 0.244754 | 0 |

The BM25 row is repeated across both model runs because the corpus/query/qrel
inputs and lexical implementation are identical. This is a diagnostic over
the DAPFAM citation-based family retrieval labels, not semantic device-product
relevance gold.

## Device dossier E2E

The separate Abbott runtime pack contains 41 patent documents and three named
device queries: MitraClip, Tendyne, and TriClip. Imported vectors were passed
through `PrecomputedVectorRetriever` into the existing dossier engine.

| Model | Device | Candidates | Dense-backed candidates | Errors |
|---|---|---:|---:|---:|
| PatEmbed | MitraClip | 35 | 33 | 0 |
| PatEmbed | Tendyne | 35 | 33 | 0 |
| PatEmbed | TriClip | 41 | 41 | 0 |
| e5 | MitraClip | 33 | 33 | 0 |
| e5 | Tendyne | 33 | 33 | 0 |
| e5 | TriClip | 41 | 41 | 0 |

Each case completed one bounded technical search and stopped with
`fixed_schedule_complete`. The two mitral-device queries share the declared
lexical technical description (`mitral valve`) in the current Abbott adapter;
their identical dense query vectors are therefore expected under this fixture.

## Generation comparison gate

The local Qwen3-8B branch is `PASS_LOCAL_QWEN3_FROZEN_PACK_GENERATION`.
The pinned revision `b968826d9c46dd6066d109eabc6255188de91218` processed the
frozen local-research pack for MitraClip, Tendyne, and TriClip; all 3/3 outputs
were schema-valid. The generation receipt records prompt/output token counts,
latency, output hashes, resource metrics, zero provider calls, and USD `0.00`
paid cost. Formal remote allocation remains
`UNKNOWN_NOT_GRANTED_RESOURCE_OBSERVATION_ONLY`.

The Qwen3-8B versus `qwen/qwen3-32b` OpenRouter comparison remains
`BLOCKED_LOCAL` and `NOT_RUN`. The preserved Phase A and paired-revalidation
receipts reconcile to USD `0.0001464` cumulative actual debit with zero
unknown-pending attempts. The public Qwen3-32B endpoint snapshot at
`2026-10-31T03:51:43.8254719Z` lists three routes: DeepInfra at USD `0.08` /
`0.28` per million prompt/completion tokens, Tenstorrent at USD `0.14` /
`0.40`, and SiliconFlow at USD `0.14` / `0.57`. This is public catalog
metadata only; it does not establish account credit, billing state, or a route
  choice. The original USD8 owner scope already approves one local generator
  plus one API generator. The API comparison remains closed because a single
  canonical ledger identity, current account credit, outbound dossier-prompt
  rights, and fresh route/parameter checks are unresolved. No provider request
  or paid cost occurred in this package. See `o3-gate.json` and the local
  generation receipt.

Offline preparation for this branch is now engineering-complete: the existing
owner scope is recorded as approved, all live callers resolve through one
per-user canonical ledger registry, mock ledgers use a separate namespace, and
the runner reserves before dispatch with exact route, payload, and per-attempt
bound checks. The paired payload builder emits a sanitized manifest and rejects
raw source payloads, unresolved remote rights, hidden candidate references,
and candidate-to-`disclosed_link` classification drift. The API runner is
covered by dry-run and mock tests; it has not sent a paid request.

## Reproduction anchors

- Canonical audit: `docs/healthtech/audits/ht-research-product-20261031/`.
- PatEmbed evaluation: `results/healthtech/ht-transformer-eval-20261031-patembed/`.
- e5 evaluation: `results/healthtech/ht-transformer-eval-20261031-e5/`.
- Local Qwen3-8B generation receipt: `docs/healthtech/audits/ht-o3-local-model-preflight-20261031/generation-canary.json`.
- Frozen evidence-pack contract: `docs/healthtech/audits/ht-o3-local-model-preflight-20261031/evidence-pack-contract.json`.
- Remote job root: `permitted-remote-job-root:research-product-o1-o4-20261031`.
- Code revision used by the runs: `257037ab349ec88e5600c074deccfc8a62fe5fc2`.
- Full repository regression suite: exit `0`; one existing optional tokenizer
  skip and two warnings.
