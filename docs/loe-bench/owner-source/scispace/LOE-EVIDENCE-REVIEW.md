# LOE-Bench: การทบทวนหลักฐานงานวิจัยและชุดข้อมูล (literature and dataset evidence review)

วันที่เก็บหลักฐาน: 2026-11-27 · ไม่ใช่ความเห็นทางกฎหมายหรือทางคลินิก · ภาษา: ไทย (ชื่อฟิลด์ ตัวระบุ และหัวตารางคงเป็นอังกฤษ)

## 0. ข้อตกลงการอ่านรายงาน

- **UNVERIFIED** = ผมอ่านไม่ถึงข้อความนั้นจริง (เช่น เข้า full text ไม่ได้, หน้าเว็บไม่ระบุวัน) จึงไม่ยืนยัน และไม่เดา
- **"abstract-only"** = อ่านได้เฉพาะบทคัดย่อ/หน้า landing page ดังนั้น locator ระดับหน้า/ตาราง/รูป = UNVERIFIED
- locator ที่ให้ (เช่น "§3.3", "Fig 6", "p.4") มาจากไฟล์ที่ผมอ่านเองจริงเท่านั้น
- **บทความ vs. abstract**: แยกชัดในตารางที่ 1 คอลัมน์ "ระดับที่อ่าน"
- **ไม่นับ cohort ซ้ำ**: งานของกลุ่ม FDA OGD (CPT 2019, TIRS 2020, CTS 2025) และกลุ่ม Beall–Darrow–Kesselheim (VIH 2018, JLME 2019, CPT 2020) อาจใช้ประชากรซ้อนกัน การซ้อนจริง = UNVERIFIED จึงนับเป็น "กลุ่ม cohort" ไม่ใช่ผลวิจัยอิสระ รวมแล้วเห็นเป็น 8 กลุ่ม cohort ที่ดูเหมือนแยกกัน (FDA OGD; Beall; Kerr–Glos; Murimi-Worstell; HSR 1997; Hemphill–Sampat; Rome; Son)
- **ข้อยกเว้นเชิงออกแบบ**: ไม่ใช้ FDA First Generic list เป็น predictor; ไม่ใช้ hindsight features (การอนุมัติภายหลัง, วัน challenge ที่ backfill, ผลคดีภายหลัง, หน้าต่างยอดขายที่ผูกกับเหตุการณ์อนาคต) ดู §5
- วันอนุมัติ, claims period หรือวันยื่น **อย่างเดียว** ไม่พิสูจน์ว่าระเบียนนั้นสาธารณะเมื่อใด (พิสูจน์ด้วยตัวเลขใน §4.3)

### การเข้าถึงที่ล้มเหลว (รายงานตรงๆ)
| งาน | สิ่งที่เกิด | ผลต่อรายงาน |
|---|---|---|
| CPT 2019, 10.1002/cpt.1479 | full text ปิด (closed access); อ่านได้เฉพาะ abstract (Europe PMC, PMID 31009066) | วิธีวิทยา/ตัวเลข/locator = UNVERIFIED |
| JLME 2019, 10.1177/1073110519840499 | ปิด; ไม่มี abstract; เห็นเฉพาะ landing page + reference list | วิธีวิทยา/ผล = UNVERIFIED |
| VIH 2018, 10.1016/j.jval.2018.04.1827 | publisher บล็อก (curl 403, Cloudflare check, scrape timeout) ผมไม่ได้พยายามเลี่ยง | อ่านเฉพาะ abstract (Europe PMC, PMID 30502781) |

---

## 1. Q1: งานที่ทำนายเวลาไปถึง submission / challenge / approval / launch

### 1.1 อนุกรมวิธาน endpoint และ time origin (ห้ามเทียบข้ามกลุ่มตรงๆ)

| กลุ่ม | endpoint | time origin ที่พบ | งานที่เป็นตัวอย่าง |
|---|---|---|---|
| E1 | วัน first ANDA submission | ELASD (earliest lawful ANDA submission date) = 4 ปีหลังอนุมัติ RLD ของ NCE; non-NCE = วันอนุมัติ RLD หรือ ELASD+1 ปี | CPT 2019 (abstract), TIRS 2020, CTS 2025 |
| E2 | วัน first generic approval | วันอนุมัติของ NME/brand | Kerr–Glos 2020 (abstract), Murimi-Worstell 2019 (ตัวแปรหนึ่ง) |
| E3 | วัน generic/biosimilar entry (market) หรือ "exclusivity period" | brand launch/approval (**UNVERIFIED** สำหรับ Beall) | Beall 2018/2019/2020, Rome 2021 |
| E4 | ความน่าจะเป็น/เวลาเกิด Paragraph IV challenge | ยอดขาย/พอร์ตสิทธิบัตร (abstract-only) | Hemphill–Sampat 2011 |
| E5 | เวลาระหว่าง generic ตัวที่ 2→3, จำนวนผู้ผลิต | วันอนุมัติ generic ตัวที่ 2 | Murimi-Worstell 2019 |
| E6 | เวลา brand→generic ในเกาหลี (non-US) | วันอนุมัติ originator | Son 2021 |

**ไม่พบ** งานต้นฉบับที่ทำนายเวลา biosimilar entry ด้วย survival model; หลักฐาน biosimilar ในชุดนี้มีเฉพาะ deterministic clock ของ Beall 2020 (abstract-only) จึงสอดคล้องกับการกำหนด biosimilar เป็น track เชิงพรรณนา

### 1.2 Trace สามงานหลักไปยัง primary records

