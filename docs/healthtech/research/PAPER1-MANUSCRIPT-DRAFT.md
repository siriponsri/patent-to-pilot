# Functional abstraction of patent queries for cross-domain prior-art acquisition: a pre-registered comparison on DAPFAM

Working manuscript, restructured 16 November 2026. Not submission-ready.

Status:
- The protocol is frozen ([protocol](plans/PAPER1-ACQUISITION-PROTOCOL-DRAFT-20261113.md), amendment A1 inside it).
- Development (dev) results are complete and descriptive (S5).
- The test stage (S8) is running. No test result exists yet. Every test number below is a placeholder.
- The earlier development-stage text of this file (R1-R7 rounds) is kept unchanged in [PAPER1-DEVELOPMENT-HISTORY.md](PAPER1-DEVELOPMENT-HISTORY.md).

How to fill this draft after the single S8 test evaluation (target: within one hour):
1. Render the tables (stdlib only):
   `python docs/healthtech/research/paper1-report/render_paper1_test_report.py <takeover>/paper1-s8-eval/terminal-observation.json --dev <takeover>/paper1-s5-eval/terminal-observation.json --receipts <takeover> --out docs/healthtech/research/paper1-report/test-S8-tables.md`
   where `<takeover>` = `docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112`. If the evaluator writes `summary.json` separately, pass that file instead; both forms are accepted.
2. Check the last line of Table R3: it must say that all verdicts MATCH the frozen rule. Exit code 2 means a mismatch; stop and investigate before writing anything.
3. Replace every `[[R…]]` placeholder with the value from the named table in `test-S8-tables.md`.
4. Keep exactly one of the three conclusion branches in section 9 (and the matching abstract sentence), chosen by the H1 verdict in Table R3. Delete the other two.
5. Do not change the analysis, margins or wording rules after seeing the result.

Placeholder key (all tables come from `render_paper1_test_report.py`):

| Placeholder | Source |
|---|---|
| `[[R1-OUT]]`, `[[R1-IN]]`, `[[R1-ALL]]` | Table R1, metrics per system |
| `[[R2-OUT]]`, `[[R2-IN]]`, `[[R2-ALL]]` | Table R2, paired Recall@200 differences |
| `[[R3]]`, `[[R3b]]` | Table R3 gatekeeping, R3b harm check |
| `[[R4-C1]]`, `[[R4-C2]]`, `[[R4-C3]]` | Table R4 controls |
| `[[R5-OUT]]` (and IN/ALL) | Table R5 exposure strata and rank bins |
| `[[R6]]` | Table R6 fallbacks |
| `[[R7]]` | Table R7 efficiency |
| `[[R3:H1]]`, `[[R3:H2]]`, `[[R3:H3]]` | verdict label of that step, exactly as printed |
| `[[R2-OUT:H1:mean]]`, `[[R2-OUT:H1:ci]]` | mean Δ and 95% CI of that row |

## Abstract (template)

Cross-domain prior art uses different words for the same technical idea, so dense retrieval often misses it. We test whether a large-language-model rewrite that restates a patent query as its function, mechanism, problem and conditions, without application-domain nouns (functional abstraction, FA), brings more known cross-domain prior art into the top 200 when fused with the original query. On DAPFAM, with 773 test queries (556 with cross-domain positives), we compare the fused system F-FA against the dense baseline B0, against a generic LLM rewrite fused the same way (F-GR) and against a source-anchored faithful rewrite (F-SACR). The protocol, margins and test order were frozen before any test query was processed. The primary endpoint is cross-domain (OUT) Recall@200, tested in a fixed sequence with a cluster bootstrap. F-FA minus B0 on OUT Recall@200 was [[R2-OUT:H1:mean]] (95% CI [[R2-OUT:H1:ci]]); the frozen rule classifies H1 as [[R3:H1]].
- Branch A (H1 superior): Abstraction-fused retrieval acquired more known cross-domain positives than B0; [[H2/H3 sentence]].
- Branch B (H1 practically equivalent): The interval excludes gains larger than 0.010, so any benefit of abstraction at this cost is small.
- Branch C (H1 inconclusive or inferior): The test did not show a benefit; [[one sentence on harm check and controls]].
We also report the cost per query, fallbacks, exposure strata (queries rescued and displaced), a word-shuffle fusion control and a family-overlap sensitivity analysis.

