# HealthTech O1-O4 HTTP/vector package report - 2026-10-31

## Objective and scope

Validate the bounded product/research package for local HTTP jobs, real vector
retrieval, local generation, and adaptive-acquisition reporting. The tested
code candidate is implementation commit
`928729ee1381280cc11d85439e63a71dff91432f`, based on
`cec3cc4cd122dba2e33d5fbea02adfba57b89b32`. The worktree remains an isolated
single-writer branch.

Exclusions: paid inference, outbound dossier prompts, deployment, public
ports, semantic judgment acquisition, clinical/FTO analysis, patent-validity
analysis, and commercial/user validation.

## O1 - loopback HTTP product path

The service keeps the existing dossier engine and adds a fail-closed
server-owned vector binding. The frontend chooses the first available provider,
sends the selected provider id, and records the actual backend provider.

Verified acceptance:

| Surface | Result | Evidence |
|---|---|---|
| Full Python suite | PASS | exit code 0; two existing optional skips; warnings only |
| Frontend unit/contract suite | PASS | `74/74` tests |
| Real Chrome loopback flow | PASS | job start, running cancel, resume/retry, source inspection, history 1->2, reload, JSON/TH/EN export |
| CLI smoke | PASS | `scripts/healthtech/serve_http.py --help` |
| Loopback boundary | PASS | frontend/backend origins are `127.0.0.1`; no live provider calls |

The integration test deferred Windows temporary-directory cleanup after an
`EPERM` retry limit; the acceptance itself exited `0` and all workflow checks
passed. The deferred directory is test scratch state, not a product output.

## O2 - PatEmbed and multilingual-e5 vector retrieval

The new `ht-http-vector-config-v1` binding validates model identity, compatible
encoder configuration, passage/query roles, dimensions, runtime order, query
text hashes, exact query ids, and exact corpus patent ids before a job runs.
Only the exact precomputed query vector bound to the validated runtime query
can be used. The browser receives neither vector paths nor raw vector bundles.

| Model | Revision | License | Corpus manifest | Query manifest | Config |
|---|---|---|---|---|---|
| `datalyes/patembed-base` | `244ba452908a3093be11efb8a44396652317fb14` | `cc-by-nc-sa-4.0` | `75348afa4fede2535c09970d70353ecf9477f306a48fa46c71a445677f2302f1` | `45da46ee7dbd755f8ca8dd4c244ff6b9063f16253c27907e92ff0291c61c7e54` | `d59d00847704185d8a1bc4935e3c0f97267de53bdd60b7c193a80f3521c60c12` |
| `intfloat/multilingual-e5-base` | `d128750597153bb5987e10b1c3493a34e5a4502a` | `mit` | `643ab8856a1bcd72d2c2e4745d02bdfe46bed0190f16ab8834c3870249fdcc7b` | `8e0a933f34c26a7f1370809c5220911cf6ed1b318bd02e7b4b60cc25ce76494c` | `9e87cfb4d8401414261fb2b6f535a89905b81c2c337c8bcdc2548b4773b84daa` |

Both receipts cover the same sanitized runtime inputs: 41 corpus patents, 3
queries, and the ordered cases MitraClip, Tendyne, and TriClip. Device corpus
hash is `5965b7b51006d9d64d05250848300dee68d80a0b69324213a5ccac25a1c44e9d`;
query hash is `7e0e29b6b7e8f19dcbd28c775e8b518255b5fdcfa0846307ac5bdd7f5b1381a8`;
cohort hash is `3abd5cc308b7e69fc3b6055dd6744b0049341164adf9f95e9fa806ff35d0f121`.

For both models: HTTP jobs `3/3` succeeded; dense candidate counts were
`33`, `33`, and `41`; vector errors were `0`; source inspection returned HTTP
`200`; history versions advanced from `1` to `2`; JSON, Thai, and English
exports returned version `2`; provider calls were `0`; paid cost was `$0.00`.
See `patembed-http-receipt.json` and `e5-http-receipt.json`.

The separate DAPFAM diagnostic remains a citation-based retrieval check rather
than semantic device-patent gold. The audited dense Recall@100 values are:

| Diagnostic | Macro Recall@100 | Micro Recall@100 | Macro nDCG@100 |
|---|---:|---:|---:|
| PatEmbed | 0.422525 | 0.422319 | 0.348830 |
| multilingual-e5 | 0.287414 | 0.287296 | 0.244781 |
| BM25 control | 0.214225 | 0.213928 | not used here |

## O3 - local generation and API gate

The frozen evidence-pack run used `Qwen/Qwen3-8B` at revision
`b968826d9c46dd6066d109eabc6255188de91218`, Apache-2.0, with pack hash
`d2a91ce2471461b3e5ed5468e15926e7c2359cb21368323a168f9c8fffbb5932`.
MitraClip, Tendyne, and TriClip all returned schema-valid outputs (`3/3`).
The recorded per-case generation latencies are approximately 33.50s, 34.56s,
and 32.92s. Provider calls and paid cost were zero.

The comparison to `qwen/qwen3-32b` is `BLOCKED_LOCAL` and `NOT_RUN`. Keep the
API branch closed until the canonical cumulative ledger identity, current
account credit, exact route/provider and spend authorization, rights-cleared
outbound prompt manifest, and exact comparison authorization are all recorded.

## O4 - adaptive-acquisition evidence separation

The current report deliberately separates method classes:

| Class | Methods/evidence | Status | Interpretation |
|---|---|---|---|
| Fixed company/lexical controls | HT-B0a, HT-B0b | PASS offline | HT-B0a is the company control; HT-B0b is the BM25 lexical control |
| Fixed hybrid | HT-B1 | PASS offline | Dense + fixed fusion + local reranker; not adaptive |
| Fixed multi-query | HT-B2 | PASS offline | Declared fixed reciprocal-rank query schedule; not adaptive |
| Simple adaptive heuristic | HT-B3 | PASS offline | Observable no-new-candidate continuation/stop heuristic; not an LLM |
| Controller/mock | Offline deterministic controller and HT-B4-MOCK | PASS descriptive / mock-only | Exercises action/accounting contracts; not provider evidence |
| Local generation | Qwen3-8B frozen-pack run | PASS schema integrity | Separate from HTTP job lifecycle and not a semantic judge |
| API generation | `qwen/qwen3-32b` comparison | BLOCKED_LOCAL | No provider request dispatched |

Audited Abbott/Boston offline controller results are descriptive only. Abbott
has 3 devices, 41 patents, macro known-link Recall@20 `0.4988`, micro `0.4754`,
5 query calls, and 0 provider calls. Boston has 2 devices, 7 patents, macro
and micro Recall@20 `1.0000`, 2 query calls, and 0 provider calls. The
provider-shaped HT-B4 mock reports 3 devices, macro Recall@20 `0.8857`,
micro `0.8462`, 8 provider-shaped calls, simulated cost `$0.0008`, and zero
unknown billing. These are not live-provider results.

The fixed-control final-holdout comparison is descriptive and not estimable:
HT-B4-MOCK matched HT-B3 and was below HT-B0b, HT-B1, and HT-B2 in that run.
Different cohort sizes, candidate-universe ceilings, company/group structure,
and the unjudged-link policy prevent a pooled scientific claim.

## Verification and handoff

The exact commands and outcomes are in `verification.json`. Source hashes for
the implementation are in `manifest.json`. The package is ready for review,
but O3 remains locally blocked and O4 is not a final scientific result.

## Risks and limitations

- Product-level disclosed links are not claim-level semantic relevance labels.
- Unlisted links are unjudged, never automatic negatives.
- Shared patents/families are not merged without sourced mapping.
- Real-device browser integration is not yet wired to the named Abbott cases;
  the real-device HTTP runner is a separate sanitized script/receipt path.
- Local Qwen generation is not an HTTP job/provider action yet.
- No clinical, legal, commercial, deployment, or publication conclusion is
  supported by this package.

## Handoff

Status: `READY_FOR_REVIEW`.

Next discriminating test: after the O3 gates are cleared, bind the frozen
local generation action into the same HTTP job lifecycle and compare it with
the fixed controls under one rights-cleared, hash-frozen protocol. Until then,
keep paid provider dispatch closed.
