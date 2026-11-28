# IS2 figure and table plan

Use the KMITL AI4BA short-paper template. Place captions below figures and above tables. Keep the numbering and data identical across editions and localize labels at layout.

## Figure 1

- **TH** ขั้นตอนการจัดทำแฟ้มที่ออกแบบไว้สำหรับผู้เชี่ยวชาญ ประเมินชุดพัฒนาและให้คะแนนชุดทดสอบย้อนหลัง C′ แล้ว ส่วนการตรึงคำพยากรณ์ไปข้างหน้าของ Track A และการตรวจหลักฐานรายข้อความในแฟ้มยังรอดำเนินการ ผลด้านความต้องการและราคาเป็นสถานการณ์จำลอง
- **EN** Proposed dossier workflow for specialist review. Development evaluation and historical C′ scoring are complete. The prospective Track A prediction freeze and the dossier’s claim-level audit are pending. Demand and price are scenario outputs.
- Place at the layout marker in §3.1. Update the artwork's status labels and accessible description for the completed C′ scoring before embedding it. Preserve the Track A freeze deadline and scenario labels. Use full width if needed for legibility. [Existing system flow](../../../assets/market-window-flow.svg) · [D41 product specification](../../../loe-bench/PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026) · [SCORE](../../../loe-bench/receipts/SCORE.md)

## Figure 2

- **TH** ผลต่างการครอบคลุมการอนุมัติครั้งแรกแบบจับคู่ในชุดพัฒนาและ C′ ที่ความจุคิวร้อยละ 20 จุดแสดงค่าประมาณ เส้นช่วงแสดงช่วงความเชื่อมั่น 95% สองด้านจากการสุ่มซ้ำระดับตัวยา เส้นแนวตั้งอยู่ที่ศูนย์และ +10 จุดร้อยละ ป้ายกำกับระบุจำนวนตัวยาที่เกิดเหตุการณ์แบบไม่นับซ้ำ ช่วงของ H3 ใน C′ ใช้อธิบายผลเชิงพรรณนา
- **EN** Paired differences in first-approval recall at the 20% review budget on development data and C′. Points show estimates and bars show two-sided 95% whole-drug bootstrap intervals. Vertical lines mark zero and +10 percentage points. Labels give distinct event-drug counts. The C′ H3 interval is descriptive.
- Place at the layout marker in §4.1. Plot H1, H2 and H3 as three horizontal rows, with two vertically offset point-and-interval marks per row. Distinguish development and C′ by marker shape and legend. Use a common linear axis in percentage points, with distinct vertical lines at zero and the prespecified +10-point practical-usefulness threshold. Label each contrast and horizon and identify the distinct event-drug count for each panel. Mark the C′ H3 estimate and interval as descriptive. [FREEZE development results](../../../loe-bench/receipts/FREEZE.md#development-results) · [SCORE C′ results](../../../loe-bench/receipts/SCORE.md#primary-family) · [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

| Row | Horizon | Contrast | Development event drugs | Development estimate [95% CI] (pp) | C′ event drugs | C′ estimate [95% CI] (pp) |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| H1 | 24 months | M3 − B1 | 67 | +9.80 [+0.14, +19.65] | 202 | +20.37 [+14.37, +26.16] |
| H2 | 24 months | M3 − M1 | 67 | +5.49 [−2.00, +11.25] | 202 | +1.36 [−2.20, +3.01] |
| H3 | 12 months | M3 − B1 | 90 | +13.00 [+3.27, +23.17] | 202 | +16.69 [+9.98, +24.21] |

The main planner renders the paired plot for both editions. The checked-in Figure 2 assets depict development results and need to be regenerated before layout.

## Table 1

- **TH** ปีของวันตัดข้อมูลสำหรับแต่ละระยะพยากรณ์
- **EN** Annual cutoff schedule by horizon.
- Use the training, development and sealed-cutoff columns. Report the C′ admission verdict in §4.1. [FREEZE](../../../loe-bench/receipts/FREEZE.md) · [Preregistration splits](../../../loe-bench/PREREGISTRATION.md#splits-and-blinded-admission) · [GATE](../../../loe-bench/receipts/GATE.md)

## Table 2

- **TH** ผลต่างการครอบคลุมแบบจับคู่ใน C′ ที่ความจุคิวร้อยละ 20 และผลการทดสอบตามลำดับ
- **EN** C′ paired recall differences at the 20% review budget and fixed-sequence decisions.
- Use the §4.1 table with the point estimates, two-sided intervals, one-sided lower bounds, reached-step decisions and +10-point checks. Mark H3 descriptive. [SCORE](../../../loe-bench/receipts/SCORE.md#primary-family)

## Table 3

- **TH** ผลต่าง MAE ของยอดเบิกจ่ายเทียบกับการยกค่าล่าสุดในชุดย่อยขั้นพัฒนาที่เชื่อมกับคิว
- **EN** Paired reimbursement MAE differences relative to carry-forward on the linked development subset.
- Retain both reimbursement units, paired intervals and the retrospective, vintage-uncontrolled qualifier. Include B1-adjusted, M3-adjusted and drift, each relative to carry-forward. A positive difference means greater MAE. Keep the queue-linked denominators and reserved-origin NOT_RUN status next to the table. [C4b queue-linked results](../../../loe-bench/receipts/C4b.md) · [SCORE C4](../../../loe-bench/receipts/SCORE.md#c4--medicaid-demand-and-reimbursement)

## Table 4

- **TH** ผลขั้นพัฒนาของแบบจำลองภาษาที่ได้รับหลักฐานและวิธีเปรียบเทียบ
- **EN** Evidence-matched language model and comparator results on development data.
- Present native recall, precision and grouped average precision. Keep paired recall contrasts, intervals and the exploratory status in the adjacent text. [C2 development results](../../../loe-bench/receipts/C2.md#development-results)

Keep the C3b single-cutoff development result and the exploratory C′ C3 estimates in adjacent paragraphs in §4.2. [C3b development result](../../../loe-bench/receipts/C3b.md#c3-development-queue-result) · [SCORE C3](../../../loe-bench/receipts/SCORE.md#c3--competition-at-launch)