## 1. Introduction

Prior-art search across technical domains is hard because the same function is described with different vocabulary in different fields. DAPFAM labels each query–target pair as in-domain (IN) or out-of-domain (OUT) by IPC class, which makes this difficulty measurable [DAPFAM].

Our earlier work (Paper 53) studied instruction-conditioned reranking of DAPFAM OUT candidates. Instruction effects were near zero, and only 257 of 692 top-100 pools contained any known OUT-relevant family [Paper 53]. A reranker cannot recover a family that is not in its pool. The present study therefore moves one step earlier, to candidate acquisition: which query text brings more cross-domain positives into the top 200?

On our dev split the dense baseline B0 reaches OUT Recall@200 of 0.1477 over 349 OUT-eligible queries, and 213 of them (61%) have no known positive in the top 200. A faithful, source-anchored rewrite (SACR) stays close to the original query in embedding space (mean top-200 overlap with the baseline 0.86 on dev). We therefore ask whether an abstraction that removes application-domain nouns moves the query far enough to reach other domains, and whether any gain is specific to abstraction rather than to rewriting in general.

Research questions:
- RQ1 (H1). Does F-FA retrieve more known OUT positives at 200 than B0?
- RQ2 (H2). Is the gain specific to abstraction, compared with a generic rewrite fused the same way (F-GR)?
- RQ3 (H3). Does abstraction beat faithful reformulation (F-SACR)?
- RQ4 (secondary). What does it cost in in-domain recall, model calls and GPU time, and which queries are rescued or displaced?

Contributions:
1. A functional-abstraction query arm used by fusion with the original query.
2. A pre-registered, gatekept comparison against generic and faithful rewrite controls at reported cost, on a held-out test split opened once.
3. An exposure diagnostic that separates acquisition (rescued and displaced queries) from ranking, plus three manipulation and sensitivity controls.

Positive, null and negative outcomes are all reported (section 9).

## 2. Related work

**Cross-domain patent retrieval benchmarks.** DAPFAM [DAPFAM] is a family-level dataset built for cross-domain retrieval. Positives come from citation relations at family level, and each pair is labelled IN or OUT by IPC3 overlap. We use it under its CC BY-NC-SA 4.0 licence. PANORAMA [PANORAMA] records USPTO examination decision trails and defines tasks around them (prior-art choice PAR4PC, paragraph identification PI4PC, and rejection type NOC4PC). It grounds relevance in examiner rejections, whereas DAPFAM uses citation relations; section 8 quantifies how rarely DAPFAM positives are examiner 102/103 rejection citations.

**Agentic patent search.** PatEx-Gym [PatEx-Gym] trains a small (4B) search agent by supervised fine-tuning to run prior-art search over a corpus of about one million patents plus papers, with 1,000 benchmark tasks. PatentAgentBench [PatentAgentBench] evaluates LLM agents with search tools on 510 cases in eight professional patent suites, including invalidity search and an office-action response suite. Both study multi-step agents. Our study isolates a single, cheap step (one rewrite call per query) under a fixed retrieval pipeline, so that the effect of the query text can be attributed.

**LLM query rewriting and expansion.** Query2doc [Query2doc] and HyDE [HyDE] generate pseudo-documents for a query and retrieve with them. Our generic-rewrite control GR follows this pattern for patents ("write an abstract that would be relevant prior art"). FA differs only in the instruction: restate the query's own function, mechanism, problem and conditions in domain-neutral terms and add no content.

**Reranking and exposure.** Paper 53 [Paper 53] showed that instruction-conditioned reranking cannot add families that are absent from the candidate pool. This motivates measuring exposure directly (section 5.5).

**Fusion.** We combine rankings with reciprocal rank fusion [RRF], which needs no score calibration between the two views.

