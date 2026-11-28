# IS2 figure and table plan

Use the KMITL AI4BA short-paper template. Place captions below figures and above tables. Keep the numbering and data identical across editions and localize labels at layout.

## Figure 1

- **TH:** ขั้นตอนการจัดทำแฟ้มที่ออกแบบไว้สำหรับผู้เชี่ยวชาญ ประเมินย้อนหลังในขั้นพัฒนาแล้ว ส่วนการตรวจรับและให้คะแนน C′ การตรึงคำพยากรณ์ Track A และการตรวจหลักฐานรายข้อความในแฟ้มยังรอดำเนินการ ผลด้านความต้องการและราคาเป็นสถานการณ์จำลอง
- **EN:** Proposed dossier workflow for specialist review. Historical development evaluation is complete. Sealed C′ admission and scoring, the Track A prediction freeze and the dossier’s claim-level audit are pending. Demand and price are scenario outputs.
- Place in §3.1 before the explanation of the source trail. Reuse the corrected SVG and preserve its pending-test, freeze-deadline and scenario wording in translated labels and accessible descriptions. Use full width if needed for legibility. [System flow](../../../assets/market-window-flow.svg) · [D41 product specification](../../../loe-bench/PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026)

## Figure 2

- **TH:** ผลต่างการครอบคลุมการอนุมัติครั้งแรกแบบจับคู่ในชุดพัฒนา ที่ความจุคิวร้อยละ 20 จุดแสดงค่าประมาณ เส้นช่วงแสดงช่วงความเชื่อมั่น 95% แบบสองด้านจากการสุ่มซ้ำระดับตัวยา เส้นแนวตั้งแสดงเกณฑ์ศูนย์และ +10 จุดร้อยละ ป้ายแต่ละแถวแสดงจำนวนตัวยาที่เกิดเหตุการณ์แบบไม่นับซ้ำ
- **EN:** Paired differences in first-approval recall at the 20% review budget on development data. Points are estimates, bars are two-sided 95% whole-drug bootstrap intervals, and vertical lines mark zero and +10 percentage points. Labels give the number of distinct event drugs.
- Place at the marker in §4.1. Plot three horizontal interval rows in H1, H2, H3 order from top to bottom. Use a common linear axis in percentage points, with a vertical line at zero and a distinct vertical line at +10 for the prespecified practical-usefulness threshold. Center each point on its estimate and plot the supplied lower and upper endpoints. Include the horizon, contrast and distinct event-drug count in each row label. The counts are development denominators. [FREEZE development results](../../../loe-bench/receipts/FREEZE.md#development-results) · [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

| Row | Horizon | Contrast | Distinct event drugs | Point estimate (pp) | 95% lower (pp) | 95% upper (pp) |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| H1 | 24 months | M3 v1 − B1 | 67 | +9.80 | +0.14 | +19.65 |
| H2 | 24 months | M3 v1 − M1 | 67 | +5.49 | −2.00 | +11.25 |
| H3 | 12 months | M3 v1 − B1 | 90 | +13.00 | +3.27 | +23.17 |

The main planner renders this plot for both editions. The methods describe the release and follow-up timeline in §3.4.

## Table 1

- **TH:** ปีของวันตัดข้อมูลสำหรับแต่ละระยะพยากรณ์
- **EN:** Annual cutoff schedule by horizon.
- Use the training, development and sealed-cutoff columns. Presented years are scheduled cutoffs. Keep the pending admission verdict in Results. [FREEZE](../../../loe-bench/receipts/FREEZE.md) · [Preregistration splits](../../../loe-bench/PREREGISTRATION.md#splits-and-blinded-admission)

## Table 2

- **TH:** ผลต่าง MAE ของยอดเบิกจ่ายเทียบกับการยกค่าล่าสุดในชุดย่อยขั้นพัฒนาที่เชื่อมกับคิว
- **EN:** Paired reimbursement MAE differences relative to carry-forward on the linked development subset.
- Retain both reimbursement units, paired intervals and the retrospective, vintage-uncontrolled qualifier. Include B1-adjusted, M3-adjusted and drift, each relative to carry-forward. A positive difference means greater MAE. Keep the queue-linked denominators next to the table. [C4b queue-linked results](../../../loe-bench/receipts/C4b.md)

## Table 3

- **TH:** ผลขั้นพัฒนาของแบบจำลองภาษาที่ได้รับหลักฐานและวิธีเปรียบเทียบ
- **EN:** Evidence-matched language model and comparator results on development data.
- Present native recall, precision and grouped average precision. Keep paired recall contrasts, intervals and the exploratory status in the adjacent text. [C2 development results](../../../loe-bench/receipts/C2.md#development-results)

The C3b result stays in §4.2 with its single-cutoff scope, fractional-tie counts and paired interval. [C3b development result](../../../loe-bench/receipts/C3b.md#c3-development-queue-result)
