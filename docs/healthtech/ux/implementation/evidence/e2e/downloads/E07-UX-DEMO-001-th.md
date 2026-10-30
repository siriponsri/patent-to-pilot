# แฟ้มหลักฐาน HealthTech — ฉบับส่งออกที่รวมข้อความที่แก้

**ตัวอย่างข้อมูลสมมติสำหรับตรวจการทำงานของระบบ**

> ใช้เตรียมหลักฐานเพื่อตรวจต่อ ระบบไม่ได้ให้ข้อสรุปทางการแพทย์ กฎหมาย หรือการลงทุน

| รายการ | ค่า |
|---|---|
| อุปกรณ์ (รหัสดิบ / รหัสมาตรฐาน) | UX-DEMO-001 (synthetic) / UX-DEMO-001 |
| รหัสแฟ้มหลักฐาน / เวอร์ชันฝั่งระบบหลัก | ux-synthetic-dossier / 1 |
| สแนปช็อตในเครื่อง | snap-mvv1mujt-uvvwef3jl2v4 (บันทึกยืนยันแล้วในเบราว์เซอร์นี้) |
| โหมด | synthetic_demo — ตัวอย่างข้อมูลสมมติสำหรับตรวจการทำงานของระบบ |
| วันตัดหลักฐาน | 2026-10-27 |
| เขตอำนาจ | US |
| รอบงาน | ux-simulated-run |
| SHA-256 ของแฟ้มหลักฐาน (canonical) | 287757968b8d3b879cb64ecd62ec5a9ed28fd2bbdb08d86905cc6aebdd375e50 |
| ตัวส่งออก | healthtech-web-markdown 1.0.0 (ตัวแปลงฝั่งหน้าเว็บ ไม่ใช่ตัวส่งออก dossier.md ของระบบหลัก) |

## หลักฐานจากต้นทาง

| รหัสหลักฐาน | ข้อความ | ประเภท / ฐาน | แหล่ง / ฉบับ | ตำแหน่งอ้างอิง | ข้อความอ้างหรือค่าฟิลด์ | การตรวจความตรงกับแหล่ง |
|---|---|---|---|---|---|---|
| ux-e-device | SYNTHETIC source field: SYNTHETIC demonstration comparator | ข้อเท็จจริงจากแหล่ง / ข้อเท็จจริงตามที่ต้นทางระบุ | ux-synthetic-device / ux-authored-v1 | field:device_name | device_name = &quot;SYNTHETIC demonstration comparator&quot; | ชื่อฟิลด์และค่าตรงกับต้นทาง — การตรวจนี้ยังไม่ได้ยืนยันข้อสรุป |
| ux-e-disclosure | SYNTHETIC authored span demonstration. | การเปิดเผยข้อมูลสิทธิบัตร / ความเชื่อมโยงที่แหล่งข้อมูลรายงาน | ux-synthetic-independent-disclosure / ux-authored-v1 | chars:0:125 | SYNTHETIC ONLY: the fictional UX-DEMO-001 record reports US99000002B2 as an association. This is authored demonstration text. | ข้อความตรงกับต้นฉบับ — การตรวจนี้ยังไม่ได้ยืนยันข้อสรุป |
| ux-e-unicode | SYNTHETIC authored span demonstration. | ข้อเท็จจริงจากแหล่ง / ข้อเท็จจริงตามที่ต้นทางระบุ | ux-synthetic-unicode / ux-authored-v1 | chars:1:2 | 🙂 | ข้อความตรงกับต้นฉบับ — การตรวจนี้ยังไม่ได้ยืนยันข้อสรุป |

## สิทธิบัตรที่เป็นรายการเบื้องต้น

| รหัสดิบ | รหัสมาตรฐาน | สถานะความเชื่อมโยง | แหล่ง / ฉบับ | หลักฐานการเปิดเผย | คะแนนตามชื่อ |
|---|---|---|---|---|---|
| US 99000001 A1 | US99000001A1 | retrieved_candidate — สิทธิบัตรที่ค้นพบเป็นรายการเบื้องต้น | ux-synthetic-patent-a / ux-authored-v1 | ไม่มีข้อมูล | authored_demo_rank=1 |
| US 99000002 B2 | US99000002B2 | disclosed_link — ความเชื่อมโยงที่มีแหล่งเปิดเผยอ้างอิง | ux-synthetic-patent-b / ux-authored-v1 | ux-e-disclosure | authored_demo_rank=1 |

_ไม่ใช่ข้อสรุปด้านเสรีภาพในการดำเนินการ (FTO) ความสมบูรณ์ของสิทธิบัตร การแพทย์ หรือการลงทุน_

## ประเด็นที่ยังหาข้อสรุปไม่ได้

- SYNTHETIC example only; real evidence and coverage are unknown.

## ข้อมูลที่ควรขอเพิ่ม (จากแฟ้มหลักฐาน)