**Patent encoders.** We hold the encoder fixed (PatEmbed-large passage vectors). Patent-specific encoders and graph-informed representations [PaECTER; PatenTEB; PHAGE] change the document side; our arms change only the query side, so the two lines are complementary. Published DAPFAM numbers use other cohorts, models and metrics; they are context, not a leaderboard ([comparability matrix](plans/DAPFAM-PAPER-COMPARABILITY.md)).

## 3. Data and evaluation

**Dataset.** DAPFAM, pinned revision. Queries are the native title-and-abstract (TA) text. The candidate corpus is 45,336 families, searched in full for every query, represented by title, abstract and claims (TAC). Splits: dev 474 queries; test 773 queries, of which 556 have at least one OUT positive. The test split was staged once and its relevance labels were opened only by the single final evaluation job.

**Partitions.** IN and OUT follow DAPFAM's IPC3 rule. A query is eligible for a partition if it has at least one known positive in that partition. Eligible populations overlap; IN and OUT counts do not sum to the query count. ALL uses every query.

**Metrics.** Pinned native evaluator, macro over eligible queries: Recall@10/100/200 and nDCG@10/100/200, binary relevance; nDCG ideals use all known partition positives. A missing ranking scores zero. Unjudged families are not counted as negatives in any claim; Table R5 reports the unjudged share of the top 10 descriptively.

**Primary endpoint.** OUT Recall@200 (owner choice, fixed in the protocol).

## 4. Systems

All systems share one retrieval pipeline: the existing PatEmbed-large passage vectors (384-word windows, 64-word overlap), the query prefix `encode query for different document retrieval: `, family MaxP aggregation, and a top-200 cutoff. The corpus was not re-encoded.

| System | Query-side text | LLM calls per query |
|---|---|---|
| B0 | Original TA query | 0 |
| SACR (faithful control) | Source-anchored rewrite: a marking call and a review call; the screened candidate is used, otherwise the original query | up to 2 |
| GR (generic control) | One generated patent abstract "that would be relevant prior art", no domain or abstraction instruction | 1 |
| FA (method) | One grammar-constrained JSON object with `function`, `mechanism`, `problem`, `conditions`, restated in domain-neutral terms using only the query's content; fields concatenated in order | 1 |
| F-SACR, F-GR, F-FA | RRF of B0 with the arm's top 200 (k = 60), union cut to 200; ties by B0 rank, then family ID | — |
| F-shuffle (control C2) | RRF of B0 with a deterministic word-shuffled copy of the original query; no LLM | 0 |

**Generation.** Qwen3-8B, fp16, greedy decoding, the same decoder and output-length cap for FA and GR. Outputs are constrained by a JSON grammar (LMFE) with an end-of-sequence guard, a whitespace cap of 48 and fixed field order. The input-token cap (5,800) is checked before the model is loaded. FA and GR prompts include one short authored example (not from DAPFAM); FA and GR use the same example.

**Fallback.** If a rewrite fails (input over the cap, grammar refusal, a grammar dead end, or no screened SACR candidate), that query uses the original query text. Every query stays in every denominator. Fallback counts are reported per arm (Table R6).

**Fidelity.** FA and GR outputs have no semantic review stage, and there is no human audit and no LLM judge (owner decision). Abstraction fidelity is therefore not certified (section 8).

## 5. Protocol and analysis

### 5.1 Stages

S1 grammar qualification on CPU; S2 one synthetic GPU smoke per arm; S3 technical pilot (20 dev queries, throughput and failures only); S4 full-dev generation; S5 dev retrieval and descriptive evaluation; S6 owner checkpoint; S7 freeze of the test configuration; S8 test generation, one retrieval job and one evaluation. One GPU job ran at a time. The owner checkpoint could only choose between testing with the frozen plan or stopping; it could not change arms, prompts, margins, endpoints, fusion or test order. The owner chose to test.

### 5.2 What was seen before the freeze (disclosure)

