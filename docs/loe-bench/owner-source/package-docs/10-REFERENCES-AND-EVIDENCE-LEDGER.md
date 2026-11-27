# 10 — References & Evidence Ledger

**ข้อควรทราบ**: รายการต่อไปนี้พบจากการค้นฐานวรรณกรรมและยืนยันว่า DOI อยู่ในผลการค้นจริง แต่ผมอ่านได้ระดับ **abstract เท่านั้น** (ไม่ได้อ่านฉบับเต็ม และไม่ได้ดึงชื่อผู้แต่ง) ก่อนอ้างอิงในต้นฉบับ ต้องเปิดอ่านฉบับเต็มและเติมผู้แต่งเอง

## Paper 53
Srihangpiboon S, Ploysuwan T. "Diagnosing Near-Zero Instruction Effects in Cross-Domain Patent Reranking." KMITL. **[venue/DOI: TODO]**

## Generic entry timing
- "Drug patent expirations and the speed of generic entry." Health Services Research, 1997. (ไม่มี DOI)
- "Approximating future generic entry for new drugs." J Law Med Ethics, 2019. doi:10.1177/1073110519840499
- "A method for approximating future entry of generic drugs." Value in Health, 2018. doi:10.1016/J.JVAL.2018.04.1827
- "Predictive analysis of first ANDA submission for NCEs based on machine learning…" Clin Pharmacol Ther, 2019. doi:10.1002/CPT.1479
- "Comparing Onset of Biosimilar Versus Generic Competition in the United States." Clin Pharmacol Ther, 2020. doi:10.1002/CPT.1981
- "Effective Market Exclusivity of NMEs for Rare and Non-rare Diseases." Pharmaceutical Medicine, 2020. doi:10.1007/S40290-019-00317-9
- "Market Exclusivity of the Originator Drugs in South Korea." Front Public Health, 2021. doi:10.3389/FPUBH.2021.654952
- "Estimating Costs of Market Exclusivity Extensions For 4 Top-Selling Prescription Drugs in the US." JAMA Health Forum, 2025. doi:10.1001/jamahealthforum.2025.2631

## Biosimilars / patent thickets
- "Biological patent thickets and delayed access to biosimilars, an American problem." J Law and the Biosciences, 2022. doi:10.1093/jlb/lsac022
- "Patent Litigation and the Timing of Entry by Biologic Biosimilars Compared to Small Molecule Generics in the US, 2015–20." J Health Polit Policy Law, 2026. doi:10.1215/03616878-12513812
- "The Divisional Game…" IIC, 2022. doi:10.1007/s40319-022-01225-3
- "Unveiling the Patent Landscape of Biologic Drugs." SSRN, 2026. doi:10.2139/ssrn.6314139
- "The dual barriers to biosimilar competition: US patent thickets and EU SPCs." J Generic Medicines, 2026. doi:10.1177/17411343261422538

## Forecast accuracy
- "Pharmaceutical forecasting: throwing darts?" Nat Rev Drug Discov, 2013. doi:10.1038/NRD4127
- "Systematic bias in predictions of new drugs' budget impact." Curr Med Res Opin, 2018. doi:10.1080/03007995.2017.1320276
- "Blockbuster drugs and forecast accuracy: sponsor type…" Drug Discovery Today, 2026. doi:10.1016/j.drudis.2026.104832 (490 NMEs/biologics 2016–2025; analysts overestimate, especially for biotech sponsors)
- "Rare disease benchmarks…" Drug Discovery Today, 2026. doi:10.1016/j.drudis.2026.104792
- "Assessing the Accuracy of Sales Forecasts… Austria." Front Pharmacol, 2021. doi:10.3389/FPHAR.2021.726758
- "Analyzing Upward Deviation of Actual vs Predicted Drug Sales in Japan." doi:10.1007/s43441-019-00086-2

## LLM + patent/FTO + abstention
- TriageRAG. Systems, 2026. doi:10.3390/systems14091160
- ACE. arXiv doi:10.48550/arxiv.2604.04295
- "Intelligent System for Automated Molecular Patent Infringement Assessment." arXiv doi:10.48550/arxiv.2412.07819
- "Uncertainty-Aware Abstention in LLMs with Provable Alignment Guarantees." arXiv doi:10.48550/arxiv.2607.04430
- "Asymptotic Risk Calibration for Selective QA." arXiv doi:10.48550/arxiv.2608.12008
- ช่องว่างที่สังเกต: ไม่พบงานที่รวม LLM + FTO/infringement + selective prediction (จากการค้นของผม ไม่ใช่การรับประกันว่าไม่มี)

## แหล่งข้อมูล/คู่แข่ง
- openFDA: https://api.fda.gov/drug/orangebook.json, https://api.fda.gov/drug/drugsfda.json
- ClinicalTrials.gov API v2: https://clinicaltrials.gov/api/v2/studies
- Purple Book: https://purplebooksearch.fda.gov/index.cfm?event=downloads
- Orange Book data files: https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files
- DrugPatentWatch: https://www.drugpatentwatch.com/ ; softwarefinder (แหล่งรอง): https://softwarefinder.com/legal/drugpatentwatch
- repo ของโครงการ: https://github.com/siriponsri/patent-to-pilot
