# Deep-dive direction review: medtech device–patent linkage vs the alternatives (7 Nov 2026)

- **Status:** a bounded deep dive (about 16 searches and 6 full-text reads), done on 7 Nov 2026 at the owner's request. It extends the [first literature check](CLAIM_CHART_AND_SCOUT_LITERATURE_REVIEW_20261107_EN.md).
  - It is not a systematic review. Re-check every number against the source PDF before citing it.
- **Owner criteria (7 Nov 2026):**
  - target users are **R&D teams and medtech**;
  - "wow" means **numbers that make the field stop and look**, plus **a live demo that leaves the advisor speechless**;
  - the advisor wants a visible link to the owner's published reranking paper (Paper 53).
- **No decision is taken here.** Nothing was run. USD 0.

## 1. The finding that changes the picture

**Medtech has no public device–patent register.**
- Drugs have the FDA Orange Book; devices have nothing equivalent.
- A January 2026 JAMA Viewpoint (Simon et al., [JAMA 335(9):751–752](https://jamanetwork.com/journals/jama/fullarticle/2844541)) proposes that the FDA build one, a "Yellow Book". The authors argue that researchers cannot currently study the role of patents in device innovation and risk. Letters and a reply followed in June 2026.
- A companion paper ([SSRN 5752682](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5752682)) proposes that manufacturers list all covering patents in FDA applications.
- The FDA has not adopted the proposal.

**The one AI attempt so far has gaps that Paper 53's lens exposes.** Bridge-MedDevKG (Yang, Liu, Li; [ACL 2026 main](https://aclanthology.org/2026.acl-long.1611.pdf); [arXiv 2606.28353](https://arxiv.org/abs/2606.28353)) links FDA cardiovascular PMA devices to USPTO patents.

What it reports:
- 434 devices, 698,191 patents, and 585 expert-verified gold pairs.
- The gold comes from virtual patent marking (VPM), litigation and SEC filings.
- Only 88 of the 434 devices (20.3%) have any disclosed patent. The median is 5 patents per device, the maximum 83.
- The headline is "a conservative lower-bound recall of 91.6%", with **6.8M "high-confidence links"**.

The gaps:

| Gap | Detail |
|---|---|
| No analyst depth | There is no top-k cutoff. 6.8M links over 434 devices is about **15,700 links per device** (our arithmetic from their reported totals) |
| No precision | Not reported; listed as future work |
| Corpus excludes other fields by design | The corpus is selected by CPC prefix, mostly A61. Manufacturing classes are kept only if the title matches cardiovascular keywords. Covering patents in materials, electronics or software can never be found, which is Paper 53's point that no reranker recovers what the candidate set excludes. The share of covering patents outside A61 is not reported |
| Split unclear | There is no explicit train/test split for the reported recall, and overlap with the XGBoost training positives cannot be ruled out from the text |
| Release unusable | Our own audit (28 Oct 2026, [BRIDGE_RIGHTS_COHORT.md](BRIDGE_RIGHTS_COHORT.md)) found no licence file, no per-link source URL or date, training positives overlapping evaluation positives, and a release that does not match the paper's counts. That branch is `BLOCKED_LOCAL` |
| Scope | Cardiology only. Legal status and expiry are not discussed |

**The same link problem outside medtech is economics work, not AI evaluation.** IPRoduct (de Rassenfosse, EPFL; [NBER project](https://www.nber.org/programs-projects/projects-and-centers/7087-iproduct-database-linked-products-intellectual-property-rights); [iiindex](https://iiindex.org/datasets/iproduct/)) builds product–patent links from VPM pages: about 800 companies, 24,463 products and 19,815 US patents in one listing. Access is credit-based.
- An NBER working paper estimates that about 12% of patent holders use VPM.
- A 2026 [JELS paper](https://onlinelibrary.wiley.com/doi/10.1111/jels.70028) uses it to show that prices drop 8–10% after patent protection ends.
- It is used for economics, not as an AI linkage benchmark, and it is consumer-product focused.

## 2. Candidate "shock numbers" (to be measured, not promised)

Each could headline a paper or a demo. None has been measured yet. Each needs a frozen protocol before it is computed.

| # | Measurement | Why it would land | Link |
|---|---|---|---|
| S1 | Share of FDA-authorized high-risk devices (PMA) and of 510(k) devices from marking companies that have **any** public patent disclosure | Puts a number on the transparency gap behind the JAMA "Yellow Book" proposal. Bridge found 20.3% in one specialty | Policy and medtech |
| S2 | Share of disclosed covering patents whose CPC lies **outside A61** | If large, any A61-restricted search (including Bridge's corpus) misses them by construction | Paper 53 (exposure) and DAPFAM (cross-domain) |
| S3 | Recall of disclosed covering patents at **analyst depth** (top 20 and top 100) from the device's own FDA text | The number an engineer actually sees, against a headline recall computed over about 15,700 links per device | Paper 53 (metric vs exposure) |
| S4 | Share of marked patents that are **expired or lapsed** at snapshot time, and the "patent cliff" per device | Tells R&D when design freedom opens; stale marking is a known VPM issue | Business (R&D timing) |
| S5 | **Grounding:** share of claim-element evidence quotes in the device→patent evidence map that match the source literally, v0 vs v1 | E3 already shows v1 removes misquotes (+0.237 G1) | E3 carried to medtech |

## 3. Demo concept (the "advisor stops talking" moment)

**"Type an FDA device number → see its patent wall in seconds."**

1. **Input:** a PMA or 510(k) number. The system pulls the device's public FDA record (openFDA; US government work).
2. **Disclosed patents:** the patents the company itself marks for this product, each with its source URL, snapshot date and hash.
3. **Predicted candidates in two lanes:** own field (A61) and other fields. This reuses the Scout lanes, and S2 is why the second lane matters.
   - Predictions are labelled as unverified.
4. **Evidence map:** for each top patent, claim elements set against sentences of the device's FDA summary or labelling. Quotes are rendered by sentence reference, so a misquote cannot occur.
5. **Timeline:** expiry dates and the "patent cliff" across the wall.
6. **Labels:** every screen says it is not FTO or legal advice, and that disclosed links are company statements, not infringement findings.

**Who it is for:**
- medtech R&D (competitor walls, design-around timing);
- IP and BD teams (licensing scouting);
- regulatory and policy researchers (a prototype of the Yellow Book).

## 4. Scored comparison

Scores are this reviewer's judgement, 1 (low) to 5 (high).

| Option | Novelty vs 2026 work | Public gold | Rights | Business pull (R&D/medtech) | Paper 53 link | Feasibility (V100, no paid API) | Wow (numbers + demo) |
|---|---|---|---|---|---|---|---|
| **A. Open device–patent linkage ("open Yellow Book" prototype)** | 4: Bridge exists but leaves depth, precision, other-field coverage, rights and specialty gaps | 3: VPM disclosures, partial and strategic | 3: FDA and USPTO public; VPM pages give facts but no redistribution grant, so release identifiers and URLs only (owner/legal check) | **5** | **5** | 3: data acquisition is the main work | **5** |
| B. Solution Scout cross-domain on DAPFAM (current frozen plan) | 3 | 4: DAPFAM citations | 3: CC BY-NC-SA | 3 | 5 | **5**: ready, test unread | 2 |
| C. Claim chart / FTO | 1–2: FiNE-Patents, PatentAgentBench, PatRe | 4 | 2–3: PANORAMA NC | 4 | 3 | 2: frontier models favoured | 3 |
| D. Thai–English patent search | 4 | ? | ? (DIP data access unknown) | 2 for this target group | 2 | ? | 3 |

## 5. Recommendation

Make **A** the main study and product. Keep B's frozen protocol and the unread DAPFAM test in reserve; do not discard them.

**How A uses what exists:**
- Track B already has VPM adapters, per-link provenance and a rights matrix for Abbott, Boston Scientific, Stryker and Cook.
- The Scout lanes become the A61 vs other-fields split.
- E3 quote-by-reference becomes the evidence-map layer.
- Paper 53's exposure accounting becomes the evaluation lens, applied at analyst depth and to what the candidate set excludes.

**A defensible paper shape for WPI.** Possible title: *Which patents cover this device? An open, provenance-tracked device–patent linkage benchmark and what retrieval misses*.
1. The benchmark: per-link provenance, company-grouped holdout, frozen before scoring.
2. Descriptive numbers: S1, S2, S4.
3. Retrieval at analyst depth with exposure accounting (S3, the Paper 53 link). Baselines: BM25 and PatEmbed, A61-restricted vs unrestricted.
4. The grounded evidence map (S5) and the demo.
- A short descriptive research letter on S1/S2/S4 could later go to a health-policy venue. That is optional and decided after the numbers exist.

## 6. Risks and open checks before any protocol

1. **Gold is strategic disclosure.** Recall is a lower bound and precision cannot be read from it, as Bridge also notes. Report known-link recall only; unjudged is not negative.
2. **Rights.** VPM pages have no redistribution licence; publish only identifiers, URLs, dates and hashes. FDA records are public; USPTO data is public. **Owner decision:** whether a legal check is needed before release.
3. **Patent text and CPC source without an agent login.**
   - PatentsView now needs a USPTO login, and Google-derived text was blocked for redistribution earlier.
   - Options: the USPTO Open Data Portal (needs an API key the owner would register), or HUPD (applications up to 2018 only).
   - **Owner decision needed.**
4. **Scale.**
   - Count how many medtech companies publish VPM pages that map products to patents, and how many of those products can be matched to FDA records.
   - Respect each site's terms and robots rules.
   - A first feasibility count is needed before a protocol.
5. **Bridge reviewers.** Expect "why not use their data". The answer is our documented rights, provenance and split audit, plus the A61-only corpus issue.
6. **Timeline.** Larger than P3: roughly 3–5 weeks to a frozen benchmark, by estimate.
7. **Checks still open:**
   - whether Bridge's GitHub release states CPC shares (S2) or per-device link counts;
   - whether any 2026 work reports device–patent recall at fixed depth;
   - whether IPRoduct covers medical devices.

## Sources

- Simon et al., "A Yellow Book for Medical Devices—A Proposal for Public Health", JAMA 2026: https://jamanetwork.com/journals/jama/fullarticle/2844541 ; letter and reply: https://jamanetwork.com/journals/jama/article-abstract/2850453 , https://jamanetwork.com/journals/jama/article-abstract/2850452
- Simon, Paasche-Orlow, Noorchashm, "Inadvertent Patent Signals", SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5752682
- Bridge-MedDevKG, ACL 2026: https://arxiv.org/abs/2606.28353 , https://aclanthology.org/2026.acl-long.1611.pdf
- IPRoduct: https://www.nber.org/programs-projects/projects-and-centers/7087-iproduct-database-linked-products-intellectual-property-rights , https://iiindex.org/datasets/iproduct/
- de Rassenfosse & Higham, "Wanted: a standard for virtual patent marking": https://doi.org/10.1093/jiplp/jpaa063
- de Rassenfosse, "Notice Failure Revisited: Evidence on the Use of Virtual Patent Marking", SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3114637
- de Rassenfosse et al., "Patents and Supra-Competitive Prices", JELS 2026: https://onlinelibrary.wiley.com/doi/10.1111/jels.70028
- Combination products and Orange Book device patents, PLOS ONE: https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0148939
- 510(k) predicate genealogy, PLOS ONE: https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0258153
- FDA AI-enabled device search: https://arxiv.org/abs/2602.00006
- Earlier review sources (FiNE-Patents, PatentAgentBench, PatRe, PANORAMA, LongCite, DAPFAM): see [CLAIM_CHART_AND_SCOUT_LITERATURE_REVIEW_20261107_EN.md](CLAIM_CHART_AND_SCOUT_LITERATURE_REVIEW_20261107_EN.md)

## 7. Addendum, 7 Nov 2026: "time machine" and landscape-agent options

The owner found the device–patent dataset not "wow" enough on its own. Two further options were discussed.

### 7.1 Time machine (retrospective cross-industry foresight)

**Question:** given only a clinical problem, and only patents that existed before year T, does a search surface the cross-industry mechanism that a later medtech invention actually used?

**Dev-only counts** (DAPFAM dev split; test not touched; computed 7 Nov 2026):
- 474 dev queries; 87 have IPC A61; 35 of those have at least one cross-domain (OUT) positive, giving 82 OUT pairs.
- IPC sections of those cross-domain targets: H 36, B 24, G 18, F 14, A 12, C 9, E 4, D 1.
- Query year minus target year (earliest claim year): median 0, IQR −7 to +12. DAPFAM relevance includes newer documents, so a time-machine study must keep only older targets.
  - 38% of the targets are at least 5 years older than the query; 28% are at least 10 years older.
- Small n: a test-split analysis would be descriptive with wide CIs.
- Any A61 or time-cutoff subgroup on test needs a dated protocol amendment **before** the test read.

**Product framing:** the time machine is the **back-test** that gives a product credibility; it is not the product.
- The product is cross-industry foresight for medtech R&D: a problem brief goes in, and two lanes come out.
- Its mechanism cards show the source industry (IPC section), age, legal status (an "off-patent mechanisms" filter, labelled not FTO), family size and grounded quotes.
- Further features: watchlist alerts for new cross-industry filings, and export to the dossier for IP counsel.
- The claim to make is "back-tested on history", with the number published. Vendors market cross-industry search without a public back-test.

### 7.2 Landscape agent (reproduce an expert patent landscape in minutes)

**Prior work:**

| Work | What it does | Notes |
|---|---|---|
| Abood & Feltenberger, *Automated patent landscaping*, AI & Law 26 (2018) | Seed-set expansion plus a classifier | — |
| Pujari et al., EMNLP 2022 ([paper](https://aclanthology.org/2022.emnlp-main.791.pdf)) | Three landscaping classification datasets | InjVal (Bosch in-house expert); Ritonavir (781 families) and Atazanavir (640 families) from WIPO landscape studies. These are classification within a given set, not end-to-end reproduction |
| "Automated neural patent landscaping in the small data regime" ([AI & Law 2025](https://link.springer.com/article/10.1007/s10506-025-09483-5); [arXiv 2407.08001](https://arxiv.org/abs/2407.08001)) | Refines the training-data procedure with active learning | Finds the 2018 approach weak near the landscape boundary |
| LLM agents | — | Two searches found no 2025–2026 paper that evaluates an LLM agent against an expert landscape. PatentAgentBench has no landscape suite |

**Possible gold:** WIPO landscape datasets.
- The [WIPO Analytics manual](https://wipo-analytics.github.io/manual/datasets.html) lists e-waste, solar cooking, ritonavir, AI 2019 and **Assistive Technology 2021** (two xlsx datasets; medtech-adjacent).
- WIPO lists [Healthtech reports](https://www.wipo.int/en/web/patent-analytics/healthtech) and a [compilation of landscape reports by other organizations](https://www.wipo.int/en/web/patent-analytics/patent-landscapes-reports).
- The dataset licence is not stated on the manual page and needs a check.

**Risks:**
- Expert landscapes are usually built with Boolean and classification queries, so a CPC-query baseline may already reach high recall. That must be the first baseline.
- Our searchable corpus covers US applications only (HUPD to 2018). Mapping worldwide families needs a family source that may require a login.
