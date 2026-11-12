# Paper 1 protocol amendment: query-side acquisition of cross-domain prior art on DAPFAM

Date: 13 November 2026. Status: **DRAFT_FOR_OWNER_REVIEW, NOT FROZEN.** Nothing in this document authorizes a dispatch. It becomes binding only after owner review, as a dated freeze commit with hashes (section 11).

Inputs:
- [owner requirements](../../audits/ptp-automatic-preparation-20261112/takeover-20261112/owner-paper1-requirements.json) (interview, 13 Nov 2026);
- [MASTER-PLAN §1–10](../../../../MASTER-PLAN.md);
- [related-work audit](RELATED-WORK-AUDIT.md);
- [comparability matrix](DAPFAM-PAPER-COMPARABILITY.md);
- [native stages](NATIVE-STAGES-20261112.md).

## 1. Disclosure of what was already seen (before this draft)

Reviewers must be able to see everything below. The manuscript will repeat it.

1. **B0 native dev** (474 queries) is measured.
   - OUT: 349 eligible queries, Recall@200 = 0.14772.
   - Exposure at 200: 136 of the 349 have at least one known positive in the top 200; 213 have none.
2. **SACR faithful, pilot-20** (a subset of dev) was evaluated before this draft:
   - OUT (16 eligible): Recall@200 0.2284 → 0.2354; 2 queries better, 0 worse, 14 ties.
   - Exposure strata: both 9, neither 7, SACR-only 0, B0-only 0.
   - So SACR rescued no OUT query.

   This observation **motivated** the new arms. It is a dev observation, not evidence for them.
3. **Earlier SACR rounds R1–R7 and the synthetic, native and failure history.** All are preserved and reported as engineering and fidelity history.
4. **Graph track.**
   - Extractor v2: 2.7% query coverage.
   - Extractor v3: G1 PASS, G2 FAIL (8 of 20 pilot queries), G3 PASS.
   - An owner post-hoc override of G2 was recorded. In this paper, however, Graph is reported **only** as a feasibility/negative arm (section 9), with no further GPU work.
5. **The new arms have not been run on any DAPFAM query.** These are generic rewrite, functional abstraction and the fusions. No new-arm output or score exists at drafting time.
6. **Protected test.** No query text, qrels or outcome of the test split (773 queries, 556 OUT-eligible) has been opened.

## 2. Question and contribution

Paper 53 showed that reranking is limited by exposure. Our dev B0 leaves 61% of OUT queries with no known positive in the top 200. Faithful reformulation (SACR) stays in the same embedding neighbourhood.

**Question:** does an LLM rewrite that **abstracts away application-domain vocabulary**, keeping only function, mechanism and problem, bring cross-domain prior art into the candidate pool that dense retrieval misses? Is that gain specific to abstraction, rather than to LLM rewriting in general, and what does it cost?

**Contribution type** (owner: method + diagnostic):
- (a) a functional-abstraction query arm, used fused with the original query;
- (b) a controlled comparison against faithful and generic rewrites at matched or reported cost;
- (c) an exposure/rescue/displacement diagnostic that separates acquisition from ranking.

Positive, null and negative outcomes are all reportable. Paper 53 is cited in motivation and related work only, not as the central framing.

## 3. Systems (arms)

All arms use the same pinned resources: native TA query text, the 45,336-family TAC corpus, the existing PatEmbed-large passage vectors, query prefix `encode query for different document retrieval: `, MaxP family aggregation, and the top-200 cutoff. These are as in the pilot retrieval stage, with no corpus re-encoding.

| Arm | Query-side text | LLM calls/query | Status |
|---|---|---|---|
| **B0** | Original TA query | 0 | Measured (dev) |
| **SACR** (faithful control) | Frozen native v5 configuration: marking v5 + review v3; screened candidate, otherwise original-query fallback | ≤2 | Pilot-20 seen; full-dev approved, not run |
| **GR** (generic rewrite control) | One Query2doc/HyDE-style generation: "write a patent abstract that would be relevant prior art for this query". No domain or abstraction instruction. | 1 | New |
| **FA** (functional abstraction, the method) | One generation restating the query's own technical function, mechanism, problem and operating conditions in domain-neutral vocabulary (section 4) | 1 | New |
| **F-SACR, F-GR, F-FA** | Reciprocal rank fusion of B0 with the arm's top-200: RRF k = 60, union, re-cut to 200; ties broken by B0 rank, then family ID | — | CPU only |

