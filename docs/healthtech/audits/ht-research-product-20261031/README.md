# HealthTech research-product long run — 2026-10-31

Status: `PASS_O2_FULL_ENCODING_EVAL_DEVICE_DOSSIER_E2E_QWEN3_LOCAL_GENERATION_API_COMPARISON_BLOCKED_LOCAL`

This is the canonical continuation record for the bounded O1–O4 package. The
private remote job root is owned by this run; model weights, runtime JSONL and
returned vector shards stay outside Git. This folder stores only sanitized
provenance, hashes, command outcomes and continuation state.

## Scope

- O1 local HTTP jobs/history/export is implemented and previously accepted.
- O2 PatEmbed-base and multilingual-e5-base are downloaded and hash-recorded
  on Windows; controlled transfer to `dr-train` is present.
- The old ONNX MiniLM backend remains a historical control. It is not relabeled
  as PatEmbed or e5.
- The current implementation adds a direct Transformer backend that validates
  SentenceTransformers module layouts, applies PatEmbed prompt policy or e5
  query/passage prefixes, returns 768-dimensional little-endian float32
  vectors, and preserves the existing resumable vector-bundle contract.

## Frozen model inputs

| Model | Revision | License | Windows manifest |
|---|---|---|---|
| `datalyes/patembed-base` | `244ba452908a3093be11efb8a44396652317fb14` | `cc-by-nc-sa-4.0` | `permitted-local-storage:models-v1/manifest.json` |
| `intfloat/multilingual-e5-base` | `d128750597153bb5987e10b1c3493a34e5a4502a` | `mit` | same manifest |

Windows model manifest SHA-256: `fc8df4227c41efc25d5eac7f4c4c2d0f533c8fd90f4b033e02fc506eb900ce78`.

PatEmbed is required to use Transformer → masked mean pooling → the released
1024→768 bias-free Dense projection → L2 normalization. e5 is required to use
masked mean pooling → L2 normalization with `query: ` and `passage: ` role
prefixes. Prompt policy for this run is the predeclared PatEmbed
`retrieval_MIXED` prompt, recorded in each vector manifest config.

## Remote boundary

- Host: `dr-train` (`chaw@100.77.149.83`), strict host-key/authentication
  checks, batch mode, agent forwarding disabled.
- Approved GPU UUID: `GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089`.
- Private job root: `permitted-remote-job-root:research-product-o1-o4-20261031`.
- Runtime inputs transferred: DAPFAM `corpus.jsonl`, `queries.jsonl`, the
  runtime-only `manifest.json`, and a separate 41-patent / 3-query Abbott
  device runtime pack; no qrels, labels, gold, disclosure relations, or
  hidden evaluator fields were transferred.
- Resource bounds remain CPU ≤8 threads, RAM ≤32 GiB, one approved GPU,
  concurrency 1, and combined Windows+remote additional disk ≤40 GiB.

## Current engineering evidence

- Base branch state: `codex/research-product-o1-o4-20261031` at `257037a` before
  this uncommitted encoder patch.
- Local baseline: `tests/test_healthtech_vector_artifacts.py` and
  `tests/test_healthtech_vector_eval.py` passed `10/10` before the patch.
- Current focused checks: transformer contract, vector artifacts, and vector
  evaluation tests pass `15/15`; compile checks pass.
- Remote self-checks passed at `2026-10-31T02:47:31Z` (PatEmbed) and
  `2026-10-31T02:47:40Z` (e5): one visible Tesla V100, Torch
  `2.8.0+cu128`, 8 Torch threads, 768-dimensional `<f4` output, and L2 norms
  within float tolerance of 1.0.
- Corrected remote canaries passed with injected interruption/resume for both
  models. PatEmbed bundle manifest SHA-256 is
  `70026eba06fee6b1e5640e42d775830370179eca6fd4006a6576de676a2d1ec6`; e5
  bundle manifest SHA-256 is
  `4e7335a7b47ad3de988d8609b68ce80bc1b11cbd980e53f9ecc7cfdfb858f895`.
  Each bundle has 64 rows, two shards, and dimension 768. The same bundles
  were imported successfully on Windows.
- Full DAPFAM encoding completed for both models: 45,336 passages in 10
  shards and 1,247 imported query vectors per model. Remote validation and
  Windows import passed with matching manifest hashes.
