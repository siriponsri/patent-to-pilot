# Paper 1 supplement: DAPFAM comparison and Paper 53 alignment

Date: 2026-11-10. Status: SOURCE_REVIEWED / OUR_NATIVE_DEV_BASELINE_MEASURED / OTHER_ARM_COMPARISONS_NOT_RUN.

Owner requested this additional task within Paper 1, not a replacement goal or permission to open protected tests. Parent remains sole repository writer. Existing models, vectors, resource ledger and 60-card total human-review ceiling remain binding.

## 1. What counts as apples-to-apples

**Direct replication** requires identical dataset revision, query IDs and eligible denominators, query/document fields, candidate universe, positive-qrel/domain rules, metric/ideal ranking/cutoff, model revision/precision/prefix/pooling, passage construction, family aggregation, tie rules and configuration-selection protocol. Matching a dataset name or metric alone is insufficient.

**Matched development comparison** runs frozen feasible methods on our same authorized dev cohort and evaluator. It estimates differences on that cohort; it does not reproduce published all-query scores. **Literature context** shows published numbers with their protocol, without subtracting them from our score, ranking our method against them, or claiming superiority.

Current direct-replication status for every supplied paper: NOT_ESTABLISHED. Published all-query evaluation cannot be reproduced under the current closed-test rule. Do not inspect protected query IDs or outcomes to improve the match. No new model acquisition, corpus encoding, training, or paid calls are authorized by this supplement.

## 2. Source inventory and coverage

Paths below are relative to repository `literature-review/pdfs/02-patent-ai/`, except Paper 53. PDF page numbers are one-based file pages.

| Source | SHA256 | Coverage in this review |
|---|---|---|
| 01_dapfam.pdf | 384dff3e3ac0fe6d2064572bb0322ef4b059c82fcbd703e680a3b524e7120c27 | Opening, pp17–21 and25–26; protocol and selected main/hybrid results |
| 38_dapfam_arxiv_v2_duplicate.pdf | Same as01, byte-identical | Duplicate verified; not independent evidence or a second replication |
| 59_dapfam_array2026.pdf | 276251946dfcbcea96112657e54b84916ab5e2a40e4db6cf614b7ab56baca04f | Opening, page index, pp9–11; Table9 visually checked on p11 |
| 41_patent_embeddings_22_models_2026.pdf | 07aefa5f1673e1825b696df49ff2d5c0b79c02fe579f131a850f6baf8d0458d9 | Opening, page index, pp10,21–22; Tables19–20 visually checked on p22 |
| Paper53: `C:/Users/User/Desktop/myDegree/IS/IS_1/paper53_ieee_express.pdf` | 09d580402a49739baedb2281be16ba0a275a1c5ecdb711dfb21c93c8aba3ddbe | All6 pages text reviewed; p4 figure visually checked |

This is targeted protocol/table review, not a full review of every page or a full preprint-to-journal diff. Raw PDFs and extracted text are not added to the publication commit.

## 3. Protocol matrix

| Dimension | Dataset papers01/38 and59 | Embedding paper41 | Our planned native development comparison |
|---|---|---|---|
| Cohort | 1,247 queries,45,336 families | Public1,247-query split, no resplit/subsampling stated | Original dev only:474 queries; eligible ALL474/IN450/OUT349;45,336-family corpus |
| Query/corpus fields | Multiple query views; BM25 best TA; dense best TAC; corpus full text/TAC/passages varies | TA,TAC,abstract,claim1 views; exact query-to-document view pairing needs artifact verification | Exact native TA query; historical TAC corpus bytes pinned |
| Dense model | Snowflake arctic embed m v2.0,int8 | DAPFAM table includes four base families and training variants; patembed-base, not large | Existing PatEmbed-large fp32, pinned vectors; no re-encoding |
| Passage/aggregation | Token windows64–8192; selected maxima/avg_top3/avg/sum; best dense p2048maxP, IN footnote p1024avg_top3 | Frozen embeddings/exact cosine described; view-specific preprocessing still requires code evidence | Existing384-word windows,64-word overlap, max-family aggregation to be bound to as-run artifacts |
| Relevance/candidates | Section5.1 language about disjoint subsets/IPC leaves candidate filtering ambiguous | Positive scores binary; domain_rel partition; exact implementation needed | Pinned native adapter: positive qrels first, IN/OUT qrel partitions; full corpus candidates, no domain mask |
| Metrics | Macro nDCG@100 and Recall@100 | nDCG@10; other retrieval metrics described | Primary proposed OUT Recall@200 retained; nDCG@100/Recall@100 bridge; descriptive nDCG@10 proposed before outcomes |
| Selection | Best settings across grids; some cells use different configurations; RRF tuned on ALL | R0 zero-shot and WIPOAT-trained R3/R4; not a single22-model DAPFAM table | Freeze before scoring; no new hyperparameter search to match a published winner |
| Status | Literature context | Literature context | Matched dev comparisons only after execution and gates |

