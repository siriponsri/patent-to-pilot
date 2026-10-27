# GOAL — Patent-to-Pilot HealthTech

> Implementation checkpoint (27 October 2026): [migration and coverage](docs/healthtech/MIGRATION.md), [actual progress](docs/healthtech/progress.json). The pack’s starting statuses below are historical starting points; the full HealthTech study and product are not complete.

**Version:** 1.0 · **วันที่:** 27 ตุลาคม 2026 (Asia/Bangkok) <br>
**รูปแบบ:** Goal-based execution contract สำหรับ owner และ coding/research agents <br>
**สถานะ:** แผนที่พร้อมนำไปดำเนินงาน; เอกสารนี้ไม่ใช่หลักฐานว่าได้รันการทดลองใหม่หรือพิสูจน์ตลาดแล้ว <br>
**อ่านร่วมกับ:** [PLAN.md](PLAN.md), [README.md](README.md), [RELATED_PAPERS.md](RELATED_PAPERS.md)

## 0. อ่านส่วนนี้ก่อนเริ่มงาน

### 0.1 เป้าหมายใหญ่

พัฒนา Patent-to-Pilot ให้มี **ผลิตภัณฑ์ที่ผู้ประกอบการและนักลงทุนใช้จัดเตรียมหลักฐานสำหรับคัดกรองเทคโนโลยี HealthTech ได้จริง** และมี **งานวิจัยด้าน patent information ที่ทำซ้ำได้และพร้อมส่งพิจารณา World Patent Information** โดยใช้แกน retrieval/evidence เดียวกัน

เริ่มจาก Medical Device ที่มีชื่อหรือรหัสอุปกรณ์อ้างอิงชัดเจน ใช้ cardiovascular device–patent linking เป็นกรณีวิจัยตั้งต้นแบบมีเงื่อนไข แล้วขยาย Pharmaceutical หรือ Biologics เมื่อมีข้อมูลและงานของลูกค้ารองรับ

ให้เดินงานตามผลลัพธ์และหลักฐาน ความคืบหน้าไม่ได้วัดจากจำนวนวัน จำนวน agent จำนวนเอกสาร หรือจำนวน tests ที่เพิ่มขึ้น

### 0.2 งานที่ agent ต้องรับผิดชอบเอง

Agent ต้องอ่านบริบทที่จำเป็น เลือกงานที่พร้อมทำ ลงมือ แก้ปัญหาที่อยู่ในอำนาจ ตรวจเฉพาะสิ่งที่มีความเสี่ยงจริง บันทึกผล และส่งมอบงานที่ตรวจได้ โดยลดการถาม owner เรื่อง implementation details

เมื่อ dependency หนึ่งติดขัด ให้จำกัดผลกระทบไว้ที่งานนั้นแล้วเลือกงานอิสระถัดไป ห้ามเปลี่ยนสถานะทั้งโครงการเป็น BLOCKED เพียงเพราะ dataset หนึ่งยังไม่พร้อม, model alias หนึ่งไม่มี, ยังไม่มีลูกค้า, หรือยังไม่ได้ผลทดลองที่คาดหวัง

### 0.3 คำสั่งเริ่มต้นสำหรับ agent

1. อ่าน sections 0–4 ของไฟล์นี้ และรายการงานที่ตรงกับเป้าหมายปัจจุบันใน PLAN.md
2. ตรวจคำสั่งล่าสุดของ owner, สถานะ repository และ progress record ที่มีอยู่จริง
3. ระบุหนึ่งผลลัพธ์ที่ทำได้ด้วยข้อมูล สิทธิ์ และงบที่มี
4. เลือกวิธีที่ง่ายพอและตรวจได้ ทำงานให้เสร็จเป็นหนึ่ง work package
5. ตรวจสิ่งที่เปลี่ยนและความเสี่ยงที่เกี่ยวข้อง แก้เฉพาะ failures ที่มีสาระ
6. บันทึกสิ่งที่ทำ หลักฐาน ข้อจำกัด ต้นทุน และงานถัดไป
7. หากยังมีงานที่ได้รับอนุญาตและพร้อมทำ ให้ทำต่อโดยไม่ถามว่า “ให้ทำต่อไหม” ทุกขั้น

เอกสารนี้ตั้งใจให้ agent ตั้งแต่ระดับที่ owner เรียกว่า **gpt 5.6 luna max** อ่านต่อได้ ชื่อนี้เป็นความต้องการด้านความสามารถ ไม่ใช่การยืนยันว่าเป็น model ID ที่มีใน provider ใด อย่าเดา model ID หรือเปลี่ยนโมเดลสำหรับ scientific run โดยไม่บันทึก configuration

## 1. ขอบเขตที่ยึดเป็นค่าเริ่มต้น

### 1.1 Product contract

