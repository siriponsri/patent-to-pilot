# Literature Review for the IS2 Paper (Section 2): Market Window Dossier / LOE-Bench

*Bilingual working file: English Section 2 (Part A), reference list (Part B), evidence notes (Part C), Thai version (Part D). Citation numbers are IEEE-style, in order of first appearance, and are identical in both languages. English body: about 1532 words.*

---

# Part A. English version

## 2. Literature Review

### 2.1 Loss of exclusivity is several events, not one

Patent expiry, generic submission, final approval and commercial launch are different events, and the literature times different ones. Patent-based approximations anchor on expiry: among 170 top-selling drugs that lost exclusivity in 2000–2012, the predicted and actual median times to generic entry were both 12.5 years, but for 38 drugs protected only by secondary patents the predicted median was 16.0 years against an actual 8.25 years [1]. A companion paper extends the approximation to new drugs [2]; only its bibliographic record was accessible to us, so we attribute no finding to it. For biologics, patent-based expected entry was similar for biosimilars (median 12.3 years, n = 60) and generics (12.2 years, n = 268), yet by 2019 observed entry had occurred for 12% (3/25) of biosimilars and 65% (101/155) of generics [3]. Other studies time the first generic approval: effective market exclusivity, from NME approval to first generic approval, was modelled with Cox regression for 2001–2012 small-molecule NMEs [4], and an event-history model was fitted to 2,061 originator–generic pairs in South Korea [5]. Upstream, random survival forests predicted time to first ANDA submission after the earliest lawful submission date and outperformed Cox models in internal and external validation [6]; the same family of methods was applied to orphan products with leave-one-out and later-approval train/test validation [7]. Approval is also not marketing: of 687 first generics approved by FDA between January 2010 and June 2017, 118 (17%) were not marketed within the study frame, and among Paragraph IV first generics 53% were marketed within six months of approval and about 69% within two years [8]. These are retrospective studies with different endpoints, so their figures are not interchangeable. Vendor loss-of-exclusivity forecasts exist, but we could not open them and do not cite them.

### 2.2 Regulatory and challenge signals are conditional

Challenges are not random. Higher-sales drugs were challenged more often, later-expiring and lower-quality patents were disproportionately challenged, and effective market life was comparatively stable [9]. In a cohort of 46 first generics, Paragraph IV filing came a median 5.2 years after brand approval and a median 3.2 years separated 30-month stay expiry from launch; the authors concluded that stays were unlikely to delay entry [10]. Such signals therefore depend on patent type, remaining exclusivity, challenge status and stay timing, and on what was publicly recorded at the time. Digitised Orange Book editions make historical listings reconstructable, and the authors' validations suggest they are largely complete and accurate [11]; a separate replication dataset covers post-grant adjudication of drug patents before the agency and the courts [12] (cited as a data resource only; we did not analyse it). We found no verified study that rebuilds these signals as they were visible at each historical cutoff, separates filing from verified public availability and disposition, and treats undated records as unresolved. This is a limit of our targeted search, not a novelty claim. It motivates RQ1 and RQ3.

### 2.3 Competitive crowding and the market window

First-entry timing is only part of the window. Structural studies treat generic entry and industry dynamics as competitive processes [13], [14]. In Canada, the first generic entrant held about 30% more share among generics for at least four years [15]. For 181 US products with initial generic entry in 2015–2017, FDA reported median AMP-based generic-to-brand price ratios of 0.614 with one producer, 0.465 with two, 0.322 with three and 0.212 with four; rebates and consumer prices were excluded and the sample was limited to initial entry [16]. These quantities have different denominators: approved ANDA applicants only proxy potential competitors, marketed producers underlie the price ratios, share is measured among generics, and acquisition-price ratios are neither reimbursement nor realised price. US estimates can therefore seed scenarios but not forecasts for another market. Forecast accuracy is a further caution: for UK dispensing series around patent expiry, a naive-with-drift method was most accurate at 2–5-year horizons [17], and an industry-authored commentary reviews pharmaceutical forecasting accuracy [18] (we use none of its figures, which we could verify only from secondary copies). RQ2 accordingly treats later crowding as exploratory and price erosion as a bounded scenario.

### 2.4 Freedom-to-operate hand-off and patent AI

WIPO's landscape guidelines mention freedom to operate among the uses of landscapes, while a scope statement in the same document says a landscape need not assess validity or freedom to operate [19]. A WIPO guide teaches a self-study, three-stage search and analysis of published patent documents using freedom-to-operate determination tools [20]. Recent patent-AI benchmarks are comparators for task design: PatentAgentBench has 510 instances across eight suites including FTO search and design FTO [21]; IPBench covers eight IP mechanisms and 20 tasks, with the best of 17 LLMs at 75.8% accuracy [22]; and a BERT-based FTO analysis was tested on a narrow image-processing patent-class setup [23]. All three are preprints that measure task performance, not whether a hand-off lets qualified counsel resolve FTO faster or more reliably. The scarcity of FTO reviewers (P1) is owner-reported; we found no verified staffing baseline. The dossier is therefore designed as a traceable evidence pack and checklist; qualified counsel determines FTO.

### 2.5 Dating the evidence and the evaluation

LLM forecasters can be contaminated by information from after the forecast date: temporal leakage and extrapolation problems are documented in forecaster evaluations [24], and lookahead bias in financial text motivates chronologically consistent models [25]. ForecastBench addresses this with questions whose answers are unknown at submission, where expert forecasters outperformed the top LLM [26]; leakage is also a broader reproducibility threat in ML-based science [27]. Both evidence and evaluation therefore need dates and a prospective freeze. Outcome-trained reinforcement learning is a recent response: a 14B model matched or surpassed o1 accuracy on prediction-market questions [28], Foresight Learning improved Brier score by 27% for Qwen3-32B [29], GRPO was applied to small models with Wikipedia revisions or news tools [30], and multi-date agentic RL improved Brier scores on two forecasting benchmarks [31]. These preprints are author-reported and none concerns drug loss of exclusivity; they justify only an exploratory comparison (optional C9), not an expected gain. Preregistration templates for secondary data [32] and datasheets for datasets [33] frame how the evidence and its provenance are documented.

### 2.6 Review capacity, rare events and repeated observations

