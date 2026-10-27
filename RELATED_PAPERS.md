# RELATED PAPERS — Patent-to-Pilot HealthTech

> Migration note, 27 October 2026: this curated library is the current HealthTech starting point. PDF links now target original publishers; no paper PDF is redistributed here. Detailed method/dataset/evaluator comparisons and direct PDF locators are in [reading notes](literature-review/healthtech/READING_NOTES.md). Release-audit counts below are source-reported pack evidence, not a locally repeated dataset audit or new retrieval result.

**ฉบับ:** 1.0 · **วันที่ตรวจและรวบรวม:** 27 ตุลาคม 2026 (Asia/Bangkok) <br>
**เอกสารร่วม:** [GOAL.md](GOAL.md) · [PLAN.md](PLAN.md) · [README.md](README.md)

## 1. แพ็กนี้มีอะไร

แพ็กนี้แนบ **27 research-paper PDFs จริง รวม 458 หน้า** พร้อม source URLs, authors, venue/year, DOI เมื่อแหล่งต้นทางระบุ, file hashes และสิทธิ์ใช้ซ้ำของบทความ ไฟล์ PDF คง bytes ต้นฉบับ ไม่มีการแก้ข้อความหรือเติม watermark

รายการนี้เป็น curated related-work collection เพื่อออกแบบโครงการ ไม่ใช่ systematic review ที่อ้างว่าค้นครบทุกงาน และไม่ใช่หลักฐานว่าได้ reproduce ผลทดลองของผู้เขียนแล้ว Notes มาจาก metadata, abstract และส่วน method/data/limitations ที่เกี่ยวข้อง โดยบันทึก reading scope รายฉบับ

ไฟล์ metadata สำหรับเครื่องอยู่ที่ [paper_manifest.json](literature-review/healthtech/paper_manifest.json) และ bibliography อยู่ที่ [references.bib](literature-review/healthtech/references.bib) งาน WPI ที่เกี่ยวข้องแต่ไม่มี PDF ที่พร้อมแนบระบุเป็น citation-only และไม่นับรวมใน 27 ฉบับ

## 2. Reading routes สำหรับ agent

เลือกตามงานปัจจุบัน ไม่ต้องอ่านทั้งชุดก่อนเริ่มทุก work package

| งานที่ agent กำลังทำ | อ่านก่อน | อ่านเพิ่มเมื่อจำเป็น |
|---|---|---|
| วาง patent task และ novelty boundary | P01 Bridge, P12 Patent survey, P13 FiNE-Patents | P08 LLM-FDA-device, P11 Predicate genealogy |
| ทำ adaptive acquisition / baseline | P14 Adaptive-RAG, P17 Cost-Aware RAG, P19 BCAS | P15 MBA-RAG, P18 HALT, P16 DRAGIN |
| ออกแบบ evaluator และ evidence checks | P02 SciFact, P20 ALCE | P21 ARES, P22 RAGAs, P25 RAGTruth |
| ทำ biomedical literature component | P06 BioASQ-QA, P04 MIRAGE | P03 NLI4CT ตาม scope |
| ขยาย Pharmaceutical | P05 ChEMU, P07 ChEMBL, P09 BindingDB, P10 SureChEMBL | P13 FiNE-Patents สำหรับ methodological comparison |
| ตรวจ iterative retrieval/long patent text | P23 IRCoT, P24 FLARE, P26 Lost in the Middle | P27 Citation rewards เมื่อจะปรับ writer |

**ขั้นต่ำก่อนอ้างว่า method ใหม่:** ตรวจ P01, P13, P14, P17, P18 และ P19 ตามประเด็นที่อ้าง Generic routing, budget-aware selection, feature decomposition และ evidence-coverage stopping มี prior art แล้ว ความใหม่ของโครงการต้องมาจาก patent-specific questions และผลที่พิสูจน์ได้

## 3. การใช้หลักฐานให้ตรง task

| Paper group | สนับสนุนอะไร | ยังไม่พิสูจน์อะไรให้โครงการนี้ |
|---|---|---|
| Device–patent / patent-analysis papers | Task definition, domain methods และ novelty boundary | ความครบถ้วนของ patents ทุกกรณีหรือผลด้านกฎหมาย |
| SciFact/BioASQ/NLI4CT/MIRAGE | Component evaluation ด้วย task/labels ที่มีอยู่ | ความถูกต้องของ dossier ทั้งฉบับหรือ commercial usefulness |
| ChEMU/chemical resources | Extraction tasks และแหล่งข้อมูลเคมี | การผลิตซ้ำ clinical efficacy หรือ manufacturing feasibility |
| Adaptive/budget/stopping papers | Controller designs และ comparison principles | ว่าวิธีเดียวกันชนะใน device–patent task แล้ว |
| Citation/evaluator papers | Attribution, faithfulness และ error diagnostics | ว่า LLM judge เป็น expert gold หรือ citation ที่เปิดได้สนับสนุนข้อสรุปเสมอ |

### ข้อที่ต้องระวังก่อน implement

- **Bridge:** released cohort/corpus และ split ต้องตรวจต่างหาก; is_valid คือ completeness ไม่ใช่ relevance; paper license ไม่ได้แก้ data-license ambiguity
- **FiNE-Patents:** เป็น prior art ที่ใกล้กับ feature–evidence retrieval แต่ cohort ไม่ใช่ benchmark ของ Medical Device โดยทั่วไป
- **DRAGIN:** วิธีเดิมต้องใช้ attention/model internals; approximation ผ่าน black-box API ต้องประกาศความต่าง
- **Cost-Aware RAG:** access-friction cost tiers เป็น proxies ไม่ใช่ actual monetary costs
- **HALT:** runtime generated targets ต้องแยกจาก gold-derived diagnostic targets; coverage ไม่ใช่ exhaustive patent search
- **ARES:** มี human calibration/evaluation data จึงไม่ควรใช้ชื่อ automated เพื่ออ้างว่าไม่ต้องมี human reference เลย
- **RAGAs:** scores ช่วยวิเคราะห์ได้ แต่ไม่แทน primary existing-label evaluator
- **ChEMU:** article permission และ noncommercial dataset terms เป็นคนละเรื่อง

## 4. รายการ PDF ทั้งหมด