| รายการ | ค่าเริ่มต้น |
|---|---|
| ผู้ใช้ปลายทางหลัก | ผู้ประกอบการ MedTech และนักวิเคราะห์การลงทุน |
| ผู้ร่วมออกแบบ workflow / ช่องทางเข้าตลาด | ที่ปรึกษาเทคโนโลยี นวัตกรรม และ RA; ทีม R&D/BD ขนาดเล็ก |
| จุดเริ่มต้น | ผลิตภัณฑ์ อุปกรณ์ หรือ comparator ที่ผู้ใช้ระบุหรือเลือกแล้ว |
| งานที่ช่วย | เตรียมข้อมูลก่อนศึกษารายละเอียด ขอข้อมูลเพิ่มเติม หารือ licensing หรือกำหนดขอบเขตการพัฒนา/ทดสอบ |
| ผลลัพธ์ | แฟ้มหลักฐานที่แก้ไข ตรวจแหล่งที่มา และส่งต่อได้ |
| แหล่งข้อมูลเริ่มต้น | ข้อมูลสาธารณะและแหล่งที่มีสิทธิ์ใช้ตามงานที่ทำ |
| ภาษาผลิตภัณฑ์ | ไทยและอังกฤษ; ใช้ข้อความที่ผู้ประกอบการเข้าใจได้ |
| รูปแบบ UI | Minimal, formal, no-code journey; รักษา theme choices ที่โครงการมีไว้ |
| รูปแบบรายได้ที่ทดสอบ | Bounded project pilot; ต่อด้วย hosted active-project/team offering เมื่อมีการใช้ซ้ำ |

### 1.2 Output contract ของ dossier

แฟ้มหนึ่งชุดต้องมี:

1. Product/regulatory facts พร้อม source, jurisdiction และวันที่
2. Patent candidates และ associations พร้อมประเภทของหลักฐานที่ใช้เชื่อม
3. Feature–evidence table ที่มี locator และข้อความหรือ field ต้นทาง
4. ข้อมูลที่ยังขาดหรือค้นไม่พบภายใต้งบที่ใช้
5. รายการคำถามหรือข้อมูลที่ควรขอเพิ่มเพื่อดำเนินงานขั้นถัดไป
6. รูปแบบแก้ไข ส่งออก และตรวจประวัติได้

ค่าที่แสดงต้องแยก source fact, reported result, system inference และ unresolved ให้ชัด การมี citation ที่เปิดได้เพียงอย่างเดียวไม่ยืนยันว่าข้อสรุปได้รับการสนับสนุน

### 1.3 ขอบเขตของคำสัญญา

ผลิตภัณฑ์ช่วยเตรียมหลักฐานสำหรับการศึกษาหรือการตัดสินใจขั้นถัดไป ผลของ benchmark เริ่มต้นครอบคลุม recovery ของ documented device–patent associations เท่านั้น

การประเมิน clinical suitability, complete FTO, patent validity, manufacturing feasibility, approval probability, investment return และ idea-to-comparator matching ต้องมีข้อมูลและการประเมินเฉพาะก่อนเพิ่มเป็นคำสัญญาของผลิตภัณฑ์

ข้อนี้เป็นขอบเขตของ claims ไม่ใช่เหตุผลให้หยุดการพัฒนา source viewer, evidence table, retrieval, export หรือ workflow ที่ทำได้อยู่แล้ว

### 1.4 Research contract

**Working title:** Evaluating Adaptive Evidence Acquisition for Medical-Device Patent Screening under Incomplete Judgments

คำถามหลักคือ adaptive acquisition ช่วย recovery ของ known device–patent links หรือช่วยลดต้นทุนได้ในเงื่อนไขใด เมื่อเทียบกับวิธี fixed และวิธี adaptive ที่เรียบง่าย โดยคำนึงถึง company information, shared patents/families และคำตอบอ้างอิงที่มีไม่ครบ

Generic adaptive RAG, cost-aware selection และ evidence-aware stopping มี prior art แล้ว ห้ามอ้างสิ่งเหล่านี้เป็นความใหม่โดยอัตโนมัติ Contribution ต้องมาจาก patent-specific questions, rigorous comparisons, substantive findings และ reproducible resources ดู literature map ใน RELATED_PAPERS.md

## 2. กติกาความต่อเนื่องและอำนาจตัดสินใจ

### 2.1 แหล่งคำสั่งและการเปลี่ยนทิศทาง

คำสั่งล่าสุดของ owner และข้อกำหนดของ runtime มาก่อนค่าเริ่มต้นในเอกสารนี้ เมื่อเกิดความขัดแย้งกับแผนเก่า ให้ใช้คำสั่งปัจจุบันกับงานใหม่และบันทึกการเปลี่ยนแปลง โดยรักษาผลทดลองและหลักฐานในอดีตไว้

เอกสารชุดนี้กำหนด HealthTech track ใหม่ ใช้ prefix **HT-G** สำหรับ goals, **HT-W** สำหรับ work packages และ **HT-B** สำหรับ baselines เพื่อไม่ปะปนกับ historical G10, G13, B0–B4 หรือ protocol เดิมใน repository

Root GOAL.md และ PLAN.md เป็นจุดเริ่มอ่านสำหรับ track นี้ ข้ออ้างอิงเก่าที่ชี้ไปไฟล์ PLAN ซึ่งไม่มีอยู่จริงให้แก้เฉพาะลิงก์ที่เกี่ยวข้องเมื่อมีงานแก้ repository ไม่ต้องสร้างระบบเอกสารซ้ำหลายชุด

