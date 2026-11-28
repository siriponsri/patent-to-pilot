## Prompt for SciSpace

> Write Section 2 (Literature Review) of a KMITL IS2 short paper on Market Window Dossier and its research benchmark, LOE-Bench. Use about 1,200–1,600 words for the English section. Use the eight themes below to organize the argument, with adjacent themes combined where helpful. Start with the difference between patent expiry, generic submission, final approval and commercial launch. Connect the timing literature to competitive crowding, then explain why dated evidence, selective triage and document-backed hand-off matter. End with an explicit research-gap paragraph that motivates RQ1–RQ3 by name.
>
> Use IEEE numbered citations in order of first appearance and provide the reference list. Open the DOI, arXiv record or original publisher/issuer page for every citation and match title, authors, year and venue. Prefer peer-reviewed primary studies and official records. Mark preprints, conference-program-only records, vendor pages and other grey sources as such. Keep study findings, descriptive associations, scenario assumptions, opinions and planned analyses distinct. Exclude unverified sources from the citation list, never invent a reference or statistic, and explain any important evidence gap briefly. Follow the do-not list below. Produce the English section first, then a Thai version if feasible, preserving citation numbering and the scope of every claim.

# Market Window Dossier / LOE-Bench literature review brief

## Our study in brief

Market Window Dossier addresses two owner-identified problems. P1 is scarce capacity for freedom-to-operate (FTO) review. P2 is the risk that competitors capture anticipated demand before launch. Before bioequivalence or comparative trials, a team uses a launch-window forecast and competition scenarios to assess a candidate. The workflow produces a dated evidence pack and evaluator checklist. Qualified counsel determines FTO.

LOE-Bench uses open US FDA records available at each historical cutoff (“as-of”), with dated Orange Book evidence, Drugs@FDA approval outcomes and source-specific challenge rules. The endpoint is first final original abbreviated new drug application (ANDA) approval for an active-moiety set within 12 or 24 months. Marketing launch is a separate event. Historical Track C′ remains sealed and requires the preregistered admission gate. Prospective Track A uses the 27 November 2026 snapshot, with predictions to be hashed, tagged and externally timestamped before outcome retrieval and by 31 January 2027 UTC. It confirms if C′ did not run as confirmatory and otherwise serves as replication. Biologics are descriptive.

- **RQ1 | Confirmatory triage.** Does M3, a graph-augmented prediction and deferral system, capture more events than the B1 age/hazard table at 24 months (H1), the matched flat M1 at 24 months (H2), and B1 at 12 months (H3), in that fixed sequence? The primary endpoint is pooled positive-event recall across the top 20% of eligible rows per cutoff.
- **RQ2 | Exploratory commercial context.** Do frozen queues also capture drugs with at least three distinct approved ANDA applicants within 36 months? Evaluate price erosion as a scenario and mapped US Medicaid use and reimbursement separately.
- **RQ3 | Exploratory and descriptive dossier.** Can the output retain source-level traceability and refer unresolved items? Compare the minimal-input LLM (L1) with the evidence-matched LLM (L1e) and structured M3. Optional C9 pairs GRPO reinforcement learning with supervised fine-tuning on prospective 24-month forecasts only.

**Development only.** H1/H2/H3 recall differences were +9.80/+5.49/+13.00 percentage points (pp), with H2 sensitive to challenge coding and its interval crossing zero. L1e trailed L1 and M3 at both horizons. Crowding capture was 71.43% versus 45.83% (M3/B1, one cutoff, 21 positives). Vintage-uncontrolled Medicaid price adjustments worsened error versus carry-forward. C9 training and confirmatory scoring are **NOT_RUN**.

