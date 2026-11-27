# 02 — การเชื่อม IS2 กับ paper 53

Paper 53: "Diagnosing Near-Zero Instruction Effects in Cross-Domain Patent Reranking" (Srihangpiboon & Ploysuwan, KMITL). **TODO: ใส่ venue/DOI/สถานะตีพิมพ์จริง** (ผมยังไม่มีข้อมูลนี้)

## 1. สิ่งที่ paper 53 พบ (จากไฟล์ที่ให้มา)
- 692 held-out queries; Patent-aware เทียบ Generic เปลี่ยน strict OUT nDCG@100 +0.0008 (95% CI [−0.0010, 0.0028]); Claim-focused −0.0007 (CI [−0.0026, 0.0012]); ไม่ผ่านหลัง Holm
- 257 pools มี OUT-relevant family ใน top 100; ในกลุ่มนี้คะแนนต่างจาก Generic ~95% ของ query แต่กำไร/ขาดทุนสมดุล
- ข้อควรระวัง: ไม่ได้กู้ original-run records จึง **ตรวจซ้ำอิสระไม่ได้**

## 2. เหตุผลที่ IS2 "ต่อยอด" ได้อย่างสุจริต
บทเรียนของ paper 53: การปรับ instruction/prompt ให้ reranker ไม่ให้ผลที่วัดได้ และสิ่งที่กำหนดผลคือ "pool exposure" (มีหลักฐานที่เกี่ยวข้องในกองหรือไม่) → IS2 เปลี่ยนจาก **ปรับคำสั่ง** เป็น **โครงสร้างหลักฐาน + การงดตอบ**: ถ้าหลักฐานไม่อยู่ในกอง ระบบไม่ควรเดา แต่ส่งต่อผู้ประเมิน นี่คือ motivation ตรงๆ

ประโยคแนะนำสำหรับ Introduction (ปรับตามจริง):
> "Prior work by the same group found that instruction-level adaptation produced near-zero effects in cross-domain patent reranking, with outcomes governed largely by whether relevant evidence was present in the candidate pool [paper 53]. We therefore move from prompt-level adaptation to evidence-structured, abstention-aware prediction."

## 3. ข้อควรทำให้อ้างได้อย่างเปิดเผย
- อ้างเป็น "ผู้เขียนกลุ่มเดียวกัน" ชัดเจน; ไม่อ้างว่าผล paper 53 ถูกยืนยันอิสระแล้ว
- IS2 ต้องอยู่ได้ด้วยตัวเอง (ไม่พึ่งผลของ 53)
- ใช้คำว่า "extends/ motivated by" ไม่ใช่ "validates"

## 4. โครง IS2 (IMRaD)
1. Introduction: pain (generic/biosimilar เพิ่ม, ผู้ประเมินขาดแคลน = สมมติฐานที่ต้องหาแหล่งอ้างอิง) → prior art → gap → contributions (benchmark, method, prospective freeze)
2. Related work: generic-entry prediction; biosimilar/patent thickets; selective prediction; LLM+patent
3. Data & benchmark: แหล่ง, label, split, embargo, Track A/B/C
4. Method: evidence graph, calibration, abstention, VoI
5. Experiments: arms, metrics, preregistration, ablations
6. Results: ตารางตามเกณฑ์ที่ตรึง; ผลลบรายงานตามจริง
7. Prospective Track A: ผลบางส่วน/ตามที่มี
8. Discussion: นัยต่อ triage, ข้อจำกัด
9. Limitations; Data/code availability (sha256)
10. Ethics: ไม่ใช่ legal opinion