### 2.2 Agent ตัดสินใจได้เอง

| เรื่อง | Default action |
|---|---|
| โครงสร้างภายใน module, naming และ helper functions | เลือกให้สอดคล้องกับ repository แล้วทำต่อ |
| แก้บั๊กที่เกิดจากงานที่ได้รับมอบหมาย | แก้และตรวจเฉพาะผลกระทบ |
| Library หรือวิธีที่มีหลายทางเลือก | เลือก dependency ที่มีอยู่หรือทางที่เรียบง่าย บันทึก trade-off ที่มีสาระ |
| ตัวอย่าง UI และ synthetic fixtures | สร้างและติดป้าย synthetic ชัดเจน |
| ค่า default ของ prototype | กำหนดให้ย้อนกลับได้และบันทึก assumption |
| Source หนึ่งดึงไม่ได้ | ใช้ cached snapshot ที่มี provenance, เปลี่ยน source ที่รองรับ task เดิม, หรือ skip เฉพาะส่วนนั้น |
| Method ที่ซับซ้อนไม่ให้ประโยชน์ | ใช้วิธีง่ายใน product และรายงานผลการทดลองตามจริง |
| ข้อมูลไม่พอสำหรับ claim กว้าง | จำกัด claim แล้วทำส่วนที่พิสูจน์ได้ต่อ |
| ไม่มี expert annotator ใหม่ | ใช้ existing gold labels และ deterministic source checks; เริ่มงานได้ |
| ยังไม่มีลูกค้า | ทำ public-case workflow, demo, task script และ offer ให้ตรวจได้ต่อ |

### 2.3 เรื่องที่ต้องใช้การตัดสินใจของ owner เมื่อยังไม่มี authorization

ขอเฉพาะสิ่งที่มีผลต่อสิทธิ์ ค่าใช้จ่าย หรือ commitment จริง เช่น การจ่ายเกินงบที่ได้รับอนุญาต, การส่งข้อความถึงบุคคลภายนอก, การรับข้อตกลงทางการค้า, การเผยแพร่ข้อมูลที่ยังไม่มีสิทธิ์ หรือการกระทำที่ทำลายข้อมูลสำคัญ

ก่อนถาม ให้ทำงานเตรียมที่ได้รับอนุญาตให้เสร็จ และส่งคำถามพร้อมทางเลือกที่แนะนำ ผลกระทบ และสิ่งที่พร้อมตรวจแล้ว ถ้าคำสั่งก่อนหน้าครอบคลุมการกระทำนั้นอยู่แล้ว ให้ดำเนินการตาม authorization เดิมโดยไม่ขอซ้ำ

การเตรียม draft, code, benchmark configuration, demo, PR หรือแพ็กเอกสารที่ย้อนกลับได้ ไม่ควรกลายเป็น approval step เพิ่มโดยไม่มีเหตุผลเฉพาะ

### 2.4 สิ่งที่ต้องบันทึกแทนการถาม

บันทึก assumption เมื่อเลือก default ที่ไม่เสี่ยงต่อสิทธิ์หรือความถูกต้องของข้อสรุป ตัวอย่าง: เลือก cutoff สำหรับ development, เลือกรูปแบบ UI, เลือก export format หรือเลือก seed ของ fixture

ก่อน final evaluation ต้องตรึงค่าที่มีผลต่อ scientific inference เช่น cohort, splits, primary endpoint และ acceptance margin โดย agent สามารถจัดทำ protocol และบันทึกได้ ไม่ต้องรอ owner อนุมัติทุก parameter เว้นแต่มีข้อกำหนดเฉพาะ

## 3. สถานะและความหมายของความสำเร็จ

ใช้สถานะที่อธิบายการทำงานได้ตรง:

| สถานะ | ความหมาย |
|---|---|
| READY | Inputs และ authorization เพียงพอสำหรับเริ่ม work package |
| ACTIVE | กำลังทำงานที่ระบุขอบเขตชัดเจน |
| PARTIAL | มีผลส่งมอบที่ใช้ต่อได้ แต่ยังไม่ครบ outcome |
| COMPLETE | มีหลักฐานตาม definition of done ของ outcome นั้น |
| BLOCKED_LOCAL | Dependency เฉพาะงานยังไม่พร้อม; ต้องมีงานอิสระถัดไป |
| NOT_RUN | ยังไม่มี execution สำหรับ setting ที่กล่าวถึง |
| NOT_VALIDATED | ยังไม่มีหลักฐานยืนยัน claim ด้านผู้ใช้ ตลาด หรือผลวิจัยนั้น |
| SUPERSEDED | เปลี่ยนทิศทางแล้ว แต่รักษาหลักฐานเก่าไว้ |

อย่านำคำว่า PASS จาก unit tests หรือ mock workflow ไปใช้เป็นหลักฐานว่า HealthTech research, customer value หรือ clinical/legal claim ผ่านแล้ว

### 3.1 Evidence ที่ต้องแยก