Standalone arms (SACR, GR, FA) are reported descriptively. Fused arms are the deployable systems and carry the confirmatory tests.

**Matched cost.**
- GR and FA use the same model (Qwen3-8B fp16, greedy), the same decoder and the same output-length cap. The cap is declared in the freeze.
- SACR uses up to 2 calls. Its extra cost is reported, not equalized.

**Fallback and denominator.**
- Any GR/FA failure (input limit, grammar refusal, unknown backend state) produces original-query fallback for that query.
- Every query stays in the denominator.
- Failure counts are reported per arm.

## 4. FA and GR generation contract (to be frozen)

**FA output.** A grammar-constrained JSON object, with fields:
- `function` (what the invention does);
- `mechanism` (how);
- `problem` (what it solves);
- `conditions` (stated quantities and constraints).

Each field is a string with a declared `maxLength`. The encoded text is the fields concatenated in schema order.

The prompt instructs the model to:
- use only information stated in the query;
- replace application-domain nouns (device, clinical, product names) with generic functional terms;
- keep stated quantities;
- add no new technical content.

Short instruction-level examples come from **authored** non-DAPFAM text only.

**GR output.** One plain-text abstract under a matched JSON wrapper and length cap. It gets no abstraction or domain instruction.

**Engineering safeguards reused from the native run:**
- LMFE grammar with `CompleteJsonEOSGuard`;
- `max_consecutive_whitespaces=48`;
- `force_json_field_order=True`;
- an input-token cap checked before load, with fallback when exceeded;
- escape-safe strings.

**No semantic review stage for FA/GR.** Fidelity of abstraction is therefore **not certified**. This is a stated limitation, consistent with the owner decision to use no human audit and no LLM judge. A deterministic lexical check is reported descriptively: the share of stated numeric tokens retained, and the share of query domain nouns removed. It is not a gate.

**Allowed revision.** At most one predeclared prompt/schema revision, triggered only by an **engineering** failure on authored synthetic examples. No revision may be triggered by any DAPFAM outcome.

## 5. Endpoints

**Primary** (owner choice): OUT Recall@200, macro over OUT-eligible queries, under the pinned native evaluator. A missing output scores zero.

**Confirmatory comparisons** use the test split, with fixed-sequence gatekeeping at two-sided α = 0.05. Each step is tested only if the previous one rejects:

| Step | Comparison | Type | Hypothesis |
|---|---|---|---|
| H1 | F-FA vs B0 | superiority | Abstraction-fused retrieval acquires more known OUT positives |
| H2 | F-FA vs F-GR | superiority | The gain is specific to abstraction, not generic rewriting |
| H3 | F-FA vs F-SACR | superiority | Abstraction beats faithful reformulation |

**Equivalence margin.** δ = 0.010 absolute OUT Recall@200 (about 7% of B0 dev).
- It is fixed now, before any new-arm output.
- It is used to interpret non-rejection: "the 95% CI excludes gains larger than δ" or "inconclusive".
- If H1 is not rejected and the whole CI lies within ±δ, we report **practical equivalence** for that comparison only.
- δ will not be changed after dev or test results.

**Harm check** (secondary, non-inferiority): IN Recall@200 and ALL Recall@200 for F-FA vs B0, with margin 0.020.

**Secondary/descriptive** (no multiplicity claim):
- Recall@100, nDCG@10, nDCG@100 for ALL/IN/OUT;
- per-arm exposure at 200;
- four exposure strata (both / arm-only / B0-only / neither) with rescue and displacement counts;
- paired wins/losses/ties;
- coarse first-positive rank bins;
- unjudged share in the top 10 (descriptive only, not a relevance claim);
- failures and costs.

## 6. Statistical analysis

- **Unit and pairing.** Per-query paired differences on identical query sets.
- **Primary interval.** Cluster bootstrap over connected components of the query-to-positive-target graph, so queries sharing targets resample together. 10,000 resamples, percentile 95% CI, fixed seed declared in the freeze.
- **Component disclosure.** The number of components and the largest component's share are reported. If one component exceeds 50% of queries, a query-level paired bootstrap and a paired sign-flip randomization test (10,000) are reported as sensitivity analyses. The primary decision does not change.
- **Power.** After dev and before test, the dev paired SD per comparison will be used to compute the minimum detectable effect at 80% power for n = 556.
  - This is a planning statement. It does not change δ, endpoints or arms.
  - If power is low, the paper says so.
- **No significance claims on dev.** Dev results are descriptive and used only for engineering readiness and the owner checkpoint (section 8).