Selective prediction lets a system defer; confidence estimates for highly confident instances can be biased [34], and threshold-free evaluation should reflect the risk of undetected failures: the AUGRC metric changed method rankings on 5 of 6 datasets [35]. For rare events, precision–recall plots are more informative than ROC plots [36]. Because rows from one drug are correlated, clustered bootstrap intervals are appropriate [37]. FDA guidance on multiple endpoints, written for clinical trials, describes ordering endpoints to control false conclusions [38]; we borrow the idea by analogy for a fixed hypothesis sequence. A queue metric such as recall in the top 20% is a triage measure; it supports no inference about launch, legal outcomes or reviewer productivity.

### 2.7 Thai and ASEAN transfer

Evidence specific to Thai pharmaceutical patenting is thin in what we verified. Interviews with 19 key informants identified challenges at screening, request for examination, substantive examination and publication of search reports [39]. A 2014 law-firm commentary (grey, dated) reported an average of seven and a half years from application to grant in Thailand, and 4–13 years from request for examination to grant for pharmaceutical applications [40]. WIPO statistics give office-level indicators, for example 4,277 applications filed by Thai residents in 2024 [41]. None of these gives drug-level Thai loss-of-exclusivity, demand, price or FTO data, so US-derived values cannot be transferred and Thai demand, share, price erosion and FTO clearance are not measured here. We attempted to use the ASEAN IP Register but its page did not render verifiable content, so it is not cited.

### 2.8 The authors' prior work

Our earlier work on cross-domain patent reranking, listed as paper 53 in the iSAI-NLP 2026 programme [42], diagnoses near-zero instruction effects. We treat this, as author-supplied context (we reviewed only the programme listing), as the reason IS2 checks evidence availability and routes cases, rather than assuming that more instructions help.

### 2.9 Research gap

Across the sources we verified, timing forecasts, crowding and price studies, patent-AI benchmarks, LLM-forecasting work and evaluation methodology are largely separate literatures. We identify a specific integration gap: reconstructable open FDA evidence at each cutoff, combined with a matched fixed-capacity review queue with evidence-traced deferral, and an externally timestamped prospective check. This is not an exhaustive novelty claim, which would require a broader systematic search. RQ1 (confirmatory triage) asks whether graph-augmented prediction and deferral captures more first final original ANDA approvals within 24 and 12 months than an age/hazard table and a matched flat model. RQ2 (exploratory commercial context) asks whether the same frozen queues also capture drugs with at least three distinct approved ANDA applicants within 36 months, with price erosion as a scenario and US Medicaid use and reimbursement evaluated separately. RQ3 (exploratory, descriptive dossier) examines source-level traceability and referral of unresolved items, links the dated-evidence dossier to a Thai/ASEAN evaluator hand-off, and compares a minimal-input LLM, an evidence-matched LLM and the structured model. These are planned analyses, not findings.

---

# Part B. References (IEEE, numbered by first appearance)

Each entry is followed by its source type. Preprints, grey sources, official reports and programme listings are labelled as such.



[1] R. F. Beall, J. J. Darrow, and A. S. Kesselheim, “A method for approximating future entry of generic drugs,” *Value Health*, vol. 21, no. 12, pp. 1382–1389, Dec. 2018, doi: 10.1016/j.jval.2018.04.1827. — *Type: Peer-reviewed (abstract-level access)*

[2] R. F. Beall, J. J. Darrow, and A. S. Kesselheim, “Approximating future generic entry for new drugs,” *J. Law Med. Ethics*, vol. 47, no. 1, pp. 177–182, 2019, doi: 10.1177/1073110519840499. — *Type: Peer-reviewed (bibliographic record only; no abstract accessible, so no finding is attributed)*

[3] R. F. Beall *et al.*, “Comparing onset of biosimilar versus generic competition in the United States,” *Clin. Pharmacol. Ther.*, vol. 108, no. 6, pp. 1308–1314, 2020, doi: 10.1002/cpt.1981. — *Type: Peer-reviewed (abstract-level access)*

[4] K. W. Kerr and L. J. Glos, “Effective market exclusivity of new molecular entities for rare and non-rare diseases,” *Pharmaceut. Med.*, vol. 34, no. 1, pp. 19–29, 2020, doi: 10.1007/s40290-019-00317-9. — *Type: Peer-reviewed; FDA-authored*

[5] K.-B. Son, “Market exclusivity of the originator drugs in South Korea: A retrospective cohort study,” *Front. Public Health*, vol. 9, Art. no. 654952, 2021, doi: 10.3389/fpubh.2021.654952. — *Type: Peer-reviewed*

[6] M. Hu *et al.*, “Predictive analysis of first abbreviated new drug application submission for new chemical entities based on machine learning methodology,” *Clin. Pharmacol. Ther.*, vol. 106, no. 1, pp. 174–181, 2019, doi: 10.1002/cpt.1479. — *Type: Peer-reviewed; FDA-authored*

[7] R. Hopefl *et al.*, “Predictive analysis for first submission of generic drug application for orphan drug products using random survival forest,” *Clin. Transl. Sci.*, vol. 18, no. 10, Art. no. e70365, Oct. 2025, doi: 10.1111/cts.70365. — *Type: Peer-reviewed (full text read)*

[8] H. S. Chahal, R. Patel, and M. Shimer, “Marketing of first generic drugs approved by U.S. FDA from January 2010 to June 2017,” U.S. Food and Drug Administration, Silver Spring, MD, USA, Nov. 2021. [Online]. Available: https://www.fda.gov/media/154101/download — *Type: Official agency report (not peer-reviewed)*

[9] C. S. Hemphill and B. N. Sampat, “Evergreening, patent challenges, and effective market life in pharmaceuticals,” *J. Health Econ.*, vol. 31, no. 2, pp. 327–339, 2012, doi: 10.1016/j.jhealeco.2012.01.004. — *Type: Peer-reviewed (abstract-level access)*

[10] S. Kannappan, J. J. Darrow, A. S. Kesselheim, and R. F. Beall, “The timing of 30-month stay expirations and generic entry: A cohort study of first generics, 2013–2020,” *Clin. Transl. Sci.*, vol. 14, no. 5, pp. 1917–1923, 2021, doi: 10.1111/cts.13046. — *Type: Peer-reviewed (abstract-level access)*

[11] M. Durvasula *et al.*, “The NBER Orange Book dataset: A user’s guide,” *Res. Policy*, vol. 52, no. 7, Art. no. 104791, 2023, doi: 10.1016/j.respol.2023.104791. — *Type: Peer-reviewed (open access, PMC10731339; abstract-level access)*