- Matched DAPFAM evaluation completed for 1,247 queries and 49,869 qrel pairs
  with zero dense failures. PatEmbed dense Recall@100 is 0.422525 macro /
  0.422319 micro; e5 is 0.287414 macro / 0.287296 micro. BM25 is identical in
  both runs at 0.214225 macro / 0.213928 micro. Full metrics and input hashes
  are in `REPORT.md` and `verification.json`.
- A separate 41-patent Abbott runtime corpus was encoded on `dr-train` for
  MitraClip, Tendyne, and TriClip. Imported PatEmbed and e5 bundles powered
  six real local dossier-engine runs with one search call per case, no vector
  errors, zero provider calls, and USD 0.00 paid cost.
- The frozen local Qwen3-8B evidence-pack generation passed for MitraClip,
  Tendyne, and TriClip: 3/3 outputs were schema-valid, with zero provider
  calls and USD 0.00 paid cost. The pinned revision, pack hash, output hashes,
  token counts, resource metrics, and formal allocation boundary are recorded
  in `docs/healthtech/audits/ht-o3-local-model-preflight-20261031/`.
- The Qwen3-8B versus `qwen/qwen3-32b` API comparison remains `BLOCKED_LOCAL`
  and `NOT_RUN`. Historical OpenRouter receipts reconcile to cumulative actual
  debit USD 0.0001464 with zero unknown-pending attempts, and public Qwen3-32B
  route/pricing metadata was refreshed without credentials. The paid gate stays
  closed only because canonical ledger identity, current account credit,
  outbound dossier-prompt rights, and fresh route/parameter checks are
  unresolved. The original USD8 owner scope already approves one local
  generator plus one API generator. See `o3-gate.json`.

Offline O3 engineering preparation is complete: the canonical ledger registry,
mock namespace, rights-cleared payload manifest, API runner, and
candidate/disclosed-link validation are implemented and covered by focused
tests. This does not count as a paid comparison or research completion.

## Completed O2/O4 evidence

- DAPFAM runtime hashes: corpus
  `3e67817b72f372171b116a53369b7fefd996482261938f85ff647b3d0cad3252`, queries
  `006c76d67dc1fcdab0cb937be1b8af752e71408dba875e3a512c553c2bd575c4`, qrels
  `e51ae4e13abee0fc7523560ecddd272bc85dc98befc8ab4466155a0c2d2d4f74`.
- Full PatEmbed manifests: corpus
  `db5196ef239d79ef7a108f2c596881308e3f52e832c5bad136a244631af2abcd`, queries
  `6bacd6b8def0906101157c8c1ff80bab8fe05d1c416f18c554832abcdfaef8d0`.
- Full e5 manifests: corpus
  `94b2246b19cf481842cfd85a2757745c6f52c867b23030485778e8710adb1089`, queries
  `53342cbfd55387aa2de07c5c487a75f627eced243e87324b6eb1f7db4449c9ac`.
- Device runtime hashes: corpus
  `5965b7b51006d9d64d05250848300dee68d80a0b69324213a5ccac25a1c44e9d`, queries
  `7e0e29b6b7e8f19dcbd28c775e8b518255b5fdcfa0846307acb5dd7f5b1381a8`.
- Device bundle manifests: PatEmbed passage
  `75348afa4fede2535c09970d70353ecf9477f306a48fa46c71a445677f2302f1`, query
  `45da46ee7dbd755f8ca8dd4c244ff6b9063f16253c27907e92ff0291c61c7e54`; e5
  passage `643ab8856a1bcd72d2c2e4745d02bdfe46bed0190f16ab8834c3870249fdcc7b`,
  query `8e0a933f34c26a7f1370809c5220911cf6ed1b318bd02e7b4b60cc25ce76494c`.
- The device run uses the existing dossier engine and `PrecomputedVectorRetriever`;
  it is a product-path engineering check, not semantic relevance gold or a
  claim that any dense rank is a disclosed link.

## Evidence boundaries

Engineering PASS does not establish semantic device-patent relevance,
clinical suitability, regulatory approval, FTO, patent validity, exhaustive
recall, commercial redistribution rights, or publication readiness. DAPFAM
evaluation remains a citation-based diagnostic; unlisted pairs stay unjudged.
The three Abbott cases remain development-only, product-level disclosure
references; the compatibility view used for this run was derived from the
unchanged local cohort snapshot and was not published or staged.

## Recovery notes

The first canary launch stopped before model inference because the minimal
remote source transfer imported package initializers whose unrelated API and
repository modules were not transferred. The remote-only staging package was
repaired with no-op initializers; no repository source was changed for this
packaging issue. The corrected canary then passed with the intended injected
shard interruption and resume.
