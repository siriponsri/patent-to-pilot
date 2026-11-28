# IS2 figure and table plan

Use the KMITL AI4BA short-paper template. Place captions below figures and above tables. Keep the numbering and data identical across editions and localize labels at layout.

## Figure 1

- **TH** รูปที่ 1 ณ วันตัดข้อมูลแต่ละปี แต่ละวิธีจัดลำดับรายการยาจากข้อมูลที่เผยแพร่แล้ว โดยเลือกทบทวนได้ ⌊N/5⌋ รายการ และแบ่งน้ำหนักเมื่อคะแนนเสมอตรงขอบลำดับ การอนุมัติขั้นสุดท้ายครั้งแรกที่พบในช่วง 12 หรือ 24 เดือนถัดมาใช้คำนวณสัดส่วนรายการที่เกิดเหตุการณ์ซึ่งได้รับเลือกให้ทบทวน
- **EN** Figure 1. At each annual cutoff, each method ranks eligible drug cases using records available by that date. Review capacity is ⌊N/5⌋, with fractional allocation at boundary ties. First final approvals observed over the next 12 or 24 months are used to calculate recall.
- The main planner supplies the full-width timeline at `figures/fig1_timeline_{en,th}.png`. At 6.5 × 1.95 in, the single panel places records available by t0 before the cutoff, ranks N eligible cases into ⌊N/5⌋ review places with fractional boundary ties, and routes selected cases to the dated dossier and checklist. The outcome window (t0, t0+h] feeds recall only. Section 3.1 introduces the figure. Anchor the float at the start of §3.4 to place it near §3.3 in the rendered paper.

## Figure 2

- **TH** รูปที่ 2 ผลต่างการครอบคลุมแบบจับคู่เมื่อกำหนดจำนวนรายการที่ทบทวนไว้ที่ร้อยละ 20 (จุดร้อยละ ช่วงความเชื่อมั่น 95% สองด้านจากการสุ่มซ้ำระดับตัวยา) ใน C′ ผล H1 ผ่าน ลำดับการทดสอบสิ้นสุดที่ H2 และรายงาน H3 เชิงพรรณนา เส้นแนวตั้งระบุศูนย์และเกณฑ์ประโยชน์เชิงปฏิบัติที่กำหนดล่วงหน้า (+10 จุดร้อยละ)
- **EN** Figure 2. Paired recall differences at 20% review capacity (pp, two-sided 95% whole-drug bootstrap CIs). In C′, H1 passed, the sequence stopped at H2, and H3 is descriptive. Vertical lines mark zero and the prespecified usefulness threshold (+10 pp).
- Place after Table 1 in §4.1 at 3.0 × 2.70 in. Plot two vertically offset point-and-interval marks for each contrast and horizon. Distinguish development by marker shape and legend and give C′ greater visual weight. On the common percentage-point axis, mark zero and the prespecified usefulness threshold at +10 pp. Use the row labels “H1 passed”, “Sequence stopped at H2” and “H3 descriptive” or the Thai equivalents “H1 ผ่าน”, “ลำดับการทดสอบสิ้นสุดที่ H2” and “H3 เชิงพรรณนา”. [FREEZE development results](../../../loe-bench/receipts/FREEZE.md#development-results) · [SCORE C′ results](../../../loe-bench/receipts/SCORE.md#primary-family) · [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

| Row | Horizon | Contrast | Development event drugs | Development estimate [95% CI] (pp) | C′ event drugs | C′ estimate [95% CI] (pp) |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| H1 | 24 months | M3 − B1 | 67 | +9.80 [+0.14, +19.65] | 202 | +20.37 [+14.37, +26.16] |
| H2 | 24 months | M3 − M1 | 67 | +5.49 [−2.00, +11.25] | 202 | +1.36 [−2.20, +3.01] |
| H3 | 12 months | M3 − B1 | 90 | +13.00 [+3.27, +23.17] | 202 | +16.69 [+9.98, +24.21] |

The main planner updates the development and C′ paired plot for both editions. It is embedded in §4.1 as `figures/fig2_effects_{en,th}.png`; event-drug counts are in §4.1.

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