| งาน | primary record (ที่เข้าถึงได้) | สิ่งที่ยืนยันได้ | UNVERIFIED |
|---|---|---|---|
| CPT 2019 (10.1002/cpt.1479) Hu M, ... Zhao L; Clin Pharmacol Ther 2019;106(1):174-181; PMID 31009066 | Europe PMC record (epmc_31009066.json) | endpoint = เวลาถึง first ANDA submission ของ NCE หลัง ELASD; inputs = ข้อมูลผลิตภัณฑ์, ปัจจัยกำกับดูแล, ปัจจัย pharmacoeconomic; random survival forest vs Cox; abstract ระบุ "internal and external validations" และ ML ดีกว่า Cox | กติกาแบ่ง external validation (เวลา? สุ่ม?), ตัวเลข C-index, locator |
| VIH 2018 (10.1016/j.jval.2018.04.1827) Beall, Darrow, Kesselheim; Value Health 2018;21(12):1382-1389; PMID 30502781 | Europe PMC abstract (epmc_30502781.json) | deterministic clock: key patent = patent ที่มี PTE ไม่เช่นนั้นคือสิทธิบัตรแรกที่หมดอายุใน FDA patent register, บวก pediatric/exclusivity อื่น, จัดชนิด active-ingredient vs secondary; ทดสอบกับ 170 ยาขายดีที่สูญ exclusivity 2000–2012; median predicted 12.5 ปี (IQR 7.25–14.5) vs actual 12.5 (8.5–14.75); active-ingredient 131 (77%): 12.25 vs 13.0; secondary-only 38 (22%): 16.0 vs 8.25 (ประเมินสูงเกิน) | time origin (น่าจะ brand launch/approval), เวอร์ชันของ patent register, ฐานข้อมูล entry จาก Medicaid (derived/closed), locator ตาราง |
| JLME 2019 (10.1177/1073110519840499) Beall, Darrow, Kesselheim; J Law Med Ethics 2019;47(1):177-182; PMID 30994060 | landing page + reference list (jlme2019_beall.md) | มีอยู่จริงและเป็นงานของกลุ่มเดียวกัน | วิธีวิทยา/ผล/ประชากร ทั้งหมด |

### 1.3 ตารางที่ 1: งานศึกษา (Table 1)

คำอธิบายสั้น: "as-of" = สร้างฟีเจอร์จาก snapshot ที่สาธารณะ ณ cutoff หรือไม่; "forward time-split" = ฝึกช่วงเวลาก่อน ทดสอบช่วงหลัง (ไม่ใช่ CV แบบสุ่ม)

