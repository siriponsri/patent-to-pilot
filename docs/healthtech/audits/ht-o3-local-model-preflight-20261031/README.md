# O3 local model preflight — 2026-10-31

Status: `PASS_MODEL_ACQUIRED_OFFLINE_SMOKE_REMOTE_GENERATION`.

This bounded package checks whether the pinned `Qwen/Qwen3-8B` artifact can be
acquired into private Windows storage without exceeding the HealthTech goal's
combined Windows + remote additional-disk limit, then runs a bounded local
generation check on the owned remote V100. It does not authorize a paid
provider call or establish outbound dossier-prompt rights.

## Verified inputs

- Public Hugging Face revision: `b968826d9c46dd6066d109eabc6255188de91218`.
- License: `apache-2.0`.
- Allowlisted payload: 15 files, `16,397,461,266` bytes.
- Prior O2 embedding payload recorded in the parent audit: `1,913,198,189`
  bytes combined for PatEmbed and multilingual-e5.
- Current C: free space snapshot: `192,915,554,304` bytes.
- The host RAM snapshot was `16,824,262,656` bytes; it is not treated as
  evidence for the approved remote V100 allocation.

## Peak-storage decision

The conservative two-copy estimate is:

```text
16,397,461,266  Windows Qwen copy
16,397,461,266  remote Qwen copy
 1,913,198,189  prior embedding payload
----------------
34,708,120,721  bytes estimated peak
42,949,672,960  bytes hard bound
 8,241,552,239  bytes remaining headroom
```

The download is therefore permitted under the existing local model goal, with
the remaining headroom reserved for manifests, temporary files, and the
isolated runtime. Any measured total above the hard bound stops the dependent
transfer/runtime branch. The existing PatEmbed/e5 files are not redownloaded
by this package because their concrete storage path was not recovered from the
logical parent receipt.

## Completed acquisition and smoke checks

The existing allowlist-based downloader completed without credentials or
repository staging. The generated manifest records the pinned revision,
Apache-2.0 license, 15 allowlisted files, byte counts, and SHA-256 values.
An independent streaming verifier rechecked all 15 hashes and found no missing
or extra model files. The isolated validation environment imports
`torch==2.8.0+cpu`, `transformers==4.51.3`, `safetensors==0.5.3`, and
`accelerate==1.6.0`; offline Qwen3 config/tokenizer loading passes with
`trust_remote_code=false`.

The full 8B weight load was not attempted on Windows because the host snapshot
has only `16,824,262,656` RAM bytes and no CUDA device. This is a runtime
compatibility boundary, not a model-integrity failure. The bounded remote
V100 generation run passed with the pinned model and isolated runtime; see
[`evidence-pack-contract.json`](evidence-pack-contract.json) and
[`generation-canary.json`](generation-canary.json).

## Frozen evidence-pack generation

The local-research-only pack preserved the three-case order
`MitraClip -> Tendyne -> TriClip`, all five evidence rows per case, the full
ordered candidate lists, source IDs, source revisions/hashes, and exact
locators. It excluded evaluator labels, qrels, gold-derived queries, hidden
oracles, raw HTML/source payloads, and credentials. The pack file is retained
outside Git; only its hash-bound contract is committed.

Qwen3-8B ran with `thinking=false`, greedy decoding, FP16, eager attention,
and one visible Tesla V100-SXM2-32GB bound to UUID
`GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089`. All three outputs passed the
frozen JSON schema. Provider calls and paid cost were zero. This is local
generation and schema-integrity evidence only; it is not a semantic judge,
clinical/FTO analysis, or API comparison.

## Boundaries

No credentials were read. No provider call, API embedding, or paid inference
was performed. The remote local-generation job used only the owned job root,
the pinned model, the hash-bound pack, and the isolated runner. Formal remote
allocation remains recorded as `UNKNOWN_NOT_GRANTED_RESOURCE_OBSERVATION_ONLY`
even though the bounded job completed on the approved UUID.
