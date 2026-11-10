# HT-ST1: DAPFAM query abstraction versus fixed relation traversal

Updated: 10 November 2026. Status: DETAILED_PROTOCOL_PROPOSAL / NOT_FROZEN / NOT_RUN.

Owner-approved review allocation amendment: DAPFAM SACR30 + shared S/G extraction configuration30, each up to20 risk/escalation +10 sentinel,60 total across all configurations. MTM allocation0 pending explicit redistribution of remaining cards. No automatic borrowing or reduction of SACR coverage. Existing sampling/critical-error stop/incomplete no-pass rules retained. This replaces prior benchmark-based30/30 allocation, not the full protocol freeze. Corpus/alias sampling specification remains required before S/G extraction/review.

Owner-requested supplement: [DAPFAM paper comparability and Paper53 alignment](DAPFAM-PAPER-COMPARABILITY.md). Preserve primary OUT Recall@200; prospectively add descriptive nDCG@10 from the same rankings for metric alignment, subject to manifest freeze before scores. Published all-query/model-different numbers are contextual, not direct baselines. Adopt exposure and paired win/loss diagnostics with separate treatment of changed candidate pools. Native baseline and new method scores remain NOT_RUN.

[Master](../../../../MASTER-PLAN.md) · [Component/evidence index](../../../../INDEX-PLAN.md) · [Related work](RELATED-WORK-AUDIT.md)

## 1. Question, hypotheses and contribution

Working title: **What Does Structure Buy in Cross-Domain Patent Retrieval? A Controlled DAPFAM Comparison of Query Abstraction and Relation Traversal.**

RQ1: Does a source-linked selective query abstraction improve native OUT known-family recovery beyond a strong dense anchor and matched generic/source-anchor controls?

RQ2: Does a fixed cross-record traversal add recovery beyond searching the **identical extracted information** without traversal?

RQ3: Which intervention is preferable when construction, query processing, failures and maintenance are counted?

Candidate confirmatory contrasts: H1, G minus S on native OUT query-macro Recall@200; H2, G minus frozen SACR on the same endpoint. Both directions are uncertain. Proposed practical margin is 0.01 absolute recall, **for owner/statistical review before freeze**, not a threshold chosen from outcomes. A separate SACR mechanism claim requires its generic/preserving and mean/bottleneck development controls; H2 alone cannot establish that mechanism.

Possible contribution: controlled attribution of representation versus retrieval topology, with source-fidelity and amortized cost evidence on an incomplete-judgment patent benchmark. Broad graph/LLM/functional-search concepts are prior art. A negative finding can delimit what is worth building but is not automatically a publishable contribution.

## 2. Inputs, exposure and native task

- Proposed primary configuration: **TA query -> TAC corpus**, following the native adapter, not historical claims-inclusive query R2. Allowed input to every arm is the same exact native query text. Record encoder token coverage and actual text consumed by each extractor/scorer.
- Pin MTEB revision `9242b36a1d400fc8c3af573e6a6e0705c0b96e3d` and dataset revision `780f4011d60297fc6e97a4119b0c516d13afea2d` or prospectively amend with reasons. Recorded benchmark size is 1,247 queries /45,336 target families; actual safe-input manifest must verify these counts.
- Keep the original project 474-dev/773-protected query assignment. The old 349/556 strict-OUT counts are **not accepted native OUT denominators**. Authorized curator must establish eligible native counts without exposing protected labels to development.
- IN/OUT filters positive qrels, not candidates. Search the full native corpus for either partition. Positive judgments are binary after the declared score predicate. No-positive queries are omitted from that partition's metric denominator and counted; eligible queries with missing rankings score zero.
- Do not open mixed metadata, protected qrels, private test rankings, or source packs containing test labels. Runtime projection and evaluator projection are distinct. Opaque split hashes/receipts may be inspected without parsing protected rows.
- Historical dev has extensive exposure and a reported 374-query shared-target component. Preserve it; do not manufacture independent folds. Historical all-query published scores are public exposure, not secret test labels, and must be disclosed when claiming a project holdout.