[12] A. K. Rai, S. Vishnubhakat, J. Lemus, and E. Hovenkamp, “Replication data for: Post-grant adjudication of drug patents: Agency and/or court?,” Harvard Dataverse, ver. 1.0, 2021, doi: 10.7910/DVN/YCMKVU. — *Type: Dataset record (DataCite metadata checked; files not analysed)*

[13] F. M. Scott Morton, “Entry decisions in the generic pharmaceutical industry,” *RAND J. Econ.*, vol. 30, no. 3, p. 421 ff., 1999, doi: 10.2307/2556056. — *Type: Peer-reviewed (bibliographic record only; end page not confirmed)*

[14] D. Reiffen and M. R. Ward, “Generic drug industry dynamics,” *Rev. Econ. Stat.*, vol. 87, no. 1, pp. 37–49, 2005, doi: 10.1162/0034653053327694. — *Type: Peer-reviewed (bibliographic record only)*

[15] A. Hollis, “The importance of being first: Evidence from Canadian generic pharmaceuticals,” *Health Econ.*, vol. 11, no. 8, pp. 723–734, 2002, doi: 10.1002/hec.698. — *Type: Peer-reviewed (abstract-level access)*

[16] R. Conrad and R. Lutter, “Generic competition and drug prices: New evidence linking greater generic competition and lower generic drug prices,” U.S. Food and Drug Administration, Silver Spring, MD, USA, Dec. 2019. [Online]. Available: https://www.fda.gov/media/133509/download — *Type: Official agency report (not peer-reviewed)*

[17] K. Nikolopoulos, S. Buxton, M. Khammash, and P. Stern, “Forecasting branded and generic pharmaceuticals,” *Int. J. Forecast.*, vol. 32, no. 2, pp. 344–357, 2016, doi: 10.1016/j.ijforecast.2015.08.001. — *Type: Peer-reviewed (abstract read via institutional repository)*

[18] M. Cha, B. Rifai, and P. Sarraf, “Pharmaceutical forecasting: Throwing darts?,” *Nat. Rev. Drug Discov.*, vol. 12, no. 10, pp. 737–738, 2013, doi: 10.1038/nrd4127. — *Type: Industry-authored commentary (publisher page checked; full text paywalled, no figures from it are used)*

[19] World Intellectual Property Organization, *Guidelines for Preparing Patent Landscape Reports*, WIPO Publ. 946, Geneva, Switzerland, 2015. [Online]. Available: https://www.wipo.int/edocs/pubdocs/en/wipo_pub_946.pdf — *Type: Official guidance (WIPO)*

[20] World Intellectual Property Organization, *Identifying Inventions in the Public Domain: A Guide for Inventors and Entrepreneurs*, WIPO Publ. 1062, Geneva, Switzerland, 2020. [Online]. Available: https://www.wipo.int/publications/en/details.jsp?id=4501 — *Type: Official guidance (WIPO; catalogue page read)*

[21] Y. Hu *et al.*, “PatentAgentBench: Benchmarking LLM agents with professional patent task suites,” arXiv:2610.35031, 2026. [Online]. Available: https://arxiv.org/abs/2610.35031 — *Type: Preprint*

[22] Q. Wang *et al.*, “IPBench: Benchmarking the knowledge of large language models in intellectual property,” arXiv:2504.15524, 2025. [Online]. Available: https://arxiv.org/abs/2504.15524 — *Type: Preprint*

[23] M. Freunek and A. Bodmer, “BERT based freedom to operate patent analysis,” arXiv:2105.00817, 2021. [Online]. Available: https://arxiv.org/abs/2105.00817 — *Type: Preprint*

[24] D. Paleka, S. Goel, J. Geiping, and F. Tramèr, “Pitfalls in evaluating language model forecasters,” arXiv:2506.00723, 2025. [Online]. Available: https://arxiv.org/abs/2506.00723 — *Type: Preprint*

[25] S. He, L. Lv, A. Manela, and J. Wu, “Chronologically consistent large language models,” arXiv:2502.21206, 2025. [Online]. Available: https://arxiv.org/abs/2502.21206 — *Type: Preprint*

[26] E. Karger *et al.*, “ForecastBench: A dynamic benchmark of AI forecasting capabilities,” in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2025. [Online]. Available: https://proceedings.iclr.cc/paper_files/paper/2025/hash/ea74e45a229dac70b5b63b28d8934db6-Abstract-Conference.html (preprint: arXiv:2409.19839) — *Type: Conference paper (ICLR 2025 proceedings record confirmed)*

[27] S. Kapoor and A. Narayanan, “Leakage and the reproducibility crisis in machine-learning-based science,” *Patterns*, vol. 4, no. 9, Art. no. 100804, 2023, doi: 10.1016/j.patter.2023.100804. — *Type: Peer-reviewed (bibliographic record only)*

[28] B. Turtel, D. Franklin, K. Skotheim, L. Hewitt, and P. Schoenegger, “Outcome-based reinforcement learning to predict the future,” arXiv:2505.17989, 2025. [Online]. Available: https://arxiv.org/abs/2505.17989 — *Type: Preprint*

[29] B. Turtel, P. Wilczewski, D. Franklin, and K. Skothiem, “Future-as-label: Scalable supervision from real-world outcomes,” arXiv:2601.06336, 2026. [Online]. Available: https://arxiv.org/abs/2601.06336 — *Type: Preprint (author name spelled as on arXiv)*

[30] A. A. Levy, “Reinforcement learning for LLM-based event forecasting,” arXiv:2606.15917, 2026. [Online]. Available: https://arxiv.org/abs/2606.15917 — *Type: Preprint (MSc thesis, University of Oxford)*

[31] L. Ye *et al.*, “AlphaBet: Reinforcement learning for LLM event forecasting agents,” arXiv:2610.22684, 2026. [Online]. Available: https://arxiv.org/abs/2610.22684 — *Type: Preprint*

[32] O. van den Akker *et al.*, “Preregistration of secondary data analysis: A template and tutorial,” *Meta-Psychology*, vol. 5, 2021, doi: 10.15626/MP.2020.2625. — *Type: Peer-reviewed (bibliographic record only)*

[33] T. Gebru *et al.*, “Datasheets for datasets,” *Commun. ACM*, vol. 64, no. 12, pp. 86–92, 2021, doi: 10.1145/3458723. — *Type: Peer-reviewed (arXiv:1803.09010 matched)*

