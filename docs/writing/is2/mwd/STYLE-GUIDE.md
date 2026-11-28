# IS2 formal style guide (28 November 2026)

This guide was agreed by the main planner and the co-planner (GPT-6.2 Astra high, with SciSpace and web search) after the owner asked for formal, professional language, professional titles and academic figures. It overrides the storytelling choices made earlier: the question-form title and the conversational opening.

## Title (owner choice: option 1)

- TH: **การประเมินหลักฐานด้านการกำกับดูแลยาเพื่อจัดลำดับการทบทวนรายการยาก่อนการอนุมัติยาสามัญครั้งแรกในสหรัฐอเมริกา**
- EN: **Evaluating Regulatory Evidence for Prioritizing Drug Reviews Ahead of First US Generic Approvals**

The title follows the IS1 form ("Diagnosing Near-Zero Instruction Effects in Cross-Domain Patent Reranking"): an analytic verb, then the object of study, then the context. The Thai title is a noun phrase, the usual form for Thai research titles. The abstract defines the event at first use: the first final approval of an original ANDA.

**Evidence.** In PLOS journals, question titles drew more downloads but fewer citations (Jamali & Nikzad 2011, doi:10.1007/s11192-011-0412-z). Paiva et al. 2012 (PMC3351256) report a small negative association between title length and citations. Letchford et al. 2015 (PMC4555861) and Fox & Burns 2015 (doi:10.1002/ece3.1480) report field-dependent findings. IEEE asks for specific, concise, descriptive titles that use the reader's search terms. All of this evidence is observational, so these are external guidelines, not measured effects for this paper.

## Register rules (English and Thai)

- **Use precise verbs.** Use *ranked, estimated, resampled, compared* and "จัดลำดับ ประมาณค่า สุ่มซ้ำ เปรียบเทียบ". Do not use *suppose*, *on the desk* or "ลอง", "ขึ้นโต๊ะ", "ทีม…ได้", second person or rhetorical questions in the body.
- **Name the actor for each action.** Use *we* or "ผู้วิจัย" when the researchers chose something, "แบบจำลอง" or *the method* for computation, and "ผู้เชี่ยวชาญ" or *specialist* for legal review. Never let "ทีม" stand for all three.
- **Keep the same term for the same unit.** Use *recall*, *event case* and "รายการยา ณ วันตัดข้อมูล". Do not rotate synonyms to look varied. Keep official names in full, such as **State Drug Utilization Data**.
- **Keep effect sizes, CIs and test status.** For H2 write *did not establish an incremental gain*; mark H3 *descriptive*. Keep scope words: *historical*, *matched subset*, *unknown*.
- **Keep the IS1 continuity to two formal sentences:** the earlier result with its denominator, then the statement that IS2 studies the selection question for drug cases. Then go straight to the IS2 objective.
- **State the 20% review budget as an experimental specification**, not a fact about staffing.
- **RQs.** Use the heading "Research objectives / วัตถุประสงค์การวิจัย", keep the codes RQ1–RQ3, and write each objective in the same grammatical form.
- **Delete the drug-team lines.** Remove the one-sentence "meaning for a drug team" lines where they repeat the result. Keep the implications in formal form only where the reader interprets use: the auto-clear limitation and the Thai status checks.
- **Apply both slop skills in formal mode.**
  - no-ai-slop: banned words, no binary contrasts, no colon reveals, no puffery or metadiscourse, no summary-recap ending, no decorative em dashes.
  - zero-slop: `python -I .agents/skills/zero-slop/scripts/slopscore.py --formal`, the performed-register pass, and `--fidelity original revised` for facts.
  - Conflicts are resolved toward formal academic register. Conversational "voice" features are not added. The AI-use acknowledgment stays verbatim.

## Sentence rewrites (use in the same position in both editions)

