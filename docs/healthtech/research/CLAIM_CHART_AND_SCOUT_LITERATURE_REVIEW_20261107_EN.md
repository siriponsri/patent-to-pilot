# Literature check: claim charts, FTO and cross-domain scouting (7 Nov 2026)

- **Status:** a quick, targeted review, not a systematic one.
  - Done on 7 Nov 2026 with web search and the HTML versions of the papers.
  - Some numbers come from page summaries. Re-check every number against the PDF before citing it.
- **Why now:** the owner asked whether to move from Solution Scout to an "examiner-verifiable claim chart" product, possibly extended to freedom to operate (FTO).
  - The advisor wants the next paper to connect visibly to the owner's published reranking paper (Paper 53: *Diagnosing Near-Zero Instruction Effects in Cross-Domain Patent Reranking*).
- **No decision is taken here.** Nothing was run; USD 0.

## 1. What already exists

| Work | What it does | Gold / evaluation | Key reported numbers | Relevance |
|---|---|---|---|---|
| **FiNE-Patents** (Knappich, Hätty, Razniewski, Friedrich; SIGIR '26; [arXiv 2605.02392](https://arxiv.org/abs/2605.02392)) | Splits a claim into features. For each feature, finds the passages of the closest prior art that disclose it, then predicts novelty | EPO European Search Opinions. 3,658 first claims, 21,464 cited passages (94% paragraphs). CPC G06, G10L, H04L, H04N only | Feature-level passage F1: best LLM 20.9 vs embedding baseline 10.6. Claim novelty accuracy: best LLM 69.1, but a claim-only BERT reaches 75.2 (shortcuts) | **This is the examiner-gold claim chart task, already published.** Passages are cited by identifier |
| **PatentAgentBench** (PatSnap; [arXiv 2610.35031](https://arxiv.org/abs/2610.35031), 26 Oct 2026) | 510 cases in 8 suites run by LLM agents with search tools, including **claim charting**, invalidity search, **patent FTO** and **design FTO** | Expert annotation and review. Patent FTO uses court infringement findings; invalidity uses invalidation and IPR decisions | Claim charting CP-F1 best 55.1 (30 cases). Patent FTO recall best 86.5. Design FTO at most 3.8. Invalidity: more than two-thirds of references missing under one harness ("the limit is missing references rather than poor ranking"). Evidence alignment scores 17–18.5 points below feature extraction | **Claim charting and FTO are both already benchmarked**, with frontier models and a commercial search service |
| **PatRe** ([arXiv 2605.03571](https://arxiv.org/abs/2605.03571), May 2026) | Office action and rebuttal generation from 480 USPTO records; settings with no references, oracle references and a noisy pool | Statute precision, decision accuracy, LLM judge, human check, reference citation accuracy | Decision accuracy about 50% for the best models. Models invent rejections; citations are hallucinated without evidence | The office-action response use case is taken. Grounding is checked only at reference level |
| **PANORAMA** (LG AI Research; NeurIPS 2025 D&B; [arXiv 2510.24774](https://arxiv.org/abs/2510.24774)) | PAR4PC (prior-art choice), PI4PC (pick the examiner-cited paragraph from 5), NOC4PC (§102/§103/allowed) | USPTO Non-Final Rejections | PI4PC best 63.3 (GPT-4o). NOC4PC best 45.4 (CoT) against a random baseline of 32.3 | We already used PAR4PC and PI4PC test for retrieval (Track A). **No IPC/CPC fields** in the files we hold. Licence CC BY-NC 4.0 |
| Ikoma & Mitamura ([arXiv 2502.06316](https://arxiv.org/abs/2502.06316), 2025) | Novelty from claim plus cited passages (USPTO rejections) | Binary novelty | Generative models beat classifiers; they miss hypernym/hyponym relations | Earlier version of the same idea |
| **LongCite** ([arXiv 2409.02897](https://arxiv.org/abs/2409.02897), ACL Findings 2025) | Sentence-level citations in long-context QA | LongBench-Cite | Fine-tuned 8–9B models beat GPT-4o on citation quality | **Citing by sentence number is known in general NLP.** Our quote-by-reference (E3) is an application of it, not a new method |
| **Commercial tools** (e.g. [XLSCOUT ClaimChart / Invalidator LLM](https://xlscout.ai/faq/how-effective-is-claimchart-llm-as-a-claim-chart-generator-for-patent-analysis); [PatSnap PatentBench](https://www.patsnap.com/resources/blog/introducing-patentbench-a-new-standard-for-ai-built-for-patent-tasks/)) | Claim charts, invalidity and FTO search | Vendor claims, no public error rates | — | The business need is real and already served by paid products |
| **DAPFAM** ([Array 2026](https://www.sciencedirect.com/science/article/pii/S2590005626000433); [arXiv 2506.22141](https://arxiv.org/abs/2506.22141)) | Cross-domain (OUT) vs in-domain family retrieval | Citation-based family qrels, IPC3 split | OUT about five times lower than IN in every configuration | Paper 53 and our Scout work are built on it |
| Patent embedding benchmark ([arXiv 2605.24297](https://arxiv.org/abs/2605.24297)) | 22 embedding models, DAPFAM as an external check | Retrieval metrics | No domain-adaptive prompting | No LLM query work on DAPFAM OUT found |
| Cross-industry scouting | Vendor guides (e.g. [PatSnap cross-industry transfer](https://www.patsnap.com/resources/blog/articles/ai-cross-industry-technology-transfer-for-engineers/)); LLM analogies for science ([arXiv 2605.11258](https://arxiv.org/abs/2605.11258)) | None found for patents | — | **No peer-reviewed evaluation found** of LLM cross-industry solution search over patents |

## 2. What this means for the options

**Examiner-verifiable claim chart:** no longer novel as a headline.
- FiNE-Patents (examiner gold at feature level) and PatentAgentBench (expert claim charts) were published in 2026, by teams with frontier models and commercial search tools.
- Our resources are a local 8B model on one V100 with no paid API, so we would compete on their ground.
- Our PI4PC test split has already been read for the Track A retrieval replication.
- PANORAMA is non-commercial (NC), which also limits the product.

**Quote by reference (E3):** confirmed as useful engineering.
- v1 removes misquotes, with a G1 gain of +0.237, and halves latency.
- Citing by identifier is established practice (LongCite; FiNE-Patents passage IDs; the PI4PC multiple-choice format). Report it as a design choice backed by a measured comparison, not as a contribution.

**FTO:** already benchmarked by PatentAgentBench.
- Patent FTO there uses court infringement findings as gold. Design FTO is near zero.
- An FTO product would need legal status, jurisdiction and claim construction. It would also contradict the product rule that the tool never states novelty, validity, infringement or FTO.
- At most an "FTO triage evidence map" fits as a demonstration. The device-disclosure links from Track B are a small descriptive proxy: 8 devices and 24 patents, and `disclosed_link` is not infringement.

**What looks open, and is the direct link to Paper 53:**

1. **Cross-domain evidence.** None of the 2026 benchmarks above reports results split by in-domain vs cross-domain prior art.
   - DAPFAM's authors call cross-domain partitions under-tested.
   - We found no LLM query work on DAPFAM OUT.
   - Commercial vendors market cross-industry search without public evaluation.
2. **Missing evidence as the common bottleneck.** PatentAgentBench (missing references), PatRe (hallucinated citations without evidence) and FiNE-Patents (low passage F1) each observe it.
   - Paper 53 gives an exact accounting of it for fixed pools (Eq. 1, exposure).
   - None of the three papers separates exposure from within-pool selection the way Paper 53 does.
3. **Openness.** Local open-weight models, frozen protocols and hashes. This also addresses Paper 53's own limit, that its original-run records could not be recovered.

## 3. Recommendation for the owner's decision

Stay with **Solution Scout**, reframed as the cross-domain evidence study that follows Paper 53. Do not pivot to claim charts or FTO.

**Science:** the frozen E1/E2 protocol is ready, and the DAPFAM test split has never been read.
- E2a measures how much reported cross-domain recall depends on in-domain families competing for slots. This is Paper 53's exposure accounting carried from fixed rerank pools to candidate generation, at depth 200.
- E1 measures the analyst-facing trade-off.
- E3 is done: transfer rationales grounded by reference. E5 replicates the brief cost on PatenTEB.
- The lane gain must be reported as a protocol and candidate-set effect, since the IPC3 lane equals the OUT definition. It is not a retrieval method gain.

**Positioning against the 2026 work:** those benchmarks show that evidence is missing. This study shows that, for cross-domain prior art, the loss happens at candidate generation, and how much a lane protocol and a short brief change it. It does this on the one public cross-domain benchmark, with open models.

**Product:** a two-lane shortlist with grounded transfer rationales. That is the same business need vendors market as cross-industry search, but here it has a public evaluation.

**Optional demonstration:** a small claim-chart view of one shortlisted cross-domain document, reusing the quote-by-reference layer, labelled as a demonstration. No FTO claims.

## 4. Checks still open

- Re-verify every number above from the PDFs before citing it.
- Check whether FiNE-Patents or PatentAgentBench report any split by technology distance. If one does, Section 2 changes.
- If the owner still wants a claim-chart study:
  - check the FiNE-Patents dataset licence (it is on GitHub; the licence is not stated in the paper);
  - check whether its cited documents' CPC codes can be obtained without a login, which would allow a cross-domain cut.
- Check whether the full PANORAMA release (8,143 records) carries CPC codes. The benchmark files we hold do not.