- **Engineering evidence:** code ทำงานตาม contract, schema/IDs/versioning และ failure handling ถูกต้องตาม checks
- **Scientific evidence:** ผลจาก declared dataset/protocol พร้อม raw outputs และ uncertainty ที่เหมาะสม
- **Product evidence:** ผู้ใช้ทำงานที่ตั้งใจได้และภาระแก้ไขที่วัดได้
- **Commercial evidence:** การใช้ซ้ำ การซื้อ และต้นทุนส่งมอบจริง
- **External outcome:** peer-review acceptance หรือการตัดสินใจของหน่วยงานภายนอก ซึ่ง agent รับประกันไม่ได้

การส่ง paper ไม่ต้องรอรายได้ระดับธุรกิจใหญ่ การเปิด demo ไม่ต้องรอ journal acceptance และการที่ยังไม่มี paid pilot ไม่ควรหยุด engineering/research work ที่พร้อมทำ

## 4. สถานะตั้งต้นที่ต้องเข้าใจ

ตรวจ public repository ที่ commit **70805d30599dda723146390d39308c0faeb61ee7** ณ วันที่เอกสารนี้ มีพื้นฐาน typed records, source locators/versioning, SQLite repository, lexical retrieval/extraction, deterministic workflows, adaptation interfaces, product contracts และ provider/budget infrastructure

ยังไม่ควรถือว่ามี validated HealthTech app, medical-device adapters ครบ, completed scientific pilot, measured customer ROI หรือ journal-ready experimental results

Existing adaptation engine มีลักษณะ full generation แล้ว scoped merge ในบางเส้นทาง จึงห้ามใช้ชื่อ adaptation ไปอ้างว่าได้ประหยัด generation cost แล้ว หรือถือว่าเป็น adaptive evidence acquisition ที่แผนนี้จะทดลอง

Bridge release audit มีข้อมูลเบื้องต้นแล้ว แต่ยังต้องกระทบยอด cohort, rights และ independent evaluation protocol ไม่ต้องหยุดงาน SciFact, public facts, schemas, evaluator scaffolding, UI หรือ public-case preparation เพราะ dependency นี้

## 5. Goal cards

### HT-G0 — มี product และ research contract เดียวกัน

**Outcome:** ทุกคนอธิบายได้ว่าใครใช้แฟ้ม ใช้ก่อนทำอะไร และ paper ประเมินขั้นตอนใดของ workflow

**ผลส่งมอบขั้นต่ำ:** product contract, research questions, input/output schema และ public-case briefs 3 กรณีที่มี public identifiers หรือแหล่งจริง

**Definition of done:** มีหนึ่ง workflow เริ่มต้นที่ครอบคลุม named device/comparator → evidence shortlist → dossier → next information requests; ระบุข้ออนุมานและสิ่งที่ยังไม่วัดชัดเจน

**Agent ทำเอง:** เลือก public cases ที่เปิดแหล่งข้อมูลได้ กำหนด fields และจัดตัวอย่าง report ไม่ต้องรอ owner เลือกคำหรือสีทุกจุด

**เมื่อข้อมูลบาง case ไม่พร้อม:** เปลี่ยน case ที่ยังรักษา task เดิม อย่าขยายไปทุก Medical/Pharma/Biologics พร้อมกัน

**หลักฐาน:** schema/briefs และ walkthrough ที่มี source references; buyer demand ยังเป็น NOT_VALIDATED จนมีข้อมูลผู้ใช้

**สถานะตั้งต้น:** Contract ออกแบบแล้ว; public-case execution และ demand validation ยังต้องทำ

### HT-G1 — มีข้อมูลที่ใช้ได้ตามสิทธิ์และรองรับคำถามวิจัย

**Outcome:** เลือก corpus/cohort ได้อย่างมีเหตุผล แยก source facts, labels, completeness flags และ sampled non-gold pairs ถูกต้อง

**ผลส่งมอบขั้นต่ำ:** data/source registry, rights notes, hashes, canonical ID rules, cohort description และ split/group manifest ของ setting ที่จะรัน

**Definition of done:** ไฟล์อ่านและ join ได้, provenance ที่มี/ขาดบันทึกไว้, สิทธิ์ครอบคลุมการใช้ที่กำลังทำ, split ไม่ใช้ overlapping exports เป็น train/test อิสระ และ cohort ไม่ถูกเลือกเพราะทำให้ method ใหม่ชนะ

**งานสำคัญของ Bridge:** กระทบยอด 672 exported pairs/79 devices กับ 585 completeness-qualified pairs/74 devices และคำอธิบายใน paper; is_valid ไม่ใช่ relevance label; 87 excluded-completeness pairs ไม่ใช่ negatives; kg_linked ไม่ใช่ independent gold

**Agent ทำเอง:** ตรวจ metadata, schema และ ID types; สร้าง audit/split tooling; เลือกแหล่งที่มีสิทธิ์ชัดสำหรับงานอิสระ; หลีกเลี่ยง ontology หรือ dependency ที่ไม่จำเป็นหากสิทธิ์ยังไม่พร้อม

**เมื่อ Bridge ยังไม่พร้อม:** ตั้งเฉพาะ main Bridge experiment เป็น BLOCKED_LOCAL; ทำ SciFact evaluator, FDA facts adapter, dossier workflow และ prototype baselines บน permitted fixtures ต่อ หากต้องใช้แหล่งใหม่เป็นงานวิจัยหลัก ให้ปรับ task/claim ให้ตรงก่อน ไม่แอบแทน labels ด้วย LLM judgments

