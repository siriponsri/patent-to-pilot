# USPTO PatentsView: download inventory — 2026-11-18

ตรวจจาก USPTO Open Data Portal ขณะลงชื่อเข้าใช้ วันที่ 18 พฤศจิกายน 2026 (Asia/Bangkok)

## สถานะดาวน์โหลด

ยังไม่มีไฟล์ที่ยืนยันว่าดาวน์โหลดเสร็จหรือบันทึกลงโฟลเดอร์ปลายทาง กด g_us_rel_doc.tsv.zip แล้วพบ CAPTCHA จึงเปิดค้างเพื่อให้ผู้ใช้ดำเนินการหรือยืนยันก่อนแก้ CAPTCHA

ปลายทางที่ผู้ใช้กำหนด: `C:\Users\User\Desktop\myProject\patent-to-pilot\data\raw\uspto\`

| Dataset | File | Compressed bytes | MiB | บทบาท |
|---|---|---:|---:|---|
| Granted | g_us_rel_doc.tsv.zip | 276,677,523 | 263.860 | จำเป็น; รอ CAPTCHA |
| Pre-Grant | pg_us_rel_doc.tsv.zip | 106,086,288 | 101.172 | พบจริง; ตัวเลือกความสัมพันธ์แบบมีโครงสร้าง |
| Pre-Grant | pg_rel_app_text.tsv.zip | 240,615,262 | 229.469 | พบจริง; related application text |
| Granted | g_rel_app_text.tsv.zip | 242,227,783 | 231.007 | ไฟล์สำรองตามคำขอ |

ทั้ง 4 ไฟล์แสดง release date 2026-04-10 (Eastern) ไม่พบชื่อ pg_rel_app.tsv.zip หลังตรวจครบ 26 รายการใน Pre-Grant Disambiguated Data

## R5: claims inventory — ยังไม่ดาวน์โหลด

| ชุด | ปี | จำนวน | ZIP bytes รวม | GB (decimal) | GiB |
|---|---|---:|---:|---:|---:|
| g_claims_* | 1976–2025 | 50 | 10,425,483,938 | 10.425484 | 9.709489 |
| pg_claims_* | 2001–2025 | 25 | 8,762,044,927 | 8.762045 | 8.160290 |
| รวม | | 75 | 19,187,528,865 | 19.187529 | 17.869779 |

ขนาดรวมเป็นไฟล์ ZIP เท่านั้น ไม่ใช่ขนาดหลังแตกไฟล์ หากเพดาน 60 GB รวมไฟล์เดิมและพื้นที่ทำงาน ต้องนับพื้นที่เหล่านั้นเพิ่มก่อนดาวน์โหลดจริง การจัดทำรายการนี้ไม่ถือว่าอนุมัติดาวน์โหลด claims

## Sources

- [Granted Disambiguated Data](https://data.uspto.gov/bulkdata/datasets/pvgpatdis?fileDataFromDate=1976-01-01&fileDataToDate=2025-12-31)
- [Pre-Grant Disambiguated Data](https://data.uspto.gov/bulkdata/datasets/pvpgpubdis?fileDataFromDate=2001-03-15&fileDataToDate=2025-12-31)
- [Granted Long Text Data](https://data.uspto.gov/bulkdata/datasets/pvgpattxt?fileDataFromDate=1976-01-01&fileDataToDate=2025-12-31)
- [Pre-Grant Long Text Data](https://data.uspto.gov/bulkdata/datasets/pvpgpubtxt?fileDataFromDate=2001-03-15&fileDataToDate=2025-12-31)

## รายชื่อไฟล์ claims และขนาดตามหน้า ODP

| File | ZIP bytes | MiB | Release date/time (Eastern) |
|---|---:|---:|---|
| g_claims_2025.tsv.zip | 346,007,957 | 329.979 | 2026-04-10 / 5:33:00 PM Eastern |
| g_claims_2024.tsv.zip | 342,739,238 | 326.862 | 2026-03-12 / 10:59:20 PM Eastern |
| g_claims_2023.tsv.zip | 328,109,466 | 312.910 | 2026-03-12 / 10:59:10 PM Eastern |
| g_claims_2022.tsv.zip | 337,656,168 | 322.014 | 2026-03-12 / 10:59:04 PM Eastern |
| g_claims_2021.tsv.zip | 394,834,557 | 376.544 | 2026-03-12 / 10:58:58 PM Eastern |
| g_claims_2020.tsv.zip | 399,045,431 | 380.559 | 2026-03-12 / 10:58:50 PM Eastern |
| g_claims_2019.tsv.zip | 383,844,479 | 366.063 | 2026-03-12 / 10:58:42 PM Eastern |
| g_claims_2018.tsv.zip | 348,015,993 | 331.894 | 2026-03-12 / 10:58:36 PM Eastern |
| g_claims_2017.tsv.zip | 337,520,630 | 321.885 | 2026-03-12 / 10:58:29 PM Eastern |
| g_claims_2016.tsv.zip | 315,105,828 | 300.508 | 2026-03-12 / 10:58:23 PM Eastern |
| g_claims_2015.tsv.zip | 312,248,408 | 297.783 | 2026-03-12 / 10:58:17 PM Eastern |
| g_claims_2014.tsv.zip | 311,138,486 | 296.725 | 2026-03-12 / 10:58:11 PM Eastern |
| g_claims_2013.tsv.zip | 292,322,551 | 278.781 | 2026-03-12 / 10:58:04 PM Eastern |
| g_claims_2012.tsv.zip | 265,787,975 | 253.475 | 2026-03-12 / 10:57:57 PM Eastern |
| g_claims_2011.tsv.zip | 245,457,001 | 234.086 | 2026-03-12 / 10:57:52 PM Eastern |
| g_claims_2010.tsv.zip | 240,041,341 | 228.921 | 2026-03-12 / 10:57:46 PM Eastern |
| g_claims_2009.tsv.zip | 183,284,364 | 174.794 | 2026-03-12 / 10:57:41 PM Eastern |
| g_claims_2008.tsv.zip | 163,502,374 | 155.928 | 2026-03-12 / 10:57:37 PM Eastern |
| g_claims_2007.tsv.zip | 175,568,392 | 167.435 | 2026-03-12 / 10:57:34 PM Eastern |
| g_claims_2006.tsv.zip | 191,413,504 | 182.546 | 2026-03-12 / 10:57:29 PM Eastern |
| g_claims_2005.tsv.zip | 157,065,542 | 149.789 | 2026-03-12 / 10:57:25 PM Eastern |
| g_claims_2004.tsv.zip | 170,408,310 | 162.514 | 2026-03-12 / 10:57:22 PM Eastern |
| g_claims_2003.tsv.zip | 173,750,822 | 165.702 | 2026-03-12 / 10:57:18 PM Eastern |
| g_claims_2002.tsv.zip | 169,547,497 | 161.693 | 2026-03-12 / 10:57:14 PM Eastern |
| g_claims_2001.tsv.zip | 313,667,616 | 299.137 | 2026-03-12 / 10:57:08 PM Eastern |
| g_claims_2000.tsv.zip | 297,684,695 | 283.894 | 2026-03-12 / 10:57:03 PM Eastern |
| g_claims_1999.tsv.zip | 283,380,054 | 270.252 | 2026-03-12 / 10:56:57 PM Eastern |
| g_claims_1998.tsv.zip | 271,607,499 | 259.025 | 2026-03-12 / 10:56:52 PM Eastern |
| g_claims_1997.tsv.zip | 200,692,404 | 191.395 | 2026-03-12 / 10:56:47 PM Eastern |
| g_claims_1996.tsv.zip | 192,785,587 | 183.855 | 2026-03-12 / 10:56:43 PM Eastern |
| g_claims_1995.tsv.zip | 173,591,634 | 165.550 | 2026-03-12 / 10:56:40 PM Eastern |
| g_claims_1994.tsv.zip | 169,442,256 | 161.593 | 2026-03-12 / 10:56:36 PM Eastern |
| g_claims_1993.tsv.zip | 158,731,534 | 151.378 | 2026-03-12 / 10:56:32 PM Eastern |
| g_claims_1992.tsv.zip | 154,928,324 | 147.751 | 2026-03-12 / 10:56:29 PM Eastern |
| g_claims_1991.tsv.zip | 150,912,884 | 143.922 | 2026-03-12 / 10:56:26 PM Eastern |
| g_claims_1990.tsv.zip | 138,999,848 | 132.561 | 2026-03-12 / 10:56:23 PM Eastern |
| g_claims_1989.tsv.zip | 146,719,166 | 139.922 | 2026-03-12 / 10:56:20 PM Eastern |
| g_claims_1988.tsv.zip | 116,358,291 | 110.968 | 2026-03-12 / 10:56:17 PM Eastern |
| g_claims_1987.tsv.zip | 122,108,184 | 116.451 | 2026-03-12 / 10:56:14 PM Eastern |
| g_claims_1986.tsv.zip | 102,105,181 | 97.375 | 2026-03-12 / 10:56:12 PM Eastern |
| g_claims_1985.tsv.zip | 101,612,550 | 96.905 | 2026-03-12 / 10:56:10 PM Eastern |
| g_claims_1984.tsv.zip | 92,701,232 | 88.407 | 2026-03-12 / 10:56:08 PM Eastern |
| g_claims_1983.tsv.zip | 77,572,798 | 73.979 | 2026-03-12 / 10:56:06 PM Eastern |
| g_claims_1982.tsv.zip | 78,653,222 | 75.010 | 2026-03-12 / 10:56:04 PM Eastern |
| g_claims_1981.tsv.zip | 89,124,436 | 84.996 | 2026-03-12 / 10:56:02 PM Eastern |
| g_claims_1980.tsv.zip | 83,091,102 | 79.242 | 2026-03-12 / 10:56:00 PM Eastern |
| g_claims_1979.tsv.zip | 65,753,101 | 62.707 | 2026-03-12 / 10:55:58 PM Eastern |
| g_claims_1978.tsv.zip | 88,110,914 | 84.029 | 2026-03-12 / 10:55:56 PM Eastern |
| g_claims_1977.tsv.zip | 83,355,862 | 79.494 | 2026-03-12 / 10:55:54 PM Eastern |
| g_claims_1976.tsv.zip | 87,377,250 | 83.329 | 2026-03-12 / 10:55:51 PM Eastern |
| pg_claims_2025.tsv.zip | 416,718,646 | 397.414 | 2026-04-10 / 5:38:02 PM Eastern |
| pg_claims_2024.tsv.zip | 455,999,187 | 434.875 | 2026-03-12 / 11:37:59 PM Eastern |
| pg_claims_2023.tsv.zip | 450,419,449 | 429.553 | 2026-03-12 / 11:37:52 PM Eastern |
| pg_claims_2022.tsv.zip | 440,090,991 | 419.703 | 2026-03-12 / 11:37:43 PM Eastern |
| pg_claims_2021.tsv.zip | 410,400,671 | 391.389 | 2026-03-12 / 11:37:32 PM Eastern |
| pg_claims_2020.tsv.zip | 424,616,666 | 404.946 | 2026-03-12 / 11:37:24 PM Eastern |
| pg_claims_2019.tsv.zip | 399,936,319 | 381.409 | 2026-03-12 / 11:37:15 PM Eastern |
| pg_claims_2018.tsv.zip | 379,134,349 | 361.571 | 2026-03-12 / 11:37:05 PM Eastern |
| pg_claims_2017.tsv.zip | 373,535,697 | 356.231 | 2026-03-12 / 11:36:57 PM Eastern |
| pg_claims_2016.tsv.zip | 379,598,214 | 362.013 | 2026-03-12 / 11:36:48 PM Eastern |
| pg_claims_2015.tsv.zip | 377,622,355 | 360.129 | 2026-03-12 / 11:36:41 PM Eastern |
| pg_claims_2014.tsv.zip | 375,647,855 | 358.246 | 2026-03-12 / 11:36:33 PM Eastern |
| pg_claims_2013.tsv.zip | 343,958,054 | 328.024 | 2026-03-12 / 11:36:26 PM Eastern |
| pg_claims_2012.tsv.zip | 329,591,819 | 314.323 | 2026-03-12 / 11:36:20 PM Eastern |
| pg_claims_2011.tsv.zip | 324,295,915 | 309.273 | 2026-03-12 / 11:36:13 PM Eastern |
| pg_claims_2010.tsv.zip | 340,566,435 | 324.789 | 2026-03-12 / 11:36:06 PM Eastern |
| pg_claims_2009.tsv.zip | 333,150,757 | 317.717 | 2026-03-12 / 11:35:59 PM Eastern |
| pg_claims_2008.tsv.zip | 328,218,314 | 313.013 | 2026-03-12 / 11:35:53 PM Eastern |
| pg_claims_2007.tsv.zip | 315,784,025 | 301.155 | 2026-03-12 / 11:35:47 PM Eastern |
| pg_claims_2006.tsv.zip | 312,836,556 | 298.344 | 2026-03-12 / 11:35:41 PM Eastern |
| pg_claims_2005.tsv.zip | 324,100,887 | 309.087 | 2026-03-12 / 11:35:34 PM Eastern |
| pg_claims_2004.tsv.zip | 318,744,558 | 303.978 | 2026-03-12 / 11:35:28 PM Eastern |
| pg_claims_2003.tsv.zip | 300,646,679 | 286.719 | 2026-03-12 / 11:35:22 PM Eastern |
| pg_claims_2002.tsv.zip | 243,258,232 | 231.989 | 2026-03-12 / 11:35:17 PM Eastern |
| pg_claims_2001.tsv.zip | 63,172,297 | 60.246 | 2026-03-12 / 11:35:13 PM Eastern |