| # | Citation (ระดับที่อ่าน) | DOI / link | Endpoint & time origin | Population & exclusions | Data & features | Method & comparator | Metric & reported result | As-of reconstruction | Forward time-split | Censoring | Unit of splitting |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Hopefl R, et al. Clin Transl Sci 2025;18(10):e70365 (full text) | 10.1111/cts.70365; PMC12497357 | first ANDA submission; time zero: NCE = ELASD (4 ปีหลัง NDA), non-NCE = ELASD+1 ปี (§3.1) | orphan drug products; NCE n=140, non-NCE n=97 (leave-one-out, §4.2) | FDA Orphan DB, Orange Book, FDA internal complexity designation (closed), PSG dates, IQVIA sales 2011–2023 (closed); ตัวแปรใน Table 1; sales และ PSG availability ใช้ค่า 1 ปีก่อน ELASD (§3.1) | random survival forest; เทียบ Cox PH/AFT (§3.4, §4.3, Fig 6) | repeated 5-fold CV C-index: NCE 0.675±0.0261, non-NCE 0.754±0.0441; leave-one-out cumulative C-index 0.769 (NCE), 0.736 (non-NCE); **RSF ต่ำกว่า Cox PH/AFT ใน NCE, สูงกว่าใน non-NCE** (Fig 6) | **UNCLEAR/บางส่วน**: sales/PSG lag 1 ปีก่อน ELASD (§3.1) แต่ไม่ระบุ edition/snapshot ของ Orange Book → ไม่ยืนยัน | **YES**: แบ่งตามวัน NDA approval; NCE train 2008–2018/test 2018–2020 C-index 0.900; non-NCE train 2011–2021/test 2021–2023 C-index 0.814 (§3.3, §4.2.1/4.2.2; Fig S6A/B) | right-censored ที่วันสังเกตสุดท้าย | ผลิตภัณฑ์/NDA (ไม่ใช่ drug family; clustering ไม่ระบุ = UNVERIFIED) |
| 2 | Wittayanukorn S, et al. Ther Innov Regul Sci 2020;54(6):1372-1381 (full text) | 10.1007/s43441-020-00163-x; PMC12931830 | first ANDA submission; index = potential lawful submission date: NCE = 4 ปีหลังอนุมัติ RLD (สมมติ Paragraph IV), non-NCE = วันอนุมัติ RLD (Cohort Creation) | 400 drug families จาก 4,308 หลังตัด 3,908 (eFigure 1); NCE 140 (32.86%), non-NCE 260; index 1/1/2011–31/12/2017; ตัด: ไม่มีข้อมูลยอดขาย, ย้ายไป Discontinued Section, non-505(j) | Orange Book (สาธารณะ), FDA internal ANDA submission data (ปิด), PSG, NDC, REMS, IQVIA National Sales Perspective (ปิด); eTable 1 | Cox multivariable แยก 2 โมเดล, stepwise (SAS 9.4); sensitivity: จำกัดยอดขายที่ปี 4 หลังอนุมัติ | NCE: sales >$250M HR 4.74 (1.85–12.13); $100–250M HR 3.63 (1.31–10.08); complex HR 0.51 (0.26–0.99). non-NCE: PSG available HR 3.84 (1.86–7.91); sales $100–250M HR 2.40 (1.09–5.25); complex HR 0.62 (0.39–0.98) (Fig 3, Fig 4). P(ไม่มี ANDA) ที่ 1 และ 5 ปี: NCE 46.36%/22.66% (Fig 1); non-NCE 84.23%/51.89% (Fig 2) | **UNCLEAR**: ไม่พบการระบุ snapshot ของ Orange Book; ตำแหน่งหน้าต่างยอดขายเทียบ index = UNVERIFIED | **NO** (งาน association ไม่มี validation split) | censor ที่ submission หรือสิ้นสุดการศึกษา; follow-up เฉลี่ย 20.69 (2.29) เดือน NCE, 46.58 (1.75) เดือน non-NCE | drug family (ไม่ได้ cluster ใน Cox; ไม่ระบุ = UNVERIFIED) |
| 3 | Hu M, et al. Clin Pharmacol Ther 2019;106(1):174-181 (**abstract-only**) | 10.1002/cpt.1479; PMID 31009066 | first ANDA submission ของ NCE; origin = ELASD | UNVERIFIED | drug product info, regulatory factors, pharmacoeconomic factors (รายละเอียดฟีเจอร์ UNVERIFIED) | random survival forest vs Cox; "internal and external validations" | abstract ไม่มีตัวเลข; ML ดีกว่า Cox | UNVERIFIED | **UNVERIFIED** ("external validation" ไม่ระบุว่าแบ่งตามเวลา) | UNVERIFIED | UNVERIFIED |
| 4 | Beall RF, Darrow JJ, Kesselheim AS. Value Health 2018;21(12):1382-1389 (**abstract-only**) | 10.1016/j.jval.2018.04.1827; PMID 30502781 | เวลาถึง generic entry/สิ้นสุด market exclusivity; origin น่าจะ brand launch/approval (**UNVERIFIED**) | 170 ยาขายดีที่สูญ exclusivity 2000–2012 | FDA patent register + PTE + pediatric/exclusivity; ฐานข้อมูล entry มาจาก Medicaid (derived/closed) | deterministic patent clock; เทียบกับ entry จริง (ไม่มี model เปรียบเทียบ) | median predicted 12.5 vs actual 12.5 ปี; active-ingredient (131): 12.25 vs 13.0; secondary-only (38): 16.0 vs 8.25 | **NO/UNCLEAR**: ใช้ patent register (น่าจะเป็นสถานะปัจจุบัน; UNVERIFIED) | **NO** (ทดสอบเชิงพรรณนาย้อนหลัง) | UNVERIFIED | ยา (drug) |
| 5 | Beall RF, Darrow JJ, Kesselheim AS. J Law Med Ethics 2019;47(1):177-182 (**ไม่มี abstract**) | 10.1177/1073110519840499; PMID 30994060 | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| 6 | Beall RF, et al. Clin Pharmacol Ther 2020;108(6):1308-1314 (**abstract-only**) | 10.1002/cpt.1981 | expected vs observed generic/biosimilar entry; origin UNVERIFIED | 328 ยาอนุมัติ 2000–2012 (biosimilar expected n=60; generic n=268) | deterministic clock จากสิทธิบัตร/exclusivity | clock vs entry สังเกตได้ถึงปี 2019 | expected biosimilar median 12.3 ปี (IQR 12.0–14.0); generic 12.2 (8.4–14.0); observed entry biosimilar 3/25 (12%), generic 101/155 (65%) ถึง 2019 (คำเตือนเรื่อง hindsight ในงานเอง) | UNVERIFIED | NO (descriptive) | observed entry ถึงปี 2019 (right-censoring โดยนัย) | ยา |
| 7 | Kerr KW, Glos LJ. Pharm Med 2020;34(1):19-29 (**abstract-only**) | 10.1007/s40290-019-00317-9 | เวลาจากอนุมัติถึง first generic approval | NME อนุมัติ 2001–2012 | NME approvals report, Orange Book, Orphan DB, Drugs@FDA, IQVIA NSP (ปิด) | Cox | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| 8 | Murimi-Worstell IB, et al. PLoS ONE 2019;14(11):e0225109 (full text) | 10.1371/journal.pone.0225109 | (a) มี generic ใดๆ (GEE); (b) เวลาจาก generic ตัวที่ 2→3 (Cox; 508 ยาที่มี ≥2 generics; p.4); (c) จำนวนผู้ผลิต | 982 ผลิตภัณฑ์ Rx อนุมัติ 1982–3 เม.ย. 2018 (Fig 1, p.3). ตัดจาก 3,959: ก่อน 1982 = 1,552; LOE ก่อน 1998 = 402; monograph 133; ยังมีสิทธิบัตร 359; จับคู่ IQVIA ไม่ได้ 332; ไม่มี therapeutic class 145; OTC/discontinued 47 | IQVIA World Review 1997–2016 (ปิด/ซื้อ; Data Availability p.1), Orange Book | GEE; Cox; cluster ตาม therapeutic class (p.4) | Tables 1–2 (p.6) (ค่าเฉพาะไม่ได้สกัดเข้ารายงานนี้) | **NO** (การคัดออก "ยังมีสิทธิบัตร" = hindsight selection) | **NO** | ติดตามถึง generic ตัวที่ 3 หรือ 3 เม.ย. 2018 | ผลิตภัณฑ์; cluster = therapeutic class |
| 9 | Hemphill CS, Sampat BN. J Empir Legal Stud 2011;8(4):613-649 (**abstract-only**) | 10.1111/j.1740-1461.2011.01235.x | โอกาสเกิด Paragraph IV challenge (E4) | UNVERIFIED | ยอดขาย, พอร์ตสิทธิบัตร | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| 10 | Drug patent expirations and the speed of generic entry. Health Serv Res 1997 (เข้าถึงแบบเปิด) | ไม่มี DOI (UNVERIFIED link) | เวลาถึง generic entry หลังสิทธิบัตรหมด | 81 ยาที่สูญสิทธิบัตร 1987–1994 | Orange Book **ฉบับลงวันที่ 1986–1989** (กรณีเดียวที่ใกล้ as-of), จำนวน ANDA pending จากรายงาน OGD, ยอดขาย Pharmaceutical Data Services/Walsh-America (ปิด) | Cox | ยอดขายสัมพันธ์เชิงลบกับเวลาถึง generic entry | **PARTIAL**: ใช้ edition ลงวันที่ | NO | UNVERIFIED | ยา; locator ระดับหน้า = UNVERIFIED |
| 11 | Rome BN, Lee CC, Kesselheim AS. CPT 2021;109(2):367-371 (**abstract-only**) | 10.1002/cpt.1983 | ระยะ market exclusivity ที่มีคู่แข่งใหม่ 2012–2018 | 264 small-molecule + 4 biologic | ข้อมูล claims | เชิงพรรณนา | median exclusivity 21.5 vs 14.4 ปี (P=0.02) | UNVERIFIED | NO (descriptive) | UNVERIFIED | ยา |
| 12 | Son K-B. Front Public Health 2021;9:654952 (อ่านแล้ว; **non-US**) | 10.3389/fpubh.2021.654952 | เวลา originator→generic (เกาหลีใต้) | 2,061 คู่ originator–generic, originator อนุมัติ 2000–2013; HIRA/MFDS | ข้อมูลเกาหลี | KM, log-rank, Cox (Table 3 แบบง่าย; Table 4 ขยาย) | UNVERIFIED (ไม่ได้สกัดตัวเลข) | NO | NO | right-censored | คู่ originator–generic |