**Owner involvement:** เฉพาะการติดต่อผู้ให้ข้อมูล/รับเงื่อนไข/ค่าใช้จ่ายที่ยังไม่ได้อนุญาต โดยเตรียมข้อความและข้อสงสัยให้ครบก่อน

**สถานะตั้งต้น:** PARTIAL; audit บางส่วนเสร็จจากรอบก่อน ยังไม่ใช่ rights-cleared main benchmark

### HT-G2 — มี baseline และ evaluator ที่เชื่อถือได้

**Outcome:** ผลของวิธีพื้นฐานคำนวณซ้ำได้ และรู้ว่ามีพื้นที่ให้ศึกษา adaptive method หรือไม่

**ผลส่งมอบขั้นต่ำ:** baseline configurations, evaluator, raw ranked IDs, per-device results, cost records และ development analysis

**Definition of done:** ทุก method ใช้ corpus/cohort/output cutoff ที่เทียบกันได้; cost รวม controller และ query generation; failures อยู่ใน denominator ตาม protocol; evaluator อ่าน gold แยกจาก runtime; statistics ใช้ device/group เป็นหน่วยที่เหมาะสม

**Agent ทำเอง:** เริ่ม company/lexical และ hybrid baseline ก่อน เพิ่ม complexity เมื่อมีคำถามที่ต้องตอบจริง ใช้ development data เลือกค่า default และตรึงก่อน held-out evaluation

**ถ้าติด dense model หรือ paid API:** รัน lexical/metadata baseline และ evaluator validation ที่ทำได้ต่อ อย่าเรียก configuration ที่ยังไม่ได้รันว่าผลทดลอง

**ถ้า simple baseline ปิด headroom:** ใช้ผลนี้ปรับ research question; product สามารถใช้วิธีง่ายได้ ไม่จำเป็นต้องทำให้ agent เป็นผู้ชนะ

**สถานะตั้งต้น:** NOT_RUN สำหรับ HealthTech scientific setting

### HT-G3 — ได้ dossier workflow ที่ใช้ทำงานต่อได้

**Outcome:** ผู้ใช้เริ่มจาก public device/comparator แล้วได้แฟ้มที่ตรวจ แก้ไข และส่งต่อได้

**ผลส่งมอบขั้นต่ำ:** 3 complete public-case dossiers, source viewer, editable evidence table, export, unresolved-items section และ project history

**Definition of done:** facts สำคัญมี source/version/locator; associations แยก disclosed จาก retrieved candidates; UI แสดงภาษา/สถานะที่เข้าใจได้; source failure มีสถานะจริง; ผู้ใช้ไม่ต้องเริ่มรวบรวมแฟ้มใหม่จาก search hits ทั้งหมด

**Agent ทำเอง:** ใช้ engine ที่พร้อมที่สุด ไม่ต้องรอ adaptive experiment ชนะ; reuse typed records และ product contracts; สร้าง minimal no-code journey ก่อนเพิ่ม dashboard ที่ไม่ช่วยงานหลัก

**ถ้าข้อมูลหนึ่งประเภทขาด:** แสดง unresolved พร้อมสิ่งที่ควรขอเพิ่ม และส่งมอบส่วนที่มีหลักฐานแล้ว ห้ามเติมคำตอบที่ดูสมจริงแทนข้อมูลจริง

**Owner involvement:** ขอ feedback เมื่อมีตัวอย่างที่เปิดตรวจได้แล้ว รวมคำถามเป็นชุดเล็ก ไม่หยุดรอความเห็นต่อทุก component

**สถานะตั้งต้น:** Existing foundations มีแล้ว; HealthTech end-to-end workflow ยังไม่ implemented/validated

### HT-G4 — ได้ผลวิจัยที่ตอบคำถาม adaptive acquisition อย่างตรงไปตรงมา

**Outcome:** รู้ว่า adaptive policy ให้ประโยชน์ที่เงื่อนไขใด เมื่อเทียบกับ fixed และ simple adaptive baselines

**ผลส่งมอบขั้นต่ำ:** frozen protocol, held-out results, quality–cost curves, ablations ที่จำเป็น, group-level intervals และ error analysis

**Definition of done:** มีผลตาม primary endpoint ที่กำหนดก่อน test; เปรียบเทียบทรัพยากรอย่างเป็นธรรม; แยกผลของ company/entity signals, action order และ stopping ตามคำถามที่ตั้ง; รายงาน null/negative findings และ limitations

**Success criterion:** เลือก quality gain at matched budget หรือ cost reduction under predeclared quality margin โดยอิง development variability แล้วตรึงก่อน final test ห้ามเลือก outcome หลังเห็นผลเพื่อให้ผ่าน

**Agent ทำเอง:** เริ่ม bounded policy และ action set เล็ก; คง generator/reranker ให้เหมือนกันเมื่อทดสอบ controller; ใช้ development-only oracle เพื่อดู headroom ได้โดยติดป้าย diagnostic