[34] Y. Geifman, G. Uziel, and R. El-Yaniv, “Bias-reduced uncertainty estimation for deep neural classifiers,” in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2019. [Online]. Available: https://arxiv.org/abs/1805.08206 — *Type: Conference paper (arXiv version read)*

[35] J. Traub *et al.*, “Overcoming common flaws in the evaluation of selective classification systems,” in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, 2024. [Online]. Available: https://proceedings.neurips.cc/paper_files/paper/2024/file/047c84ec50bd8ea29349b996fc64af4b-Paper-Conference.pdf — *Type: Conference paper (proceedings PDF read)*

[36] T. Saito and M. Rehmsmeier, “The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets,” *PLOS ONE*, vol. 10, no. 3, Art. no. e0118432, 2015, doi: 10.1371/journal.pone.0118432. — *Type: Peer-reviewed (bibliographic record only)*

[37] C. A. Field and A. H. Welsh, “Bootstrapping clustered data,” *J. R. Stat. Soc. B*, vol. 69, no. 3, pp. 369–390, 2007, doi: 10.1111/j.1467-9868.2007.00593.x. — *Type: Peer-reviewed (bibliographic record only)*

[38] U.S. Food and Drug Administration, *Multiple Endpoints in Clinical Trials: Guidance for Industry*, docket FDA-2016-D-4460, 2022. [Online]. Available: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/multiple-endpoints-clinical-trials — *Type: Official guidance (landing page read; month of issue not shown on the page)*

[39] P. Leela and N. Kessomboon, “Challenges of examination processes of pharmaceutical patent application in Thailand,” *Isan J. Pharm. Sci.*, vol. 11, suppl., Feb. 2016. [Online]. Available: https://he01.tci-thaijo.org/index.php/IJPS/article/view/48601 — *Type: Peer-reviewed (supplement abstract; qualitative interviews)*

[40] Tilleke & Gibbins, “Expediting the patent examination system in Thailand: Recent developments,” Bangkok, Thailand, Mar. 3, 2014. [Online]. Available: https://www.tilleke.com/insights/expediting-patent-examination-system-thailand-recent-developments/ — *Type: Grey source (law-firm commentary; dated)*

[41] World Intellectual Property Organization, *World Intellectual Property Indicators 2025*, WIPO Publ. 941, Geneva, Switzerland, 2025. [Online]. Available: https://www.wipo.int/edocs/pubdocs/en/wipo-pub-941-2025-en-world-intellectual-property-indicators-2025.pdf — *Type: Official statistics (WIPO)*

[42] S. Srihangpiboon and T. Ploysuwan, “Diagnosing near-zero instruction effects in cross-domain patent reranking,” paper 53, iSAI-NLP 2026 programme. [Online]. Available: https://isai-nlp2026.aiat.or.th/program — *Type: Conference programme listing only (title, authors and session slot verified; text not reviewed)*

---

# Part C. Evidence notes and verification status

This section lists what was and was not verified, so that readers can weigh each citation. It is part of the working file and can be shortened before submission.

- **Scope of the review.** The section reviews only sources that we could open and check against a bibliographic record, abstract or full text. It makes a specific integration-gap statement, not an exhaustive novelty claim.
- **Excluded sources.** Five seed references from the brief (vendor pages and a vendor/industry report: DrugPatentWatch, an IQVIA article, an Evaluate loss-of-exclusivity landing page, an IQVIA Institute biosimilars report, and the ASEAN IP Register) could not be opened or verified and are not cited. The IS1 corrected study (paper 47) is not cited on its own; only the iSAI-NLP programme listing for paper 53 [42] is cited, and IS1 is treated as author-supplied context.
- **Banned manuscript.** The brief names a banned arXiv manuscript but gives no identifier, so no such identifier was entered; none of the seed references was identified as that manuscript.
- **Access level of each reference.** Full text was read for [7] and [35]; the relevant passages of the WIPO documents [19] and [41] were opened and read. Abstract-level access only: [11], [1], [3], [4], [9], [10], [15], [17], [39]. Bibliographic record only, so no findings are attributed: [2], [13], [14], [27], [32], [36], [37]. The commentary [18] is paywalled; none of its figures are used. The Replication dataset [12] was checked at metadata level and its files were not analysed.
- **Corrected details.** DOIs were corrected for Hemphill and Sampat ([9]) and for Reiffen and Ward ([14]). The end page of Scott Morton ([13]) is not confirmed. The issue month of the FDA multiple-endpoints guidance [38] is not shown on its web page (the brief gives October 2022), so only the year is cited. ForecastBench [26] is cited as the ICLR 2025 proceedings record.
- **Evidence gaps.** Among the sources we verified, only [7] is a forward (later-approval) time-split validation. We found no verified study that reconstructs the evidence as of each historical cutoff. This limit applies to our targeted search only. The data licence of the NBER Orange Book dataset [11] was not verified. No verified baseline of FTO reviewer scarcity (P1) or Thai drug-level demand, price or FTO data was found.
- **Claim separation.** Reported findings (past studies), descriptive associations, scenario assumptions (US price ratios), owner-reported opinions (P1) and planned analyses (RQ1–RQ3, optional C9) are marked as such in the text. No development-only number is used as confirmation; the text does not claim that the historical gate passed, that Track A matured, that C9 ran, or that the OSF registration was verified.
- **Status.** This is a literature review, not a legal or clinical opinion.

---

# Part D. ฉบับภาษาไทย (Thai version)

*ฉบับแปลของ Part A คงเลขอ้างอิงและขอบเขตของข้ออ้างทุกข้อเหมือนต้นฉบับภาษาอังกฤษ ศัพท์เทคนิคคงเป็นภาษาอังกฤษ รายการอ้างอิงใช้ชุดเดียวกับ Part B*

## 2. การทบทวนวรรณกรรม (Literature Review)

### 2.1 การสูญเสียสิทธิผูกขาด (loss of exclusivity) ไม่ใช่เหตุการณ์เดียว

