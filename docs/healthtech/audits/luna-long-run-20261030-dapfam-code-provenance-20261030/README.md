# HT-M36 DAPFAM runner code provenance binding

Status: `PASS_OFFLINE_REPRODUCIBILITY_PROVENANCE`

Run ID: `luna-long-run-20261030-dapfam-code-provenance-20261030`

## Objective

Bind each DAPFAM BM25 result to the exact working-tree runner source, not only to the Git `HEAD` revision. This closes a reproducibility gap discovered after M35: the runner and test could be uncommitted while the manifest reported only the prior committed `HEAD`.

## Implementation

- Added `code_provenance()` and `git_worktree_dirty()` to `scripts/healthtech/run_dapfam_bm25.py`.
- Every manifest now records the runner entrypoint, SHA-256, Git revision, and whether the worktree was dirty at execution time.
- Added a regression test for the provenance shape and cross-platform entrypoint path handling.
- Preserved the existing BM25 method, qrels-only policy, ranking outputs, and DAPFAM/HT-T1 boundary.

## Verification

- Final targeted suite: `6 passed`.
- Compile check: passed for runner and test.
- Synthetic smoke: passed with `4` candidates, `2` queries, and `3` qrel pairs; manifest code SHA matched the runner.
- Full baseline: passed with `45,336` candidates, `1,247` queries, `49,869` qrel pairs, and `1,247` ranking rows at `k=100`.
- Post-run integrity checks: all counts, unique query IDs, ranking widths, code SHA, Git revision binding, dirty-tree state, output presence, and zero provider calls passed.

## Results

Full output: `results/healthtech/ht-dapfam-bm25-20261030-r3/`.

- Macro Recall@100: `0.21398467432950194`.
- Micro Recall@100: `0.2136868707128244`.
- Macro nDCG@100: `0.19229519072532472`.
- Runner SHA-256: `15b6ddedda892221b7fefff1ebbc198e35f7e886f22a8695fc93c7ae6df52573`.
- Code revision: `7edf2f4adf013787d0db5f3a028c5d0ac58ae7f4`.
- Worktree state: `dirty=true`, explicitly recorded rather than inferred away.

## Boundaries

This is a reproducibility and engineering improvement for the separate DAPFAM citation-based retrieval diagnostic. It does not create semantic device-product labels, change the HT-T1 denominator or unjudged policy, or establish clinical, FTO, patent-validity, exhaustive-recall, investment, or publication claims. No provider/network calls, credentials, restricted payload transfer, or paid cost occurred.

Parent package: `docs/healthtech/audits/luna-long-run-20261030-dapfam-bm25-20261030/`.