**ไม่นำมาใช้เป็นหลักฐาน predictor:** JHPPL 2026 (10.1215/03616878-12513812) เพราะ "ผลคดี" คือ hindsight feature; Kumar V et al. TIRS 2023 (10.1007/s43441-023-00562-w) ไม่เห็น abstract; PLOS Med 2023 (10.1371/journal.pmed.1004309, insulin patents) ไม่ได้อ่าน; CPT 2021 (10.1002/cpt.2322) เชิงพรรณนาเรื่องต้นทุน; JAMA Intern Med 2026 (10.1001/jamainternmed.2026.0980) ไม่เห็น abstract (ชื่อเรื่องบ่งชี้เรื่อง delisting สิทธิบัตรที่ FTC ท้าทาย แต่ไม่พึ่งพา)

### 1.4 ข้อสังเกตจาก Table 1

1. **มี forward time-split จริงเพียงงานเดียวที่อ่านเต็ม (CTS 2025)**; CPT 2019 = UNVERIFIED; ที่เหลือเป็น association หรือ descriptive
2. **ไม่มีงานใดที่ยืนยันได้ว่าทำ as-of reconstruction เต็มรูป**; ที่ใกล้ที่สุดคือ HSR 1997 (Orange Book ลงวันที่) และ CTS 2025 (lag ตัวแปรยอดขาย/PSG 1 ปี) ซึ่งเป็นช่องว่างที่ LOE-Bench เติมได้
3. **ตัวทำนายหลักที่ซ้ำกัน** = ยอดขาย (HR สูงเมื่อยอดขาย >$100–250M), PSG availability, ความซับซ้อนของผลิตภัณฑ์ (HR<1) และอายุตั้งแต่ time origin — ยอดขายมาจาก IQVIA (ปิด) ทุกงาน
4. **Clock แบบ deterministic** (Beall) ประเมินเกินสำหรับยาที่มีแต่ secondary patents (16.0 vs 8.25 ปี) → อาร์ม "age-based clock" ควรมีฐานเปรียบเทียบนี้
5. **RSF ไม่ชนะ Cox เสมอ** (CTS 2025 Fig 6) → ห้ามตั้งสมมติฐานล่วงหน้าว่าโมเดลซับซ้อนดีกว่า

---

## 2. Q2: selective prediction / failure ranking / calibration / learning-to-defer

ผลค้นหา 255 รายการ ส่วนใหญ่เป็นภาพ/NLP; **ไม่พบงานที่ประเมินพร้อมกันบน (ก) ตารางขนาดเล็ก-ไม่สมดุล (ข) time shift (ค) clustered observations** (credit-card default, UCI 30k, fixed split, ไม่มี temporal/cluster, 10.69987/jacs.2023.30403 คือใกล้ที่สุดและอ่านแค่ระดับ abstract)

| งาน | ข้อสรุปที่เกี่ยวข้อง | สถานะการอ่าน | Locator |
|---|---|---|---|
| Traub et al., AUGRC, arXiv 2407.01032 | AURC ไม่แปลง risk ที่ working point เป็นคะแนนรวม; เสนอ AUGRC (ความเสี่ยงเฉลี่ยของ failures ที่ไม่ถูกตรวจพบ) | อ่านเต็ม | abstract p.1; p.2; Table 1 (R1–R5) p.3; Fig 1 |
| Jaeger et al., arXiv 2211.15259 | สามข้อผิดพลาดของการประเมิน failure detection; proper scoring rules ปนการจัดอันดับกับ calibration | อ่านเต็ม | p.2 (pitfalls); p.3 |
| Feng et al., arXiv 2305.15508 | MSP เป็น baseline ธรรมชาติและแข็ง; ทิ้ง auxiliary confidence head แล้วใช้ MSP อาจดีกว่า; temperature scaling | อ่านเต็ม | p.1; p.3 |
| Liang et al., arXiv 2405.05160 | ภายใต้ distribution shift คะแนนแบบ training-based ไม่ชนะคะแนนง่ายๆ; SRmax แข็ง | อ่านเต็ม | pp.3–4 |
| Baumgartner et al., arXiv 2508.02319 | UQ vs learned deferral; AIROGS (imbalance รุนแรง); pAUC ที่ specificity 90–100% | อ่านเต็ม | pp.4–5; Table 1 p.6 (ไม่ได้สกัดค่า) |
| Zhu et al., ECCV 2022, 10.1007/978-3-031-19806-9_30 | วิธี calibration ไม่ช่วยหรือเสียหายต่อ failure prediction | abstract-only | UNVERIFIED |
| arXiv 2410.15361; arXiv 2403.14715; CA-AURC (J Biomed Inform 2026, 10.1016/j.jbi.2026.105084); arXiv 2505.18622; Galil et al. arXiv 2302.11874; SelectiveNet 2019; Geifman & El-Yaniv 2017 | AURC characterization; label smoothing ทำให้ selective classification แย่ลง; AURC ปรับสำหรับ imbalance; ฯลฯ | abstract-only | UNVERIFIED |

### สังเคราะห์สำหรับ LOE-Bench
- **"จัดอันดับดีขึ้นทุกระดับ coverage" ≠ "ปลอดภัยขึ้นที่ threshold เดียว"**: AURC/AUGRC เป็นสรุปข้ามหลาย coverage (Traub p.1–3) ส่วน operating point เดียวต้องกำหนด threshold ล่วงหน้าและรายงาน selective risk ที่ coverage นั้นแยกต่างหาก ดังนั้นตัวชี้วัดหลักที่ตั้งไว้ (AURC ใน 80% coverage แรก) ต้องจับคู่กับการตรวจ fixed-threshold ที่ freeze จาก cutoff ก่อนหน้า
- baseline ที่ต้องชนะคือ **confidence ranking แบบ MSP/SRmax** (Feng p.3; Liang pp.3–4) ไม่ใช่ "ไม่มีการปฏิเสธ"
- calibration ไม่รับประกันว่าลำดับ failure ดีขึ้น (Zhu 2022 = abstract-only; Jaeger p.3) → รายงาน Brier/ECE แยกจากอันดับ
- หลักฐานสำหรับ time shift/clustered/small-imbalanced = **ช่องว่าง**; ข้อสรุปจากภาพ/NLP ต้องถือเป็นสมมติฐานเท่านั้น
- วิธี learning-to-defer แบบฝึกได้ (Baumgartner) ต้องมีข้อมูลฝึกมาก ซึ่งขัดกับจำนวน positives ที่น้อยใน LOE-Bench (smoke test: 209 positives ที่ h=36)

---

