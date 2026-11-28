# REPORT1 figure requests

Design brief for the main planner. The section anchors refer to [REPORT-TH.md](REPORT-TH.md). Use the development or historical qualifier in each caption and panel. All source paths in the notes are relative to the repository root.

## Figure 1. Research timeline

**Anchor** [Introduction](REPORT-TH.md#introduction).

**Purpose** Show how the research question changed while product and evaluation work sometimes overlapped.

**Data** Use the report timeline. Mark the early G02 point (24 Oct), DAPFAM checks (5–16 Nov), BridgeRet/AM-7 and B53 (19–22 Nov), G03 and P2 (21–25 Nov), Workbench S-series (25 Nov), RA Pharma D30–D39 (26–27 Nov), D40 (27 Nov) and D41, registration and C′ (28 Nov), all in 2026. Show separate arrows for concurrent work. Put the Paper 53 conference program date, 20 Nov, on the dissemination row. Sources: `INDEX-PLAN.md`, `docs/ra-pharma/scispace-consultation/03-EXPERIMENTAL-RECORD.md`, `docs/writing/is2/IS2-SHORT-PAPER-DRAFT-EN.md`, `docs/maintenance/OWNER-DECISIONS-20261122.md`, `docs/loe-bench/HANDOFF.md`.

**Thai caption** ลำดับการเปลี่ยนคำถามจากการค้นและจัดอันดับสิทธิบัตรสู่การจัดคิวทบทวนหลักฐานสำหรับยาสามัญ โดยงานวิจัยและการพัฒนาต้นแบบบางส่วนเกิดพร้อมกัน

## Figure 2. DAPFAM exposure in IS1 / Paper 53

**Anchor** [Phase 1](REPORT-TH.md#phase-one), §2.2.

**Purpose** Explain the first-stage ceiling with a two-part flow and a proportional graphic.

**Data** Original Paper 53: 692 eligible OUT queries, 257 with at least one known OUT target in the first 100 and 435 without. Generic and patent-aware strict OUT nDCG@100 are 0.0626 and 0.0634. Show IN and OUT only as labeled paths. Use the verified OUT denominator for quantitative labels. Sources: `docs/evidence-scope/00-organization.md` original-source correction, `docs/writing/is2/mwd/SLIDES-PREP.md`.

**Thai caption** ในกลุ่มคำค้นที่มีคำตอบข้ามสาขาตามชุดอ้างอิง 435 จาก 692 คำค้นไม่มีเป้าหมายที่ทราบในผู้สมัคร 100 อันดับแรก การจัดอันดับใหม่ในรายการเดิมเรียกเป้าหมายเหล่านี้กลับมาไม่ได้

## Figure 3. B53 exposure and instruction contrasts

**Anchor** [Phase 1](REPORT-TH.md#phase-one), §2.3.

**Purpose** Show the first-stage comparison alongside the matched instruction question.

**Data** Stage 1 OUT n = 905. F0/F1/F2/F3/F4 exposure at 100 ranks = 37.1/26.6/37.6/31.7/33.6%, at 200 = 47.1/34.4/46.9/41.9/43.1%, at 1,000 = 73.3/54.8/70.1/63.2/64.7%. Stage 2 common-exposed n = 153. Use the ten point estimates and intervals in the Stage 2 primary table. Label the stages separately. Sources: `docs/writing/is2/results/B53-STAGE1-RESULTS.md`, `docs/writing/is2/results/B53-STAGE2-RESULTS.md`.

**Thai caption** ความลึกและชนิดของตัวค้นมีผลต่อการปรากฏของเป้าหมาย ส่วนผลต่างของคำสั่งบนคำค้นที่ทุกตัวค้นพบเป้าหมายมีขนาดเล็ก

## Figure 4. BridgeRet retriever fine-tune grid

**Anchor** [Phase 2](REPORT-TH.md#phase-two), §3.2.

**Purpose** Show how the frozen FT selection compares with Qwen3 zero-shot and the strongest observed baseline.

**Data** Plot DEV and VAL OUT Recall@200 in §3.2 or use the full grid table. Emphasize Qwen3 zero-shot 0.2741/0.2961, S2-t0.02 0.2472/0.2826 and PatEmbed zero-shot 0.3282/0.3494. Source: `docs/healthtech/research/paper1-bridgeret/ft-grid30k/sstar-grid30k.md`.

**Thai caption** ตัวค้น Qwen3 ที่เลือกหลังปรับฝึกให้ OUT Recall@200 ต่ำกว่าการใช้ Qwen3 โดยไม่ฝึกเพิ่ม ทั้งใน DEV และ VAL

## Figure 5. Why the structural acquisition arm stopped

**Anchor** [Phase 2](REPORT-TH.md#phase-two), §3.6.

**Purpose** Make the displacement mechanism legible.

**Data** 2,000 DEV applications. Complete-content fusion 0.44998, unresolved relation 0.44372, paired ALL Recall@200 difference −0.00626 [−0.00902, −0.00369]. Annotate 11 recovered and 58 displaced judged positives at rank 200. Show the older C0 A3r1 effect only in its own comparison if used. Source: `docs/tracking/owner-note-22112026/receipts/P2-T04_results.md`.

**Thai caption** วิธีค้นตามความสัมพันธ์ที่ยังขาดเพิ่มเป้าหมายที่ทราบ 11 รายการ และทำให้หลุดจากกลุ่ม 58 รายการ เมื่อเทียบกับการรวมผลค้นจากข้อความสมบูรณ์

## Figure 6. Controlled evidence reading and source admission

**Anchor** [Phase 3](REPORT-TH.md#phase-three), §§4.2–4.3.

**Purpose** Show what changed when the project moved to evidence at exact scope and edition.

**Data** Independent panels: S3 Thai coverage control 6/27 versus scope controller 3/27; Option A 22/22 each; original fresh FDA intake 3 selected, 2 overviews, 0 exact pairs, 0 scored; D37 B1E 24/24 original labels and 22/24 usable pairs. Keep the two FDA cohorts visually separate. Sources: `docs/healthtech/audits/S3-20261125/RESULTS.md`, `docs/evidence-scope/alternative-evidence/RESULTS.md`, `docs/ra-pharma/ip-pharma/EIGHT-IDEA-RESULTS.md`, `docs/ra-pharma/ip-pharma/b1e/PLANNER-REVIEW.md`.

**Thai caption** คะแนนการอ่านเอกสารในชุดควบคุมและความพร้อมของแหล่งข้อมูลยาวัดคนละขั้น กรณีที่หาเอกสารไม่ครบฉบับยังไม่เข้าสู่การให้คะแนน

## Figure 7. As-of pipeline and test boundary

**Anchor** [Phase 4](REPORT-TH.md#phase-four), §§5.2–5.5.

**Purpose** Draw what the model sees, when outcomes are joined, and how the registered queue uses limited capacity.

**Data** Approvals and GSRS establish identity and eligibility. Orange Book within six calendar months and publicly available by cutoff; PIV and timely qualifying court witnesses; ground-truth ANDA outcome strictly after cutoff. Show B1 → M1 → M3, the latter adding OPEN/BLOCKED/CONTESTED; one fifth rounded down with fractional boundary ties. Draw registration, blinded gate verdict, then scoring. Reuse components as appropriate from `docs/writing/is2/mwd/figures/fig1_flow_th.html`. Sources: `docs/loe-bench/PREREGISTRATION.md`, `docs/loe-bench/receipts/GATE.md`, `docs/loe-bench/receipts/SCORE.md`.

**Thai caption** การจัดคิวใช้หลักฐานที่มีอยู่ ณ วันตัด ส่วนผลอนุมัติภายหลังใช้ให้คะแนนหลังผ่านขั้นตรวจตามแผนที่ลงทะเบียน

## Figure 8. C′ effects

**Anchor** [Phase 4](REPORT-TH.md#phase-four), §5.6.

**Purpose** Present the fixed-sequence result with visible uncertainty.

**Data** Reuse `docs/writing/is2/mwd/figures/fig2_effects_th.svg`. Confirm H1 +20.37 [+14.37, +26.16], H2 +1.36 [−2.20, +3.01], H3 +16.69 [+9.98, +24.21] pp against `docs/loe-bench/receipts/SCORE.md`. Label H3 descriptive and mark the +10 pp usefulness threshold separately from 0. If including the FREEZE values, use a separate panel and the `FREEZE.md` receipt.

**Thai caption** M3 จับเหตุการณ์ในคิวระยะ 24 เดือนได้มากกว่าฐานอายุยา การเพิ่มกราฟเทียบกับ M1 ไม่ผ่านเกณฑ์ และผลระยะ 12 เดือนรายงานเชิงพรรณนา

## Figure 9. Exploratory market and language-model results

**Anchor** [Phase 4](REPORT-TH.md#phase-four), §§5.7–5.8.

**Purpose** Give exploratory results a visible place without merging unlike endpoints.

**Data** Separate panels: C3 DEV +25.60 pp [6.25, 45.00] and C′ +30.11 pp [20.16, 36.86]; C4b Q4 MAE change versus carry-forward −172.13 for drift, +372.05 for B1 adjustment, +381.24 for M3 adjustment in USD per prescription. The C′ C4 field reads NOT_RUN. For L1 and L1e display the four-arm recall values in the report, with facets by cohort and horizon. Sources: `docs/loe-bench/receipts/C3b.md`, `docs/loe-bench/receipts/C4b.md`, `docs/loe-bench/receipts/C2.md`, `docs/loe-bench/receipts/SCORE.md`, `docs/loe-bench/receipts/SCORELLM.md`.

**Thai caption** คิวเดิมจับเหตุการณ์ผู้ยื่นหลายรายได้เพิ่มขึ้นในผลเชิงสำรวจ ขณะที่การปรับยอดเบิกจ่ายตามสถานการณ์ราคาเพิ่มความคลาดเคลื่อน และแบบจำลองภาษาที่ทดสอบจับเหตุการณ์หลักได้น้อยกว่าวิธีตารางและกราฟ

## Figure 10. Track A and the pending results

**Anchor** [Phase 4](REPORT-TH.md#phase-four), §§5.9–5.10.

**Purpose** Distinguish prepared predictions, training completion, pending freeze and unobserved outcomes.

**Data** t0 27 Nov 2026; 651 core forecasts and 130 expected slots per arm per horizon; planned freeze by 31 Jan 2027 23:59 UTC and before outcome access; outcomes mature 27 Nov 2027 and 27 Nov 2028. C9 training complete 64/64 updates for each arm, predictions and scoring pending. P1-RSF-OPEN and P2-COX-OPEN spec locked, results pending. Place the C′ AUC plan outside the Track A time arrow. Sources: `docs/loe-bench/receipts/TRACKA-CORE.md`, `docs/loe-bench/receipts/C9TRAIN2.md`, `docs/loe-bench/PRIOR-ARMS-SPEC.md`, `docs/loe-bench/PREREGISTRATION.md`.

**Thai caption** Track A เตรียมคำพยากรณ์แกนแล้วและยังรอการตรึงชุด ผลของแบบจำลองที่ฝึกเพิ่มและวิธีคู่เทียบจะอ่านได้เมื่อมีคำพยากรณ์ที่ตรึงและผลตามระยะติดตาม

## Figure 11. Product screens

**Anchor** [Product](REPORT-TH.md#product), §§6.1–6.2.

**Purpose** Explain the difference between the decision queue, citation inspection, outcome display and deliverable forms.

**Data** Use `product/screenshots/landing-th.png`, `app-th.png` (Moxifloxacin, 24 months, 1 Jan 2014, decision page), `app-sources-focus.png` (Bimatoprost, patent citation), `app-outcome.png` (Solifenacin outside the queue) and `desktop-window.png`. Files after the first share the same directory. Source: `docs/loe-bench/receipts/UIBUILD.md#screenshots`. Use the visible development-data indicator and label the desktop capture as the launched executable.

**Thai caption** หน้าสาธิตแสดงคิว แฟ้มรายกรณี และต้นทางของข้อความอ้างอิง ผู้ใช้เปิดดูเหตุการณ์ย้อนหลังได้เมื่อทบทวนคำพยากรณ์แล้ว

## Figure 12. Evidence gate for the Thai and ASEAN hand-off

**Anchor** [Product](REPORT-TH.md#product), §6.3.

**Purpose** Show why a source pointer and a current national status are separate deliverables.

**Data** Display 1,789/1,789 traceable claims overall, 1,757 hash-backed; EVP 3/5 document-supported restrictions including one historical case; family leads 17/17 US grant anchors and Thai status 0/6 development cases. Use separate denominators and scopes. Annotate that official case searches did not complete and the checklist carries next actions. Sources: `docs/loe-bench/receipts/UIBUILD.md`, `docs/loe-bench/receipts/EVP.md`.

**Thai caption** การย้อนรอยข้อกล่าวอ้างและการพบเบาะแสตระกูลทำได้ตามขอบเขตนำร่อง ส่วนสถานะรายประเทศต้องตรวจจากหลักฐานไทยที่ตรงกรณี