| # | Location | English | Thai |
|---|---|---|---|
| 1 | Abstract, first sentence | The evaluation limited review to one fifth of eligible drug cases at each annual cutoff, rounded down to a whole number of cases. | การประเมินกำหนดให้ทบทวนได้หนึ่งในห้าของรายการยาที่เข้าเกณฑ์ ณ วันตัดข้อมูลแต่ละปี โดยปัดจำนวนรายการลงเป็นจำนวนเต็ม |
| 2 | Introduction, opening | In an earlier study of cross-domain patent reranking [n], no known relevant document appeared among the first 100 candidates for 435 of 692 queries. | การศึกษาก่อนหน้าเรื่องการจัดอันดับเอกสารสิทธิบัตรข้ามสาขา [n] พบว่า สำหรับคำค้น 435 จาก 692 รายการ เอกสาร 100 อันดับแรกไม่มีเอกสารที่ทราบว่าเกี่ยวข้อง |
| 3 | Introduction | The present study examines how to select drug cases for review when the number of available places is fixed. | การศึกษาครั้งนี้จึงพิจารณาวิธีเลือกรายการยาเพื่อทบทวนเมื่อกำหนดจำนวนรายการที่ทบทวนได้ไว้ล่วงหน้า |
| 4 | End of introduction | We compared the proportion of subsequent first final US generic approval cases captured by rankings based on records available at each cutoff. | ผู้วิจัยเปรียบเทียบว่าวิธีจัดลำดับจากข้อมูลที่มี ณ วันตัดข้อมูลแต่ละปีครอบคลุมรายการที่ต่อมามีการอนุมัติยาสามัญขั้นสุดท้ายครั้งแรกในสหรัฐอเมริกาเป็นสัดส่วนเท่าใด |
| 5 | RQ1 | RQ1 compared recall at fixed review capacity for M3 versus drug age (B1) and for M3 versus dated tabular evidence (M1), in the preregistered sequence. | RQ1 เปรียบเทียบสัดส่วนรายการที่เกิดเหตุการณ์ซึ่งได้รับเลือกให้ทบทวน เมื่อกำหนดจำนวนรายการที่ทบทวนเท่ากัน โดยเปรียบเทียบ M3 กับวิธีตามอายุยา (B1) และวิธีที่ใช้ตารางหลักฐาน ณ วันตัดข้อมูล (M1) ตามลำดับที่ลงทะเบียนไว้ |
| 6 | RQ2 | RQ2 comprised three exploratory analyses: recall under a 7B language model given the same upstream evidence, capture of cases with at least three approved applicants within 36 months, and reimbursement forecast error after applying a price factor. | RQ2 ประกอบด้วยการวิเคราะห์เชิงสำรวจสามเรื่อง ได้แก่ การครอบคลุมของแบบจำลองภาษา 7B เมื่อได้รับหลักฐานต้นทางชุดเดียวกัน การครอบคลุมรายการที่มีผู้ยื่นคำขอได้รับอนุมัติอย่างน้อยสามรายภายใน 36 เดือน และความคลาดเคลื่อนของค่าพยากรณ์ยอดเบิกจ่ายหลังใช้ตัวคูณราคา |
| 7 | RQ3 | RQ3 assessed which dossier claims could be traced to a dated source and which required further specialist verification. | RQ3 ประเมินว่าข้อความใดในแฟ้มสืบถึงแหล่งข้อมูลที่ระบุวันที่ได้ และข้อความใดยังต้องให้ผู้เชี่ยวชาญตรวจสอบเพิ่มเติม |
| 8 | H1 result | At equal review capacity, M3 captured 66.85% of the 368 event cases at 24 months, compared with 46.48% for B1. | เมื่อกำหนดจำนวนรายการที่ทบทวนเท่ากัน M3 ครอบคลุมร้อยละ 66.85 ของรายการที่เกิดเหตุการณ์ภายใน 24 เดือนทั้งหมด 368 รายการ เทียบกับร้อยละ 46.48 สำหรับ B1 |
| 9 | H2 result | Adding graph states to M1 changed 24-month recall by +1.36 percentage points (95% CI −2.20 to +3.01). The preregistered sequence stopped at H2. | เมื่อเพิ่มสถานะกราฟใน M1 ผลต่างการครอบคลุมที่ 24 เดือนเท่ากับ +1.36 จุดร้อยละ (ช่วงความเชื่อมั่น 95% −2.20 ถึง +3.01) การทดสอบตามลำดับที่ลงทะเบียนไว้สิ้นสุดที่ H2 |
| 10 | Use and safety | The historical results support prioritization for review. The automatic clearance rule failed the prespecified safety criterion for M3 at both horizons. Cases outside the queue therefore remain eligible for routine review. | ผลย้อนหลังสนับสนุนการใช้วิธีนี้จัดลำดับรายการที่จะทบทวน กฎยกเว้นการทบทวนโดยอัตโนมัติของ M3 ไม่ผ่านเกณฑ์ความปลอดภัยที่กำหนดไว้ทั้งสองระยะ รายการนอกลำดับที่เลือกจึงยังอยู่ในขอบเขตการทบทวนตามปกติ |
| 11 | Competition | The number of approved applicants provides an indicator of potential competition. Estimating the number of producers that marketed a product would require sales data. | จำนวนผู้ยื่นคำขอที่ได้รับอนุมัติเป็นตัวบ่งชี้การแข่งขันที่อาจเกิดขึ้น การประมาณจำนวนผู้ผลิตที่วางจำหน่ายยาจริงต้องใช้ข้อมูลการจำหน่าย |
| 12 | Price | Applying the 0.465 factor increased mean absolute error for both Medicaid reimbursement measures in the retrospectively matched subset. | ในชุดย่อยที่จับคู่ข้อมูลย้อนหลัง การใช้ตัวคูณ 0.465 เพิ่มค่าคลาดเคลื่อนสัมบูรณ์เฉลี่ยของการพยากรณ์ยอดเบิกจ่าย Medicaid ทั้งสองตัวชี้วัด |

