# Patent-to-Pilot — ข้อเสนอ long run รุ่น 3

**วันที่:** 27 ตุลาคม 2026
**สถานะ:** PROPOSAL_READY_FOR_OWNER_REVIEW — อนุมัติทิศทางแล้ว แต่ **ยังไม่อนุมัติงบเกิน USD 5**
**Product vision:** Capability-Constrained Cross-Domain Technology Transfer
**Paper แรก:** *Transfer or Retest? Calibrated Knowledge Transfer and Experimental Design under Capability Shift*

## 1. ข้อเสนอสำหรับเจ้าของ

เดินสองสายที่เชื่อมกัน แต่ไม่ใช้ความสำเร็จของสายหนึ่งแทนหลักฐานอีกสาย

- **ผลิตภัณฑ์:** ช่วยผู้ประกอบการและนักลงทุนพิจารณาว่าองค์ความรู้จากแหล่งหนึ่งใช้กับเงื่อนไขของตนได้แค่ไหน มีข้อขัดแย้งอะไร และควรตรวจอะไรต่อ R&D เป็นเครื่องยนต์เบื้องหลัง ไม่ใช่ระบบซื้อขายลงทุนหรือบริษัทผลิตยาอัตโนมัติ
- **งานวิจัยแรก:** เริ่มจาก measured solvent/material หรือ operating-regime shift ที่นิยามได้และมีผลวัดจริง ถามว่าเมื่อไรควรถ่ายโอนความรู้ เมื่อไรควรซื้อข้อมูล target เพิ่ม และเมื่อไรหลักฐานยังไม่พอ ยังไม่ศึกษา broad factory scale-up
- **งบ:** เสนอ LEAN รวม $25 หรือ **แนะนำรวม $50** โดยรวม $5 ที่อนุมัติแล้ว ไม่ใช่ $50 เพิ่ม งบนี้เป็น model API cap ของทั้ง campaign ไม่ใช่คำรับรองว่าพอทำ paper จนตีพิมพ์
- **ลำดับ:** ตรวจ novelty/rights/grouped split → offline feasibility → baseline/policy calibration → frozen evaluation → error analysis/reproducibility → manuscript ส่วน UI ให้ Claude ทำ branch แยกจาก mock contracts

การใช้เวลานานไม่ใช่เหตุผลให้ใช้เงินเพิ่ม หากข้อมูลหรือสมมติฐานไม่ผ่าน ให้จบด้วยผลลบ/INCONCLUSIVE หรือหยุดเฉพาะ branch ที่ไม่ช่วย
รอบจัดทำ proposal นี้ไม่มี model calls, training, dependency installation หรือ deploy

### ความน่าสนใจที่พิสูจน์ได้ กับสิ่งที่ยังเป็นความหวัง

**Engineering ที่มีหลักฐานแล้ว:** source/version traceability, revision history, schema/identity/accounting guards และ clean-checkout regression เป็นพื้นฐานที่ตรวจได้ แต่ dashboard, จำนวน agents หรือ 142 tests ไม่ใช่ research novelty

**Research ที่อาจมีคุณค่า:** เมื่อ solvent หรือ regime เปลี่ยน ระบบกล้าบอกว่าไม่ควรถ่ายโอน และเลือกซื้อ target evidence เฉพาะจุดได้คุ้มกว่า strong classical transfer methods ภายใต้งบเดียวกัน นี่ต้องวัดจริง หากชนะเพียง chat-only/random baseline แต่แพ้ well-tuned GP หรือ robust two-phase transfer ก็ยังไม่พออ้าง methodological advance

**Vision ระยะยาว:** ส่งต่อองค์ความรู้ข้ามบริบทที่ capabilities ต่างกัน พร้อมคำอธิบายและ experimental evidence ยังเป็นวิสัยทัศน์ ไม่ได้พิสูจน์ cross-industry invention จาก solvent benchmark เดียว
ไม่ทราบ rubric หรือความคาดหวังของอาจารย์ผู้สอน CNW จึงไม่ทำนายว่าอาจารย์จะเห็นว่าว้าวหรือธรรมดา เกณฑ์ที่เสนอคือ reproducible challenge, strong comparators, uncertainty ที่น่าเชื่อถือ และความรู้ใหม่ที่ยังมีคุณค่าแม้ผลเป็นลบ

เจ้าของกำลังพิจารณาคุณค่าก่อนอนุมัติ long run ข้อเสนอ $50 จึงเป็น headroom option หลัง novelty/data gates ไม่ใช่คำแนะนำให้เติมเงินหรือเริ่มรันทันที

## 2. สิ่งที่เปลี่ยน และสิ่งที่เก็บไว้

ทิศทางใหม่ได้รับอนุมัติจากข้อความเจ้าของ “ปรับให้ตามข้อเสนอใหม่ได้เลย” ส่วน “เสนอ budget ... ก่อน long run” เป็นคำขอข้อเสนอ ไม่ใช่การอนุมัติ $25/$50
ผู้ใช้เป้าหมายยังเป็น entrepreneur/investor ตาม requirements v2; ผู้ใช้ benchmark อาจเป็นนักวิจัยเทคนิค ไม่จำเป็นต้องเป็นกลุ่มเดียวกัน