## 3. Q3: ตารางที่ 2: ชุดข้อมูล (Table 2)

คอลัมน์ "release-date proof" = หลักฐานที่ใช้ยืนยันว่าไฟล์/ฉบับนี้สาธารณะเมื่อใด ไม่ใช่วันอนุมัติหรือวันยื่น

| # | Dataset / edition | Release-date proof | Licence | Row locator & join fields | Archival coverage / revision | Leakage limitations |
|---|---|---|---|---|---|---|
| D1 | **Orange Book data files zip** (FDA, https://www.fda.gov/media/76860/download; หน้า https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files); 3 ไฟล์ `~`-delimited: Products.txt, Patent.txt, Exclusivity.txt | ฉบับเก่า: **Wayback captures** (CDX: 31 เดือนที่ต่างกัน 2019-07-19 ถึง 2026-11-03 = ครอบคลุมไม่ครบทุกเดือน). ตัวอย่างวัดเอง: capture 20191214001219 header `x-archive-orig-last-modified` = 13 Dec 2019 20:53:37 GMT; zip member mtime = 2019-12-13; `content-disposition` filename = EOBZIP_2019_11.zip (ป้ายชื่อเดือน ≠ วันแก้ไขไฟล์). capture 20261103032442: last-modified 13 Oct 2026; members 2026-10-09 | **UNVERIFIED** (ไม่พบข้อความ licence บนหน้าที่อ่าน; อย่าสรุปว่าเป็น public domain) | Patent.txt: Appl_Type, Appl_No, Product_No, Patent_No, Patent_Expire_Date_Text, Drug_Substance_Flag, Drug_Product_Flag (เฉพาะสิทธิบัตรที่ยื่น Form 3542 หลัง 2003-08-18), Patent_Use_Code, Delist_Flag, Submission_Date. Exclusivity.txt: ..., Exclusivity_Code, Exclusivity_Date (วันหมดอายุ). Products.txt: Ingredient, DF;Route, Trade_Name, Applicant, Strength, Appl_Type, Appl_No, Product_No, TE_Code, Approval_Date, RLD, RS, Type, Applicant_Full_Name. **Join key = (Appl_Type, Appl_No, Product_No)** | ไฟล์ปัจจุบัน "updated monthly" (หน้า Orange Book home). NBER ระบุว่า FDA web archive ครอบคลุม ต.ค. 2016–ปัจจุบัน (Appendix A; fn 8, https://www.fda.gov/about-fda/about-website/fdagov-archive — ผมไม่ได้เปิดหน้านี้เอง = UNVERIFIED) | (i) Submission_Date ว่างในไฟล์ปี 2019 ~29% (4,392/15,261 แถว); (ii) 7,431/13,322 patent keys ใน snapshot 2019-12 **หายไป**จาก snapshot 2026-10 (หมดอายุ/delist) → ใช้ไฟล์ปัจจุบันย้อนหลังเกิด survivor bias; (iii) 42/6,607 แถวที่ Submission_Date ≤ cutoff และยังไม่หมดอายุ ยังไม่ปรากฏใน snapshot ณ cutoff (lag) |
| D2 | **openFDA Orange Book API** (https://open.fda.gov/apis/drug/orangebook/) | หน้าระบุ "Content current as of: 2026-11-27", update monthly → snapshot เคลื่อนที่ ไม่มีประวัติ | ToS (https://open.fda.gov/terms/): public domain / CC0 1.0 ยกเว้นที่ระบุไว้; ขอให้อ้างแต่ไม่บังคับ; FDA อาจจำกัดอัตราเรียก | ฟิลด์ตาม Orange Book (ดู D1) | ไม่มีประวัติ revision | **ไม่ใช้ทำ as-of** (gate G1) เหมาะเฉพาะ cutoff ปัจจุบัน/พัฒนาโค้ด |
| D3 | **NBER Orange Book Dataset 1985–2016** (Durvasula, Hemphill, Sampat et al., "The NBER Orange Book Dataset: A user's guide", Res Policy 2023;52(7):104791, 10.1016/j.respol.2023.104791; PMC10731339; ข้อมูล https://www.nber.org/research/data/orange-book-patent-and-exclusivity-data-1985-2016) | edition รายปี (มี edition variable ในแต่ละแถว: §3); ไม่มี No. 1986 (fn 7); ยังไม่ได้เปิดหน้า NBER เอง → วันปล่อยชุดข้อมูล = UNVERIFIED | **UNVERIFIED** (ไม่ได้อ่านหน้า NBER) | 4 ไฟล์ Stata: FDA-drug-patents.dta (5,511 patents, 2,173 NDAs), FDA-drug-exclusivity.dta, FDA-patent-use-codes.dta, FDA-drug-exclusivity-codes.dta (§3); join ด้วย NDA number; flag DS/DP ตั้งแต่ edition 2004, use-code ตั้งแต่ edition 1998 (§3) | print editions 1985–1999 + digital 2000–2016 (§1); Appendix A แนะนำต่อด้วย PDF รายปีของ FDA หรือไฟล์รายเดือนผ่าน Wayback/FDA archive | ความละเอียดเป็นรายปี (ไม่ใช่รายเดือน) → patent ที่อยู่ช่วงสั้นๆ แล้ว delist อาจหาย; ข้อผิดพลาด PTE: OB ไม่รายงาน PTE ในบางสิทธิบัตร (Table 2), expiry ถูกต้อง 93% ในกลุ่ม PTE (§4); NBER ใช้ "latest applicable edition" แก้วันหมดอายุในบางตาราง (ต้องระวังว่าเป็นข้อมูลที่แก้ภายหลัง = hindsight หากนำไปใช้เป็นฟีเจอร์); PTE list จาก USPTO ฉบับ 18 Jan 2016 |
| D4 | **Orange Book print/PDF editions และ Cumulative Supplement** (Preface: Hatch-Waxman กำหนดให้พิมพ์พร้อม monthly supplements; home page ลิงก์ "Current Cumulative Supplement" media/72973). Internet Archive items: bwb_Y0-CHF-191 (1995), approveddrugprod0000cent (1997) | วันที่ edition บนปก/หน้าชื่อ (ยังไม่ได้เปิดดู) = UNVERIFIED; การเข้าถึงใน IA (น่าจะ lending) = UNVERIFIED; หน้า FDA สมมติ "orange-book-archives" ให้ 404 → **ไม่พบหน้าคลัง edition เก่าที่ยืนยันได้** | UNVERIFIED | ต้อง OCR/parse เอง (NBER Appendix A: "considerable processing") | ไม่ครบทุกปี (UNVERIFIED) | OCR error; ฉบับพิมพ์มีรอบการแก้ไขที่ไม่รู้วันแน่ชัด |
| D5 | **Paragraph IV Certification List** + **New Paragraph IV Certifications list** (https://www.fda.gov/drugs/abbreviated-new-drug-application-anda/patent-certifications-and-suitability-petitions) | หน้าระบุ list วันแรกยื่น PIV ตั้งแต่ 2004-03-02; ตั้งแต่ 2019-06-18 เพิ่มคอลัมน์ Date of First PIV Submission ("pre-MMA" สำหรับเก่า), Number of Potential First Applicant ANDAs, 180-Day Decision Status, 180-Day Decision Posting Date. New PIV list "as of October 27, 2026" (XLS media/194880; PDF media/166048) | UNVERIFIED | ฟิลด์ New PIV: Drug Name, Dosage Form, Strength, RLD/NDA, Date of Submission; join → Orange Book ผ่าน NDA/ingredient/strength (ไม่มี key ตรงที่ยืนยันได้) | FDA ระบุว่า "updated retrospectively as practicable" และ "may adjust over time" → เนื้อหาย้อนหลังถูก backfill; suitability petition tracking อัปเดตล่าสุด ส.ค. 2015 | **สูง**: คอลัมน์ 180-day status/ค่าที่ backfill = hindsight; Date of Submission ≠ วันที่รายการนั้นสาธารณะ; ต้องใช้ capture ลงวันที่เท่านั้น (ไม่ได้ตรวจความครอบคลุมของ Wayback สำหรับหน้านี้ = UNVERIFIED) |
| D6 | **Purple Book monthly "Historical Data Changes Report"** CSV/XLSX (https://purplebooksearch.fda.gov/downloads); รูปแบบ URL https://www.accessdata.fda.gov/drugsatfda_docs/PurpleBook/<year>/purplebook-search-<month>-data-download.csv | รายการดาวน์โหลดรายเดือน ก.พ. 2020–ต.ค. 2026 (หน้าที่เก็บผ่าน Wayback capture 20261118132322; มีนาคม 2021 มี XLSX อย่างเดียว). **วันปล่อยไฟล์แต่ละเดือน = UNVERIFIED**: Wayback CDX ของไฟล์ CSV บน accessdata มี capture เพียงเดือน พ.ค. 2026 (เช่น 20260504163538) → วัน capture ≠ วันปล่อย | UNVERIFIED (เนื้อหา FDA; ไม่ได้อ่านข้อความ licence) | ไฟล์เมษายน 2024 (หัวไฟล์ "Purple Book Monthly Historical Data Changes Report - April 2024"): คอลัมน์ N/R/U, Applicant, BLA Number, Proprietary Name, Proper Name, BLA Type (351(a)/351(k)), Strength, Dosage Form, Route, Product Presentation, Marketing Status, Licensure, Approval Date, Ref. Product Proper/Proprietary Name, Supplement Number, Submission Type, License Number, Product Number, Center, Date of First Licensure, Exclusivity Expiration Date, First Interchangeable Exclusivity Exp. Date, Ref. Product Exclusivity Exp. Date, Orphan Exclusivity Exp. Date. ส่วนบน = รายการเปลี่ยนแปลงของเดือน (U/N/R), ส่วนล่าง = ผลิตภัณฑ์ทั้งหมดของเดือน. join: BLA Number + Product Number; ref product ผ่านคอลัมน์ Ref. Product. ผมพาร์ส April 2024 ได้ 1,971 แถว, 98 แถว 351(k) Original (ผ่านบริการ scrape; curl ตรงถูกบล็อก) | ปีละไฟล์ archive 2020–2025; R = ผลิตภัณฑ์ที่เพิ่งถูกเพิ่มเข้าฐานข้อมูล (เช่น CBER เพิ่มครั้งแรกในรุ่น ส.ค. 2020) ไม่ใช่การอนุมัติใหม่ | Approval Date/Date of First Licensure ≠ วันสาธารณะ; แถว R บิดเบือน "วันเข้ากลุ่ม"; มีหน้า "Patent List" (ไม่ได้ตรวจ = UNVERIFIED) |
| D7 | **Drugs@FDA data files** (https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files; ZIP media/89850) | "updated each morning, Monday through Friday"; หน้าแสดง Data Last Updated Nov 25th 2026 → snapshot เดียวที่เคลื่อนที่; ERD ลงวันที่ 10 ม.ค. 2025 | UNVERIFIED | 12 ตาราง: Submissions (ApplNo, SubmissionClassCodeID, SubmissionType, SubmissionNo, SubmissionStatus, SubmissionStatusDate, SubmissionsPublicNotes, ReviewPriority), Products, MarketingStatus(+_Lookup), TE, ApplicationDocs (title, URL, date), SubmissionPropertyType (Orphan), ActionTypes_Lookup ฯลฯ; **join = ApplNo + ProductNo** | ไม่มีประวัติในแหล่งนี้; Wayback coverage ไม่ได้ตรวจ = UNVERIFIED | ใช้เป็นแหล่ง **label** (วัน first ANDA approval) ได้เพราะเหตุการณ์อนุมัติคงที่ แต่ห้ามใช้เป็นฟีเจอร์ ณ cutoff; SubmissionStatusDate ≠ วันสาธารณะ |
| D8 | **Medicaid State Drug Utilization Data (SDUD)** (https://data.medicaid.gov/dataset/158a1baa-5506-400a-8ec3-97756f0b0536; ไฟล์ปี 2025) | Issued 2025-12-09; **Modified 2026-07-13** (ไฟล์ sdud2025_updatedjuly2026.csv); หน้า SDUD อัปเดตล่าสุด 2026-11-24; 2Q2021+3Q2021 โพสต์พร้อมกัน ก.พ. 2022 | public domain label 1.0 (https://www.usa.gov/publicdomain/label/1.0/) | 5,308,547 แถว × 15 คอลัมน์: utilization_type, state, ndc, labeler_code, product_code, package_size, year, quarter, suppression_used, product_name, units_reimbursed, number_of_prescriptions, total/medicaid/non-medicaid amount reimbursed. join: NDC → NDC directory (UNVERIFIED) → Orange Book ผ่านส่วนผสม/ความแรง/appl no. | ไฟล์รายปี 1991–2026 | **ถูกแก้ภายหลัง** (modified หลัง issued 7 เดือน) → ต้องเก็บ vintage ตามวันโพสต์; suppression flag; เป็นเฉพาะ Medicaid (proxy ของ demand ไม่ใช่ตลาดรวม) |
| D9 | **NDC Directory; Medicare Part D spending dashboard; PSG list; 180-day exclusivity list; Federal Register notices** | **UNVERIFIED ทั้งหมด** (ยังไม่ได้เปิดดูวันที่ปล่อย) | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| D10 | **Licensed repositories**: IQVIA (NSP / World Review), DrugPatentWatch, Cortellis/Citeline, Evaluate, Lex Machina, Docket Navigator, ParagraphFour | **ปิด/ต้องมีสัญญา**; ผมไม่ได้ตรวจเงื่อนไขหรือความครอบคลุมเชิงเก็บถาวร: UNVERIFIED. เป็นที่รู้จากงานที่อ่าน: IQVIA เป็นแหล่งยอดขายใน TIRS 2020, CTS 2025, PLOS ONE 2019 (Data Availability p.1: ซื้อได้); ParagraphFour ใช้ใน NBER paper (Table 1, §4) ครอบคลุมคดีที่ยุติตั้งแต่ 1 พ.ย. 2003 | UNVERIFIED (reuse/redistribution มักจำกัด) | UNVERIFIED | UNVERIFIED | ผลคดี/ข้อมูลที่ vendor ทำย้อนหลัง = hindsight หากไม่ได้ stamp วัน |

---

## 4. จะรู้ได้อย่างไรว่าอะไรเป็นสาธารณะ ณ วัน cutoff

### 4.1 หลักการ
กำหนดให้ cutoff = T. "สาธารณะ ณ T" = ระเบียนที่ปรากฏใน snapshot ที่มีหลักฐานว่าเผยแพร่แล้วไม่เกิน T. ใช้ **การปรากฏใน snapshot** เป็นตัวพิสูจน์ ไม่ใช่ฟิลด์วันที่ในระเบียน

### 4.2 ขั้นตอนที่ใช้ได้จริง (พิสูจน์แล้วกับ Orange Book zip)
1. ดึงรายการ capture ด้วย Wayback CDX: `http://web.archive.org/cdx/search/cdx?url=<url>&output=json&fl=timestamp,statuscode,digest` (digest เหมือนกัน = ไฟล์เดียวกัน)
2. ดึง byte ดิบ: `http://web.archive.org/web/<timestamp>id_/<url>`; เก็บ response headers
3. เก็บหลักฐานเป็นลำดับชั้น: (a) memento-datetime ของ capture = **ขอบบน** (ไฟล์สาธารณะไม่เกินวันนี้); (b) `x-archive-orig-last-modified` = ประมาณวันเผยแพร่ แต่ถ้าไฟล์ถูกอัปโหลดซ้ำก็เปลี่ยนได้ (UNVERIFIED ว่า FDA ทำหรือไม่); (c) วันที่ของไฟล์ใน zip; (d) ชื่อไฟล์/ป้ายเดือน — **ห้ามเชื่อ**: capture ธ.ค. 2019 ชื่อ EOBZIP_2019_11.zip แต่ last-modified = 13 ธ.ค. 2019
4. สำหรับ cutoff T: เลือก snapshot ล่าสุดที่ **memento-datetime ≤ T** (ใช้ของเก่าปลอดภัย ใช้ของใหม่เสี่ยงรั่ว); ถ้าไม่มี capture ใกล้ T ให้ **ตัดแถว cutoff นั้นออกและบันทึกเหตุผล** แทนการเติมด้วยไฟล์ปัจจุบัน
5. หลีกเลี่ยงการยิง Wayback ถี่ (ผมถูก HTTP 429 หลังยิงต่อเนื่อง)
6. จำกัดความครอบคลุม: ไฟล์ Orange Book นี้มี 31 เดือนที่ต่างกันใน 2019-07 ถึง 2026-11; ก่อน 2019-07 บนต้นทาง URL นี้ = ไม่พบ (UNVERIFIED ว่ามี URL เก่าอื่น); FDA archive (ต.ค. 2016–) ตามที่ NBER ระบุ = UNVERIFIED

### 4.3 หลักฐานจากการคำนวณเองว่าทำไม "วันที่ในระเบียน" ใช้ไม่ได้ (สคริปต์: `/home/sandbox/loe_lit/asof_demo.py`; รันซ้ำแล้วได้ตัวเลขเดิม)
| การวัด | snapshot 2019-12-13 | snapshot 2026-10 |
|---|---|---|
| Patent.txt แถวทั้งหมด | 15,261 | 22,438 |
| แถวที่มี Submission_Date | 10,869 (≈71%) | 19,633 |
| Products.txt แถว (NDA key ต่างกัน) | 38,117 (22,276) | 48,865 (27,428) |

- จาก 13,322 patent keys (Appl_No, Product_No, Patent_No) ปี 2019-12: **7,431 หายจาก snapshot 2026-10**; ปี 2026 มี key ใหม่ 11,857 → ใช้ไฟล์ปัจจุบันสร้าง "สิ่งที่ ณ 2019 เห็น" จะขาดสิทธิบัตรที่หมดอายุ/ถูก delist แล้ว
- จาก 6,607 แถวปี 2026 ที่ Submission_Date ≤ 2019-12-13 และสิทธิบัตรยังไม่หมดอายุ ณ วันนั้น มี **42 แถว (0.64%) ยังไม่อยู่** ใน snapshot 2019-12 (เช่น NDA 209310 สิทธิบัตร 10357640 ยื่น 6 ธ.ค. 2019; NDA 212038 สิทธิบัตร 10500162 ยื่น 11 ธ.ค. 2019) สอดคล้องกับ lag ระหว่างยื่นกับเผยแพร่ → Submission_Date ไม่ใช่วันที่สาธารณะ
- นี่เป็นตัวอย่างจากสอง snapshot ไม่ใช่การประมาณอัตรา lag ทั่วไป

### 4.4 ข้อกำหนดเฉพาะแต่ละแหล่ง
- **Purple Book**: ใช้ไฟล์รายเดือน (D6) แต่ต้องมีหลักฐานวันปล่อยของแต่ละเดือนจากแหล่งอื่น เพราะ capture ของ CSV อยู่เพียง พ.ค. 2026; ส่วนบนของไฟล์ (N/U/R) ช่วยทำ diff รายเดือน; Approval Date ไม่ใช่วันเผยแพร่
- **PIV list**: ใช้ได้เฉพาะ capture ลงวันที่; คอลัมน์ที่เติมย้อนหลังถือเป็นข้อมูลหลัง cutoff
- **Drugs@FDA**: ไม่มีประวัติ → ใช้เฉพาะเป็นแหล่ง label
- **SDUD**: เก็บ vintage ตามวันโพสต์/แก้ไข (Issued vs Modified)
- **ยอดขาย IQVIA**: ใช้ได้เฉพาะหน้าต่างที่ปิดก่อน T (เช่น lag ตามที่ CTS 2025 §3.1 ทำ 1 ปี) และ vendor ต้องไม่แก้ย้อนหลัง = UNVERIFIED

---

## 5. สิ่งที่ถูกยกเว้น และ closed-source inputs

**ยกเว้นเป็น predictor/feature:**
1. FDA First Generic list (ตามโจทย์)
2. การอนุมัติภายหลัง cutoff; จำนวน/วัน ANDA ที่ถูกอนุมัติหลัง T
3. วัน challenge ที่ backfill (PIV list คอลัมน์ที่เพิ่มหลัง 2019-06-18; 180-day decision status)
4. ผลคดีภายหลัง (เช่น แหล่งแบบ JHPPL 2026)
5. หน้าต่างยอดขายที่ผูกกับเหตุการณ์อนาคต (เช่น "ยอดขายปีที่ 4 หลังอนุมัติ" ถ้าเกิดหลัง T สำหรับ cutoff นั้น; TIRS 2020 sensitivity ใช้แบบนี้)
6. Delist_Flag และสถานะ "ยังมีสิทธิบัตร" จากไฟล์ปัจจุบัน

**Closed-source (ระบุชัด):** IQVIA NSP/World Review (TIRS 2020, CTS 2025, Kerr–Glos, Murimi-Worstell); FDA internal ANDA submission data และ drug-complexity designation (TIRS 2020, CTS 2025); ฐานข้อมูล entry derived จาก Medicaid (VIH 2018); Pharmaceutical Data Services/Walsh-America (HSR 1997); ParagraphFour และ vendor อื่นใน D10. ตัวแทนแบบเปิดที่เป็นไปได้ = SDUD (เฉพาะ Medicaid)

---

## 6. สามไอเดียต้นทุนต่ำสำหรับการเปรียบเทียบแบบ matched, development-only

เงื่อนไขร่วม: ใช้ entity set, cutoff, split, งบค้นหา hyperparameter เดียวกันทั้งสามอาร์ม (age clock / flat logistic ที่ calibrate แล้ว / evidence graph แบบสามค่า); ไม่แตะ test set; cluster ตาม drug family; ไม่ใช้ฟีเจอร์ใน §5

| # | ไอเดีย | ทำอย่างไร | เหตุผลที่อาจล้มเหลว (หนึ่งข้อ) |
|---|---|---|---|
| 1 | **ท่อ as-of จาก Wayback snapshot** | ใช้ snapshot ของ D1 ที่ capture ≤ cutoff (§4.2) สร้างฟีเจอร์ที่ cutoff รายปี; label จาก D7; แบ่งแบบ forward time-split ตามปี cutoff; เปรียบเทียบสามอาร์ม | ความครอบคลุม snapshot ไม่ครบ (31 เดือนใน 2019-07 ถึง 2026-11) ทำให้เหลือจำนวน cutoff-year และ positives น้อยเกินจะแยกอาร์มได้ |
| 2 | **ตรวจ selective prediction สองแบบบนการทำนายชุดเดียวกัน** | คำนวณ AURC และ AUGRC ภายใน 80% coverage แรก เทียบกับ MSP/SRmax baseline และตรวจ selective risk ที่ threshold เดียวที่ freeze จาก cutoff ก่อนหน้า; bootstrap แบบ cluster ตาม drug family | CI ของส่วนต่างจะกว้างจนรวม 0 เพราะ positives น้อยและ threshold จาก cutoff เก่าไม่ถ่ายโอนภายใต้ time shift; MSP เป็น baseline ที่ชนะยากตามงานภาพ/NLP (Feng p.3; Liang pp.3–4) |
| 3 | **จำลอง feature set ของ CTS 2025/TIRS 2020 แบบ open-only** | แทนยอดขาย IQVIA ด้วย demand proxy จาก SDUD (vintage ตามวันโพสต์) + ฟีเจอร์ Orange Book/PSG ที่เป็นสาธารณะ; เทียบ Cox/RSF กับอาร์ม evidence graph ภายใต้ forward split | SDUD ครอบคลุมเฉพาะ Medicaid, มี suppression และถูกแก้ภายหลัง จึงอาจไม่ถ่ายทอดสัญญาณยอดขายที่ HR สูงในงานเดิม (ซึ่งใช้ IQVIA) |

ส่วน track biosimilar (เชิงพรรณนา): ใช้ diff รายเดือนของ Purple Book (D6) หลังยืนยันวันปล่อยแต่ละไฟล์ได้เท่านั้น

---

## 7. ข้อจำกัดของรายงานนี้
- สามงานหลัก (CPT 2019, JLME 2019, VIH 2018) อ่านไม่ถึง full text; ข้อสรุปเรื่อง as-of/time-split/censoring ของงานเหล่านี้ = UNVERIFIED
- งานระดับ abstract-only ใน Table 1 (แถว 3–7, 9, 11) ไม่มี locator
- ไม่ได้ตรวจ licence ของ OB zip, PIV list, Purple Book, Drugs@FDA, NBER, Wayback; ไม่ได้ตรวจเงื่อนไข vendor ทั้งหมด
- ความครอบคลุม Wayback ตรวจเฉพาะ URL ของ OB zip และหน้า Purple Book downloads; การคำนวณ snapshot เป็นสองจุด ไม่ใช่การประเมินทั่วไป
- ผลลัพธ์ smoke-test ของโครงการ (เช่น 209 positives ที่ h=36) เป็นตัวเลขของ baseline เบื้องต้นของผม ไม่ใช่ผลวิจัย