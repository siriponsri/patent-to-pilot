# G5 solo operational case table checkpoint

Observed: 2026-11-04 Asia/Bangkok (recorded UTC `2026-11-03T23:41:27.9786139Z`)

## Candidate and scope

- Existing Patent-to-Pilot goal; no new goal or epoch.
- Worktree: `patent-to-pilot-long-run-20261103`.
- Branch: `codex/patent-to-pilot-long-run-20261103`.
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`.
- Tree state: intentionally dirty; unrelated owner/Claude/Luna changes preserved.
- Change type: documentation and continuation-record update only. The local Qwen receipt was read and rebound; no model rerun, paid call, GPU job, or ledger mutation occurred.

## Completed package

The manuscript operational-value section now binds the three-case machine-side
measurements to the current local Qwen receipt and deterministic operational
evaluation. It records:

- `3/3` schema-valid local Qwen3-8B cases;
- `12/12` exact source/locator bindings and `12/12` classification-contract matches;
- `12/15 = 80%` emitted-evidence coverage and `3/3` cases with unresolved-item visibility;
- prompt/output tokens `7,301/1,448` and mean generation latency `54.320437` seconds;
- provider calls `0` and paid cost `USD0.00`; and
- model revision `b968826d9c46dd6066d109eabc6255188de91218`.

The manuscript explicitly separates these machine-side and developer-self-
evaluation proxies from human time, independent user validation, revenue,
willingness-to-pay, ROI, semantic accuracy, and customer validation, all of
which remain unmeasured.

## Verification

- Local Qwen receipt candidate binding: current HEAD `88dc404...`.
- Receipt source: `ptp-local-qwen-patent-run-20261104/verification.json`.
- Receipt SHA-256: `6bf2a84bb66c7c0723b1508379883a45188248eafdd5f03fe2f8ccc9e331efcd`.
- Operational-evaluation SHA-256: `8e329c714fb38a2aa12662bd76c672e756fac60ed5b5185a560de4b31bfc341b`.
- Markdown links after update: `74` checked, `0` missing.
- `git diff --check`: pass.

## Resource and evidence boundary

- Paid provider calls: `0`.
- GPU jobs: `0`.
- Downloads: `0`.
- Ledger mutations/reservations: `0`.
- External business validation: not performed in the solo project and not claimed.
- Merge/push/publish: not performed.

## Next action

Continue with `portable_candidate_instructions` (G7). Keep the installed wheel
evidence separate from source-checkout scripts and private data/model recovery;
do not claim clean-machine installation or public release until separately
verified and owner-reviewed.