| หลักฐานเดิม | ใช้ต่ออย่างไร | ห้ามตีความเป็น |
|---|---|---|
| Published `4adcdf3`, clean-clone 142 tests ผ่าน | engineering foundation: typed records, provenance, revision, mock transport/accounting และ reproducibility | หลักฐาน transfer accuracy หรือ scientific pilot |
| PTP-0001..3 authored cases | regression/traceability fixtures | independent held-out scientific cases |
| SYN-* 48 dev/demo cases | UI/stress tests และ failure controls | 48 independent material campaigns หรือ real business outcomes |
| B0–B4/P, G09/G10/G11 historical evidence | รักษาเป็น research/engineering history | เปลี่ยน labels ย้อนหลังให้เป็น transfer benchmark |
| V2 API/cost plan | อ้างอิงกลไก guard ที่ตรวจแล้ว | แผน executable สำหรับ paper ใหม่โดยอัตโนมัติ |

ไม่ renumber G01–G22 ไม่แก้ frozen evaluation, accepted G11 adaptation, historical paid journals หรือ `docs/research/pilot-next/`
ประวัติค่าใช้จ่ายเดิม $0.0001464 แสดงแยกตาม receipt เดิม ไม่ย้าย/ลบเพื่อให้ได้ quota ใหม่ ไม่มีการตรวจ account หรืออ่าน `.env` ในงานนี้

## 3. นิยามปัญหาให้วัดได้

**Source task:** measured campaign/material/regime ที่มีข้อมูลเผยให้ model ได้ตาม manifest
**Target task:** campaign/material/regime ที่แยกจาก development และมี target outcomes ซ่อนอยู่ใน evaluator
**Capability shift:** ความต่างที่บันทึกได้ เช่น solvent ที่ใช้ได้, material identity, temperature/residence-time range ไม่เท่ากับการพิสูจน์ว่ากระบวนการ scale-up ใช้งานโรงงานได้

ในแต่ละ decision step ให้ policy เห็นเฉพาะ source data, permitted target inputs และ target observations ที่ถูกเปิดเผยแล้ว

- **Transfer:** commit prediction/decision ณ ตอนนั้น โดยใช้ source และ target observations ที่มีสิทธิ์อยู่แล้ว ไม่เห็นผลของ target query ถัดไป
- **Retest:** ใช้ target-label query ก่อนตัดสินใจถัดไป จ่าย query cost และบันทึกสิ่งที่เปิดเผยจริง
- **Insufficient Evidence / abstain:** ยังไม่ออกคำแนะนำที่อ้างความมั่นใจ ต้องรายงาน coverage และ deferral cost ไม่ได้รับคะแนนดีเพียงเพราะไม่ตอบ

ถ้าใช้ offline replay คำว่า query คือ **เลือกเปิดผลวัดเดิมใน observed pool** ไม่ใช่การทำ wet-lab experiment ใหม่ จุดที่ไม่มีผลวัดใน pool ห้ามแต่ง outcome หรือเรียกโมเดล surrogate ว่า measured truth
หากต้องใช้ simulator ให้แยก SIMULATED track/metrics/claims จาก MEASURED track ตั้งแต่ manifest

### Negative transfer และ hindsight labels

สำหรับ target group g และ query budget b ให้ loss ที่ยิ่งต่ำยิ่งดีเป็น L และเปรียบเทียบ

`Delta(g,b) = L_transfer(g,b) - L_no-transfer(g,b)`

Preregister practical tolerance `delta` ก่อนดู final outcomes: beneficial เมื่อ Delta < -delta, neutral เมื่อ |Delta| <= delta, harmful เมื่อ Delta > delta
เลือก tolerance จาก measurement resolution/replicate noise หรือเกณฑ์เชิงงานที่อธิบายได้ใน development เท่านั้น ไม่เลือกย้อนหลังเพื่อให้วิธีชนะ หากหาเกณฑ์ไม่ได้ ให้แสดง sensitivity grid ที่ freeze ไว้และไม่อ้าง threshold ที่ validate แล้ว
กรณีความไม่แน่นอนสูงให้ UNRESOLVED ไม่บังคับใส่ gold class ที่มั่นใจเกินหลักฐาน

Hindsight labels และ true Delta อยู่ **evaluator-only** Policy อาจทำนาย harmful-transfer risk แต่ห้ามอ่าน target held-out outcomes หรือ evaluator label เพื่อเลือก Transfer/Retest

## 4. Hypotheses และ metrics ที่รองรับ claim จริง

| Hypothesis | การทดสอบหลัก | สิ่งที่ผลลัพธ์รองรับ / ไม่รองรับ |
|---|---|---|
| H1 ตรวจ beneficial/neutral/harmful transfer บน unseen material/regime groups ได้ | prospective risk prediction, classwise recall/precision, Brier/log loss, reliability และ risk-coverage | รองรับความสามารถคาดการณ์ risk ภายใน benchmark; ไม่พิสูจน์ causal transferability ของทุกเทคโนโลยี |
| H2 ทำ target performance ดีขึ้นเมื่อ calibration/query budget เท่ากัน | paired fixed-budget loss/learning-curve area, regret หรือ task utility ที่ freeze; query/abstention costs | รองรับความคุ้มค่าของ policy/model ใน observed pool; ไม่เท่ากับลด wet-lab cost จริง |
| H3 document representation เพิ่มคุณค่าเหนือ chemical descriptors | descriptor-only, document-only, combined, shuffled/label-free template ablations ที่งบเท่ากัน | รองรับ representation benefit ในข้อมูลที่ตรวจ leakage แล้ว; ไม่ใช่ novelty จากใช้ LLM หรือ patent retrieval |

