# Current-head O2/O3 runtime rebind

This package continues the existing Patent-to-Pilot O1-O4 goal without opening
a new compute or paid window. It rebinds prior actual remote embedding and
local Qwen receipts to candidate `88dc40471cb9078f929c02bb893cfa1e364da841`
using scoped runtime-path comparisons. It does not claim a new remote run,
new GPU allocation, or a live API result.

## Outcome

- O2: `PASS_CURRENT_HEAD_RUNTIME_BOUND_REMOTE_ARTIFACTS_NO_RERUN`
- O3 local branch: `PASS_CURRENT_HEAD_LOCAL_QWEN_REBOUND`
- O3 API branch: `BLOCKED_LOCAL`

The earlier actual remote run encoded PatEmbed-base and multilingual-e5-base
into resumable shards, imported them on Windows, validated the bundles, ran the
shared retrieval evaluator, and ran six device-dossier vector paths. The prior
actual local Qwen run processed the frozen three-case pack with guided JSON and
produced 3/3 schema-valid outputs. Both receipts remain immutable.

## Binding checks

The O2 relevant-path comparison from prior candidate
`20e38974ed32bc6fca9760b9f1974b3c3f8dfa34` to current candidate returned exit
code 0. The checked paths cover vector artifacts, transformer encoders,
retrieval/vector HTTP, shard encoders, and retrieval evaluators.

The Qwen relevant-path comparison from parent runtime candidate
`50b27cd9229bc03232486c68654a0a56866250e0` to the current candidate returned
exit code 0. The checked paths cover the Qwen runner, generation payload,
generation contract, and Qwen regression tests. The current candidate is a
descendant of both parent commits.

## Actual prior evidence retained

- Remote PatEmbed corpus/query manifests: 45,336 passage rows and 1,247 query
  rows; 10 resumable corpus shards plus one query bundle per encoder.
- Remote e5 corpus/query manifests: 45,336 passage rows and 1,247 query rows;
  10 resumable corpus shards plus one query bundle.
- Matched DAPFAM diagnostic: 1,247 queries and 49,869 qrel pairs; PatEmbed
  dense macro Recall@100 `0.4225251715`, e5 dense macro Recall@100
  `0.2874142386`. This is a diagnostic benchmark result, not semantic
  device-patent gold.
- Device vector dossier path: six local runs across MitraClip, Tendyne, and
  TriClip, with zero provider calls and USD 0.00 paid cost.
- Local Qwen3-8B: frozen pack SHA-256
  `d2a91ce2471461b3e5ed5468e15926e7c2359cb21368323a168f9c8fffbb5932`,
  immutable revision `b968826d9c46dd6066d109eabc6255188de91218`, guided
  schema-valid cases `3/3`, provider calls `0`, paid cost `USD0.00`.

## Boundaries

No new inference was performed in this rebind. The original remote 24-hour
window and allocation are not restarted. The API branch remains closed because
the current canonical journal, current account credit, exact route/pricing,
outbound-rights and writer-quiescence gates are not all exposed. The Qwen
receipt is local-generation evidence only; it is not a local-vs-API comparison.

The old HTTP/generation path changed after its prior browser-generation receipt,
so that receipt is not promoted to current-head E2E generation evidence by this
package. The fresh current-head local-vector receipt remains the authoritative
current O1/O4 retrieval engineering evidence.