การหมดอายุของสิทธิบัตร การยื่นขออนุมัติยาสามัญ (generic submission) การอนุมัติขั้นสุดท้าย (final approval) และการวางจำหน่ายเชิงพาณิชย์ (commercial launch) เป็นคนละเหตุการณ์กัน และงานวิจัยแต่ละชิ้นจับเวลาคนละจุด การประมาณจากสิทธิบัตรใช้วันหมดอายุเป็นจุดยึด: ในยาขายดี 170 รายการที่สูญเสียสิทธิผูกขาดในช่วงปี 2000–2012 ค่ามัธยฐานของเวลาที่ทำนายและเวลาจริงกว่ายาสามัญจะเข้าสู่ตลาดเท่ากันที่ 12.5 ปี แต่สำหรับยา 38 รายการที่ได้รับการคุ้มครองด้วยสิทธิบัตรรอง (secondary patents) เท่านั้น ค่ามัธยฐานที่ทำนายคือ 16.0 ปี เทียบกับค่าจริง 8.25 ปี [1] งานคู่กันขยายวิธีประมาณนี้ไปยังยาใหม่ [2] แต่เราเข้าถึงได้เพียงระเบียนบรรณานุกรม จึงไม่อ้างผลการศึกษาใด ๆ จากงานนี้ สำหรับยาชีววัตถุ เวลาเข้าสู่ตลาดที่คาดจากสิทธิบัตรใกล้เคียงกันระหว่าง biosimilar (มัธยฐาน 12.3 ปี, n = 60) และยาสามัญ (12.2 ปี, n = 268) แต่ ณ ปี 2019 พบการเข้าสู่ตลาดจริงใน biosimilar เพียง 12% (3/25) เทียบกับยาสามัญ 65% (101/155) [3] งานอื่นจับเวลาที่การอนุมัติยาสามัญตัวแรก: effective market exclusivity ซึ่งนับจากการอนุมัติ NME ถึงการอนุมัติยาสามัญตัวแรก ถูกจำลองด้วย Cox regression สำหรับ NME โมเลกุลเล็กปี 2001–2012 [4] และมีการใช้แบบจำลอง event-history กับคู่ยาต้นแบบ–ยาสามัญ 2,061 คู่ในเกาหลีใต้ [5] ในขั้นต้นน้ำ random survival forest ถูกใช้ทำนายเวลาถึงการยื่น ANDA ครั้งแรกหลังวันที่ยื่นได้ตามกฎหมายเร็วที่สุด และให้ผลดีกว่าแบบจำลอง Cox ทั้งในการตรวจสอบภายในและภายนอก [6] วิธีการตระกูลเดียวกันนี้ถูกนำไปใช้กับผลิตภัณฑ์ยากำพร้า (orphan) โดยตรวจสอบด้วย leave-one-out และการแบ่งฝึก/ทดสอบตามการอนุมัติที่เกิดทีหลัง [7] นอกจากนี้ การอนุมัติไม่เท่ากับการวางตลาด: จากยาสามัญตัวแรก 687 รายการที่ FDA อนุมัติระหว่างเดือนมกราคม 2010 ถึงมิถุนายน 2017 มี 118 รายการ (17%) ที่ไม่ได้วางตลาดภายในกรอบการศึกษา และในกลุ่มยาสามัญตัวแรกแบบ Paragraph IV มี 53% ที่วางตลาดภายในหกเดือนหลังอนุมัติ และประมาณ 69% ภายในสองปี [8] ทั้งหมดนี้เป็นการศึกษาย้อนหลังที่มี endpoint ต่างกัน ตัวเลขจึงใช้แทนกันไม่ได้ มีการพยากรณ์ loss-of-exclusivity ของผู้ให้บริการเชิงพาณิชย์ แต่เราเปิดอ่านไม่ได้จึงไม่อ้างอิง

### 2.2 สัญญาณด้านกฎระเบียบและการท้าทายสิทธิบัตรขึ้นกับเงื่อนไข

การท้าทายสิทธิบัตรไม่ได้เกิดแบบสุ่ม ยาที่มียอดขายสูงถูกท้าทายบ่อยกว่า สิทธิบัตรที่หมดอายุช้ากว่าและคุณภาพต่ำกว่าถูกท้าทายเกินสัดส่วน และ effective market life ค่อนข้างคงที่ [9] ในกลุ่มศึกษายาสามัญตัวแรก 46 รายการ การยื่น Paragraph IV เกิดขึ้นเมื่อมัธยฐาน 5.2 ปีหลังการอนุมัติยาต้นแบบ และมัธยฐาน 3.2 ปีคั่นระหว่างการสิ้นสุด 30-month stay กับการวางตลาด ผู้เขียนสรุปว่า stay ไม่น่าจะทำให้การเข้าสู่ตลาดล่าช้า [10] สัญญาณเหล่านี้จึงขึ้นกับชนิดของสิทธิบัตร สิทธิผูกขาดที่เหลืออยู่ สถานะการท้าทาย และจังหวะของ stay รวมทั้งสิ่งที่ถูกบันทึกเป็นสาธารณะ ณ เวลานั้น Orange Book ฉบับที่แปลงเป็นดิจิทัลทำให้สร้างรายการสิทธิบัตรย้อนหลังได้ และผู้เขียนรายงานว่าการตรวจสอบบ่งชี้ว่าข้อมูลครบถ้วนและถูกต้องเป็นส่วนใหญ่ [11] ส่วนชุดข้อมูลสำหรับการจำลองงานอีกชุดครอบคลุมการพิจารณาหลังการออกสิทธิบัตรของสิทธิบัตรยาต่อหน่วยงานและศาล [12] (อ้างในฐานะแหล่งข้อมูลเท่านั้น เราไม่ได้วิเคราะห์ชุดข้อมูลนี้) เราไม่พบงานที่ผ่านการตรวจสอบแล้วซึ่งสร้างสัญญาณเหล่านี้ใหม่ตามที่มองเห็นได้ ณ แต่ละ cutoff ในอดีต แยกการยื่นออกจากความพร้อมใช้งานสาธารณะที่ตรวจสอบได้และสถานะการพิจารณา และถือว่าระเบียนที่ไม่มีวันที่เป็นเรื่องที่ยังไม่ได้ข้อสรุป นี่เป็นข้อจำกัดของการค้นแบบเจาะจงของเรา ไม่ใช่การอ้างความใหม่ และเป็นแรงจูงใจของ RQ1 และ RQ3

### 2.3 การแออัดของคู่แข่งและช่วงเวลาตลาด (market window)