เลือก **primary endpoint หนึ่งชุด** หลัง data feasibility โดยไม่ดู final outcomes: เช่น group-averaged target loss ณ b* และ harmful-transfer risk บน coverage ที่กำหนด ส่วน optimization/regret เป็น secondary หาก observed pool และ objective เหมาะจริง
รายงาน raw group counts, effect sizes, paired group/bootstrap intervals และ failure analysis; random seeds/repeated rows/revisions ไม่เพิ่ม independent N
N และ repetitions ต้องอิง usable campaigns/materials และ pilot precision ไม่อิง K ของ API matrix หรือจำนวน synthetic rows

### แยกสอง tracks เพื่อไม่สับสนเหตุและผล

**Track A — matched information:** ทุก transfer comparator ได้ source set เดียวกันและ target-prefix/query points เดียวกันที่ freeze ทดสอบผลของการถ่ายโอนโดยลด confounding จาก query selection
No-transfer ตั้งใจไม่ได้ source data แต่มี target-prefix และ budget เท่ากัน

**Track B — adaptive acquisition:** policy เลือก query ของตนเองได้ภายใต้ target-query budget/initialization/candidate pool เดียวกัน ผลรวมสะท้อน model + acquisition policy ไม่อ้างว่าเป็น pure representation effect

มี zero-query และ target-only settings ด้วย ที่ b=0 ต้องนิยาม no-source prior จาก development เท่านั้น ไม่ fit target-only model ด้วย held-out labels แอบแฝง
เสนอ checkpoints b={0,2,4,8} เป็น development starting grid เท่านั้น ต้องปรับและ freeze ตาม query unit ที่ข้อมูลรองรับ ก่อน confirmatory run

### ป้องกัน always-retest / always-abstain ชนะโดยง่าย

- เปรียบเทียบ fixed-budget learning curves และ risk-coverage/query-cost frontiers ไม่เทียบเฉพาะ error ของข้อที่ยอมตอบ
- แยก granted budget, consumed queries และ remaining budget พร้อม cost ต่อ action; cost หน่วย query ไม่ใช่ราคาทดลองจริงที่แต่งขึ้น
- All-retest ใช้ budget เดียวกันและต้องออกผลเมื่อถึง horizon; ถ้าหมด budget ต้องหยุด/abstain ตามกติกาเดียวกัน
- Zero coverage ให้ risk เป็น NA และรายงาน deferral ไม่ให้ risk=0 แล้วประกาศชนะ
- กำหนด query cost, abstention penalty หรือ coverage constraint ก่อน final run พร้อม sensitivity analysis ห้ามเลือกราคาหลังเห็นวิธีที่ชนะ

## 5. Baselines, controls และ novelty gate

ใช้ IDs **T-/A-** สำหรับแผนใหม่ แยกจาก B0–B4/P เดิม ไม่ใช่การ rename implementation ที่มีอยู่

| Model family (PLANNED) | หน้าที่ |
|---|---|
| T0 descriptor/no-transfer/target-only | ไม่ใช้ source ของ trial นี้; target observations เท่ากัน มี zero-query reference ที่ระบุชัด |
| T1 pooled conventional transfer | รวม source/target แบบไม่แยก task เป็น strong simple baseline |
| T2 transfer GP / justified equivalent | แยก task correlations เช่น multi-task GP พร้อม comparable tuning allowance |
| T3 uncertainty-calibrated transfer | calibrate harmful-transfer risk/uncertainty ด้วย development groups ไม่ใช้ final target outcomes |
| T4 two-phase robust transfer | comparator ใกล้งาน Chen 2026; ศึกษารายละเอียดและ justify equivalent หาก reproduce ไม่ได้ ห้ามใช้ชื่อแล้วเขียนวิธีง่ายกว่ามาก |
| T5 document-augmented candidate | conditional H3: เพิ่ม representation เมื่อมี rights-cleared label-free documents และ baseline T0–T4 พร้อม |

Policy controls ที่ต้องมี: all-transfer, all-retest, random-query, space-filling query และ active-learning query พร้อม selective Transfer/Retest/abstain candidate
ไม่จำเป็นต้องทำทุก Cartesian combination: freeze minimal discriminating matrix ที่แยก model effect/acquisition effect และควบคุม target-query budget/tuning cost ได้
ทุก transfer method มี source availability เหมือนกัน ไม่มีวิธีหนึ่งเห็น source labels/target pool มากกว่าอีกวิธีโดยไม่ประกาศ setting

### Closest competing work — ไม่ใช่ completed systematic review