RQ numbering follows the IS2 brief. The audited preregistration governs the confirmatory sequence. [D41 plan](https://github.com/siriponsri/patent-to-pilot/blob/0d5659a2/docs/loe-bench/PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026) · [Preregistration](https://github.com/siriponsri/patent-to-pilot/blob/0d5659a2/docs/loe-bench/PREREGISTRATION.md) · [Development receipts](https://github.com/siriponsri/patent-to-pilot/tree/0d5659a2/docs/loe-bench/receipts).

## Claims the review must support

1. **C1 | Timing has several endpoints.** Prior patent-clock, market-exclusivity and first-submission studies establish relevant baselines. First submission, final approval and observed commercial entry answer different questions and can have different dates. Historical regulatory vintages and event definitions constrain comparison. (RQ1)
2. **C2 | Regulatory and challenge signals are conditional.** Patent type, remaining exclusivity, Paragraph IV challenge and stay timing inform possible entry dates. Filing, verified public availability and eventual disposition are distinct. An undated record or a missing link can leave a material question unresolved. (RQ1, RQ3)
3. **C3 | Competitive crowding matters.** Empirical studies link entrant counts, market incentives and prices. Approved applicants proxy potential competitors. Marketed producers, acquisition prices, market share and gross payer reimbursement have their own denominators. US estimates can motivate scenarios within their source populations. (RQ2)
4. **C4 | An FTO hand-off needs traceable evidence.** Patent landscape and FTO search guidance motivate jurisdiction, claim scope, legal-status checks and exact source locators. Patent retrieval and AI task benchmarks provide comparators for work components. P1 is an owner-reported constraint, and a measurable staffing baseline remains open. (RQ3)
5. **C5 | Date both evidence and evaluation.** Timestamped evidence and prospective forecast freezes address distinct leakage risks. An LLM may carry knowledge learned after a historical cutoff even with dated prompts. Prospective comparisons keep matched evidence and a common outcome. Outcome-trained RL studies justify an exploratory comparison on this task. (RQ1, RQ3)
6. **C6 | Review capacity and repeated observations affect evaluation.** Connect selective prediction to deferral, then justify event recall and precision for rare events and a fixed review budget. Discuss whole-drug clustered intervals, fixed-sequence multiplicity, secondary-data preregistration and dataset documentation. (RQ1, RQ3)
7. **C7 | Thai and ASEAN transfer needs jurisdiction-specific evidence.** Local patent examination, national-phase status and registry coverage determine what belongs in the checklist. US approval forecasts and open-data labels are US-specific. (RQ2, RQ3)
8. **C8 | Evidence availability motivates the IS1 bridge.** The authors' earlier cross-domain patent reranking study found near-zero instruction effects in its tested pools. That observation motivates checking evidence availability and routing unresolved cases in IS2. (RQ3)

### Research gap

The seed literature covers components of the workflow: submission or arrival models, sources on patent and exclusivity timing, competition and pricing studies, FTO search practice, and general forecasting and abstention benchmarks. Closest-work comparisons should test whether any documented system combines reconstructable open FDA evidence at each cutoff, a matched fixed-capacity review queue with evidence-traced deferral, and an externally timestamped prospective check. LOE-Bench evaluates that combination for first final approval (RQ1), then examines whether the same queue captures later applicant crowding and informs explicitly bounded price scenarios (RQ2). The dossier links dated evidence to a Thai/ASEAN evaluator hand-off and tests a matched-evidence LLM comparator (RQ3). Frame this as a specific integration gap based on the search coverage. An exhaustive novelty claim would require a broader systematic search.

## Seed bibliography by theme

C1–C8 in the source annotations refer to the claims above. The numbers below identify seed records. Renumber the references in the drafted Section 2 by first appearance. Evidence types describe what the linked record can support.

### T1 | Generic entry and loss-of-exclusivity forecasts

[1] R. Hopefl et al., “Predictive analysis for first submission of generic drug application for orphan drug products using random survival forest,” Clin. Transl. Sci., 2025. [Source](https://ascpt.onlinelibrary.wiley.com/doi/full/10.1111/cts.70365).

**Primary peer-reviewed.** Random survival forests predicted time to first orphan-product ANDA submission. Sales led variable importance for new chemical entities, and product-specific guidance availability was important for non-NCEs. **Supports C1, RQ1.**

[2] M. Hu, A. Babiskin, and S. Wittayanukorn, “Predictive analysis of first abbreviated new drug application submission for new chemical entities based on machine learning methodology,” Clin. Pharmacol. Ther., 2019, doi: 10.1002/cpt.1479. [Source](https://pubmed.ncbi.nlm.nih.gov/31009066/).

**Primary peer-reviewed.** Survival models estimated time from earliest lawful filing to first ANDA submission, with internal and external validation reported. **Supports C1, RQ1.**

[3] R. F. Beall, J. J. Darrow, and A. S. Kesselheim, “A method for approximating future entry of generic drugs,” Value Health, 2018, doi: 10.1016/j.jval.2018.04.1827. [Source](https://pubmed.ncbi.nlm.nih.gov/30502781/).

**Primary peer-reviewed.** An expiry-and-exclusivity clock approximated observed entry in a cohort of 170 top sellers, with weaker performance for the secondary-patent subgroup. **Supports C1, RQ1.**

[4] R. F. Beall, J. J. Darrow, and A. S. Kesselheim, “Approximating future generic entry for new drugs,” J. Law Med. Ethics, vol. 47, no. 1, pp. 177–182, 2019. [Source](https://doi.org/10.1177/1073110519840499).

**Scholarly methods and policy article.** Explains the authors' patent-term approximation and the need to account for regulatory and legal timing. **Supports C1, RQ1.**

[5] R. F. Beall et al., “Comparing onset of biosimilar versus generic competition in the United States,” Clin. Pharmacol. Ther., vol. 108, no. 6, pp. 1308–1314, 2020. [Source](https://doi.org/10.1002/cpt.1981).

**Primary peer-reviewed.** Compared clock-based expected and observed competition for a US approval cohort and found similar expected exclusivity durations across the two product classes. **Supports C1, RQ1.**

[6] K. W. Kerr and L. J. Glos, “Effective market exclusivity of new molecular entities for rare and non-rare diseases,” Pharmaceut. Med., vol. 34, pp. 19–29, 2020. [Source](https://doi.org/10.1007/s40290-019-00317-9).

**Primary peer-reviewed.** Measured exclusivity to first generic approval. The statistically lower hazard appeared for entities with both orphan and non-orphan indications versus single non-orphan indications. **Supports C1, RQ1.**

[7] K.-B. Son, “Market exclusivity of the originator drugs in South Korea: A retrospective cohort study,” Front. Public Health, vol. 9, Art. no. 654952, 2021. [Source](https://doi.org/10.3389/fpubh.2021.654952).

**Primary peer-reviewed.** Estimated Korean originator exclusivity periods in a retrospective cohort, illustrating the need for local endpoint definitions. **Supports C1, C7, RQ1.**

[8] H. S. Chahal, R. Patel, and M. Shimer, “Marketing of first generic drugs approved by U.S. FDA from January 2010 to June 2017,” US FDA, Nov. 2021. [Source](https://www.fda.gov/media/154101/download?attachment=).

**Government report, empirical.** Examines the gap between first approval and marketing in an FDA cohort of 687 first generics. **Supports C1, C3, RQ1–RQ2.**

[9] DrugPatentWatch, “Generic drug market entry: The complete patent expiry, ANDA strategy, and IP valuation playbook,” Apr. 2026. [Online]. [Source](https://www.drugpatentwatch.com/blog/finding-and-evaluating-generic-market-entry-opportunities/).

**Vendor, grey.** Describes a commercial entry-opportunity workflow using patents and exclusivities for market evaluation. **Supports C1, C3, RQ1–RQ2.**

[10] IQVIA, “Beyond patent protection: Generics driving market trajectories.” [Online]. [Source](https://www.iqvia.com/de-at/library/articles/beyond-patent-protection-generics-driving-market-trajectories).

**Vendor, grey.** Offers a commercial reference for how post-expiry generics enter market analytics. **Supports C1, C3, RQ2.**

[11] J+D Forecasting (Evaluate), “Loss of exclusivity report.” [Online]. [Source](https://discover.evaluate.com/loss-of-exclusivity-report-download).

**Vendor, grey.** The landing page describes a report on incorporating patent cliffs into forecasting workflows. **Supports C1, C3, RQ2.**


### T2 | Patents, exclusivity and Paragraph IV challenges

[12] C. S. Hemphill and B. N. Sampat, “Evergreening, patent challenges, and effective market life in pharmaceuticals,” J. Health Econ., vol. 31, no. 2, pp. 327–339, 2012. [Source](https://www.sciencedirect.com/science/article/abs/pii/S0167629612000057).

**Primary peer-reviewed.** Empirically connects patent challenges and patent portfolios with effective market life, including challenges directed at later-expiring patents. **Supports C1, C2, RQ1.**

[13] A. K. Rai, S. Vishnubhakat, J. Lemus, and E. Hovenkamp, “Replication data for: Post-grant adjudication of drug patents: Agency and/or court?,” Harvard Dataverse, ver. 1.0, 2021, doi: 10.7910/DVN/YCMKVU. [Source](https://api.datacite.org/dois/10.7910/DVN/YCMKVU).

**Primary replication dataset.** Records court and PTAB activity for drug patents. Court filing evidence requires a dated public witness and exact case-to-drug linkage at a forecast cutoff. **Supports C2, C5, RQ1–RQ3.**

[14] S. Kannappan, J. J. Darrow, A. S. Kesselheim, and R. F. Beall, “The timing of 30-month stay expirations and generic entry: A cohort study of first generics, 2013–2020,” Clin. Transl. Sci., vol. 14, no. 5, pp. 1917–1923, 2021. [Source](https://doi.org/10.1111/cts.13046).

**Primary peer-reviewed.** Studied 46 first generics and reported a median 3.2 years from estimated stay expiration to launch. Stay expiration alone was an incomplete launch clock. **Supports C2, RQ1.**

[15] M. Durvasula et al., “The NBER Orange Book dataset: A user's guide,” Res. Policy, vol. 52, no. 7, Art. no. 104791, 2023, doi: 10.1016/j.respol.2023.104791. [Source](https://pubmed.ncbi.nlm.nih.gov/38130474/).

**Primary peer-reviewed.** Documents annual historical patent and exclusivity editions and data limitations relevant to historical replay. **Supports C2, C5, RQ1.**


### T3 | Competition, price erosion and entry decisions

[16] R. Conrad and R. Lutter, “Generic competition and drug prices: New evidence linking greater generic competition and lower generic drug prices,” US FDA, Dec. 2019. [Source](https://www.fda.gov/media/133509/download).

**Government report, empirical.** For the FDA study sample, median generic-to-pre-entry-brand manufacturer price ratios were about 46% with two producers and 21% with four. These are US average manufacturer price measures used to motivate scenarios. **Supports C3, RQ2.**

[17] F. M. Scott Morton, “Entry decisions in the generic pharmaceutical industry,” RAND J. Econ., vol. 30, no. 3, pp. 421–440, 1999. [Source](https://www.jstor.org/stable/2556056).

**Primary peer-reviewed.** Larger pre-entry revenue markets attracted more entrants. Firm portfolio characteristics also mattered to entry decisions. **Supports C3, RQ2.**

[18] D. Reiffen and M. R. Ward, “Generic drug industry dynamics,” Rev. Econ. Stat., vol. 87, no. 1, pp. 37–49, 2005. [Source](https://www.ftc.gov/sites/default/files/documents/reports/generic-drug-industry-dynamics/industrydynamicsreiffenwp_0.pdf).

**Primary peer-reviewed article with linked author working paper.** Estimated US generic entry and price dynamics. Prices fell as seller count rose, and expected rents influenced entry. **Supports C3, RQ2.**

[19] A. Hollis, “The importance of being first: Evidence from Canadian generic pharmaceuticals,” Health Econ., vol. 11, no. 8, pp. 723–734, 2002. [Source](https://doi.org/10.1002/hec.698).

**Primary peer-reviewed.** Canadian generic market data show a first-entrant market-share advantage in the study setting. **Supports C3, RQ2.**

[20] IQVIA Institute for Human Data Science, “Biosimilars in the United States 2023–2027.” [Online]. [Source](https://www.iqvia.com/insights/the-iqvia-institute/reports-and-publications/reports/biosimilars-in-the-united-states-2023-2027).

**Industry research report, grey.** Describes historical uptake, competition and savings and gives a forward outlook. Distinguish the report's projections from historical observations. **Supports C3, RQ2.**

[21] K. Nikolopoulos, S. Buxton, M. Khammash, and P. Stern, “Forecasting branded and generic pharmaceuticals,” Int. J. Forecast., vol. 32, no. 2, pp. 344–357, 2016, doi: 10.1016/j.ijforecast.2015.08.001. [Source](https://research.bangor.ac.uk/en/publications/forecasting-branded-and-generic-pharmaceuticals/).

**Primary peer-reviewed.** Compares forecasting methods for UK branded and generic prescription series, motivating simple time-series baselines such as drift. **Supports C3, RQ2.**

[22] M. Cha, B. Rifai, and P. Sarraf, “Pharmaceutical forecasting: Throwing darts?,” Nat. Rev. Drug Discov., vol. 12, no. 10, pp. 737–738, 2013. [Source](https://doi.org/10.1038/nrd4127).

**Brief industry-authored analysis.** Discusses discrepancies between analyst forecasts and realized pharmaceutical sales, motivating caution about sales point estimates. **Supports C3, RQ2.**


### T4 | Freedom-to-operate practice and patent AI

[23] World Intellectual Property Organization, Guidelines for Preparing Patent Landscape Reports, WIPO Publ. 946, 2015. [Source](https://www.wipo.int/edocs/pubdocs/en/wipo_pub_946.pdf).

**Intergovernmental guidance, grey.** Provides a methodology for defining scope, searching, analyzing and presenting patent landscapes. **Supports C4, RQ3.**

[24] World Intellectual Property Organization, Identifying Inventions in the Public Domain: A Guide for Inventors and Entrepreneurs, WIPO Publ. 1062, 2020. [Source](https://www.wipo.int/publications/en/details.jsp?id=4501).

**Intergovernmental guidance, grey.** Describes a staged patent search and analysis of territorial coverage, legal status and claims for FTO-related work. **Supports C4, C7, RQ3.**

[25] Y. Hu et al., “PatentAgentBench: Benchmarking LLM agents with professional patent task suites,” arXiv:2610.35031, 2026. [Source](https://arxiv.org/abs/2610.35031).

**Preprint.** Defines professional patent-task suites for evaluating agents. It is an external benchmark for patent work components. **Supports C4, RQ3.**

[26] M. Freunek and A. Bodmer, “BERT based freedom to operate patent analysis,” arXiv:2105.00817, 2021. [Source](https://arxiv.org/abs/2105.00817).

**Preprint.** Proposes matching patent descriptions to independent claims to rank potentially relevant patents from a product or invention description. **Supports C4, RQ3.**

[27] Q. Wang et al., “IPBench: Benchmarking the knowledge of large language models in intellectual property,” arXiv:2504.15524, 2025. [Source](https://arxiv.org/abs/2504.15524).

**Preprint.** Evaluates LLM intellectual-property knowledge across tasks. It provides a comparator for task capability rather than a product-specific legal judgment. **Supports C4, RQ3.**


### T5 | LLM forecasting, temporal leakage and reinforcement learning

[28] B. Turtel, D. Franklin, K. Skotheim, L. Hewitt, and P. Schoenegger, “Outcome-based reinforcement learning to predict the future,” arXiv:2505.17989, 2025. [Source](https://arxiv.org/abs/2505.17989).

**Preprint.** Uses resolved real-event outcomes as RL reward signals and reports probabilistic forecast experiments. **Supports C5, RQ3.**

[29] B. Turtel, P. Wilczewski, D. Franklin, and K. Skothiem, “Future-as-label: Scalable supervision from real-world outcomes,” arXiv:2601.06336, 2026. [Source](https://arxiv.org/abs/2601.06336).

**Preprint.** Uses causally masked information and proper scoring-rule rewards after event resolution. **Supports C5, RQ3.**

[30] A. A. Levy, “Reinforcement learning for LLM-based event forecasting,” arXiv:2606.15917, 2026. [Source](https://arxiv.org/abs/2606.15917).

**Thesis preprint.** Tests GRPO on real-event forecasting with pre-outcome information, including a small Qwen 2.5 model. **Supports C5, RQ3.**

[31] L. Ye et al., “AlphaBet: Reinforcement learning for LLM event forecasting agents,” arXiv:2610.22684, 2026. [Source](https://arxiv.org/abs/2610.22684).

**Preprint.** Trains search, reasoning and probability reporting jointly across several pre-resolution dates. **Supports C5, RQ3.**

[32] D. Paleka, S. Goel, J. Geiping, and F. Tramèr, “Pitfalls in evaluating language model forecasters,” arXiv:2506.00723, 2025. [Source](https://arxiv.org/abs/2506.00723).

**Preprint.** Examines evaluation pitfalls for LLM forecasters, including historical look-ahead and the interpretation of human comparisons. **Supports C5, RQ1, RQ3.**

[33] E. Karger et al., “ForecastBench: A dynamic benchmark of AI forecasting capabilities,” in Proc. ICLR, 2025. [Source](https://arxiv.org/abs/2409.19839).

**Primary peer-reviewed conference paper, linked preprint.** Continuously evaluates forecasts of unresolved questions, motivating prospective outcome-blind submission. **Supports C5, RQ1, RQ3.**

[34] S. He, L. Lv, A. Manela, and J. Wu, “Chronologically consistent large language models,” arXiv:2502.21206, 2025. [Source](https://arxiv.org/abs/2502.21206).

**Preprint version.** Trains models on time-restricted corpora and studies look-ahead in empirical applications. **Supports C5, RQ1, RQ3.**


### T6 | Evaluation, selective prediction and reproducibility

[35] Y. Geifman, G. Uziel, and R. El-Yaniv, “Bias-reduced uncertainty estimation for deep neural classifiers,” in Proc. ICLR, 2019. [Source](https://arxiv.org/abs/1805.08206).

**Primary peer-reviewed conference paper, linked preprint.** Shows how overconfident errors can distort selective risk and evaluates alternative uncertainty estimates. **Supports C6, RQ1, RQ3.**

[36] J. Traub et al., “Overcoming common flaws in the evaluation of selective classification systems,” in Adv. Neural Inf. Process. Syst., 2024. [Source](https://proceedings.neurips.cc/paper_files/paper/2024/file/047c84ec50bd8ea29349b996fc64af4b-Paper-Conference.pdf).

**Primary peer-reviewed conference paper.** Proposes area under the generalized risk–coverage curve (AUGRC) to summarize undetected failure risk across coverage. **Supports C6, RQ1.**

[37] T. Saito and M. Rehmsmeier, “The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets,” PLOS ONE, vol. 10, no. 3, Art. no. e0118432, 2015. [Source](https://doi.org/10.1371/journal.pone.0118432).

**Primary peer-reviewed.** Demonstrates why precision–recall displays help when positive outcomes are rare. **Supports C6, RQ1.**

[38] C. A. Field and A. H. Welsh, “Bootstrapping clustered data,” J. R. Stat. Soc. B, vol. 69, no. 3, pp. 369–390, 2007. [Source](https://doi.org/10.1111/j.1467-9868.2007.00593.x).

**Peer-reviewed statistical methods.** Studies bootstrap variants for clustered observations, motivating drug-level rather than row-level resampling. **Supports C6, RQ1.**

[39] US FDA, Multiple Endpoints in Clinical Trials: Guidance for Industry, Oct. 2022. [Source](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/multiple-endpoints-clinical-trials).

**Government guidance, grey.** Explains multiplicity control including ordered testing strategies across related endpoints. **Supports C6, RQ1.**

[40] O. van den Akker et al., “Preregistration of secondary data analysis: A template and tutorial,” Meta-Psychology, vol. 5, Art. no. 2625, 2021, doi: 10.15626/MP.2020.2625. [Source](https://research.tilburguniversity.edu/en/publications/preregistration-of-secondary-data-analysis-a-template-and-tutoria/).

**Peer-reviewed methods tutorial.** Provides a registration template capturing prior knowledge, data access and planned analyses for secondary data. **Supports C5, C6, RQ1.**

[41] S. Kapoor and A. Narayanan, “Leakage and the reproducibility crisis in machine-learning-based science,” Patterns, vol. 4, no. 9, Art. no. 100804, 2023. [Source](https://doi.org/10.1016/j.patter.2023.100804).

**Peer-reviewed methods and empirical audit.** Documents leakage modes across ML-based research and proposes reporting to make prevention auditable. **Supports C5, C6, RQ1.**

[42] T. Gebru et al., “Datasheets for datasets,” Commun. ACM, vol. 64, no. 12, pp. 86–92, 2021. [Source](https://arxiv.org/abs/1803.09010).

**Published methodology article, linked preprint.** Proposes documenting dataset motivation, composition, collection, uses and limitations. **Supports C5, C6, RQ1, RQ3.**


### T7 | Thai and ASEAN context

[43] P. Leela and N. Kessomboon, “Challenges of examination processes of pharmaceutical patent application in Thailand,” Isan J. Pharm. Sci., vol. 11, suppl., 2016. [Source](https://he01.tci-thaijo.org/index.php/IJPS/article/view/48601).

**Primary journal study, qualitative.** Document review and interviews with 19 key informants describe challenges in screening, examination and communication of search reports. **Supports C7, RQ3.**

[44] Tilleke & Gibbins, “Expediting the patent examination system in Thailand: Recent developments,” Mar. 2014. [Online]. [Source](https://www.tilleke.com/insights/expediting-patent-examination-system-thailand-recent-developments/).

**Practitioner commentary, grey.** Reports a historical 4–13 year range from substantive-examination request to grant for pharmaceutical applications, an interval distinct from filing to grant. **Supports C7, RQ3.**

[45] World Intellectual Property Organization, World Intellectual Property Indicators 2025, WIPO Publ. 941, 2025. [Source](https://www.wipo.int/edocs/pubdocs/en/wipo-pub-941-2025-en-world-intellectual-property-indicators-2025.pdf).

**Intergovernmental statistical report, grey.** Provides cross-office patent activity indicators and reporting definitions. Check denominators and edition before citing a Thailand-specific number. **Supports C7, RQ3.**

[46] ASEAN Intellectual Property Portal, “ASEAN IP Register.” [Online]. [Source](https://ip-register.aseanip.org/).

**Regional registry, primary administrative source.** Provides a regional patent-search entry point. Record the national office, evidence date and available status fields for each trace. **Supports C7, RQ3.**


### T8 | Authors’ prior work and the IS1 bridge

[47] S. Srihangpiboon and T. Ploysuwan, “Diagnosing near-zero instruction effects in cross-domain patent reranking,” conference paper listed in the iSAI-NLP program, paper 53, 2026. [Source](https://isai-nlp2026.aiat.or.th/program).

**Authors' prior conference paper, program-verified.** The authors report near-zero instruction contrasts in tested shortlists. Candidate-pool exposure motivates checking evidence availability in IS2. **Supports C8, RQ3.**

**UNVERIFIED as a standalone citation.** The authors' corrected KMITL IS1 study is recorded in the [project’s original-source ledger](https://github.com/siriponsri/patent-to-pilot/blob/0d5659a2/docs/evidence-scope/00-organization.md#original-source-corrections) under `IS1_ฉบับแก้ไข.pdf`. The ledger describes a separate post-hoc PatEmbed depth check on 725 queries, with known OUT-family exposure of 40.8% at 100 and 77.2% at 1,000. This is a first-stage exposure check, alongside Paper 53’s near-zero instruction contrasts in frozen top-100 pools. It motivates RQ3 and supports C8 as author-supplied context. Wait for the authors to supply approved citation metadata before adding an independent IS1 reference.

## Search strategy for extending the bibliography

Search 1999–November 2026 for the first pass. Include older foundational work when directly relevant and record the reason. Record database, date, query and filters. Search SciSpace and PubMed for discovery, then validate the record and the asserted finding on the publisher, author repository or official issuer site. Follow citations forward from the strongest endpoint-matched studies.

| Theme | Suggested query terms | Priority outlets and sources |
| --- | --- | --- |
| T1 | `first generic approval`, `first ANDA submission`, `generic market entry prediction`, `effective market exclusivity`, `survival analysis` | Clinical Pharmacology & Therapeutics, Clinical and Translational Science, Value in Health, FDA |
| T2 | `Orange Book historical editions`, `Paragraph IV`, `30-month stay`, `patent challenge timing`, `evergreening`, `biosimilar patent thicket` | Journal of Health Economics, Research Policy, Journal of Law and the Biosciences, FDA, Harvard Dataverse |
| T3 | `generic entrants price erosion`, `first mover generic`, `approved applicants vs marketed entrants`, `biosimilar uptake`, `prescription demand drift` | Review of Economics and Statistics, RAND Journal of Economics, Health Economics, International Journal of Forecasting, FDA and CMS |
| T4 | `freedom to operate patent search legal status claims`, `evidence trace patent AI`, `patent task benchmark` | WIPO guides, ACL and SIGIR proceedings, identifiable patent AI benchmark papers |
| T5 | `prospective LLM forecasting`, `temporal leakage`, `as-of data availability`, `GRPO outcome forecasting Brier` | ICLR, NeurIPS, ICML, ACL, arXiv for clearly marked recent work |
| T6 | `selective classification abstention risk coverage`, `recall at budget`, `cluster bootstrap rare event`, `fixed-sequence testing`, `secondary data preregistration` | NeurIPS, ICLR, JRSS B, PLOS ONE, Meta-Psychology, FDA |
| T7 | `Thailand pharmaceutical patent pendency`, `ASEAN patent national phase status`, `สิทธิบัตรยา ระยะเวลาตรวจสอบ` | Isan Journal of Pharmaceutical Sciences, ThaiJO, WIPO, Thai Department of Intellectual Property and ASEAN IP Register |
| T8 | `Diagnosing Near-Zero Instruction Effects in Cross-Domain Patent Reranking`, `iSAI-NLP 2026 paper 53`, `candidate pool exposure patent reranking` | Official conference program and any verified proceedings, author-cleared IS1 record |

**Include** studies with an identifiable cohort or benchmark, an explicit outcome and defensible time origin. Record jurisdiction, period, denominator, access or observation dates, and the selection rule. Include standards and vendor materials only for the workflow or market context they document. Label preprints and retain the version when results depend on it. **Exclude** DOI/title mismatches, inaccessible claims with no primary witness, duplicates across preprint and published versions, and historical evaluations presented as as-of without dated source support. If a weaker comparator is the closest match, describe its limitations and continue searching for a stronger one.

## Do-not list

- Exclude the project-banned arXiv manuscript specified by the authors. Do not enter its identifier in the bibliography.
- Do not fabricate references, identifiers, outcome counts, review-time savings or claims of nationwide FTO evaluator scarcity.
- Do not report Thai demand, market share, price erosion or FTO clearance as measured facts. P2 is the motivating risk. The FDA manufacturer-price factors are US scenario inputs, and SDUD reimbursement differs from realized market price.
- Do not treat FDA approval, marketed launch and patent expiry as interchangeable, or treat list absence as negative evidence without a coverage rule.
- Do not use development-only numbers as confirmation or claim that the historical gate passed, Track A matured, C9 ran or OSF submission was independently verified.
- Do not claim superiority over commercial products or an LLM class, or infer commercial launch, legal outcomes or reviewer productivity from a queue metric.