| ID | ปี | งาน / บทบาท | PDF |
|---|---:|---|---|
| [P01](#p01) | 2026 | **Bridge-MedDevKG** — Core medical-device patent benchmark | [17 หน้า](https://aclanthology.org/2026.acl-long.1611.pdf) |
| [P02](#p02) | 2020 | **SciFact** — Supporting evidence-verification benchmark | [17 หน้า](https://aclanthology.org/2020.emnlp-main.609.pdf) |
| [P03](#p03) | 2023 | **NLI4CT** — Optional clinical-record evidence benchmark | [20 หน้า](https://aclanthology.org/2023.emnlp-main.1041.pdf) |
| [P04](#p04) | 2024 | **MIRAGE** — Biomedical RAG evaluation background | [19 หน้า](https://aclanthology.org/2024.findings-acl.372.pdf) |
| [P05](#p05) | 2021 | **ChEMU** — Pharmaceutical patent-extraction benchmark | [28 หน้า](https://www.frontiersin.org/journals/research-metrics-and-analytics/articles/10.3389/frma.2021.654438/pdf) |
| [P06](#p06) | 2023 | **BioASQ-QA** — Biomedical literature-retrieval benchmark | [12 หน้า](https://www.nature.com/articles/s41597-023-02068-4.pdf) |
| [P07](#p07) | 2024 | **ChEMBL** — Pharmaceutical production-data resource | [13 หน้า](https://europepmc.org/articles/PMC10767899?pdf=render) |
| [P08](#p08) | 2026 | **LLM-FDA-device** — Medical-device regulatory extraction related work | [10 หน้า](https://www.nature.com/articles/s41746-026-02353-7.pdf) |
| [P09](#p09) | 2025 | **BindingDB** — Pharmaceutical binding-evidence resource | [12 หน้า](https://www.bindingdb.org/rwd/bind/gkae1075.pdf) |
| [P10](#p10) | 2016 | **SureChEMBL** — Chemical patent-data resource | [9 หน้า](https://europepmc.org/articles/PMC4702887?pdf=render) |
| [P11](#p11) | 2021 | **Device-predicate genealogy** — Medical-device relationship and public-data background | [11 หน้า](https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0258153&type=printable) |
| [P12](#p12) | 2025 | **Patent-analysis survey** — Patent-information literature map | [17 หน้า](https://aclanthology.org/2025.acl-long.419.pdf) |
| [P13](#p13) | 2026 | **FiNE-Patents** — Fine-grained patent evidence benchmark and close prior art | [12 หน้า](https://arxiv.org/pdf/2605.02392v1) |
| [P14](#p14) | 2024 | **Adaptive-RAG** — adaptive_retrieval | [15 หน้า](https://aclanthology.org/2024.naacl-long.389.pdf) |
| [P15](#p15) | 2025 | **MBA-RAG** — adaptive_retrieval | [7 หน้า](https://aclanthology.org/2025.coling-main.218.pdf) |
| [P16](#p16) | 2024 | **DRAGIN** — adaptive_retrieval | [23 หน้า](https://aclanthology.org/2024.acl-long.702.pdf) |
| [P17](#p17) | 2026 | **Cost-Aware RAG** — budgeted_evidence | [27 หน้า](https://aclanthology.org/2026.findings-emnlp.413.pdf) |
| [P18](#p18) | 2026 | **HALT** — stopping_and_verification | [23 หน้า](https://aclanthology.org/2026.findings-emnlp.343.pdf) |
| [P19](#p19) | 2026 | **BCAS** — budgeted_evaluation | [10 หน้า](https://aclanthology.org/2026.lrec-1.808.pdf) |
| [P20](#p20) | 2023 | **ALCE** — citation_evaluation | [24 หน้า](https://aclanthology.org/2023.emnlp-main.398.pdf) |
| [P21](#p21) | 2024 | **ARES** — rag_evaluation | [17 หน้า](https://aclanthology.org/2024.naacl-long.20.pdf) |
| [P22](#p22) | 2024 | **RAGAs** — rag_evaluation | [9 หน้า](https://aclanthology.org/2024.eacl-demo.16.pdf) |
| [P23](#p23) | 2023 | **IRCoT** — iterative_retrieval | [24 หน้า](https://aclanthology.org/2023.acl-long.557.pdf) |
| [P24](#p24) | 2023 | **FLARE** — active_retrieval | [24 หน้า](https://aclanthology.org/2023.emnlp-main.495.pdf) |
| [P25](#p25) | 2024 | **RAGTruth** — hallucination_evaluation | [17 หน้า](https://aclanthology.org/2024.acl-long.585.pdf) |
| [P26](#p26) | 2024 | **Lost in the Middle** — long_context_evaluation | [17 หน้า](https://aclanthology.org/2024.tacl-1.9.pdf) |
| [P27](#p27) | 2024 | **Fine-grained citation rewards** — citation_generation | [24 หน้า](https://aclanthology.org/2024.acl-long.161.pdf) |

## 5. Notes รายฉบับ

<a id="p01"></a>

### P01 — From Regulatory Approvals to Patents: Cross-Domain Linking for Cardiovascular Device Traceability

**ผู้เขียน:** Qingqing Yang; Haijiang Liu; Moyan Li <br>
**ปี/เวที:** 2026 — ACL 2026 (Long Papers) <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2026.acl-long.1611/) · [doi:10.18653/v1/2026.acl-long.1611](https://doi.org/10.18653/v1/2026.acl-long.1611) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P01_Bridge_MedDevKG_2026.pdf](https://aclanthology.org/2026.acl-long.1611.pdf) — 17 หน้า

- **สาระที่เกี่ยวข้อง:** Introduces cardiovascular device-to-patent linking and a multi-signal candidate-generation and reranking framework. It supplies the closest public task for the proposed patent-screening research.
- **ใช้กับโครงการ:** ใช้กำหนด task หลักและ baseline ที่ใกล้ที่สุด รวมทั้งขอบเขต known device–patent associations
- **ข้อจำกัดในการอ้างผล:** ต้องแยก paper corpus จาก release 50k และกระทบยอด cohort; judgments ไม่ครบ จึงห้ามตีความ unlabeled เป็น false หรือ known recall เป็น exhaustive recall
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://aclanthology.org/2026.acl-long.1611/)
- **ข้อมูล/code/model:** Repository dataset/reuse terms require separate clarification; the paper CC BY license does not license all released data.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p02"></a>

### P02 — Fact or Fiction: Verifying Scientific Claims

**ผู้เขียน:** David Wadden; Shanchuan Lin; Kyle Lo; Lucy Lu Wang; Madeleine van Zuylen; Arman Cohan; Hannaneh Hajishirzi <br>
**ปี/เวที:** 2020 — EMNLP 2020 <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2020.emnlp-main.609/) · [doi:10.18653/v1/2020.emnlp-main.609](https://doi.org/10.18653/v1/2020.emnlp-main.609) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P02_SciFact_2020.pdf](https://aclanthology.org/2020.emnlp-main.609.pdf) — 17 หน้า

- **สาระที่เกี่ยวข้อง:** Defines scientific claim verification with evidence retrieval, support/refute judgments and rationale selection. The existing expert annotations support a component evaluation without commissioning new labels.
- **ใช้กับโครงการ:** ใช้ประเมิน evidence verifier และ rationale selection แยกจาก retrieval ของสิทธิบัตร
- **ข้อจำกัดในการอ้างผล:** ผลบน scientific claims ไม่ยืนยันว่า patent claim ครอบคลุมอุปกรณ์หรือว่า dossier ทั้งฉบับถูกต้อง
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://aclanthology.org/2020.emnlp-main.609/)
- **ข้อมูล/code/model:** SciFact annotations/claims CC BY 4.0; corpus abstracts ODC-By 1.0; code Apache 2.0, per repository LICENSE.md.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p03"></a>

### P03 — NLI4CT: Multi-Evidence Natural Language Inference for Clinical Trial Reports

**ผู้เขียน:** Mael Jullien; Marco Valentino; Hannah Frost; Paul O’Regan; Dónal Landers; Andre Freitas <br>
**ปี/เวที:** 2023 — EMNLP 2023 <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2023.emnlp-main.1041/) · [doi:10.18653/v1/2023.emnlp-main.1041](https://doi.org/10.18653/v1/2023.emnlp-main.1041) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P03_NLI4CT_2023.pdf](https://aclanthology.org/2023.emnlp-main.1041.pdf) — 20 หน้า

- **สาระที่เกี่ยวข้อง:** Provides annotated statements and clinical-trial reports for inference-relation prediction and evidence retrieval. It is relevant when the product expands to reasoning over trial records.
- **ใช้กับโครงการ:** ใช้เป็นทางขยายสำหรับ entailment/contradiction และ supporting-fact selection ใน trial records
- **ข้อจำกัดในการอ้างผล:** ขอบเขตเฉพาะและเป็น reasoning บน records ที่กำหนด ไม่ใช่ benchmark ของ open retrieval หรือคำแนะนำการรักษา
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://aclanthology.org/2023.emnlp-main.1041/)
- **ข้อมูล/code/model:** Dataset redistribution/commercial terms were not established in the prior release audit; verify independently before use.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p04"></a>

### P04 — Benchmarking Retrieval-Augmented Generation for Medicine

**ผู้เขียน:** Guangzhi Xiong; Qiao Jin; Zhiyong Lu; Aidong Zhang <br>
**ปี/เวที:** 2024 — Findings of ACL 2024 <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2024.findings-acl.372/) · [doi:10.18653/v1/2024.findings-acl.372](https://doi.org/10.18653/v1/2024.findings-acl.372) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P04_MIRAGE_2024.pdf](https://aclanthology.org/2024.findings-acl.372.pdf) — 19 หน้า

- **สาระที่เกี่ยวข้อง:** Introduces MIRAGE and the MedRAG toolkit to compare medical QA across corpora, retrievers and language models. It motivates controlled component comparisons and attention to corpus choice and context length.
- **ใช้กับโครงการ:** อ้างอิงการออกแบบ RAG experiments และการควบคุม corpus/retriever/model
- **ข้อจำกัดในการอ้างผล:** Medical QA accuracy ไม่ใช่ device–patent recovery หรือคุณภาพการคัดเทคโนโลยีเชิงธุรกิจ
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://aclanthology.org/2024.findings-acl.372/)
- **ข้อมูล/code/model:** MIRAGE combines existing QA datasets; inspect each underlying dataset license rather than inheriting the paper license.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p05"></a>

### P05 — ChEMU 2020: Natural Language Processing Methods Are Effective for Information Extraction From Chemical Patents

**ผู้เขียน:** Jiayuan He; Dat Quoc Nguyen; Saber A. Akhondi; Christian Druckenbrodt; Camilo Thorne; Ralph Hoessel; Zubair Afzal; Zenan Zhai; Biaoyan Fang; Hiyori Yoshikawa; Ameer Albahem; Lawrence Cavedon; Trevor Cohn; Timothy Baldwin; Karin Verspoor <br>
**ปี/เวที:** 2021 — Frontiers in Research Metrics and Analytics 6:654438 <br>
**ต้นทาง:** [Publication page](https://www.frontiersin.org/journals/research-metrics-and-analytics/articles/10.3389/frma.2021.654438/full) · [doi:10.3389/frma.2021.654438](https://doi.org/10.3389/frma.2021.654438) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P05_ChEMU_2020_2021.pdf](https://www.frontiersin.org/journals/research-metrics-and-analytics/articles/10.3389/frma.2021.654438/pdf) — 28 หน้า

- **สาระที่เกี่ยวข้อง:** Describes expert-annotated chemical-patent entities and reaction events, participating extraction methods and evaluation. Its discussion of leakage is useful for patent-level splits and avoiding overoptimistic extraction claims.
- **ใช้กับโครงการ:** เป็น benchmark หลักของ Pharmaceutical extraction branch เมื่อเลือก branch นี้
- **ข้อจำกัดในการอ้างผล:** การสกัด entities/events ถูกต้องไม่รับรอง process reproducibility หรือ manufacturing feasibility
- **สิทธิ์ของบทความ:** CC BY (article copyright statement); [หลักฐานสิทธิ์](https://www.frontiersin.org/journals/research-metrics-and-analytics/articles/10.3389/frma.2021.654438/full)
- **ข้อมูล/code/model:** Mendeley dataset version inspected previously states CC BY-NC 3.0; article CC BY does not override the dataset terms.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p06"></a>

### P06 — BioASQ-QA: A manually curated corpus for Biomedical Question Answering

**ผู้เขียน:** Anastasia Krithara; Anastasios Nentidis; Konstantinos Bougiatiotis; Georgios Paliouras <br>
**ปี/เวที:** 2023 — Scientific Data 10:170 <br>
**ต้นทาง:** [Publication page](https://www.nature.com/articles/s41597-023-02068-4) · [doi:10.1038/s41597-023-02068-4](https://doi.org/10.1038/s41597-023-02068-4) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P06_BioASQ_QA_2023.pdf](https://www.nature.com/articles/s41597-023-02068-4.pdf) — 12 หน้า

- **สาระที่เกี่ยวข้อง:** Documents biomedical questions with reference answers, relevant documents and snippets. It supports literature and passage-retrieval evaluation using annotations produced by the benchmark organizers.
- **ใช้กับโครงการ:** ใช้เมื่อเพิ่มการค้นบทความ biomedical; เลือก snapshot และ official task ให้ชัด
- **ข้อจำกัดในการอ้างผล:** Ideal-answer similarity ไม่เพียงพอสำหรับรับรองข้อเท็จจริงทั้ง dossier; full-text article rights ตรวจแยก
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://www.nature.com/articles/s41597-023-02068-4)
- **ข้อมูล/code/model:** Official BioASQ portal states CC BY 2.5 for challenge data; source-publication rights remain separate.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p07"></a>

### P07 — The ChEMBL Database in 2023: a drug discovery platform spanning multiple bioactivity data types and time periods

**ผู้เขียน:** Barbara Zdrazil; Eloy Felix; Fiona Hunter; Emma J. Manners; James Blackshaw; Sybilla Corbett; Marleen de Veij; Harris Ioannidis; David Mendez Lopez; Juan F. Mosquera; Maria Paula Magarinos; Nicolas Bosc; Ricardo Arcila; Tevfik Kizilören; Anna Gaulton; A. Patrícia Bento; Melissa F. Adasme; Peter Monecke; Gregory A. Landrum; Andrew R. Leach <br>
**ปี/เวที:** 2024 — Nucleic Acids Research 52(D1):D1180–D1192 <br>
**ต้นทาง:** [Publication page](https://academic.oup.com/nar/article/52/D1/D1180/7337608) · [doi:10.1093/nar/gkad1004](https://doi.org/10.1093/nar/gkad1004) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P07_ChEMBL_2024.pdf](https://europepmc.org/articles/PMC10767899?pdf=render) — 13 หน้า

- **สาระที่เกี่ยวข้อง:** Describes the ChEMBL bioactivity platform and its curated, heterogeneous data. It supports the design of a molecule–target–assay evidence adapter rather than an automatic commercialization score.
- **ใช้กับโครงการ:** ใช้วาง data model ของ assay, activity, unit, relation และ source provenance สำหรับ Pharma
- **ข้อจำกัดในการอ้างผล:** Assay activity ต้องอ่านพร้อมเงื่อนไข และไม่เท่ากับ clinical efficacy หรือ commercial feasibility
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://academic.oup.com/nar/article/52/D1/D1180/7337608)
- **ข้อมูล/code/model:** ChEMBL database is distributed under CC BY-SA 3.0; paper CC BY 4.0 is a different license.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p08"></a>

### P08 — Scaling medical device regulatory science using large language models

**ผู้เขียน:** Hanyang Li; Xiao He; Adarsh Subbaswamy; Patrick Vossler; Alexej Gossmann; Karandeep Singh; Jean Feng <br>
**ปี/เวที:** 2026 — npj Digital Medicine 9:221 <br>
**ต้นทาง:** [Publication page](https://www.nature.com/articles/s41746-026-02353-7) · [doi:10.1038/s41746-026-02353-7](https://doi.org/10.1038/s41746-026-02353-7) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P08_LLM_FDA_device_2026.pdf](https://www.nature.com/articles/s41746-026-02353-7.pdf) — 10 หน้า

- **สาระที่เกี่ยวข้อง:** Studies LLM extraction from pre- and post-market regulatory documents with expert annotations and judge-based assessment. It establishes close prior work for regulatory extraction in the proposed product.
- **ใช้กับโครงการ:** ใช้กำหนด related work และ schema ของ regulatory facts; ศึกษา modular extraction
- **ข้อจำกัดในการอ้างผล:** การเปิด raw FDA records ไม่แปลว่า expert annotation files พร้อมใช้เป็น benchmark; prior repo audit did not find all referenced gold CSVs
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://www.nature.com/articles/s41746-026-02353-7)
- **ข้อมูล/code/model:** Raw FDA source rights and annotation-release availability must be checked separately; code repository GPL-3.0.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p09"></a>

### P09 — BindingDB in 2024: a FAIR knowledgebase of protein-small molecule binding data

**ผู้เขียน:** Tiqing Liu; Linda Hwang; Stephen K. Burley; Carmen I. Nitsche; Christopher Southan; W. Patrick Walters; Michael K. Gilson <br>
**ปี/เวที:** 2025 — Nucleic Acids Research 53(D1):D1633–D1644 <br>
**ต้นทาง:** [Publication page](https://academic.oup.com/nar/article/53/D1/D1633/7906836) · [doi:10.1093/nar/gkae1075](https://doi.org/10.1093/nar/gkae1075) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P09_BindingDB_2025.pdf](https://www.bindingdb.org/rwd/bind/gkae1075.pdf) — 12 หน้า

- **สาระที่เกี่ยวข้อง:** Describes a measured protein–small-molecule affinity resource with curated literature and patent data. It supplies a potential source of assay-backed evidence for pharmaceutical dossiers.
- **ใช้กับโครงการ:** เชื่อม compound/target/measurement พร้อมเอกสารต้นทางและวันที่ เพื่อใช้ใน Pharma branch
- **ข้อจำกัดในการอ้างผล:** Binding affinity ไม่พิสูจน์ความสำเร็จทางคลินิก; imported records มีสิทธิ์ต่างตามแหล่ง
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://academic.oup.com/nar/article/53/D1/D1633/7906836)
- **ข้อมูล/code/model:** Paper describes CC BY 4.0 curation terms while website info inspected states CC BY 3.0 for staff-curated data; imported ChEMBL is BY-SA 3.0. Pin exact snapshot terms.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p10"></a>

### P10 — SureChEMBL: a large-scale, chemically annotated patent document database

**ผู้เขียน:** George Papadatos; Mark Davies; Nathan Dedman; Jon Chambers; Anna Gaulton; James Siddle; Richard Koks; Sean A. Irvine; Joe Pettersson; Nicko Goncharoff; Anne Hersey; John P. Overington <br>
**ปี/เวที:** 2016 — Nucleic Acids Research 44(D1):D1220–D1228 <br>
**ต้นทาง:** [Publication page](https://academic.oup.com/nar/article/44/D1/D1220/2503067) · [doi:10.1093/nar/gkv1253](https://doi.org/10.1093/nar/gkv1253) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P10_SureChEMBL_2016.pdf](https://europepmc.org/articles/PMC4702887?pdf=render) — 9 หน้า

- **สาระที่เกี่ยวข้อง:** Presents automated extraction and indexing of chemical structures from patent documents, linking compound records to patent text and images. It motivates chemical-entity adapters for the pharmaceutical extension.
- **ใช้กับโครงการ:** ใช้เข้าใจ compound–patent mappings และแหล่งที่มาของ chemical mentions
- **ข้อจำกัดในการอ้างผล:** Compound mention ไม่เท่ากับ claimed invention หรือ active compound; pipeline ปัจจุบันต้องอ้าง SureChEMBL 2.0 docs เพิ่ม
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://academic.oup.com/nar/article/44/D1/D1220/2503067)
- **ข้อมูล/code/model:** Current data-release terms must be checked independently; historical article and current bulk database terms are not interchangeable.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p11"></a>

### P11 — Mapping the genealogy of medical device predicates in the United States

**ผู้เขียน:** Dhruv B. Pai <br>
**ปี/เวที:** 2021 — PLOS ONE 16(10):e0258153 <br>
**ต้นทาง:** [Publication page](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0258153) · [doi:10.1371/journal.pone.0258153](https://doi.org/10.1371/journal.pone.0258153) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P11_Device_Predicate_Genealogy_2021.pdf](https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0258153&type=printable) — 11 หน้า

- **สาระที่เกี่ยวข้อง:** Uses public FDA device summaries to map predicate relationships and explore device genealogy. It provides concrete background for public-record linking and traceable regulatory context.
- **ใช้กับโครงการ:** ใช้อธิบายคุณค่าของ relationship tracing ใน Medical Device และการเก็บ predicate/source provenance
- **ข้อจำกัดในการอ้างผล:** Predicate relation เป็นคนละความสัมพันธ์กับ patent relation; text similarity ไม่ใช่คำตัดสิน substantial equivalence จากระบบเรา
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0258153)
- **ข้อมูล/code/model:** Paper points to Kaggle DOI 10.34740/kaggle/dsv/1949990; dataset access/license was not audited for this pack.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p12"></a>

### P12 — A Survey on Patent Analysis: From NLP to Multimodal AI

**ผู้เขียน:** Homaira Huda Shomee; Zhu Wang; Sathya N. Ravi; Sourav Medya <br>
**ปี/เวที:** 2025 — ACL 2025 (Long Papers) <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2025.acl-long.419/) · [doi:10.18653/v1/2025.acl-long.419](https://doi.org/10.18653/v1/2025.acl-long.419) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P12_Patent_Analysis_Survey_2025.pdf](https://aclanthology.org/2025.acl-long.419.pdf) — 17 หน้า

- **สาระที่เกี่ยวข้อง:** Organizes NLP and multimodal patent-analysis research across patent lifecycle tasks. It helps locate the project within retrieval and evidence analysis and avoid conflating those tasks with patent valuation or generation.
- **ใช้กับโครงการ:** ใช้จัด related-work taxonomy และตรวจว่าส่วนใดมีวิธีเดิมแล้ว
- **ข้อจำกัดในการอ้างผล:** Survey สนับสนุนบริบท ไม่ใช่ผลทดลองหรือหลักฐานความใหม่ของวิธีที่เสนอ
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://aclanthology.org/2025.acl-long.419/)
- **ข้อมูล/code/model:** A survey is not a dataset license or a ready evaluation corpus.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p13"></a>

### P13 — Is It Novel and Why? Fine-Grained Patent Novelty Prediction Based on Passage Retrieval

**ผู้เขียน:** Valentin Knappich; Anna Hätty; Simon Razniewski; Annemarie Friedrich <br>
**ปี/เวที:** 2026 — SIGIR 2026; bundled arXiv author version v1 <br>
**ต้นทาง:** [Publication page](https://arxiv.org/abs/2605.02392) · [doi:10.1145/3805712.3809576](https://doi.org/10.1145/3805712.3809576) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P13_FiNE_Patents_2026.pdf](https://arxiv.org/pdf/2605.02392v1) — 12 หน้า

- **สาระที่เกี่ยวข้อง:** Introduces feature-level prior-art passage retrieval and novelty reasoning grounded in European Search Opinion references. It demonstrates that feature decomposition and evidence-grounded patent workflows already have close prior work.
- **ใช้กับโครงการ:** ใช้เปรียบเทียบการจัด feature–evidence table และระวังการอ้าง novelty ของ decomposition/retrieval workflow
- **ข้อจำกัดในการอ้างผล:** Cohort มาจาก CPC G06, G10L, H04L, H04N และ first claims; ไม่ยืนยันความสามารถด้าน Medical Device โดยอัตโนมัติ
- **สิทธิ์ของบทความ:** CC BY 4.0; [หลักฐานสิทธิ์](https://arxiv.org/abs/2605.02392)
- **ข้อมูล/code/model:** Repository data/code terms must be checked separately before use; paper author version explicitly CC BY 4.0.
- **ขอบเขตการอ่าน:** First-page title/authors/abstract, relevant task/data passages and copyright statement; no experiment reproduction.

<a id="p14"></a>

### P14 — Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity

**ผู้เขียน:** Soyeong Jeong; Jinheon Baek; Sukmin Cho; Sung Ju Hwang; Jong C. Park <br>
**ปี/เวที:** 2024 — Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers) <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2024.naacl-long.389/) · [doi:10.18653/v1/2024.naacl-long.389](https://doi.org/10.18653/v1/2024.naacl-long.389) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P14_Adaptive_RAG_2024.pdf](https://aclanthology.org/2024.naacl-long.389.pdf) — 15 หน้า

- **สาระที่เกี่ยวข้อง:** ฐานการเลือกกลยุทธ์ retrieval ตามความซับซ้อนของคำถาม
- **ใช้กับโครงการ:** ใช้เป็น routing baseline หรือ prior art โดยคง retriever/reranker เดียวกันเมื่อเปรียบเทียบ policy
- **ข้อจำกัดในการอ้างผล:** ผล open-domain QA ไม่ยืนยัน device–patent linking; routing ตาม complexity มีงานแล้ว
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2024.naacl-long.389/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p15"></a>

### P15 — MBA-RAG: a Bandit Approach for Adaptive Retrieval-Augmented Generation through Question Complexity

**ผู้เขียน:** Xiaqiang Tang; Qiang Gao; Jian Li; Nan Du; Qi Li; Sihong Xie <br>
**ปี/เวที:** 2025 — Proceedings of the 31st International Conference on Computational Linguistics <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2025.coling-main.218/) · ไม่พบ DOI ใน metadata ของแหล่งที่ตรวจ; ใช้ canonical publication URL <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P15_MBA_RAG_2025.pdf](https://aclanthology.org/2025.coling-main.218.pdf) — 7 หน้า

- **สาระที่เกี่ยวข้อง:** เลือก retrieval strategy ด้วย multi-armed bandit และ reward ที่คำนึงถึงคุณภาพ/ต้นทุน
- **ใช้กับโครงการ:** ใช้เป็นฐานของ optional lightweight router; เริ่มเมื่อจำนวน independent groups รองรับ
- **ข้อจำกัดในการอ้างผล:** จำนวน retrieval steps เป็น cost proxy; ต้องคิดต้นทุนจริง และระวัง overfitting จาก labeled devices จำนวนน้อย
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2025.coling-main.218/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p16"></a>

### P16 — DRAGIN: Dynamic Retrieval Augmented Generation based on the Information Needs of Large Language Models

**ผู้เขียน:** Weihang Su; Yichen Tang; Qingyao Ai; Zhijing Wu; Yiqun Liu <br>
**ปี/เวที:** 2024 — Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2024.acl-long.702/) · [doi:10.18653/v1/2024.acl-long.702](https://doi.org/10.18653/v1/2024.acl-long.702) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P16_DRAGIN_2024.pdf](https://aclanthology.org/2024.acl-long.702.pdf) — 23 หน้า

- **สาระที่เกี่ยวข้อง:** ปรับเวลาและ query สำหรับ retrieval ด้วย uncertainty และ attention
- **ใช้กับโครงการ:** ใช้แยกคำถาม when-to-retrieve จาก what-to-query ใน ablations
- **ข้อจำกัดในการอ้างผล:** วิธีต้นฉบับต้องใช้ model internals; API ที่ไม่มี attention ไม่รองรับตรง ๆ และ approximation ต้องติดป้ายตามจริง
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2024.acl-long.702/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **Metadata note:** The ACL landing-page title includes Real-time; the PDF title omits that word. Authors/venue/pages identify the same work; the PDF title is used here.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p17"></a>

### P17 — When Knowledge Is Not Free: Cost-Aware Evidence Selection in Retrieval-Augmented Generation

**ผู้เขียน:** Mingyan Wu; Han Yang; Omer Ben-Porat; Yftah Ziser <br>
**ปี/เวที:** 2026 — Findings of the Association for Computational Linguistics: EMNLP 2026 <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2026.findings-emnlp.413/) · ไม่พบ DOI ใน metadata ของแหล่งที่ตรวจ; ใช้ canonical publication URL <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P17_Cost_Aware_Evidence_2026.pdf](https://aclanthology.org/2026.findings-emnlp.413.pdf) — 27 หน้า

- **สาระที่เกี่ยวข้อง:** ศึกษา fixed และ agentic evidence selection ภายใต้ evidence-access budget
- **ใช้กับโครงการ:** เป็นงานใกล้เคียงของ controller ที่ชั่งหลักฐานกับต้นทุน ต้องมี strong fixed/simple comparators
- **ข้อจำกัดในการอ้างผล:** Cost tiers เป็น access-friction proxies ไม่ใช่ค่า API หรือ licensing fees จริง; budget-aware selection ไม่ใช่ความใหม่โดยตัวมันเอง
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2026.findings-emnlp.413/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p18"></a>

### P18 — HALT: Verification-Aware Stopping for Retrieval-Augmented Search Agents

**ผู้เขียน:** Daeyoung Roh; Donghee Han <br>
**ปี/เวที:** 2026 — Findings of the Association for Computational Linguistics: EMNLP 2026 <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2026.findings-emnlp.343/) · ไม่พบ DOI ใน metadata ของแหล่งที่ตรวจ; ใช้ canonical publication URL <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P18_HALT_2026.pdf](https://aclanthology.org/2026.findings-emnlp.343.pdf) — 23 หน้า

- **สาระที่เกี่ยวข้อง:** ควบคุม stopping ด้วยความสัมพันธ์ระหว่าง claims กับ evidence
- **ใช้กับโครงการ:** เปรียบเทียบ coverage-aware stopping กับ fixed caps และ no-new-candidate rules
- **ข้อจำกัดในการอ้างผล:** Coverage ของคำถามที่ระบบสร้างไม่ยืนยันว่าพบ patents ทั้งหมด; gold-derived claims ใช้ได้เฉพาะ diagnostic setting ที่ประกาศ
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2026.findings-emnlp.343/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p19"></a>

### P19 — Quantifying the Accuracy and Cost Impact of Design Decisions in Budget-Constrained Agentic LLM Search

**ผู้เขียน:** Kyle A. McCleary; James M. Ghawaly <br>
**ปี/เวที:** 2026 — Proceedings of the Fifteenth Language Resources and Evaluation Conference <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2026.lrec-1.808/) · [doi:10.63317/3wfsiry9yjog](https://doi.org/10.63317/3wfsiry9yjog) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P19_BCAS_2026.pdf](https://aclanthology.org/2026.lrec-1.808.pdf) — 10 หน้า

- **สาระที่เกี่ยวข้อง:** ศึกษาผลของ search depth, retrieval strategy และ completion budget อย่างควบคุม
- **ใช้กับโครงการ:** ใช้วาง controlled experiments และ resource accounting ของ patent study
- **ข้อจำกัดในการอ้างผล:** Budget-gated harness อย่างเดียวมี prior art; ต้องมี patent-specific questions และผลที่ให้ความรู้ใหม่
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2026.lrec-1.808/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p20"></a>

### P20 — Enabling Large Language Models to Generate Text with Citations

**ผู้เขียน:** Tianyu Gao; Howard Yen; Jiatong Yu; Danqi Chen <br>
**ปี/เวที:** 2023 — Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2023.emnlp-main.398/) · [doi:10.18653/v1/2023.emnlp-main.398](https://doi.org/10.18653/v1/2023.emnlp-main.398) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P20_ALCE_Citations_2023.pdf](https://aclanthology.org/2023.emnlp-main.398.pdf) — 24 หน้า

- **สาระที่เกี่ยวข้อง:** ALCE แยกคุณภาพคำตอบกับคุณภาพ citations ใน retrieval-generation workflow
- **ใช้กับโครงการ:** ใช้กำหนด citation completeness, source support และ answer correctness คนละมิติ
- **ข้อจำกัดในการอ้างผล:** Citation เปิดได้ไม่เท่ากับ semantic support และไม่ยืนยัน clinical/legal conclusions
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2023.emnlp-main.398/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p21"></a>

### P21 — ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems

**ผู้เขียน:** Jon Saad-Falcon; Omar Khattab; Christopher Potts; Matei Zaharia <br>
**ปี/เวที:** 2024 — Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers) <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2024.naacl-long.20/) · [doi:10.18653/v1/2024.naacl-long.20](https://doi.org/10.18653/v1/2024.naacl-long.20) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P21_ARES_2024.pdf](https://aclanthology.org/2024.naacl-long.20.pdf) — 17 หน้า

- **สาระที่เกี่ยวข้อง:** ประเมิน context relevance, answer faithfulness และ answer relevance ด้วย trained judges/PP inference
- **ใช้กับโครงการ:** ใช้ศึกษาข้อกำหนดของ evaluator และเทียบกับ existing-label strategy ของโครงการ
- **ข้อจำกัดในการอ้างผล:** ARES มี human-annotated calibration/evaluation data; ห้ามอธิบายว่าไม่ต้องมี human ground truth เลย
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2024.naacl-long.20/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p22"></a>

### P22 — RAGAs: Automated Evaluation of Retrieval Augmented Generation

**ผู้เขียน:** Shahul Es; Jithin James; Luis Espinosa Anke; Steven Schockaert <br>
**ปี/เวที:** 2024 — Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics: System Demonstrations <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2024.eacl-demo.16/) · [doi:10.18653/v1/2024.eacl-demo.16](https://doi.org/10.18653/v1/2024.eacl-demo.16) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P22_RAGAs_2024.pdf](https://aclanthology.org/2024.eacl-demo.16.pdf) — 9 หน้า

- **สาระที่เกี่ยวข้อง:** เสนอ component-oriented automated evaluation สำหรับ RAG
- **ใช้กับโครงการ:** ใช้ diagnostic signals ช่วยหา failure ร่วมกับ primary dataset-based metrics
- **ข้อจำกัดในการอ้างผล:** LLM-based scores ขึ้นกับ evaluator model และไม่กลายเป็น expert gold ของ Medical Device โดยอัตโนมัติ
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2024.eacl-demo.16/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p23"></a>

### P23 — Interleaving Retrieval with Chain-of-Thought Reasoning for Knowledge-Intensive Multi-Step Questions

**ผู้เขียน:** Harsh Trivedi; Niranjan Balasubramanian; Tushar Khot; Ashish Sabharwal <br>
**ปี/เวที:** 2023 — Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2023.acl-long.557/) · [doi:10.18653/v1/2023.acl-long.557](https://doi.org/10.18653/v1/2023.acl-long.557) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P23_IRCoT_2023.pdf](https://aclanthology.org/2023.acl-long.557.pdf) — 24 หน้า

- **สาระที่เกี่ยวข้อง:** สลับ retrieval กับ intermediate reasoning สำหรับ multi-step questions
- **ใช้กับโครงการ:** ใช้เป็นพื้นฐานของ fixed iterative retrieval และวิเคราะห์ว่า iteration ช่วยเพียงใด
- **ข้อจำกัดในการอ้างผล:** Reasoning ที่สร้างขึ้นเป็นข้อเสนอจากโมเดล ต้องตรวจหลักฐาน; task ต่างจาก device–patent recovery
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2023.acl-long.557/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p24"></a>

### P24 — Active Retrieval Augmented Generation

**ผู้เขียน:** Zhengbao Jiang; Frank F. Xu; Luyu Gao; Zhiqing Sun; Qian Liu; Jane Dwivedi-Yu; Yiming Yang; Jamie Callan; Graham Neubig <br>
**ปี/เวที:** 2023 — Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2023.emnlp-main.495/) · [doi:10.18653/v1/2023.emnlp-main.495](https://doi.org/10.18653/v1/2023.emnlp-main.495) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P24_FLARE_2023.pdf](https://aclanthology.org/2023.emnlp-main.495.pdf) — 24 หน้า

- **สาระที่เกี่ยวข้อง:** ใช้ anticipated content และ low-confidence signals เพื่อกระตุ้น retrieval ระหว่าง generation
- **ใช้กับโครงการ:** ใช้วาง prior art สำหรับ active retrieval และ query reformulation
- **ข้อจำกัดในการอ้างผล:** ผล long-form QA ไม่ยืนยัน patent association recovery; confidence signal อาจต้องพึ่ง model access
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2023.emnlp-main.495/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p25"></a>

### P25 — RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models

**ผู้เขียน:** Cheng Niu; Yuanhao Wu; Juno Zhu; Siliang Xu; KaShun Shum; Randy Zhong; Juntong Song; Tong Zhang <br>
**ปี/เวที:** 2024 — Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2024.acl-long.585/) · [doi:10.18653/v1/2024.acl-long.585](https://doi.org/10.18653/v1/2024.acl-long.585) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P25_RAGTruth_2024.pdf](https://aclanthology.org/2024.acl-long.585.pdf) — 17 หน้า

- **สาระที่เกี่ยวข้อง:** มี annotations ของ hallucinations ใน RAG responses
- **ใช้กับโครงการ:** ใช้ศึกษา error taxonomy หรือ optional hallucination component evaluation
- **ข้อจำกัดในการอ้างผล:** ไม่แปลงคะแนนเป็นความถูกต้องด้านการแพทย์หรือกฎหมายสิทธิบัตร; ตรวจ dataset terms แยกจาก paper
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2024.acl-long.585/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p26"></a>

### P26 — Lost in the Middle: How Language Models Use Long Contexts

**ผู้เขียน:** Nelson F. Liu; Kevin Lin; John Hewitt; Ashwin Paranjape; Michele Bevilacqua; Fabio Petroni; Percy Liang <br>
**ปี/เวที:** 2024 — Transactions of the Association for Computational Linguistics <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2024.tacl-1.9/) · [doi:10.1162/tacl_a_00638](https://doi.org/10.1162/tacl_a_00638) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P26_Lost_In_The_Middle_2024.pdf](https://aclanthology.org/2024.tacl-1.9.pdf) — 17 หน้า

- **สาระที่เกี่ยวข้อง:** ศึกษาผลของตำแหน่งข้อมูลสำคัญใน long context
- **ใช้กับโครงการ:** ใช้วาง chunking, evidence ordering และ long-document sensitivity checks
- **ข้อจำกัดในการอ้างผล:** ผลขึ้นกับ models/tasks ที่ทดลอง; ต้องวัด input construction และโมเดลของโครงการเอง
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2024.tacl-1.9/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

<a id="p27"></a>

### P27 — Training Language Models to Generate Text with Citations via Fine-grained Rewards

**ผู้เขียน:** Chengyu Huang; Zeqiu Wu; Yushi Hu; Wenya Wang <br>
**ปี/เวที:** 2024 — Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) <br>
**ต้นทาง:** [Publication page](https://aclanthology.org/2024.acl-long.161/) · [doi:10.18653/v1/2024.acl-long.161](https://doi.org/10.18653/v1/2024.acl-long.161) <br>
**PDF ต้นทาง (ไฟล์ใน pack ตรวจ hash แล้ว; ไม่แนบใน public repo):** [P27_Fine_Grained_Citation_Rewards_2024.pdf](https://aclanthology.org/2024.acl-long.161.pdf) — 24 หน้า

- **สาระที่เกี่ยวข้อง:** ศึกษาการฝึก generation ด้วย rewards สำหรับ citation quality ระดับละเอียด
- **ใช้กับโครงการ:** เป็นทางเลือกพัฒนา writer ในอนาคตหลัง core workflow มีประโยชน์แล้ว
- **ข้อจำกัดในการอ้างผล:** การฝึก citation model ไม่จำเป็นสำหรับ MVP; generation metrics อย่างเดียวไม่ยืนยัน dossier usefulness
- **สิทธิ์ของบทความ:** CC BY 4.0 (ACL Anthology post-2016 publication notice); [หลักฐานสิทธิ์](https://aclanthology.org/2024.acl-long.161/)
- **ข้อมูล/code/model:** Paper license is not a license for its data, code, model weights or third-party content.
- **ขอบเขตการอ่าน:** Primary landing-page abstract and metadata, PDF title/abstract, and targeted method/limitation text; not a reproduced experiment.

## 6. Citation-only ที่เกี่ยวข้องกับ World Patent Information

### C01 — Poce & Cerro (2026)

**A survey on automated and AI-based tools for patent retrieval with a special focus on the life sciences domain.** World Patent Information. DOI: [10.1016/j.wpi.2026.102439](https://doi.org/10.1016/j.wpi.2026.102439)

- [Publisher record](https://www.sciencedirect.com/science/article/pii/S0172219026000141)
- [Author-institution record](https://iris.unimol.it/handle/11695/156812)
- **ใช้กับโครงการ:** สนับสนุน domain relevance และบริบทปัญหาการค้นสิทธิบัตร life sciences
- **ข้อจำกัด:** การมีงานในวารสารนี้ไม่ยืนยัน novelty หรือ acceptance ของโครงการใหม่
- **สถานะ PDF:** ไม่แนบ; ไม่มีการใช้ paywall workaround และไม่นับเป็นหนึ่งใน 27 PDFs

## 7. Official data references สำหรับ implementation

แหล่งด้านล่างเป็น data/service references ไม่ใช่ research papers ที่นำมานับเพิ่ม

| Source | Official reference | ใช้กับงาน |
|---|---|---|
| Bridge-MedDevKG release | [Repository](https://github.com/myqqhub/Bridge-MedDevKG) | Audit/cohort/main conditional retrieval task |
| SciFact | [Repository and terms](https://github.com/allenai/scifact) | Existing-label evidence benchmark |
| FDA PMA | [openFDA](https://open.fda.gov/apis/device/pma/) | Product/application facts |
| FDA 510(k) | [openFDA](https://open.fda.gov/apis/device/510k/) | Device clearance records |
| openFDA terms | [License](https://open.fda.gov/license/) | Source/field-specific reuse, including GMDN exception |
| Orange Book | [Data files](https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files) | Product–patent/exclusivity records |
| Purple Book | [Downloads](https://purplebooksearch.fda.gov/downloads) | Real snapshot changes; U/N/R meanings must be preserved |
| ChEMU dataset | [Mendeley Data](https://data.mendeley.com/datasets/wy6745bjfj/1) | Chemical-patent benchmark; CC BY-NC 3.0 dataset terms |
| BioASQ | [Official datasets](https://participants-area.bioasq.org/datasets/) / [archival snapshot](https://zenodo.org/records/7655130) | Biomedical document/snippet tasks |
| PMC Open Access | [Official guide](https://pmc.ncbi.nlm.nih.gov/tools/openftlist/) | Full text under per-article terms |
| SureChEMBL current access | [SureChEMBL 2.0](https://www.ebi.ac.uk/about/news/updates-from-data-resources/surechembl-2-0-is-here/) | Current snapshots; historical paper is not current API documentation |
| Open Targets | [License](https://platform-docs.opentargets.org/licence) | Target/disease evidence and upstream terms |

Paper issue years are retained: ChEMBL is cited as 2024, BindingDB as 2025, and SureChEMBL as 2016 even though their titles/online dates refer to an earlier year.

## 8. Attribution, verification และการใช้ซ้ำ

1. ไฟล์ PDF เป็นผลงานของผู้เขียนและ publisher ที่ระบุ ไม่ใช่บทความที่สร้างขึ้นใหม่โดยโครงการนี้
2. PDF ในแพ็กคง bytes ต้นฉบับ และตรวจ signature, readability, page count, first-page title และ SHA256 แล้ว
3. ผู้เขียน ชื่อบทความ แหล่งต้นทาง และ license evidence ระบุรายฉบับ ให้รักษาข้อมูล attribution เหล่านี้เมื่อส่งต่อ
4. Paper license ไม่ให้สิทธิ์ใน datasets, code, model weights หรือ third-party content ทุกส่วนโดยอัตโนมัติ
5. ชุดนี้ไม่รวม raw benchmark datasets หรือข้อมูลภายในองค์กร
6. ไม่ต้องเพิ่มงานอ่านทุก paper เป็น global prerequisite ของทุก work package ให้เปิดอ่านตาม decision ที่จะทำ

ใช้ [pack provenance](docs/healthtech/pack-provenance.json) และ [paper manifest](literature-review/healthtech/paper_manifest.json) ตรวจรายการ/hash/size ของต้นทาง CHECKSUMS.sha256 และ PACK_MANIFEST.json ต้นฉบับยังอยู่ใน input pack ซึ่งไม่ได้แก้ไข