เวลาที่ผู้เข้าตลาดรายแรกเข้ามาเป็นเพียงส่วนหนึ่งของช่วงเวลาตลาด งานเชิงโครงสร้างมองการเข้าสู่ตลาดของยาสามัญและพลวัตของอุตสาหกรรมเป็นกระบวนการแข่งขัน [13], [14] ในแคนาดา ผู้เข้าตลาดยาสามัญรายแรกมีส่วนแบ่งในกลุ่มยาสามัญสูงกว่าประมาณ 30% เป็นเวลาอย่างน้อยสี่ปี [15] สำหรับผลิตภัณฑ์สหรัฐฯ 181 รายการที่มีการเข้าสู่ตลาดของยาสามัญครั้งแรกในปี 2015–2017 FDA รายงานค่ามัธยฐานของอัตราส่วนราคายาสามัญต่อยาต้นแบบตาม AMP เท่ากับ 0.614 เมื่อมีผู้ผลิตหนึ่งราย 0.465 เมื่อมีสองราย 0.322 เมื่อมีสามราย และ 0.212 เมื่อมีสี่ราย โดยไม่รวมส่วนลด (rebates) และราคาผู้บริโภค และจำกัดเฉพาะตัวอย่างที่มีการเข้าสู่ตลาดครั้งแรก [16] ปริมาณเหล่านี้มีตัวหารต่างกัน: ผู้ยื่น ANDA ที่ได้รับอนุมัติเป็นเพียงตัวแทนของคู่แข่งที่อาจเกิดขึ้น ผู้ผลิตที่วางตลาดอยู่เป็นฐานของอัตราส่วนราคา ส่วนแบ่งวัดในกลุ่มยาสามัญ และอัตราส่วนราคาซื้อไม่ใช่ราคาเบิกจ่ายหรือราคาที่เกิดขึ้นจริง ค่าประมาณของสหรัฐฯ จึงใช้เป็นต้นทางของสถานการณ์สมมติ (scenario) ได้ แต่ไม่ใช่การพยากรณ์สำหรับตลาดอื่น ความแม่นยำของการพยากรณ์เป็นข้อควรระวังเพิ่มเติม: สำหรับอนุกรมการจ่ายยาในสหราชอาณาจักรรอบการหมดสิทธิบัตร วิธี naive-with-drift แม่นยำที่สุดที่ขอบเขตเวลา 2–5 ปี [17] และมีบทวิจารณ์ที่เขียนโดยภาคอุตสาหกรรมทบทวนความแม่นยำของการพยากรณ์ยา [18] (เราไม่ใช้ตัวเลขใด ๆ จากบทความนี้ เพราะตรวจสอบได้จากสำเนารองเท่านั้น) RQ2 จึงถือการแออัดในภายหลังเป็นการวิเคราะห์เชิงสำรวจ และถือการลดลงของราคาเป็นสถานการณ์สมมติที่มีขอบเขตจำกัด

### 2.4 การส่งมอบงาน freedom-to-operate (FTO) และ AI ด้านสิทธิบัตร

แนวทางการจัดทำ landscape ของ WIPO กล่าวถึง freedom to operate เป็นหนึ่งในการใช้ประโยชน์ของ landscape ขณะที่ข้อความระบุขอบเขตในเอกสารเดียวกันระบุว่ารายงาน landscape ไม่จำเป็นต้องประเมินความสมบูรณ์ของสิทธิ (validity) หรือ FTO [19] คู่มือของ WIPO สอนการค้นและวิเคราะห์เอกสารสิทธิบัตรที่เผยแพร่แล้วด้วยตนเองเป็นสามขั้น โดยใช้เครื่องมือสำหรับการพิจารณา freedom to operate [20] เกณฑ์วัด (benchmark) ด้าน AI สิทธิบัตรล่าสุดเป็นตัวเปรียบเทียบสำหรับการออกแบบงาน: PatentAgentBench มี 510 อินสแตนซ์ใน 8 ชุดงาน รวมการค้น FTO และ design FTO [21]; IPBench ครอบคลุมกลไกทรัพย์สินทางปัญญา 8 แบบและ 20 งาน โดย LLM ที่ดีที่สุดจาก 17 ตัวได้ความแม่นยำ 75.8% [22]; และการวิเคราะห์ FTO ด้วย BERT ถูกทดสอบกับชุดสิทธิบัตรด้านการประมวลผลภาพที่แคบ [23] ทั้งสามเป็น preprint ที่วัดสมรรถนะของงาน ไม่ได้วัดว่าการส่งมอบงานช่วยให้ที่ปรึกษาที่มีคุณสมบัติตัดสิน FTO ได้เร็วหรือแม่นยำขึ้นหรือไม่ ปัญหาการขาดแคลนผู้ประเมิน FTO (P1) เป็นข้อมูลที่เจ้าของโครงการรายงานเอง (owner-reported) เราไม่พบข้อมูลฐานด้านกำลังคนที่ตรวจสอบแล้ว ดังนั้น dossier ถูกออกแบบเป็นชุดหลักฐานที่ตรวจย้อนกลับได้และรายการตรวจสอบ ส่วนการตัดสิน FTO เป็นหน้าที่ของที่ปรึกษาที่มีคุณสมบัติ

### 2.5 การระบุวันที่ของหลักฐานและของการประเมิน

ตัวพยากรณ์ที่ใช้ LLM อาจปนเปื้อนข้อมูลหลังวันพยากรณ์: ปัญหา temporal leakage และการอนุมานนอกช่วงข้อมูลมีบันทึกไว้ในการประเมินตัวพยากรณ์ [24] และ lookahead bias ในข้อความทางการเงินเป็นเหตุผลของแบบจำลองที่สอดคล้องตามลำดับเวลา [25] ForecastBench แก้ปัญหานี้ด้วยคำถามที่ยังไม่ทราบคำตอบ ณ เวลาส่ง โดยผู้เชี่ยวชาญด้านการพยากรณ์ทำได้ดีกว่า LLM ที่ดีที่สุด [26]; การรั่วไหลของข้อมูลยังเป็นภัยต่อการทำซ้ำผลในวงกว้างของวิทยาศาสตร์ที่ใช้ ML [27] ทั้งหลักฐานและการประเมินจึงต้องมีวันที่และการตรึง (freeze) แบบมองไปข้างหน้า การเรียนรู้แบบเสริมกำลัง (RL) ที่ฝึกจากผลลัพธ์เป็นการตอบสนองล่าสุด: โมเดล 14B เทียบเท่าหรือเหนือกว่าความแม่นยำของ o1 บนคำถามจาก prediction market [28], Foresight Learning ปรับปรุง Brier score 27% สำหรับ Qwen3-32B [29], มีการใช้ GRPO กับโมเดลขนาดเล็กร่วมกับการแก้ไขวิกิพีเดียหรือเครื่องมือข่าว [30] และ RL แบบ agentic หลายวันที่ปรับปรุง Brier score ใน benchmark การพยากรณ์สองชุด [31] preprint เหล่านี้เป็นตัวเลขที่ผู้เขียนรายงานเอง และไม่มีชิ้นใดเกี่ยวกับ loss of exclusivity ของยา จึงรองรับได้เพียงการเปรียบเทียบเชิงสำรวจ (C9 ซึ่งเป็นตัวเลือก) ไม่ใช่ผลได้ที่คาดหวัง แม่แบบการลงทะเบียนล่วงหน้า (preregistration) สำหรับข้อมูลทุติยภูมิ [32] และ datasheets for datasets [33] เป็นกรอบการบันทึกหลักฐานและที่มาของข้อมูล