- Request an independently sourced, dated real device-patent disclosure.

## ฉบับร่างคำขอข้อมูลในเครื่อง (ผู้ใช้เขียนเอง)

| คำถาม | อ้างอิง | บทบาทผู้ที่ควรถาม | ลำดับความสำคัญ | สถานะ |
|---|---|---|---|---|
| What dated source supports this association? | ux-e-disclosure | technology reviewer | ปกติ | ฉบับร่าง |
| ขอเอกสารเปิดเผยที่ลงวันที่ / Request a dated disclosure | ไม่มีข้อมูล | ไม่มีข้อมูล | ปกติ | ฉบับร่าง |

## การเชื่อมโยงคุณลักษณะ (ผู้ใช้เขียนเอง ระบบไม่ได้ตรวจยืนยัน)

- SYNTHETIC sensor: ux-e-device

## ข้อความแก้ไขที่อยู่ในแฟ้มที่นำเข้า (user_edits)

- review_note: ข้อความทดสอบการส่งออก / User note must survive export

## บันทึกของผู้ใช้ (ผู้ใช้เขียนเอง ข้อเท็จจริงจากแหล่งไม่เปลี่ยน)

### ux-note-1 — เกี่ยวกับ ux-e-device (สถานะการทบทวน: ต้องขอความชัดเจน)

> ยังต้องขอหลักฐานเพิ่มเติม / Request more evidence

### note-mvv1mmkv-178asv3ghzv1d — เกี่ยวกับ dossier (สถานะการทบทวน: ฉันทบทวนแล้ว (เป็นการทบทวนของผู้ใช้เท่านั้น))

> RACE_B

### note-mvv1msjf-6zoz6n50mmxm — เกี่ยวกับ dossier (สถานะการทบทวน: ฉันทบทวนแล้ว (เป็นการทบทวนของผู้ใช้เท่านั้น))

> EDIT_FROM_TAB_B

### note-mvv1mtil-upnt3w1qlri8a — เกี่ยวกับ dossier (สถานะการทบทวน: ฉันทบทวนแล้ว (เป็นการทบทวนของผู้ใช้เท่านั้น))

> RACE_A

## รายการแหล่งข้อมูล

- ux-synthetic-device: urn:synthetic:ux-synthetic-device; revision ux-authored-v1; US; 2026-10-27; sha256 65ae11daa06998a6b2daba3aeff3f74b062052ec0aa38cb380a9221bad2839f9; ข้อมูลสมมติ; หมายเหตุสิทธิ์: Project-authored synthetic fixture; no real device, patent or disclosure.
- ux-synthetic-patent-a: urn:synthetic:ux-synthetic-patent-a; revision ux-authored-v1; US; 2026-10-27; sha256 17c5d17d46fb16a8885af7bf0e566fbdce17137911e83e1c796c6f3a09270031; ข้อมูลสมมติ; หมายเหตุสิทธิ์: Project-authored synthetic fixture; no real device, patent or disclosure.
- ux-synthetic-patent-b: urn:synthetic:ux-synthetic-patent-b; revision ux-authored-v1; US; 2026-10-27; sha256 4f2042bba28f5fca61bf4a01aeca568293199207348aafb80341c5ffc4fffc2e; ข้อมูลสมมติ; หมายเหตุสิทธิ์: Project-authored synthetic fixture; no real device, patent or disclosure.
- ux-synthetic-independent-disclosure: urn:synthetic:ux-synthetic-independent-disclosure; revision ux-authored-v1; US; 2026-10-27; sha256 4bdf5ac7134e2257eb5242d4bcf4fdd2f45e75d7319ec383a400a0629e76afad; ข้อมูลสมมติ; หมายเหตุสิทธิ์: Project-authored synthetic fixture; no real device, patent or disclosure.
- ux-synthetic-unicode: urn:synthetic:ux-synthetic-unicode; revision ux-authored-v1; US; 2026-10-27; sha256 dfdf39721a3e57d17bb6ed6503cfc8e6f1fef718c58e184d1ac1c903cbc20d39; ข้อมูลสมมติ; หมายเหตุสิทธิ์: Project-authored synthetic fixture; no real device, patent or disclosure.

## ขอบเขตการส่งออก

- รวมไว้: ข้อเท็จจริงจากแหล่งพร้อมตำแหน่งอ้างอิง รายการเบื้องต้นและสถานะ ประเด็นที่ยังไม่มีข้อสรุป คำขอข้อมูลจากแฟ้ม ฉบับร่างคำขอในเครื่อง การเชื่อมโยงคุณลักษณะ user_edits ที่นำเข้า และบันทึกของผู้ใช้
- ไม่รวม: ข้อมูลต้นฉบับทั้งหมดของแหล่งและเหตุการณ์ของรอบงาน (ใช้ JSON กู้คืนหากต้องการสำเนาที่ไม่สูญหาย)