Unresolved source issues must remain explicit: paper41 p21 describes approximately11million families, conflicting with the45,336-family DAPFAM description; Table20 caption refers to a full22-model comparison in Table19, while that table contains a smaller set of base families/variants. Do not infer actual evaluated corpus or query pairing from these statements. Paper41 IN/OUT columns must not be silently treated as the TAC-view cell. Resolve from released manifests/code if available without protected-data access; otherwise retain UNKNOWN.

## 4. Published reference values, not our results

Array Table9,p11 (also preprint Table15,p20). Values are reported, not independently reproduced.

| Method | nDCG100 ALL/IN/OUT | Recall100 ALL/IN/OUT | Selected input |
|---|---|---|---|
| BM25 document | .2728/.3032/.0525 | .3278/.3949/.1368 | TA query/full text corpus |
| BM25 passage | .2929/.3275/.0589 | .3468/.4175/.1521 | TA/p4096maxP |
| Dense document | .3055/.3477/.0509 | .3627/.4437/.1332 | TAC/TAC |
| Dense passage | .3381/.3839/.0592 | .4072/.4973/.1538 | TAC/p2048maxP; IN best uses p1024avg_top3 |

These best-by-partition cells are not proof that one frozen joint configuration achieves every cell. Preprint Table18,p25 uses a dense passage row .3381/.3822/.0590 and Recall100 .4072/.4950/.1552, then hybrid K30 .3475/.3913/.0625 and .4171/.5062/.1653. Preserve that table's own baseline; do not combine it with Table9's selected best row. Document hybrid tables also have different dense reference cells.

Paper41 Table19,p22: zero-shot patembed-base nDCG10 TA=.5326,TAC=.5647,abstract=.5258,claim1=.5393,mean=.5406,IN=.5423,OUT=.0484. Zero-shot Qwen3-embedding0.6B OUT=.0511; BGE-M3 OUT=.0423; BM25 OUT=.0335. These are nDCG10, not nDCG100. The IN/OUT-to-view mapping remains unresolved. Table20 training results are outside our no-training scope. Neither these values nor Paper53's fixed-pool reranker scores are valid numerical baselines for our current dev experiment.

Native B0 dev now measured in [receipt](../../audits/ptp-native-dense-preparation-20261110/README.md): OUT349 queries,Recall200=.14772,Recall100=.09732,nDCG100=.04490,nDCG10=.02328. These remain separate from the published all-query rows. SACR/S/G score cells: **NOT_RUN**. No cross-paper score delta, percent improvement or significance claim is computed.

## 5. Paper 53: use its diagnostic structure with correct boundaries

Paper53, *Diagnosing Near-Zero Instruction Effects in Cross-Domain Patent Reranking*, studies fixed top100 pools with patembed-base,TAC and Qwen3-Reranker0.6B on692 held-out OUT queries (724 sensitivity;32 earlier exploration queries excluded). Its original raw/qrel/preprocessing/frozen-pool mapping and per-query outputs are reported unrecovered. Treat its results as reported, not reproduced; do not import its cohort, instruction arms or tuning decisions.

Adopt for Paper1:

1. Report candidate exposure to known positive families separately from ranking quality, with eligible denominator and first-positive rank bins. Non-exposure reflects available judgments, not proof of semantic irrelevance.
2. Report paired wins/losses/ties and absolute effects with uncertainty, including zeros and failed arms. Non-significance does not establish equivalence.
3. For genuinely identical fixed pools only, use the descriptive accounting identity `mean(delta_all) = exposed_fraction * mean(delta_exposed)` when both systems necessarily score zero for all unexposed queries. Verify that condition rather than assuming it.
4. SACR/S/G may change pools. Use four exposure strata (both,A-only,B-only,neither), recovery and displacement counts, plus the weighted paired differences over all strata. Do not apply the fixed-pool identity or claim a causal mechanism from this decomposition.
5. Freeze endpoint/selection alignment and inference families before retrieval outcomes. Keep Paper1's existing primary endpoint and grouping rules; do not copy Paper53's692-query denominator, nine-test family or post-hoc dependence treatment.
6. Plan a configuration table, absolute endpoint table, paired-effect plot, exposure/win-loss figure and failure/fidelity/time/resource table. Separate construction cost, query cost and amortized cost; dataset-paper query timings exclude indexing/encoding.

## 6. Prospective execution and acceptance

- Add descriptive nDCG@10 from the same saved rankings alongside nDCG@100/Recall@100/200, before any new native dev scores. This is a metric bridge, not an additional confirmatory hypothesis or a primary-endpoint change. Freeze exact metric implementation and denominator policy with the run manifest before execution.
- Native B0 has completed the staged dev runtime/evaluator, vector/passage/model binding and isolation checks; measured results are linked above. Carry the same bindings into subsequent arms. Source review alone does not establish parity for a new arm.
- For each result row record query cohort hash, eligible counts per partition, qrel semantics, fields, candidate scope, preprocessing, model/pooling/precision, family aggregation, cutoffs, ties, tuning history, failure policy and cost scope. Mark unknowns explicitly.
- Evaluate feasible authorized arms against B0 on identical dev inputs and relevance rules. Publish literature-context rows in a separate table, not an apparent common leaderboard.
- Any exact published-model reproduction requiring new corpus encoding, training or protected queries remains out of scope. Report the gap rather than silently relaxing the owner's rules.
- Additional paper comparison itself consumes zero human fidelity cards and zero model calls. Existing60-card ceiling across all benchmarks/configurations is unchanged; S/G allocation remains a separate pre-execution gate.

Completion of this supplement requires an implemented metric contract, actual authorized measurements and final comparability labels. The source/protocol matrix, implemented metric contract, actual B0 dev measurements and descriptive exposure are complete. Direct published-score replication is NOT_ESTABLISHED; paired method comparisons are NOT_RUN because no comparator has passed all required gates. Earlier configurations failed prerequisite gates; R5 Graph screening is active under the separately approved bounded plan. No method-quality improvement is claimed.

## Descriptive exposure of the existing baseline

These fixed coarse bins were declared before aggregation of the existing sealed
dev per-query metrics. They are not exact first-positive ranks. No retrieval was
rerun and no new method scores were inspected. All nine recomputed macro recall
values match the original published dev receipt.

| Partition | Eligible | First positive 1–10 | 11–100 | 101–200 | None at 200 |
|---|---:|---:|---:|---:|---:|
| ALL | 474 | 308 | 115 | 19 | 32 |
| IN | 450 | 299 | 110 | 21 | 20 |
| OUT | 349 | 37 | 67 | 32 | 213 |

The OUT baseline exposes at least one known positive for 136/349 queries at200;
213/349 expose none. This is distinct from macro Recall@200=0.14772. Unexposed
does not mean semantically irrelevant: judgments are incomplete. IN/OUT eligible
populations overlap. Paper53-inspired paired wins/losses, rescue and uncertainty
analyses are NOT_RUN because no comparator passed the prior gates.

The isolated aggregation used0.575023457 seconds whole supervisor time,1CPU,
512MiB memory limit,0GPU/model calls, no network and no protected-test mounts.
Peak memory was not measured. Four hand-computable validation fixtures passed.