Read rows 2–4 together as the new opening paragraph. Where a table or an earlier sentence already gives the values in rows 8 and 9, replace the old wording rather than repeating the numbers.

## Figures (Claude redraws)

- **Figure 1** becomes a single-panel time schematic in matplotlib, full width, 6.5 × 1.95 in. It shows the cutoff t0, the horizon end t0+h, the records published by t0, the ranking of N eligible cases into k = floor(N/5), a branch to the dated dossier and checklist, and the outcome window (t0, t0+h] feeding recall only. It has no IS1 panel, no glyphs, no rounded cards and no narrative labels.
  - EN caption: "At each annual cutoff, each method ranks eligible drug cases using records available by that date. Review capacity is ⌊N/5⌋, with fractional allocation at boundary ties. First final approvals observed over the next 12 or 24 months are used to calculate recall."
  - TH caption: "ณ วันตัดข้อมูลแต่ละปี แต่ละวิธีจัดลำดับรายการยาจากข้อมูลที่เผยแพร่แล้ว โดยเลือกทบทวนได้ ⌊N/5⌋ รายการ และแบ่งน้ำหนักเมื่อคะแนนเสมอตรงขอบลำดับ การอนุมัติขั้นสุดท้ายครั้งแรกที่พบในช่วง 12 หรือ 24 เดือนถัดมาใช้คำนวณสัดส่วนรายการที่เกิดเหตุการณ์ซึ่งได้รับเลือกให้ทบทวน"
  - Place it near §3.1–3.3.
- **Figure 2** keeps the paired-difference plot, one column, 3.0 × 2.70 in.
  - Row labels read "H1 passed", "Sequence stopped at H2" and "H3 descriptive" (or the Thai equivalents).
  - The +10 line is the *prespecified usefulness threshold* / "เกณฑ์ประโยชน์เชิงปฏิบัติที่กำหนดล่วงหน้า", explained in the caption.
  - Do not repeat all six numbers in the image, the caption and the text.
- **Production.**
  - Fonts: Arial 7.5–8 pt for English and TH Sarabun New for Thai (×1.4).
  - Colours and lines: ink #1F1F1F, secondary #6E6E6E, accent #0072B2, axes 0.6 pt, CIs 1.2–1.5 pt.
  - Formats: PDF/SVG vector plus a PNG at 600 dpi at final size.
  - Embedding: the Word PDF had downsampled images to about 200 ppi, so set no-compression in the docx and re-check the embedded resolution.
  - Sources: Rougier et al. 2014 (journal.pcbi.1003833), Tufte, Schneeweiss et al. 2019 (PMID 30856654, design diagrams for database studies), Weissgerber et al. 2015, and the Nature, IEEE and Elsevier artwork guides.

## Other must-fixes

- §3.5 in the English edition must define the reimbursement measures as the Thai edition does: the fourth-quarter reimbursement per prescription and the annual total over the next four quarters.
- Results headings name the metric, for example "Recall at fixed review capacity / การครอบคลุมเมื่อกำหนดจำนวนรายการที่ทบทวน".
- Separate the forecast reference date (27 Nov 2026) from the date the package was generated and timestamped.
- Track A status sentences wait for the freeze receipt. Keep the target at 9 pages, with 10 as the hard maximum.