## 7. Stages and resources (estimates, to be measured)

| Stage | Content | Estimate |
|---|---|---|
| S1 CPU qualification | FA/GR grammar cases (valid, too-long, key-order, whitespace, escape) and fixture | ≤120 s CPU booking per job |
| S2 synthetic GPU smoke | FA and GR on one authored example each; ≤2 calls, ≤1800 s | <1 GPU-h |
| S3 technical pilot | FA and GR on pilot-20 for throughput/failure only. Retrieval of pilot-20 for the new arms is **not evaluated separately**; it is subsumed in S4 | <1 GPU-h |
| S4 full-dev generation | SACR (6×79 batches, approved), FA, GR on 474 dev queries | SACR ≈13 GPU-h (measured ~98 s/query); FA, GR ≈4–8 GPU-h each (unmeasured) |
| S5 full-dev retrieval + evaluation | Encode arm texts, search, fuse, evaluate dev | <1 GPU-h + CPU |
| S6 owner checkpoint | Section 8 | — |
| S7 freeze | Section 11 | — |
| S8 test | SACR, FA, GR generation on 773 test queries; retrieval; one evaluation | ≈21 + 2×(6–13) GPU-h |

**Totals.**
- Dev ≈ 25–30 GPU-h, inside the 128 h full-dev cap.
- Dev + test ≈ 60–75 GPU-h, inside the ~186 h GPU remaining (669,013 s at generation 93).
- Every stage is reserved from measured throughput before dispatch.
- One GPU job at a time.
- A new `test` stage envelope and predecessor (`full_dev`) need a journal amendment at freeze time.

## 8. Owner checkpoint after dev (no test before it)

After S5 the owner reviews the dev results. The owner may:
- (a) proceed to freeze and test **with the confirmatory plan in section 5 unchanged**; or
- (b) stop. The paper is then reported as dev-only, with that limitation.

The checkpoint **cannot** change arms, prompts, δ, endpoints, fusion parameters or the test order. That prevents selection on dev outcomes, while keeping the owner's request to discuss before continuing when results do not answer the question.

## 9. Graph: feasibility/negative section

Report:
- extractor designs v2/v3;
- census coverage (2.7%, then 52.3% of dev queries);
- frozen gates G1–G3 and their results (G2 FAIL, 8 of 20);
- the 14,123-relation screening scope;
- the owner's post-hoc override (`POST_HOC_OWNER_OVERRIDE_OF_FROZEN_FEASIBILITY_GATE`);
- the decision not to run Graph retrieval in Paper 1.

No Graph retrieval score is claimed. Graph does not enter any comparison table.

## 10. Threats to validity (stated in advance)

- **Incomplete judgments.** Unjudged is not negative. A rewrite that surfaces unlabelled relevant families is under-credited. There is no human audit and no LLM judge (owner decisions).
- **No fidelity certification for FA/GR.** Gains could come from content drift; the descriptive lexical checks only partly address this.
- **Single dataset.** MTM transfer is out of scope (ST2).
- **Single model family** (Qwen3-8B) **and single encoder** (PatEmbed-large).
- **Dev observations.** The SACR pilot motivated FA, and that is disclosed. The test split is untouched.
- **Shared-target dependence** (section 6).
- **Comparability.** Published DAPFAM numbers use other cohorts, models and metrics. They appear only as literature context, never as a leaderboard (see the [comparability matrix](DAPFAM-PAPER-COMPARABILITY.md)).

## 11. Freeze contents (to be produced after owner review)

A dated commit containing:
- FA/GR prompts and schemas with hashes;
- the decoder and length caps;
- the SACR v5 configuration pin;
- the encoder/prefix/vector/model pins;
- the RRF parameters and tie rule;
- the evaluator hash;
- the bootstrap seed and resample count;
- δ and the non-inferiority margins;
- the gatekeeping order;
- stage envelopes and call/time caps;
- the failure/fallback rules;
- this disclosure list.

Changes after freeze are only engineering-fault repairs within existing authority, each recorded. There are no outcome-driven retries.

## 12. Venue (owner: not fixed)

Design to the stricter information-retrieval journal standard (e.g. IP&M or JASIST): a test split, a predeclared margin, a cluster-aware CI, cost and failure accounting, and controls for generic rewriting. World Patent Information remains the domain-fit fallback. Choose after results. No acceptance is promised, and nothing will be submitted, nor any publisher terms accepted, on the owner's behalf.
