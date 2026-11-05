# Stage 0 — organization-adaptive cross-domain acquisition study (DAPFAM)

- Protocol: [ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md](../../research/ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md) (draft, not frozen)
- Base commit: `47fa6df`. The Stage 0 code is in this commit.
- Status: **PASS**.
- **The test split was not scored.** Only dev and the internal pipeline check were evaluated.
- Paid cost: USD 0. GPU: dr-train V100 under the approved lock, about 6,270 s in total.
- Machine-readable aggregates: [stage0-results.json](stage0-results.json) and [stage0-split-inputs.json](stage0-split-inputs.json). Private outputs (split file, rankings, generations) are in `_private_artifacts/healthtech/ptp-org-adaptive-20261105/`; their SHA-256 values are recorded in the JSON files.

## Results

| Check | Result |
|---|---|
| Input hashes (corpus, queries, qrels) | Match the pinned manifest |
| Split | 526 components. Dev: 474 queries (349 OUT-eligible). Test: 773 queries (556 OUT-eligible). Components with ≥ 50 queries went to dev. |
| GPU inputs | Label-free text only; 188,944 dense passages; 6,206 query windows |
| Models | PatEmbed-large `2d5c0f92…` (all 10 files hash-verified; CC BY-NC-SA 4.0); Qwen3-8B `b968826d…` (Apache-2.0) |
| Pooling equivalence | Bit-identical to `sentence-transformers` 4.1.0 on 80 texts (max abs diff 0.0) |
| Internal pipeline consistency | PASS (strict-OUT Recall@200 delta 0.000000 against the owner's earlier unpublished internal run). Not a reported result. |
| Truncation at 512 tokens | 10.1% of passages (4% of passage tokens lost). **1,187 of 1,247 queries (median 1,309 tokens; 71% of query tokens lost).** |

### Dense variants on dev (macro recall; test not scored)

| Variant | strict-OUT R@100 | strict-OUT R@200 | IN R@200 | All R@200 |
|---|---:|---:|---:|---:|
| R2 single-window query | **0.1120** | **0.1618** | **0.5182** | **0.3520** |
| R2w multi-window, max over windows | 0.1087 | 0.1552 | 0.5081 | 0.3463 |
| R2w multi-window, mean over windows | 0.1085 | 0.1538 | 0.5053 | 0.3436 |

**Negative result.** Encoding the whole query (71% more query text) did not help with either aggregation; every dev endpoint was lower. R2 single-window stays the dense fixed candidate. A plausible reading: windows from deep in the claims add spurious matches, while the first window (title, abstract and opening claims) carries most of the useful signal. Both variants are reported. No further variants were tried, to avoid tuning on dev.

### Qwen3-8B canary (20 dev queries, greedy, no retries)

| Prompt | Calls | Failed | Queries with usable IPC-shift classes | Mean latency |
|---|---:|---:|---:|---:|
| v0 | 40 | 0 | **1 of 20** | 9.7 s |
| v1 | 40 | 1 (malformed JSON) | 19 of 20 | 9.1 s |

- **v0 failure.** Qwen returned subclass or group codes (e.g. `B63J`, `C12N1/00`), mostly inside the query's own fields. After filtering, Q2 was unusable.
- **v1 fix.** The prompt now requires an explicit three-character format and excludes the query's own classes; the parser keeps the class prefix and removes own classes. 40 of 50 proposed classes are in a different IPC section.
- **Gate.** 2.5% of calls failed, under the 5% limit.
- **Risk carried to Stage 1.** Proposals concentrate on generic classes (G01 in 15 of 20 queries; B01 and F16 in 7 each). Stage 1 measures whether Q2 adds cross-domain exposure.
- **Functional queries (Q1)** had a median of 55 words. Pseudo-documents (Q3) had 122–154 words.

## Incidents and deviations

- **Queue blocked.** A watcher process whose own command line contained the waited-for pattern blocked the canary queue, leaving the GPU idle for about one hour. Only the two watcher shells created for this study were terminated. Later watchers use self-excluding patterns.
- **Runner versions.**
  - The dense encoding ran with runner SHA-256 `559f52e2…`, before the neutral rename and the `device` parameter were added. The pooling math is unchanged.
  - The max-window ranking ran on an earlier copy of the current runner; its max path is identical to the current default.
  - The mean-window ranking ran with `81c48e4e…`.
- **Shared venv.** `sentence-transformers` 4.1.0 was added to the shared dr-train venv with owner approval. Only new packages were installed; the before and after `pip freeze` files are kept on dr-train.

## Next (Stage 1, dev only)

1. Run R1 (BM25 over TAC) and R3 = RRF(R1, R2) on dev.
2. Run Qwen v1 actions Q1–Q3 on the 474 dev queries (about 2.4 h of GPU).
3. Compute F\*, M\* and the dev oracle.
4. Apply the headroom gate before any test scoring.