## 3. Reusable implementation and open gates

Reuse `evaluation/dapfam_native.py`, `evaluation/dapfam_acquisition.py`, `research/mtm_runtime.py`, existing full-index `sacr_acquisition.py`, selector, binding/journal/outcome components and source/vector identity checks. Reuse historical vectors only after corpus/passage/order/model binding and TA-query baseline parity. Existence/fixtures do not attest a real run.

Native evaluator differential fixtures passed historically. SACR generation remains blocked by SYN003's source-order failure; accepted rejected-family continuation and fidelity ledger are incomplete. Source-anchor/matched-coverage controls remain prospective. S/G corpus extraction, alias registry, adjacency/operator and index do not exist as validated research components in the inspected evidence. Do not label `adaptation/engine.py` a research retrieval graph.

## 4. Four-system final panel and development controls

| Arm | Frozen behavior | Evidence it isolates |
|---|---|---|
| HT-ST1-B0 | PatEmbed-large passage anchor; native TA input; fixed preprocessing, prefixes, truncation, MaxP and family-ID ties | Reference retrieval without new query/corpus semantics |
| HT-ST1-SACR | One viable fixed source-preserving configuration; <=3 views, full-index acquisition <=200 families/view, union <=600, fixed selection to 200 | Practical query-side intervention |
| HT-ST1-S | Same grounded corpus relation records, text fields, aliases and query analysis as G; full structured-index retrieval with **no cross-record expansion** | Extracted/normalized information without topology |
| HT-ST1-G | S inputs plus one deterministic, bounded, source-linked cross-record traversal | Increment attributable to the declared traversal procedure |

Do not add the adaptive agent as a fifth final system. Published PHAGE, PaECTER or PatenTEB scores are literature context. A new comparator implementation requires rights, exact matching configuration and measured resources; if essential, explicitly revise the final panel before freeze. No fabricated reproduction label.

Small development-only control menu, fixed before new outcomes:

1. Generic/preserving views × mean-only/bottleneck selector on identical profile/passages and the same union **within each selector contrast**. Distinct unions answer acquisition questions, not pure selector questions.
2. Deterministic source-anchor/compact query control and text-coverage-matched extraction to distinguish preservation from merely reading more source tokens.
3. S/G with identical record and alias hashes, entry seeds, terminal scoring and allowed query representation. S must have the same normalized descriptors and relation fields, including serialized local relations. Hiding useful alias/edge text from S creates an information confound.
4. S-depth: deeper non-traversing structured search under G's record/score-work envelope. B0 deeper-search diagnostic if it is needed to test “more search” rather than topology. Final output remains 200.
5. One type/degree-preserving graph rewiring or edge-removal diagnostic, preserving local record text/alias access. Perturbed links are artificial diagnostic artifacts and cannot support product explanations.

Controls stay on dev unless explicitly included in the final multiplicity plan. A final claim cannot be rescued by a favorable unregistered control.

## 5. SACR contract to close

Retain raw source spans, roles, quantities, units, comparisons, polarity/direction and condition attachment. Source-order blocks <=8; uncertain attachment is unresolved. Do not remove anatomy/material/context automatically. Exact quotes establish source integrity, not semantic preservation.

The implemented local score is `max_block max_passage [(1-beta)*mean_i z_i + beta*min_i z_i]`, where z=(1+cosine)/2, with the minimum within a single passage. Max over blocks permits partial requirement matching; it is not an all-constraints entailment score. Proposed beta/alpha=0.5 are draft defaults; freeze after bounded dev without test access. Rank normalization depends on the union.

Apply the adopted failure rules symmetrically to controls: unusable normally terminated generated families are rejected and charged; retain only independently valid anchor/compact work. No text/JSON repair, reordering of failed output, replacement calls or selective query deletion. Infrastructure/unknown termination remains unresolved until checked. The failure-continuation implementation must precede new scientific use.

