# Research & Innovation Portfolio — Patent-to-Pilot (one page, 19 Nov 2026)

ผลงานที่นักศึกษาพัฒนาระหว่างการศึกษา IS (KMITL, คณะเทคโนโลยีสารสนเทศ, AI4BA) แบ่ง 3 คอลัมน์ตามสถานะจริง
ไม่มีช่องใดอ้างการตีพิมพ์ สิทธิของสถาบัน หรือการใช้งานจริงที่ยังไม่มีเอกสาร

| ด้าน | ทำสำเร็จแล้ว (มีหลักฐาน) | กำลังดำเนินการ (IS2 และงานคู่ขนาน) | ศักยภาพต่อยอด (เงื่อนไข: ผลวิจัย + ความเห็นชอบของสถาบัน) |
|---|---|---|---|
| ผลงานวิชาการ | Paper 53 ได้รับการตอบรับ นำเสนอ 20 พ.ย. 2569 (DOI รอออก); IS1 ผ่าน (85/100, S) | IS2: B53 first-stage substitution บน DAPFAM (protocol ตรึงแล้ว กำลังรัน) | บทความวารสาร 3 เรื่องในรายชื่อวารสารของคณะ (`journal/VENUES.md`) เมื่อมีผลและผ่าน peer review |
| โครงสร้างพื้นฐานงานวิจัย | Canonical split manifest แบบ family-aware (freeze receipt); Challenge-1M 1,000,000 units; ข้อมูลข้อความ USPTO/PatentsView พร้อม hash | B53 pipeline + tests; P1 fine-tuning grid บน RunPod (งบ ≤ USD 20) | ชุด benchmark/โค้ดสำหรับการสอนและการวิจัย ภายใต้ใบอนุญาตที่เหมาะสม |
| ผลเชิงวิธีวิทยา | DEV baselines วัดแล้ว (BM25 0.1727, Arctic 0.2248, Qwen3 0.2741, PatEmbed-large 0.3282 OUT R@200); pre-declaration ก่อนคำนวณ; cost ledger | การรายงาน null/negative result อย่างตรงไปตรงมา; exposure accounting ที่ไม่สรุปเชิงสาเหตุ | ตัวอย่างการสอนเรื่อง reproducibility, test isolation, causal caution |
| ซอฟต์แวร์ | Solution Scout ต้นแบบ local TH/EN (evidence dossier, provenance, export) | demo 60–90 วินาที แบบ static พร้อมป้ายแหล่งข้อมูล | pilot กับ design partner / technology transfer หากได้รับความร่วมมือจริง |
| ประโยชน์ต่อผู้ใช้ | ยังไม่มีผู้ใช้จริง (NOT_MEASURED) | proxy: zero-exposure rate, first-hit rank, review depth, cost per recovered citation | user study กับผู้ค้นสิทธิบัตร / ฝ่าย R&D |

ป้ายหลักฐานที่ใช้บนสไลด์: MEASURED · HISTORICAL PROJECT RECORD · ENGINEERING VALIDATED · DESIGNED / NOT_RUN · HYPOTHESIS ·
PUBLISHED / ACCEPTED (Paper 53 = ACCEPTED จนกว่า DOI จะออก)
