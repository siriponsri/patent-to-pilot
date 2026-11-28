# IS2 figure and table plan

Use the KMITL AI4BA short-paper template. Place captions below figures and above tables. Keep the numbering and data identical across editions and localize labels at layout.

## Figure 1

- **TH** รูปที่ 1 ใน IS1 ขั้นค้นคืนไม่พบเอกสารเป้าหมายที่ทราบใน 100 อันดับแรกสำหรับ 435 จาก 692 คำค้น ใน IS2 ทีมใช้หลักฐานที่เผยแพร่แล้ว ณ วันตัดข้อมูลเพื่อจัดยาเข้าเกณฑ์หนึ่งในห้าเข้าคิวส่งแฟ้มให้ผู้เชี่ยวชาญ ทีมใช้ผลที่เกิดขึ้นใน 24 เดือนสำหรับให้คะแนนเท่านั้น
- **EN** Figure 1. IS1 found no known target in the first 100 candidates for 435 of 692 queries. In IS2, the team uses evidence published by the cutoff to queue one in five eligible drug cases for specialist review. The 24-month outcomes enter scoring only.
- The main planner supplies full-width artwork at `figures/fig1_decision_{en,th}.png`. The IS1 inset counts 435 of 692 queries with no known relevant target in the first 100 candidates. The IS2 path runs from the eligible list through evidence published by the cutoff and the one-in-five queue to the specialist dossier. Place the 24-month outcome beyond the cutoff line and route it only to scoring. Section 3.1 introduces the figure. Section 3.4 anchors the float for pagination.

## Figure 2

- **TH** รูปที่ 2 ผลต่างการครอบคลุมแบบจับคู่ที่ความจุร้อยละ 20 (จุดร้อยละ ช่วงความเชื่อมั่น 95% สองด้านจากการสุ่มซ้ำระดับตัวยา) ใน C′ ผล H1 +20.37 [+14.37, +26.16] ผ่าน ส่วน H2 +1.36 [−2.20, +3.01] ไม่ผ่าน ทีมจึงหยุดทดสอบและรายงาน H3 +16.69 [+9.98, +24.21] เชิงพรรณนา ขอบล่างด้านเดียวตรงกับขอบล่างที่ระบุ ค่าประมาณ H1 และ H3 สูงกว่า +10 จุดร้อยละ เส้นอยู่ที่ศูนย์และ +10 จุดร้อยละ ชุดพัฒนามีตัวยาที่เกิดเหตุการณ์แบบไม่นับซ้ำ 67 และ 90 ตัวที่ระยะ 24 และ 12 เดือน ส่วน C′ มี 202 ตัวในแต่ละระยะ
- **EN** Figure 2. Paired recall differences at 20% capacity (pp, two-sided 95% whole-drug bootstrap CIs). C′ H1 +20.37 [+14.37, +26.16] passed. H2 +1.36 [−2.20, +3.01] failed and stopped testing. H3 +16.69 [+9.98, +24.21] is descriptive. One-sided bounds are the listed lower endpoints. H1 and H3 estimates exceed +10 pp. Lines mark zero and +10 pp. Distinct event drugs at 24 and 12 months were 67 and 90 in development and 202 each in C′.
- Place immediately after Table 1 in §4.1. Plot H1, H2 and H3 as three horizontal rows, with two vertically offset point-and-interval marks per row. Give C′ greater visual weight and distinguish development by marker shape and legend. Use a common axis in percentage points with vertical lines at zero and the prespecified +10-point practical-usefulness threshold. Label each contrast and horizon and identify the distinct event-drug counts. Mark C′ H3 as descriptive. [FREEZE development results](../../../loe-bench/receipts/FREEZE.md#development-results) · [SCORE C′ results](../../../loe-bench/receipts/SCORE.md#primary-family) · [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

| Row | Horizon | Contrast | Development event drugs | Development estimate [95% CI] (pp) | C′ event drugs | C′ estimate [95% CI] (pp) |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| H1 | 24 months | M3 − B1 | 67 | +9.80 [+0.14, +19.65] | 202 | +20.37 [+14.37, +26.16] |
| H2 | 24 months | M3 − M1 | 67 | +5.49 [−2.00, +11.25] | 202 | +1.36 [−2.20, +3.01] |
| H3 | 12 months | M3 − B1 | 90 | +13.00 [+3.27, +23.17] | 202 | +16.69 [+9.98, +24.21] |

`make_fig2.py` renders the development and C′ paired plot for both editions. It is embedded in §4.1 as `figures/fig2_effects_{en,th}.png`; event-drug counts are in the caption.

## Table 1

- **TH** ตารางที่ 1 การครอบคลุมที่ความจุคิวร้อยละ 20 ในชุดทดสอบย้อนหลัง C′
- **EN** Recall at the 20% review budget on the sealed historical test (C′).
- Rows, event rows, slots and recall for B1, M1, M3, L1 and L1e at both horizons. The cutoff schedule moved into §3.2 prose (Astra critique, 28 Nov). [SCORE](../../../loe-bench/receipts/SCORE.md) · [SCORELLM](../../../loe-bench/receipts/SCORELLM.md)

Figure 2’s caption carries the former Table 2 decisions, including the lower bounds, +10-point comparison and H2 stop rule. [SCORE](../../../loe-bench/receipts/SCORE.md#primary-family)

## Table 2

- **TH** ผลต่าง MAE ของยอดเบิกจ่ายเทียบกับการยกค่าล่าสุดในชุดย่อยขั้นพัฒนาที่เชื่อมกับคิว
- **EN** Paired reimbursement MAE differences relative to carry-forward on the linked development subset.
- Retain both reimbursement units, paired intervals and the retrospective, vintage-uncontrolled qualifier. Include B1-adjusted, M3-adjusted and drift, each relative to carry-forward. A positive difference means greater MAE. Keep the queue-linked denominators and reserved-origin NOT_RUN status next to the table. [C4b queue-linked results](../../../loe-bench/receipts/C4b.md) · [SCORE C4](../../../loe-bench/receipts/SCORE.md#c4--medicaid-demand-and-reimbursement)

Section 4.2 reports the exploratory language-model results and development contrasts in prose, with C′ recall in Table 1. Section 4.3 places the C3b development and C′ approved-applicant results together before the Medicaid analysis and Table 2. [C2 development results](../../../loe-bench/receipts/C2.md#development-results) · [C3b development result](../../../loe-bench/receipts/C3b.md#c3-development-queue-result) · [SCORE C3](../../../loe-bench/receipts/SCORE.md#c3--competition-at-launch)