Keep the adopted automation-first fixed fidelity sample and cumulative owner-card cap. A PASS is only `SOLO_SCREEN_AND_SENTINEL_GATE_PASS`, weaker than independent human validation. Unknown/critical errors stop the configuration. An anchor-only fallback does not demonstrate the selective method works.

## 6. Proposed minimal S/G operator to make review concrete

This is a proposed implementable operator, **not adopted code or a validated novelty claim**. Final numeric limits require feasibility measurements and a methods-log declaration.

**Record:** `relation_id`, raw/canonical publication ID and kind, family ID from sourced mapping, source revision/hash/field/span, action, operand, effect, explicit conditions, unresolved attachments, raw descriptors and normalized descriptor IDs. Keep one occurrence per grounded relation; do not merge whole patent families by lexical similarity.

**Aliases:** versioned raw-to-normalized mappings with provenance and ambiguity flags. Initial deterministic morphology/sourced lexical mapping only. A synonym link is a system inference unless explicitly supported; no gold/citation-derived equivalences. S and G receive identical accepted mappings. Unknown/ambiguous aliases do not create edges.

**Edges:** source-owner link; within-source explicit relation-role links; cross-record links through accepted same-role normalized descriptors. Preserve direction/type and qualify compatible explicit conditions. Similar shared words alone do not prove compatible mechanisms. No examiner/citation qrel edges in the technical-relation graph. Any separately sourced citation experiment is a different method.

**Entry and traversal:** score all indexed relation serializations with the common pinned structured retriever; take a fixed label-free entry set. Proposed engineering defaults:32 seeds, maximum 2 cross-record hops, fanout<=8 per expansion, <=512 visited relation records and <=600 candidate families; ties by immutable IDs; no random walk/model call at retrieval. De-duplicate visits and stop at the first reached bound; count empty/frontier-exhausted cases. These defaults can be rejected by resource/fidelity gates before outcomes.

**Scoring:** entry semantic score in[0,1], cross-record path score as the maximum over permitted paths of `entry_score * product(edge_weight) * 0.8^h`, with initial accepted-equivalence edge weight 1 and explicitly unsupported edges excluded. Store every contributing path. Final family selection uses the same frozen terminal source/passage scorer and anchor fusion for S/G; traversal changes acquired families only in the primary G−S mechanism comparison. Path-weight ranking is a separately declared dev diagnostic, not silently added to the terminal scorer. No learned weights or qrel-driven aliases.

**S behavior:** query the identical full relation index directly, take its fixed structured candidate budget, then use the same terminal scorer. S-depth equalizes relation-scoring/visit allowance where possible. Record indexed coverage, scanned/visited records, scored passages, families and actual latency; budgets need not yield identical compute, so report both.

**Failure:** missing/malformed relation records are counted per source/family, not replaced by gold-rich documents. Fix the fallback for extraction-empty families prospectively and apply it identically to S/G. Preserve B0 as the declared unchanged anchor when it is part of both systems. A graph built only on relevant targets or selected top pools cannot support full-corpus discovery claims.

## 7. Protocol, endpoints and analysis

Primary proposal: native OUT query-macro Recall@200. Report NDCG@100 for native published-protocol comparability and Recall@20/100, hit@20/100/200, MRR@100 as declared secondaries. Existing native wrapper implements NDCG/Recall; hit/MRR and component inference need reviewed fixtures before use.

Define `Recall@k=|known positives∩topk|/|known positives|`; `hit@k=1` if that intersection is nonempty. Preserve failed eligible queries as zero and show successes/failures separately. Novel candidate discovery is unjudged unless independently assessed; do not call every non-qrel result false positive. Report union known-positive exposure, rescue/loss versus B0, displacement during final selection and generation/fallback rates.

Paired analysis unit is the query with resampling by shared-positive/family component. Report query-macro estimate and group-weighted sensitivity, component count/sizes and leave-one-large-component-out diagnostics where declared. Do not force balanced four-fold CV by cutting a shared component. If too few independent groups exist for credible intervals, report descriptive intervals/limits and label confirmatory inference infeasible.

