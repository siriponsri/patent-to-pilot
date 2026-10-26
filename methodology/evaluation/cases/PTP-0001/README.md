# PTP-0001: แยกวัสดุฐานรองออกจากวัสดุเข็ม

24 ตุลาคม 2026 · **หนึ่ง development case** · ไม่มี model run หรือ scientific validation · ผู้สร้างยังไม่มี expert gold

## ใช้ตอบคำถามอะไร

ถ้าองค์กรเปลี่ยนข้อห้ามเรื่องวัสดุ ระบบต้องแก้เฉพาะรายการที่เกี่ยวข้องและบอกสิ่งที่ยังไม่รู้ กรณีนี้จงใจเริ่มเล็ก: เปรียบเทียบ **ตัวเลือกวัสดุ substrate** ในเอกสาร ไม่ได้ตัดสินว่ากระบวนการผลิต microneedle ทั้งเส้นทางทำได้ ปลอดภัย หรือไม่ติดสิทธิ์

แหล่งจริงคือ [US20060086689A1, Method of fabricating microneedles](https://patents.google.com/patent/US20060086689A1/en), publication date 2006-04-27 คำอธิบาย Fig. 2A/paragraph 0016 แยก substrate ออกจาก seed layer ส่วน paragraph 0017–0019 กล่าวถึง pattern, micromold และวัสดุเข็มคนละบทบาท มี [source snapshot/hash](sources/source-manifest.json) และ character offsets ที่ตรวจซ้ำได้

ไม่ได้จับคู่ publication นี้กับ DAPFAM family ID และไม่เดา family/publication number จากชื่อคล้ายกัน Source assertion เป็นสิ่งที่ patent กล่าว ไม่ใช่ผลทดลองที่ยืนยันโดยโครงการ

## โจทย์องค์กรที่แต่งขึ้นอย่างเปิดเผย

- เป้าหมาย: ทำชุดเอกสารเปรียบเทียบส่วนประกอบเพื่อให้ผู้ทบทวนทำงานต่อ
- มีความสามารถอ่านเอกสาร ส่วนความสามารถผลิตจริงยัง unknown
- Candidate A เลือก silicon substrate; B เลือก glass substrate ทั้งสองเป็น **benchmark choices** จากทางเลือกที่กล่าวใน source ไม่ใช่ route ที่ผ่านการรับรอง
- P0 อนุญาตทั้งสองวัสดุ; P1 ห้าม silicon เฉพาะ substrate และยังอนุญาต glass
- ต้องมีช่อง measured production yield แต่ allowed packet ไม่ได้ให้หลักฐานผล yield

สถานะคำตอบมีเพียง passes_this_explicit_check / fails_this_explicit_check / unknown การผ่านกฎนี้ไม่เท่ากับผ่านกฎอื่นหรือเป็นคำแนะนำทางคลินิก

## Change sequence และ expected behavior

| State | เหตุการณ์ | A | B | สิ่งที่ต้องรักษา |
|---|---|---|---|---|
| S0 | P0 | ผ่านกฎนี้ | ผ่านกฎนี้ | ID, source links, yield unknown |
| S1 | P1 ห้าม silicon substrate | ไม่ผ่านกฎนี้ | ผ่านกฎนี้ | ไม่เปลี่ยน substrate เป็น final needle; ถอน/qualify การเลือก A ที่อาศัยการผ่านกฎ |
| S2 | เปลี่ยนชื่อ project เท่านั้น | ไม่ผ่านเหมือนเดิม | ผ่านเหมือนเดิม | วัสดุ, evidence และ policy states เดิม |
| S3 | ถอน C02 ซึ่งเป็น allowed support เพียงรายการเดียวของ B ใน packet นี้ | ไม่ผ่านเหมือนเดิม | unknown | เก็บประวัติ C02 แต่ไม่ใช้เป็น current support |
| S4 | ขอให้ยืนยัน yield โดยไม่มีหลักฐานใหม่ | ไม่ผ่านกฎ substrate; yield unknown | substrate unknown; yield unknown | ขอหลักฐาน ไม่แต่งตัวเลข |

การถอนหลักฐานกับการห้ามวัสดุให้สถานะต่างกัน การไม่พบ yield หมายถึง packet นี้ไม่รองรับ ไม่ใช่ประกาศว่าไม่มีข้อมูลในโลก ข้อความตัวอย่างของ source สลับ silver/palladium ให้คง ambiguity ไม่แก้ต้นฉบับให้ดูลงตัว

## แยก bookkeeping ออกจาก extraction/search

**Track A: checked facts.** ให้ [checked tuples](public-input/track-A-checked-facts.json) ชุดเดียวกันทุกวิธี Rules ควรทำได้ถูกและถูกกว่า หาก agent ไม่เพิ่มประโยชน์ให้รายงานตามจริง Track นี้ใช้เช็ก revision bookkeeping ไม่ใช้พิสูจน์ agency

**Track B: open text / fixed source.** ให้เฉพาะ current [S0–S4 packets](public-input/S0.json), synthetic choices/policy และ [output schema](public-input/output-schema.json) ไม่มี checked tuples, hidden witness mapping หรือ gold dependency graph วิธีต่าง ๆ ต้องหา component role และ witness จากข้อความก่อนใช้ policy evaluator เดียวกัน เปรียบเทียบ lexical/component-window extraction + rules, one-pass structured extraction + rules และ adaptive/dependency-guided extraction เมื่อมี task อนุญาตให้รันจริง รายงาน extraction/witness correctness แยกจาก policy consistency ให้ทุกวิธีมีข้อความ/งบ extraction เท่ากัน

**Adaptive-search track ภายหลัง:** ยังไม่สร้าง ต้องมี verified distractors และหลักฐานกู้คืนได้ที่ไม่อยู่ใน initial retrieved subset แล้วให้ทุก baseline เข้าถึง pool/งบเดียวกัน หนึ่ง packet สั้นนี้ไม่พิสูจน์ search efficiency อย่ารวมผล fixed-source กับ retrieval-change จนไม่รู้ว่าผลมาจากการค้นหรือ repair

Baseline adaptive-search + full regeneration และ adaptive-search + direct revision ต้องเปลี่ยน what/where/how จาก intermediate results และลอง alternative อย่างมีขอบเขตตามการตีความบทความ Oltra-Garcia ไม่เรียก exact reproduction ของ algorithm ที่ paper ไม่ได้เผยแพร่

## โครงสร้างและขอบเขต evaluator

- `public-input/`: current packets, schema และ Track A supplement ให้เฉพาะ supplement ใน Track A
- `sources/`: curator source archive ไม่ส่งทั้ง directory ให้ evaluated system โดยเฉพาะหลังถอน support
- `evaluator-only/`: witnesses, expected states และ authored fixtures **ไม่ส่งให้ระบบที่ถูกประเมิน** การแยก folder อย่างเดียวไม่ใช่ access control; เมื่อทำ runner จริงต้อง stage แค่ public current packet ไปยัง process/workspace แยก
- [validate_case.py](validate_case.py): offline source/contract checks ไม่ได้ตัดสิน semantic entailment หรือ engineering feasibility
- Positive fixture คือ expected output ที่ผู้สร้างเขียน ไม่ใช่ model output Negative fixtures จงใจใส่ wrong component role, revoked-source reuse, invented yield และ collateral change

```powershell
rtk proxy python methodology/evaluation/cases/PTP-0001/validate_case.py --report
```

ดูผลที่ [verification.json](verification.json) จำนวน checks ไม่ใช่จำนวน independent scientific samples หยุดกรณีแรกเมื่อ literal witness/contract checks และ negative fixtures ผ่าน แล้วทบทวนว่า schema มีประโยชน์พอก่อนขยายไป independent source/family groups