- B0 dev results (section 6.1) were known before the protocol was written.
- The SACR result on a 20-query dev pilot was known and motivated the FA arm: on OUT, SACR rescued no query that B0 missed.
- Earlier development rounds of SACR and a relation-extraction (graph) track are recorded in the development history. The graph track is not part of this paper's comparisons.
- Full dev results for all arms (section 6.1) were seen at the S6 checkpoint, before the test freeze. They did not change the confirmatory plan.
- A pre-declared tail-fusion design (A2: keep B0's top k, fill the tail from the arm) was evaluated once on dev under a selection rule fixed in advance. No variant met the rule, so it was not carried to test ([A2 result](../audits/ptp-automatic-preparation-20261112/takeover-20261112/paper1-a2/A2-RESULT.md)).
- No test query text, label or outcome was opened before the single evaluation.

### 5.3 Engineering repairs during generation

These changed failure handling only; arms, prompts, schemas, margins and analysis were unchanged.
- One FA dev query raised a grammar refusal (the end-of-sequence guard refused a premature stop). The protocol already required original-query fallback for such failures, but the worker stopped the whole batch. The worker was repaired to apply the fallback and continue; the failed query was not regenerated, and the unstarted queries of that batch ran in a continuation job. One GR dev query later hit the same refusal and was handled by the repaired worker.
- The same repair was applied to SACR, and later extended to a second verified grammar failure type (a grammar state with no allowed next token).
- Each repair was qualified on an authored CPU fixture before use and recorded with owner approval.

### 5.4 Hypotheses and decision rule

Fixed-sequence gatekeeping at two-sided α = 0.05 on OUT Recall@200; each step is tested only if the previous one concluded superior:

| Step | Comparison | Hypothesis |
|---|---|---|
| H1 | F-FA vs B0 | Abstraction-fused retrieval acquires more known OUT positives |
| H2 | F-FA vs F-GR | The gain is specific to abstraction |
| H3 | F-FA vs F-SACR | Abstraction beats faithful reformulation |

Interpretation of each tested step from the 95% CI of the mean paired difference (frozen rule):
- superior: the CI lies entirely above 0;
- inferior: the CI lies entirely below 0;
- practically equivalent: the CI lies inside −0.010 to +0.010 (δ = 0.010, about 7% of dev B0);
- inconclusive: otherwise.

Harm check (secondary): non-inferiority of F-FA vs B0 on IN and ALL Recall@200 with margin 0.020 (lower CI bound above −0.020).

### 5.5 Statistics and controls

- Unit: per-query paired differences on identical query sets.
- Interval: cluster bootstrap over connected components of the query-to-positive graph (queries sharing a positive resample together), 10,000 resamples, seed 20261113, percentile 95%. Component counts and the largest component's share are reported; if one component holds more than half of the queries, a query-level bootstrap and a sign-flip test are added as sensitivity analyses without changing the decision.
- Power: from dev paired SDs, the minimum detectable OUT difference at 80% power for n = 556 is about 0.014 for H1-H3, larger than δ = 0.010. The test therefore has limited power for effects of the size of δ.
- Secondary (descriptive): Recall@10/100, nDCG@10/100/200; wins/losses/ties; exposure at 200 and four exposure strata against B0 (both, system only = rescued, B0 only = displaced, neither); first-positive rank bins; unjudged top-10 share; fallbacks; cost.
- C1 manipulation check (label-free): share of non-fallback queries whose top-200 equals the reference, mean top-200 Jaccard overlap, share of truncated texts. Above 95% identical lists means an engineering fault and the arm is not evaluated.
- C2 word-shuffle fusion control (F-shuffle): estimates how much fusing B0 with any perturbed second view changes recall. F-FA minus F-shuffle is reported descriptively, outside the gatekeeping.
- C3 family-overlap sensitivity: every endpoint again without queries whose own family occurs in the corpus.
- Retrieval reference: the anchors were re-encoded in each retrieval job; if they match the pinned B0 under the frozen rule, the re-encoded anchors are the reference (dev: 472 of 474 identical).

## 6. Results

### 6.1 Development split (descriptive; no significance claims)

Source: [dev tables](paper1-report/dev-S5-tables.md), rendered from the S5 evaluation receipt. Dev intervals are for planning only.

| OUT, n = 349 | Recall@200 | Exposed at 200 | Rescued vs B0 | Displaced vs B0 |
|---|---|---|---|---|
| B0 | 0.1477 | 136 | — | — |
| F-FA | 0.1471 | 135 | 8 | 9 |
| F-GR | 0.1522 | 139 | 5 | 2 |
| F-SACR | 0.1504 | 138 | 2 | 0 |
| F-shuffle | 0.1450 | 136 | 7 | 7 |
| FA (standalone) | 0.1332 | 119 | 15 | 32 |

Paired OUT Recall@200 differences on dev (descriptive 95% CI): F-FA − B0 −0.0006 (−0.0116 to +0.0225; 16 wins, 31 losses, 302 ties); F-FA − F-GR −0.0051; F-FA − F-SACR −0.0033; F-FA − F-shuffle +0.0020. In-domain recall fell with F-FA: IN Recall@200 0.4796 vs 0.5137 (difference −0.0341, CI −0.0444 to −0.0212), which is beyond the 0.020 harm margin on dev. Standalone FA reached the most different neighbourhoods (mean top-200 Jaccard with the reference 0.41, against 0.75 for GR and 0.86 for SACR) and rescued 15 OUT queries, but displaced 32.

Generation on dev: FA 473 rewrites and 1 fallback; GR 473 and 1; SACR 468 and 6. GPU time including model load: about 24 s per query for FA, 23 s for GR and 95 s for SACR (Table R7 in the dev tables).

These dev results were seen before the test freeze (section 5.2). They did not change the plan.

### 6.2 Test split: confirmatory result

[[R3]]

[[R3b]]

Paired OUT differences on test, all comparisons: [[R2-OUT]]

Text to complete: "On the 556 OUT-eligible test queries, F-FA minus B0 was [[R2-OUT:H1:mean]] (95% CI [[R2-OUT:H1:ci]]), so H1 is [[R3:H1]]. H2 is [[R3:H2]] and H3 is [[R3:H3]]. On IN and ALL, the harm check shows [[R3b result words]]."

### 6.3 Test split: metrics per system

[[R1-OUT]]

[[R1-IN]]

[[R1-ALL]]

[[R2-IN]]

[[R2-ALL]]

### 6.4 Controls

[[R4-C1]]

[[R4-C2]]

[[R4-C3]]

Text to complete: C1 passed for [[arms]]. F-FA minus F-shuffle on OUT was [[value, CI]], so [[the fusion effect beyond a perturbed second view is / is not distinguishable]]. Excluding the [[n]] overlapping-family queries changes H1 from [[a]] to [[b]].

### 6.5 Exposure: rescued and displaced queries

[[R5-OUT]]

Text to complete: F-FA rescued [[n]] OUT queries that B0 missed and displaced [[n]] that B0 had found; for F-GR the numbers are [[n]]/[[n]] and for F-SACR [[n]]/[[n]].

### 6.6 Fallbacks and cost

[[R6]]

[[R7]]

Text to complete: FA and GR each cost one model call per query, about [[x]] GPU-seconds per query on one V100 including model load; SACR cost two calls and about [[x]] GPU-seconds. Token counts are not in the public receipts.

## 7. Discussion

Write after the result, using only the tables above. Points to address in every branch:
- Whether the OUT change comes from rescued queries (acquisition) or from reordering within already-exposed queries (Table R5).
- The IN/ALL cost of fusion (harm check), and whether the dev pattern (IN loss beyond the margin) repeated on test.
- How F-FA compares with F-shuffle: a fused second view that is merely different can change recall; only the difference beyond F-shuffle can be attributed to the content of the abstraction.
- Cost per query against the size of the effect.
- Agreement or disagreement between dev and test, stated without testing it.

## 8. Limitations

- **Incomplete judgments.** DAPFAM positives are citation-derived and incomplete. A rewrite that surfaces relevant but unlabelled families is under-credited, and one that surfaces irrelevant families is not penalised beyond lost recall. There was no human audit and no LLM judge.
- **What DAPFAM positives represent.** We linked DAPFAM dev families to US documents by exact normalised title (a US family member dated on or after the earliest claim date; ambiguous titles abstained) and matched them against USPTO office-action citations for 2008-2017. Only 13 of 9,480 dev positive pairs (3 of 2,990 OUT pairs) were cited by an examiner as the basis of a 102 or 103 rejection. Among pairs where both sides mapped and the query had a 102/103 office action, the share was 1.0% for IN (10/1,028) and 0.7% for OUT (3/428). This is descriptive: the title matching is an approximation whose precision was not measured, and US office actions outside 2008-2017 or in other offices were not covered. It means that DAPFAM measures recovery of cited prior art in general (applicant citations, other offices, other family members), not of art that examiners used to reject claims ([OA feasibility note, section 9](paper2-precheck/OA-DATA-FEASIBILITY.md)).
- **Single benchmark, single model, single encoder.** One dataset, one generator (Qwen3-8B) and one encoder (PatEmbed-large). Transfer to other collections, larger models or other encoders is not tested.
- **Exposed dev split.** The dev split was used for engineering readiness, the SACR pilot that motivated FA, the owner checkpoint and the A2 design. Dev numbers are therefore not independent evidence; only the test split carries the confirmatory claims.
- **No fidelity certification for FA and GR.** A gain could come from content drift rather than faithful abstraction. The lexical checks reported at the pilot stage only partly address this.
- **Limited power.** The planned minimum detectable OUT difference (about 0.014 at 80% power, n = 556) exceeds δ = 0.010.
- **Shared-target dependence.** Queries share positives; the cluster bootstrap accounts for this, but the effective sample size is smaller than the query count (see component counts in Table R1).
- **Engineering repairs during generation** (section 5.3) changed failure handling for a small number of queries; all such queries are counted with the original-query fallback.
- **Comparability.** Published DAPFAM scores use other cohorts, models and metrics and are not compared numerically.

## 9. Conclusion (three prepared branches; keep exactly one)

Selection rule: use the H1 verdict in Table R3 as printed. `SUPERIOR` → Branch A. `PRACTICALLY_EQUIVALENT` → Branch B. `INCONCLUSIVE` or `INFERIOR` → Branch C.

**Branch A — H1 superior.**
On the DAPFAM test split, fusing a functional-abstraction rewrite with the original query retrieved more known cross-domain prior art at 200 than dense retrieval alone (OUT Recall@200 [[R2-OUT:H1:mean]], 95% CI [[R2-OUT:H1:ci]]). [Keep one:] (A1, H2 superior) The gain exceeded that of a generic rewrite fused the same way, so it is attributable to the abstraction instruction rather than to rewriting in general; [H3 sentence: superior to the faithful rewrite / H3 not superior]. (A2, H2 not superior) The gain was not shown to exceed that of a generic rewrite fused the same way, so we can attribute it to LLM rewriting plus fusion, not specifically to abstraction. The improvement costs one model call and about [[x]] GPU-seconds per query and [[harm check result]] on in-domain recall. The effect is measured against citation-derived labels on one benchmark with one model and encoder.

**Branch B — H1 practically equivalent.**
On the DAPFAM test split, fusing a functional-abstraction rewrite with the original query did not change cross-domain recall at 200 by more than 0.010 in either direction (OUT Recall@200 [[R2-OUT:H1:mean]], 95% CI [[R2-OUT:H1:ci]]). H2 and H3 were not tested. At one model call and about [[x]] GPU-seconds per query, abstraction-fused acquisition does not offer a practically relevant gain in this setting. The exposure analysis shows that the rewrite does rescue some queries but displaces a similar number ([[n]] rescued, [[n]] displaced). Gains smaller than 0.010 cannot be excluded.

**Branch C — H1 inconclusive or inferior.**
On the DAPFAM test split, we could not show that fusing a functional-abstraction rewrite with the original query improves cross-domain recall at 200 (OUT Recall@200 [[R2-OUT:H1:mean]], 95% CI [[R2-OUT:H1:ci]], classified [[R3:H1]]). H2 and H3 were not tested. [If INFERIOR:] The fused system retrieved fewer known cross-domain positives than the baseline. [If INCONCLUSIVE:] The interval is too wide to rule out either a small loss or a gain larger than 0.010; the planned power was limited (section 8). The exposure analysis shows [[n]] rescued and [[n]] displaced OUT queries, and the in-domain harm check shows [[result]]. This negative result is consistent with Paper 53's finding that candidate exposure, not ranking, limits cross-domain recovery, and it indicates that a single rewrite of the query does not by itself solve exposure.

## 10. Reproducibility and cost

- Frozen protocol, prompts, schemas and analysis code: [protocol](plans/PAPER1-ACQUISITION-PROTOCOL-DRAFT-20261113.md), [freeze manifest](../audits/ptp-automatic-preparation-20261112/takeover-20261112/paper1-freeze/freeze-manifest.json), [test freeze manifest](../audits/ptp-automatic-preparation-20261112/takeover-20261112/paper1-freeze/test-freeze-manifest.json).
- Dev evaluation receipt: [S5 evaluation](../audits/ptp-automatic-preparation-20261112/takeover-20261112/paper1-s5-eval/terminal-observation.json); summary [PAPER1-S5-SUMMARY.json](../audits/ptp-automatic-preparation-20261112/takeover-20261112/PAPER1-S5-SUMMARY.json).
- Generation and retrieval jobs: one settlement receipt per batch under the [takeover audit folder](../audits/ptp-automatic-preparation-20261112/takeover-20261112/); Table R7 lists the receipts it read.
- Renderer and tests: [render_paper1_test_report.py](paper1-report/render_paper1_test_report.py), `tests/test_render_paper1_test_report.py`.
- Per-query values and raw model outputs stay private; only aggregates are published.

## References

- [DAPFAM] Ayaou, I., Cavallucci, D., and Chibane, H. DAPFAM: A Domain-Aware Family-level Dataset to benchmark cross domain patent retrieval. arXiv:2506.22141; Array (2026).
- [PANORAMA] Lim, H., et al. PANORAMA: A Dataset and Benchmarks Capturing Decision Trails and Rationales in Patent Examination. NeurIPS 2025 Datasets and Benchmarks; arXiv:2510.24774.
- [PatEx-Gym] PatEx-Gym / PatEx-Bench: agentic prior-art search. arXiv:2610.33503 (2026).
- [PatentAgentBench] Hu, et al. PatentAgentBench. arXiv:2610.35031 (2026).
- [Paper 53] Srihangpiboon, S., et al. Diagnosing Near-Zero Instruction Effects in Cross-Domain Patent Reranking. iSAI-NLP (IEEE). [Verify author list, year and pages before submission.]
- [Query2doc] Wang, L., Yang, N., and Wei, F. Query2doc: Query Expansion with Large Language Models. EMNLP 2023.
- [HyDE] Gao, L., Ma, X., Lin, J., and Callan, J. Precise Zero-Shot Dense Retrieval without Relevance Labels. ACL 2023.
- [RRF] Cormack, G. V., Clarke, C. L. A., and Büttcher, S. Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods. SIGIR 2009.
- [PaECTER] Ghosh, M., et al. PaECTER: Patent-level Representation Learning using Citation-informed Transformers. arXiv:2402.19411; PLOS ONE (2026).
- [PatenTEB] PatenTEB: a patent text embedding benchmark. arXiv:2510.22264.
- [PHAGE] Yoo, Y., Xu, Q., Wu, Z., and Cao, L. Heterogeneous Dependency Graph-Guided Attention for Patent Representation Learning. arXiv:2605.10073.

Author lists marked "et al." and venue details must be checked against the primary records before submission.

## Appendix A. Graph track (feasibility only)

The relation-extraction (graph) track did not pass its frozen feasibility gate on the dev pilot and is not part of any comparison in this paper. Its designs, gates and outcomes are recorded in the protocol (section 9) and the [development history](PAPER1-DEVELOPMENT-HISTORY.md).