If H1/H2 are both confirmatory, apply Holm to their two tests and declare interval interpretation before final access. B0/IN/overall are secondary, with explicit multiplicity treatment if used for claims. A CI spanning zero and ±0.01 is inconclusive. Equivalence/noninferiority needs its own prospective margin/test; absence of significance is insufficient.

Before freeze fix all populations, denominators, endpoints, effect margins, tie rules, group mappings, candidate/visit caps, extraction and query fields, model/decoder/index hashes, failures/retries, cost rules and maximum final systems. Protected test remains closed until the owner authorizes the exact panel and one evaluation. Do not reopen it for ST3 tuning later.

## 8. Sequential work packages and acceptance

| Package | Permitted future input/output | Acceptance / stop |
|---|---|---|
| HT-ST1-W1 | Curator dev-only manifest -> native baseline receipt | Identity, eligible denominator and exact parity gate; stop on mismatch without altering old results |
| HT-ST1-W2 | Static SACR diagnosis -> viable declared configuration or explicit infeasibility | No consumed-smoke retry; accepted failure semantics and fidelity implementation required |
| HT-ST1-W3 | Authorized deterministic stratified engineering sample -> S/G schema/fidelity/throughput report | Sample chosen without qrels; same extraction S/G; no retrieval quality claim from small corpus |
| HT-ST1-W4 | Measured projection -> bounded full-corpus extraction decision | Construction+review+storage fits remaining **newly scoped** approval; otherwise stop or narrow scientific question transparently |
| HT-ST1-W5 | Fixed dev cohorts -> limited controls and frozen method choice | Preserve every configuration/attempt, reject outcome-driven expansion; independent writer review if available, otherwise disclose self-review |
| HT-ST1-W6 | Dated freeze + owner authority -> one protected comparison | At most 4 systems; no adaptive-agent insertion; no test-driven tuning |
| HT-ST1-W7 | All receipts -> manuscript/tables/reproducibility | Negative results retained; rights checked; no raw restricted release |

Owner review points are concrete run declarations/resources, final protocol/panel and release. Routine documentation/fixture fixes do not need repeated confirmation within scope. A missing local dependency blocks its branch only.

## 9. Resource and stop criteria

Do not inherit graph compute from the old SACR 72 h allowance. Obtain actual remaining journaled consumption and existing V100 slot/window before a future proposal. Measure sample source-length quantiles, windows/calls, extraction/normalization/validation time, memory, disk and failures. Project both full-corpus cost and rebuild/update costs with a conservative upper scenario. One-call-per-family at 10s already projects 126 h for DAPFAM; do not schedule it under 72h.

Proposed feasibility limits for discussion, not new permissions: one <=100-record label-free engineering sample; one fixed schema/prompt configuration; no training or new full-corpus encoder pass; stop on critical source/role/condition/alias defects, exceeded resource envelope, insufficient reviewed coverage or non-repeatable index identity. If SACR cannot be made viable within authorized work, document the failure and ask for a concrete panel revision before final freeze; do not replace it invisibly or abandon independent S/G specifications.

## 10. Reporting, risks and next action

Report all four systems and declared controls, extraction coverage by field/IPC/length, historical exposure, shared-target dependence, generation/fidelity failures, known-link judgment limits, training contamination uncertainty, cost amortization at declared query volumes and rights. Do not extrapolate to MedTech, inventive design success or customers.

Nearest-work distinctions and unresolved access are in [RELATED-WORK-AUDIT](RELATED-WORK-AUDIT.md). Before a novelty claim, resolve FOPNet's protocol inconsistencies and publicly available artifacts, inspect PHAGE v3 and exact comparator availability, and complete limited-access functional-search sources. None is a reason to open protected labels early.

**Next bounded action:** reconcile the existing curator staging attempt from allowed sanitized receipts; verify a dev-only native TA input and baseline binding; independently finish the S/G operator/resource declaration. This document does not launch those actions.