- **Catechol benchmark:** มี solvent featurization, GP/transfer และ active-learning benchmarks อยู่แล้ว จึงไม่ใช่ contribution เพียงนำข้อมูลนี้มารัน transfer อีกครั้ง [paper](https://arxiv.org/html/2506.07619v1)
- **Helleckes et al., Biotechnology Journal 2024:** มี GP knowledge transfer และ calibration design บน simulated bioprocess data [record/DOI](https://juser.fz-juelich.de/record/1030435)
- **Chen et al., Digital Discovery 2026:** ใกล้เป็นพิเศษ เพราะศึกษา robust chemical BO transfer, negative transfer และ two-phase strategy selection ต้องทำ claim-by-claim comparison ก่อน main study [primary publisher](https://pubs.rsc.org/dd/article/5/10/4121/1358875/Robust-transfer-learning-for-Bayesian-optimization)
- **MUSE, EMNLP 2025:** มี patent analogy/inspiration engine แล้ว ห้ามอ้าง novelty จาก cross-domain patent retrieval เพียงอย่างเดียว [ACL](https://aclanthology.org/2025.emnlp-main.1547/)
- Internal Paper53/Paper86 และ literature เดิมต้องมี reuse/overlap disclosure ตาม provenance จริง ไม่ยกความสำเร็จเดิมเป็นผลใหม่

**Novelty gate:** ต้องชี้ให้ได้ว่าต่างจาก robust/two-phase transfer ที่มีอยู่ตรง prospective calibrated decision risk, cost-aware Transfer/Retest หรือ document increment ที่พิสูจน์ได้อย่างไร หากต่างเพียงชื่อ/หน้าจอ ให้ปรับ contribution ก่อน confirmatory run ไม่ซื้อ API เพิ่มเพื่อชดเชย
ผลค้นนี้เป็น bounded primary-source planning; SciSpace/Consensus targeted work เป็น parent-reported ส่วน Consensus Deep ติด quota ไม่อ้างว่าเป็น systematic review ที่เสร็จแล้ว

## 6. Data candidate, rights และ acquisition gate

### Primary candidate: Catechol measured benchmark

[Upstream repository](https://github.com/jpfolch/catechol_solvent_selection) snapshot commit `0d8e3f41f33eb9e23e35854c9dbf12b3e99bf727`
Paper v1 รายงาน catechol full1227 observations, single-solvent subset656 และ related allyl-phenyl-ether283; **single-solvent เป็น subset ไม่ใช่ชุดอิสระเพิ่ม** ตัวเลขนี้เป็น source-reported ไม่ใช่ local parse counts และไม่ใช่จำนวน independent campaigns

Metadata ที่ตรวจได้โดยไม่ acquire CSV payload:

| Asset | Bytes / Git blob SHA | สถานะ |
|---|---|---|
| `data/full_data/catechol_full_data_yields.csv` | 520566 / `c8df1b68faf66bfe2f3e349d7ba89bc140c748c7` | metadata inspected, local acquisition NOT_RUN |
| `data/full_data/claisen_data_clean.csv` | 63660 / `51a1008d2135fca1db4a0fba023a0229862b6d71` | metadata inspected, local acquisition NOT_RUN |
| `data/single_solvent/catechol_single_solvent_yields.csv` | 186992 / `0de3b59905c04097dcdeac37d25e6b094f801ec5` | metadata inspected, local acquisition NOT_RUN |

พบ [root MIT LICENSE](https://github.com/jpfolch/catechol_solvent_selection/blob/0d8e3f41f33eb9e23e35854c9dbf12b3e99bf727/LICENSE) ของ Jose Pablo Folch2025 จริง และ README อธิบาย repo เป็น code/data
แต่ยังไม่ได้ตรวจ asset headers/third-party feature notices ทั้งหมด จึงไม่ประกาศว่า featurizations/underlying sources ทุกชิ้นมีสิทธิ์เดียวกันแล้ว ให้บันทึก per-asset license scope, citation, redistribution conditions และ raw SHA256 หลัง bounded acquisition ก่อนใช้/เผยแพร่
License ของ upstream ไม่ได้เปลี่ยน license ของ Patent-to-Pilot หรือครอบคลุม paper PDF อัตโนมัติ

**Data feasibility checklist:** parse schema/units, missing values, duplicates, experiment/ramp IDs, repeated conditions, material identity/mixtures, measurement noise, output definitions, campaign timestamps หากมี และ actual unique group counts
Paper แสดงโจทย์ที่เกี่ยวกับ correlated transient measurements และมี selection/preprocessing choices อยู่แล้ว จึงต้องตรวจ exclusions/measurement provenance ไม่ถือว่าแต่ละแถวเป็น independent random experiment

### Secondary / diagnostic only

[Helleckes Zenodo10630629](https://zenodo.org/records/10630629), v1.0.0 ระบุ in-silico mammalian-cell-culture data และ fixed/noisy variants หน้า License แสดงช่องว่างในการอ่านครั้งนี้; API metadata เข้าถึงไม่ได้ **license UNKNOWN, acquisition/use NOT_APPROVED by this proposal alone**
แม้ภายหลังใช้ได้ ก็เป็น SIMULATED diagnostic ไม่แทน measured primary evidence
NoBOOM และ PC-Gym เป็น optional diagnostic ideas ไม่ใช่ selected datasets หรือที่อ้างว่ารันแล้ว

Existing PLS/EnterpriseRAG/DAPFAM acquisitions ยังเป็น asset history ไม่ถูกนำมาเป็น measured transfer ground truth โดยปริยาย

## 7. Source-target split และ leakage controls

เลือก primary setting หลัง inventory แต่ก่อนดู heldout outcomes:

1. **Material/solvent shift:** hold out material/solvent groups; mixtures ที่มี heldout material และ duplicate conditions ต้องอยู่ component เดียวกัน ต้องตรวจว่า component graph ไม่ทำให้ usable split เหลือไม่พอ
2. **Operating-regime shift:** hold out entire campaigns/contiguous regimes ที่มีเหตุผลเชิงกายภาพ ตรวจ overlap/near-neighbor leakage ไม่ใช้ random adjacent time-series rows แบ่ง train/test
3. **Related-reaction extension:** optional setting ของ source reaction กับ target reaction ต้อง harmonize output/unit/objective และประกาศว่า task diversity จำกัด ไม่เรียกว่า broad cross-domain validation

แยก development/calibration/final target groups; shared campaigns, repeated samples, templates และ source-document derivatives ไม่กระจายข้าม split
Chemical grouping ใน benchmark ใหม่นี้ไม่ใช่ patent family IDs ของ PLS ให้ใช้ namespaces ต่างกันและเก็บ mapping provenance
Timestamp ไม่มีก็รายงาน UNKNOWN ไม่สร้าง historical prospective claim

Runtime เห็น target candidate inputs ได้ตาม transductive setting ที่ freeze แต่ **ไม่เห็น target labels** จน evaluator เปิด query ที่ถูกหักงบ ต้องมี access log/query ledger และ trap controls
Scaler, feature selection, calibration thresholds และ hyperparameter search fit เฉพาะ permitted development/source/training portions ตาม setting; ห้าม fit บน final target labels

แยก evaluator process/assets จาก method inputs มี closed public schemas และ permission/read controls ที่ตรวจได้ Hash/key filters อย่างเดียวไม่ใช่ OS isolation
Hindsight negative-transfer class, clean oracle decisions, future observations และ final-test outcome tables อยู่ evaluator-only
หากไม่มี credible measured grouped split ให้หยุด scientific claim หรือเสนอ scope ใหม่อย่างชัดเจน ไม่แทนด้วย synthetic success

## 8. H3 document branch — conditional และตัดได้

ก่อนสร้าง text features ต้องมี approved label-free corpus พร้อม locators/versions/rights แยกจาก outcome tables และ campaign selection results
ข้อความที่แปลงจาก descriptors เดิมล้วนไม่ได้เพิ่ม information ใหม่ ผลดีอาจเป็น inductive bias ต้องเรียกให้ตรง ไม่อ้างว่า “อ่านเอกสารแล้วได้ความรู้เพิ่ม”
Cache immutable extraction features ต่อ unique approved text/pair ตาม SHA/model/prompt/schema; ไม่เรียกซ้ำทุก fold และไม่ใช้ cached output ที่เคยเห็น heldout labels
เปรียบเทียบ descriptor-only, text-only, combined, shuffled/mismatched text และ label-free templated text ที่ matched information/budgets
บันทึก pretrained-model contamination risk และ identity masking controls ไม่อ้างว่าพิสูจน์ว่า LLM ไม่เคยเห็น public benchmark มาก่อนแล้ว

LLM consistency audit เป็น audit การสกัด ไม่ใช่ scientific ground truth Primary evaluator ใช้ measured outcomes + frozen numeric metrics/rubric; human review ตรวจ semantic/provenance และ disagreements แยกต่างหาก
ถ้า H3 ไม่เพิ่มประโยชน์ที่ preregister ไว้ ให้หยุด text branch และรายงานผล ไม่หยุด H1/H2 ทั้งหมด และไม่เพิ่ม LLM calls เพื่อไล่ผลบวก

## 9. Offline feasibility และแผน long run เป็นช่วง

ตารางนี้เป็น work order ที่เสนอสำหรับการรับช่วงภายหลัง ไม่ใช่บันทึกว่างานวิจัยเสร็จหรือกำลัง training ในรอบนี้

| Phase / G mapping | Deliverables | Gate และ stop condition |
|---|---|---|
| P0 scope/novelty — G01,G02 | claim/competitor matrix, precise RQs, narrow capability shift | ความต่างจาก Chen/Catechol/Helleckes ต้องตรวจได้; novelty ยังไม่พอ → revise claim |
| P1 data — G03,G05,G06 | bounded acquisition receipts, per-asset rights, group inventory, split manifest | rights/grouping/observed pool ใช้ได้จริง; independent groups ไม่พอ → BLOCKED/จำกัด claim |
| P2 offline feasibility — G07,G10,G13,G18 | loader, target-label broker, query ledger, T0/T1/T2 minimal baselines, deterministic controls | leakage traps, equal budgets, zero-query/target-only และ replay integrity ผ่านก่อน API expansion |
| P3 development calibration — G10,G13 | T3/T4, practical tolerance, risk calibration, fixed-budget curves, resource/cost receipt | development เท่านั้น; stop เมื่อ bounds/reliability/independent unit ไม่ชัด |
| P4 conditional text — G08,G10,G13 | approved text corpus, cached features, H3 ablations | text ไม่ช่วย → stop branch; no extra heldout tuning |
| P5 frozen confirmation — G06,G16,G17 | preregistered manifest, paired metrics/uncertainty, negative/failed outputs | no main until readiness passes; main ไม่ชนะก็รายงาน ไม่ rerun เพื่อ significance |
| P6 reproducibility/manuscript — G18,G20 | clean-checkout replay, exact env/config/data lineage, evidence tables/manuscript | results มาจาก actual artifacts; submission/APC/rankings ยัง separate gates |
| Parallel product — G04,G09,G14,G15 | journey/API proposals, backend adapters, Claude mock branch | UI ไม่เปิด access ไป evaluator; deploy/auth/hosting approval แยก |

แต่ละ phase ต้องมี finite run manifest: eligible groups, folds, seeds, hyperparameter trials/fit count, target-query checkpoints, wallclock/RAM/worker limits และ artifact paths
Local CPU เริ่มได้ภายหลังตรวจ resource availability และตั้งขอบเขต ไม่ถือว่า classical compute ฟรีไร้ขีดจำกัดหรือเป็น OpenRouter calls; รอบนี้ไม่มี training
Engineering status เดิมคือ offline reproducible components ไม่ใช่ scientific pilot-ready/new benchmark implemented

## 10. Budget proposal — ยังรอ owner เลือก

**ที่อนุมัติอยู่ตอนนี้: $5 รวมทั้ง campaign ใหม่ตาม scope เดิม**
**ข้อเสนอ:** LEAN **$25 รวม** หรือ RECOMMENDED **$50 รวม** ซึ่งรวม $5 เดิมอยู่แล้ว ไม่ใช่เพิ่ม $25/$50 เข้าไปอีก
**$100:** เป็น optional future expansion ที่ต้องเสนอ scope/budget ใหม่ ไม่ใช่คำแนะนำรอบนี้

### ราคาที่ใช้คำนวณ

Official model cards ตรวจ 27Oct2026: [Gemini2.5FlashLite](https://openrouter.ai/google/gemini-2.5-flash-lite) input/output $0.10/$0.40 ต่อ 1M tokens; [GPT-4.1Mini](https://openrouter.ai/openai/gpt-4.1-mini) $0.40/$1.60 ต่อ 1M
Route ยังต้อง revalidate ก่อน dispatch: google-ai-studio / openai, require parameters, no fallback/auto substitution ไม่มี cache discount หรือ paid embedding rate สมมติ

| Request type | Expected input/output | Expected USD | Proposed reservation input/output | Base bound USD |
|---|---:|---:|---:|---:|
| Extraction — Gemini | 2000/300 | 0.00032 | 4000/1000 | 0.00080 |
| Consistency audit — Mini | 4000/600 | 0.00256 | 8000/1500 | 0.00560 |
| Text prediction comparator — Gemini | 3000/300 | 0.00042 | 6000/1000 | 0.00100 |
| Text prediction comparator — Mini | 3000/300 | 0.00168 | 6000/1000 | 0.00400 |

Input ต้องรวม system/schema/context/framing ทั้งหมด Expected tokens เป็นประมาณการ ไม่ใช่ upper bound
Reservation ข้างต้นใช้บังคับได้เมื่อ tokenizer/route/output limit ตรวจจริงแล้วเท่านั้น มิฉะนั้นเป็น planning bounds และ **ห้าม dispatch** จากตัวเลขนี้

ให้ K=unique approved extraction pairs, A=consistency audits, QG/QM=justified prediction requests ไม่ใช่จำนวน scientific groups

`E = 0.00032K + 0.00256A + 0.00042QG + 0.00168QM`

`R = 0.00080K + 0.00560A + 0.00100QG + 0.00400QM`

| Capacity example เท่านั้น | K / A / QG / QM | E ของ matrix | R | R+25% retry reserve+$5 allocated | Campaign cap |
|---|---|---:|---:|---:|---:|
| LEAN | 3000/250/1500/1500 | $4.75 | $11.30 | $19.125 | $25 proposed |
| RECOMMENDED | 6000/500/3000/3000 | $9.50 | $22.60 | $33.25 | $50 proposed |

K/A/Q เป็น capacity illustrations ไม่ใช่ dataset size, sample-size justification หรือจำนวนงานที่ต้องใช้ให้หมด เผื่อ envelope $5 ไว้ภายใน cap อย่างอนุรักษนิยม; actual manifest ต้อง deduplicate กับ stage1 และนับ actual debit ครั้งเดียว
เลือกจำนวนจริงจาก eligible sources/groups และ frozen design ไม่สร้างข้อความ/target ปลอมเพื่อเติม capacity
Prediction comparators ทำเฉพาะเมื่อตอบ hypothesis จริง ไม่ต้องใช้ LLM แทน classical predictor ทุก iteration
หาก eligible manifest เล็กพอจะจบภายใน $5 ก็จบได้ ไม่สร้าง requests เพิ่มเพื่อให้ใช้งบ $25/$50 การแนะนำ $50 เป็น headroom ceiling ไม่ใช่ประมาณการว่าต้องจ่ายจริง $50

### Cumulative gates ถ้า owner อนุมัติ $50

| Stage | เพดานสะสม ไม่บวกกัน | สิ่งที่ต้องผ่านก่อนเดินต่อ |
|---|---:|---|
| 1 feasibility/token micro-pilot | $5 | offline data/leakage gate, exact payload/route, verified bounds, shared ledger |
| 2 development benchmark/baselines | $15 | stage1 reliable, actual cost และ manifest ที่ตอบ RQ ได้; ไม่ใช้ final labels จูน |
| 3 frozen confirmation/ablations | $35 | frozen plan/groups/metrics/tolerance, readiness/audit ผ่าน |
| 4 reproducibility/robustness/error analysis | $50 | มี recorded need ภายใน scope เดิม ไม่รันซ้ำเพื่อ significance หรือเพื่อใช้เงินให้เต็ม |

ถ้าอนุมัติเพียง $25 ให้ลด frozen matrix ตาม priority และกำหนด ceiling สุดท้าย $25 ไม่ถือว่า $35/$50 ถูกอนุมัติแล้ว
ภายหลัง approval สามารถเดินต่อภายใน gate/scope ที่ตกลงโดยไม่ถามซ้ำทุก request แต่ material scope/model/data/cost change ต้องหยุดให้พิจารณา

### Ledger และ retries

ทุก agent/UI/retry ใช้ shared atomic durable accounting เดียว:

`settled campaign debit + unknown/inflight reservations + next worst-case bound <= current cumulative stage cap`

Retry ได้สูงสุด **2 extra attempts ต่อ logical request** เฉพาะ transient failures ภายใต้งบ retry รวมไม่เกิน 25%ของ base reserve ไม่ถือว่า failed calls ฟรี ไม่มี retry สำหรับ schema/model drift/leakage เพียงเพื่อให้ได้คำตอบดีขึ้น
Unknown billing ต้อง reconcile ก่อนเดินต่อ; reserve/charge ไม่ถูกล้างเมื่อ restart/ย้าย agent; replay IDs ไม่ dispatch ซ้ำ
หากเพิ่ม cap ภายหลัง ต้อง audited policy migration/approval receipt ที่ carry ยอดของ campaign $5 เดิมและ pending ทั้งหมด ไม่สร้าง ledger ว่างแล้วได้$50 เพิ่มอีก Current code policy ยัง$5 ไม่แก้ constant ในงานเอกสารนี้

### เงินที่ไม่รวม และไม่ควรตีเป็นศูนย์

External CPU/GPU, storage/egress, expert annotation, physical experiments, hosting/domain, APC และ purchase fees/tax/FX ยัง TBD และไม่ได้รับอนุมัติ
[OpenRouter pricing](https://openrouter.ai/pricing) แสดง Standard fee5.5%; เป็น credit-purchase/checkout consideration แยกจาก model inference debit ไม่เสนอ exact checkout total หรือสั่งเติมเงินอัตโนมัติ
Owner เติมเครดิตเอง ไม่ใช้ยอดบัญชี/ยอด$10 ที่เคยรายงานเป็น cap งบนี้ไม่ครอบคลุม subscription/runtime ของ Claude/Luna โดยสมมติ

## 11. Product journey สำหรับ Claude — branch แยก

1. **Objective & capabilities:** ผู้ใช้ระบุเป้าหมายและข้อจำกัดสั้น ๆ ระบบช่วยสกัด แสดง measured/assumed/unknown แยกกัน
2. **Candidate mechanisms:** แสดง source-linked mechanisms, compatibility/incompatibility และเหตุผล ข้อความ patent เป็น evidence/inspiration ไม่ใช่ผลวัด target
3. **Transfer assessment:** Transfer / Retest / Insufficient Evidence พร้อม coverage scope, uncertainty, consumed queries และสิ่งที่ยังตรวจไม่ได้ ไม่มี confidence เปอร์เซ็นต์ที่แต่งขึ้น
4. **Consequential plan review:** ผู้ใช้ยืนยัน experiment plan ที่มีผลต่อ resource/safety ก่อนส่งต่อคนทำจริง ไม่บังคับ approve ทุก field และไม่ execute เครื่องมือแลบ/โรงงานเอง
5. **Measured result entry/import:** รับผลจริงหรือ replay results โดยติดชนิด MEASURED/REPLAY/SIMULATED/DEMO ให้ตรง ไม่แปลง demo เป็น measured
6. **Update & compare:** เห็น before/after, evidence versions, changed assumptions และ preserved content
7. **Evidence pack export:** export source/rights/metrics/unknowns/model/run provenance เป็น draft technical due diligence ไม่ใช่ investment/FTO/regulatory advice

Design minimal/formal, EN/TH configurable ตาม direction รอบนี้ มี formal/light/dark และ KMITL/ICT-inspired themes โดยไม่อ้าง official identity ก่อนตรวจทางการ
Loading/empty/error/blocked/insufficient-evidence/query-exhausted/version-conflict states ต้องมีข้อความและ next action; keyboard/contrast/responsive เป็น acceptance target
Claude ใช้ mock adapters และ branch แยกก่อน reviewedmerge ไม่ทำ UI implementation ในงานนี้

**Proposed contract เท่านั้น:** `TransferAssessment` ควรมี objective/source/target IDs, capability_shift, recommendation, predicted risk/delta พร้อม uncertainty, query_count/remaining_budget, evidence_refs, incompatibilities, next_query_plan, status/version
ไม่มี evaluator hindsight labels หรือ heldout outcomes ใน publicresponse Existing typed product contracts/HTTP API ไม่ถูกอ้างว่ารองรับ fields ใหม่นี้แล้ว ให้ Luna ทำ versionedadapter ก่อน integration

## 12. Role split, stop rules และ acceptance

| ผู้รับช่วง | งาน | Boundary |
|---|---|---|
| Pepo / GPT Work | proposal/requirements, bounded offline backend contracts/tests, targeted independent review ของงาน Luna, docs/evidence | ไม่อ้างว่าตัวเองเป็น domain expert หรือเริ่ม paidrun จากเอกสาร |
| Luna Max | data/protocol implementation, classical baselines, guarded long-run integration หลัง gates/approval | executor preference ไม่ใช่เปลี่ยน API model; no unapproved routes, no hidden resets |
| Claude | UI/mock journey บน branch แยก | ไม่แก้ frozen evaluation/backend guards เพื่อให้ demo ผ่าน; merge หลัง review |
| Owner / domain reviewers | material budget/data/deploy decisions, consequentialexperiment approval; researchrubric ถ้าต้องมี expertvalidation | no automatic investment/lab/regulatory execution; independentvalidation ต้องระบุผู้ประเมินจริง |

หยุด affected stage เมื่อ license ไม่ชัด, measured split ใช้ไม่ได้, source/target leakage, model/route/price/bounds เปลี่ยน, unknownbilling, cap/reliabilitybreach หรือไม่มี novelty ที่พออธิบายได้
H3 ไม่ช่วยหยุด H3; H1/H2 ไม่ช่วยรายงาน NO_ADVANTAGE; independentgroups น้อยรายงาน INCONCLUSIVE ไม่เพิ่ม syntheticrows เพื่อแก้ N
ไม่ rerunheldout เพื่อไล่ significance ไม่ให้ LLM เป็น soleevaluator ไม่จ่าย APC/submit/deploy/เช่า GPU โดยอาศัย APIcap นี้

**Engineering release-ready:** clean source/dependencies/tests, reliable jobs/history/export/security และ reviewedUI ตาม scope จริง
**Scientific pilot-ready:** rights/grouped data, numeric evaluator, fair baselines/query broker, bounded resource/ledger และ exactrunmanifest
**Journal submission-ready:** novelty review, sufficiently justified measured evaluation, uncertainty/failureanalysis, reproducibility และ manuscript ที่ใช้ผลจริง

ทั้งสามสถานะแยกกัน ปัจจุบันมีเพียง bounded engineering reproduction ที่ผ่าน ไม่ได้ปิด fullG10/G13/G16 หรือรับรอง internationalranking/Q1/acceptance
Journal venue ต้องเลือกใหม่ให้สอดคล้องกับ contribution ของ paper นี้ ไม่ถือว่า WPI เดิมเหมาะที่สุดโดยอัตโนมัติ

## 13. แบบตอบอนุมัติที่เสนอให้เจ้าของเลือก

ข้อความต่อไปนี้เป็น **TEMPLATE — ยังไม่ใช่ record ว่าอนุมัติแล้ว**

> อนุมัติแผน Transfer or Retest รุ่น 3 โดยเลือก [LEAN cap รวม USD25 / RECOMMENDED cap รวม USD50] รวม USD5 ที่อนุมัติไว้แล้ว นับทุก agent/retry/UItest ในบัญชีเดียว อนุญาตให้เดินต่อภายใน cumulativegates เมื่อผ่าน readiness และ manifest ตรวจแล้ว ไม่เติมเงินอัตโนมัติ
>
> ให้ใช้เฉพาะ rights-cleared public/synthetic inputs ที่ระบุใน manifest ผ่าน OpenRouter ไป Gemini2.5FlashLite→google-ai-studio และ GPT-4.1Mini→openai ตาม route/bounds ที่ตรวจแล้ว ข้อมูล source และ targetcalibration ที่เปิดเผยตาม queryrule ต้องระบุใน payloadallowlist ไม่มี private หรือ heldouttargetlabels/เฉลยส่งออก ไม่เปลี่ยน provider/model เอง
>
> ให้ Pepo/Luna ทำ scopedbackend/tests/docs และ commit/pushmain ของ origin เดิมหลัง checks Claude ทำ UIbranch แยกก่อน reviewedmerge ไม่ forcepush ไม่ deploy/ซื้อ hosting/เช่า GPU/ทำ wetlab/submitpaper หรือจ่าย APC โดยอัตโนมัติ หาก gates ไม่ผ่านให้หยุดเฉพาะส่วนและรายงานผลลบ/ข้อจำกัด

หากยังไม่เลือก ให้คง cap เดิม$5 และไม่มีการ dispatch จาก proposal นี้ ไม่อนุมาน budget เพิ่มจากคำว่า longrun

## 14. แหล่งอ้างอิงและข้อจำกัดการตรวจ

- Catechol [paper v1](https://arxiv.org/html/2506.07619v1), [repo snapshot](https://github.com/jpfolch/catechol_solvent_selection/tree/0d8e3f41f33eb9e23e35854c9dbf12b3e99bf727), [LICENSE](https://github.com/jpfolch/catechol_solvent_selection/blob/0d8e3f41f33eb9e23e35854c9dbf12b3e99bf727/LICENSE): อ่าน paper/README/license และ GitHubassetmetadata ไม่ได้ acquire/parseCSV หรือรัน upstreamcode
- Helleckes [published record](https://juser.fz-juelich.de/record/1030435), DOI10.1002/biot.202400080 และ [Zenodo](https://zenodo.org/records/10630629): source อธิบาย simulation; assetlicense ยัง UNKNOWN
- Chen [publisher record](https://pubs.rsc.org/dd/article/5/10/4121/1358875/Robust-transfer-learning-for-Bayesian-optimization), DOI10.1039/d6dd00527f: indexedprimarypublishertext อ่านได้ แต่ directfullpage ตอบ 403 รายละเอียด algorithm/reproduction ต้องตรวจต่อ ไม่อ้าง fullreproduction
- [MUSE](https://aclanthology.org/2025.emnlp-main.1547/): primaryabstract/metadata อ่านได้ ใช้เป็น noveltyboundary ไม่ใช่ baseline ที่รันแล้ว
- Official [Gemini](https://openrouter.ai/google/gemini-2.5-flash-lite), [Mini](https://openrouter.ai/openai/gpt-4.1-mini), [pricing](https://openrouter.ai/pricing): modelcardprices ตรวจ 27Oct2026 ไม่ใช่ route-specificexecutionguarantee
- Library research report `libfile_a65723cbb4188191bb49536184469e96` ไม่ได้ materialize/read ในรอบนี้ ใช้ essentialdirection และ parent-reportedresearchbrief ร่วมกับ primarychecks ข้างต้น
- GitHub/ZenodoAPI บางหน้าผ่าน webtool อ่านไม่ได้; GitHubpublicmetadata อ่านผ่าน connector ได้ OpenReview พบ browserchallenge จึงหยุด ไม่ผ่าน challenge/credentials

Current requirements: [รุ่น 3](../product/REQUIREMENTS_DECISIONS_20261027_V3_TH.md) · ประวัติเดิม: [รุ่น 2](../product/REQUIREMENTS_DECISIONS_20261027_V2_TH.md) · [Release reproduction](../handoff/RELEASE_REPRODUCIBILITY_20261027_R1_TH.md)