**ถ้า adaptive ไม่ชนะ:** ส่งผลและเหตุผลที่ตรวจได้ ใช้วิธีที่เหมาะใน product และประเมินว่ามี patent-information finding ที่เพียงพอสำหรับ manuscript หรือไม่ ไม่บิดผลหรือเพิ่ม test runs ไปเรื่อย ๆ เพื่อหาชัยชนะ

**สถานะตั้งต้น:** NOT_RUN

### HT-G5 — ได้หลักฐานคุณค่าต่อผู้ใช้และทิศทางรายได้

**Outcome:** รู้ว่าผู้ใช้ทำงานต่อได้จริง แฟ้มช่วยหรือเพิ่มภาระตรงไหน และมีคนซื้อบริการส่วนใด

**ผลส่งมอบขั้นต่ำ:** task script, public-case demo, feedback/results record, correction burden, repeat-use record และ bounded pilot offer

**เริ่มได้ทันทีเมื่อ HT-G3 มีตัวอย่าง:** เตรียม usability tasks และ offer โดยไม่ต้องรอ HT-G4 จบ การเตรียมเหล่านี้ไม่ต้องมีข้อมูลภายในองค์กร

**Usability evidence:** ผู้ใช้เปิดหาหลักฐาน เปรียบเทียบข้อมูล แก้แฟ้ม และเตรียมคำขอข้อมูลได้; นับเวลารวมการตรวจ/แก้ ไม่รายงานเฉพาะเวลาที่โมเดลสร้างคำตอบ

**Commercial evidence:** มีการใช้กับ case ใหม่และ bounded paid pilot หรือ purchase ที่ตรวจได้; แยกการซื้อ software/workspace ออกจากการซื้อบริการคนทำรายงาน และบันทึก manual work ทุกส่วน

**ค่าเริ่มต้น discovery:** ใช้ผู้ใช้เป้าหมายอย่างน้อย 3 คนเป็นจุดเริ่มเรียนรู้ ไม่ตีความว่าเป็น sample size ที่พิสูจน์ตลาดทั้งหมด ไม่ต้องให้ผู้ใช้เหล่านี้สร้าง expert labels สำหรับ paper

**เมื่อยังไม่มีผู้ใช้:** ทำ demo, task script, comparison package และ offer ให้พร้อม; ตั้ง demand เป็น NOT_VALIDATED และทำ research/engineering ต่อ

**Owner involvement:** การแนะนำผู้ใช้หรืออนุญาต outreach เมื่อจำเป็น; agent ต้องเตรียมสิ่งที่จะส่งให้ตรวจได้ก่อน ไม่ส่งข้อความเองหากยังไม่มี authorization

**สถานะตั้งต้น:** NOT_VALIDATED

### HT-G6 — มี manuscript และ reproducible research release ที่พร้อมส่งพิจารณา

**Outcome:** ผู้ประเมินและผู้ใช้ repository ตรวจที่มาของข้อสรุปและทำซ้ำ setting ที่ประกาศได้

**ผลส่งมอบขั้นต่ำ:** manuscript draft, related-work matrix, configurations, evaluator, per-query results ที่เผยแพร่ได้, source/data/model/system cards, limitations และ citation metadata

**Definition of done:** paper มี patent-central research question; method comparisons ถูกต้อง; figures/tables สืบกลับไป raw output ได้; research code และ data rights แยกชัด; ไม่มี placeholder result หรือ claimed improvement ที่ไม่เคยรัน

**Agent ทำเอง:** เขียน introduction/method/data/protocol ที่ข้อเท็จจริงพร้อมแล้วก่อนผลทดลองได้ โดยติดป้ายส่วนผลที่ยัง NOT_RUN; จัด reproducibility package เป็นงานต่อเนื่อง ไม่รอจนเขียน paper เสร็จค่อยสร้าง provenance

**เมื่อผลยังไม่เพียงพอ:** ทำ manuscript ส่วนที่รองรับได้และระบุ experiment ที่เหลือเพียงชุดที่จำเป็น การมี PDF paper references จำนวนมากไม่เท่ากับ journal readiness

**เกณฑ์ venue:** ถ้าถอด patent component แล้วคำถามและผลหลักยังเหมือนเดิม ให้ทบทวน fit กับ WPI โดยรักษา research integrity ไม่เพิ่มศัพท์ patent เพื่อให้ดูเข้าวารสาร

**สถานะตั้งต้น:** Literature/documentation pack พร้อมเตรียมงาน; scientific results/manuscript readiness ยังต้องทำ

### HT-G7 — มีผลิตภัณฑ์ที่พร้อมติดตั้ง ใช้ และดูแล

**Outcome:** ผู้ใช้หรือผู้ดูแลรัน workflow ได้ตามคู่มือ เห็นสถานะงาน ค่าใช้จ่าย และข้อผิดพลาดที่แก้ไขได้

**ผลส่งมอบขั้นต่ำ:** no-code user journey, setup/deployment instructions ที่ตรงกับของจริง, configuration examples ที่ไม่มี secrets, logs ที่มีขอบเขต, backup/export path และ operational cost record

**Definition of done:** เส้นทางหลักทำงาน end-to-end บน environment ที่ระบุ; failed source/provider ไม่ทำข้อมูลหาย; versioned dossiers กลับมาเปิดได้; UI TH/EN สอดคล้อง; ไม่มีการแสดง synthetic demo เป็นผลวิจัยจริง

