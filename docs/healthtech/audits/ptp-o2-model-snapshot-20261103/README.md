# O2 pinned encoder snapshot acquisition - 2026-11-03

Status: `PASS_MODEL_SNAPSHOT_LOCAL_CPU_CANARY_REMOTE_ENCODE_NOT_RUN`.

This additive checkpoint continues the existing Patent-to-Pilot O1-O4 goal at
candidate HEAD `88dc40471cb9078f929c02bb893cfa1e364da841`. It records the
allowlist-based acquisition of the two declared O2 encoder snapshots into the
private ignored Windows model root. It does not claim a remote encode,
retrieval-quality result, or a new GPU allocation.

## Acquisition

The existing repository runner was used without credentials:

```text
rtk proxy python -u scripts/healthtech/prepare_research_models.py \
  --output data/raw/healthtech/models/required-encoders \
  --models patembed-base multilingual-e5-base
```

The runner checked the pinned Hub revision and model-card license, downloaded
only the declared allowlist, wrote per-file byte counts and SHA-256 hashes, and
kept the private model root outside Git. No Qwen weights were downloaded in
this package.

| Encoder | Hub revision | Declared license | Files | Bytes |
|---|---|---:|---:|---:|
| `datalyes/patembed-base` | `244ba452908a3093be11efb8a44396652317fb14` | `cc-by-nc-sa-4.0` | 14 | 778,662,281 |
| `intfloat/multilingual-e5-base` | `d128750597153bb5987e10b1c3493a34e5a4502a` | `mit` | 11 | 1,134,535,908 |
| **Total** |  |  | **25** | **1,913,198,189** |

The private acquisition manifest SHA-256 is
`1b3af4bfc52671c5b411aee473b394a2e2ff12e7681dec0e3f478a74012278ac`.
The manifest is stored at the ignored model root and is not copied into this
audit folder.

## Integrity and layout verification

`build_transformer_model_binding` accepted both local trees using the pinned
model ID, revision, module layout, pooling configuration, and required file
hashes. The key runtime artifacts were:

- PatEmbed transformer weights: `774,215,768` bytes,
  `ae1a87ca79784c8fc457b24b26ebfed812e8f5d5075436b0ba8ad83773560edc`.
- PatEmbed tokenizer: `958,763` bytes,
  `d5496fadd2d7fda4e958da4285f7cd97c41177bbfc500580addc9c08896fb773`.
- PatEmbed projection: `3,145,816` bytes,
  `8987d3aba976a0f6174b2743792d1bc5f8dca0cf0d0da8ba167bf0026819bc42`.
- multilingual-e5 transformer weights: `1,112,201,288` bytes,
  `a18a44fad1d0b46ded15928144138cff1135d5cc8233bdd90be5f18822de09a7`.
- multilingual-e5 tokenizer: `17,082,660` bytes,
  `62c24cdc13d4c9952d63718d6c9fa4c287974249e16b7ade6d5a85e7bbb75626`.

Focused encoder/layout/local-execution/vector-bundle regressions passed `16`
tests with zero failures, errors, or skips. The full current candidate suite
also passed `617` tests with `0` failures, `0` errors, and `1` known optional
tokenizer-artifact skip. Compile checks passed.

## Local runtime smoke

An isolated project-parent venv was used only for a bounded CPU smoke. With
local-files-only loading and eight CPU threads, both encoders produced finite
little-endian float32 arrays of shape `[2, 768]` with L2 norms `[1.0, 1.0]`:

- PatEmbed-base: 29 attention tokens, 7.681 seconds.
- multilingual-e5-base: 32 attention tokens, 4.309 seconds.

The sanitized result is in `cpu-canary.json`; the two authored smoke texts were
not persisted. This confirms runtime loading and normalization only. It is not
a remote encode, a retrieval metric, or evidence of adaptive superiority.

## Boundaries

- The repository's global Windows interpreter still does not have the model
  runtime; the smoke used an isolated venv outside the worktree.
- No remote transfer, SSH inspection, V100 job, encode shard, retrieval
  evaluation, provider call, reservation, attempt, retry, ledger mutation,
  budget reset, or time-window reset occurred in this package.
- PatEmbed is declared `cc-by-nc-sa-4.0`; its weights and derived vectors stay
  private and research-only unless a separate rights review authorizes another
  use. multilingual-e5 is declared MIT, but the project still keeps the local
  snapshot private by default.
- The prior private vector-bundle revalidation remains a separate integrity
  receipt. This checkpoint does not pool that result with a new encode or call
  it a current remote quality result.

## Next action

Obtain a live, owner-authorized remote allocation/ownership receipt and an
available transfer path before sending the pinned snapshots to `dr-train`.
Then run the existing resumable shard encoder at concurrency 1 on the
approved V100, retain failed and resumed shards, and evaluate only after the
returned manifests pass the existing binding checks. Keep the paid OpenRouter
branch independent and fail closed until the canonical R1 history/export and
current scoped credit evidence are reconciled.

