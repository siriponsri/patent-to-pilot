# P2-T02 coverage control — results receipt (P1-DEV only)

**Protocol:** [P2-T02-COVERAGE-CONTROL-PROTOCOL.md](../../../healthtech/research/p2-coverage/P2-T02-COVERAGE-CONTROL-PROTOCOL.md)
(frozen bd30d3f7) with amendment [A1 (RunPod)](../../../healthtech/research/p2-coverage/P2-T02-AMENDMENT-A1-RUNPOD.md).
**Run:** RunPod pod `jd41r4cvv171q6`, RTX PRO 4500 Blackwell 32 GB, US-KS-2, 23 Nov 2026 12:42–19:25 UTC (deleted;
about 6.7 h × USD 0.72 ≈ USD 4.8, envelope R1). Block P1-DEV only: no VAL and no TEST.
**Outputs (private):** `../_private_artifacts/p2t02-runpod/` (runs, per-query evaluations, results.json, gates, logs;
tar sha256 in `p2t02-runpod-outputs.tar.sha256`). The content (21 GB) and the C1/C2 vectors (15 GB) were not kept:
they rebuild in 5.5 min and about 2 h per arm.

## Gates

| Gate | Result |
|---|---|
| A1 rebuild gate A: corpus text | byte-identical (`287ef7e0…`) |
| A1 rebuild gate B: unit order | identical |
| A1 rebuild gate C: BM25-C0 vs archive | 100% of queries identical; every mean difference 0.0 |
| A1 rebuild gate D: Arctic-C0 vs archive | 99.906% of queries identical; largest mean difference 0.00008 |
| Protocol stage 0: evaluator path vs summary | passed |
| Encoder validation (id path vs stored C0 vectors, 2,048 units) | min cosine 0.99991; id path = text path bitwise |
| C0 retrieval reproduction with the new retriever | **exact**: 25,626,000 of 25,626,000 rows identical |

## Arm table (P1-DEV, query-macro, 25,626 queries with text; evaluator population 26,547)

| Arm | ALL R@200 | IN R@200 | OUT R@200 | ALL R@1000 | OUT MRR |
|---|---|---|---|---|---|
| Arctic C0 (current: title + abstract + first claim, 512 cap) | 0.2980 | 0.3588 | 0.2247 | 0.4655 | 0.0564 |
| **Arctic C1 (complete content, flat 512-token windows, max-p)** | **0.3145** | 0.3763 | 0.2393 | 0.4853 | 0.0592 |
| Arctic C2 (complete content, structural claim groups, max-p) | 0.3058 | 0.3656 | 0.2315 | 0.4786 | 0.0565 |
| BM25 C0 | 0.2174 | 0.2529 | 0.1727 | 0.3474 | 0.0462 |
| **BM25 full text** | **0.2397** | 0.2823 | 0.1882 | 0.3819 | 0.0495 |

## Frozen contrasts (cluster bootstrap by art unit, B = 10,000, seed 20261119)

| Contrast | ALL R@200 Δ [95% CI] | IN | OUT |
|---|---|---|---|
| Coverage: Arctic C1 − C0 | **+0.0165 [0.0144, 0.0186]** | +0.0174 [0.0142, 0.0206] | +0.0146 [0.0117, 0.0176] |
| Coverage: BM25 full − C0 | **+0.0223 [0.0200, 0.0247]** | +0.0293 [0.0259, 0.0328] | +0.0155 [0.0121, 0.0188] |
| Structure: Arctic C2 − C1 | **−0.0087 [−0.0105, −0.0069]** | −0.0106 [−0.0134, −0.0078] | −0.0078 [−0.0102, −0.0053] |
| Arctic C2 − C0 | +0.0078 [0.0056, 0.0101] | +0.0068 [0.0032, 0.0104] | +0.0068 [0.0038, 0.0098] |

## Decision (frozen rule, applied by `p2t02_analyse.py decide`)

- **Arctic: C1 (flat complete content) becomes the representation baseline. Structure gets no credit**: C2 is worse
  than C1 on ALL, IN and OUT.
- **BM25: BM25 full text becomes the BM25 representation baseline.**
- These are **engineering controls**. A gain here means "more eligible text was indexed". It is not evidence for the
  acquisition method. They raise the bar that P2-T04 and later comparisons must clear.
- **Triggered:** owner decision D19, the complete-content follow-up for PatEmbed and Qwen3. It is now under envelope
  R2 (D22) on RunPod and needs a declared amendment before it runs.
- **Deferred to dr-train** (amendment A1 §2.5): the descriptive G03 fusion check with the substituted arms, and the
  deeper original-query control (windows 1–2). Neither changes the decision.

## Cost (pod logs)

| Stage | Wall time | Peak RSS |
|---|---|---|
| Content build (1M units; 3,973,755 C1 / 5,955,181 C2 passages; 1.77 B C1 tokens) | 5 min 35 s | 15.7 GB |
| Encode C1 | 1 h 58 min | 26.7 GB |
| Encode C2 | 2 h 01 min | 36.3 GB |
| Retrieve C1 / C2 | 11 min / 13 min | 24.3 / 35.2 GB |
| BM25 full | 15 min | 12.6 GB |
| Decide (bootstrap) | 2 min 30 s | 4.1 GB |

Content stats: 999,997 units with live claims; 88,170 cancelled rows dropped; 0 first-claim mismatches.

## Incidents

- The first dr-train launch (23 Nov) exhausted host memory. See [run notes](../../../healthtech/research/p2-coverage/P2-T02-RUN-NOTES.md) §4.
- On RunPod, the first content-build attempt was a false memory abort: page cache was counted as used. It was fixed
  (amendment A1 §7 run record) and the run resumed. No output was affected.