**Agent ทำเอง:** เลือก infrastructure ที่สอดคล้องกับของเดิมและ deployment target ที่ได้รับอนุญาต; เตรียม configuration และ deployable build ให้เสร็จก่อนขอ action ที่ต้องใช้อำนาจ owner

**เมื่อ deployment ยังไม่อนุญาต:** ส่ง local/staging artifact และ runbook ที่ตรวจได้ ทำ engineering/research ต่อ ความพร้อม deploy กับการ deploy จริงเป็นคนละสถานะ

**สถานะตั้งต้น:** Prototype foundations มีแล้ว; production HealthTech deployment ยังไม่ validated

### HT-G8 — ขยาย domain โดยรักษาความสอดคล้องของข้อมูลและธุรกิจ

**Outcome:** เพิ่มหนึ่ง vertical เมื่อมีงานของลูกค้าและ reference task ของ vertical นั้น

| Branch | งานที่พิจารณา | หลักฐานเริ่มต้น |
|---|---|---|
| Pharmaceutical | Patent evidence extraction / compound–experiment dossier | ChEMU และแหล่ง chemical/product data ที่ใช้ได้ตามสิทธิ์ |
| Biologics | Product/evidence monitoring และ factual dossier refresh | Purple Book snapshots; เปรียบเทียบ deterministic diff/full rebuild |
| IVD / analytical devices | Comparator/evidence workflow สำหรับอุปกรณ์กลุ่มนั้น | Official records และ task-specific reference data ที่ตรวจได้ |
| Thai regulatory context | Facts และ source versions ของหน่วยงานไทย | Official Thai sources; jurisdiction mapping ของตนเอง |

**Definition of done:** input/output/buyer/task/metrics ของ branch ใหม่ตรงกัน; ไม่ยืมผล cardiovascular เพื่ออ้างประสิทธิภาพใน domain ใหม่; data rights และ provenance ระบุได้

**Agent ทำเอง:** เตรียม source inventory และ prototype adapter แบบแยก module เมื่อเป็นงานที่พร้อมทำ แต่ไม่ขยาย main experiment จนขอบเขตกลายเป็นหลาย paper ในคราวเดียว

**สถานะตั้งต้น:** PLANNED; ไม่ใช่ prerequisite ของ core release

## 6. วิธีจัดการ blockers ให้เดินงานต่อได้

### 6.1 Local-blocker rule

ทุก BLOCKED_LOCAL record ต้องมี 5 ช่อง: affected task, reason, evidence, safe next action และ condition to resume

ตัวอย่าง:

| เหตุการณ์ | พักเฉพาะ | เดินต่อได้ |
|---|---|---|
| Bridge rights ยังไม่ชัด | การใช้/เผยแพร่ข้อมูลเกินสิทธิ์ที่ยืนยันได้ | SciFact, source schemas, FDA facts, UI, evaluator contracts |
| ไม่มี corpus ใหญ่เต็ม paper | Claim และ run ที่ต้องใช้ full corpus | Released-corpus study ที่ประกาศ universe ตรงตามจริง |
| ไม่มี dense model | Dense method ที่จำเป็นต้องดาวน์โหลด/จ่าย | Lexical/metadata baseline และ evaluator |
| Provider ใช้งานไม่ได้ | Runs ที่พึ่ง provider นั้น | Offline fixtures, parser, ranker, caching และ docs |
| ไม่มีผู้ใช้ทดสอบ | Customer-validation conclusion | Product demo, task script, research, export |
| Method ไม่ชนะ | Positive-improvement claim | Failure analysis, simpler product, revised research finding |
| Paper บางฉบับไม่มี PDF ที่ใช้ซ้ำได้ | การแนบ PDF ฉบับนั้น | Citation และอ่านจากแหล่งที่มีสิทธิ์; ใช้ related papers อื่นที่เกี่ยวข้องจริง |

### 6.2 Bounded investigation

หากวิธีเข้าถึง dependency เดิมล้มเหลวซ้ำ ให้ลองทางเลือกที่ต่างอย่างมีสาระ ไม่ทำคำสั่งเดิมวนหลายรอบ เมื่อยังไม่สำเร็จให้บันทึกแล้วเปลี่ยนไปงานอิสระ ไม่ใช้เวลาทั้งรอบกับ dependency เดียวโดยไม่มีผลใหม่

เกณฑ์นี้ลดการติดค้าง ไม่อนุญาตให้ข้าม access controls, เปลี่ยน permissions เอง, เดา credentials หรือปลอมผลสำเร็จ

## 7. Verification ที่พอดีกับความเสี่ยง

- แก้ข้อความ/diagram: ตรวจลิงก์ ความสอดคล้อง และการแสดงผล ไม่ต้องเพิ่ม test suite
- เปลี่ยน schema/parser: ตรวจ valid/invalid records ที่ตรงความเสี่ยงจริง
- เปลี่ยน retrieval/evaluator: ใช้ fixture ที่รู้ผลและตรวจ ID normalization, ranking, denominators, duplicates และ failure handling
- เปลี่ยน adaptive controller: ตรวจ budget cap, allowed actions, no-gold runtime และ deterministic logging
- เปลี่ยน scientific protocol: ตรวจ split/cohort/cost/metric ก่อน final run; หลีกเลี่ยง tuning บน test
- เปลี่ยน UI/workflow: ตรวจเส้นทางหลักที่ผู้ใช้ทำจริงและผลเมื่อ source/provider ล้มเหลว