### 2.6 กำลังการทบทวน เหตุการณ์หายาก และข้อสังเกตที่ซ้ำกัน

Selective prediction ทำให้ระบบเลื่อนการตัดสิน (defer) ได้; ค่าความเชื่อมั่นของอินสแตนซ์ที่มั่นใจสูงอาจมีอคติ [34] และการประเมินแบบไม่ขึ้นกับ threshold ควรสะท้อนความเสี่ยงของความล้มเหลวที่ตรวจไม่พบ: metric AUGRC เปลี่ยนอันดับของวิธีการใน 5 จาก 6 ชุดข้อมูล [35] สำหรับเหตุการณ์หายาก กราฟ precision–recall ให้ข้อมูลมากกว่ากราฟ ROC [36] เนื่องจากแถวข้อมูลของยาตัวเดียวกันสัมพันธ์กัน จึงเหมาะที่จะใช้ช่วงความเชื่อมั่นแบบ clustered bootstrap [37] แนวทางของ FDA เรื่อง multiple endpoints ซึ่งเขียนสำหรับการทดลองทางคลินิก อธิบายการจัดลำดับ endpoint เพื่อควบคุมข้อสรุปที่ผิดพลาด [38]; เรายืมแนวคิดนี้โดยเทียบเคียงสำหรับลำดับสมมติฐานที่กำหนดตายตัว metric ของคิว เช่น recall ใน top 20% เป็นมาตรวัดการคัดแยก (triage) ไม่รองรับการอนุมานใด ๆ เกี่ยวกับการวางตลาด ผลทางกฎหมาย หรือประสิทธิภาพของผู้ทบทวน

### 2.7 การถ่ายโอนสู่ไทยและอาเซียน

หลักฐานเฉพาะด้านสิทธิบัตรยาของไทยมีจำกัดในสิ่งที่เราตรวจสอบได้ การสัมภาษณ์ผู้ให้ข้อมูลหลัก 19 คนระบุความท้าทายในขั้นตอนการคัดกรอง การขอตรวจสอบ การตรวจสอบเนื้อหา และการเผยแพร่รายงานการค้น [39] บทวิจารณ์ปี 2014 ของสำนักงานกฎหมาย (grey source, มีวันที่) รายงานค่าเฉลี่ยเจ็ดปีครึ่งตั้งแต่ยื่นคำขอจนถึงออกสิทธิบัตรในประเทศไทย และ 4–13 ปีตั้งแต่การขอตรวจสอบเนื้อหาจนถึงออกสิทธิบัตรสำหรับคำขอด้านยา [40] สถิติของ WIPO ให้ตัวชี้วัดระดับสำนักงาน เช่น คำขอที่ยื่นโดยผู้มีถิ่นที่อยู่ในไทย 4,277 คำขอในปี 2024 [41] ไม่มีแหล่งใดให้ข้อมูลระดับตัวยาของไทยเกี่ยวกับ loss of exclusivity ความต้องการ ราคา หรือ FTO ดังนั้นค่าที่ได้จากสหรัฐฯ จึงถ่ายโอนไม่ได้ และ demand ส่วนแบ่งตลาด การลดลงของราคา และการเคลียร์ FTO ของไทยไม่ได้ถูกวัดในงานนี้ เราพยายามใช้ ASEAN IP Register แต่หน้าเว็บไม่แสดงเนื้อหาที่ตรวจสอบได้ จึงไม่อ้างอิง

### 2.8 งานก่อนหน้าของผู้เขียน

งานก่อนหน้าของเราเรื่องการจัดอันดับสิทธิบัตรข้ามโดเมน (cross-domain patent reranking) ซึ่งอยู่ในรายการ paper 53 ของโปรแกรม iSAI-NLP 2026 [42] วินิจฉัยผลของ instruction ที่ใกล้ศูนย์ (near-zero instruction effects) เราถือสิ่งนี้เป็นบริบทที่ผู้เขียนให้มา (เราตรวจสอบเฉพาะรายการในโปรแกรม) และเป็นเหตุผลที่ IS2 ตรวจสอบความพร้อมของหลักฐานและส่งต่อ (route) แต่ละกรณี แทนที่จะสมมติว่าการเพิ่ม instruction จะช่วยเสมอ

### 2.9 ช่องว่างงานวิจัย (Research gap)

ในแหล่งที่เราตรวจสอบแล้ว งานพยากรณ์เวลา งานด้านการแออัดของคู่แข่งและราคา เกณฑ์วัด AI ด้านสิทธิบัตร งานพยากรณ์ด้วย LLM และระเบียบวิธีประเมินผล ส่วนใหญ่เป็นวรรณกรรมที่แยกจากกัน เราระบุช่องว่างเชิงบูรณาการที่เฉพาะเจาะจง: หลักฐานเปิดของ FDA ที่สร้างใหม่ได้ ณ แต่ละ cutoff ร่วมกับคิวทบทวนความจุคงที่ที่จับคู่กัน ซึ่งมีการเลื่อนการตัดสินที่ตรวจย้อนไปยังหลักฐานได้ และการตรวจสอบแบบมองไปข้างหน้าที่มีการประทับเวลาจากภายนอก นี่ไม่ใช่การอ้างความใหม่แบบครบถ้วน ซึ่งต้องอาศัยการค้นเชิงระบบที่กว้างกว่านี้ RQ1 (การคัดแยกเชิงยืนยัน, confirmatory triage) ถามว่าการทำนายแบบเสริมกราฟและการเลื่อนการตัดสินจับการอนุมัติ ANDA ต้นฉบับขั้นสุดท้ายครั้งแรกได้มากกว่าตาราง age/hazard และแบบจำลอง flat ที่จับคู่กันภายใน 24 และ 12 เดือนหรือไม่ RQ2 (บริบทเชิงพาณิชย์แบบสำรวจ, exploratory commercial context) ถามว่าคิวที่ตรึงแล้วชุดเดียวกันจับยาที่มีผู้ยื่น ANDA ที่ได้รับอนุมัติอย่างน้อยสามรายที่แตกต่างกันภายใน 36 เดือนได้ด้วยหรือไม่ โดยถือการลดลงของราคาเป็นสถานการณ์สมมติ และประเมินการใช้และการเบิกจ่ายของ US Medicaid แยกต่างหาก RQ3 (dossier เชิงสำรวจและเชิงพรรณนา, exploratory, descriptive dossier) ตรวจสอบการตรวจย้อนถึงระดับแหล่งข้อมูลและการส่งต่อรายการที่ยังไม่ได้ข้อสรุป เชื่อม dossier ที่มีวันที่กำกับหลักฐานกับการส่งมอบงานให้ผู้ประเมินไทย/อาเซียน และเปรียบเทียบ LLM ที่รับ input น้อยที่สุด LLM ที่จับคู่หลักฐาน และแบบจำลองเชิงโครงสร้าง นี่คือการวิเคราะห์ที่วางแผนไว้ ไม่ใช่ผลการศึกษา

