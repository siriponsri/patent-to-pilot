# REPORT2 figure requests

Design brief for the main planner. The section anchors refer to [REPORT-TH.md](REPORT-TH.md). Use the development or historical qualifier in each caption and panel. All source paths in the notes are relative to the repository root. Eleven figures retain their REPORT1 identifiers for the audit.

## Figure 1. Research timeline

**Anchor** [Introduction](REPORT-TH.md#introduction).

**Purpose** Show how the research question changed while product and evaluation work sometimes overlapped.

**Data** Use the report timeline. Mark the October G02 point (24 Oct), *กรอบวิจัยเดิม*, DAPFAM checks (5–16 Nov), BridgeRet/AM-7 and B53 (19–22 Nov), the November G02, *ระบบนำเข้าเอกสารและเชื่อมผู้ให้บริการ*, on the G01/G02 workstream before G03 and P2 (21–25 Nov), Workbench S-series (25 Nov), RA Pharma D30–D39 (26–27 Nov), D40 (27 Nov) and D41, registration and C′ (28 Nov), all in 2026. Show separate arrows for concurrent work. Put the Paper 53 conference program date, 20 Nov, on the dissemination row. Sources: `INDEX-PLAN.md`, `docs/ra-pharma/scispace-consultation/03-EXPERIMENTAL-RECORD.md`, `docs/ra-pharma/scispace-consultation/02-CURRENT-POSITION.md`, `artifacts/owner-program/PTP-2026-11-21/G02/STATUS.md`, `docs/writing/is2/IS2-SHORT-PAPER-DRAFT-EN.md`, `docs/maintenance/OWNER-DECISIONS-20261122.md`, `docs/loe-bench/HANDOFF.md`.

**Thai caption** ลำดับการเปลี่ยนคำถามจากการค้นและจัดอันดับสิทธิบัตรสู่การจัดคิวทบทวนหลักฐานสำหรับยาสามัญ โดยงานวิจัยและการพัฒนาต้นแบบบางส่วนเกิดพร้อมกัน

## Figure 2. DAPFAM exposure in IS1 / Paper 53

**Anchor** [Phase 1](REPORT-TH.md#phase-one), §2.2.

**Purpose** Explain the first-stage ceiling with a two-part flow and a proportional graphic.

**Data** Original Paper 53: 692 eligible OUT queries, 257 with at least one known OUT target in the first 100 and 435 without. Generic and patent-aware strict OUT nDCG@100 are 0.0626 and 0.0634. Show IN and OUT only as labeled paths. Use the verified OUT denominator for quantitative labels. Sources: `docs/evidence-scope/00-organization.md` original-source correction, `docs/writing/is2/mwd/SLIDES-PREP.md`.

**Thai caption** ในกลุ่มคำค้นที่มีคำตอบข้ามสาขาตามชุดอ้างอิง 435 จาก 692 คำค้นไม่มีเป้าหมายที่ทราบในเอกสารที่ระบบคัดมา 100 อันดับแรก การจัดอันดับใหม่ในรายการเดิมเรียกเป้าหมายเหล่านี้กลับมาไม่ได้

**Sentence below Figure 2** Paper 53 ใช้คำค้น OUT 692 คำค้น ส่วนการทดลอง B53 ขั้นค้นคืนใช้คำค้น OUT 905 คำค้นตามเกณฑ์ของการทดลองนั้น
<!-- src: docs/evidence-scope/00-organization.md, docs/writing/is2/results/B53-STAGE1-RESULTS.md -->

The former Figure 3 tables are in [Appendix ง](REPORT-TH.md#retrieval-tables). The F4 RRF(BM25, Arctic) Exposure@1000 is 64.3% in `docs/writing/is2/results/B53-STAGE1-RESULTS.md`. The matched instruction contrasts come from `docs/writing/is2/results/B53-STAGE2-RESULTS.md`.

## Figure 4. BridgeRet selected retrievers

**Anchor** [Phase 2](REPORT-TH.md#phase-two), §3.2.

**Purpose** Show how the frozen FT selection compares with Qwen3 zero-shot and the strongest observed baseline.

**Data** Plot the three DEV and VAL OUT Recall@200 pairs in §3.2. Use Qwen3 zero-shot 0.2741/0.2961, S2-t0.02 0.2472/0.2826 and PatEmbed zero-shot 0.3282/0.3494. Source: `docs/healthtech/research/paper1-bridgeret/ft-grid30k/sstar-grid30k.md`.

**Thai caption** ตัวค้น Qwen3 ที่เลือกหลังปรับฝึกให้ OUT Recall@200 ต่ำกว่าการใช้ Qwen3 โดยไม่ฝึกเพิ่ม ทั้งใน DEV และ VAL

## Figure 5. Why the structural acquisition arm stopped

**Anchor** [Phase 2](REPORT-TH.md#phase-two), §3.6.

**Purpose** Make the displacement mechanism legible.

**Data** 2,000 DEV applications. Complete-content fusion 0.44998, unresolved relation 0.44372, paired ALL Recall@200 difference −0.00626 [−0.00902, −0.00369]. Annotate 11 recovered and 58 displaced judged positives at rank 200. Show the older C0 A3r1 effect only in its own comparison if used. Source: `docs/tracking/owner-note-22112026/receipts/P2-T04_results.md`.

**Thai caption** วิธีค้นตามความสัมพันธ์ที่ยังขาดเพิ่มเป้าหมายที่ทราบ 11 รายการ และทำให้หลุดจากกลุ่ม 58 รายการ เมื่อเทียบกับการรวมผลค้นจากข้อความสมบูรณ์

## Figure 6. Controlled evidence reading and source admission

**Anchor** [Phase 3](REPORT-TH.md#phase-three), §§4.2–4.3.

**Purpose** Show what changed when the project moved to evidence at exact scope and edition.

**Data** Independent panels: S3 Thai coverage control 6/27 versus scope controller 3/27, difference −11.11 pp [−33.33, 0.00], with all three losses in one family; Option A 22/22 each; original fresh FDA intake 3 selected, 2 overviews, 0 exact pairs, 0 scored; D37 B1E 24/24 original labels and 22/24 usable pairs in previously viewed development groups, with one rights-related processing exception and subsequent removal. Keep the two FDA cohorts visually separate. Sources: `docs/healthtech/audits/S3-20261125/RESULTS.md`, `docs/evidence-scope/alternative-evidence/RESULTS.md`, `docs/ra-pharma/ip-pharma/EIGHT-IDEA-RESULTS.md`, `docs/ra-pharma/ip-pharma/b1e/PLANNER-REVIEW.md`.

**Thai caption** คะแนนการอ่านเอกสารในชุดควบคุมและความพร้อมของแหล่งข้อมูลยาวัดคนละขั้น กรณีที่หาเอกสารไม่ครบฉบับยังไม่เข้าสู่การให้คะแนน

## Figure 7. As-of pipeline and test boundary

**Anchor** [Phase 4](REPORT-TH.md#phase-four), §§5.2–5.5.

**Purpose** Draw what the model sees, when outcomes are joined, and how the registered queue uses limited capacity.

**Data** Approvals and GSRS establish identity and eligibility. Orange Book within six calendar months and publicly available by cutoff; PIV and timely qualifying court witnesses; ground-truth ANDA outcome strictly after cutoff. Show B1 → M1 → M3, the latter adding OPEN/BLOCKED/CONTESTED; one fifth rounded down with fractional boundary ties. Draw registration, blinded gate verdict, then scoring. Reuse components as appropriate from `docs/writing/is2/mwd/figures/fig1_flow_th.html`. Sources: `docs/loe-bench/PREREGISTRATION.md`, `docs/loe-bench/receipts/GATE.md`, `docs/loe-bench/receipts/SCORE.md`.

**Thai caption** การจัดคิวใช้หลักฐานที่มีอยู่ ณ วันตัด ส่วนผลอนุมัติภายหลังใช้ให้คะแนนหลังผ่านขั้นตรวจตามแผนที่ลงทะเบียน

## Figure 8. C′ effects

**Anchor** [Phase 4](REPORT-TH.md#phase-four), §5.6.

**Purpose** Present the fixed-sequence result with visible uncertainty.

**Data** Reuse `docs/writing/is2/mwd/figures/fig2_effects_th.svg`. Confirm H1 +20.37 [+14.37, +26.16], H2 +1.36 [−2.20, +3.01], H3 +16.69 [+9.98, +24.21] pp against `docs/loe-bench/receipts/SCORE.md`. Label H3 “เชิงพรรณนา”. Draw separate lines at 0 pp (statistical reference) and +10 pp (practical-usefulness threshold for the point estimate). If including the FREEZE values, use a separate panel and the `FREEZE.md` receipt.

**Thai caption** M3 จับเหตุการณ์ในคิวระยะ 24 เดือนได้มากกว่าฐานอายุยา การเพิ่มกราฟเทียบกับ M1 ไม่ผ่านเกณฑ์ และผลระยะ 12 เดือนรายงานเชิงพรรณนา

## Figure 9. Exploratory competition and Medicaid reimbursement

**Anchor** [Phase 4](REPORT-TH.md#phase-four), §5.7.

**Purpose** Show the C3 competition outcome and C4 scenario errors on their own scales.

**Data** Panel C3 shows M3 − B1 queue recall in percentage points with 95% intervals. DEV (2013) +25.60 [+6.25, +45.00]. C′ (2017–2023) +30.11 [+20.16, +36.86]. The outcome is at least three approved applicants within 36 months, using the fixed 24-month queue. Sources: `docs/loe-bench/receipts/C3b.md`, `docs/loe-bench/receipts/SCORE.md`.

Panel C4 shows C4b Q4 MAE differences versus carry-forward in USD per prescription for the queue-linked subset (four cutoffs, 160 matched pairs for Q4 reimbursement per prescription and 150 for annual reimbursement). Drift −172.13 [−292.12, −66.37], B1 adjustment +372.05 [+193.27, +587.26], M3 adjustment +381.24 [+203.61, +606.77]. Annotate the separate result across all seven matched periods, drift −14.08 [−50.03, +20.47] USD per prescription. The FDA ratio 0.465 came from a report published after the simulated periods. National totals are NOT_ESTIMABLE. C′ C4 is NOT_RUN. Sources: `docs/loe-bench/receipts/C4b.md`, `docs/loe-bench/receipts/SCORE.md`.

**Thai caption** คิวเดิมครอบคลุมเหตุการณ์ที่มีผู้ยื่นหลายรายเพิ่มขึ้นในผลเชิงสำรวจ ส่วนการปรับยอดเบิกจ่ายตามสถานการณ์ราคาเพิ่มความคลาดเคลื่อนในกลุ่มที่เชื่อมกับคิวได้

## Figure 10. Track A and related evidence status

**Anchor** [Phase 4](REPORT-TH.md#phase-four), §§5.9–5.10.

**Data** Track A is a prospective replication. At t0 (27 Nov 2026), the core has 651 forecasts and 130 expected queue slots per arm per horizon. As of 28 Nov, the freeze card is dispatched and the full Git tag and OSF timestamp freeze is pending. Use the literal label [สถานะ freeze: รอ]. Deadline wording is “ก่อน 31 มกราคม 2570 เวลา 23:59 UTC และก่อนดึงข้อมูลผลหลัง t0”. Neither outcome window is due. The 12-month estimate can be read at maturity (27 Nov 2027), and formal H3 waits for both 24-month steps H1 and H2 after maturity on 27 Nov 2028. Sources: `docs/loe-bench/receipts/TRACKA-CORE.md`, `docs/loe-bench/HANDOFF.md`, `docs/loe-bench/PREREGISTRATION.md`.

SFT and GRPO each completed 64 updates. The later L4 request failed for lack of stock. Label L1, L1e, C9-SFT and C9-GRPO predictions NOT_RUN for that attempt. No pod, USD 0. The C9 comparison waits for 24-month follow-up. Sources: `docs/loe-bench/receipts/C9TRAIN2.md`, `docs/loe-bench/receipts/TRACKA-GPU.md`.

P1-RSF-OPEN and P2-COX-OPEN passed technical admission, with 651 private t0 forecasts per arm per horizon. Label 24-month recall values “PRIORARMS DEV” (P1 48.35%, P2 36.26%, M3 49.45%) and the prospective comparison “PRIORARMS Track A” (pending). Sources: `docs/loe-bench/receipts/PRIORARMS.md`, `docs/loe-bench/PRIOR-ARMS-SPEC.md`.

Place the C′ supplement outside the Track A timeline. Analysis note committed at 4ee32b11. AUC and accuracy at 0.5 are NOT_RUN because the authorized runner has no export-only command. C-index is NOT_ESTIMABLE because exact event times are absent. Source: `docs/loe-bench/receipts/PRIORARMS-CPRIME-NOTE.md`.

**Thai caption** Track A สร้างคำพยากรณ์แกนแล้วและรอตรึงทั้งชุด ส่วนการพยากรณ์ด้วยแบบจำลองภาษาหยุดในรอบที่ไม่มีเครื่อง L4 ผลเทียบล่วงหน้าต้องรอให้ครบระยะติดตาม

## Figure 11. Product screens

**Anchor** [Product](REPORT-TH.md#product), §§6.1–6.2.

**Purpose** Explain the difference between the decision queue, citation inspection, outcome display and deliverable forms.

**Data** Use `product/screenshots/landing-th.png`, `app-th.png` (Moxifloxacin, 24 months, 1 Jan 2014, decision page), `app-sources-focus.png` (Bimatoprost, patent citation), `app-outcome.png` (Solifenacin outside the queue) and `desktop-window.png`. Files after the first share the same directory. Source: `docs/loe-bench/receipts/UIBUILD.md#screenshots`. Label the decision panel “Moxifloxacin”, the citation panel “Bimatoprost”, and the outcome panel “Solifenacin”. Use the visible development-data indicator and label the desktop capture as the launched executable.

**Thai caption** หน้าสาธิตแสดงคิว แฟ้มรายกรณี และต้นทางของข้อความอ้างอิง ผู้ใช้เปิดดูเหตุการณ์ย้อนหลังได้เมื่อทบทวนคำพยากรณ์แล้ว

## Figure 12. Evidence gate for the Thai and ASEAN hand-off

**Anchor** [Product](REPORT-TH.md#product), §6.3.

**Purpose** Show why a source pointer and a current national status are separate deliverables.

**Data** Display 1,789/1,789 traceable claims overall, 1,757 hash-backed; EVP 3/5 document-supported restrictions including one historical case; family leads 17/17 US grant anchors and Thai status 0/6 development cases. Use separate denominators and scopes. Annotate that official case searches did not complete and the checklist carries next actions. Sources: `docs/loe-bench/receipts/UIBUILD.md`, `docs/loe-bench/receipts/EVP.md`.

**Thai caption** การย้อนรอยข้อกล่าวอ้างและการพบเบาะแสตระกูลทำได้ตามขอบเขตนำร่อง ส่วนสถานะรายประเทศต้องตรวจจากหลักฐานไทยที่ตรงกรณี