รัน targeted checks ให้เพียงพอ แล้วหยุด optional testing เมื่อไม่เหลือความเสี่ยงเฉพาะที่ต้องแก้ ไม่เพิ่ม checks ที่เพียงสะท้อน implementation หรือทำให้การส่งมอบหยุดโดยไม่มีประโยชน์

## 8. Definition of project progress

โครงการก้าวหน้าเมื่อได้ผลส่งมอบที่ใช้ต่อได้ เช่น adapter ที่อ่าน source จริงได้, evaluator ที่ตรวจข้อผิดพลาดได้, dossier ที่ตรวจแหล่งได้, experiment ที่ตอบคำถาม หรือข้อมูลผู้ใช้ที่ทำให้ตัดสินใจได้ดีขึ้น

ไม่ใช้จำนวน commits, agent messages, simulated cases, PDF references, GitHub stars หรือคำชม demo เป็นตัวแทน scientific/commercial validation

### 8.1 สิ่งที่ agent ต้องส่งทุกครั้ง

ใช้รายงานสั้นที่อ่านแล้วรู้ว่าจะทำอะไรต่อ:

1. **Outcome:** ทำอะไรเสร็จและช่วยเป้าหมายใด
2. **Evidence:** path/command/source/result ที่ตรวจได้
3. **Remaining:** สิ่งที่ยังไม่รู้หรือยังไม่รัน
4. **Blocker:** เฉพาะ dependency ที่ยังติด พร้อมขอบเขตผลกระทบ
5. **Next:** งานพร้อมทำถัดไป
6. **Owner decision:** ใส่เฉพาะเมื่อมีการตัดสินใจที่ owner ต้องทำจริง

อย่าส่งเพียง “พร้อมให้ตรวจ” หรือ “รออนุมัติให้ทำต่อ” เมื่อยังมีงานที่ได้รับอนุญาตให้ทำได้

## 9. ข้อมูลและการเผยแพร่

Repository ที่ public ไม่ได้แปลว่ามี open-source license โดยอัตโนมัติ จาก snapshot ที่ตรวจยังไม่พบ root LICENSE จึงต้องแสดงสถานะตามจริง และเตรียมตัวเลือก license ให้ owner ตัดสินใจเมื่อจำเป็นต่อการเผยแพร่สิทธิ์

Paper PDFs, datasets, source records, software, model weights และ generated artifacts มีสิทธิ์คนละส่วน ห้ามนำ license ของ paper ไปครอบ dataset หรือ copy raw data ที่ไม่มีสิทธิ์เข้า repository

แพ็กเอกสารนี้แนบ papers ตาม source/license metadata ของแต่ละไฟล์ ไม่มีการโอนสิทธิ์ของผู้เขียนหรือ publisher และไม่มีการรวม raw Bridge dataset, private organization data, patient data, credentials หรือ model keys

## 10. การใช้เอกสารนี้กับ agent ตัวถัดไป

ส่ง task ที่มี outcome และ constraints สั้น ๆ เช่น:

> อ่าน GOAL.md sections 0–4 และ PLAN.md ที่เกี่ยวข้อง ตรวจ repository ปัจจุบัน แล้วเลือกหนึ่ง HT-W ที่พร้อมทำเพื่อให้ได้ end-to-end public-case dossier ใช้ existing authorization และงบที่บันทึกไว้ ทำงานย้อนกลับได้และ targeted checks เอง หาก dependency ติดให้พักเฉพาะงานนั้นแล้วทำงานอิสระต่อ ส่ง evidence และ next action ที่ชัดเจน ห้ามอ้างผลทดลองที่ยังไม่ได้รัน

Agent ไม่ต้องอ่าน PDF ทั้งหมดก่อนเริ่มทุกงาน ให้ใช้ reading routes ใน RELATED_PAPERS.md และเปิดเฉพาะ papers ที่มีผลกับการตัดสินใจปัจจุบัน เมื่อจะ implement หรืออ้างรายละเอียด method จึงอ่านส่วนที่เกี่ยวข้องจากต้นฉบับ

**เป้าหมายของเอกสารชุดนี้คือให้ agent รับภาระการเตรียม ลงมือ ตรวจ และแก้ปัญหาแทน owner โดยรักษาข้อเท็จจริงของงานให้ชัดเจนและเดินหน้าได้ต่อเนื่อง**

## Migration support records — 27 October 2026

แหล่งข้อมูลเสริมที่เสนอเพื่อรองรับ goals เดิม: [supplemental data](docs/healthtech/research/SUPPLEMENTAL_DATA.md) สถานะ implementation จริง: [coverage](docs/healthtech/MIGRATION.md) ข้อเสนอนี้ไม่เปลี่ยน scientific thesis, success criteria หรือ product scope ในเอกสารนี้