---

# Part E. หมายเหตุด้านหลักฐานและสถานะการตรวจสอบ

ส่วนนี้ระบุสิ่งที่ตรวจสอบแล้วและยังตรวจสอบไม่ได้ เพื่อให้ผู้อ่านชั่งน้ำหนักแต่ละการอ้างอิง เป็นส่วนของไฟล์ทำงานและตัดให้สั้นลงได้ก่อนส่ง

- **ขอบเขตของการทบทวน** ทบทวนเฉพาะแหล่งที่เราเปิดได้และเทียบกับระเบียนบรรณานุกรม บทคัดย่อ หรือฉบับเต็มได้ เป็นการระบุช่องว่างเชิงบูรณาการที่เฉพาะเจาะจง ไม่ใช่การอ้างความใหม่แบบครบถ้วน
- **แหล่งที่ตัดออก** อ้างอิงตั้งต้นจากบรีฟ 5 รายการ (หน้าเว็บของผู้ให้บริการ และรายงานของผู้ให้บริการ/อุตสาหกรรม ได้แก่ DrugPatentWatch บทความของ IQVIA หน้า loss-of-exclusivity ของ Evaluate รายงาน biosimilars ของ IQVIA Institute และ ASEAN IP Register) เปิดหรือตรวจสอบไม่ได้ จึงไม่อ้างอิง งาน IS1 ฉบับแก้ไข (paper 47) ไม่ถูกอ้างเดี่ยว ๆ อ้างเฉพาะรายการ paper 53 ในโปรแกรม iSAI-NLP [42] และถือ IS1 เป็นบริบทที่ผู้เขียนให้มา
- **ต้นฉบับ arXiv ที่ห้ามอ้าง** บรีฟระบุว่ามีต้นฉบับที่ห้ามอ้าง แต่ไม่ได้ให้ identifier จึงไม่ได้ใส่ identifier ใด ๆ และไม่พบว่าอ้างอิงตั้งต้นรายการใดเป็นต้นฉบับดังกล่าว
- **ระดับการเข้าถึงของแต่ละรายการ** อ่านฉบับเต็ม: [7] และ [35]; เปิดอ่านส่วนที่เกี่ยวข้องของเอกสาร WIPO [19], [41] เข้าถึงระดับบทคัดย่อเท่านั้น: [11], [1], [3], [4], [9], [10], [15], [17], [39] เห็นเฉพาะระเบียนบรรณานุกรม จึงไม่ระบุผลการศึกษา: [2], [13], [14], [27], [32], [36], [37] บทวิจารณ์ [18] ต้องเสียเงินจึงไม่ใช้ตัวเลขใด ๆ จากบทความนี้ ชุดข้อมูล [12] ตรวจที่ระดับ metadata และไม่ได้วิเคราะห์ไฟล์ข้อมูล
- **รายละเอียดที่แก้ไข** แก้ DOI ของ Hemphill and Sampat ([9]) และ Reiffen and Ward ([14]) หน้าสุดท้ายของ Scott Morton ([13]) ยืนยันไม่ได้ หน้าเว็บของแนวทาง FDA เรื่อง multiple endpoints [38] ไม่แสดงเดือนที่ออก (บรีฟระบุตุลาคม 2022) จึงอ้างเฉพาะปี ส่วน ForecastBench [26] อ้างเป็นระเบียน proceedings ของ ICLR 2025
- **ช่องว่างของหลักฐาน** ในแหล่งที่ตรวจสอบแล้ว มีเพียง [7] ที่เป็นการตรวจสอบแบบแบ่งเวลาไปข้างหน้า (ตามการอนุมัติที่เกิดทีหลัง) เราไม่พบงานที่ตรวจสอบแล้วซึ่งสร้างหลักฐานใหม่ ณ แต่ละ cutoff ในอดีต ข้อจำกัดนี้เป็นของการค้นแบบเจาะจงของเราเท่านั้น ไม่ได้ตรวจสอบใบอนุญาตข้อมูลของชุดข้อมูล NBER Orange Book [11] และไม่พบข้อมูลฐานที่ตรวจสอบแล้วเรื่องการขาดแคลนผู้ประเมิน FTO (P1) หรือข้อมูลระดับตัวยาของไทยด้านความต้องการ ราคา และ FTO
- **การแยกประเภทข้ออ้าง** ผลการศึกษาที่รายงานไว้ (งานในอดีต) ความสัมพันธ์เชิงพรรณนา สมมติฐานของสถานการณ์ (อัตราส่วนราคาของสหรัฐฯ) ความเห็นที่เจ้าของโครงการรายงาน (P1) และการวิเคราะห์ที่วางแผนไว้ (RQ1–RQ3, C9 ที่เป็นตัวเลือก) ถูกระบุแยกกันในเนื้อหา ไม่ใช้ตัวเลขระยะพัฒนาเป็นการยืนยัน และไม่อ้างว่า historical gate ผ่าน Track A สุกงอม C9 ถูกรัน หรือการลงทะเบียน OSF ได้รับการตรวจสอบแล้ว
- **สถานะ** เป็นการทบทวนวรรณกรรม ไม่ใช่ความเห็นทางกฎหมายหรือทางคลินิก